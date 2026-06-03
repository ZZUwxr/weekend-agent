"""Adapters that wrap existing Skills as AgentTool implementations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from local_explorer_agent.app.domain.enums import PlanType, StageType
from local_explorer_agent.app.domain.models import PlanCandidate, Stage
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
    from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
    from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
    from local_explorer_agent.app.agent.skills.place_selection import PlaceSelectionSkill
    from local_explorer_agent.app.agent.skills.routing import RoutingSkill
    from local_explorer_agent.app.agent.skills.timeline_builder import TimelineBuilderSkill
    from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill


# ── Args schemas ─────────────────────────────────────────────────────────────


class UnderstandUserArgs(BaseModel):
    user_query: str = Field(description="The user's natural language query")
    user_id: str = Field(description="User ID")
    city: str = Field(default="深圳", description="Target city")
    start_time: datetime = Field(description="Planned start time")
    duration_minutes: int = Field(gt=0, le=720, description="Duration in minutes")


class EmptyArgs(BaseModel):
    """Tools that read all inputs from AgentState use this empty schema."""


class SelectPlacesArgs(BaseModel):
    city: str = Field(default="深圳", description="Target city for POI search")


# ── Tool adapters ────────────────────────────────────────────────────────────


class UnderstandUserTool:
    name = "understand_user"
    description = "解析用户自然语言查询，推断群体构成、角色和约束"
    args_schema = UnderstandUserArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: UserUnderstandingSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, UnderstandUserArgs)
        result = self._skill.run(
            user_query=args.user_query,
            user_id=args.user_id,
            city=args.city,
            start_time=args.start_time,
            duration_minutes=args.duration_minutes,
            user_memory=state.user_memory,
        )
        data = result.model_dump()
        _attach_fallback_warning(data, self._skill, "用户理解")
        return ToolResult(success=True, data=data)


class DetectConflictsTool:
    name = "detect_conflicts"
    description = "基于群体上下文检测潜在冲突（饮食、体力、预算等）"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: ConflictDetectionSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if state.inferred_context is None:
            return ToolResult(success=False, error_message="inferred_context is required")
        conflicts = self._skill.run(state.inferred_context)
        data = {"conflicts": [c.model_dump() for c in conflicts]}
        _attach_fallback_warning(data, self._skill, "冲突检测")
        return ToolResult(
            success=True,
            data=data,
        )


class GenerateNegotiationStrategyTool:
    name = "generate_negotiation_strategy"
    description = "为检测到的冲突生成协商策略"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: NegotiationSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if state.inferred_context is None:
            return ToolResult(success=False, error_message="inferred_context is required")
        strategies = self._skill.run(
            group_context=state.inferred_context,
            conflicts=state.conflicts,
        )
        data = {"strategies": [s.model_dump() for s in strategies]}
        _attach_fallback_warning(data, self._skill, "协商策略")
        return ToolResult(
            success=True,
            data=data,
        )


class DraftExperiencePlanTool:
    name = "draft_experience_plan"
    description = "基于群体上下文、冲突和策略生成候选体验方案"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: ExperiencePlanningSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if state.inferred_context is None:
            return ToolResult(success=False, error_message="inferred_context is required")
        candidates = self._skill.run(
            group_context=state.inferred_context,
            conflicts=state.conflicts,
            negotiation_strategies=state.negotiation_strategies,
        )
        candidates = _apply_requirement_scope_to_candidates(candidates, state)
        data = {"candidates": [c.model_dump() for c in candidates]}
        _attach_fallback_warning(data, self._skill, "体验方案生成")
        return ToolResult(
            success=True,
            data=data,
        )


class SelectPlacesTool:
    name = "select_places"
    description = "为每个候选方案的阶段选择合适的 POI 地点"
    args_schema = SelectPlacesArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: PlaceSelectionSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, SelectPlacesArgs)
        if state.inferred_context is None:
            return ToolResult(success=False, error_message="inferred_context is required")
        if not state.candidate_plans:
            return ToolResult(success=False, error_message="candidate_plans is required")

        updated: list[dict[str, Any]] = []
        for candidate in state.candidate_plans:
            result = self._skill.run(
                candidate=candidate,
                group_context=state.inferred_context,
                city=args.city,
                start_time=state.request.start_time,
                user_memory=state.user_memory,
            )
            updated.append(result.model_dump())

        return ToolResult(success=True, data={"candidates": updated})


class CalculateRoutesTool:
    name = "calculate_routes"
    description = "为候选方案计算 POI 之间的转场路线"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: RoutingSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if not state.candidate_plans:
            return ToolResult(success=False, error_message="candidate_plans is required")

        updated: list[dict[str, Any]] = []
        for candidate in state.candidate_plans:
            result = self._skill.run(candidate)
            updated.append(result.model_dump())

        return ToolResult(success=True, data={"candidates": updated})


class BuildTimelineTool:
    name = "build_timeline"
    description = "为候选方案构建详细时间轴"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, skill: TimelineBuilderSkill) -> None:
        self._skill = skill

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if not state.candidate_plans:
            return ToolResult(success=False, error_message="candidate_plans is required")

        updated: list[dict[str, Any]] = []
        for candidate in state.candidate_plans:
            result = self._skill.run(
                candidate=candidate,
                start_time=state.request.start_time,
                duration_minutes=state.request.duration_minutes,
            )
            updated.append(result.model_dump())

        return ToolResult(success=True, data={"candidates": updated})


class ScoreCandidatesTool:
    name = "score_candidates"
    description = "对候选方案评分并选择推荐方案"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, score_fn: Any, choose_fn: Any) -> None:
        self._score_fn = score_fn
        self._choose_fn = choose_fn

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if state.inferred_context is None:
            return ToolResult(success=False, error_message="inferred_context is required")
        if not state.candidate_plans:
            return ToolResult(success=False, error_message="candidate_plans is required")

        scored = [
            self._score_fn(candidate, state.inferred_context) for candidate in state.candidate_plans
        ]
        if state.user_memory is not None:
            scored = [_apply_memory_fit(candidate, state.user_memory) for candidate in scored]

        vr = state.validation_result
        if vr is not None:
            blocked_ids = {v.affected_plan_id for v in vr.blocking_violations if v.affected_plan_id}
            warning_plan_ids = {v.affected_plan_id for v in vr.warnings if v.affected_plan_id}
            for plan in scored:
                if plan.plan_id in blocked_ids:
                    plan.overall_score = max(0.0, plan.overall_score - 1.0)
                n_warnings = sum(1 for pid in warning_plan_ids if pid == plan.plan_id)
                if n_warnings:
                    plan.overall_score = max(0.0, round(plan.overall_score - 0.2 * n_warnings, 2))

        eligible = scored
        if vr is not None:
            blocked_ids = {v.affected_plan_id for v in vr.blocking_violations if v.affected_plan_id}
            eligible = [p for p in scored if p.plan_id not in blocked_ids] or scored

        recommended = self._choose_fn(eligible)
        if state.is_revision and state.revision_target_plan_id and state.revision_patches:
            target = next(
                (plan for plan in eligible if plan.plan_id == state.revision_target_plan_id),
                None,
            )
            if target is not None:
                recommended = target

        return ToolResult(
            success=True,
            data={
                "candidates": [c.model_dump() for c in scored],
                "recommended_plan_id": recommended.plan_id,
                "scoring_summary": {
                    "total_candidates": len(scored),
                    "eligible_candidates": len(eligible),
                    "recommended_plan_id": recommended.plan_id,
                    "recommended_overall_score": recommended.overall_score,
                },
            },
        )


def _apply_memory_fit(candidate, memory):  # type: ignore[no-untyped-def]
    terms: set[str] = set()
    poi_ids: set[str] = set()
    for stage in candidate.stages:
        categories = stage.constraints.get("categories")
        tags = stage.constraints.get("tags") or stage.constraints.get("标签")
        terms.update(_as_string_list(categories))
        terms.update(_as_string_list(tags))
        if stage.selected_poi is None:
            continue
        poi = stage.selected_poi
        poi_ids.add(poi.id)
        terms.add(poi.category)
        terms.update(poi.activity_tags)
        terms.update(poi.mood_tags)
        terms.update(poi.suitable_for)
        terms.update(poi.conflict_relief_tags)

    delta = 0.0
    matched_positive: list[str] = []
    matched_negative: list[str] = []
    for term in terms:
        if term in memory.category_weights:
            contribution = (memory.category_weights[term] - 1.0) * 0.2
            delta += contribution
            (matched_positive if contribution > 0 else matched_negative).append(term)
        if term in memory.tag_weights:
            contribution = (memory.tag_weights[term] - 1.0) * 0.12
            delta += contribution
            (matched_positive if contribution > 0 else matched_negative).append(term)
        if term in memory.likes:
            delta += 0.04
            matched_positive.append(term)
        if term in memory.dislikes:
            delta -= 0.06
            matched_negative.append(term)

    if poi_ids.intersection(memory.liked_poi_ids):
        delta += 0.2
        matched_positive.append("喜欢过的地点")
    if poi_ids.intersection(memory.disliked_poi_ids):
        delta -= 0.4
        matched_negative.append("不喜欢的地点")

    delta = max(-0.6, min(0.4, delta))
    if abs(delta) < 0.01:
        return candidate

    candidate.overall_score = round(max(0.0, min(5.0, candidate.overall_score + delta)), 2)
    if matched_positive and delta > 0:
        reason = "匹配你的历史偏好：" + "、".join(_dedupe(matched_positive)[:3])
    elif matched_negative and delta < 0:
        reason = "与你的历史偏好有轻微冲突：" + "、".join(_dedupe(matched_negative)[:3])
    else:
        reason = "已参考你的历史偏好微调推荐分。"
    candidate.recommendation_reason = _append_reason(candidate.recommendation_reason, reason)
    return candidate


def _attach_fallback_warning(data: dict[str, Any], skill: object, label: str) -> None:
    runner = getattr(skill, "prompt_runner", None)
    reason = getattr(runner, "last_fallback_reason", None)
    if not reason:
        return
    warnings = list(data.get("warnings") or [])
    warnings.append(f"{label}使用规则兜底：{_clip_warning(reason)}")
    data["warnings"] = warnings


def _clip_warning(value: str, limit: int = 180) -> str:
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _apply_requirement_scope_to_candidates(
    candidates: list[PlanCandidate],
    state: AgentState,
) -> list[PlanCandidate]:
    intake = state.requirement_intake
    if intake is None or not candidates:
        return candidates
    if intake.activity_count.max != 1:
        return _apply_multi_activity_hints(candidates, state)

    desired_stage = _stage_type_for_primary_intent(intake.primary_intent)
    template = _preferred_candidate_for_stage(candidates, desired_stage)
    stage = None
    if desired_stage is not None:
        stage = next(
            (
                item.model_copy(deep=True)
                for item in template.stages
                if _stage_type_value(item.stage_type) == desired_stage
            ),
            None,
        )
    if stage is None:
        stage = template.stages[0].model_copy(deep=True)

    stage.duration_minutes = min(
        max(stage.duration_minutes, 60),
        max(state.request.duration_minutes, 60),
    )
    stage.reasoning = _append_reason(
        stage.reasoning,
        "需求采集显示用户只想完成一个核心环节，因此不额外拼接第二站。",
    )

    categories = intake.search_hints.get("categories")
    tags = intake.search_hints.get("tags")
    if categories:
        stage.constraints = {**stage.constraints, "categories": categories}
    if tags:
        raw_tags = stage.constraints.get("标签") or stage.constraints.get("tags") or []
        stage.constraints = {
            **stage.constraints,
            "标签": list(dict.fromkeys([*_as_string_list(raw_tags), *_as_string_list(tags)])),
        }

    scoped = template.model_copy(deep=True)
    scoped.plan_id = "plan_a"
    scoped.plan_type = PlanType.PLAN_A
    scoped.title = _single_activity_title(intake.primary_intent, stage.name)
    scoped.theme = "只围绕用户明确目标安排一个核心环节。"
    scoped.stages = [stage]
    scoped.tradeoff_summary = "本次不扩展多站路线，优先避免无关转场。"
    scoped.recommendation_reason = _append_reason(
        scoped.recommendation_reason,
        "匹配需求采集：用户只想完成一个核心活动。",
    )
    return [scoped]


def _apply_multi_activity_hints(
    candidates: list[PlanCandidate],
    state: AgentState,
) -> list[PlanCandidate]:
    query = state.request.query
    updated = [candidate.model_copy(deep=True) for candidate in candidates]
    wants_exhibition = any(term in query for term in ("看展", "展览", "逛展", "美术馆", "画展"))
    wants_chat = any(term in query for term in ("聊天", "聊聊天", "找个地方聊", "找地方聊天"))

    for candidate in updated:
        explore_stage: Stage | None = None
        chat_stage: Stage | None = None
        if wants_exhibition:
            explore_stage = _stage_for_exhibition(candidate)
            if explore_stage is not None:
                explore_stage.stage_type = StageType.EXPLORE
                explore_stage.name = "看展"
                explore_stage.experience_goal = "先完成看展这个明确目标，再进入低强度聊天收尾。"
                explore_stage.constraints = {
                    **explore_stage.constraints,
                    "categories": ["展览"],
                    "标签": _merge_tags(explore_stage.constraints, ["看展", "展览", "室内"]),
                }
                explore_stage.reasoning = _append_reason(
                    explore_stage.reasoning, "用户明确提出看展，优先锁定展览类地点。"
                )

        if wants_chat:
            chat_stage = _first_chat_stage(candidate)
            if chat_stage is None or chat_stage is explore_stage:
                chat_stage = Stage(
                    stage_id=_new_hint_stage_id(candidate, "chat"),
                    stage_type=StageType.RELAX,
                    name="找个地方聊天",
                    experience_goal="找一个适合坐下来聊天的低强度空间。",
                    duration_minutes=60,
                    energy_level=1,
                    constraints={
                        "categories": ["咖啡", "茶馆", "书店"],
                        "标签": ["聊天", "安静", "休息"],
                        "indoor": True,
                    },
                    reasoning="用户明确提出再找个地方聊天，因此保留第二个收尾环节。",
                )
                candidate.stages.append(chat_stage)
            else:
                chat_stage.stage_type = StageType.RELAX
                chat_stage.name = "找个地方聊天"
                chat_stage.experience_goal = "找一个适合坐下来聊天的低强度空间。"
                chat_stage.constraints = {
                    **chat_stage.constraints,
                    "categories": ["咖啡", "茶馆", "书店"],
                    "标签": _merge_tags(chat_stage.constraints, ["聊天", "安静", "休息"]),
                    "indoor": True,
                }
                chat_stage.reasoning = _append_reason(
                    chat_stage.reasoning, "用户明确提出聊天收尾。"
                )

        if wants_exhibition and wants_chat:
            candidate.title = "看展后聊天"
            candidate.theme = "先看展，再找一个安静空间坐下来聊天。"
            candidate.tradeoff_summary = "保留两个明确环节，不把聊天误压缩成看展本身。"
            if explore_stage is not None and chat_stage is not None:
                candidate.stages = [explore_stage, chat_stage]

    return updated


def _stage_for_exhibition(candidate: PlanCandidate) -> Stage | None:
    explore = _first_stage_of_type(candidate, StageType.EXPLORE.value)
    if explore is not None:
        return explore
    return next(iter(candidate.stages), None)


def _first_stage_of_type(candidate: PlanCandidate, stage_type: str) -> Stage | None:
    return next(
        (stage for stage in candidate.stages if _stage_type_value(stage.stage_type) == stage_type),
        None,
    )


def _first_chat_stage(candidate: PlanCandidate) -> Stage | None:
    for stage in candidate.stages:
        if _stage_type_value(stage.stage_type) == StageType.RELAX.value:
            return stage
    for stage in candidate.stages:
        if _stage_type_value(stage.stage_type) == StageType.DINE.value:
            continue
        text = " ".join(
            str(value)
            for value in (
                stage.name,
                stage.experience_goal,
                stage.reasoning,
                stage.constraints,
            )
        )
        if "聊天" in text:
            return stage
    return None


def _merge_tags(constraints: dict[str, Any], tags: list[str]) -> list[str]:
    existing = constraints.get("标签") or constraints.get("tags") or []
    return list(dict.fromkeys([*_as_string_list(existing), *tags]))


def _new_hint_stage_id(candidate: PlanCandidate, suffix: str) -> str:
    existing = {stage.stage_id for stage in candidate.stages}
    index = len(candidate.stages) + 1
    while True:
        stage_id = f"{candidate.plan_id}_{suffix}_{index}"
        if stage_id not in existing:
            return stage_id
        index += 1


def _stage_type_for_primary_intent(primary_intent: str) -> str | None:
    if primary_intent == "dining":
        return StageType.DINE.value
    if primary_intent in {"culture", "outing", "leisure", "date", "solo"}:
        return StageType.EXPLORE.value
    return None


def _stage_type_value(value: object) -> str:
    if isinstance(value, StageType):
        return value.value
    return str(value)


def _preferred_candidate_for_stage(
    candidates: list[PlanCandidate],
    desired_stage: str | None,
) -> PlanCandidate:
    if desired_stage is None:
        return candidates[0]
    for candidate in candidates:
        if any(_stage_type_value(stage.stage_type) == desired_stage for stage in candidate.stages):
            return candidate
    return candidates[0]


def _single_activity_title(primary_intent: str, fallback: str) -> str:
    if primary_intent == "dining":
        return "就安排这一顿饭"
    if primary_intent == "culture":
        return "只安排这一个文化活动"
    if primary_intent == "date":
        return "就安排这次约会重点"
    if primary_intent == "solo":
        return "就安排这一个独处去处"
    if primary_intent == "outing":
        return "只安排这一个出门点"
    return fallback


def _as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _append_reason(existing: str, reason: str) -> str:
    if not existing:
        return reason
    if reason in existing:
        return existing
    return f"{existing} {reason}"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
