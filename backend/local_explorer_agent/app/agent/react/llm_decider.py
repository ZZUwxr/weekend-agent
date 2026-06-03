"""LLM-powered ReAct decider that uses structured output to select actions."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.prompts import build_controller_prompt
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.validation import PlanValidationResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.llm.base import BaseLLMClient
    from local_explorer_agent.app.agent.react.mock_decider import MockReActDecider
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.react.tool_registry import ToolSpec

logger = logging.getLogger(__name__)


class LLMReActDecider:
    """Decider that calls an LLM to produce structured AgentAction JSON.

    On parse failure, retries with repair prompts. If all retries fail
    and fallback is enabled, delegates to MockReActDecider.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        max_retries: int = 2,
        fallback_decider: MockReActDecider | None = None,
        allow_fallback: bool = True,
        deterministic_preview: bool = False,
    ) -> None:
        self._llm_client = llm_client
        self._max_retries = max_retries
        self._fallback_decider = fallback_decider
        self._allow_fallback = allow_fallback
        self._deterministic_preview = deterministic_preview

    async def decide(
        self,
        state: AgentState,
        tools: list[ToolSpec],
    ) -> AgentAction:
        forced_action = _forced_cancel_followup_revision_action(state)
        if forced_action is not None:
            return forced_action

        forced_action = _forced_followup_revision_action(state)
        if forced_action is not None:
            return forced_action

        forced_action = _forced_dining_revision_action(state)
        if forced_action is not None:
            return forced_action

        if self._deterministic_preview and not state.is_revision and not state.is_replan:
            forced_action = _deterministic_preview_action(state)
            if forced_action is not None:
                return forced_action

        state_summary = state.to_llm_summary()
        tool_dicts = [t.model_dump() for t in tools]
        prompt = build_controller_prompt(
            state_summary,
            tool_dicts,
            policy_summary=_policy_summary(state, tool_dicts),
        )

        try:
            action = await asyncio.to_thread(self._llm_client.complete_json, prompt, AgentAction)
            logger.info(
                "LLM decider chose: %s (%s)",
                action.action_type,
                action.decision_summary[:60],
            )
            return action
        except Exception as exc:
            logger.warning("LLM decider failed: %s", exc)
            return await self._handle_failure(state, tools, exc)

    async def _handle_failure(
        self,
        state: AgentState,
        tools: list[ToolSpec],
        original_error: Exception,
    ) -> AgentAction:
        if self._allow_fallback and self._fallback_decider is not None:
            logger.info("Falling back to MockReActDecider")
            try:
                return await self._fallback_decider.decide(state, tools)
            except Exception as fallback_exc:
                logger.error("Fallback decider also failed: %s", fallback_exc)
                raise original_error from fallback_exc

        raise original_error


def _deterministic_preview_action(state: AgentState) -> AgentAction | None:
    """Keep real-model preview on a stable rail while semantic tools still use LLMs."""
    req = state.request

    if state.user_memory is None:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="read_user_memory",
            tool_args={
                "user_id": state.user_id,
                "companion_ids": state.request.companion_ids,
            },
            decision_summary="规划开始先读取用户记忆，作为软偏好输入",
        )

    if state.requirement_intake is None:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="intake_user_requirements",
            tool_args={"query": req.query},
            decision_summary="规划前先结构化采集核心意图和缺失槽位",
        )

    clarification = state.clarification_response
    if (
        clarification is not None
        and clarification.needs_clarification
        and not clarification.can_continue_with_assumptions
        and not state.clarification_answers
    ):
        return AgentAction(
            action_type=AgentActionType.ASK_CLARIFICATION,
            message="；".join(question.question for question in clarification.questions[:3]),
            decision_summary="缺少必填信息，先向用户澄清再继续规划",
        )

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
            decision_summary="结合当前输入和记忆理解同行人、角色和约束",
        )

    if not _conflict_detection_done(state):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="detect_conflicts",
            decision_summary="生成方案前先检测饮食、体力、预算和节奏冲突",
        )

    if state.conflicts and not _negotiation_done(state):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="generate_negotiation_strategy",
            decision_summary="存在角色冲突，先生成协商策略再规划",
        )

    if not state.candidate_plans:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="draft_experience_plan",
            decision_summary="基于理解结果和冲突处理生成候选方案",
        )

    if _has_unselected_stage(state):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="select_places",
            tool_args={"city": req.city},
            decision_summary="候选方案缺少具体地点，先选择 POI",
        )

    if any(_candidate_needs_route(candidate) for candidate in state.candidate_plans):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="calculate_routes",
            decision_summary="多地点方案需要先计算转场路线",
        )

    if any(not candidate.timeline for candidate in state.candidate_plans):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="build_timeline",
            decision_summary="候选方案缺少时间轴，先构建时间安排",
        )

    if state.validation_result is None:
        return AgentAction(
            action_type=AgentActionType.VALIDATE_PLAN,
            decision_summary="输出前先校验方案约束",
        )

    vr = state.validation_result
    if (
        isinstance(vr, PlanValidationResult)
        and vr.blocking_violations
        and state.repair_count < get_settings().agent_max_repair_attempts
    ):
        return AgentAction(
            action_type=AgentActionType.REPAIR_PLAN,
            decision_summary="发现阻塞性约束，先修复方案",
        )

    if (
        isinstance(vr, PlanValidationResult)
        and vr.blocking_violations
        and state.repair_count >= get_settings().agent_max_repair_attempts
    ):
        return AgentAction(
            action_type=AgentActionType.FAIL,
            message="方案仍有阻塞性约束，暂时无法安全输出。",
            decision_summary="修复次数已用完，停止输出不安全方案",
        )

    if not state.scoring_completed:
        return AgentAction(
            action_type=AgentActionType.SCORE_PLAN,
            decision_summary="校验通过后评分并选择推荐方案",
        )

    return AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="预览流程已完成，输出最终方案",
    )


