from statistics import mean

from local_explorer_agent.app.domain.enums import RoleType, StageType
from local_explorer_agent.app.domain.models import (
    GroupContext,
    PlanCandidate,
    SatisfactionScore,
)


def score_candidate(candidate: PlanCandidate, group_context: GroupContext) -> PlanCandidate:
    scores: list[SatisfactionScore] = []
    priority_role_ids = {
        stage.priority_role_id for stage in candidate.stages if stage.priority_role_id
    }
    stage_types = {stage.stage_type for stage in candidate.stages}

    for role in group_context.roles:
        score = 3.0
        reasons: list[str] = []
        sacrificed: list[str] = []
        compensation: str | None = None

        if role.role_id in priority_role_ids:
            score += 0.8
            reasons.append("至少有一个阶段优先满足该角色")

        if role.role_type == RoleType.CHILD and StageType.ENERGY_RELEASE in stage_types:
            score += 0.7
            reasons.append("安排了释放体力和互动阶段")

        if role.role_type == RoleType.SPOUSE:
            has_diet_stage = any(
                stage.stage_type == StageType.DINE and "low_calorie" in stage.constraints
                for stage in candidate.stages
            )
            if has_diet_stage:
                score += 0.6
                reasons.append("餐饮阶段照顾低负担饮食")
            elif any(role.hard_constraints):
                sacrificed.append("餐饮健康约束不够明确")
            if "约会" in candidate.theme or "约会" in candidate.title:
                score += 0.3
                reasons.append("方案围绕约会氛围和聊天体验设计")

        if role.role_type == RoleType.USER and StageType.RELAX in stage_types:
            score += 0.4
            reasons.append("保留了轻松收尾和成人恢复空间")

        if role.role_id not in priority_role_ids:
            sacrificed.append("没有作为阶段第一优先级")
            compensation = "通过低转场、短排队和备选方案降低后悔感"

        bounded_score = min(5.0, round(score, 2))
        scores.append(
            SatisfactionScore(
                role_id=role.role_id,
                score=bounded_score,
                reasons=reasons or ["满足基础硬约束"],
                sacrificed_points=sacrificed,
                compensation=compensation,
            )
        )

    values = [item.score for item in scores] or [0]
    candidate.satisfaction_scores = scores
    candidate.overall_score = round(mean(values), 2)
    candidate.min_role_score = round(min(values), 2)
    candidate.fairness_score = round(max(0.0, 5.0 - (max(values) - min(values))), 2)
    return candidate


def choose_recommended_candidate(candidates: list[PlanCandidate]) -> PlanCandidate:
    return max(
        candidates,
        key=lambda plan: (
            plan.min_role_score * 0.4 + plan.fairness_score * 0.3 + plan.overall_score * 0.3,
            plan.overall_score,
        ),
    )
