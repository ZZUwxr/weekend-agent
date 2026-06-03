"""Stable preset data for endpoints that don't depend on PlanOutput.

These are backend-driven static responses matching the frontend mock data exactly.
They can be enhanced later with real user data from a user service.
"""

from local_explorer_agent.app.mobile.schemas import (
    ActivityPreferencesPageDto,
    ActivityTagOptionDto,
    BudgetPacePreferencesPageDto,
    BudgetPaceRadioOptionDto,
    HomeCompanionOptionDto,
    DietaryFamilyMemberRowDto,
    DietaryNeedOptionDto,
    DietaryPreferencesPageDto,
    HomeDashboardDto,
    HomeHistoryItemDto,
    HomeSceneCardDto,
    ProfileArchiveTagDto,
    ProfileMemoryRowDto,
    ProfilePageDto,
    ProfilePreferenceRowDto,
    ProfileQuickFooterActionDto,
    ProfileTravelTemplateDto,
    TravelDurationOptionDto,
    TravelModeMethodOptionDto,
    TravelModeSettingsPageDto,
    TravelRadiusPresetDto,
)

_STATUS_BAR_URL = "/assets/home-statusBar.png"
_MASCOT_URL = "/assets/home-mascot.png"
_VOICE_ICON_URL = "/assets/home-voiceInput.png"

HOME_DASHBOARD = HomeDashboardDto(
    greeting_lines=("HI~ ✨", "今天有什么安排？"),
    mascot_image_url=_MASCOT_URL,
    status_bar_image_url=_STATUS_BAR_URL,
    voice_input_icon_url=_VOICE_ICON_URL,
    scene_section_title="场景快选",
    scenes=[
        HomeSceneCardDto(
            id="scene_couple", variant="couple",
            title="情侣约会", subtitle="COUPLE", tag="浪漫氛围",
        ),
        HomeSceneCardDto(
            id="scene_friends", variant="friends",
            title="朋友聚会", subtitle="Friendship", tag="释放压力",
        ),
        HomeSceneCardDto(
            id="scene_family", variant="family",
            title="家庭亲子", subtitle="Family", tag="寓教于乐",
        ),
        HomeSceneCardDto(
            id="scene_solo", variant="solo",
            title="个人出游", subtitle="Solo", tag="自我放松",
        ),
    ],
    filter_tags=["距离最近", "价格实惠", "休闲娱乐", "环境氛围"],
    companion_section_title="这次和谁一起",
    companion_options=[
        HomeCompanionOptionDto(
            id="self",
            label="只有我",
            role_label="本人",
            summary="按个人偏好规划，不额外带入同行人约束",
            avatar_emoji="🙋",
            selected_by_default=True,
        ),
    ],
    history_section_title="历史安排",
    history=[
        HomeHistoryItemDto(
            id="hist_1", title="小小探险家的下午",
            meta_line="上周六 · 家庭亲子 · 3人 · ¥388",
        ),
        HomeHistoryItemDto(
            id="hist_2", title="四人小馆觅食记",
            meta_line="上上六 · 朋友 · 4人 · ¥530",
        ),
    ],
)

