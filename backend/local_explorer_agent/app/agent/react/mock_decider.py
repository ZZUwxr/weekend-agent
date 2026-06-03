"""Deterministic mock decider for local tests and fallback mode."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.validation import PlanValidationResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.react.tool_registry import ToolSpec


class MockReActDecider:
    """Rule-based decider; this is a stable fallback, not the real LLM policy."""

    async def decide(
        self,
        state: AgentState,
        tools: list[ToolSpec],
    ) -> AgentAction:
        req = state.request
        settings = get_settings()

        # Replan mode: skip understand/conflicts/strategies/draft, go to repair or validate
        if state.is_revision:
            return self._decide_revision(state)

        if state.is_replan:
            return self._decide_replan(state, settings)

        if state.user_memory is None and not _tool_attempted(state, "read_user_memory"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="read_user_memory",
                tool_args={
                    "user_id": req.user_id,
                    "companion_ids": req.companion_ids,
                },
                decision_summary="读取用户长期记忆，用于后续偏好和同行人约束判断",
            )

        # 0. Intake user requirements before planning. This detects whether the
        # user wants one activity or several, and may produce clarification.
        if state.requirement_intake is None:
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="intake_user_requirements",
                tool_args={"query": req.query},
                decision_summary="先采集并结构化用户需求，明确活动数量和关键缺失信息",
            )

        if _required_clarification_pending(state):
            return AgentAction(
                action_type=AgentActionType.ASK_CLARIFICATION,
                message=_clarification_message(state),
                decision_summary="需求采集发现关键槽位缺失，先请求澄清",
            )

        # 1. Understand user
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
                decision_summary="步骤1: 解析用户意图，推断群体构成",
            )

        # 2. Detect conflicts
        if not _conflict_detection_done(state):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="detect_conflicts",
                decision_summary="步骤2: 检测群体内潜在冲突",
            )

        # 3. Generate negotiation strategies only when conflicts exist.
        if state.conflicts and not _negotiation_done(state):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="generate_negotiation_strategy",
                decision_summary="步骤3: 为冲突生成协商策略",
            )

        # 4. Draft experience plans
        if not state.candidate_plans:
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="draft_experience_plan",
                decision_summary="步骤4: 生成候选体验方案",
            )

        # 5. Select places (check if any stage lacks selected_poi)
        if any(
            stage.selected_poi is None
            for candidate in state.candidate_plans
            for stage in candidate.stages
        ):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="select_places",
                tool_args={"city": req.city},
                decision_summary="步骤5: 为各阶段选择合适的 POI 地点",
            )

        # 6. Calculate routes
        if any(_needs_route(candidate) for candidate in state.candidate_plans):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="calculate_routes",
                decision_summary="步骤6: 计算 POI 间转场路线",
            )

        # 7. Build timeline
        if any(not candidate.timeline for candidate in state.candidate_plans):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="build_timeline",
                decision_summary="步骤7: 构建详细时间轴",
            )

        # 8. Validate plan constraints
        if state.validation_result is None:
            return AgentAction(
                action_type=AgentActionType.VALIDATE_PLAN,
                decision_summary="步骤8: 校验候选方案约束（安全、距离、时间等）",
            )

        # 9. Repair if blocking violations exist and repair budget allows
        vr = state.validation_result
        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count < settings.agent_max_repair_attempts
        ):
            summary = (
                f"步骤9: 修复 {len(vr.blocking_violations)} 个阻塞性违规"
                f"（第 {state.repair_count + 1} 次修复）"
            )
            return AgentAction(
                action_type=AgentActionType.REPAIR_PLAN,
                decision_summary=summary,
            )

        # 10. Re-validate after repair
        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count >= settings.agent_max_repair_attempts
        ):
            message = (
                f"修复 {settings.agent_max_repair_attempts} 次后仍有阻塞性违规，无法生成有效方案"
            )
            return AgentAction(
                action_type=AgentActionType.FAIL,
                message=message,
                decision_summary="步骤10: 修复次数耗尽，标记失败",
            )

        # 11. Score candidates
        if not state.scoring_completed:
            return AgentAction(
                action_type=AgentActionType.SCORE_PLAN,
                decision_summary="步骤11: 评分并选择推荐方案",
            )

        # 12. Final answer
        return AgentAction(
            action_type=AgentActionType.FINAL_ANSWER,
            decision_summary="所有步骤完成，输出最终方案",
        )

    def _decide_revision(self, state: AgentState) -> AgentAction:
        """Revision path: interpret → optional facts → patch → validate → score → explain."""
        message = state.revision_instruction or ""

        if not _tool_succeeded(state, "interpret_revision_request"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                tool_args={
                    "message": message,
                    "target_plan_id": state.revision_target_plan_id,
                    "revision_mode": state.revision_mode,
                },
                decision_summary="解析用户修改意见，提取 revision intents",
            )

        if "avoid_queue" in state.revision_intents and not _tool_succeeded(state, "queue_lookup"):
            poi_id = _first_unlocked_poi_id(state)
            if poi_id:
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="queue_lookup",
                    tool_args={"poi_id": poi_id},
                    decision_summary="用户不想排队，先查询目标地点排队风险",
                )

        is_cancel_followup_revision = _needs_cancel_followup_revision(message)
        if is_cancel_followup_revision and not _tool_succeeded(state, "remove_followup_stage"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="remove_followup_stage",
                tool_args={
                    "target_plan_id": state.revision_target_plan_id,
                    "activity_or_category": _negated_followup_category_from_message(message),
                    "message": message,
                },
                decision_summary="按用户意见取消喝酒、小酒馆等后续环节",
            )

        if is_cancel_followup_revision:
            replacement_followup = _replacement_followup_category_from_message(message)
            if (
                replacement_followup is not None
                and not _tool_succeeded(state, "add_followup_stage")
            ):
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="add_followup_stage",
                    tool_args={
                        "target_plan_id": state.revision_target_plan_id,
                        "activity_or_category": replacement_followup,
                        "anchor": _followup_anchor(message),
                        "mode": "add",
                        "message": message,
                    },
                    decision_summary="取消原后续活动后按用户新偏好新增后续环节",
                )
            dining_category = _dining_replacement_category_from_message(message) or _dining_category_from_message(message)
            if (
                dining_category is not None
                and replacement_followup is None
                and not _tool_succeeded(state, "revise_dining_stage")
            ):
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="revise_dining_stage",
                    tool_args={
                        "target_plan_id": state.revision_target_plan_id,
                        "cuisine_or_category": dining_category,
                        "mode": "replace_or_add",
                        "insert_anchor": "before_dining" if _is_before_dining_message(message) else "default",
                        "message": message,
                    },
                    decision_summary="取消后续活动后按用户新偏好补充餐饮",
                )

        followup_category = None
        is_followup_revision = False
        if not is_cancel_followup_revision:
            followup_category = _followup_revision_category(state, message)
            is_followup_revision = _needs_followup_revision(
                message,
                state.revision_intents,
                followup_category,
            )
        if is_followup_revision and not _tool_succeeded(state, "add_followup_stage"):
            dining_category = _dining_category_from_message(message)
            if (
                dining_category is not None
                and dining_category != followup_category
                and not _explicit_add_followup_around_dining(message)
                and not _tool_succeeded(state, "revise_dining_stage")
            ):
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="revise_dining_stage",
                    tool_args={
                        "target_plan_id": state.revision_target_plan_id,
                        "cuisine_or_category": dining_category,
                        "mode": _dining_revision_mode(message, state.revision_intents),
                        "insert_anchor": "before_dining" if _is_before_dining_message(message) else "default",
                        "message": message,
                    },
                    decision_summary="复合修改中先调整餐饮，再追加饭后活动",
                )

            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="add_followup_stage",
                tool_args={
                    "target_plan_id": state.revision_target_plan_id,
                    "activity_or_category": followup_category,
                    "anchor": _followup_anchor(message),
                    "mode": _followup_revision_mode(message),
                    "message": message,
                },
                decision_summary="按用户意见在饭后新增后续活动",
            )

        is_dining_revision = _needs_dining_revision(message, state.revision_intents)
        if is_dining_revision and not _tool_succeeded(state, "revise_dining_stage"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="revise_dining_stage",
                tool_args={
                    "target_plan_id": state.revision_target_plan_id,
                    "cuisine_or_category": _dining_category_from_message(message),
                    "mode": _dining_revision_mode(message, state.revision_intents),
                    "insert_anchor": "before_dining" if _is_before_dining_message(message) else "default",
                    "message": message,
                },
                decision_summary="按用户意见调整餐饮环节，支持替换或新增晚饭",
            )

        if (
            not is_followup_revision
            and not is_dining_revision
            and not is_cancel_followup_revision
            and not _tool_succeeded(state, "replace_poi")
        ):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="replace_poi",
                tool_args={
                    "target_plan_id": state.revision_target_plan_id,
                    "intents": state.revision_intents,
                    "message": message,
                },
                decision_summary="按用户意见优先做局部 POI patch",
            )

        if not _tool_succeeded(state, "calculate_routes"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="calculate_routes",
                decision_summary="局部替换 POI 后重新计算路线",
            )

        if not _tool_succeeded(state, "rebuild_timeline"):
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="rebuild_timeline",
                tool_args={"target_plan_id": state.revision_target_plan_id},
                decision_summary="局部 patch 后重建时间线",
            )

        if state.validation_result is None:
            return AgentAction(
                action_type=AgentActionType.VALIDATE_PLAN,
                decision_summary="修订后重新校验约束",
            )

        vr = state.validation_result
        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count < get_settings().agent_max_repair_attempts
        ):
            return AgentAction(
                action_type=AgentActionType.REPAIR_PLAN,
                decision_summary="修订后仍有阻塞风险，先修复方案",
            )

        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count >= get_settings().agent_max_repair_attempts
        ):
            return AgentAction(
                action_type=AgentActionType.FAIL,
                message="修订后仍有阻塞性约束，无法安全完成修改",
                decision_summary="修订失败，返回明确原因",
            )

        if not state.scoring_completed:
            return AgentAction(
                action_type=AgentActionType.SCORE_PLAN,
                decision_summary="修订后重新评分推荐",
            )

        if state.revision_summary is None:
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="explain_changes",
                decision_summary="生成修改摘要，说明改动和保留项",
            )

        return AgentAction(
            action_type=AgentActionType.FINAL_ANSWER,
            decision_summary="修订完成，输出更新后的方案",
        )

    def _decide_replan(
        self,
        state: AgentState,
        settings: Any,
    ) -> AgentAction:
        """Replan path: repair → re-validate → score → final."""
        vr = state.validation_result

        # If we have a trigger event but haven't validated yet, validate first
        if vr is None and state.trigger_event is not None:
            return AgentAction(
                action_type=AgentActionType.VALIDATE_PLAN,
                decision_summary="重新规划: 校验变更后的约束",
            )

        # Repair if blocking violations and budget allows
        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count < settings.agent_max_repair_attempts
        ):
            return AgentAction(
                action_type=AgentActionType.REPAIR_PLAN,
                decision_summary=f"重新规划: 修复 {len(vr.blocking_violations)} 个违规",
            )

        # Re-validate after repair if still has violations
        if (
            isinstance(vr, PlanValidationResult)
            and vr.blocking_violations
            and state.repair_count >= settings.agent_max_repair_attempts
        ):
            return AgentAction(
                action_type=AgentActionType.FAIL,
                message=f"重新规划: 修复 {settings.agent_max_repair_attempts} 次后仍有阻塞性违规",
                decision_summary="重新规划: 修复失败",
            )

        # Score if not yet scored
        if not state.scoring_completed:
            return AgentAction(
                action_type=AgentActionType.SCORE_PLAN,
                decision_summary="重新规划: 重新评分",
            )

        # Final answer
        return AgentAction(
            action_type=AgentActionType.FINAL_ANSWER,
            decision_summary="重新规划完成，输出更新后的方案",
        )


def _tool_succeeded(state: AgentState, tool_name: str) -> bool:
    return any(
        observation.tool_name == tool_name and observation.success
        for observation in state.observations
    )


def _tool_attempted(state: AgentState, tool_name: str) -> bool:
    return any(observation.tool_name == tool_name for observation in state.observations)


def _conflict_detection_done(state: AgentState) -> bool:
    return bool(state.conflicts) or _tool_succeeded(state, "detect_conflicts")


def _negotiation_done(state: AgentState) -> bool:
    return bool(state.negotiation_strategies) or _tool_succeeded(
        state,
        "generate_negotiation_strategy",
    )


def _needs_route(candidate: Any) -> bool:
    selected_poi_count = sum(1 for stage in candidate.stages if stage.selected_poi is not None)
    return selected_poi_count >= 2 and not candidate.route_segments


def _required_clarification_pending(state: AgentState) -> bool:
    clarification = state.clarification_response
    if clarification is None or not clarification.needs_clarification:
        return False
    if clarification.can_continue_with_assumptions:
        return False
    if state.clarification_answers:
        return False
    return any(question.required for question in clarification.questions)


def _clarification_message(state: AgentState) -> str:
    clarification = state.clarification_response
    if clarification is None:
        return "我需要再确认几个关键约束。"
    questions = [
        f"{question.question_id}: {question.question}" for question in clarification.questions[:3]
    ]
    return "\n".join(questions)


def _first_unlocked_poi_id(state: AgentState) -> str | None:
    locked = {
        str(item["id"])
        for item in state.locked_items
        if item.get("type") == "poi" and item.get("id")
    }
    target_plan_id = state.revision_target_plan_id or state.recommended_plan_id
    candidates = state.candidate_plans
    preferred = [
        candidate for candidate in candidates if candidate.plan_id == target_plan_id
    ] or candidates
    for candidate in preferred:
        for stage in candidate.stages:
            if stage.selected_poi and stage.selected_poi.id not in locked:
                return stage.selected_poi.id
    return None


def _needs_dining_revision(message: str, intents: list[str]) -> bool:
    if _explicit_add_followup_around_dining(message):
        return False
    if _needs_followup_revision(message, intents, _followup_category_from_message(message)):
        return False
    if "add_dining" in intents or "change_dining" in intents:
        return True
    dining_terms = (
        "晚饭",
        "午饭",
        "晚餐",
        "午餐",
        "吃饭",
        "用餐",
        "桑拿鸡",
        "火锅",
        "粤菜",
        "烧烤",
        "烤肉",
        "日料",
        "西餐",
        "轻食",
    )
    return any(term in message for term in dining_terms)


def _dining_revision_mode(message: str, intents: list[str]) -> str:
    add_terms = ("加晚饭", "加个晚饭", "加一顿", "加顿饭", "新增晚饭", "加吃饭")
    if "add_dining" in intents or any(term in message for term in add_terms):
        return "add"
    return "replace_or_add"


def _dining_category_from_message(message: str) -> str | None:
    replacement = _dining_replacement_category_from_message(message)
    if replacement is not None:
        return replacement
    negated = _negated_dining_categories(message)
    for label, keywords in _DINING_CATEGORY_KEYWORDS:
        if label in negated:
            continue
        if any(keyword in message for keyword in keywords):
            return label
    if negated:
        return "餐厅"
    return None


def _dining_replacement_category_from_message(message: str) -> str | None:
    for marker in ("换成", "改成", "换为", "改为", "加一个", "加个", "新增"):
        if marker not in message:
            continue
        tail = message.split(marker, 1)[1]
        for label, keywords in _DINING_CATEGORY_KEYWORDS:
            if any(keyword in tail for keyword in keywords):
                return label
    return None


_DINING_CATEGORY_KEYWORDS = [
    ("桑拿鸡", ("桑拿鸡",)),
    ("火锅", ("火锅",)),
    ("粤菜", ("粤菜", "早茶", "茶餐厅")),
    ("烧烤", ("烧烤", "烤串")),
    ("烤肉", ("烤肉",)),
    ("日料", ("日料", "寿司", "居酒屋")),
    ("西餐", ("西餐", "牛排", "披萨")),
    ("轻食", ("轻食", "低卡", "清淡")),
    ("咖啡", ("咖啡",)),
    ("甜品", ("甜品", "蛋糕")),
]


def _negated_dining_categories(message: str) -> set[str]:
    return {
        label
        for label, keywords in _DINING_CATEGORY_KEYWORDS
        if any(_keyword_is_negated(message, keyword) for keyword in keywords)
    }


def _keyword_is_negated(message: str, keyword: str) -> bool:
    index = message.find(keyword)
    if index < 0:
        return False
    window = f"{_same_clause_prefix(message[:index])}{keyword}{_same_clause_suffix(message[index + len(keyword):])}"
    return any(
        term in window for term in ("不想", "不吃", "不要", "别吃", "别", "换掉", "去掉", "取消")
    )


def _same_clause_prefix(text: str) -> str:
    for marker in ("，", "。", "；", ";", ",", "了", "吧", "换成", "改成", "换为", "改为"):
        if marker in text:
            text = text.rsplit(marker, 1)[1]
    return text[-8:]


def _same_clause_suffix(text: str) -> str:
    for marker in ("，", "。", "；", ";", ",", "换成", "改成", "换为", "改为"):
        if marker in text:
            text = text.split(marker, 1)[0]
    return text[:6]


def _needs_followup_revision(
    message: str,
    intents: list[str],
    followup_category: str | None,
) -> bool:
    if _needs_cancel_followup_revision(message):
        return False
    if "add_followup_stage" in intents:
        return True
    if followup_category is None:
        return False
    if _explicit_add_followup_around_dining(message):
        return True
    return any(
        term in message
        for term in (
            "饭后",
            "吃完饭",
            "餐后",
            "之后",
            "再安排",
            "安排",
            "换",
            "换个",
            "换一家",
            "换地方",
            "换地点",
            "不要",
            "太吵",
            "太远",
            "安静",
            "近一点",
        )
    )


def _needs_cancel_followup_revision(message: str) -> bool:
    if _negated_followup_category_from_message(message) is not None:
        return True
    return any(
        term in message
        for term in (
            "喝酒取消",
            "酒馆取消",
            "取消喝酒",
            "取消酒馆",
            "不想去喝酒",
            "不去喝酒",
            "不想喝酒",
            "不喝酒",
            "不要喝酒",
            "别去喝酒",
            "别喝酒",
        )
    )


def _followup_revision_mode(message: str) -> str:
    replace_terms = (
        "换",
        "换个",
        "换一家",
        "换地方",
        "换地点",
        "不要",
        "太吵",
        "太远",
        "近一点",
    )
    if any(term in message for term in replace_terms):
        return "replace_or_add"
    return "add"


def _followup_revision_category(state: AgentState, message: str) -> str | None:
    explicit_category = _followup_category_from_message(message)
    if explicit_category is not None:
        return explicit_category
    if not _has_generic_followup_replace_term(message):
        return None
    if _message_targets_dining(message):
        return None
    return _latest_followup_category_from_state(state)


def _explicit_add_followup_around_dining(message: str) -> bool:
    return (
        _followup_category_from_message(message) is not None
        and any(term in message for term in ("之前", "之后", "饭前", "饭后", "餐前", "餐后"))
        and any(term in message for term in ("加", "加一个", "加个", "安排", "再安排"))
    )


def _has_generic_followup_replace_term(message: str) -> bool:
    return any(
        term in message
        for term in (
            "换",
            "换个",
            "换一家",
            "换地方",
            "换地点",
            "不要",
            "太吵",
            "太远",
            "安静",
            "近一点",
        )
    )


def _message_targets_dining(message: str) -> bool:
    dining_terms = (
        "晚饭",
        "午饭",
        "晚餐",
        "午餐",
        "吃饭的地方",
        "用餐地方",
        "桑拿鸡",
        "火锅",
        "粤菜",
        "烧烤",
        "烤肉",
        "日料",
        "西餐",
        "轻食",
    )
    if any(term in message for term in dining_terms):
        return True
    if "餐厅" in message or "饭店" in message:
        return not any(term in message for term in ("离餐厅", "离饭店", "餐厅近", "饭店近", "附近"))
    return False


def _latest_followup_category_from_state(state: AgentState) -> str | None:
    target_plan_id = state.revision_target_plan_id or state.recommended_plan_id
    candidates = state.candidate_plans
    preferred = [
        candidate for candidate in candidates if candidate.plan_id == target_plan_id
    ] or candidates
    for candidate in preferred:
        for stage in reversed(candidate.stages):
            poi = stage.selected_poi
            if poi is None:
                continue
            stage_type = getattr(stage.stage_type, "value", str(stage.stage_type))
            category = _normalize_followup_category(poi.category)
            if stage_type == "relax" and _stage_looks_like_followup(stage) and category is not None:
                return category
            if _stage_looks_like_followup(stage) and category in {
                "小酒馆",
                "甜品",
                "咖啡",
                "茶馆",
                "书店",
            }:
                return category
    return None


def _stage_looks_like_followup(stage: object) -> bool:
    constraints = getattr(stage, "constraints", None)
    text = " ".join(
        str(value)
        for value in (
            getattr(stage, "stage_id", ""),
            getattr(stage, "name", ""),
            getattr(stage, "reasoning", ""),
            constraints if constraints is not None else "",
        )
    )
    return any(term in text for term in ("followup", "饭后", "餐后", "后续"))


def _is_after_dining_message(message: str) -> bool:
    return any(term in message for term in ("饭后", "吃完饭", "餐后", "晚饭后", "吃完")) or (
        "吃" in message and "之后" in message
    )


def _is_before_dining_message(message: str) -> bool:
    return any(term in message for term in ("饭前", "餐前", "吃饭前", "用餐前")) or (
        "吃" in message and "之前" in message
    )


def _followup_anchor(message: str) -> str:
    if _is_before_dining_message(message):
        return "before_dining"
    if _is_after_dining_message(message):
        return "after_dining"
    return "after_last"


def _followup_category_from_message(message: str) -> str | None:
    replacement = _replacement_followup_category_from_message(message)
    if replacement is not None:
        return replacement
    negated = _negated_followup_categories(message)
    for label, keywords in _followup_category_keywords():
        if label in negated:
            continue
        if any(keyword in message for keyword in keywords):
            return label
    return None


def _replacement_followup_category_from_message(message: str) -> str | None:
    negated = _negated_followup_categories(message)
    for marker in ("换成", "改成", "换为", "改为", "换去", "改去"):
        if marker not in message:
            continue
        tail = message.split(marker, 1)[1]
        for label, keywords in _followup_category_keywords():
            if label in negated:
                continue
            if any(keyword in tail for keyword in keywords):
                return label
    return None


def _negated_followup_category_from_message(message: str) -> str | None:
    categories = _negated_followup_categories(message)
    if not categories:
        return None
    if "小酒馆" in categories:
        return "小酒馆"
    return sorted(categories)[0]


def _negated_followup_categories(message: str) -> set[str]:
    return {
        label
        for label, keywords in _followup_category_keywords()
        if any(_keyword_is_cancelled(message, keyword) for keyword in keywords)
    }


def _followup_category_keywords() -> list[tuple[str, tuple[str, ...]]]:
    return [
        (
            "小酒馆",
            (
                "小酒馆",
                "酒馆",
                "酒吧",
                "清吧",
                "喝酒",
                "喝个酒",
                "喝点酒",
                "喝两杯",
                "喝一杯",
                "小酌",
            ),
        ),
        ("聊天", ("聊天", "聊聊天", "找个地方聊", "找地方聊天")),
        ("甜品", ("甜品", "蛋糕", "糖水")),
        ("咖啡", ("咖啡", "喝咖啡")),
        ("茶馆", ("茶馆", "喝茶")),
        ("书店", ("书店",)),
    ]


def _keyword_is_cancelled(message: str, keyword: str) -> bool:
    index = message.find(keyword)
    if index < 0:
        return False
    window = message[max(0, index - 6) : index + len(keyword) + 6]
    return any(
        term in window
        for term in ("不想", "不去", "不要", "别去", "别", "取消", "不喝", "别喝")
    )


def _normalize_followup_category(category: str | None) -> str | None:
    if category in {"酒馆", "酒吧", "清吧"}:
        return "小酒馆"
    return category
