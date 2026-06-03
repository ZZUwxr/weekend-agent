from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.decider import AgentDecider
from local_explorer_agent.app.agent.react.exceptions import PolicyViolationError
from local_explorer_agent.app.agent.react.executor import ActionExecutor
from local_explorer_agent.app.agent.react.policy import AgentPolicy
from local_explorer_agent.app.agent.react.reducer import StateReducer
from local_explorer_agent.app.agent.react.state import AgentState
from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry
from local_explorer_agent.app.domain.enums import ExecutionAction, PlanState
from local_explorer_agent.app.domain.models import (
    ExecutionTask,
    GroupContext,
    PlanCandidate,
    PlanEvent,
    PlanOutput,
    PlanPatch,
    PlanRevisionSummary,
)
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest, PlanRevisionRequest
from local_explorer_agent.app.domain.validation import PlanValidationResult

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {"completed", "failed", "needs_user_input"}


class ReActAgentRuntime:
    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        decider: AgentDecider,
        policy: AgentPolicy,
        executor: ActionExecutor,
        reducer: StateReducer,
        max_steps: int = 20,
        max_tool_calls: int = 30,
    ) -> None:
        self.tool_registry = tool_registry
        self.decider = decider
        self.policy = policy
        self.executor = executor
        self.reducer = reducer
        self.max_steps = max_steps
        self.max_tool_calls = max_tool_calls
        self.last_state: AgentState | None = None

    async def run(
        self,
        request: PlanPreviewRequest,
        event_emitter: Any | None = None,
    ) -> PlanOutput:
        state = self._init_state(request)
        emitter = event_emitter

        try:
            state = await self._run_state(state, emitter)
        except Exception as exc:
            if emitter:
                await emitter.emit_error(str(exc), state.step_count)
            raise

        self.last_state = state
        plan = self._finalize(state)
        if emitter:
            await emitter.emit_plan_complete(plan)
        return plan

    async def run_from_state(
        self,
        state: AgentState,
        event_emitter: Any | None = None,
    ) -> PlanOutput:
        emitter = event_emitter
        state = state.model_copy(update={"status": "running"})
        try:
            state = await self._run_state(state, emitter)
        except Exception as exc:
            if emitter:
                await emitter.emit_error(str(exc), state.step_count)
            raise

        self.last_state = state
        plan = self._finalize(state)
        if emitter:
            await emitter.emit_plan_complete(plan)
        return plan

    async def run_replan(
        self,
        original_plan: PlanOutput,
        event: PlanEvent,
        event_emitter: Any | None = None,
    ) -> PlanOutput:
        state = self._init_state_for_replan(original_plan, event)
        emitter = event_emitter

        try:
            state = await self._run_state(state, emitter)
        except Exception as exc:
            if emitter:
                await emitter.emit_error(str(exc), state.step_count)
            raise

        self.last_state = state
        plan = self._finalize_replan(state, original_plan)
        if emitter:
            await emitter.emit_plan_complete(plan)
        return plan

    async def run_revision(
        self,
        original_plan: PlanOutput,
        request: PlanRevisionRequest,
        event_emitter: Any | None = None,
    ) -> PlanOutput:
        state = self._init_state_for_revision(original_plan, request)
        emitter = event_emitter
        if emitter:
            await emitter.emit_revision_started(state.step_count, original_plan.session_id)
        try:
            state = await self._run_state(state, emitter)
        except Exception as exc:
            if emitter:
                await emitter.emit_error(str(exc), state.step_count)
            raise

        self.last_state = state
        plan = self._finalize_revision(state, original_plan)
        if emitter:
            await emitter.emit_revision_complete(plan)
            await emitter.emit_plan_complete(plan)
        return plan

    async def _run_state(
        self,
        state: AgentState,
        emitter: Any | None,
    ) -> AgentState:
        for _step in range(self.max_steps):
            action = await self.decide_next_action(state)
            action = self._validate_or_correct_action(action, state)

            if emitter:
                await emitter.emit_action(state.step_count, action)

            observation = await self.executor.execute(action, state)

            if emitter:
                await emitter.emit_observation(state.step_count, observation)

            state = self.reducer.reduce(state, action, observation)

            if emitter:
                await emitter.emit_state_updated(state.step_count, state)

            if state.status in _TERMINAL_STATUSES:
                break
        return state

    async def decide_next_action(self, state: AgentState) -> AgentAction:
        return await self.decider.decide(state, self.tool_registry.list_specs())

    def _validate_or_correct_action(
        self,
        action: AgentAction,
        state: AgentState,
    ) -> AgentAction:
        try:
            self.policy.validate_action(action, state, self.tool_registry)
            return action
        except PolicyViolationError as exc:
            corrected = self._correct_policy_violation(action, state, str(exc))
            if corrected is None:
                raise
            logger.warning(
                "Correcting policy-violating action %s at step %s: %s -> %s",
                action.action_type,
                state.step_count,
                exc,
                corrected.action_type,
            )
            self.policy.validate_action(corrected, state, self.tool_registry)
            return corrected

    def _correct_policy_violation(
        self,
        action: AgentAction,
        state: AgentState,
        reason: str,
    ) -> AgentAction | None:
        if (
            action.action_type == AgentActionType.ASK_CLARIFICATION
            and "must not include tool_name" in reason
        ):
            return AgentAction(
                action_type=AgentActionType.ASK_CLARIFICATION,
                message=action.message,
                decision_summary=f"移除澄清动作中的工具名：{reason}",
            )

        is_repair_action = action.action_type == AgentActionType.REPAIR_PLAN or (
            action.action_type == AgentActionType.CALL_TOOL and action.tool_name == "repair_plan"
        )

        if not is_repair_action and not state.is_revision and not state.is_replan:
            if state.user_memory is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="read_user_memory",
                    tool_args={
                        "user_id": state.user_id,
                        "companion_ids": state.request.companion_ids,
                    },
                    decision_summary=f"纠偏前补读用户记忆：{reason}",
                )
            if state.requirement_intake is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="intake_user_requirements",
                    tool_args={"query": state.request.query},
                    decision_summary=f"纠偏前补齐需求采集：{reason}",
                )

        should_correct_intake_gate = (
            "read_user_memory" in reason
            or "user_memory" in reason
            or "intake_user_requirements" in reason
            or "missing required slots" in reason
            or "requirement_intake" in reason
        )
        if should_correct_intake_gate and not state.is_revision and not state.is_replan:
            if state.user_memory is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="read_user_memory",
                    tool_args={
                        "user_id": state.user_id,
                        "companion_ids": state.request.companion_ids,
                    },
                    decision_summary=f"规划前补读用户记忆：{reason}",
                )
            if state.requirement_intake is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="intake_user_requirements",
                    tool_args={"query": state.request.query},
                    decision_summary=f"规划前补齐需求采集：{reason}",
                )
            clarification = state.clarification_response
            if (
                clarification is not None
                and clarification.needs_clarification
                and not clarification.can_continue_with_assumptions
                and not state.clarification_answers
            ):
                message = "；".join(question.question for question in clarification.questions[:3])
                return AgentAction(
                    action_type=AgentActionType.ASK_CLARIFICATION,
                    message=message,
                    decision_summary=f"规划前先等待用户补充关键信息：{reason}",
                )

        if "optional clarification" in reason:
            return _next_planning_action_after_optional_clarification(state, reason)

        if "detect_conflicts" in reason:
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="detect_conflicts",
                decision_summary=f"继续规划前补齐冲突检测：{reason}",
            )

        if "generate_negotiation_strategy" in reason:
            if state.conflicts:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="generate_negotiation_strategy",
                    decision_summary=f"存在角色冲突，先生成协商策略：{reason}",
                )
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="draft_experience_plan",
                decision_summary=f"无角色冲突，跳过协商策略并继续生成方案：{reason}",
            )

        if is_repair_action:
            if not state.candidate_plans:
                return None
            if state.validation_result is None:
                return AgentAction(
                    action_type=AgentActionType.VALIDATE_PLAN,
                    decision_summary=f"修复前补齐方案校验：{reason}",
                )
            validation = state.validation_result
            if isinstance(validation, PlanValidationResult) and (
                not validation.passed or validation.blocking_violations
            ):
                return AgentAction(
                    action_type=AgentActionType.FAIL,
                    message="修复次数已用完，当前方案仍有阻塞性约束。",
                    decision_summary=f"修复预算耗尽，终止继续修复：{reason}",
                )
            if not state.scoring_completed or not state.recommended_plan_id:
                return AgentAction(
                    action_type=AgentActionType.SCORE_PLAN,
                    decision_summary=f"无需继续修复，改为补齐评分推荐：{reason}",
                )
            return AgentAction(
                action_type=AgentActionType.FINAL_ANSWER,
                decision_summary=f"无需继续修复，输出最终方案：{reason}",
            )

        if action.action_type != AgentActionType.FINAL_ANSWER:
            return None

        if not state.candidate_plans:
            return None

        if not state.is_revision and not state.is_replan:
            if state.user_memory is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="read_user_memory",
                    tool_args={
                        "user_id": state.user_id,
                        "companion_ids": state.request.companion_ids,
                    },
                    decision_summary=f"最终输出前补读用户记忆：{reason}",
                )
            if state.requirement_intake is None:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="intake_user_requirements",
                    tool_args={"query": state.request.query},
                    decision_summary=f"最终输出前补齐需求采集：{reason}",
                )

        if _has_unselected_stage(state):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="select_places",
                tool_args={"city": state.request.city},
                decision_summary=f"最终输出前补齐地点选择：{reason}",
            )

        if any(_candidate_needs_route(candidate) for candidate in state.candidate_plans):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="calculate_routes",
                decision_summary=f"最终输出前补齐路线计算：{reason}",
            )

        if any(not candidate.timeline for candidate in state.candidate_plans):
            if state.is_revision:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="rebuild_timeline",
                    tool_args={"target_plan_id": state.revision_target_plan_id},
                    decision_summary=f"最终输出前补齐修订后的时间线：{reason}",
                )
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="build_timeline",
                decision_summary=f"最终输出前补齐时间线：{reason}",
            )

        validation = state.validation_result
        if validation is None:
            return AgentAction(
                action_type=AgentActionType.VALIDATE_PLAN,
                decision_summary=f"补齐最终输出前的方案校验：{reason}",
            )

        if isinstance(validation, PlanValidationResult) and (
            not validation.passed or validation.blocking_violations
        ):
            if (
                validation.blocking_violations
                and state.repair_count < self.policy.max_repair_attempts
            ):
                return AgentAction(
                    action_type=AgentActionType.REPAIR_PLAN,
                    decision_summary=f"最终输出前先修复阻塞性约束：{reason}",
                )
            return AgentAction(
                action_type=AgentActionType.FAIL,
                message="方案仍有阻塞性约束，暂时无法安全输出最终方案。",
                decision_summary=f"阻塞性约束未修复，终止输出：{reason}",
            )

        candidate_ids = {candidate.plan_id for candidate in state.candidate_plans}
        if (
            not state.scoring_completed
            or not state.recommended_plan_id
            or state.recommended_plan_id not in candidate_ids
        ):
            if state.inferred_context is None:
                req = state.request
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="understand_user",
                    tool_args={
                        "user_query": req.query,
                        "user_id": req.user_id,
                        "city": req.city,
                        "start_time": req.start_time.isoformat(),
                        "duration_minutes": req.duration_minutes,
                    },
                    decision_summary=f"评分前补齐用户理解结果：{reason}",
                )
            return AgentAction(
                action_type=AgentActionType.SCORE_PLAN,
                decision_summary=f"补齐最终输出前的评分推荐：{reason}",
            )

        if state.requirement_intake is None:
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="intake_user_requirements",
                tool_args={"query": state.request.query},
                decision_summary=f"最终输出前补齐需求采集：{reason}",
            )

        clarification = state.clarification_response
        if (
            clarification is not None
            and clarification.needs_clarification
            and not clarification.can_continue_with_assumptions
            and not state.clarification_answers
        ):
            message = "；".join(question.question for question in clarification.questions[:3])
            return AgentAction(
                action_type=AgentActionType.ASK_CLARIFICATION,
                message=message,
                decision_summary=f"最终输出前先等待用户补充关键信息：{reason}",
            )

        return None

    def _init_state(self, request: PlanPreviewRequest) -> AgentState:
        return AgentState(
            session_id=f"sess_{uuid4().hex[:12]}",
            user_id=request.user_id,
            request=request,
            goal=request.query,
        )

    def _init_state_for_replan(self, original_plan: PlanOutput, event: PlanEvent) -> AgentState:
        request = PlanPreviewRequest(
            user_id=original_plan.user_id,
            query=original_plan.input_query,
            city="深圳",
            start_time=_infer_plan_start_time(original_plan),
            duration_minutes=240,
        )
        return AgentState(
            session_id=original_plan.session_id,
            user_id=original_plan.user_id,
            request=request,
            goal=f"replan due to {event.event_type}",
            inferred_context=original_plan.inferred_context,
            conflicts=original_plan.conflicts,
            negotiation_strategies=original_plan.negotiation_strategies,
            candidate_plans=[c.model_copy(deep=True) for c in original_plan.plan_candidates],
            recommended_plan_id=original_plan.recommended_plan_id,
            execution_graph=[t.model_copy(deep=True) for t in original_plan.execution_graph],
            is_replan=True,
            original_plan=original_plan,
            trigger_event=event,
        )

    def _init_state_for_revision(
        self,
        original_plan: PlanOutput,
        request: PlanRevisionRequest,
    ) -> AgentState:
        preview_request = PlanPreviewRequest(
            user_id=original_plan.user_id,
            query=f"{original_plan.input_query}\n用户修改意见：{request.message}",
            city="深圳",
            start_time=_infer_plan_start_time(original_plan),
            duration_minutes=240,
        )
        return AgentState(
            session_id=original_plan.session_id,
            user_id=original_plan.user_id,
            request=preview_request,
            goal=f"revise plan: {request.message}",
            inferred_context=original_plan.inferred_context,
            conflicts=original_plan.conflicts,
            negotiation_strategies=original_plan.negotiation_strategies,
            candidate_plans=[c.model_copy(deep=True) for c in original_plan.plan_candidates],
            recommended_plan_id=original_plan.recommended_plan_id,
            execution_graph=[t.model_copy(deep=True) for t in original_plan.execution_graph],
            assumptions=[*original_plan.assumptions],
            is_revision=True,
            revision_instruction=request.message,
            revision_target_plan_id=request.target_plan_id,
            revision_mode=request.revision_mode,
            locked_items=request.locked_items,
            original_plan=original_plan,
        )

    def _finalize(self, state: AgentState) -> PlanOutput:
        if not state.candidate_plans:
            logger.warning("No candidate plans produced for session %s", state.session_id)
            return PlanOutput(
                session_id=state.session_id,
                user_id=state.user_id,
                input_query=state.request.query,
                inferred_context=state.inferred_context or GroupContext(),
                conflicts=state.conflicts,
                negotiation_strategies=state.negotiation_strategies,
                plan_candidates=[],
                recommended_plan_id="",
                state=(
                    PlanState.CLARIFYING if state.status == "needs_user_input" else PlanState.FAILED
                ),
                assumptions=state.assumptions,
                clarification=state.clarification_response,
            )

        recommended_id = state.recommended_plan_id
        candidate_ids = {candidate.plan_id for candidate in state.candidate_plans}
        if not recommended_id or recommended_id not in candidate_ids:
            recommended_id = state.candidate_plans[0].plan_id
            logger.warning("No recommended_plan_id set, defaulting to %s", recommended_id)

        exec_graph = state.execution_graph
        if not exec_graph:
            recommended = next(
                (c for c in state.candidate_plans if c.plan_id == recommended_id),
                state.candidate_plans[0],
            )
            exec_graph = self._build_execution_graph(recommended)

        plan_candidates = _enrich_diet_tradeoffs(state.candidate_plans, state, recommended_id)
        assumptions = _enrich_diet_assumptions(state.assumptions, state, plan_candidates, recommended_id)
        assumptions = _enrich_memory_assumptions(assumptions, state)
        assumptions = _enrich_fallback_assumptions(assumptions, state)

        return PlanOutput(
            session_id=state.session_id,
            user_id=state.user_id,
            input_query=state.request.query,
            inferred_context=state.inferred_context or GroupContext(),
            conflicts=state.conflicts,
            negotiation_strategies=state.negotiation_strategies,
            plan_candidates=plan_candidates,
            recommended_plan_id=recommended_id,
            execution_graph=exec_graph,
            state=PlanState.FAILED if state.status == "failed" else PlanState.PREVIEW,
            share_message=f"我为你准备了 {recommended_id}，确认后可以执行预约、叫车和分享任务。",
            assumptions=assumptions,
            clarification=state.clarification_response,
            revision_summary=state.revision_summary,
        )

    def _finalize_replan(self, state: AgentState, original_plan: PlanOutput) -> PlanOutput:
        base = self._finalize(state)
        base.plan_version = original_plan.plan_version + 1
        base.state = original_plan.state
        base.share_message = original_plan.share_message
        if state.trigger_event:
            base.replan_reason = f"事件 {state.trigger_event.event_type} 触发重新规划"
        return base

    def _finalize_revision(
        self,
        state: AgentState,
        original_plan: PlanOutput,
    ) -> PlanOutput:
        base = self._finalize(state)
        base.plan_version = original_plan.plan_version + 1
        base.state = PlanState.PREVIEW
        base.revision_summary = state.revision_summary or _fallback_revision_summary(state)
        base.share_message = "已根据你的修改意见更新方案，确认后再执行预约、叫车和分享任务。"
        return base

    def _build_execution_graph(self, recommended) -> list[ExecutionTask]:
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
                        requires_user_confirmation=True,
                        preconditions=["plan_confirmed"],
                        human_readable_confirmation=f"预订餐厅: {poi.name}",
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
                        requires_user_confirmation=True,
                        preconditions=["plan_confirmed"],
                        human_readable_confirmation=f"预订活动: {poi.name}",
                    )
                )

        selected_pois = [stage.selected_poi for stage in recommended.stages if stage.selected_poi]
        if len(selected_pois) >= 2:
            first_poi = selected_pois[0]
            last_poi = selected_pois[-1]
            taxi_depends = [t.task_id for t in tasks]
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
                    requires_user_confirmation=True,
                    preconditions=["plan_confirmed"],
                    human_readable_confirmation="呼叫出租车回家",
                )
            )
        if len(recommended.stages) >= 2 and tasks:
            tasks.append(
                ExecutionTask(
                    task_id="task_share_plan",
                    action=ExecutionAction.SHARE_PLAN,
                    depends_on=[t.task_id for t in tasks],
                    params={"channel": "mock_card"},
                    requires_user_confirmation=True,
                    preconditions=["plan_confirmed"],
                    human_readable_confirmation="分享行程给家人",
                )
            )
        return tasks


