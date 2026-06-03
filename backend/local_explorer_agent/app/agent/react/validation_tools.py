"""ConstraintValidatorTool and PlanRepairTool for ReAct runtime."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from local_explorer_agent.app.domain.enums import RoleType
from local_explorer_agent.app.domain.models import PlanCandidate, Stage
from local_explorer_agent.app.domain.validation import PlanValidationResult, PlanViolation
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState

logger = logging.getLogger(__name__)

_BLOCKING_SEVERITY = 4

_CHILD_SUITABLE_KEYWORDS = {"child", "children", "kid", "kids", "儿童", "亲子", "家庭", "孩子"}
_HIGH_CALORIE_CATEGORIES = {"火锅", "烧烤", "烤肉"}
_DIET_KEYWORDS = {"减肥", "减脂", "低卡", "低热量", "清淡", "控糖", "健身"}
_LOW_ENERGY_KEYWORDS = {"不累", "轻松", "别走太多", "休闲", "慢节奏"}
_DISTANCE_KEYWORDS = {"不远", "别太远", "近一点", "不要太远"}


class EmptyArgs(BaseModel):
    """Tools that read all inputs from AgentState use this empty schema."""


class ConstraintValidatorTool:
    name = "validate_plan_constraints"
    description = "检查候选方案是否违反硬约束（时间、城市、安全、距离等）"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        violations = _validate_candidates(state)
        blocking = [v for v in violations if v.severity >= _BLOCKING_SEVERITY]
        warnings = [v for v in violations if v.severity < _BLOCKING_SEVERITY]
        result = PlanValidationResult(
            passed=len(blocking) == 0,
            blocking_violations=blocking,
            warnings=warnings,
        )
        return ToolResult(success=True, data=result.model_dump())


def _validate_candidates(state: AgentState) -> list[PlanViolation]:
    violations: list[PlanViolation] = []

    if not state.candidate_plans:
        violations.append(PlanViolation(
            violation_type="no_candidates",
            message="没有候选方案可供验证",
            severity=5,
        ))
        return violations

    for plan in state.candidate_plans:
        violations.extend(_validate_single_plan(plan, state))

    return violations


def _validate_single_plan(plan: PlanCandidate, state: AgentState) -> list[PlanViolation]:
    violations: list[PlanViolation] = []
    req = state.request
    ctx = state.inferred_context
    intake = state.requirement_intake

    if intake is not None and len(plan.stages) > intake.activity_count.max:
        severity = 5 if intake.activity_count.max == 1 else 3
        violations.append(PlanViolation(
            violation_type="activity_count_exceeded",
            message=(
                f"用户需求最多安排 {intake.activity_count.max} 个核心环节，"
                f"但方案包含 {len(plan.stages)} 个阶段"
            ),
            severity=severity,
            affected_plan_id=plan.plan_id,
            suggested_repair_action="reduce_stage_count",
        ))

    has_child = ctx is not None and any(r.role_type == RoleType.CHILD for r in ctx.roles)
    has_elder = ctx is not None and any(r.role_type == RoleType.ELDER for r in ctx.roles)
    needs_low_energy = (
        has_elder
        or (
            ctx is not None
            and any(kw in (ctx.input_query or req.query) for kw in _LOW_ENERGY_KEYWORDS)
        )
    )
    diet_text_parts = [req.query]
    if ctx is not None:
        diet_text_parts.extend([
            ctx.input_query,
            *ctx.inferred_constraints,
            *[
                item
                for r in ctx.roles
                for item in (
                    r.hard_constraints
                    + r.soft_preferences
                    + r.hidden_needs
                    + r.risk_points
                )
            ],
        ])
    needs_diet = any(
        keyword in str(part)
        for part in diet_text_parts
        for keyword in _DIET_KEYWORDS
    )
    distance_sensitive = any(kw in req.query for kw in _DISTANCE_KEYWORDS)

    for stage in plan.stages:
        poi = stage.selected_poi
        if poi is None:
            continue

        if poi.city != req.city:
            violations.append(PlanViolation(
                violation_type="city_mismatch",
                message=f"POI '{poi.name}' 城市为 {poi.city}，但请求城市为 {req.city}",
                severity=5,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if has_child and not _is_suitable_for_children(poi, stage):
            message = (
                f"POI '{poi.name}' 不适合儿童"
                f"（suitable_for={poi.suitable_for}, category={poi.category}）"
            )
            violations.append(PlanViolation(
                violation_type="child_safety",
                message=message,
                severity=4,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if needs_low_energy and poi.energy_level >= 4:
            violations.append(PlanViolation(
                violation_type="energy_too_high",
                message=f"POI '{poi.name}' 体力要求过高（energy_level={poi.energy_level}）",
                severity=3,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if needs_diet and stage.stage_type == "dine" and poi.category in _HIGH_CALORIE_CATEGORIES:
            violations.append(PlanViolation(
                violation_type="diet_conflict",
                message=f"餐饮 POI '{poi.name}'（{poi.category}）与低卡饮食需求冲突",
                severity=2,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if poi.queue_risk == "high":
            violations.append(PlanViolation(
                violation_type="queue_risk",
                message=f"POI '{poi.name}' 排队风险高（queue_risk=high）",
                severity=3,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if not poi.indoor and _has_weather_concern(req.query, poi):
            violations.append(PlanViolation(
                violation_type="weather_conflict",
                message=f"户外 POI '{poi.name}' 可能受天气影响",
                severity=3,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

        if _is_closed_at_plan_time(poi, req.start_time):
            violations.append(PlanViolation(
                violation_type="closed_poi",
                message=f"POI '{poi.name}' 在计划时间可能未营业（open_hours={poi.open_hours}）",
                severity=5,
                affected_plan_id=plan.plan_id,
                affected_poi_id=poi.id,
                suggested_repair_action="replace_poi",
            ))

    if distance_sensitive:
        total_walking = sum(
            seg.get("walking_minutes", 0) for seg in plan.route_segments
        )
        total_distance = sum(
            seg.get("distance_meters", 0) for seg in plan.route_segments
        )
        if total_distance > 5000 or total_walking > 40:
            message = (
                f"总步行 {total_walking} 分钟 / 总距离 {total_distance} 米，"
                "超出用户距离预期"
            )
            violations.append(PlanViolation(
                violation_type="distance_too_far",
                message=message,
                severity=3,
                affected_plan_id=plan.plan_id,
                suggested_repair_action="reduce_distance",
            ))

    poi_ids = [s.selected_poi.id for s in plan.stages if s.selected_poi]
    for i in range(len(poi_ids) - 1):
        from_id, to_id = poi_ids[i], poi_ids[i + 1]
        has_segment = any(
            seg.get("from") == from_id and seg.get("to") == to_id
            for seg in plan.route_segments
        )
        if not has_segment:
            violations.append(PlanViolation(
                violation_type="missing_route",
                message=f"POI {from_id} → {to_id} 之间缺少路线信息",
                severity=4,
                affected_plan_id=plan.plan_id,
                suggested_repair_action="calculate_routes",
            ))

    if plan.timeline:
        total_minutes = sum(item.duration_minutes for item in plan.timeline)
        if total_minutes > req.duration_minutes + 30:
            violations.append(PlanViolation(
                violation_type="time_overrun",
                message=f"方案总时长 {total_minutes} 分钟超出请求的 {req.duration_minutes} 分钟",
                severity=3,
                affected_plan_id=plan.plan_id,
            ))

    return violations


def _is_suitable_for_children(poi: Any, stage: Stage) -> bool:
    suitable_text = " ".join(str(item) for item in poi.suitable_for)
    if any(kw in suitable_text for kw in _CHILD_SUITABLE_KEYWORDS):
        return True
    child_friendly_categories = {
        "亲子空间",
        "游乐园",
        "公园",
        "书店",
        "展览",
        "手作体验",
        "餐厅",
        "轻食",
        "咖啡",
        "甜品",
        "茶馆",
    }
    if poi.category in child_friendly_categories:
        return True
    if stage.stage_type == "energy_release":
        return True
    return False


def _is_closed_at_plan_time(poi: Any, start_time: Any) -> bool:
    if not poi.open_hours:
        return False
    hours = poi.open_hours.lower()
    if "休息" in hours or "closed" in hours or "周一至周日" not in hours and "全天" not in hours:
        try:
            hour = start_time.hour
            match = re.search(r"(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})", hours)
            if match:
                open_h = int(match.group(1))
                close_h = int(match.group(3))
                if close_h > open_h:
                    return hour < open_h or hour >= close_h
                else:
                    return hour < open_h and hour >= close_h
        except (AttributeError, ValueError):
            pass
    return False


def _has_weather_concern(query: str, poi: Any) -> bool:
    weather_keywords = {"下雨", "雨天", "高温", "太热", "太晒", "暴晒"}
    if any(kw in query for kw in weather_keywords):
        return True
    weather_fit_text = str(poi.weather_fit)
    if (
        poi.weather_fit
        and "rain" not in weather_fit_text.lower()
        and "雨" not in weather_fit_text
    ):
        return False
    return False


# ── PlanRepairTool ────────────────────────────────────────────────────────


class PlanRepairTool:
    name = "repair_plan"
    description = "根据验证结果修复候选方案中的违规问题"
    args_schema = EmptyArgs
    is_execution_tool = False
    requires_confirmation = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        if state.validation_result is None:
            return ToolResult(success=False, error_message="validation_result is required")

        actions_taken: list[str] = []
        updated_plans = []

        for plan in state.candidate_plans:
            plan_violations = [
                v for v in state.validation_result.blocking_violations
                if v.affected_plan_id == plan.plan_id
            ]
            if not plan_violations:
                updated_plans.append(plan.model_dump())
                continue

            repaired = _repair_plan(plan, plan_violations, actions_taken)
            updated_plans.append(repaired.model_dump())

        return ToolResult(
            success=True,
            data={
                "candidates": updated_plans,
                "repair_actions_taken": actions_taken,
            },
        )


def _repair_plan(
    plan: PlanCandidate,
    violations: list[PlanViolation],
    actions_taken: list[str],
) -> PlanCandidate:
    for violation in violations:
        if violation.affected_poi_id:
            _try_replace_poi(plan, violation, actions_taken)
        elif violation.violation_type == "distance_too_far":
            _handle_distance(plan, violation, actions_taken)
        elif violation.violation_type == "activity_count_exceeded":
            _reduce_stage_count(plan, actions_taken)
        else:
            actions_taken.append(
                f"无法自动修复 '{violation.violation_type}': {violation.message}"
            )

    return plan


def _try_replace_poi(
    plan: PlanCandidate,
    violation: PlanViolation,
    actions_taken: list[str],
) -> None:
    for stage in plan.stages:
        if stage.selected_poi and stage.selected_poi.id == violation.affected_poi_id:
            if stage.fallback_pois:
                old_name = stage.selected_poi.name
                stage.selected_poi = stage.fallback_pois[0]
                actions_taken.append(
                    f"将 '{old_name}' 替换为备选 '{stage.selected_poi.name}'"
                )
            else:
                message = (
                    f"POI '{stage.selected_poi.name}' 存在 "
                    f"{violation.violation_type} 问题但无备选方案"
                )
                actions_taken.append(
                    message
                )
            break


def _handle_distance(
    plan: PlanCandidate,
    violation: PlanViolation,
    actions_taken: list[str],
) -> None:
    plan.tradeoff_summary += " [距离较远，已降低推荐优先级]"
    actions_taken.append("标记方案距离较远，降低推荐优先级")


def _reduce_stage_count(
    plan: PlanCandidate,
    actions_taken: list[str],
) -> None:
    if len(plan.stages) <= 1:
        return
    original_count = len(plan.stages)
    preferred = next(
        (stage for stage in plan.stages if str(stage.stage_type) == "dine"),
        plan.stages[0],
    )
    plan.stages = [preferred]
    plan.timeline = []
    plan.route_segments = []
    plan.tradeoff_summary += " [已按用户单一目标收敛为一个核心环节]"
    actions_taken.append(f"将 {original_count} 个阶段收敛为 1 个核心环节")
