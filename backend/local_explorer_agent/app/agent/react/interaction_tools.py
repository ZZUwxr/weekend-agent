"""Interactive planning tools for clarification and plan revision."""

from __future__ import annotations

import math
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from local_explorer_agent.app.domain.enums import StageType, TimelineItemType
from local_explorer_agent.app.domain.models import (
    POI,
    ClarificationQuestion,
    ClarificationResponse,
    PlanCandidate,
    PlanPatch,
    PlanRevisionSummary,
    RequirementActivityCount,
    RequirementIntake,
    Stage,
    TimelineItem,
)
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.tools.poi_tool import POITool


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two (lat, lon) points."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _adjacent_poi_distances(
    candidate: PlanCandidate,
    target_idx: int,
) -> tuple[float | None, float | None]:
    """Return (prev_km, next_km) from stages[target_idx] to its neighbours."""
    target_poi = candidate.stages[target_idx].selected_poi
    if not target_poi or not target_poi.lat or not target_poi.lon:
        return None, None
    prev_km, next_km = None, None
    if target_idx > 0:
        prev_poi = candidate.stages[target_idx - 1].selected_poi
        if prev_poi and prev_poi.lat and prev_poi.lon:
            prev_km = _haversine_km(prev_poi.lat, prev_poi.lon, target_poi.lat, target_poi.lon)
    if target_idx < len(candidate.stages) - 1:
        next_poi = candidate.stages[target_idx + 1].selected_poi
        if next_poi and next_poi.lat and next_poi.lon:
            next_km = _haversine_km(next_poi.lat, next_poi.lon, target_poi.lat, target_poi.lon)
    return prev_km, next_km


_SINGLE_PURPOSE_MARKERS = (
    "只想",
    "就想",
    "就只想",
    "单纯想",
    "只要",
    "就吃",
    "就看",
    "就去",
    "别安排别的",
    "不用安排别的",
)

_MULTI_STOP_MARKERS = (
    "然后",
    "再去",
    "再吃",
    "再找",
    "找个地方",
    "找地方",
    "结束后",
    "之后",
    "顺便",
    "吃完再",
    "看完再",
    "接着",
)

_DINING_CATEGORIES = {
    "餐厅",
    "轻食",
    "火锅",
    "桑拿鸡",
    "烧烤",
    "烤肉",
    "日料",
    "西餐",
    "粤菜",
    "甜品",
    "咖啡",
    "茶馆",
}

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

_INTENT_SIGNALS = (
    ("火锅", ("火锅",)),
    ("烧烤", ("烧烤",)),
    ("烤肉", ("烤肉",)),
    ("轻食", ("轻食", "低卡", "清淡")),
    ("甜品", ("甜品", "蛋糕", "冰淇淋")),
    ("咖啡", ("咖啡", "喝咖啡")),
    ("茶馆", ("茶馆", "喝茶")),
    ("吃饭", ("吃个饭", "吃饭", "用餐", "晚饭", "午饭", "吃点")),
    ("看展", ("看个展", "看展", "展览", "逛展", "美术馆", "画展")),
    ("聊天", ("聊天", "聊聊天", "找个地方聊", "找地方聊天")),
    ("书店", ("书店",)),
    ("桌游", ("桌游",)),
    ("密室逃脱", ("密室逃脱", "密室")),
    ("小剧场", ("小剧场", "脱口秀", "演出", "黑盒剧场")),
    ("手作体验", ("手作", "陶艺", "皮具", "银饰")),
    ("买手店", ("买手店", "vintage", "小店")),
    ("Citywalk", ("Citywalk", "citywalk")),
    ("游乐园", ("游乐园", "游乐场", "乐园")),
    ("亲子空间", ("亲子空间",)),
    ("公园", ("公园",)),
)


class ClarifyRequirementsArgs(BaseModel):
    query: str | None = None


class IntakeUserRequirementsArgs(BaseModel):
    query: str | None = None


class InterpretRevisionArgs(BaseModel):
    message: str
    target_plan_id: str | None = None
    revision_mode: Literal["partial", "full"] = "partial"


class ReplacePOIArgs(BaseModel):
    target_plan_id: str | None = None
    target_stage_id: str | None = None
    intents: list[str] = Field(default_factory=list)
    message: str = ""


class ReviseDiningStageArgs(BaseModel):
    target_plan_id: str | None = None
    cuisine_or_category: str | None = None
    mode: Literal["replace_or_add", "replace", "add"] = "replace_or_add"
    insert_anchor: Literal["default", "before_dining"] = "default"
    message: str = ""


class AddFollowupStageArgs(BaseModel):
    target_plan_id: str | None = None
    activity_or_category: str | None = None
    anchor: Literal["after_dining", "after_last", "before_dining"] = "after_dining"
    mode: Literal["replace_or_add", "replace", "add"] = "replace_or_add"
    message: str = ""


class RemoveFollowupStageArgs(BaseModel):
    target_plan_id: str | None = None
    activity_or_category: str | None = None
    message: str = ""


class ApplyPlanPatchArgs(BaseModel):
    patch: dict[str, Any]


class RebuildTimelineArgs(BaseModel):
    target_plan_id: str | None = None


class ExplainChangesArgs(BaseModel):
    summary_hint: str | None = None


class ClarifyRequirementsTool:
    name = "clarify_requirements"
    description = "判断是否需要向用户澄清关键约束，最多生成 3 个简短问题和安全默认假设"
    args_schema = ClarifyRequirementsArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ClarifyRequirementsArgs)
        query = (args.query or state.request.query).strip()
        response = _build_clarification_response(query, state)
        return ToolResult(success=True, data=response.model_dump())


class IntakeUserRequirementsTool:
    name = "intake_user_requirements"
    description = (
        "在规划前解析用户 query，判断核心意图、想完成几个活动、缺失槽位，必要时生成少量澄清问题"
    )
    args_schema = IntakeUserRequirementsArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, IntakeUserRequirementsArgs)
        query = (args.query or state.request.query).strip()
        intake = _build_requirement_intake(query, state)
        return ToolResult(success=True, data=intake.model_dump())


class InterpretRevisionRequestTool:
    name = "interpret_revision_request"
    description = "把用户自然语言修改意见解析为结构化 revision intents"
    args_schema = InterpretRevisionArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, InterpretRevisionArgs)
        intents = _detect_revision_intents(args.message)
        return ToolResult(
            success=True,
            data={
                "message": args.message,
                "target_plan_id": args.target_plan_id,
                "revision_mode": args.revision_mode,
                "intents": intents or ["explain_plan"],
            },
        )


class ReplacePOITool:
    name = "replace_poi"
    description = "根据 revision intent 局部替换候选方案中的 POI，并尊重 locked_items"
    args_schema = ReplacePOIArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, poi_tool: POITool) -> None:
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ReplacePOIArgs)
        candidates = [candidate.model_copy(deep=True) for candidate in state.candidate_plans]
        if not candidates:
            return ToolResult(success=False, error_message="candidate_plans is required")

        target = _find_target_candidate(candidates, args.target_plan_id, state.recommended_plan_id)
        stage, stage_idx = _find_target_stage_with_index(target, args, state)
        if stage is None:
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["没有找到可修改且未锁定的阶段"],
                },
            )

        old_poi = stage.selected_poi
        search_intents = args.intents or state.revision_intents
        replacement = self._search_replacement(
            state,
            old_poi,
            search_intents,
            args.message,
            target_candidate=target,
            target_stage_idx=stage_idx,
        )
        if replacement is None or (old_poi and replacement.id == old_poi.id):
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["未找到更合适的替换地点，已保留原方案"],
                },
            )

        stage.selected_poi = replacement
        stage.reasoning = _replacement_reason(search_intents, args.message)
        patch = PlanPatch(
            patch_type="replace_poi",
            target_plan_id=target.plan_id,
            target_stage_id=stage.stage_id,
            old_value=_poi_patch_value(old_poi),
            new_value=_poi_patch_value(replacement),
            reason=stage.reasoning,
        )
        return ToolResult(
            success=True,
            data={
                "candidates": [candidate.model_dump() for candidate in candidates],
                "patches": [patch.model_dump()],
                "warnings": [],
            },
        )

    def _search_replacement(
        self,
        state: AgentState,
        old_poi: POI | None,
        intents: list[str],
        message: str,
        target_candidate: PlanCandidate | None = None,
        target_stage_idx: int | None = None,
    ) -> POI | None:
        indoor = True if "prefer_indoor" in intents else None
        max_queue_risk = "low" if "avoid_queue" in intents else None
        categories = [old_poi.category] if old_poi else None
        tags = _tags_for_intents(intents, message)
        pois = self._search_pois(
            state=state,
            tags=tags,
            categories=categories,
            indoor=indoor,
            max_queue_risk=max_queue_risk,
        )
        if not pois and categories:
            pois = self._search_pois(
                state=state,
                tags=tags,
                categories=None,
                indoor=indoor,
                max_queue_risk=max_queue_risk,
            )
        locked_ids = _locked_poi_ids(state.locked_items)
        eligible = []
        for poi in pois:
            if poi is None:
                continue
            if old_poi and poi.id == old_poi.id:
                continue
            if poi.id in locked_ids:
                continue
            if "prefer_indoor" in intents and not poi.indoor:
                continue
            if "avoid_queue" in intents and str(poi.queue_risk).lower() == "high":
                continue
            eligible.append(poi)

        if not eligible:
            return None

        # Distance-aware sorting: when reduce_distance intent, prefer POIs
        # that are closer to adjacent stages.
        if (
            "reduce_distance" in intents
            and target_candidate is not None
            and target_stage_idx is not None
            and old_poi
            and old_poi.lat
            and old_poi.lon
        ):
            eligible = _sort_by_adjacent_distance(
                eligible,
                target_candidate,
                target_stage_idx,
                old_poi,
            )

        return eligible[0]

    def _search_pois(
        self,
        *,
        state: AgentState,
        tags: list[str],
        categories: list[str] | None,
        indoor: bool | None,
        max_queue_risk: str | None,
    ) -> list[POI]:
        result = self._poi_tool.search_poi(
            city=state.request.city,
            tags=tags or None,
            categories=categories,
            indoor=indoor,
            max_queue_risk=max_queue_risk,
            limit=12,
            priority_categories=categories,
        )
        if not result.success:
            return []
        return [poi for poi in (_coerce_poi(item) for item in result.data or []) if poi is not None]