def _fallback_revision_summary(state: AgentState) -> PlanRevisionSummary | None:
    if not state.revision_patches:
        if state.warnings:
            return PlanRevisionSummary(
                summary="已检查修改意见，但没有找到需要调整的对应环节。",
                patches=[],
                unchanged_items=state.locked_items,
                warnings=state.warnings,
            )
        return None
    return PlanRevisionSummary(
        summary=_summarize_revision_patches(state.revision_patches),
        patches=state.revision_patches,
        unchanged_items=state.locked_items,
        warnings=state.warnings,
    )


def _summarize_revision_patches(patches: list[PlanPatch]) -> str:
    parts: list[str] = []
    for patch in patches:
        new_value = patch.new_value or {}
        old_value = patch.old_value or {}
        new_name = str(new_value.get("name") or new_value.get("stage_name") or "新地点")
        old_name = str(old_value.get("name") or "")
        category = str(new_value.get("category") or "")
        requested = str(new_value.get("requested_category") or category)
        reason = patch.reason.strip("。") if patch.reason else ""

        if patch.patch_type == "add_dining_stage":
            text = f"已新增{_dining_label(requested, category)}：{new_name}"
        elif patch.patch_type == "replace_dining_stage":
            label = _dining_label(requested, category)
            if old_name:
                text = f"已把晚饭从「{old_name}」换成{label}「{new_name}」"
            else:
                text = f"已把晚饭换成{label}「{new_name}」"
        elif patch.patch_type == "add_followup_stage":
            label = requested or category or "后续活动"
            anchor_text = _anchor_summary_label(str(new_value.get("anchor") or "after_last"))
            text = f"已在{anchor_text}新增{label}：{new_name}"
        elif patch.patch_type == "replace_followup_stage":
            label = requested or category or "后续活动"
            old_category = str(old_value.get("category") or "")
            if old_name:
                if old_category and old_category != label:
                    text = f"已把饭后{old_category}从「{old_name}」换成{label}「{new_name}」"
                else:
                    text = f"已把饭后{label}从「{old_name}」换成「{new_name}」"
            else:
                text = f"已把饭后{label}换成「{new_name}」"
        elif patch.patch_type == "remove_followup_stage":
            label = str(
                old_value.get("requested_category") or old_value.get("category") or "后续活动"
            )
            if old_name:
                text = f"已取消{label}：「{old_name}」"
            else:
                text = f"已取消{label}后续环节"
        else:
            text = f"已根据你的意见局部调整：{new_name}"

        if reason:
            text = f"{text}。原因：{reason}"
        parts.append(text)
    return "；".join(parts)


