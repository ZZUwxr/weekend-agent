from collections.abc import Callable
from typing import Any

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
from local_explorer_agent.app.domain.schemas import (
    PlanPreviewRequest,
    PlanPreviewStreamEvent,
    PlanPreviewStreamEventType,
)
from local_explorer_agent.app.domain.scoring import choose_recommended_candidate, score_candidate

PlanPreviewEventCallback = Callable[[PlanPreviewStreamEvent], None]

_STEP_META: dict[int, tuple[str, str]] = {
    1: ("user_understanding", "识别用户意图"),
    2: ("conflict_detection", "识别群体冲突"),
    3: ("negotiation", "生成协商策略"),
    4: ("experience_planning", "生成体验骨架"),
    5: ("place_selection", "选择主备地点"),
    6: ("routing", "规划转场路线"),
    7: ("timeline_builder", "生成时间轴"),
    8: ("scoring_recommendation", "评分与推荐"),
}


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

    def preview_plan(
        self,
        request: PlanPreviewRequest,
        event_callback: PlanPreviewEventCallback | None = None,
    ) -> PlanOutput:
        current_step = 0
        try:
            current_step = 1
            self._emit_step_start(current_step, event_callback)
            group_context = self.user_understanding_skill.run(
                user_query=request.query,
                user_id=request.user_id,
                city=request.city,
                start_time=request.start_time,
                duration_minutes=request.duration_minutes,
            )
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "group_type": group_context.group_type,
                    "group_size": group_context.group_size,
                    "scene_label": group_context.scene_label,
                    "role_ids": [role.role_id for role in group_context.roles],
                    "constraints_count": len(group_context.inferred_constraints),
                    "clarification_questions_count": len(
                        group_context.clarification_questions
                    ),
                },
            )

            current_step = 2
            self._emit_step_start(current_step, event_callback)
            conflicts = self.conflict_detection_skill.run(group_context)
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "conflicts_count": len(conflicts),
                    "conflict_ids": [conflict.conflict_id for conflict in conflicts],
                    "max_severity": max(
                        (conflict.severity for conflict in conflicts),
                        default=0,
                    ),
                },
            )

            current_step = 3
            self._emit_step_start(current_step, event_callback)
            strategies = self.negotiation_skill.run(
                group_context=group_context,
                conflicts=conflicts,
            )
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "strategies_count": len(strategies),
                    "strategy_types": [strategy.strategy_type for strategy in strategies],
                },
            )

            current_step = 4
            self._emit_step_start(current_step, event_callback)
            candidates = self.experience_planning_skill.run(
                group_context=group_context,
                conflicts=conflicts,
                negotiation_strategies=strategies,
            )
            self._emit_step_complete(
                current_step,
                event_callback,
                {"candidates": [self._candidate_summary(candidate) for candidate in candidates]},
            )

            current_step = 5
            self._emit_step_start(current_step, event_callback)
            selected_candidates: list[PlanCandidate] = []
            for index, candidate in enumerate(candidates):
                self._emit_candidate_start(index, candidate, event_callback)
                selected_candidates.append(
                    self.place_selection_skill.run(
                        candidate=candidate,
                        group_context=group_context,
                        city=request.city,
                        event_callback=event_callback,
                    )
                )
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "candidates": [
                        self._selection_summary(candidate)
                        for candidate in selected_candidates
                    ]
                },
            )

            current_step = 6
            self._emit_step_start(current_step, event_callback)
            routed_candidates = [
                self.routing_skill.run(candidate, event_callback=event_callback)
                for candidate in selected_candidates
            ]
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "candidates": [
                        {
                            "plan_id": candidate.plan_id,
                            "route_segments_count": len(candidate.route_segments),
                        }
                        for candidate in routed_candidates
                    ]
                },
            )

            current_step = 7
            self._emit_step_start(current_step, event_callback)
            timed_candidates = [
                self.timeline_builder_skill.run(
                    candidate=candidate,
                    start_time=request.start_time,
                    duration_minutes=request.duration_minutes,
                )
                for candidate in routed_candidates
            ]
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "candidates": [
                        {
                            "plan_id": candidate.plan_id,
                            "timeline_items_count": len(candidate.timeline),
                        }
                        for candidate in timed_candidates
                    ]
                },
            )

            current_step = 8
            self._emit_step_start(current_step, event_callback)
            enriched_candidates: list[PlanCandidate] = []
            for index, candidate in enumerate(timed_candidates):
                scored = score_candidate(candidate, group_context)
                enriched_candidates.append(scored)
                self._emit_candidate_complete(index, scored, event_callback)

            recommended = choose_recommended_candidate(enriched_candidates)
            recommended.recommendation_reason = (
                "该方案不是简单平均分最高，而是在 overall_score、min_role_score、fairness_score "
                "之间更均衡，能避免某个角色被明显牺牲，并保留局部备选点。"
            )
            recommended.tradeoff_summary = "优先控制距离、排队和饮食冲突，牺牲少量新奇感换稳定性。"
            execution_graph = self._build_execution_graph(recommended)
            self._emit_step_complete(
                current_step,
                event_callback,
                {
                    "recommended_plan_id": recommended.plan_id,
                    "recommended_title": recommended.title,
                    "execution_tasks_count": len(execution_graph),
                    "scores": {
                        "overall_score": recommended.overall_score,
                        "min_role_score": recommended.min_role_score,
                        "fairness_score": recommended.fairness_score,
                    },
                },
            )

            plan = PlanOutput(
                user_id=request.user_id,
                input_query=request.query,
                inferred_context=group_context,
                conflicts=conflicts,
                negotiation_strategies=strategies,
                plan_candidates=enriched_candidates,
                recommended_plan_id=recommended.plan_id,
                execution_graph=execution_graph,
                share_message=(
                    f"我为你们做了一个{recommended.title}："
                    "先照顾孩子，再自然安排轻食，最后轻松收尾。"
                ),
            )
            saved = self.session_store.save(plan)
            self._emit(
                event_callback,
                "plan_complete",
                {
                    "session_id": saved.session_id,
                    "recommended_plan_id": saved.recommended_plan_id,
                    "candidates_count": len(saved.plan_candidates),
                },
            )
            return saved
        except Exception as exc:
            self._emit(
                event_callback,
                "error",
                {"step": current_step or None, "error": str(exc)},
            )
            raise

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

    def _emit_step_start(
        self,
        step: int,
        event_callback: PlanPreviewEventCallback | None,
    ) -> None:
        name, label = _STEP_META[step]
        self._emit(
            event_callback,
            "step_start",
            {"step": step, "name": name, "label": label},
        )

    def _emit_step_complete(
        self,
        step: int,
        event_callback: PlanPreviewEventCallback | None,
        result: dict[str, Any],
    ) -> None:
        name, label = _STEP_META[step]
        self._emit(
            event_callback,
            "step_complete",
            {"step": step, "name": name, "label": label, "result": result},
        )

    def _emit_candidate_start(
        self,
        candidate_index: int,
        candidate: PlanCandidate,
        event_callback: PlanPreviewEventCallback | None,
    ) -> None:
        self._emit(
            event_callback,
            "candidate_start",
            {
                "candidate_index": candidate_index,
                "plan_type": candidate.plan_type,
                "title": candidate.title,
            },
        )

    def _emit_candidate_complete(
        self,
        candidate_index: int,
        candidate: PlanCandidate,
        event_callback: PlanPreviewEventCallback | None,
    ) -> None:
        self._emit(
            event_callback,
            "candidate_complete",
            {
                "candidate_index": candidate_index,
                "plan_type": candidate.plan_type,
                "title": candidate.title,
                "overall_score": candidate.overall_score,
                "min_role_score": candidate.min_role_score,
                "fairness_score": candidate.fairness_score,
            },
        )

    def _candidate_summary(self, candidate: PlanCandidate) -> dict[str, Any]:
        return {
            "plan_id": candidate.plan_id,
            "plan_type": candidate.plan_type,
            "title": candidate.title,
            "stage_count": len(candidate.stages),
            "stage_ids": [stage.stage_id for stage in candidate.stages],
        }

    def _selection_summary(self, candidate: PlanCandidate) -> dict[str, Any]:
        return {
            "plan_id": candidate.plan_id,
            "selected_poi_ids": [
                stage.selected_poi.id for stage in candidate.stages if stage.selected_poi
            ],
            "fallback_pois_count": sum(len(stage.fallback_pois) for stage in candidate.stages),
        }

    def _emit(
        self,
        event_callback: PlanPreviewEventCallback | None,
        event: PlanPreviewStreamEventType,
        data: dict[str, Any],
    ) -> None:
        if event_callback is None:
            return
        event_callback(PlanPreviewStreamEvent(event=event, data=data))