class ReviseDiningStageTool:
    name = "revise_dining_stage"
    description = (
        "处理用户在已生成方案后的餐饮修改：把晚饭/午饭换成指定菜系，"
        "或在原方案没有用餐环节时新增一顿饭"
    )
    args_schema = ReviseDiningStageArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, poi_tool: POITool) -> None:
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ReviseDiningStageArgs)
        candidates = [candidate.model_copy(deep=True) for candidate in state.candidate_plans]
        if not candidates:
            return ToolResult(success=False, error_message="candidate_plans is required")

        target = _find_target_candidate(candidates, args.target_plan_id, state.recommended_plan_id)
        message = args.message or state.revision_instruction or ""
        excluded_categories = _negated_dining_categories(message)
        cuisine = _normalize_dining_category(args.cuisine_or_category or _detect_cuisine(message))
        if cuisine in excluded_categories:
            cuisine = "餐厅"
        locked_ids = _locked_poi_ids(state.locked_items)
        dining_stage, dining_idx = _find_dining_stage_with_index(target)

        if dining_stage is not None and _stage_locked(dining_stage, locked_ids):
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["餐饮地点已锁定，无法替换晚饭。"],
                },
            )

        if dining_stage is not None and args.mode in {"replace_or_add", "replace"}:
            old_poi = dining_stage.selected_poi
            replacement = self._search_dining_poi(
                state=state,
                cuisine=cuisine,
                exclude_ids={old_poi.id} if old_poi else set(),
                exclude_categories=excluded_categories,
                locked_ids=locked_ids,
                target_candidate=target,
                target_stage_idx=dining_idx,
            )
            if replacement is None:
                return ToolResult(
                    success=True,
                    data={
                        "candidates": [candidate.model_dump() for candidate in candidates],
                        "patches": [],
                        "warnings": [f"没有找到可替换的{cuisine}餐饮地点，已保留原晚饭。"],
                    },
                )

            dining_stage.selected_poi = replacement
            dining_stage.fallback_pois = self._search_dining_pois(
                state=state,
                cuisine=cuisine,
                locked_ids=locked_ids,
                exclude_ids={replacement.id},
                exclude_categories=excluded_categories,
                limit=3,
            )
            dining_stage.name = _dining_stage_name(cuisine)
            dining_stage.constraints = _merge_dining_constraints(dining_stage.constraints, cuisine)
            if excluded_categories:
                dining_stage.constraints["exclude_categories"] = sorted(excluded_categories)
            dining_stage.reasoning = _dining_revision_reason(cuisine, excluded_categories)
            target.route_segments = []
            target.timeline = []
            patch = PlanPatch(
                patch_type="replace_dining_stage",
                target_plan_id=target.plan_id,
                target_stage_id=dining_stage.stage_id,
                old_value=_poi_patch_value(old_poi),
                new_value=_dining_patch_value(replacement, cuisine),
                reason=dining_stage.reasoning,
            )
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [patch.model_dump()],
                    "warnings": [],
                },
            )

        if args.mode in {"replace_or_add", "add"}:
            new_poi = self._search_dining_poi(
                state=state,
                cuisine=cuisine,
                exclude_ids=set(),
                exclude_categories=excluded_categories,
                locked_ids=locked_ids,
                target_candidate=target,
                target_stage_idx=len(target.stages),
            )
            if new_poi is None:
                return ToolResult(
                    success=True,
                    data={
                        "candidates": [candidate.model_dump() for candidate in candidates],
                        "patches": [],
                        "warnings": [f"没有找到可新增的{cuisine}餐饮地点。"],
                    },
                )

            stage = _build_dining_stage(target, new_poi, cuisine)
            insert_idx = _dining_insert_index(target, args.insert_anchor)
            target.stages.insert(insert_idx, stage)
            target.route_segments = []
            target.timeline = []
            patch = PlanPatch(
                patch_type="add_dining_stage",
                target_plan_id=target.plan_id,
                target_stage_id=stage.stage_id,
                old_value=None,
                new_value={
                    "stage_id": stage.stage_id,
                    "stage_name": stage.name,
                    **(_dining_patch_value(new_poi, cuisine) or {}),
                },
                reason=f"根据用户修改意见，新增{cuisine}餐饮环节。",
            )
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [patch.model_dump()],
                    "warnings": [],
                },
            )

        return ToolResult(
            success=True,
            data={
                "candidates": [candidate.model_dump() for candidate in candidates],
                "patches": [],
                "warnings": ["没有找到可修改的餐饮环节。"],
            },
        )

    def _search_dining_poi(
        self,
        *,
        state: AgentState,
        cuisine: str,
        exclude_ids: set[str],
        exclude_categories: set[str],
        locked_ids: set[str],
        target_candidate: PlanCandidate,
        target_stage_idx: int | None,
    ) -> POI | None:
        pois = self._search_dining_pois(
            state=state,
            cuisine=cuisine,
            locked_ids=locked_ids,
            exclude_ids=exclude_ids,
            exclude_categories=exclude_categories,
            limit=12,
        )
        if not pois:
            return None
        if target_stage_idx is not None:
            pois = _sort_pois_for_stage_insert(pois, target_candidate, target_stage_idx)
        return pois[0]

    def _search_dining_pois(
        self,
        *,
        state: AgentState,
        cuisine: str,
        locked_ids: set[str],
        exclude_ids: set[str],
        exclude_categories: set[str],
        limit: int,
    ) -> list[POI]:
        categories = _dining_search_categories(cuisine)
        result = self._poi_tool.search_poi(
            city=state.request.city,
            categories=categories,
            tags=None,
            indoor=None,
            max_queue_risk=None,
            limit=limit,
            priority_categories=categories,
        )
        pois = []
        if result.success:
            raw_pois = [
                poi for poi in (_coerce_poi(item) for item in result.data or []) if poi is not None
            ]
            pois = _filter_dining_search_results(raw_pois, cuisine, allow_generic=False)
        if not pois and categories != ["餐厅"]:
            fallback = self._poi_tool.search_poi(
                city=state.request.city,
                categories=["餐厅", "轻食", "火锅"],
                tags=[cuisine] if cuisine not in {"餐厅", "都可以"} else None,
                indoor=None,
                max_queue_risk=None,
                limit=limit,
                priority_categories=["餐厅", "轻食", "火锅"],
            )
            if fallback.success:
                raw_pois = [
                    poi
                    for poi in (_coerce_poi(item) for item in fallback.data or [])
                    if poi is not None
                ]
                pois = _filter_dining_search_results(raw_pois, cuisine, allow_generic=True)
        return [
            poi
            for poi in pois
            if poi.id not in locked_ids
            and poi.id not in exclude_ids
            and poi.category not in exclude_categories
        ]