def _dining_label(requested_category: str, actual_category: str) -> str:
    if requested_category and requested_category not in {"餐厅", "吃饭", "用餐", "都可以"}:
        if actual_category and actual_category != requested_category:
            return f"{requested_category}方向的{actual_category}晚饭"
        return f"{requested_category}晚饭"
    if actual_category and actual_category != "餐厅":
        return f"{actual_category}晚饭"
    return "晚饭"


def _anchor_summary_label(anchor: str) -> str:
    if anchor == "before_dining":
        return "用餐前"
    if anchor == "after_dining":
        return "饭后"
    return "行程末尾"


_DIET_KEYWORDS = ("减肥", "减脂", "低卡", "低热量", "清淡", "控糖", "健身")
_HIGH_CALORIE_CATEGORIES = {"火锅", "烧烤", "烤肉"}
_DIET_BBQ_NOTICE = "提醒：同行人有减脂/低卡偏好，烧烤环节建议优先选择清淡烤物、少油少酱，并在前后安排轻松补偿。"


def _enrich_diet_tradeoffs(
    candidates: list[PlanCandidate],
    state: AgentState,
    recommended_id: str | None,
) -> list[PlanCandidate]:
    if not _request_has_diet_need(state):
        return candidates
    enriched: list[PlanCandidate] = []
    for candidate in candidates:
        if candidate.plan_id != recommended_id or not _candidate_has_high_calorie_dining(candidate):
            enriched.append(candidate)
            continue
        combined_text = " ".join(
            text
            for text in (
                candidate.tradeoff_summary,
                candidate.recommendation_reason,
            )
            if text
        )
        if any(keyword in combined_text for keyword in _DIET_KEYWORDS) or "补偿" in combined_text:
            enriched.append(candidate)
            continue
        suffix = _DIET_BBQ_NOTICE
        separator = " " if candidate.tradeoff_summary else ""
        enriched.append(candidate.model_copy(
            update={"tradeoff_summary": f"{candidate.tradeoff_summary}{separator}{suffix}"}
        ))
    return enriched


