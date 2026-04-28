from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.place_selection import PlaceSelectionSkill
from local_explorer_agent.app.agent.skills.replanning import ReplanningSkill
from local_explorer_agent.app.agent.skills.routing import RoutingSkill
from local_explorer_agent.app.agent.skills.timeline_builder import TimelineBuilderSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.domain.enums import ExecutionAction
from local_explorer_agent.app.domain.models import (
    ExecutionTask,
    PlanCandidate,
    PlanEvent,
    PlanOutput,
)
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.domain.scoring import choose_recommended_candidate, score_candidate


class Orchestrator:
    def __init__(
        self,
        *,
        session_store: SessionStore,
        user_understanding_skill: UserUnderstandingSkill,
        conflict_detection_skill: ConflictDetectionSkill,
        negotiation_skill: NegotiationSkill,
        experience_planning_skill: ExperiencePlanningSkill,
        place_selection_skill: PlaceSelectionSkill,
        routing_skill: RoutingSkill,
        timeline_builder_skill: TimelineBuilderSkill,
        replanning_skill: ReplanningSkill,
    ) -> None:
        self.session_store = session_store
        self.user_understanding_skill = user_understanding_skill
        self.conflict_detection_skill = conflict_detection_skill
        self.negotiation_skill = negotiation_skill
        self.experience_planning_skill = experience_planning_skill
        self.place_selection_skill = place_selection_skill
        self.routing_skill = routing_skill
        self.timeline_builder_skill = timeline_builder_skill
        self.replanning_skill = replanning_skill

    def preview_plan(self, request: PlanPreviewRequest) -> PlanOutput:
        group_context = self.user_understanding_skill.run(
            user_query=request.query,
            user_id=request.user_id,
            city=request.city,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
        )
        conflicts = self.conflict_detection_skill.run(group_context)
        strategies = self.negotiation_skill.run(group_context=group_context, conflicts=conflicts)
        candidates = self.experience_planning_skill.run(
            group_context=group_context,
            conflicts=conflicts,
            negotiation_strategies=strategies,
        )

        enriched_candidates: list[PlanCandidate] = []
        for candidate in candidates:
            candidate = self.place_selection_skill.run(
                candidate=candidate,
                group_context=group_context,
                city=request.city,
            )
            candidate = self.routing_skill.run(candidate)
            candidate = self.timeline_builder_skill.run(
                candidate=candidate,
                start_time=request.start_time,
                duration_minutes=request.duration_minutes,
            )
            candidate = score_candidate(candidate, group_context)
            enriched_candidates.append(candidate)

        recommended = choose_recommended_candidate(enriched_candidates)
        recommended.recommendation_reason = (
            "该方案不是简单平均分最高，而是在 overall_score、min_role_score、fairness_score "
            "之间更均衡，能避免某个角色被明显牺牲，并保留局部备选点。"
        )
        recommended.tradeoff_summary = "优先控制距离、排队和饮食冲突，牺牲少量新奇感换稳定性。"

        plan = PlanOutput(
            user_id=request.user_id,
            input_query=request.query,
            inferred_context=group_context,
            conflicts=conflicts,
            negotiation_strategies=strategies,
            plan_candidates=enriched_candidates,
            recommended_plan_id=recommended.plan_id,
            execution_graph=self._build_execution_graph(recommended),
            share_message=f"我为你们做了一个{recommended.title}：先照顾孩子，再自然安排轻食，最后轻松收尾。",
        )
        return self.session_store.save(plan)

    def replan(self, *, session_id: str, event: PlanEvent) -> PlanOutput:
        plan = self.session_store.get(session_id)
        updated = self.replanning_skill.run(plan=plan, event=event)
        return self.session_store.update(updated)

    def _build_execution_graph(self, recommended: PlanCandidate) -> list[ExecutionTask]:
        tasks: list[ExecutionTask] = []
        for stage in recommended.stages:
            poi = stage.selected_poi
            if not poi:
                continue
            if stage.stage_type == "dine":
                tasks.append(
                    ExecutionTask(
                        task_id=f"task_book_{stage.stage_id}",
                        action=ExecutionAction.BOOK_RESTAURANT,
                        poi_id=poi.id,
                        params={"stage_id": stage.stage_id, "party_size_hint": 3},
                    )
                )
            elif poi.business_rules.get("reservation_required") or stage.stage_type in {
                "energy_release",
                "explore",
            }:
                tasks.append(
                    ExecutionTask(
                        task_id=f"task_activity_{stage.stage_id}",
                        action=ExecutionAction.BOOK_ACTIVITY,
                        poi_id=poi.id,
                        params={"stage_id": stage.stage_id},
                    )
                )

        first_poi = recommended.stages[0].selected_poi if recommended.stages else None
        last_poi = recommended.stages[-1].selected_poi if recommended.stages else None
        taxi_depends = [task.task_id for task in tasks]
        tasks.append(
            ExecutionTask(
                task_id="task_call_taxi_home",
                action=ExecutionAction.CALL_TAXI,
                poi_id=last_poi.id if last_poi else None,
                depends_on=taxi_depends,
                params={
                    "from_poi_id": first_poi.id if first_poi else None,
                    "to_poi_id": last_poi.id if last_poi else None,
                },
            )
        )
        tasks.append(
            ExecutionTask(
                task_id="task_share_plan",
                action=ExecutionAction.SHARE_PLAN,
                depends_on=[task.task_id for task in tasks],
                params={"channel": "mock_card"},
            )
        )
        return tasks