class AddFollowupStageTool:
    name = "add_followup_stage"
    description = "在已生成方案后追加或替换后续环节，例如饭后小酒馆、饭后甜品、看展后咖啡"
    args_schema = AddFollowupStageArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, poi_tool: POITool) -> None:
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, AddFollowupStageArgs)
        candidates = [candidate.model_copy(deep=True) for candidate in state.candidate_plans]
        if not candidates:
            return ToolResult(success=False, error_message="candidate_plans is required")

        target = _find_target_candidate(candidates, args.target_plan_id, state.recommended_plan_id)
        message = args.message or state.revision_instruction or ""
        category = _normalize_followup_category(
            args.activity_or_category or _detect_followup_category(message)
        )
        if category is None and args.mode in {"replace_or_add", "replace"}:
            category = _infer_existing_followup_category(target, message)
        if category is None:
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["没有识别到要新增的后续活动类型。"],
                },
            )

        locked_ids = _locked_poi_ids(state.locked_items)
        existing_ids = {
            stage.selected_poi.id for stage in target.stages if stage.selected_poi is not None
        }
        existing_followup, existing_idx = _find_existing_followup_stage_with_index(target, category)
        if (
            existing_followup is not None
            and args.mode in {"replace_or_add", "replace"}
            and _stage_locked(existing_followup, locked_ids)
        ):
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": [f"{category}地点已锁定，无法替换。"],
                },
            )

        replacement_followup = existing_followup
        replacement_idx = existing_idx
        if (
            replacement_followup is None
            and args.mode in {"replace_or_add", "replace"}
            and _has_generic_followup_replacement_term(message)
        ):
            replacement_followup, replacement_idx = _find_latest_followup_stage_with_index(target)

        if (
            replacement_followup is not None
            and args.mode in {"replace_or_add", "replace"}
            and _stage_locked(replacement_followup, locked_ids)
        ):
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": [f"{category}地点已锁定，无法替换。"],
                },
            )

        if replacement_followup is not None and args.mode in {"replace_or_add", "replace"}:
            old_poi = replacement_followup.selected_poi
            replacement = self._search_followup_poi(
                state=state,
                category=category,
                exclude_ids=existing_ids,
                locked_ids=locked_ids,
                target_candidate=target,
                insert_idx=replacement_idx or 0,
            )
            if replacement is None:
                return ToolResult(
                    success=True,
                    data={
                        "candidates": [candidate.model_dump() for candidate in candidates],
                        "patches": [],
                        "warnings": [f"没有找到可替换的{category}地点，已保留原后续环节。"],
                    },
                )
            replacement_followup.selected_poi = replacement
            replacement_followup.fallback_pois = []
            replacement_followup.name = _followup_stage_name(category)
            replacement_followup.experience_goal = _followup_experience_goal(category)
            replacement_followup.constraints = {
                "categories": [category],
                "tags": _followup_search_tags(category) or [],
            }
            replacement_followup.reasoning = _followup_replace_reason(category)
            target.route_segments = []
            target.timeline = []
            patch = PlanPatch(
                patch_type="replace_followup_stage",
                target_plan_id=target.plan_id,
                target_stage_id=replacement_followup.stage_id,
                old_value=_poi_patch_value(old_poi),
                new_value={
                    "stage_id": replacement_followup.stage_id,
                    "stage_name": replacement_followup.name,
                    "requested_category": category,
                    "anchor": args.anchor,
                    **(_poi_patch_value(replacement) or {}),
                },
                reason=replacement_followup.reasoning,
            )
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [patch.model_dump()],
                    "warnings": [],
                },
            )

        if existing_followup is not None and args.mode == "add":
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": [f"方案里已经有{category}环节，未重复添加。"],
                },
            )

        if args.mode == "replace":
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": [f"没有找到可替换的{category}环节。"],
                },
            )

        insert_idx = _followup_insert_index(target, args.anchor)
        poi = self._search_followup_poi(
            state=state,
            category=category,
            exclude_ids=existing_ids,
            locked_ids=locked_ids,
            target_candidate=target,
            insert_idx=insert_idx,
        )
        if poi is None:
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": [f"没有找到可新增的{category}地点。"],
                },
            )

        stage = _build_followup_stage(target, poi, category, args.anchor)
        target.stages.insert(insert_idx, stage)
        target.route_segments = []
        target.timeline = []
        patch = PlanPatch(
            patch_type="add_followup_stage",
            target_plan_id=target.plan_id,
            target_stage_id=stage.stage_id,
            old_value=None,
            new_value={
                "stage_id": stage.stage_id,
                "stage_name": stage.name,
                "requested_category": category,
                "anchor": args.anchor,
                **(_poi_patch_value(poi) or {}),
            },
            reason=_followup_reason(category, args.anchor),
        )
        return ToolResult(
            success=True,
            data={
                "candidates": [candidate.model_dump() for candidate in candidates],
                "patches": [patch.model_dump()],
                "warnings": [],
            },
        )

    def _search_followup_poi(
        self,
        *,
        state: AgentState,
        category: str,
        exclude_ids: set[str],
        locked_ids: set[str],
        target_candidate: PlanCandidate,
        insert_idx: int,
    ) -> POI | None:
        categories = _followup_search_categories(category)
        result = self._poi_tool.search_poi(
            city=state.request.city,
            categories=categories,
            tags=_followup_search_tags(category),
            indoor=None,
            max_queue_risk=None,
            limit=12,
            priority_categories=categories,
        )
        if not result.success:
            return None
        pois = [
            poi
            for poi in (_coerce_poi(item) for item in result.data or [])
            if poi is not None
            and poi.id not in exclude_ids
            and poi.id not in locked_ids
            and _poi_matches_followup_category(poi, category)
        ]
        if not pois:
            return None
        return _sort_pois_for_stage_insert(pois, target_candidate, insert_idx)[0]


class RemoveFollowupStageTool:
    name = "remove_followup_stage"
    description = "取消已生成方案中的后续环节，例如取消喝酒、小酒馆、饭后咖啡或聊天收尾"
    args_schema = RemoveFollowupStageArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, RemoveFollowupStageArgs)
        candidates = [candidate.model_copy(deep=True) for candidate in state.candidate_plans]
        if not candidates:
            return ToolResult(success=False, error_message="candidate_plans is required")

        target = _find_target_candidate(candidates, args.target_plan_id, state.recommended_plan_id)
        message = args.message or state.revision_instruction or ""
        category = _normalize_followup_category(
            args.activity_or_category
            or _negated_followup_category_from_message(message)
            or _detect_followup_category(message)
        )
        stage, stage_idx = _find_existing_followup_stage_with_index(target, category)
        if stage is None and category is None:
            stage, stage_idx = _find_latest_followup_stage_with_index(target)
        if stage is None or stage_idx is None:
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["没有找到可取消的后续环节。"],
                },
            )

        locked_ids = _locked_poi_ids(state.locked_items)
        if _stage_locked(stage, locked_ids):
            return ToolResult(
                success=True,
                data={
                    "candidates": [candidate.model_dump() for candidate in candidates],
                    "patches": [],
                    "warnings": ["该后续地点已锁定，无法取消。"],
                },
            )

        removed = target.stages.pop(stage_idx)
        target.route_segments = []
        target.timeline = []
        patch = PlanPatch(
            patch_type="remove_followup_stage",
            target_plan_id=target.plan_id,
            target_stage_id=removed.stage_id,
            old_value={
                "stage_id": removed.stage_id,
                "stage_name": removed.name,
                "requested_category": category
                or (removed.selected_poi.category if removed.selected_poi else None),
                **(_poi_patch_value(removed.selected_poi) or {}),
            },
            new_value=None,
            reason=_followup_remove_reason(category or "后续活动"),
        )
        return ToolResult(
            success=True,
            data={
                "candidates": [candidate.model_dump() for candidate in candidates],
                "patches": [patch.model_dump()],
                "warnings": [],
            },
        )


class ApplyPlanPatchTool:
    name = "apply_plan_patch"
    description = "应用结构化 PlanPatch；当前支持 replace_poi 类局部 patch"
    args_schema = ApplyPlanPatchArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ApplyPlanPatchArgs)
        patch = PlanPatch.model_validate(args.patch)
        locked_ids = _locked_poi_ids(state.locked_items)
        if patch.old_value and patch.old_value.get("poi_id") in locked_ids:
            return ToolResult(
                success=False,
                error_message="locked item cannot be modified by apply_plan_patch",
            )
        return ToolResult(
            success=True,
            data={
                "candidates": [candidate.model_dump() for candidate in state.candidate_plans],
                "patches": [patch.model_dump()],
            },
        )


class RebuildTimelineTool:
    name = "rebuild_timeline"
    description = "局部重建候选方案 timeline，保留 locked_items 和现有 POI"
    args_schema = RebuildTimelineArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, RebuildTimelineArgs)
        candidates = [candidate.model_copy(deep=True) for candidate in state.candidate_plans]
        for candidate in candidates:
            if args.target_plan_id and candidate.plan_id != args.target_plan_id:
                continue
            candidate.timeline = _build_simple_timeline(candidate, state)
        return ToolResult(
            success=True,
            data={"candidates": [candidate.model_dump() for candidate in candidates]},
        )


