import re
from datetime import datetime

from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.domain.enums import GroupType, RoleType
from local_explorer_agent.app.domain.memory import UserMemoryContext
from local_explorer_agent.app.domain.models import GroupContext, RoleProfile

_CHILD_TOKENS = ("孩子", "小孩", "娃", "宝宝", "女儿", "儿子", "孩子们", "亲子")
_CHILD_NEGATION_TOKENS = (
    "不带孩子",
    "不带小孩",
    "不带娃",
    "不带宝宝",
    "不要带孩子",
    "不要带娃",
    "别带孩子",
    "别带娃",
    "没有孩子",
    "不想亲子",
    "不要亲子",
)
_ELDER_TOKENS = ("老人", "长辈", "爸妈", "父母")
_FAMILY_TOKENS = ("家庭", "全家", "一家", "带娃", "遛娃")
_COUPLE_TOKENS = (
    "情侣",
    "约会",
    "二人世界",
    "伴侣",
    "对象",
    "女朋友",
    "男朋友",
    "女友",
    "男友",
    "老婆",
    "老公",
    "妻子",
    "丈夫",
    "爱人",
    "太太",
)
_FRIEND_TOKENS = (
    "和朋友",
    "跟朋友",
    "朋友们",
    "朋友局",
    "几个朋友",
    "朋友一起",
    "同事",
    "部门",
    "团建",
    "2男2女",
    "两男两女",
    "男生",
    "女生",
)
_SOLO_TOKENS = ("一个人", "自己", "独自", "独处", "单人", "solo")