def _enrich_diet_assumptions(
    assumptions: list[str],
    state: AgentState,
    candidates: list[PlanCandidate],
    recommended_id: str | None,
) -> list[str]:
    if not _request_has_diet_need(state):
        return assumptions
    recommended = next(
        (candidate for candidate in candidates if candidate.plan_id == recommended_id),
        candidates[0] if candidates else None,
    )
    if recommended is None or not _candidate_has_high_calorie_dining(recommended):
        return assumptions
    if any(any(keyword in item for keyword in _DIET_KEYWORDS) for item in assumptions):
        return assumptions
    return [*assumptions, _DIET_BBQ_NOTICE]


def _enrich_memory_assumptions(assumptions: list[str], state: AgentState) -> list[str]:
    memory = state.user_memory
    if memory is None:
        return assumptions

    has_memory_signal = any(
        (
            memory.likes,
            memory.dislikes,
            memory.category_weights,
            memory.tag_weights,
            memory.liked_poi_ids,
            memory.disliked_poi_ids,
            memory.companions,
        )
    )
    if not has_memory_signal:
        return assumptions

    note = "已参考你的历史偏好和反馈；当前输入中的明确要求优先。"
    if note in assumptions:
        return assumptions
    return [*assumptions, note]


def _enrich_fallback_assumptions(assumptions: list[str], state: AgentState) -> list[str]:
    fallback_warnings = [warning for warning in state.warnings if "规则兜底" in warning]
    if not fallback_warnings:
        return assumptions
    note = "部分规划步骤在模型响应不稳定时使用规则兜底，方案已继续完成校验。"
    if note in assumptions:
        return assumptions
    return [*assumptions, note]


