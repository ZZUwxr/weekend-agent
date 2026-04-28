from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.schemas import ConflictListOutput
from local_explorer_agent.app.domain.enums import ConflictType, DecisionType, GroupType, RoleType
from local_explorer_agent.app.domain.models import Conflict, GroupContext


class ConflictDetectionSkill:
    name = "conflict_detection"

    def __init__(self, prompt_runner: JSONPromptRunner | None = None) -> None:
        self.prompt_runner = prompt_runner

    def run(self, group_context: GroupContext) -> list[Conflict]:
        if self.prompt_runner is not None:
            output = self.prompt_runner.run(
                "conflict_detection.md",
                {"group_context": group_context.model_dump_json()},
                ConflictListOutput,
                fallback=lambda: ConflictListOutput(items=self._run_rule_based(group_context)),
            )
            return output.items
        return self._run_rule_based(group_context)

    def _run_rule_based(self, group_context: GroupContext) -> list[Conflict]:
        conflicts: list[Conflict] = []
        role_ids = {role.role_id for role in group_context.roles}
        roles_by_type = {role.role_type: role for role in group_context.roles}

        if group_context.group_type == GroupType.FRIENDS:
            return self._detect_friends_conflicts(group_context)

        child_id = (
            "child_5yo"
            if "child_5yo" in role_ids
            else self._first_role_id(role_ids, "child")
        )
        spouse_id = (
            "spouse_dieter"
            if "spouse_dieter" in role_ids
            else self._first_role_id(role_ids, "spouse")
        )
        adult_id = (
            "adult_user"
            if "adult_user" in role_ids
            else self._first_role_id(role_ids, "user")
        )

        if RoleType.CHILD in roles_by_type and RoleType.USER in roles_by_type:
            conflicts.append(
                Conflict(
                    conflict_id="energy_mismatch",
                    conflict_type=ConflictType.ENERGY_MISMATCH,
                    involved_roles=[child_id, adult_id],
                    description="孩子需要互动和体力释放，成人希望轻松参与且不被行程拖累。",
                    severity=4,
                    affected_decisions=[DecisionType.ACTIVITY, DecisionType.TIMELINE],
                    evidence=["孩子角色包含释放体力需求", "用户输入强调几小时和别太远"],
                    resolution_hint="前段优先满足孩子，后段切换到低刺激放松场景。",
                )
            )

        spouse = roles_by_type.get(RoleType.SPOUSE)
        if spouse and any("低" in item or "轻食" in item for item in spouse.hard_constraints):
            conflicts.append(
                Conflict(
                    conflict_id="diet_conflict",
                    conflict_type=ConflictType.DIET_CONFLICT,
                    involved_roles=[spouse_id, child_id, adult_id],
                    description="配偶需要低负担饮食，但家庭出游又需要方便、轻松、不显得被特殊照顾。",
                    severity=4,
                    affected_decisions=[DecisionType.DINING, DecisionType.ROUTE],
                    evidence=["配偶最近在减肥", "家庭场景需要餐饮便利和情绪照顾"],
                    resolution_hint="选择正常氛围的轻食或多选项餐厅，把低卡作为自然选择而不是特殊安排。",
                )
            )

        if group_context.group_type == GroupType.FAMILY:
            conflicts.append(
                Conflict(
                    conflict_id="participation_gap",
                    conflict_type=ConflictType.PACE_CONFLICT,
                    involved_roles=[role.role_id for role in group_context.roles],
                    description="成人可能变成纯陪同和照看者，孩子与减脂配偶的需求都被满足时，成人参与感容易被牺牲。",
                    severity=3,
                    affected_decisions=[
                        DecisionType.ACTIVITY,
                        DecisionType.ROUTE,
                        DecisionType.TIMELINE,
                    ],
                    evidence=["存在儿童优先阶段", "配偶有餐饮硬约束", "成人用户希望轻松参与"],
                    resolution_hint="让成人拥有一个明确优先阶段，并用短转场和休息节点补偿前段陪伴成本。",
                )
            )

        if not conflicts:
            conflicts.append(
                Conflict(
                    conflict_id="conf_unknown_001",
                    conflict_type=ConflictType.UNKNOWN,
                    involved_roles=[role.role_id for role in group_context.roles],
                    description="暂未发现显著冲突，但仍需避免单一角色主导全部行程。",
                    severity=2,
                    affected_decisions=[DecisionType.ACTIVITY],
                    evidence=["输入信息较少"],
                    resolution_hint="采用最小后悔策略，优先低风险、低转场、高兼容地点。",
                )
            )

        return conflicts

    def _detect_friends_conflicts(self, group_context: GroupContext) -> list[Conflict]:
        role_ids = {role.role_id for role in group_context.roles}
        photo_id = self._pick(role_ids, "photo_oriented_role")
        practical_id = self._pick(role_ids, "practical_oriented_role")
        budget_id = self._pick(role_ids, "budget_sensitive_role")
        lively_id = self._pick(role_ids, "lively_oriented_role")
        return [
            Conflict(
                conflict_id="atmosphere_vs_efficiency_conflict",
                conflict_type=ConflictType.PHOTO_VS_PRACTICAL,
                involved_roles=[photo_id, practical_id],
                description="一部分朋友希望地点有氛围、能拍照，另一部分朋友更在意路线顺、不折腾、少排队。",
                severity=4,
                affected_decisions=[
                    DecisionType.ACTIVITY,
                    DecisionType.ROUTE,
                    DecisionType.TIMELINE,
                ],
                evidence=["输入提到想拍照和有氛围", "同时强调别太折腾"],
                resolution_hint="把拍照氛围放在一个明确阶段，其余阶段用低转场和可执行性补偿。",
            ),
            Conflict(
                conflict_id="quiet_vs_lively_conflict",
                conflict_type=ConflictType.INDOOR_OUTDOOR,
                involved_roles=[practical_id, lively_id, photo_id],
                description="有人希望热闹、有周末感，也有人可能偏好安静聊天和稳定体验，氛围强度需要分段控制。",
                severity=3,
                affected_decisions=[DecisionType.ACTIVITY, DecisionType.DINING],
                evidence=["朋友局包含氛围诉求", "半天行程需要避免全程过吵或过静"],
                resolution_hint="前段安排轻探索或拍照，中段选择可聊天餐饮，避免单一氛围贯穿全程。",
            ),
            Conflict(
                conflict_id="budget_pressure",
                conflict_type=ConflictType.BUDGET_CONFLICT,
                involved_roles=[budget_id, photo_id, lively_id],
                description="拍照氛围和周末感容易推高客单价，但预算敏感角色希望控制成本。",
                severity=3,
                affected_decisions=[DecisionType.DINING, DecisionType.ACTIVITY],
                evidence=["输入明确预算别太高", "拍照和氛围通常对应更高消费或排队成本"],
                resolution_hint="优先选择低门槛拍照点，把高消费项目变成可选而不是主线。",
            ),
        ]

    def _pick(self, role_ids: set[str], preferred: str) -> str:
        return preferred if preferred in role_ids else sorted(role_ids)[0]

    def _first_role_id(self, role_ids: set[str], prefix: str) -> str:
        return next((role_id for role_id in sorted(role_ids) if role_id.startswith(prefix)), prefix)