class UserUnderstandingSkill:
    name = "user_understanding"

    def __init__(self, prompt_runner: JSONPromptRunner | None = None) -> None:
        self.prompt_runner = prompt_runner

    def run(
        self,
        *,
        user_query: str,
        user_id: str,
        city: str,
        start_time: datetime,
        duration_minutes: int,
        user_memory: UserMemoryContext | None = None,
    ) -> GroupContext:
        if self.prompt_runner is not None:
            context = self.prompt_runner.run(
                "user_understanding.md",
                {
                    "user_query": user_query,
                    "user_id": user_id,
                    "city": city,
                    "time_context": {
                        "start_time": start_time.isoformat(),
                        "duration_minutes": duration_minutes,
                    },
                    "memory_context": (
                        user_memory.compact_summary() if user_memory else None
                    ),
                },
                GroupContext,
                fallback=lambda: self._run_rule_based(
                    user_query=user_query,
                    city=city,
                    duration_minutes=duration_minutes,
                ),
            )
        else:
            context = self._run_rule_based(
                user_query=user_query,
                city=city,
                duration_minutes=duration_minutes,
            )
        context.input_query = user_query
        if user_memory is not None:
            context = self._apply_memory_context(context, user_query, user_memory)
            context.input_query = user_query
        return context

    def _run_rule_based(
        self,
        *,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        if self._is_family_query(user_query):
            return self._build_family_or_default_context(user_query, city, duration_minutes)
        if self._is_couple_query(user_query):
            return self._build_couple_context(user_query, city, duration_minutes)
        if self._is_friend_query(user_query):
            return self._build_friends_context(user_query, city, duration_minutes)
        if self._is_solo_query(user_query):
            return self._build_solo_context(user_query, city, duration_minutes)
        return self._build_general_context(user_query, city, duration_minutes)

    def _build_family_or_default_context(
        self,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        shared_constraints = self._extract_shared_constraints(user_query, city, duration_minutes)
        roles: list[RoleProfile] = [
            RoleProfile(
                role_id="adult_user",
                role_type=RoleType.USER,
                display_name="成人用户",
                hard_constraints=shared_constraints,
                soft_preferences=["轻松参与", "低转场压力"],
                hidden_needs=["希望自己也能参与，而不是全程只做协调者"],
                risk_points=["如果同行人的核心体验不足，整体行程会变得被动"],
                priority_weight=1.0,
                confidence=0.9,
            )
        ]

        if any(
            token in user_query
            for token in ["老婆", "妻子", "爱人", "太太", "女朋友", "对象", "男朋友"]
        ):
            spouse_constraints = []
            spouse_preferences = ["不被特殊对待", "轻松聊天"]
            hidden_needs = ["健康饮食但不想牺牲用餐氛围"]
            risk_points = ["低卡需求容易和亲子餐饮便利性冲突"]
            role_id = "spouse_partner"
            diet_tokens = ["减肥", "减脂", "控糖", "低卡", "健身", "清淡"]
            if any(token in user_query for token in diet_tokens):
                role_id = "spouse_dieter"
                spouse_constraints.append("餐饮需低负担、低油低糖或轻食可选")
            roles.append(
                RoleProfile(
                    role_id=role_id,
                    role_type=RoleType.SPOUSE,
                    display_name="减脂中的配偶" if role_id == "spouse_dieter" else "配偶",
                    hard_constraints=spouse_constraints,
                    soft_preferences=spouse_preferences,
                    hidden_needs=hidden_needs,
                    risk_points=risk_points,
                    priority_weight=1.15,
                    confidence=0.88,
                )
            )

        if _mentions_child(user_query):
            age = self._extract_age(user_query)
            child_role_id = f"child_{age}yo" if age else "child"
            roles.append(
                RoleProfile(
                    role_id=child_role_id,
                    role_type=RoleType.CHILD,
                    display_name=f"{age}岁孩子" if age else "孩子",
                    age=age,
                    hard_constraints=[
                        f"适合{age}岁儿童" if age else "适合儿童",
                        "安全、可控、不过度排队",
                    ],
                    soft_preferences=["互动", "释放体力", "新鲜感"],
                    hidden_needs=["需要先被满足，后续成人阶段才更稳"],
                    risk_points=["久坐或纯逛店容易失去耐心"],
                    priority_weight=1.25,
                    confidence=0.92 if age else 0.82,
                )
            )

        if any(token in user_query for token in ["老人", "长辈", "爸妈", "父母"]):
            roles.append(
                RoleProfile(
                    role_id="elder_companion",
                    role_type=RoleType.ELDER,
                    display_name="长辈",
                    hard_constraints=["低步行", "需要休息点"],
                    soft_preferences=["安静", "路线顺"],
                    hidden_needs=["少上下楼和少暴晒"],
                    risk_points=["长距离转场会显著降低满意度"],
                    priority_weight=1.2,
                    confidence=0.86,
                )
            )

        group_type = self._infer_group_type(roles)
        scene_label = "family_half_day" if group_type == GroupType.FAMILY else "local_outing"
        clarification_questions: list[str] = []
        if duration_minutes <= 0:
            clarification_questions.append("这次大约可以安排多久？")

        return GroupContext(
            group_type=group_type,
            roles=roles,
            group_size=len(roles),
            scene_label=scene_label,
            inferred_constraints=shared_constraints,
            clarification_questions=clarification_questions,
            confidence_summary={
                "role_detection": round(sum(role.confidence for role in roles) / len(roles), 2),
                "constraints": 0.86,
                "overall": 0.88,
            },
        )

    def _build_couple_context(
        self,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        shared_constraints = self._extract_shared_constraints(user_query, city, duration_minutes)
        shared_constraints.extend(["情侣约会场景", "优先适合聊天、氛围和低转场"])
        diet_tokens = ["减肥", "减脂", "控糖", "低卡", "健身", "清淡"]
        partner_constraints = []
        partner_preferences = ["有氛围", "适合聊天", "轻松拍照"]
        partner_hidden_needs = ["希望约会被认真安排，但节奏不要太赶"]
        partner_risk_points = ["地点太工具化、太嘈杂或排队太久会削弱约会感"]
        role_id = "spouse_partner"
        if any(token in user_query for token in diet_tokens):
            role_id = "spouse_dieter"
            partner_constraints.append("餐饮需低负担、低油低糖或轻食可选")
            partner_preferences.append("健康但不牺牲用餐氛围")

        roles = [
            RoleProfile(
                role_id="adult_user",
                role_type=RoleType.USER,
                display_name="成人用户",
                hard_constraints=shared_constraints,
                soft_preferences=["自然聊天", "路线顺", "约会体验不要像任务打卡"],
                hidden_needs=["希望有一点仪式感，同时不显得刻意"],
                risk_points=["过度嘈杂、排队或不适合两人聊天的地点会破坏约会节奏"],
                priority_weight=1.0,
                confidence=0.9,
            ),
            RoleProfile(
                role_id=role_id,
                role_type=RoleType.SPOUSE,
                display_name="伴侣" if role_id == "spouse_partner" else "有饮食偏好的伴侣",
                hard_constraints=partner_constraints,
                soft_preferences=partner_preferences,
                hidden_needs=partner_hidden_needs,
                risk_points=partner_risk_points,
                priority_weight=1.1,
                confidence=0.88,
            ),
        ]
        return GroupContext(
            group_type=GroupType.COUPLE,
            roles=roles,
            group_size=2,
            scene_label="couple_date",
            inferred_constraints=_dedupe(shared_constraints),
            clarification_questions=[],
            confidence_summary={
                "role_detection": 0.9,
                "constraints": 0.84,
                "overall": 0.88,
            },
        )

    def _build_solo_context(
        self,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        shared_constraints = self._extract_shared_constraints(user_query, city, duration_minutes)
        shared_constraints.append("单人出行，优先按自己的节奏安排")
        roles = [
            RoleProfile(
                role_id="adult_user",
                role_type=RoleType.USER,
                display_name="成人用户",
                hard_constraints=shared_constraints,
                soft_preferences=["安静", "可自由调整", "低转场压力"],
                hidden_needs=["希望一个人也能获得放松和新鲜感"],
                risk_points=["过度社交化或不适合单人停留的地点会降低匹配度"],
                priority_weight=1.0,
                confidence=0.88,
            )
        ]
        return GroupContext(
            group_type=GroupType.SOLO,
            roles=roles,
            group_size=1,
            scene_label="solo_explore",
            inferred_constraints=_dedupe(shared_constraints),
            clarification_questions=[],
            confidence_summary={
                "role_detection": 0.86,
                "constraints": 0.82,
                "overall": 0.84,
            },
        )

    def _build_general_context(
        self,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        shared_constraints = self._extract_shared_constraints(user_query, city, duration_minutes)
        shared_constraints.append("未明确同行人，按通用本地轻出行处理")
        roles = [
            RoleProfile(
                role_id="adult_user",
                role_type=RoleType.USER,
                display_name="成人用户",
                hard_constraints=shared_constraints,
                soft_preferences=["轻松", "路线顺", "少踩雷"],
                hidden_needs=["希望先得到可执行的推荐，再按偏好微调"],
                risk_points=["套用无关同行人模板会偏离真实需求"],
                priority_weight=1.0,
                confidence=0.74,
            )
        ]
        return GroupContext(
            group_type=GroupType.UNKNOWN,
            roles=roles,
            group_size=1,
            scene_label="general_local_outing",
            inferred_constraints=_dedupe(shared_constraints),
            clarification_questions=[],
            confidence_summary={
                "role_detection": 0.72,
                "constraints": 0.8,
                "overall": 0.76,
            },
        )

    def _build_friends_context(
        self,
        user_query: str,
        city: str,
        duration_minutes: int,
    ) -> GroupContext:
        shared_constraints = self._extract_shared_constraints(user_query, city, duration_minutes)
        shared_constraints.extend(["周末朋友半日出行", "需要兼顾拍照氛围、效率和预算"])
        roles = [
            RoleProfile(
                role_id="photo_oriented_role",
                role_type=RoleType.FRIEND,
                display_name="拍照氛围导向朋友",
                hard_constraints=[],
                soft_preferences=["出片", "有氛围", "新鲜感", "适合分享"],
                hidden_needs=["希望行程看起来有记忆点，而不是普通吃饭逛街"],
                risk_points=["如果地点太实用或太普通，会觉得周末出行不值"],
                priority_weight=1.05,
                confidence=0.86,
            ),
            RoleProfile(
                role_id="practical_oriented_role",
                role_type=RoleType.FRIEND,
                display_name="效率实用导向朋友",
                hard_constraints=["别太折腾", "路线顺", "不要长时间排队"],
                soft_preferences=["转场少", "安排清楚", "有备选"],
                hidden_needs=["希望计划可执行，不要为了拍照牺牲舒适度"],
                risk_points=["过多网红点或绕路会降低参与意愿"],
                priority_weight=1.0,
                confidence=0.84,
            ),
            RoleProfile(
                role_id="budget_sensitive_role",
                role_type=RoleType.FRIEND,
                display_name="预算敏感朋友",
                hard_constraints=["预算别太高", "避免高客单价"],
                soft_preferences=["性价比", "可自由消费", "少踩雷"],
                hidden_needs=["不想因为预算扫兴，也不想显得自己难配合"],
                risk_points=["高价餐饮或门票会制造隐性压力"],
                priority_weight=1.0,
                confidence=0.86,
            ),
            RoleProfile(
                role_id="lively_oriented_role",
                role_type=RoleType.FRIEND,
                display_name="热闹体验导向朋友",
                hard_constraints=[],
                soft_preferences=["热闹", "互动", "周末感", "有氛围"],
                hidden_needs=["希望气氛被带起来，不要全程太安静"],
                risk_points=["太安静的场景会让朋友局不够尽兴"],
                priority_weight=0.95,
                confidence=0.78,
            ),
        ]
        return GroupContext(
            group_type=GroupType.FRIENDS,
            roles=roles,
            group_size=4,
            scene_label="friends_weekend_half_day",
            inferred_constraints=shared_constraints,
            clarification_questions=[],
            confidence_summary={
                "role_detection": 0.84,
                "constraints": 0.82,
                "overall": 0.84,
            },
        )

    def _extract_age(self, query: str) -> int | None:
        match = re.search(r"(\d{1,2})\s*岁", query)
        return int(match.group(1)) if match else None

    def _is_friend_demo(self, query: str) -> bool:
        friend_tokens = ["朋友", "2男2女", "两男两女", "男生", "女生", "同事", "部门", "团建"]
        preference_tokens = [
            "拍照",
            "氛围",
            "预算",
            "别太折腾",
            "热闹",
            "别太贵",
            "烧烤",
            "烤肉",
            "桌游",
            "密室",
            "夜间",
            "烟火气",
        ]
        return any(token in query for token in friend_tokens) and any(
            token in query for token in preference_tokens
        )

    def _is_family_query(self, query: str) -> bool:
        return (
            _mentions_child(query)
            or any(token in query for token in _ELDER_TOKENS)
            or any(token in query for token in _FAMILY_TOKENS)
        )

    def _is_couple_query(self, query: str) -> bool:
        return any(token in query for token in _COUPLE_TOKENS)

    def _is_friend_query(self, query: str) -> bool:
        return self._is_friend_demo(query) or any(token in query for token in _FRIEND_TOKENS)

    def _is_solo_query(self, query: str) -> bool:
        return any(token in query for token in _SOLO_TOKENS)

    def _extract_shared_constraints(
        self,
        query: str,
        city: str,
        duration_minutes: int,
    ) -> list[str]:
        constraints = [f"城市：{city}", f"总时长约{duration_minutes}分钟"]
        if "今天" in query or "下午" in query:
            constraints.append("时间窗口偏短，优先低转场")
        if any(token in query for token in ["别太远", "不要太远", "近一点"]):
            constraints.append("距离不能太远")
        if any(token in query for token in ["排队", "别排"]):
            constraints.append("避免长时间排队")
        return constraints

    def _infer_group_type(self, roles: list[RoleProfile]) -> GroupType:
        role_types = {role.role_type for role in roles}
        if RoleType.CHILD in role_types or RoleType.ELDER in role_types:
            return GroupType.FAMILY
        if RoleType.FRIEND in role_types:
            return GroupType.FRIENDS
        if RoleType.SPOUSE in role_types:
            return GroupType.COUPLE
        if role_types == {RoleType.USER}:
            return GroupType.SOLO
        return GroupType.UNKNOWN

    def _apply_memory_context(
        self,
        context: GroupContext,
        user_query: str,
        memory: UserMemoryContext,
    ) -> GroupContext:
        roles = [role.model_copy(deep=True) for role in context.roles]
        inferred_constraints = list(context.inferred_constraints)
        profile = memory.profile
        if profile.budget_preference:
            inferred_constraints.append(f"记忆：预算偏好 {profile.budget_preference}")
        if profile.pace_preference:
            inferred_constraints.append(f"记忆：节奏偏好 {profile.pace_preference}")
        if profile.max_walking_minutes_per_segment is not None:
            inferred_constraints.append(
                f"记忆：单段步行不超过{profile.max_walking_minutes_per_segment}分钟"
            )

        adult = next((role for role in roles if role.role_type == RoleType.USER), None)
        if adult is not None:
            adult.soft_preferences = _dedupe([*adult.soft_preferences, *memory.likes[:8]])
            adult.risk_points = _dedupe([*adult.risk_points, *memory.dislikes[:8]])

        memory_added_companion = False
        selected_companion_ids = set(memory.selected_companion_ids)
        for companion in memory.companions:
            explicitly_selected = companion.companion_id in selected_companion_ids
            if not explicitly_selected and not _companion_relevant(
                companion.display_name,
                companion.role_type,
                user_query,
            ):
                continue
            role_type = _role_type(companion.role_type)
            if not explicitly_selected and _memory_companion_conflicts_current_scene(
                role_type=role_type,
                context_group_type=context.group_type,
                query=user_query,
            ):
                continue
            existing = next(
                (
                    role
                    for role in roles
                    if role.role_type == role_type
                    and (companion.age is None or role.age in {None, companion.age})
                ),
                None,
            )
            if existing is None:
                roles.append(
                    RoleProfile(
                        role_id=companion.companion_id,
                        role_type=role_type,
                        display_name=companion.display_name,
                        age=companion.age,
                        hard_constraints=companion.hard_constraints,
                        soft_preferences=companion.soft_preferences,
                        risk_points=companion.risk_points,
                        confidence=0.78,
                    )
                )
                memory_added_companion = True
                continue
            existing.hard_constraints = _dedupe([
                *existing.hard_constraints,
                *companion.hard_constraints,
            ])
            existing.soft_preferences = _dedupe([
                *existing.soft_preferences,
                *companion.soft_preferences,
            ])
            existing.risk_points = _dedupe([
                *existing.risk_points,
                *companion.risk_points,
            ])
            if existing.age is None:
                existing.age = companion.age

        group_type = (
            self._infer_group_type(roles)
            if context.group_type != GroupType.UNKNOWN or memory_added_companion
            else context.group_type
        )
        return context.model_copy(update={
            "roles": roles,
            "group_size": len(roles),
            "group_type": group_type,
            "inferred_constraints": _dedupe(inferred_constraints),
        })


def _role_type(value: str) -> RoleType:
    try:
        return RoleType(value)
    except ValueError:
        return RoleType.UNKNOWN


def _companion_relevant(display_name: str, role_type: str, query: str) -> bool:
    if display_name and display_name in query:
        return True
    role_keywords = {
        "spouse": ["老婆", "妻子", "爱人", "太太", "对象", "女朋友", "男朋友"],
        "child": ["孩子", "小孩", "娃", "宝宝", "女儿", "儿子", "亲子"],
        "elder": ["老人", "长辈", "爸妈", "父母"],
        "friend": ["朋友", "同事", "团建"],
    }
    return any(keyword in query for keyword in role_keywords.get(role_type, []))


def _mentions_child(query: str) -> bool:
    if any(token in query for token in _CHILD_NEGATION_TOKENS):
        return False
    return any(token in query for token in _CHILD_TOKENS)


def _memory_companion_conflicts_current_scene(
    *,
    role_type: RoleType,
    context_group_type: GroupType | str,
    query: str,
) -> bool:
    if context_group_type == GroupType.COUPLE and role_type in {RoleType.CHILD, RoleType.ELDER}:
        return not (_mentions_child(query) or any(token in query for token in _ELDER_TOKENS))
    if context_group_type == GroupType.SOLO and role_type != RoleType.USER:
        return not any(token in query for token in _CHILD_TOKENS + _ELDER_TOKENS + _COUPLE_TOKENS)
    if context_group_type == GroupType.FRIENDS and role_type in {
        RoleType.CHILD,
        RoleType.ELDER,
        RoleType.SPOUSE,
    }:
        return not (
            _mentions_child(query)
            or any(token in query for token in _ELDER_TOKENS)
            or any(token in query for token in _COUPLE_TOKENS)
        )
    return False


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