class ExplainChangesTool:
    name = "explain_changes"
    description = "生成 PlanRevisionSummary，说明改了哪里、为什么改、哪些内容保留"
    args_schema = ExplainChangesArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ExplainChangesArgs)
        patches = state.revision_patches
        warnings = list(state.warnings)
        intents = state.revision_intents

        if patches:
            summary_text = args.summary_hint or _revision_patch_summary(patches)
        else:
            # Produce a meaningful explanation instead of a generic "no changes"
            reason = _no_patch_reason(intents, warnings)
            summary_text = args.summary_hint or reason
            if not any(
                "未找到" in w or "没有找到" in w or "锁定" in w or "无法" in w
                for w in warnings
            ):
                warnings.append(reason)

        summary = PlanRevisionSummary(
            summary=summary_text,
            patches=patches,
            unchanged_items=state.locked_items,
            warnings=warnings,
        )
        return ToolResult(success=True, data=summary.model_dump())


def _build_clarification_response(
    query: str,
    state: AgentState,
) -> ClarificationResponse:
    lowered = query.lower()
    safe_defaults = [
        f"默认城市为 {state.request.city or '深圳'}",
        f"默认时长为 {state.request.duration_minutes or 240} 分钟",
        "默认中等预算、轻松节奏",
    ]
    if any(term in query for term in ("你看着", "随便", "都可以", "你安排")):
        return ClarificationResponse(
            needs_clarification=False,
            questions=[],
            safe_assumptions=[*safe_defaults, "用户授权 Agent 使用安全默认假设"],
            can_continue_with_assumptions=True,
        )

    generic_terms = ("出去玩", "玩一下", "周末", "逛逛")
    has_specific_signal = any(
        term in query
        for term in (
            "孩子",
            "老人",
            "室内",
            "户外",
            "下雨",
            "排队",
            "预算",
            "吃",
            "近",
            "不累",
            "拍照",
        )
    )
    is_generic = len(query) <= 12 and any(term in query for term in generic_terms)
    if is_generic and not has_specific_signal:
        return ClarificationResponse(
            needs_clarification=True,
            questions=[
                ClarificationQuestion(
                    question_id="q_activity_style",
                    question="更想室内轻松、户外走走，还是都可以？",
                    reason="活动类型会显著影响 POI、路线和天气风险判断",
                    options=["室内轻松", "户外走走", "都可以"],
                    required=True,
                    default_assumption="都可以，优先少走路、少排队",
                ),
                ClarificationQuestion(
                    question_id="q_group",
                    question="这次是自己、情侣/家庭，还是朋友一起？",
                    reason="同行人会影响安全、节奏、餐饮和路线安排",
                    options=["自己", "情侣/家庭", "朋友"],
                    required=True,
                    default_assumption="按 2-3 人轻松出行安排",
                ),
            ],
            safe_assumptions=safe_defaults,
            can_continue_with_assumptions=False,
        )

    if "宠物" in query or "无障碍" in query or "孕" in query:
        return ClarificationResponse(
            needs_clarification=True,
            questions=[
                ClarificationQuestion(
                    question_id="q_accessibility",
                    question="有没有必须满足的通行、休息或安全要求？",
                    reason="这类约束会影响安全边界和地点可选范围",
                    options=["无台阶/少走路", "方便休息", "都需要"],
                    required=True,
                )
            ],
            safe_assumptions=safe_defaults,
            can_continue_with_assumptions=False,
        )

    if "rain" in lowered:
        safe_defaults.append("英文 rain 视为下雨风险，优先室内")
    return ClarificationResponse(
        needs_clarification=False,
        questions=[],
        safe_assumptions=safe_defaults,
        can_continue_with_assumptions=True,
    )


def _build_requirement_intake(query: str, state: AgentState) -> RequirementIntake:
    normalized = query.strip()
    answer_text = " ".join(state.clarification_answers.values())
    combined = f"{normalized} {answer_text}".strip()
    primary_intent = _detect_primary_intent(combined)
    activity_count = _infer_activity_count(combined, primary_intent)
    required_slots = _extract_required_slots(combined, state)
    search_hints = _search_hints_for_intent(primary_intent, combined, required_slots)
    known_constraints = _known_constraints_for_intake(
        state=state,
        query=combined,
        primary_intent=primary_intent,
        activity_count=activity_count,
        required_slots=required_slots,
    )
    missing_slots = _missing_slots_for_intake(
        query=combined,
        primary_intent=primary_intent,
        required_slots=required_slots,
        answered=state.clarification_answers,
    )
    clarification = _build_intake_clarification(
        state=state,
        primary_intent=primary_intent,
        missing_slots=missing_slots,
        required_slots=required_slots,
        activity_count=activity_count,
    )
    scope = _intent_scope_for_count(combined, activity_count)
    assumptions = [
        f"默认城市为 {state.request.city or '深圳'}",
        f"默认时长为 {state.request.duration_minutes or 240} 分钟",
    ]
    if any(term in combined for term in ("你看着", "随便", "都可以", "你安排")):
        assumptions.append("用户授权 Agent 使用安全默认假设")
    if clarification.can_continue_with_assumptions:
        assumptions.extend(clarification.safe_assumptions)
    clarification.safe_assumptions = list(
        dict.fromkeys(
            [
                *assumptions,
                *clarification.safe_assumptions,
            ]
        )
    )[:8]

    return RequirementIntake(
        raw_query=normalized,
        primary_intent=primary_intent,
        intent_scope=scope,
        activity_count=activity_count,
        required_slots=required_slots,
        known_constraints=known_constraints,
        missing_slots=missing_slots,
        search_hints=search_hints,
        clarification=clarification,
    )


def _detect_primary_intent(query: str) -> str:
    ordered = _detect_intent_labels(query)
    if not ordered:
        if any(term in query for term in ("约会", "情侣", "二人世界")):
            return "date"
        if any(term in query for term in ("自己", "一个人", "独处", "独自")):
            return "solo"
        if any(term in query for term in ("出去玩", "逛逛", "玩一下", "周末")):
            return "leisure"
        return "unknown"
    first = ordered[0]
    if first in {
        "火锅",
        "烧烤",
        "烤肉",
        "轻食",
        "甜品",
        "咖啡",
        "茶馆",
        "吃饭",
        "粤菜",
        "日料",
        "西餐",
    }:
        return "dining"
    if first in {"看展", "书店", "小剧场", "桌游", "密室逃脱", "聊天", "手作体验", "买手店"}:
        return "culture"
    if first in {"公园", "游乐园", "亲子空间", "Citywalk"}:
        return "outing"
    return "unknown"


def _detect_intent_labels(query: str) -> list[str]:
    matched: list[tuple[int, str]] = []
    extra_keywords = {
        "粤菜": ("粤菜", "早茶", "茶餐厅"),
        "日料": ("日料", "寿司", "居酒屋"),
        "西餐": ("西餐", "牛排", "披萨"),
    }
    for label, keywords in _INTENT_SIGNALS:
        position = _first_position(query, keywords)
        if position >= 0:
            matched.append((position, label))
    for label, keywords in extra_keywords.items():
        position = _first_position(query, keywords)
        if position >= 0:
            matched.append((position, label))
    labels: list[str] = []
    for _position, label in sorted(matched, key=lambda item: item[0]):
        if label not in labels:
            labels.append(label)
    return labels


def _infer_activity_count(query: str, primary_intent: str) -> RequirementActivityCount:
    labels = _detect_intent_labels(query)
    evidence: list[str] = []
    if any(marker in query for marker in _MULTI_STOP_MARKERS):
        evidence.append("出现多环节连接词")
        count = max(2, min(4, len(labels) or 2))
        return RequirementActivityCount(
            min=count,
            max=count,
            confidence=0.78,
            evidence=evidence,
        )
    if any(marker in query for marker in _SINGLE_PURPOSE_MARKERS):
        evidence.append("用户表达只想完成一个目标")
        return RequirementActivityCount(
            min=1,
            max=1,
            confidence=0.95,
            evidence=evidence,
        )
    if len(labels) > 1:
        evidence.append("query 中出现多个不同活动目标")
        count = min(4, len(labels))
        return RequirementActivityCount(
            min=count,
            max=count,
            confidence=0.72,
            evidence=evidence,
        )
    if primary_intent in {"dining", "culture", "date", "solo"} and labels:
        evidence.append("query 只有一个明确目标")
        return RequirementActivityCount(
            min=1,
            max=1,
            confidence=0.82,
            evidence=evidence,
        )
    return RequirementActivityCount(
        min=1,
        max=3,
        confidence=0.5,
        evidence=["query 未明确活动数量，允许 1-3 个轻量环节"],
    )


