from dataclasses import dataclass

from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.schemas import PlanCandidateListOutput
from local_explorer_agent.app.domain.enums import GroupType, PlanType, StageType
from local_explorer_agent.app.domain.models import (
    Conflict,
    GroupContext,
    NegotiationStrategy,
    PlanCandidate,
    Stage,
)


@dataclass(frozen=True)
class _IntentSignal:
    stage_type: StageType
    label: str
    keywords: tuple[str, ...]


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

_INTENT_SIGNALS: tuple[_IntentSignal, ...] = (
    _IntentSignal(StageType.DINE, "火锅", ("火锅",)),
    _IntentSignal(StageType.DINE, "烧烤", ("烧烤",)),
    _IntentSignal(StageType.DINE, "烤肉", ("烤肉",)),
    _IntentSignal(StageType.DINE, "轻食", ("轻食", "低卡", "清淡")),
    _IntentSignal(StageType.DINE, "甜品", ("甜品", "蛋糕", "冰淇淋")),
    _IntentSignal(StageType.DINE, "咖啡", ("咖啡", "喝咖啡")),
    _IntentSignal(StageType.DINE, "茶馆", ("茶馆", "喝茶")),
    _IntentSignal(StageType.DINE, "吃饭", ("吃个饭", "吃饭", "用餐", "晚饭", "午饭", "吃点")),
    _IntentSignal(StageType.EXPLORE, "看展", ("看个展", "看展", "展览", "逛展", "美术馆", "画展")),
    _IntentSignal(StageType.RELAX, "聊天", ("聊天", "聊聊天", "找个地方聊", "找地方聊天")),
    _IntentSignal(StageType.EXPLORE, "书店", ("书店",)),
    _IntentSignal(StageType.EXPLORE, "桌游", ("桌游",)),
    _IntentSignal(StageType.EXPLORE, "密室逃脱", ("密室逃脱", "密室")),
    _IntentSignal(StageType.EXPLORE, "小剧场", ("小剧场", "脱口秀", "演出", "黑盒剧场")),
    _IntentSignal(StageType.EXPLORE, "手作体验", ("手作", "陶艺", "皮具", "银饰")),
    _IntentSignal(StageType.EXPLORE, "买手店", ("买手店", "vintage", "小店")),
    _IntentSignal(StageType.EXPLORE, "Citywalk", ("Citywalk", "citywalk")),
    _IntentSignal(StageType.ENERGY_RELEASE, "游乐园", ("游乐园", "游乐场", "乐园")),
    _IntentSignal(StageType.ENERGY_RELEASE, "亲子空间", ("亲子空间",)),
    _IntentSignal(StageType.ENERGY_RELEASE, "公园", ("公园",)),
)