def _forced_cancel_followup_revision_action(state: AgentState) -> AgentAction | None:
    if not state.is_revision:
        return None
    message = state.revision_instruction or ""
    if not _needs_cancel_followup_revision(message):
        return None

    if not _tool_succeeded(state, "interpret_revision_request"):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="interpret_revision_request",
            tool_args={
                "message": message,
                "target_plan_id": state.revision_target_plan_id,
                "revision_mode": state.revision_mode,
            },
            decision_summary="取消后续活动先解析 revision intents",
        )

    if not _tool_succeeded(state, "remove_followup_stage"):
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

    replacement_followup = _replacement_followup_category_from_message(message)
    if replacement_followup is not None and not _tool_succeeded(state, "add_followup_stage"):
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

    return _revision_tail_action(
        state,
        route_summary="取消后续环节后重新计算路线",
        timeline_summary="取消后续环节后重建时间线",
        validate_summary="取消后续环节后重新校验约束",
        score_summary="取消后续环节后重新评分推荐",
        explain_summary="生成取消后续环节的修订摘要",
        final_summary="取消后续环节修订完成，输出更新后的方案",
        fail_message="取消后续环节后仍有阻塞性约束，无法安全完成修改",
    )


def _conflict_detection_done(state: AgentState) -> bool:
    return bool(state.conflicts) or _tool_succeeded(state, "detect_conflicts")


def _negotiation_done(state: AgentState) -> bool:
    return bool(state.negotiation_strategies) or _tool_succeeded(
        state,
        "generate_negotiation_strategy",
    )


def _has_unselected_stage(state: AgentState) -> bool:
    return any(
        stage.selected_poi is None
        for candidate in state.candidate_plans
        for stage in candidate.stages
    )


def _candidate_needs_route(candidate) -> bool:  # type: ignore[no-untyped-def]
    selected_poi_count = sum(
        1 for stage in candidate.stages if stage.selected_poi is not None
    )
    return selected_poi_count >= 2 and not candidate.route_segments


def _forced_followup_revision_action(state: AgentState) -> AgentAction | None:
    if not state.is_revision:
        return None
    message = state.revision_instruction or ""
    followup_category = _followup_revision_category(state, message)
    if not _needs_followup_revision(
        message,
        state.revision_intents,
        followup_category,
    ):
        return None

    if not _tool_succeeded(state, "interpret_revision_request"):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="interpret_revision_request",
            tool_args={
                "message": message,
                "target_plan_id": state.revision_target_plan_id,
                "revision_mode": state.revision_mode,
            },
            decision_summary="饭后追加活动先解析 revision intents",
        )

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
            decision_summary="复合修改中先调整餐饮，再追加饭后环节",
        )

    if not _tool_succeeded(state, "add_followup_stage"):
        anchor = _followup_anchor(message)
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="add_followup_stage",
            tool_args={
            "target_plan_id": state.revision_target_plan_id,
            "activity_or_category": followup_category,
            "anchor": anchor,
            "mode": _followup_revision_mode(message),
            "message": message,
        },
            decision_summary=_followup_decision_summary(followup_category, anchor),
        )

    return _revision_tail_action(
        state,
        route_summary="新增后续环节后重新计算路线",
        timeline_summary="新增后续环节后重建时间线",
        validate_summary="新增后续环节后重新校验约束",
        score_summary="新增后续环节后重新评分推荐",
        explain_summary="生成后续环节修订摘要",
        final_summary="后续环节修订完成，输出更新后的方案",
        fail_message="后续环节修订后仍有阻塞性约束，无法安全完成修改",
    )