def _extract_required_slots(query: str, state: AgentState) -> dict[str, Any]:
    answers = state.clarification_answers
    cuisine = _detect_cuisine(query)
    group_size = _detect_group_size(query)
    budget = _detect_budget(query)
    area = _detect_area(query)
    pace = _detect_pace(query)
    if not cuisine:
        cuisine = _slot_from_answers(answers, ("q_cuisine", "q_cuisine_or_style"))
    if group_size is None:
        group_size = _group_size_from_text(_slot_from_answers(answers, ("q_group_size", "q_group")))
    return {
        "cuisine_or_style": cuisine,
        "group_size": group_size,
        "budget": budget,
        "area": area,
        "pace": pace,
        "companions": _detect_companions(query),
    }


def _search_hints_for_intent(
    primary_intent: str,
    query: str,
    slots: dict[str, Any],
) -> dict[str, Any]:
    cuisine = slots.get("cuisine_or_style")
    if primary_intent == "dining":
        categories = [cuisine] if cuisine and cuisine != "都可以" else ["餐厅", "轻食"]
        if "火锅" in query:
            categories = ["火锅"]
        return {"stage_type": "dine", "categories": categories, "tags": ["少排队"]}
    if primary_intent == "culture":
        if "展" in query:
            return {"stage_type": "explore", "categories": ["展览"], "tags": ["室内"]}
        if "书店" in query:
            return {"stage_type": "explore", "categories": ["书店"], "tags": ["安静"]}
        return {"stage_type": "explore", "categories": ["展览", "书店"], "tags": ["室内"]}
    if primary_intent == "date":
        return {
            "stage_type": "explore",
            "categories": ["展览", "Citywalk", "买手店", "咖啡", "甜品"],
            "tags": ["情侣", "约会", "聊天", "拍照", "有氛围"],
        }
    if primary_intent == "solo":
        return {
            "stage_type": "explore",
            "categories": ["展览", "书店", "Citywalk", "咖啡"],
            "tags": ["独处", "安静", "轻松", "少排队"],
        }
    if primary_intent == "outing":
        if any(term in query for term in ("孩子", "小孩", "娃", "宝宝", "女儿", "儿子", "亲子")):
            return {"stage_type": "explore", "categories": ["公园", "亲子空间"], "tags": ["轻松", "亲子"]}
        return {"stage_type": "explore", "categories": ["公园", "Citywalk", "书店"], "tags": ["轻松"]}
    return {"stage_type": None, "categories": [], "tags": []}


def _known_constraints_for_intake(
    *,
    state: AgentState,
    query: str,
    primary_intent: str,
    activity_count: RequirementActivityCount,
    required_slots: dict[str, Any],
) -> list[str]:
    constraints = [
        f"城市为{state.request.city}",
        f"计划时长{state.request.duration_minutes}分钟",
    ]
    if primary_intent != "unknown":
        constraints.append(f"核心意图：{primary_intent}")
    if activity_count.max == 1:
        constraints.append("只安排一个核心环节")
    elif activity_count.min == activity_count.max:
        constraints.append(f"安排{activity_count.max}个环节")
    if required_slots.get("cuisine_or_style"):
        constraints.append(f"餐饮偏好：{required_slots['cuisine_or_style']}")
    if required_slots.get("group_size"):
        constraints.append(f"人数：{required_slots['group_size']}")
    if "别太远" in query or "附近" in query or "近" in query:
        constraints.append("低转场/距离不要太远")
    return list(dict.fromkeys(constraints))


def _missing_slots_for_intake(
    *,
    query: str,
    primary_intent: str,
    required_slots: dict[str, Any],
    answered: dict[str, str],
) -> list[str]:
    missing: list[str] = []
    answered_text = " ".join(answered.values())
    if primary_intent == "dining":
        cuisine = required_slots.get("cuisine_or_style")
        if not cuisine and not _answer_means_anything_ok(answered_text):
            missing.append("cuisine_or_style")
        if required_slots.get("group_size") is None:
            missing.append("group_size")
    elif primary_intent in {"unknown", "leisure"}:
        if _is_vague_open_query(query) and not _answer_means_anything_ok(query):
            missing.extend(["activity_style", "activity_count"])
    elif primary_intent == "culture" and not ("展" in answered_text or "书店" in answered_text):
        if not any(term in _safe_join(required_slots.values()) for term in ("展", "书店")):
            missing.append("culture_style")
    return missing[:4]


def _is_vague_open_query(query: str) -> bool:
    if any(term in query for term in ("你看着", "随便", "都可以", "你安排")):
        return False
    detail_terms = (
        "老婆",
        "老公",
        "情侣",
        "约会",
        "自己",
        "一个人",
        "独处",
        "孩子",
        "朋友",
        "老人",
        "减肥",
        "低卡",
        "别太远",
        "附近",
        "不累",
        "室内",
        "户外",
        "拍照",
        "预算",
        "吃",
        "展",
    )
    generic_terms = ("出去玩", "玩一下", "逛逛", "周末")
    return any(term in query for term in generic_terms) and not any(
        term in query for term in detail_terms
    )


def _build_intake_clarification(
    *,
    state: AgentState,
    primary_intent: str,
    missing_slots: list[str],
    required_slots: dict[str, Any],
    activity_count: RequirementActivityCount,
) -> ClarificationResponse:
    if state.clarification_answers:
        return ClarificationResponse(
            needs_clarification=False,
            questions=[],
            safe_assumptions=_safe_assumptions_for_slots(primary_intent, required_slots),
            can_continue_with_assumptions=True,
        )

    questions: list[ClarificationQuestion] = []
    if "cuisine_or_style" in missing_slots:
        questions.append(
            ClarificationQuestion(
                question_id="q_cuisine",
                question="想吃哪类？比如火锅、粤菜、烧烤、日料，还是都可以？",
                reason="只吃饭时，菜系会直接决定餐厅搜索方向",
                options=["火锅", "粤菜", "烧烤", "日料", "都可以"],
                required=True,
                default_assumption="都可以，优先选评分稳、排队少的餐厅",
            )
        )
    if "group_size" in missing_slots:
        questions.append(
            ClarificationQuestion(
                question_id="q_group_size",
                question="几个人一起？",
                reason="人数会影响餐厅类型、排队和预订建议",
                options=["1人", "2人", "3-4人", "5人以上"],
                required=False,
                default_assumption="按2人安排",
            )
        )
    if "activity_style" in missing_slots:
        questions.append(
            ClarificationQuestion(
                question_id="q_activity_style",
                question="更想吃饭、看展/逛店，还是纯放松？",
                reason="活动类型会决定后续搜索和时间安排",
                options=["吃饭", "看展/逛店", "纯放松"],
                required=True,
                default_assumption="按轻松室内安排",
            )
        )
    if "activity_count" in missing_slots:
        questions.append(
            ClarificationQuestion(
                question_id="q_activity_count",
                question="这次想安排几个环节？",
                reason="环节数量会直接约束方案阶段数",
                options=["只要1个", "2个以内", "都可以"],
                required=True,
                default_assumption="2个以内，少转场",
            )
        )
    if "culture_style" in missing_slots:
        questions.append(
            ClarificationQuestion(
                question_id="q_culture_style",
                question="更想看展、美术馆，还是去书店待一会儿？",
                reason="文化类目标需要明确地点类别",
                options=["看展", "美术馆", "书店", "都可以"],
                required=False,
                default_assumption="优先室内、少排队",
            )
        )

    questions = questions[:3]
    needs = any(question.required for question in questions)
    if activity_count.max == 1 and primary_intent in {"dining", "culture"}:
        # Single-purpose queries deserve one precise required question when the
        # core category is vague, but optional slots (for example group size)
        # should not block a clear request like "只想吃火锅".
        needs = any(question.required for question in questions)
    return ClarificationResponse(
        needs_clarification=bool(questions),
        questions=questions,
        safe_assumptions=_safe_assumptions_for_slots(primary_intent, required_slots),
        can_continue_with_assumptions=not needs,
    )


def _intent_scope_for_count(
    query: str,
    activity_count: RequirementActivityCount,
) -> str:
    if activity_count.max == 1:
        return "single_activity"
    if activity_count.min >= 2 or any(marker in query for marker in _MULTI_STOP_MARKERS):
        return "multi_activity"
    if activity_count.confidence < 0.6:
        return "open_ended"
    return "unknown"


def _detect_cuisine(query: str) -> str | None:
    negated = _negated_dining_categories(query)
    for label, keywords in _DINING_CATEGORY_KEYWORDS:
        if label in negated:
            continue
        if any(keyword in query for keyword in keywords):
            return label
    if negated:
        return "餐厅"
    if any(term in query for term in ("都可以", "随便", "你看着")):
        return "都可以"
    return None