PROFILE_PAGE = ProfilePageDto(
    status_bar_image_url=_STATUS_BAR_URL,
    nav_title="我的",
    show_notifications_bell=True,
    user_name="",
    avatar_emoji=None,
    default_start_line="默认起点：家（科技生活区）",
    archive_section_title="同行人出行档案",
    archive_edit_label="编辑",
    archive_tags=[
        ProfileArchiveTagDto(id="a1", icon_emoji="👶", label="儿子 · 5岁"),
        ProfileArchiveTagDto(id="a2", icon_emoji="💗", label="老婆 · 减肥期"),
        ProfileArchiveTagDto(id="a3", icon_emoji="🙋", label="我"),
    ],
    preference_section_title="出行偏好",
    preference_edit_label="编辑",
    preference_rows=[
        ProfilePreferenceRowDto(
            id="p1", kind="car",
            title="出行方式与距离", summary="打车 · 5km内 · 3–4小时",
        ),
        ProfilePreferenceRowDto(
            id="p2", kind="food",
            title="饮食偏好", summary="需低卡 · 需儿童餐",
        ),
        ProfilePreferenceRowDto(
            id="p3", kind="activity",
            title="活动偏好", summary="户外自然 · 互动体验",
        ),
        ProfilePreferenceRowDto(
            id="p4", kind="budget",
            title="预算与节奏", summary="中等 · 放松型",
        ),
    ],
    memory_section_title="记忆与偏好",
    memory_rows=[
        ProfileMemoryRowDto(
            id="m1", kind="agent_weights", label="Agent 学到的偏好权重",
        ),
        ProfileMemoryRowDto(
            id="m2", kind="last_feedback", label="上次出行反馈",
        ),
        ProfileMemoryRowDto(
            id="m3", kind="disliked_places", label="不喜欢的地点",
        ),
    ],
    templates_section_title="常用出行模板",
    templates=[
        ProfileTravelTemplateDto(
            id="t1", title="周末家庭出行",
            usage_badge="使用 3 次", thumb_emoji="👨‍👩‍👧",
        ),
        ProfileTravelTemplateDto(
            id="t2", title="朋友聚会",
            usage_badge="使用 2 次", thumb_emoji="🍻",
        ),
    ],
    quick_footer_actions=[
        ProfileQuickFooterActionDto(id="q0", kind="settings", label="设置"),
        ProfileQuickFooterActionDto(id="q1", kind="share", label="分享"),
        ProfileQuickFooterActionDto(id="q2", kind="rate", label="评价"),
        ProfileQuickFooterActionDto(id="q3", kind="help", label="帮助"),
        ProfileQuickFooterActionDto(id="q4", kind="about", label="关于"),
    ],
)

TRAVEL_MODE_SETTINGS = TravelModeSettingsPageDto(
    status_bar_image_url=_STATUS_BAR_URL,
    nav_title="出行方式与距离",
    back_label="返回",
    method_section_title="默认出行方式",
    method_options=[
        TravelModeMethodOptionDto(id="taxi", label="打车"),
        TravelModeMethodOptionDto(id="self_drive", label="自驾"),
        TravelModeMethodOptionDto(id="transit", label="地铁/公交"),
    ],
    selected_method_id="taxi",
    radius_section_title="默认出行半径",
    radius_value_format="{km}km内",
    radius_slider_min_km=1,
    radius_slider_max_km=15,
    radius_slider_step_km=1,
    selected_radius_km=5,
    radius_presets=[
        TravelRadiusPresetDto(id="r3", label="3km", value_km=3),
        TravelRadiusPresetDto(id="r5", label="5km", value_km=5),
        TravelRadiusPresetDto(id="r10", label="10km", value_km=10),
    ],
    duration_section_title="默认出行时长",
    duration_options=[
        TravelDurationOptionDto(
            id="dur-afternoon", label="3–4 小时（下午半天）",
        ),
        TravelDurationOptionDto(
            id="dur-short", label="2 小时内（短暂出行）",
        ),
        TravelDurationOptionDto(
            id="dur-half", label="半天（4–6 小时）",
        ),
        TravelDurationOptionDto(id="dur-full", label="全天"),
    ],
    selected_duration_id="dur-afternoon",
    save_button_label="保存修改",
)