def _request_has_diet_need(state: AgentState) -> bool:
    parts: list[str] = [state.request.query]
    if state.revision_instruction:
        parts.append(state.revision_instruction)
    if state.inferred_context is not None:
        ctx = state.inferred_context
        parts.extend([ctx.input_query, *ctx.inferred_constraints])
        for role in ctx.roles:
            parts.extend(
                role.hard_constraints
                + role.soft_preferences
                + role.hidden_needs
                + role.risk_points
            )
    return any(keyword in str(part) for part in parts for keyword in _DIET_KEYWORDS)


def _candidate_has_high_calorie_dining(candidate: PlanCandidate) -> bool:
    for stage in candidate.stages:
        poi = stage.selected_poi
        if poi is None:
            continue
        if str(stage.stage_type) == "dine" and poi.category in _HIGH_CALORIE_CATEGORIES:
            return True
    return False


def _next_planning_action_after_optional_clarification(
    state: AgentState,
    reason: str,
) -> AgentAction | None:
    req = state.request
    if state.inferred_context is None:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="understand_user",
            tool_args={
                "user_query": req.query,
                "user_id": req.user_id,
                "city": req.city,
                "start_time": req.start_time.isoformat(),
                "duration_minutes": req.duration_minutes,
            },
            decision_summary=f"跳过非必填澄清，继续理解用户需求：{reason}",
        )
    if not _conflict_detection_done(state):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="detect_conflicts",
            decision_summary=f"跳过非必填澄清，继续检测冲突：{reason}",
        )
    if state.conflicts and not _negotiation_done(state):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="generate_negotiation_strategy",
            decision_summary=f"跳过非必填澄清，继续生成协商策略：{reason}",
        )
    if not state.candidate_plans:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="draft_experience_plan",
            decision_summary=f"跳过非必填澄清，继续生成候选方案：{reason}",
        )
    if any(
        stage.selected_poi is None
        for candidate in state.candidate_plans
        for stage in candidate.stages
    ):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="select_places",
            tool_args={"city": req.city},
            decision_summary=f"跳过非必填澄清，继续选择地点：{reason}",
        )
    if any(_candidate_needs_route(candidate) for candidate in state.candidate_plans):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="calculate_routes",
            decision_summary=f"跳过非必填澄清，继续计算路线：{reason}",
        )
    if any(not candidate.timeline for candidate in state.candidate_plans):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="build_timeline",
            decision_summary=f"跳过非必填澄清，继续构建时间线：{reason}",
        )
    if state.validation_result is None:
        return AgentAction(
            action_type=AgentActionType.VALIDATE_PLAN,
            decision_summary=f"跳过非必填澄清，继续校验方案：{reason}",
        )
    if not state.scoring_completed:
        return AgentAction(
            action_type=AgentActionType.SCORE_PLAN,
            decision_summary=f"跳过非必填澄清，继续评分推荐：{reason}",
        )
    return AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary=f"跳过非必填澄清，输出最终方案：{reason}",
    )