def _detect_group_size(query: str) -> int | None:
    direct = _group_size_from_text(query)
    if direct is not None:
        return direct
    if "朋友" in query:
        return 2
    if "老婆孩子" in query or "老公孩子" in query:
        return 3
    if "情侣" in query or "老婆" in query or "老公" in query:
        return 2
    return None


def _group_size_from_text(text: str | None) -> int | None:
    if not text:
        return None
    digits = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "一": 1,
        "两": 2,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
    }
    for key, value in digits.items():
        if f"{key}人" in text or f"{key}个" in text:
            return value
    if "自己" in text or "一个人" in text or "独自" in text:
        return 1
    if "3-4" in text or "三四" in text:
        return 4
    if "5人以上" in text or "五人以上" in text:
        return 5
    return None


def _detect_budget(query: str) -> str | None:
    if any(term in query for term in ("便宜", "别太贵", "性价比", "预算低")):
        return "low"
    if any(term in query for term in ("贵一点", "预算高", "精致", "高级")):
        return "high"
    if "人均" in query or "预算" in query:
        return "medium"
    return None


def _detect_area(query: str) -> str | None:
    for area in ("南山", "福田", "罗湖", "宝安", "龙岗", "前海", "科技园"):
        if area in query:
            return area
    if "附近" in query:
        return "nearby"
    return None


def _detect_pace(query: str) -> str:
    if any(term in query for term in ("轻松", "不累", "别太赶", "慢一点", "松弛")):
        return "relaxed"
    if any(term in query for term in ("充实", "多安排", "多玩几个")):
        return "active"
    return "normal"


def _detect_companions(query: str) -> list[str]:
    companions: list[str] = []
    for label in ("老婆", "老公", "孩子", "朋友", "同事", "老人", "父母"):
        if label in query:
            companions.append(label)
    return companions


def _slot_from_answers(answers: dict[str, str], ids: tuple[str, ...]) -> str | None:
    for question_id in ids:
        answer = answers.get(question_id)
        if answer:
            if _answer_means_anything_ok(answer):
                return "都可以"
            cuisine = _detect_cuisine(answer)
            return cuisine or answer
    return None


def _answer_means_anything_ok(text: str | None) -> bool:
    return bool(text) and any(term in text for term in ("都可以", "随便", "你看着"))


def _safe_assumptions_for_slots(primary_intent: str, slots: dict[str, Any]) -> list[str]:
    assumptions: list[str] = ["默认中等预算、轻松节奏"]
    if primary_intent == "dining":
        if not slots.get("cuisine_or_style") or slots.get("cuisine_or_style") == "都可以":
            assumptions.append("餐饮默认优先排队少、评分稳定、适合聊天")
        if slots.get("group_size") is None:
            assumptions.append("人数未知时按2人用餐安排")
    if primary_intent in {"unknown", "leisure", "date", "solo"}:
        assumptions.append("活动目标不明确时优先室内、少转场、低后悔方案")
    return assumptions


def _first_position(query: str, keywords: tuple[str, ...]) -> int:
    positions = [query.find(keyword) for keyword in keywords if keyword in query]
    return min(positions) if positions else -1


def _safe_join(values: object) -> str:
    if isinstance(values, dict):
        return " ".join(str(value) for value in values.values())
    if isinstance(values, list | tuple | set):
        return " ".join(str(value) for value in values)
    return str(values)


def _detect_revision_intents(message: str) -> list[str]:
    intents: list[str] = []
    mapping = [
        ("reduce_distance", ("远", "近一点", "别太远", "路程")),
        ("prefer_indoor", ("室内", "下雨", "太晒", "太热")),
        ("avoid_queue", ("排队", "热门", "等太久")),
        ("lower_budget", ("便宜", "预算", "贵", "低一点")),
        (
            "add_followup_stage",
            (
                "饭后",
                "吃完饭",
                "餐后",
                "之后安排",
                "再安排",
                "小酒馆",
                "酒馆",
                "酒吧",
                "清吧",
                "喝酒",
                "喝个酒",
                "喝点酒",
                "喝两杯",
                "聊天",
                "找个地方聊",
                "找地方聊天",
                "小酌",
            ),
        ),
        ("add_dining", ("加晚饭", "加个晚饭", "加一顿", "加顿饭", "加吃饭", "新增晚饭")),
        (
            "change_dining",
            (
                "晚饭",
                "午饭",
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
            ),
        ),
        ("replace_poi", ("换", "换掉", "不要这个", "第二个")),
        ("remove_stage", ("删掉", "少一个", "取消", "不想去", "不去了")),
        ("shorten_duration", ("太赶", "太久", "短一点", "不赶")),
        ("make_child_friendly", ("孩子", "亲子", "儿童")),
        ("make_less_tiring", ("累", "轻松", "少走")),
        ("explain_plan", ("为什么", "解释", "说明")),
    ]
    for intent, keywords in mapping:
        if any(keyword in message for keyword in keywords):
            intents.append(intent)
    return intents


def _find_target_candidate(
    candidates: list[PlanCandidate],
    target_plan_id: str | None,
    recommended_plan_id: str | None,
) -> PlanCandidate:
    for candidate in candidates:
        if target_plan_id and candidate.plan_id == target_plan_id:
            return candidate
    for candidate in candidates:
        if recommended_plan_id and candidate.plan_id == recommended_plan_id:
            return candidate
    return candidates[0]


def _find_target_stage(
    candidate: PlanCandidate,
    args: ReplacePOIArgs,
    state: AgentState,
):
    stage, _ = _find_target_stage_with_index(candidate, args, state)
    return stage


def _find_target_stage_with_index(
    candidate: PlanCandidate,
    args: ReplacePOIArgs,
    state: AgentState,
) -> tuple[Stage | None, int | None]:
    """Return (stage, index) respecting locked items and message hints."""
    locked_ids = _locked_poi_ids(state.locked_items)
    if args.target_stage_id:
        for idx, stage in enumerate(candidate.stages):
            if stage.stage_id == args.target_stage_id and not _stage_locked(stage, locked_ids):
                return stage, idx
    message = args.message or state.revision_instruction or ""
    if "第二" in message and len(candidate.stages) >= 2:
        stage = candidate.stages[1]
        if not _stage_locked(stage, locked_ids):
            return stage, 1
    if "第三" in message and len(candidate.stages) >= 3:
        stage = candidate.stages[2]
        if not _stage_locked(stage, locked_ids):
            return stage, 2
    if "第一" in message and len(candidate.stages) >= 1:
        stage = candidate.stages[0]
        if not _stage_locked(stage, locked_ids):
            return stage, 0
    for idx, stage in enumerate(candidate.stages):
        if not _stage_locked(stage, locked_ids):
            return stage, idx
    return None, None


def _sort_by_adjacent_distance(
    pois: list[POI],
    candidate: PlanCandidate,
    stage_idx: int,
    old_poi: POI,
) -> list[POI]:
    """Sort candidate POIs by total distance to adjacent stages, ascending.

    The old POI's distance is used as a baseline.  POIs that reduce total
    adjacent distance come first; those that increase it come last.
    """
    old_prev, old_next = None, None
    if stage_idx > 0:
        prev_poi = candidate.stages[stage_idx - 1].selected_poi
        if prev_poi and prev_poi.lat and prev_poi.lon and old_poi.lat and old_poi.lon:
            old_prev = _haversine_km(prev_poi.lat, prev_poi.lon, old_poi.lat, old_poi.lon)
    if stage_idx < len(candidate.stages) - 1:
        next_poi = candidate.stages[stage_idx + 1].selected_poi
        if next_poi and next_poi.lat and next_poi.lon and old_poi.lat and old_poi.lon:
            old_next = _haversine_km(next_poi.lat, next_poi.lon, old_poi.lat, old_poi.lon)
    old_total = (old_prev or 0) + (old_next or 0)

    def _new_total(poi: POI) -> float:
        total = 0.0
        if stage_idx > 0:
            prev_poi = candidate.stages[stage_idx - 1].selected_poi
            if prev_poi and prev_poi.lat and prev_poi.lon and poi.lat and poi.lon:
                total += _haversine_km(prev_poi.lat, prev_poi.lon, poi.lat, poi.lon)
        if stage_idx < len(candidate.stages) - 1:
            next_poi = candidate.stages[stage_idx + 1].selected_poi
            if next_poi and next_poi.lat and next_poi.lon and poi.lat and poi.lon:
                total += _haversine_km(next_poi.lat, next_poi.lon, poi.lat, poi.lon)
        return total

    # Partition: closer-than-old first, then farther, each sorted by distance
    closer = []
    farther = []
    for poi in pois:
        d = _new_total(poi)
        if d < old_total:
            closer.append((d, poi))
        else:
            farther.append((d, poi))
    closer.sort(key=lambda x: x[0])
    farther.sort(key=lambda x: x[0])
    return [poi for _, poi in closer] + [poi for _, poi in farther]