def _forced_dining_revision_action(state: AgentState) -> AgentAction | None:
    if not state.is_revision:
        return None
    message = state.revision_instruction or ""
    if not _needs_dining_revision(message, state.revision_intents):
        return None

    if not _tool_succeeded(state, "interpret_revision_request"):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="interpret_revision_request",
            tool_args={
                "message": message,
                "target_plan_id": state.revision_target_plan_id,
                "revision_mode": state.revision_mode,
            },
            decision_summary="餐饮修改先解析 revision intents，避免误用通用替换",
        )

    if not _tool_succeeded(state, "revise_dining_stage"):
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
            decision_summary="餐饮修改使用专门工具新增或替换晚饭",
        )

    return _revision_tail_action(
        state,
        route_summary="餐饮修订后重新计算路线",
        timeline_summary="餐饮修订后重建时间线",
        validate_summary="餐饮修订后重新校验约束",
        score_summary="餐饮修订后重新评分推荐",
        explain_summary="生成餐饮修订摘要，说明新增或替换原因",
        final_summary="餐饮修订完成，输出更新后的方案",
        fail_message="餐饮修订后仍有阻塞性约束，无法安全完成修改",
    )


def _revision_tail_action(
    state: AgentState,
    *,
    route_summary: str,
    timeline_summary: str,
    validate_summary: str,
    score_summary: str,
    explain_summary: str,
    final_summary: str,
    fail_message: str,
) -> AgentAction:
    if not _tool_succeeded(state, "calculate_routes"):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="calculate_routes",
            decision_summary=route_summary,
        )

    if not _tool_succeeded(state, "rebuild_timeline"):
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="rebuild_timeline",
            tool_args={"target_plan_id": state.revision_target_plan_id},
            decision_summary=timeline_summary,
        )

    if state.validation_result is None:
        return AgentAction(
            action_type=AgentActionType.VALIDATE_PLAN,
            decision_summary=validate_summary,
        )

    vr = state.validation_result
    settings = get_settings()
    if (
        isinstance(vr, PlanValidationResult)
        and vr.blocking_violations
        and state.repair_count < settings.agent_max_repair_attempts
    ):
        return AgentAction(
            action_type=AgentActionType.REPAIR_PLAN,
            decision_summary="修订后仍有阻塞风险，先修复方案",
        )

    if (
        isinstance(vr, PlanValidationResult)
        and vr.blocking_violations
        and state.repair_count >= settings.agent_max_repair_attempts
    ):
        return AgentAction(
            action_type=AgentActionType.FAIL,
            message=fail_message,
            decision_summary="修订失败，返回明确原因",
        )

    if not state.scoring_completed:
        return AgentAction(
            action_type=AgentActionType.SCORE_PLAN,
            decision_summary=score_summary,
        )

    if state.revision_summary is None:
        return AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name="explain_changes",
            decision_summary=explain_summary,
        )

    return AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary=final_summary,
    )


def _tool_succeeded(state: AgentState, tool_name: str) -> bool:
    return any(
        observation.tool_name == tool_name and observation.success
        for observation in state.observations
    )


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


def _followup_decision_summary(category: str | None, anchor: str) -> str:
    activity = category or "后续环节"
    if anchor == "before_dining":
        return f"按用户意见在用餐前新增{activity}环节"
    if anchor == "after_dining":
        return f"按用户意见在饭后新增{activity}环节"
    return f"按用户意见在行程末尾新增{activity}环节"


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


def _policy_summary(
    state: AgentState,
    tool_specs: list[dict[str, object]],
) -> dict[str, object]:
    allowed_tools = [
        str(tool["name"]) for tool in tool_specs if not bool(tool.get("is_execution_tool", False))
    ]
    blocked_tools = [
        str(tool["name"]) for tool in tool_specs if bool(tool.get("is_execution_tool", False))
    ]
    blocked_tools.extend(["booking_execute", "taxi_execute", "share_execute"])
    return {
        "phase": "preview",
        "allowed_tools": allowed_tools,
        "blocked_tools": sorted(set(blocked_tools)),
        "must_validate_before_final": state.validation_result is None,
        "must_score_before_final": not state.scoring_completed,
        "repair_count": state.repair_count,
        "recent_observation_count": len(state.observations),
    }