_LABEL_CATEGORIES: dict[str, list[str]] = {
    "火锅": ["火锅"],
    "烧烤": ["烧烤"],
    "烤肉": ["烤肉", "烧烤"],
    "轻食": ["轻食"],
    "甜品": ["甜品"],
    "咖啡": ["咖啡"],
    "茶馆": ["茶馆"],
    "吃饭": ["餐厅", "轻食"],
    "看展": ["展览"],
    "聊天": ["咖啡", "茶馆", "书店"],
    "书店": ["书店"],
    "桌游": ["桌游"],
    "密室逃脱": ["密室逃脱"],
    "小剧场": ["小剧场"],
    "手作体验": ["手作体验"],
    "买手店": ["买手店"],
    "Citywalk": ["Citywalk", "公园"],
    "游乐园": ["游乐园"],
    "亲子空间": ["亲子空间"],
    "公园": ["公园"],
}


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
            return self._apply_single_purpose_policy(
                output.items,
                group_context=group_context,
                conflicts=conflicts,
                negotiation_strategies=negotiation_strategies,
            )
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
        single_purpose_stage = self._single_purpose_stage(group_context)
        if group_context.group_type == GroupType.FAMILY:
            plans = self._build_family_plans(group_context, strategies)
        elif group_context.group_type == GroupType.FRIENDS:
            plans = self._build_friends_plans(group_context, strategies)
        elif group_context.group_type == GroupType.COUPLE:
            plans = self._build_couple_plans(group_context, strategies)
        elif group_context.group_type == GroupType.SOLO:
            plans = self._build_solo_plans(group_context, strategies)
        else:
            plans = self._build_general_plans(group_context, strategies)
        if single_purpose_stage is not None:
            return [self._build_single_option_plan(plans, group_context, single_purpose_stage)]
        return plans

    def _apply_single_purpose_policy(
        self,
        plans: list[PlanCandidate],
        *,
        group_context: GroupContext,
        conflicts: list[Conflict],
        negotiation_strategies: list[NegotiationStrategy],
    ) -> list[PlanCandidate]:
        single_purpose_stage = self._single_purpose_stage(group_context)
        if single_purpose_stage is None:
            return plans
        templates = plans or self._run_rule_based(
            group_context=group_context,
            conflicts=conflicts,
            negotiation_strategies=negotiation_strategies,
        )
        return [self._build_single_option_plan(templates, group_context, single_purpose_stage)]

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
                plan_id="plan_c",
                plan_type=PlanType.PLAN_C,
                title="均衡：亲子放电 + 自然低卡 + 松弛收尾",
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
                plan_id="plan_c",
                plan_type=PlanType.PLAN_C,
                title="均衡：轻氛围 + 低预算餐 + 顺路收尾",
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

    def _build_couple_plans(
        self,
        group_context: GroupContext,
        strategies: dict[str, NegotiationStrategy],
    ) -> list[PlanCandidate]:
        user_id = self._role_id(group_context, "adult_user", "user")
        partner_id = self._role_id(group_context, "spouse_partner", "spouse")
        return [
            PlanCandidate(
                plan_id="plan_a",
                plan_type=PlanType.PLAN_A,
                title="氛围约会线",
                theme="先用文艺或海边氛围打开话题，再用晚餐和夜景收住节奏",
                strategy=strategies.get("rotate_priority"),
                tradeoff_summary="氛围感更强，但会保留少排队和短转场约束，避免约会被等待消耗。",
                stages=[
                    Stage(
                        stage_id="stage_ca_1",
                        stage_type=StageType.EXPLORE,
                        name="氛围轻探索",
                        experience_goal="先安排适合并肩逛、拍照和自然聊天的开场，不进入高压打卡。",
                        priority_role_id=partner_id,
                        duration_minutes=65,
                        energy_level=2,
                        constraints={
                            "标签": ["情侣", "约会", "拍照", "文艺", "有氛围"],
                            "categories": ["展览", "Citywalk", "买手店"],
                            "avoid_queue": True,
                        },
                        reasoning="约会开场需要先创造共同话题，而不是直接进入工具化餐饮。",
                    ),
                    Stage(
                        stage_id="stage_ca_2",
                        stage_type=StageType.DINE,
                        name="可聊天晚餐",
                        experience_goal="选择适合两个人慢慢聊的餐饮点，兼顾味道、座位舒适和排队风险。",
                        priority_role_id=user_id,
                        duration_minutes=70,
                        energy_level=1,
                        constraints={
                            "标签": ["情侣", "约会", "聊天", "氛围"],
                            "categories": ["餐厅", "轻食", "火锅"],
                            "avoid_queue": True,
                        },
                        reasoning="餐饮是约会中最长的相处段，需要比单纯好吃更关注聊天体验。",
                    ),
                    Stage(
                        stage_id="stage_ca_3",
                        stage_type=StageType.RELAX,
                        name="夜景或甜品收尾",
                        experience_goal="用低强度收尾保留余韵，适合散步、甜品或安静坐一会儿。",
                        priority_role_id=partner_id,
                        duration_minutes=45,
                        energy_level=1,
                        constraints={
                            "标签": ["浪漫", "约会", "聊天", "松弛"],
                            "categories": ["甜品", "咖啡", "茶馆", "公园"],
                            "avoid_queue": True,
                        },
                        reasoning="结尾比加项目更重要，保留轻松回顾和自由调整空间。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_b",
                plan_type=PlanType.PLAN_B,
                title="轻松聊天线",
                theme="少转场、低压力，以咖啡书店和轻餐把聊天体验放到第一位",
                strategy=strategies.get("soften_conflict"),
                tradeoff_summary="不追求强打卡，换取更稳定的座位、聊天和可执行性。",
                stages=[
                    Stage(
                        stage_id="stage_cb_1",
                        stage_type=StageType.RELAX,
                        name="咖啡聊天开场",
                        experience_goal="先找一个坐得住、声音不过吵的空间，让两个人自然进入状态。",
                        priority_role_id=user_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["情侣", "聊天", "安静", "松弛"],
                            "categories": ["咖啡", "茶馆", "书店"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="如果用户没有指定强活动，聊天质量应比项目数量更重要。",
                    ),
                    Stage(
                        stage_id="stage_cb_2",
                        stage_type=StageType.EXPLORE,
                        name="顺路轻逛",
                        experience_goal="安排一个顺路、低门槛、适合拍照或互相挑选的小探索点。",
                        priority_role_id=partner_id,
                        duration_minutes=55,
                        energy_level=2,
                        constraints={
                            "标签": ["约会", "拍照", "轻松", "小众"],
                            "categories": ["书店", "买手店", "Citywalk"],
                            "avoid_queue": True,
                        },
                        reasoning="轻逛比硬安排项目更适合保留约会的松弛感。",
                    ),
                    Stage(
                        stage_id="stage_cb_3",
                        stage_type=StageType.DINE,
                        name="舒服收尾餐",
                        experience_goal="用不太赶的餐饮收尾，方便根据当时状态延长或提前结束。",
                        priority_role_id=user_id,
                        duration_minutes=65,
                        energy_level=1,
                        constraints={
                            "标签": ["约会", "聊天", "不赶", "少排队"],
                            "categories": ["餐厅", "轻食", "甜品"],
                            "avoid_queue": True,
                        },
                        reasoning="把餐饮放后面，能根据前两段状态自然调整约会长度。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_c",
                plan_type=PlanType.PLAN_C,
                title="均衡：氛围 + 聊天 + 低转场",
                theme="把约会感、聊天质量和可执行性拆到不同阶段，避免任何一项过度压倒体验",
                strategy=strategies.get("min_regret"),
                tradeoff_summary="推荐不是硬凑浪漫，而是在氛围、舒适和少排队之间取一个更稳的平衡。",
                recommendation_reason=(
                    "该方案兼顾 overall_score、min_role_score 和 fairness_score："
                    "有约会氛围，也给两个人保留充分聊天和低转场空间。"
                ),
                stages=[
                    Stage(
                        stage_id="stage_cr_1",
                        stage_type=StageType.EXPLORE,
                        name="轻氛围开场",
                        experience_goal="用展览、街区或小店建立共同话题，避免开场直接变成吃饭任务。",
                        priority_role_id=partner_id,
                        duration_minutes=60,
                        energy_level=2,
                        constraints={
                            "标签": ["情侣", "约会", "文艺", "拍照", "有氛围"],
                            "categories": ["展览", "Citywalk", "买手店"],
                            "avoid_queue": True,
                        },
                        reasoning="推荐方案先给约会一个可记住的轻量高点。",
                    ),
                    Stage(
                        stage_id="stage_cr_2",
                        stage_type=StageType.DINE,
                        name="聊天友好餐",
                        experience_goal="选择不会过度嘈杂、适合两个人慢慢聊的餐饮空间。",
                        priority_role_id=user_id,
                        duration_minutes=65,
                        energy_level=1,
                        constraints={
                            "标签": ["约会", "聊天", "舒适", "少排队"],
                            "categories": ["餐厅", "轻食", "火锅"],
                            "avoid_queue": True,
                        },
                        reasoning="把最长停留段做稳，约会体验不会被排队或噪音带偏。",
                    ),
                    Stage(
                        stage_id="stage_cr_3",
                        stage_type=StageType.RELAX,
                        name="安静收尾",
                        experience_goal="用甜品、咖啡、茶馆或夜景散步收尾，给约会留出回味空间。",
                        priority_role_id=partner_id,
                        duration_minutes=45,
                        energy_level=1,
                        constraints={
                            "标签": ["浪漫", "约会", "松弛", "聊天"],
                            "categories": ["甜品", "咖啡", "茶馆", "公园"],
                            "avoid_queue": True,
                        },
                        reasoning="收尾低强度，方便继续聊或灵活结束。",
                    ),
                ],
            ),
        ]

    def _build_solo_plans(
        self,
        group_context: GroupContext,
        strategies: dict[str, NegotiationStrategy],
    ) -> list[PlanCandidate]:
        user_id = self._role_id(group_context, "adult_user", "user")
        return [
            PlanCandidate(
                plan_id="plan_a",
                plan_type=PlanType.PLAN_A,
                title="独处充电线",
                theme="用展览、书店和咖啡把一个人的自由节奏安排清楚",
                strategy=strategies.get("rotate_priority"),
                tradeoff_summary="活动感更明确，但每一段都保留可提前结束和少转场空间。",
                stages=[
                    Stage(
                        stage_id="stage_sa_1",
                        stage_type=StageType.EXPLORE,
                        name="安静探索",
                        experience_goal="找一个能慢慢看、慢慢逛的地点，给自己一点新鲜感。",
                        priority_role_id=user_id,
                        duration_minutes=70,
                        energy_level=2,
                        constraints={
                            "标签": ["独处", "文艺", "安静", "新鲜"],
                            "categories": ["展览", "书店", "Citywalk"],
                            "avoid_queue": True,
                        },
                        reasoning="单人出行最重要的是节奏可控，不需要迁就他人。",
                    ),
                    Stage(
                        stage_id="stage_sa_2",
                        stage_type=StageType.RELAX,
                        name="坐下来休息",
                        experience_goal="安排一个能坐下整理状态的空间，适合阅读、发呆或轻办公。",
                        priority_role_id=user_id,
                        duration_minutes=60,
                        energy_level=1,
                        constraints={
                            "标签": ["安静", "松弛", "休息", "独处"],
                            "categories": ["咖啡", "茶馆", "书店"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="给单人路线一个稳定休息段，比塞满项目更舒服。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_b",
                plan_type=PlanType.PLAN_B,
                title="轻松随走线",
                theme="低预算、低转场，适合一个人临时出门散心",
                strategy=strategies.get("soften_conflict"),
                tradeoff_summary="不追求强目的地，优先选择低成本和低后悔点。",
                stages=[
                    Stage(
                        stage_id="stage_sb_1",
                        stage_type=StageType.EXPLORE,
                        name="城市慢走",
                        experience_goal="找一个适合随走随停的街区、公园或书店，降低计划负担。",
                        priority_role_id=user_id,
                        duration_minutes=75,
                        energy_level=2,
                        constraints={
                            "标签": ["独处", "轻松", "低预算", "散步"],
                            "categories": ["Citywalk", "公园", "书店"],
                            "avoid_queue": True,
                        },
                        reasoning="独处场景可以让路线更自由，不需要强绑定固定项目。",
                    ),
                    Stage(
                        stage_id="stage_sb_2",
                        stage_type=StageType.DINE,
                        name="简单补给",
                        experience_goal="安排一段不需要久等的轻餐或饮品，保证体验连续。",
                        priority_role_id=user_id,
                        duration_minutes=45,
                        energy_level=1,
                        constraints={
                            "标签": ["轻食", "咖啡", "不赶", "少排队"],
                            "categories": ["轻食", "咖啡", "甜品"],
                            "avoid_queue": True,
                        },
                        reasoning="单人餐饮要降低等待和选择成本。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_c",
                plan_type=PlanType.PLAN_C,
                title="均衡：探索 + 休息",
                theme="先给自己一点新鲜感，再用安静空间收住节奏",
                strategy=strategies.get("min_regret"),
                tradeoff_summary="推荐方案兼顾新鲜感和恢复感，不把一个人的行程做得过满。",
                recommendation_reason=(
                    "该方案兼顾 overall_score、min_role_score 和 fairness_score："
                    "一个人出门有明确目标，也能随时放慢节奏。"
                ),
                stages=[
                    Stage(
                        stage_id="stage_sr_1",
                        stage_type=StageType.EXPLORE,
                        name="低压探索点",
                        experience_goal="选择一个适合单人进入、停留时间可长可短的探索点。",
                        priority_role_id=user_id,
                        duration_minutes=70,
                        energy_level=2,
                        constraints={
                            "标签": ["独处", "文艺", "轻松", "少排队"],
                            "categories": ["展览", "书店", "Citywalk"],
                            "avoid_queue": True,
                        },
                        reasoning="先满足新鲜感，但不让体验过度依赖排队或预约。",
                    ),
                    Stage(
                        stage_id="stage_sr_2",
                        stage_type=StageType.RELAX,
                        name="安静收尾",
                        experience_goal="用咖啡、茶馆或书店收尾，让这次出门有恢复感。",
                        priority_role_id=user_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["安静", "松弛", "独处", "休息"],
                            "categories": ["咖啡", "茶馆", "书店"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="一个人的路线应该允许临场延长或提前结束。",
                    ),
                ],
            ),
        ]

    def _build_general_plans(
        self,
        group_context: GroupContext,
        strategies: dict[str, NegotiationStrategy],
    ) -> list[PlanCandidate]:
        user_id = self._role_id(group_context, "adult_user", "user")
        return [
            PlanCandidate(
                plan_id="plan_a",
                plan_type=PlanType.PLAN_A,
                title="轻探索路线",
                theme="用可聊天、可拍照、低排队的城市轻活动覆盖未明确同行人的需求",
                strategy=strategies.get("rotate_priority"),
                tradeoff_summary="默认不套用无关同行人模板，先给出成人通用且容易修改的路线。",
                stages=[
                    Stage(
                        stage_id="stage_ga_1",
                        stage_type=StageType.EXPLORE,
                        name="轻探索开场",
                        experience_goal="找一个低门槛、有新鲜感、适合多数成人场景的活动点。",
                        priority_role_id=user_id,
                        duration_minutes=65,
                        energy_level=2,
                        constraints={
                            "标签": ["轻松", "文艺", "有氛围", "少排队"],
                            "categories": ["展览", "书店", "Citywalk", "公园"],
                            "avoid_queue": True,
                        },
                        reasoning="未明确同行人时，应先选择成人通用轻活动。",
                    ),
                    Stage(
                        stage_id="stage_ga_2",
                        stage_type=StageType.DINE,
                        name="顺路轻餐",
                        experience_goal="安排一个不需要复杂决策的餐饮或饮品点，方便衔接前后活动。",
                        priority_role_id=user_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["聊天", "轻食", "少排队"],
                            "categories": ["餐厅", "轻食", "咖啡"],
                            "avoid_queue": True,
                        },
                        reasoning="用餐饮提高行程完整度，但不把路线变成家庭模板。",
                    ),
                    Stage(
                        stage_id="stage_ga_3",
                        stage_type=StageType.RELAX,
                        name="低强度收尾",
                        experience_goal="用咖啡、茶馆或公园收尾，保留灵活修改空间。",
                        priority_role_id=user_id,
                        duration_minutes=40,
                        energy_level=1,
                        constraints={
                            "标签": ["松弛", "聊天", "休息"],
                            "categories": ["咖啡", "茶馆", "公园"],
                            "avoid_queue": True,
                        },
                        reasoning="通用路线需要低后悔收尾，方便用户继续细化需求。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_b",
                plan_type=PlanType.PLAN_B,
                title="室内稳妥路线",
                theme="优先室内、短转场、少排队，适合需求还不够明确时先稳住体验",
                strategy=strategies.get("soften_conflict"),
                tradeoff_summary="牺牲一点户外随机感，换取更强的可执行性。",
                stages=[
                    Stage(
                        stage_id="stage_gb_1",
                        stage_type=StageType.EXPLORE,
                        name="室内轻逛",
                        experience_goal="选择展览、书店或咖啡类地点，减少天气和排队不确定性。",
                        priority_role_id=user_id,
                        duration_minutes=70,
                        energy_level=1,
                        constraints={
                            "标签": ["室内", "文艺", "轻松", "少排队"],
                            "categories": ["展览", "书店", "咖啡"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="默认稳妥方案使用成人通用室内点兜底。",
                    ),
                    Stage(
                        stage_id="stage_gb_2",
                        stage_type=StageType.RELAX,
                        name="坐下来收尾",
                        experience_goal="找一个能坐下聊天或休息的地方，减少转场负担。",
                        priority_role_id=user_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["聊天", "安静", "休息"],
                            "categories": ["咖啡", "茶馆", "书店"],
                            "indoor": True,
                            "avoid_queue": True,
                        },
                        reasoning="用低强度空间补足行程，不强行加入家庭活动。",
                    ),
                ],
            ),
            PlanCandidate(
                plan_id="plan_c",
                plan_type=PlanType.PLAN_C,
                title="均衡：轻活动 + 轻餐 + 休息",
                theme="在成人通用场景里兼顾新鲜感、餐饮和低转场",
                strategy=strategies.get("min_regret"),
                tradeoff_summary="推荐方案用低后悔成人路线做默认值，避免套用无关场景。",
                recommendation_reason=(
                    "该方案兼顾 overall_score、min_role_score 和 fairness_score："
                    "先保证轻松、少排队、可继续修改。"
                ),
                stages=[
                    Stage(
                        stage_id="stage_gr_1",
                        stage_type=StageType.EXPLORE,
                        name="轻活动开场",
                        experience_goal="先安排一个多数成人都容易接受的轻探索点。",
                        priority_role_id=user_id,
                        duration_minutes=60,
                        energy_level=2,
                        constraints={
                            "标签": ["轻松", "文艺", "新鲜", "少排队"],
                            "categories": ["展览", "书店", "Citywalk"],
                            "avoid_queue": True,
                        },
                        reasoning="推荐默认值保留成人轻活动基线。",
                    ),
                    Stage(
                        stage_id="stage_gr_2",
                        stage_type=StageType.DINE,
                        name="轻松餐饮",
                        experience_goal="选择不难决策、排队压力低的餐饮或饮品点。",
                        priority_role_id=user_id,
                        duration_minutes=55,
                        energy_level=1,
                        constraints={
                            "标签": ["聊天", "轻食", "少排队"],
                            "categories": ["轻食", "咖啡", "餐厅"],
                            "avoid_queue": True,
                        },
                        reasoning="餐饮作为稳定段，而不是无关场景补偿段。",
                    ),
                    Stage(
                        stage_id="stage_gr_3",
                        stage_type=StageType.RELAX,
                        name="松弛收尾",
                        experience_goal="用低强度空间结束路线，让用户后续能自然微调。",
                        priority_role_id=user_id,
                        duration_minutes=40,
                        energy_level=1,
                        constraints={
                            "标签": ["松弛", "休息", "聊天"],
                            "categories": ["咖啡", "茶馆", "书店"],
                            "avoid_queue": True,
                        },
                        reasoning="收尾保持通用可执行，减少误推荐成本。",
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

    def _single_purpose_stage(self, group_context: GroupContext) -> StageType | None:
        query = group_context.input_query
        if not query:
            return None
        if any(marker in query for marker in _MULTI_STOP_MARKERS):
            return None

        matched: list[tuple[int, StageType, str]] = []
        for signal in _INTENT_SIGNALS:
            position = self._first_match_position(query, signal.keywords)
            if position >= 0:
                matched.append((position, signal.stage_type, signal.label))

        ordered_types: list[StageType] = []
        for _, stage_type, _label in sorted(matched, key=lambda item: item[0]):
            if stage_type not in ordered_types:
                ordered_types.append(stage_type)

        if len(ordered_types) != 1:
            return None

        return ordered_types[0]

    def _build_single_option_plan(
        self,
        plans: list[PlanCandidate],
        group_context: GroupContext,
        stage_type: StageType,
    ) -> PlanCandidate:
        query = group_context.input_query
        label = self._primary_label_for_stage(query, stage_type)
        template = self._preferred_template_for_stage(plans, stage_type)
        stage = next(
            (
                item.model_copy(deep=True)
                for item in template.stages
                if item.stage_type == stage_type
            ),
            template.stages[0].model_copy(deep=True),
        )
        stage.name = self._single_option_stage_name(stage_type, label, stage.name)
        stage.experience_goal = self._single_option_goal(stage_type, label)
        stage.reasoning = f"用户明确只想完成「{label}」这一件事，因此不额外拼接第二站。"
        categories = _LABEL_CATEGORIES.get(label)
        if categories:
            raw_tags = stage.constraints.get("标签", [])
            tags = [raw_tags] if isinstance(raw_tags, str) else list(raw_tags)
            stage.constraints = {
                **stage.constraints,
                "categories": categories,
                "标签": list(dict.fromkeys([*tags, label])),
            }
        candidate = template.model_copy(deep=True)
        candidate.plan_id = "plan_a"
        candidate.plan_type = PlanType.PLAN_A
        candidate.title = self._single_option_title(stage_type, label)
        candidate.theme = f"围绕「{label}」只安排这一件事，减少无关转场和补偿段。"
        candidate.stages = [stage]
        candidate.tradeoff_summary = (
            "这次不展开多方案对比，直接把时间和注意力集中在一个明确目标上。"
        )
        candidate.recommendation_reason = (
            "用户目标非常单一，直接给出一个最合适的推荐方案，"
            f"围绕「{label}」安排会比机械展开多方案更自然。"
        )
        return candidate

    def _preferred_template_for_stage(
        self,
        plans: list[PlanCandidate],
        stage_type: StageType,
    ) -> PlanCandidate:
        preferred_ids = ("plan_c", "plan_a", "plan_b")
        for plan_id in preferred_ids:
            for plan in plans:
                has_stage_type = any(stage.stage_type == stage_type for stage in plan.stages)
                if plan.plan_id == plan_id and has_stage_type:
                    return plan
        for plan in plans:
            if any(stage.stage_type == stage_type for stage in plan.stages):
                return plan
        return plans[0]

    def _primary_label_for_stage(self, query: str, stage_type: StageType) -> str:
        for signal in _INTENT_SIGNALS:
            if signal.stage_type != stage_type:
                continue
            if any(keyword in query for keyword in signal.keywords):
                return signal.label
        if stage_type == StageType.DINE:
            return "吃饭"
        if stage_type == StageType.ENERGY_RELEASE:
            return "去一个点玩"
        return "去一个点"

    def _single_option_title(self, stage_type: StageType, label: str) -> str:
        if stage_type == StageType.DINE:
            if label == "吃饭":
                return "就安排这一顿饭"
            return f"就去吃{label}"
        if label == "看展":
            return "就去看这一个展"
        if label == "书店":
            return "就去这家书店待一会儿"
        return f"就围绕「{label}」安排"

    def _single_option_stage_name(
        self,
        stage_type: StageType,
        label: str,
        fallback: str,
    ) -> str:
        if stage_type == StageType.DINE:
            if label == "吃饭":
                return "只安排一顿饭"
            return f"直奔{label}"
        if label == "看展":
            return "只看这一个展"
        if label == "书店":
            return "在书店安静待一会儿"
        return fallback

    def _single_option_goal(self, stage_type: StageType, label: str) -> str:
        if stage_type == StageType.DINE:
            return f"围绕「{label}」完成这次出门的唯一核心目标，不额外拼接别的活动。"
        return f"围绕「{label}」完成这次出门的唯一核心目标，减少无关转场。"

    def _first_match_position(self, query: str, keywords: tuple[str, ...]) -> int:
        positions = [query.find(keyword) for keyword in keywords if keyword in query]
        return min(positions) if positions else -1