def _stage_locked(stage, locked_ids: set[str]) -> bool:
    return bool(stage.selected_poi and stage.selected_poi.id in locked_ids)


def _detect_followup_category(message: str) -> str | None:
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


def _normalize_followup_category(value: str | None) -> str | None:
    if not value:
        return None
    if value in {"酒馆", "酒吧", "清吧", "喝酒", "喝个酒", "喝点酒", "喝两杯", "喝一杯", "小酌"}:
        return "小酒馆"
    return value


def _infer_existing_followup_category(
    candidate: PlanCandidate,
    message: str,
) -> str | None:
    if not _has_generic_followup_replacement_term(message):
        return None
    if _message_targets_dining(message):
        return None
    for stage in reversed(candidate.stages):
        poi = stage.selected_poi
        if poi is None:
            continue
        category = _normalize_followup_category(poi.category)
        if (
            stage.stage_type == StageType.RELAX
            and _stage_looks_like_followup(stage)
            and category is not None
        ):
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


def _has_generic_followup_replacement_term(message: str) -> bool:
    return any(
        term in message
        for term in (
            "换",
            "换个",
            "换一家",
            "换地方",
            "换地点",
            "取消",
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


def _stage_looks_like_followup(stage: Stage) -> bool:
    constraints = stage.constraints if stage.constraints is not None else ""
    text = " ".join(
        str(value) for value in (stage.stage_id, stage.name, stage.reasoning, constraints)
    )
    return any(term in text for term in ("followup", "饭后", "餐后", "后续"))


def _followup_search_categories(category: str) -> list[str]:
    if category == "小酒馆":
        return ["小酒馆"]
    if category == "聊天":
        return ["咖啡", "茶馆", "书店"]
    return [category]


def _followup_search_tags(category: str) -> list[str] | None:
    if category == "小酒馆":
        return ["小酒馆", "酒馆", "酒吧", "清吧", "饭后", "聊天"]
    if category == "聊天":
        return ["聊天", "安静", "休息"]
    return [category]


def _poi_matches_followup_category(poi: POI, category: str) -> bool:
    if poi.category == category:
        return True
    if category == "小酒馆":
        return poi.category == "小酒馆" or any(
            _poi_matches_term(poi, term) for term in ("小酒馆", "酒馆", "酒吧", "清吧", "小酌")
        )
    if category == "聊天":
        return poi.category in {"咖啡", "茶馆", "书店"} or _poi_matches_term(poi, "聊天")
    return _poi_matches_term(poi, category)


def _find_existing_followup_stage_with_index(
    candidate: PlanCandidate,
    category: str | None,
) -> tuple[Stage | None, int | None]:
    if category is None:
        return None, None
    for idx, stage in enumerate(candidate.stages):
        poi = stage.selected_poi
        if poi is None:
            continue
        if _poi_matches_followup_category(poi, category):
            return stage, idx
    return None, None


def _find_latest_followup_stage_with_index(
    candidate: PlanCandidate,
) -> tuple[Stage | None, int | None]:
    for idx in range(len(candidate.stages) - 1, -1, -1):
        stage = candidate.stages[idx]
        if _stage_looks_like_followup(stage):
            return stage, idx
        poi = stage.selected_poi
        if poi is not None and _normalize_followup_category(poi.category) in {
            "小酒馆",
            "甜品",
            "咖啡",
            "茶馆",
            "书店",
        }:
            return stage, idx
    return None, None


def _followup_insert_index(candidate: PlanCandidate, anchor: str) -> int:
    if anchor == "before_dining":
        for idx, stage in enumerate(candidate.stages):
            if stage.stage_type == StageType.DINE:
                return idx
    if anchor == "after_dining":
        for idx in range(len(candidate.stages) - 1, -1, -1):
            if candidate.stages[idx].stage_type == StageType.DINE:
                return idx + 1
    return len(candidate.stages)


def _build_followup_stage(
    candidate: PlanCandidate,
    poi: POI,
    category: str,
    anchor: str = "after_dining",
) -> Stage:
    return Stage(
        stage_id=_new_stage_id(candidate, "followup"),
        stage_type=StageType.RELAX,
        name=_followup_stage_name(category, anchor),
        experience_goal=_followup_experience_goal(category, anchor),
        priority_role_id=None,
        duration_minutes=70 if category == "小酒馆" else 60,
        energy_level=1,
        constraints={"categories": [category], "tags": _followup_search_tags(category) or []},
        selected_poi=poi,
        fallback_pois=[],
        reasoning=_followup_reason(category, anchor),
    )


def _followup_stage_name(category: str, anchor: str = "after_dining") -> str:
    if category == "小酒馆":
        return "饭前小酒馆" if anchor == "before_dining" else "饭后小酒馆"
    if category == "聊天":
        return "找个地方聊天"
    prefix = "饭前" if anchor == "before_dining" else "饭后"
    return f"{prefix}{category}"


def _followup_experience_goal(category: str, anchor: str = "after_dining") -> str:
    before = anchor == "before_dining"
    if category == "小酒馆":
        if before:
            return "吃饭前找一个轻松的小酒馆或清吧坐一会儿，先聊天放松。"
        return "吃完饭后找一个轻松的小酒馆坐一会儿，聊天收尾。"
    if category == "聊天":
        if before:
            return "吃饭前先找一个适合坐下来聊天的地方，低强度开场。"
        return "找一个适合坐下来聊天的地方，低强度收尾。"
    if before:
        return f"吃饭前安排一个轻松的{category}环节，先坐下来聊天和缓冲。"
    return f"吃完饭后安排一个轻松的{category}环节，延长这次出门的余兴。"


def _followup_reason(category: str, anchor: str) -> str:
    anchor_text = (
        "用餐前"
        if anchor == "before_dining"
        else "饭后"
        if anchor == "after_dining"
        else "行程末尾"
    )
    return f"根据用户修改意见，在{anchor_text}新增{category}环节。"


def _followup_replace_reason(category: str) -> str:
    return f"根据用户修改意见，替换{category}后续环节。"


def _followup_remove_reason(category: str) -> str:
    return f"根据用户修改意见，取消{category}后续环节。"


def _find_dining_stage_with_index(candidate: PlanCandidate) -> tuple[Stage | None, int | None]:
    for idx, stage in enumerate(candidate.stages):
        if stage.stage_type == StageType.DINE:
            return stage, idx
    dining_terms = ("晚饭", "午饭", "餐", "饭", "用餐", "晚餐", "午餐")
    for idx, stage in enumerate(candidate.stages):
        if _stage_looks_like_followup(stage) or stage.stage_type == StageType.RELAX:
            continue
        text = " ".join(
            str(value)
            for value in (
                stage.name,
                stage.experience_goal,
                stage.reasoning,
                stage.selected_poi.category if stage.selected_poi else "",
                stage.selected_poi.name if stage.selected_poi else "",
            )
        )
        if any(term in text for term in dining_terms):
            return stage, idx
    return None, None


def _normalize_dining_category(value: str | None) -> str:
    if not value or value in {"都可以", "随便"}:
        return "餐厅"
    return value


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
    prefix = _same_clause_prefix(message[:index])
    suffix = _same_clause_suffix(message[index + len(keyword) :])
    window = f"{prefix}{keyword}{suffix}"
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


def _dining_search_categories(cuisine: str) -> list[str]:
    if cuisine in {"餐厅", "吃饭", "用餐"}:
        return ["餐厅", "轻食", "火锅", "桑拿鸡", "粤菜"]
    return [cuisine]


def _filter_dining_search_results(
    pois: list[POI],
    cuisine: str,
    *,
    allow_generic: bool,
) -> list[POI]:
    if cuisine in {"餐厅", "吃饭", "用餐", "都可以"}:
        return [poi for poi in pois if poi.category in _DINING_CATEGORIES]

    exact = [poi for poi in pois if poi.category == cuisine or _poi_matches_term(poi, cuisine)]
    if exact:
        return exact
    if allow_generic:
        return [poi for poi in pois if poi.category in _DINING_CATEGORIES]
    return []


def _poi_matches_term(poi: POI, term: str) -> bool:
    values = [
        poi.name,
        poi.category,
        poi.area or "",
        *poi.activity_tags,
        *poi.mood_tags,
        *poi.suitable_for,
        *poi.conflict_relief_tags,
    ]
    return any(term in str(value) for value in values if value)


def _merge_dining_constraints(
    constraints: dict[str, Any],
    cuisine: str,
) -> dict[str, Any]:
    merged = dict(constraints or {})
    categories = list(merged.get("categories") or [])
    if cuisine not in categories:
        categories.insert(0, cuisine)
    tags = list(merged.get("tags") or merged.get("标签") or [])
    for tag in ("晚饭", cuisine):
        if tag and tag not in tags:
            tags.append(tag)
    merged["categories"] = categories
    merged["tags"] = tags
    return merged


def _dining_stage_name(cuisine: str) -> str:
    if cuisine in {"餐厅", "吃饭", "用餐"}:
        return "晚饭"
    return f"{cuisine}晚饭"


def _dining_revision_reason(cuisine: str, excluded_categories: set[str]) -> str:
    if excluded_categories:
        excluded = "、".join(sorted(excluded_categories))
        if cuisine in {"餐厅", "吃饭", "用餐"}:
            return f"根据用户修改意见，避开{excluded}并改为其他餐饮。"
        return f"根据用户修改意见，避开{excluded}并改为{cuisine}。"
    return f"根据用户修改意见，把餐饮环节调整为{cuisine}。"


def _build_dining_stage(candidate: PlanCandidate, poi: POI, cuisine: str) -> Stage:
    return Stage(
        stage_id=_new_stage_id(candidate, "dine"),
        stage_type=StageType.DINE,
        name=_dining_stage_name(cuisine),
        experience_goal="补充体力，也给这次行程一个可坐下来聊天的收束点。",
        priority_role_id=None,
        duration_minutes=75,
        energy_level=1,
        constraints=_merge_dining_constraints({}, cuisine),
        selected_poi=poi,
        fallback_pois=[],
        reasoning=f"根据用户补充需求新增{cuisine}餐饮环节。",
    )


def _new_stage_id(candidate: PlanCandidate, suffix: str) -> str:
    existing = {stage.stage_id for stage in candidate.stages}
    index = len(candidate.stages) + 1
    while True:
        stage_id = f"{candidate.plan_id}_{suffix}_{index}"
        if stage_id not in existing:
            return stage_id
        index += 1


def _dining_insert_index(candidate: PlanCandidate, insert_anchor: str = "default") -> int:
    if insert_anchor == "before_dining":
        for idx, stage in enumerate(candidate.stages):
            if stage.stage_type == StageType.DINE:
                return idx
    for idx, stage in enumerate(candidate.stages):
        if stage.stage_type == StageType.RELAX:
            return idx
    return len(candidate.stages)


def _sort_pois_for_stage_insert(
    pois: list[POI],
    candidate: PlanCandidate,
    stage_idx: int,
) -> list[POI]:
    def adjacent_distance(poi: POI) -> float:
        total = 0.0
        if stage_idx > 0:
            prev = candidate.stages[stage_idx - 1].selected_poi
            if prev and prev.lat and prev.lon and poi.lat and poi.lon:
                total += _haversine_km(prev.lat, prev.lon, poi.lat, poi.lon)
        if stage_idx < len(candidate.stages):
            nxt = candidate.stages[stage_idx].selected_poi
            if nxt and nxt.lat and nxt.lon and poi.lat and poi.lon:
                total += _haversine_km(nxt.lat, nxt.lon, poi.lat, poi.lon)
        return total

    return sorted(pois, key=lambda poi: (adjacent_distance(poi), poi.avg_price or 0))


def _locked_poi_ids(locked_items: list[dict[str, Any]]) -> set[str]:
    return {
        str(item["id"]) for item in locked_items if item.get("type") == "poi" and item.get("id")
    }


def _tags_for_intents(intents: list[str], message: str) -> list[str]:
    tags: list[str] = []
    if "make_child_friendly" in intents:
        tags.extend(["亲子", "儿童"])
    if "make_less_tiring" in intents:
        tags.extend(["轻松", "休闲"])
    if "reduce_distance" in intents:
        tags.extend(["轻松", "休闲", "就近"])
    if "avoid_queue" in intents:
        tags.extend(["小众", "不排队"])
    if "lower_budget" in intents:
        tags.extend(["平价"])
    if "prefer_indoor" in intents:
        tags.append("室内")
    return tags


def _replacement_reason(intents: list[str], message: str) -> str:
    reasons = []
    if "reduce_distance" in intents:
        reasons.append("距离更近")
    if "avoid_queue" in intents:
        reasons.append("排队风险更低")
    if "prefer_indoor" in intents:
        reasons.append("室内场所")
    if "make_child_friendly" in intents:
        reasons.append("更适合孩子")
    if reasons:
        return f"替换为{'、'.join(reasons)}的地点。"
    return f"根据用户修改意见进行局部替换：{message[:80]}"


def _no_patch_reason(intents: list[str], warnings: list[str]) -> str:
    """Build a human-readable reason for why no patches were produced."""
    if any("锁定" in w for w in warnings):
        return "该地点已锁定，无法修改。建议解锁后重试。"
    if any("没有找到可取消" in w for w in warnings):
        return "没有找到可取消的后续环节，当前方案已保持不变。"
    if any("没有识别到要新增" in w for w in warnings):
        return "没有识别到要新增的后续活动类型，当前方案已保持不变。"
    if "avoid_queue" in intents and "reduce_distance" in intents:
        return "已搜索更近且低排队风险的替代地点，但未找到符合条件的选项。当前方案已是最优。"
    if "avoid_queue" in intents:
        return "已搜索低排队风险的替代地点，但同类场所排队风险相近，当前方案已是最优。"
    if "reduce_distance" in intents:
        return "已搜索更近的替代地点，但同类场所距离相近，当前方案已是最优。"
    if "prefer_indoor" in intents:
        return "已搜索室内替代场所，但未找到符合条件的选项。"
    return "已检查方案，没有找到需要强制替换的部分。"


def _revision_patch_summary(patches: list[PlanPatch]) -> str:
    parts: list[str] = []
    for patch in patches:
        new_value = patch.new_value or {}
        old_value = patch.old_value or {}
        new_name = str(new_value.get("name") or new_value.get("stage_name") or "新地点")
        old_name = str(old_value.get("name") or "")
        category = str(new_value.get("category") or "")
        requested_category = str(new_value.get("requested_category") or category)
        reason = patch.reason.strip("。") if patch.reason else ""

        if patch.patch_type == "add_dining_stage":
            label = _dining_summary_label(requested_category, category)
            text = f"已新增{label}：{new_name}"
        elif patch.patch_type == "replace_dining_stage":
            label = _dining_summary_label(requested_category, category)
            if old_name:
                text = f"已把晚饭从「{old_name}」换成{label}「{new_name}」"
            else:
                text = f"已把晚饭换成{label}「{new_name}」"
        elif patch.patch_type == "add_followup_stage":
            label = requested_category or category or "后续活动"
            anchor_text = _anchor_summary_label(str(new_value.get("anchor") or "after_last"))
            text = f"已在{anchor_text}新增{label}：{new_name}"
        elif patch.patch_type == "replace_followup_stage":
            label = requested_category or category or "后续活动"
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

    return "；".join(parts) if parts else "已根据你的意见完成局部调整。"


def _dining_summary_label(requested_category: str, actual_category: str) -> str:
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


def _poi_patch_value(poi: POI | None) -> dict[str, Any] | None:
    if poi is None:
        return None
    return {
        "poi_id": poi.id,
        "name": poi.name,
        "category": poi.category,
        "indoor": poi.indoor,
        "queue_risk": poi.queue_risk,
        "area": poi.area,
    }


def _dining_patch_value(poi: POI | None, requested_category: str) -> dict[str, Any] | None:
    value = _poi_patch_value(poi)
    if value is None:
        return None
    value["requested_category"] = requested_category
    return value


def _coerce_poi(value: Any) -> POI | None:
    if isinstance(value, POI):
        return value
    if isinstance(value, dict):
        try:
            return POI.model_validate(value)
        except Exception:
            return None
    return None


def _build_simple_timeline(
    candidate: PlanCandidate,
    state: AgentState,
) -> list[TimelineItem]:
    current = state.request.start_time
    timeline: list[TimelineItem] = []
    for index, stage in enumerate(candidate.stages):
        poi = stage.selected_poi
        if index > 0:
            timeline.append(
                TimelineItem(
                    time=current.strftime("%H:%M"),
                    type=TimelineItemType.BUFFER,
                    duration_minutes=10,
                    estimated_cost=0,
                    notes="局部修改后保留缓冲时间。",
                )
            )
            current += timedelta(minutes=10)
        item_type = TimelineItemType.ACTIVITY
        if str(stage.stage_type) == "dine":
            item_type = TimelineItemType.DINING
        timeline.append(
            TimelineItem(
                time=current.strftime("%H:%M"),
                type=item_type,
                poi_id=poi.id if poi else None,
                poi_name=poi.name if poi else stage.name,
                duration_minutes=stage.duration_minutes,
                estimated_cost=float(poi.avg_price or 0) if poi else 0,
                notes=stage.experience_goal,
            )
        )
        current += timedelta(minutes=stage.duration_minutes)
    return timeline