DIETARY_PREFERENCES = DietaryPreferencesPageDto(
    status_bar_image_url=_STATUS_BAR_URL,
    nav_title="饮食偏好",
    nav_subtitle="适用对象：全部成员 / 可分别设置",
    back_label="返回",
    special_needs_section_title="特殊饮食需求（可多选）",
    need_options=[
        DietaryNeedOptionDto(id="need-lowcal", label="低卡 / 健康轻食"),
        DietaryNeedOptionDto(id="need-veg", label="素食"),
        DietaryNeedOptionDto(id="need-halal", label="清真"),
        DietaryNeedOptionDto(
            id="need-none", label="无特殊", exclusive=True,
        ),
        DietaryNeedOptionDto(
            id="need-allergen", label="过敏源（展开填写）",
            expand_when_checked=True,
        ),
    ],
    selected_need_ids=["need-lowcal"],
    family_section_title="添加人物偏好",
    family_members=[
        DietaryFamilyMemberRowDto(
            id="f-son", name="儿子",
            summary_line="偏好：儿童餐 · 不辣", avatar_emoji="👦",
        ),
        DietaryFamilyMemberRowDto(
            id="f-wife", name="老婆",
            summary_line="约束：低卡 · 健康轻食", avatar_emoji="👩",
        ),
        DietaryFamilyMemberRowDto(
            id="f-me", name="我",
            summary_line="无特殊", avatar_emoji="🙋‍♂️",
        ),
    ],
    save_button_label="保存修改",
)

ACTIVITY_PREFERENCES = ActivityPreferencesPageDto(
    status_bar_image_url=_STATUS_BAR_URL,
    nav_title="活动偏好",
    back_label="返回",
    tags_section_title="偏好的活动类型（可多选）",
    tag_options=[
        ActivityTagOptionDto(
            id="tag-nature", label="户外自然（公园/农场/绿道）",
        ),
        ActivityTagOptionDto(
            id="tag-interactive", label="互动体验（手工/喂动物等）",
        ),
        ActivityTagOptionDto(
            id="tag-art", label="文艺展览（美术馆/博物馆）",
        ),
        ActivityTagOptionDto(
            id="tag-shopping", label="逛街购物（商场/市集）",
        ),
        ActivityTagOptionDto(
            id="tag-sports", label="运动健身（骑行/攀岩等）",
        ),
        ActivityTagOptionDto(
            id="tag-quiet", label="安静放松（咖啡/书店/SPA）",
        ),
    ],
    selected_tag_ids=["tag-nature", "tag-interactive"],
    family_section_title="添加人物偏好",
    family_members=[
        DietaryFamilyMemberRowDto(
            id="f-son", name="儿子",
            summary_line="体力充沛 · 需互动体验", avatar_emoji="👦",
        ),
        DietaryFamilyMemberRowDto(
            id="f-wife", name="老婆",
            summary_line="不喜太累 · 需有参与感", avatar_emoji="👩",
        ),
        DietaryFamilyMemberRowDto(
            id="f-me", name="我",
            summary_line="无特殊", avatar_emoji="🙋‍♂️",
        ),
    ],
    save_button_label="保存修改",
)

BUDGET_PACE_PREFERENCES = BudgetPacePreferencesPageDto(
    status_bar_image_url=_STATUS_BAR_URL,
    nav_title="预算与节奏",
    back_label="返回",
    budget_section_title="预算倾向",
    budget_options=[
        BudgetPaceRadioOptionDto(
            id="budget-value",
            title="性价比优先",
            description="更关注价格与实用，优先选择高性价比的行程安排。",
        ),
        BudgetPaceRadioOptionDto(
            id="budget-medium",
            title="中等（人均80-150）",
            description="平衡预算与体验，兼顾性价比与舒适度。",
        ),
        BudgetPaceRadioOptionDto(
            id="budget-quality",
            title="品质体验优先",
            description="更看重体验与服务，优先选择更高品质的安排。",
        ),
    ],
    selected_budget_id="budget-medium",
    pace_section_title="行程节奏偏好",
    pace_options=[
        BudgetPaceRadioOptionDto(
            id="pace-tight",
            title="紧凑充实（多打卡）",
            description="行程安排紧凑，尽可能多看景点、打卡体验。",
        ),
        BudgetPaceRadioOptionDto(
            id="pace-relaxed",
            title="放松舒适（有缓冲休息）",
            description="留出充足休息时间，行程从容不赶路。",
        ),
        BudgetPaceRadioOptionDto(
            id="pace-spontaneous",
            title="随性自由（走哪算哪）",
            description="行程灵活随意，按当天心情自由安排。",
        ),
    ],
    selected_pace_id="pace-relaxed",
    save_button_label="保存修改",
)