def _tool_succeeded(state: AgentState, tool_name: str) -> bool:
    return any(
        observation.tool_name == tool_name and observation.success
        for observation in state.observations
    )


def _conflict_detection_done(state: AgentState) -> bool:
    return bool(state.conflicts) or _tool_succeeded(state, "detect_conflicts")


def _negotiation_done(state: AgentState) -> bool:
    return bool(state.negotiation_strategies) or _tool_succeeded(
        state,
        "generate_negotiation_strategy",
    )


def _candidate_needs_route(candidate) -> bool:
    selected_poi_count = sum(1 for stage in candidate.stages if stage.selected_poi is not None)
    return selected_poi_count >= 2 and not candidate.route_segments


def _has_unselected_stage(state: AgentState) -> bool:
    return any(
        stage.selected_poi is None
        for candidate in state.candidate_plans
        for stage in candidate.stages
    )


def _infer_plan_start_time(plan: PlanOutput):
    recommended = next(
        (
            candidate
            for candidate in plan.plan_candidates
            if candidate.plan_id == plan.recommended_plan_id
        ),
        plan.plan_candidates[0] if plan.plan_candidates else None,
    )
    if recommended and recommended.timeline:
        first_time = recommended.timeline[0].time
        try:
            hour_text, minute_text = first_time.split(":", 1)
            return plan.created_at.replace(
                hour=int(hour_text),
                minute=int(minute_text[:2]),
                second=0,
                microsecond=0,
            )
        except (ValueError, AttributeError):
            pass
    return plan.created_at
