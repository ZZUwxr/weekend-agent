from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.schemas import NegotiationStrategyListOutput
from local_explorer_agent.app.domain.enums import GroupType, StrategyType
from local_explorer_agent.app.domain.models import Conflict, GroupContext, NegotiationStrategy


class NegotiationSkill:
    name = "negotiation"

    def __init__(self, prompt_runner: JSONPromptRunner | None = None) -> None:
        self.prompt_runner = prompt_runner

    def run(
        self,
        *,
        group_context: GroupContext,
        conflicts: list[Conflict],
    ) -> list[NegotiationStrategy]:
        if self.prompt_runner is not None:
            output = self.prompt_runner.run(
                "negotiation.md",
                {
                    "group_context": group_context.model_dump_json(),
                    "conflicts": [conflict.model_dump() for conflict in conflicts],
                },
                NegotiationStrategyListOutput,
                fallback=lambda: NegotiationStrategyListOutput(
                    items=self._run_rule_based(group_context=group_context, conflicts=conflicts)
                ),
            )
            return output.items
        return self._run_rule_based(group_context=group_context, conflicts=conflicts)

    def _run_rule_based(
        self,
        *,
        group_context: GroupContext,
        conflicts: list[Conflict],
    ) -> list[NegotiationStrategy]:
        if not conflicts:
            return []

        conflict_ids = [conflict.conflict_id for conflict in conflicts]
        role_ids = {role.role_id for role in group_context.roles}
        if group_context.group_type == GroupType.FRIENDS:
            priority_order = [
                self._pick(role_ids, "photo_oriented_role"),
                self._pick(role_ids, "budget_sensitive_role"),
                self._pick(role_ids, "practical_oriented_role"),
                self._pick(role_ids, "lively_oriented_role"),
            ]
            scene_filters = ["有氛围但不高价", "可拍照", "路线顺", "可聊天", "少排队"]
            compensation_focus = "被牺牲的朋友必须在下一阶段获得预算、效率或氛围上的补偿"
            min_regret_floor = 3.6
        elif group_context.group_type == GroupType.FAMILY:
            priority_order = [
                self._pick(role_ids, "child_5yo"),
                self._pick(role_ids, "spouse_dieter"),
                self._pick(role_ids, "adult_user"),
            ]
            scene_filters = ["亲子友好", "低负担餐饮", "低转场", "可休息", "少排队"]
            compensation_focus = "成人陪伴成本、减脂餐饮约束和孩子放电需求需要轮流被看见"
            min_regret_floor = 3.5
        elif group_context.group_type == GroupType.COUPLE:
            priority_order = [
                self._pick(role_ids, "spouse_partner"),
                self._pick(role_ids, "spouse_dieter"),
                self._pick(role_ids, "adult_user"),
            ]
            scene_filters = ["适合聊天", "有约会氛围", "少排队", "低转场", "成人约会场景"]
            compensation_focus = "氛围感、聊天舒适度和餐饮体验需要轮流被看见"
            min_regret_floor = 3.7
        elif group_context.group_type == GroupType.SOLO:
            priority_order = [self._pick(role_ids, "adult_user")]
            scene_filters = ["安静", "可自由调整", "低转场", "少排队", "单人友好"]
            compensation_focus = "独处路线要保留节奏自由和低后悔点"
            min_regret_floor = 3.6
        else:
            priority_order = [self._pick(role_ids, "adult_user")]
            scene_filters = ["成人通用", "轻松", "低转场", "少排队", "低后悔"]
            compensation_focus = "需求未明确时先给低后悔成人通用路线，等待用户继续细化"
            min_regret_floor = 3.5

        return [
            NegotiationStrategy(
                strategy_id="strategy_rotate_001",
                strategy_type=StrategyType.ROTATE_PRIORITY,
                target_conflicts=conflict_ids,
                explanation="把不同角色的优先级分摊到不同阶段，避免任何角色全程让步。",
                stage_policy={
                    "优先级顺序": priority_order,
                    "落地规则": "每个主要角色至少拥有一个被明确优先考虑的阶段。",
                    "阶段约束": scene_filters,
                },
                compensation_policy={
                    "识别输家": (
                        "若某角色没有优先阶段，或其硬约束只被口头提及没有落到阶段约束中，"
                        "即视为被牺牲。"
                    ),
                    "默认补偿": compensation_focus,
                },
            ),
            NegotiationStrategy(
                strategy_id="strategy_soften_001",
                strategy_type=StrategyType.SOFTEN_CONFLICT,
                target_conflicts=[item.conflict_id for item in conflicts if item.severity >= 3],
                explanation="把看似冲突的诉求转成可以同时筛选地点和阶段的柔性条件。",
                stage_policy={
                    "地点筛选倾向": scene_filters,
                    "路线筛选倾向": ["短转场", "少排队", "天气风险低", "失败后可替换"],
                    "冲突软化方式": (
                        "把冲突要求写进同一个阶段的 constraints，"
                        "而不是让某个角色单独妥协。"
                    ),
                },
                compensation_policy={
                    "高强度后补偿": "高能量或高氛围阶段之后必须接低压力阶段。",
                    "硬约束补偿": "预算、饮食、路线效率等硬约束优先用地点属性自然满足。",
                },
            ),
            NegotiationStrategy(
                strategy_id="strategy_compensate_001",
                strategy_type=StrategyType.COMPENSATE_LOSER,
                target_conflicts=conflict_ids,
                explanation="当某阶段明显优先满足一个角色时，用下一阶段或转场设计补偿其他角色。",
                stage_policy={
                    "补偿触发": (
                        "某角色连续两个阶段不是 priority_role_id，"
                        "或其 risk_points 被阶段放大。"
                    ),
                    "补偿阶段类型": ["dine", "relax", "explore"],
                    "补偿对象顺序": priority_order,
                },
                compensation_policy={
                    "补偿方式": "减少下一段排队和步行，或给被牺牲角色安排明确偏好的活动/餐饮。",
                    "最低满意度保护": (
                        f"若预估任一角色低于 {min_regret_floor} 分，"
                        "必须缩短牺牲阶段或换成更兼容的阶段。"
                    ),
                },
            ),
            NegotiationStrategy(
                strategy_id="strategy_min_regret_001",
                strategy_type=StrategyType.MIN_REGRET,
                target_conflicts=conflict_ids,
                explanation="推荐方案优先选择没有明显短板的组合，避免平均分高但某个角色明显不满意。",
                stage_policy={
                    "推荐排序": (
                        "优先提高 min_role_score，再看 fairness_score，最后才看 overall_score。"
                    ),
                    "避免项": ["长排队", "长转场", "只服务单一角色", "高预算压力"],
                    "保底条件": scene_filters,
                },
                compensation_policy={
                    "最低角色分下限": min_regret_floor,
                    "低于下限处理": "缩短牺牲角色不喜欢的阶段，并增加替代补偿。",
                },
            ),
        ]

    def _pick(self, role_ids: set[str], preferred: str) -> str:
        if preferred in role_ids:
            return preferred
        if not role_ids:
            return preferred
        if preferred.startswith("child"):
            return next(
                (role_id for role_id in sorted(role_ids) if role_id.startswith("child")),
                preferred,
            )
        if preferred.startswith("spouse"):
            return next(
                (role_id for role_id in sorted(role_ids) if role_id.startswith("spouse")),
                preferred,
            )
        if preferred.startswith("adult") or preferred.startswith("user"):
            return next(
                (role_id for role_id in sorted(role_ids) if role_id.startswith("adult")),
                preferred,
            )
        return sorted(role_ids)[0]
