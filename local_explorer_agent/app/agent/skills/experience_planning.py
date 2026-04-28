from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.schemas import PlanCandidateListOutput
from local_explorer_agent.app.domain.enums import PlanType, StageType
from local_explorer_agent.app.domain.models import (
    Conflict,
    GroupContext,
    NegotiationStrategy,
    PlanCandidate,
    Stage,
)


class ExperiencePlanningSkill:
    name = "experience_planning"

    def __init__(self, prompt_runner: JSONPromptRunner | None = None) -> None:
        self.prompt_runner = prompt_runner

    def run(
        self,
        *,
        group_context: GroupContext,
        conflicts: list[Conflict],
        negotiation_strategies: list[NegotiationStrategy],
    ) -> list[PlanCandidate]:
        if self.prompt_runner is not None:
            output = self.prompt_runner.run(
                "experience_planning.md",
                {
                    "group_context": group_context.model_dump_json(),
                    "conflicts": [conflict.model_dump() for conflict in conflicts],
                    "negotiation_strategies": [
                        strategy.model_dump() for strategy in negotiation_strategies
                    ],
                },
                PlanCandidateListOutput,
                fallback=lambda: PlanCandidateListOutput(
                    items=self._run_rule_based(
                        group_context=group_context,
                        conflicts=conflicts,
                        negotiation_strategies=negotiation_strategies,
                    )
                ),
            )
            return output.items
        return self._run_rule_based(
            group_context=group_context,
            conflicts=conflicts,
            negotiation_strategies=negotiation_strategies,
        )

    def _run_rule_based(
        self,
        *,
        group_context: GroupContext,
        conflicts: list[Conflict],
        negotiation_strategies: list[NegotiationStrategy],
    ) -> list[PlanCandidate]:
        del conflicts
        strategies = self._strategies_by_type(negotiation_strategies)
        if group_context.group_type == "friends":
            return self._build_friends_plans(group_context, strategies)
        return self._build_family_plans(group_context, strategies)

    def _build_family_plans(
        self,
        group_context: GroupContext,
        strategies: dict[str, NegotiationStrategy],
    ) -> list[PlanCandidate]:
        child_id = self._role_id(group_context, "child_5yo", "child")
        spouse_id = self._role_id(group_context, "spouse_dieter", "spouse")
        adult_id = self._role_id(group_context, "adult_user", "adult")
        return [
            PlanCandidate(
                plan_id="plan_a",
                plan_type=PlanType.PLAN_A,
                title="先放电再轻食",
                theme="孩子先释放体力，成人用低压力餐饮和短转场收回来",
                strategy=strategies.get("rotate_priority"),
                tradeoff_summary="先满足孩子，可能牺牲一点成人开场舒适度，因此后段安排轻食和放松补偿。",
                stages=[
                    Stage(
                        stage_id="stage_a_1",
                        stage_type=StageType.ENERGY_RELEASE,
                        name="亲子互动放电",
                        experience_goal="先满足5岁孩子的互动和体力释放需求，降低后续阶段的不确定性",
                        priority_role_id=child_id,
                        duration_minutes=75,
                        energy_level=4,
                        constraints={
                            "标签": ["释放体力", "亲子", "互动"],
                            "categories": ["亲子空间", "公园"],
                            "avoid_queue": True,
                        },
                        reasoning="先处理最高波动角色，家庭行程会更稳。",
                    ),
                    Stage(
                        stage_id="stage_a_2",
                        stage_type=StageType.DINE,
                        name="轻负担晚餐",
                        experience_goal="照顾减脂需求，同时保留正常家庭用餐氛围",
                        priority_role_id=spouse_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "低卡", "聊天"],
                            "categories": ["轻食"],
                            "low_calorie": True,
                            "avoid_queue": True,
                        },
                        reasoning="把低卡变成地点自然属性，不把减脂者特殊化。",
                    ),
                    Stage(
                        stage_id="stage_a_3",
                        stage_type=StageType.RELAX,
                        name="低刺激收尾",
                        experience_goal="给成人用户聊天和恢复空间，也让孩子从高能量切换下来",
                        priority_role_id=adult_id,
                        duration_minutes=45,
                        energy_level=1,
                        constraints={
                            "标签": ["安静", "松弛", "休息"],
                            "categories": ["书店", "咖啡"],
                            "indoor": True,
                        },
                        reasoning="用放松阶段补偿前段亲子优先带来的成人参与感缺口。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_b",
                plan_type=PlanType.PLAN_B,
                title="稳妥室内线",
                theme="弱化天气和排队风险，优先选择室内、短转场、低后悔点",
                strategy=strategies.get("soften_conflict"),
                tradeoff_summary="牺牲一点户外释放感，换取更高的可控性和低转场压力。",
                stages=[
                    Stage(
                        stage_id="stage_b_1",
                        stage_type=StageType.EXPLORE,
                        name="室内轻探索",
                        experience_goal="兼顾孩子新鲜感和成人轻松参与，避免一开始就过度消耗",
                        priority_role_id=child_id,
                        duration_minutes=60,
                        energy_level=2,
                        constraints={
                            "标签": ["亲子", "低刺激", "室内"],
                            "categories": ["书店", "亲子空间"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="把活动强度降到中低，降低疲惫风险。",
                    ),
                    Stage(
                        stage_id="stage_b_2",
                        stage_type=StageType.DINE,
                        name="健康轻食",
                        experience_goal="餐饮先满足减脂硬约束，减少临场纠结",
                        priority_role_id=spouse_id,
                        duration_minutes=60,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "低卡", "聊天"],
                            "categories": ["轻食"],
                            "low_calorie": True,
                            "avoid_queue": True,
                        },
                        reasoning="用餐是减脂冲突的关键决策点。",
                    ),
                    Stage(
                        stage_id="stage_b_3",
                        stage_type=StageType.RELAX,
                        name="咖啡短休",
                        experience_goal="用短时休息作为成人用户的明确补偿",
                        priority_role_id=adult_id,
                        duration_minutes=35,
                        energy_level=1,
                        constraints={
                            "标签": ["聊天", "休息", "补偿"],
                            "categories": ["咖啡", "书店"],
                            "indoor": True,
                        },
                        reasoning="收尾不贪多，减少超时和反悔。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_recommended",
                plan_type=PlanType.RECOMMENDED,
                title="推荐：亲子放电 + 自然低卡 + 松弛收尾",
                theme="在孩子释放、配偶饮食和成人参与感之间取更均衡的最小后悔解",
                strategy=strategies.get("min_regret"),
                tradeoff_summary="推荐不是简单追求平均分最高，而是优先避免任何角色被明显牺牲。",
                recommendation_reason=(
                    "该方案不是简单平均分最高，而是同时兼顾 overall_score、min_role_score "
                    "和 fairness_score：孩子先被满足，减脂餐饮自然落地，成人也有明确补偿阶段。"
                ),
                stages=[
                    Stage(
                        stage_id="stage_r_1",
                        stage_type=StageType.ENERGY_RELEASE,
                        name="可控亲子放电",
                        experience_goal="用室内亲子活动先满足孩子，同时控制排队和天气变量",
                        priority_role_id=child_id,
                        duration_minutes=70,
                        energy_level=4,
                        constraints={
                            "标签": ["释放体力", "亲子", "互动"],
                            "categories": ["亲子空间"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="推荐方案优先处理最容易影响全局的孩子状态。",
                    ),
                    Stage(
                        stage_id="stage_r_2",
                        stage_type=StageType.DINE,
                        name="自然低卡用餐",
                        experience_goal="把减脂约束融入普通家庭用餐，不制造心理负担",
                        priority_role_id=spouse_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "低卡", "聊天"],
                            "categories": ["轻食"],
                            "low_calorie": True,
                            "avoid_queue": True,
                        },
                        reasoning="餐饮是硬约束，且应避免被特殊对待。",
                    ),
                    Stage(
                        stage_id="stage_r_3",
                        stage_type=StageType.RELAX,
                        name="书店松弛收尾",
                        experience_goal="给成人聊天与恢复空间，并让孩子自然降速",
                        priority_role_id=adult_id,
                        duration_minutes=45,
                        energy_level=1,
                        constraints={
                            "标签": ["安静", "松弛", "休息"],
                            "categories": ["书店"],
                            "indoor": True,
                        },
                        reasoning="书店比咖啡更兼容亲子降速和成人松弛。",
                    ),
                ],
            ),
        ]

    def _build_friends_plans(
        self,
        group_context: GroupContext,
        strategies: dict[str, NegotiationStrategy],
    ) -> list[PlanCandidate]:
        photo_id = self._role_id(group_context, "photo_oriented_role", "friend")
        practical_id = self._role_id(group_context, "practical_oriented_role", "friend")
        budget_id = self._role_id(group_context, "budget_sensitive_role", "friend")
        lively_id = self._role_id(group_context, "lively_oriented_role", "friend")
        return [
            PlanCandidate(
                plan_id="plan_a",
                plan_type=PlanType.PLAN_A,
                title="氛围拍照优先线",
                theme="先满足出片和周末感，再用轻食和短休补偿预算与效率",
                strategy=strategies.get("rotate_priority"),
                tradeoff_summary="拍照氛围更强，但需要用后续低预算、少转场阶段补偿实用导向朋友。",
                stages=[
                    Stage(
                        stage_id="stage_fa_1",
                        stage_type=StageType.EXPLORE,
                        name="出片轻探索",
                        experience_goal="给拍照导向朋友一个明确的氛围高点",
                        priority_role_id=photo_id,
                        duration_minutes=65,
                        energy_level=2,
                        constraints={
                            "标签": ["拍照", "文艺", "有氛围"],
                            "categories": ["书店", "公园", "咖啡"],
                            "avoid_queue": True,
                        },
                        reasoning="朋友局需要一个能被记住和分享的开场。",
                    ),
                    Stage(
                        stage_id="stage_fa_2",
                        stage_type=StageType.DINE,
                        name="预算友好轻餐",
                        experience_goal="控制客单价，避免预算敏感朋友承压",
                        priority_role_id=budget_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "聊天", "性价比"],
                            "categories": ["轻食", "咖啡"],
                            "avoid_queue": True,
                            "budget_level": "medium_low",
                        },
                        reasoning="用餐阶段最容易放大预算压力，需要明确保护。",
                    ),
                    Stage(
                        stage_id="stage_fa_3",
                        stage_type=StageType.RELAX,
                        name="顺路聊天收尾",
                        experience_goal="降低转场和疲惫，让实用导向朋友不觉得折腾",
                        priority_role_id=practical_id,
                        duration_minutes=40,
                        energy_level=1,
                        constraints={
                            "标签": ["聊天", "休息", "路线顺"],
                            "categories": ["咖啡", "书店"],
                            "indoor": True,
                        },
                        reasoning="用低强度收尾补偿前段氛围优先。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_b",
                plan_type=PlanType.PLAN_B,
                title="效率舒适优先线",
                theme="先保证不折腾和预算可控，再给氛围导向朋友保留拍照节点",
                strategy=strategies.get("soften_conflict"),
                tradeoff_summary="路线和预算更稳，但氛围高点会更克制。",
                stages=[
                    Stage(
                        stage_id="stage_fb_1",
                        stage_type=StageType.EXPLORE,
                        name="近距离轻逛",
                        experience_goal="用短转场、低排队的轻探索建立安全底盘",
                        priority_role_id=practical_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["路线顺", "低刺激", "少排队"],
                            "categories": ["书店", "咖啡"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="先降低折腾感，后面才有空间安排氛围。",
                    ),
                    Stage(
                        stage_id="stage_fb_2",
                        stage_type=StageType.DINE,
                        name="可聊天轻食",
                        experience_goal="兼顾预算和聊天氛围，避免餐饮成为分歧点",
                        priority_role_id=budget_id,
                        duration_minutes=60,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "聊天", "性价比"],
                            "categories": ["轻食"],
                            "avoid_queue": True,
                            "budget_level": "medium_low",
                        },
                        reasoning="预算敏感诉求必须落到餐饮选择里。",
                    ),
                    Stage(
                        stage_id="stage_fb_3",
                        stage_type=StageType.EXPLORE,
                        name="短时氛围补偿",
                        experience_goal="给热闹和拍照导向朋友一个轻量补偿点",
                        priority_role_id=lively_id,
                        duration_minutes=40,
                        energy_level=2,
                        constraints={
                            "标签": ["热闹", "拍照", "周末感"],
                            "categories": ["公园", "咖啡", "书店"],
                            "avoid_queue": True,
                        },
                        reasoning="不让效率方案变成完全无趣的保守路线。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_recommended",
                plan_type=PlanType.RECOMMENDED,
                title="推荐：轻氛围 + 低预算餐 + 顺路收尾",
                theme="把拍照、预算、效率和热闹感拆到不同阶段，降低单点冲突",
                strategy=strategies.get("min_regret"),
                tradeoff_summary="推荐不是简单平均分最高，而是避免拍照、预算或效率任一侧成为明显输家。",
                recommendation_reason=(
                    "该方案不是简单平均分最高，而是兼顾 overall_score、min_role_score "
                    "和 fairness_score：拍照有高点，预算有保护，路线效率有补偿，热闹感也不过度。"
                ),
                stages=[
                    Stage(
                        stage_id="stage_fr_1",
                        stage_type=StageType.EXPLORE,
                        name="轻氛围拍照点",
                        experience_goal="用低门槛氛围点满足出片需求，避免一开始就高消费",
                        priority_role_id=photo_id,
                        duration_minutes=55,
                        energy_level=2,
                        constraints={
                            "标签": ["拍照", "文艺", "有氛围"],
                            "categories": ["书店", "公园", "咖啡"],
                            "avoid_queue": True,
                        },
                        reasoning="先给氛围导向朋友可见收益，但控制成本和排队。",
                    ),
                    Stage(
                        stage_id="stage_fr_2",
                        stage_type=StageType.DINE,
                        name="性价比聊天餐",
                        experience_goal="保护预算敏感角色，同时给大家稳定聊天空间",
                        priority_role_id=budget_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "聊天", "性价比"],
                            "categories": ["轻食"],
                            "avoid_queue": True,
                            "budget_level": "medium_low",
                        },
                        reasoning="预算和聊天是朋友局中最适合合并处理的决策点。",
                    ),
                    Stage(
                        stage_id="stage_fr_3",
                        stage_type=StageType.RELAX,
                        name="顺路松弛收尾",
                        experience_goal="控制转场和疲惫，让实用导向朋友获得明确补偿",
                        priority_role_id=practical_id,
                        duration_minutes=40,
                        energy_level=1,
                        constraints={
                            "标签": ["休息", "路线顺", "少排队"],
                            "categories": ["咖啡", "书店"],
                            "indoor": True,
                        },
                        reasoning="最后用确定性收尾，避免半天行程越玩越散。",
                    ),
                ],
            ),
        ]

    def _strategies_by_type(
        self,
        strategies: list[NegotiationStrategy],
    ) -> dict[str, NegotiationStrategy]:
        return {str(strategy.strategy_type): strategy for strategy in strategies}

    def _role_id(self, group_context: GroupContext, preferred: str, fallback_prefix: str) -> str:
        role_ids = [role.role_id for role in group_context.roles]
        if preferred in role_ids:
            return preferred
        return next(
            (role_id for role_id in role_ids if role_id.startswith(fallback_prefix)),
            role_ids[0] if role_ids else preferred,
        )
