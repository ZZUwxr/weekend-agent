"""Presenter: maps PlanOutput domain model to mobile-friendly DTOs.

Port of frontend_phone/src/lib/api/weekend-agent.adapter.ts mapping logic.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from local_explorer_agent.app.agent.skills.timeline_builder import (
    select_route_transport,
)
from local_explorer_agent.app.domain.models import (
    PlanCandidate,
    PlanOutput,
    Stage,
)
from local_explorer_agent.app.mobile.schemas import (
    BookingCheckoutPageDto,
    BookingFlowAiMessage,
    BookingFlowItemDto,
    BookingFlowProgressBanner,
    BookingFlowTodoCard,
    BookingFlowUserPill,
    BookingRideDetailCardDto,
    BookingRideLegDto,
    BookingTodoCardDto,
    BookingTodoItemDto,
    BookingTodosPageDto,
    BookingVenueDetailCardDto,
    BookingVenueDetailRowDto,
    ClarificationCardDto,
    ClarificationFieldDto,
    ClarificationOptionDto,
    ItineraryHubFlowChipDto,
    ItineraryHubPageDto,
    ItineraryHubQuickActionDto,
    ItineraryHubTimelineNodeDto,
    ItineraryTimelinePageDto,
    ItineraryTimelineSegmentDto,
    ItineraryTransportDto,
    NeedsSectionDto,
    PageFooterSummaryParts,
    ParticipantNeedCardDto,
    PaymentConfirmationPageDto,
    PaymentConfirmHelpActionDto,
    PaymentConfirmRecommendedRowDto,
    PaymentConfirmRowDto,
    PaymentConfirmTimelineChipDto,
    PaymentLineItemDto,
    PaymentMethodOptionDto,
    PaymentPageDto,
    PlanActivityDto,
    PlanActivityTagDto,
    PlanComparisonPageDto,
    PlanMemberRatingDto,
    TravelConversationPageDto,
    TravelPlanCardDto,
    TravelStatusStepDto,
    TripLiveMapLocationCardDto,
    TripLiveMapPageDto,
    TripLiveMapRemindersCardDto,
    TripLiveMapSnapshotCardDto,
    TripLiveMapStopDto,
)

_STATUS_BAR_URL = "/assets/home-statusBar.png"
_VOICE_ICON_URL = "/assets/home-voiceInput.png"
_MAP_IMAGE_URL = "/map-empty-viewport.png"


# ---------------------------------------------------------------------------
# Public presenter functions
# ---------------------------------------------------------------------------


def _display_input_message(plan: PlanOutput) -> str:
    raw = (plan.input_query or "").strip()
    if not raw:
        return "希望安排轻松的周末活动"
    return re.split(r"\n用户(?:澄清|修改意见)：", raw, maxsplit=1)[0].strip() or raw


def present_conversation_page(plan: PlanOutput) -> TravelConversationPageDto:
    return TravelConversationPageDto(
        travel_id=plan.session_id,
        input_message=_display_input_message(plan),
        status_steps=_build_status_steps(plan),
        clarification=_build_clarification_card(plan),
        needs_section=NeedsSectionDto(
            header_title="正在分析每个人的需求…",
            cards=_build_need_cards(plan),
        ),
    )


def present_plan_comparison(plan: PlanOutput) -> PlanComparisonPageDto:
    return PlanComparisonPageDto(
        travel_id=plan.session_id,
        status_bar_image_url=_STATUS_BAR_URL,
        top_status_text=_build_top_status_text(plan),
        plans=[_map_plan_card(plan, c) for c in plan.plan_candidates],
        assistant_message=_build_assistant_message(plan),
        voice_input_icon_url=_VOICE_ICON_URL,
    )


def present_timeline_page(plan: PlanOutput, plan_id: str) -> ItineraryTimelinePageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    segments = _build_timeline_segments(candidate)
    duration = _sum_stage_minutes(candidate)
    label = _label_for_plan(candidate, plan_id, len(plan.plan_candidates))
    return ItineraryTimelinePageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        voice_input_icon_url=_VOICE_ICON_URL,
        plan_pill_label=label,
        ai_status_message=f"已选择{label}，正在整理详细时间轴与路线。",
        card_title=f"{candidate.title if candidate else '行程'} · 时间轴与路线",
        segments=segments,
        card_footer_summary=f"总时长：约 {_format_duration(duration)}（含活动与转场）",
        page_footer_summary_parts=PageFooterSummaryParts(
            highlight=f"总时长：约 {_format_duration(duration)}",
            rest="（已结合路线、排队和缓冲时间）",
        ),
    )


def present_booking_todos(plan: PlanOutput, plan_id: str) -> BookingTodosPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    venue_items: list[BookingTodoItemDto] = []
    if candidate:
        for stage in candidate.stages:
            if stage.selected_poi:
                venue_items.append(BookingTodoItemDto(
                    id=stage.selected_poi.id or stage.stage_id,
                    kind="venue",
                    title=stage.selected_poi.name or stage.name,
                    subtitle=(
                        f"{_format_duration(stage.duration_minutes)}"
                        f" · {stage.experience_goal}"
                    ),
                    thumbnail_image_url=_generic_poi_image(stage.selected_poi.category),
                    status_label="待预约" if _needs_booking(stage) else "可现场安排",
                ))
    ride_lines = [
        f"{leg.leg_index} {leg.route}（{leg.duration_label}）"
        for leg in _build_ride_legs(candidate)
    ]
    todo_items = [*venue_items]
    if ride_lines:
        todo_items.append(BookingTodoItemDto(
            id="rides",
            kind="rides",
            title="叫车安排",
            lines=ride_lines,
            status_label="待确认",
        ))
    label = _label_for_plan(candidate, plan_id, len(plan.plan_candidates))
    flow: list[BookingFlowItemDto] = [
        BookingFlowAiMessage(id="m1", body=f"已生成 {label} 的详细安排。"),
        BookingFlowAiMessage(id="m2", body="需要帮你把可预约事项整理出来吗？"),
        BookingFlowUserPill(id="u1", label="需要"),
        BookingFlowProgressBanner(id="p1", body="正在整理预约、叫车和分享任务…"),
        BookingFlowTodoCard(id="td1", card=BookingTodoCardDto(
            title="待办事项",
            items=todo_items,
            footer_banner_text="preview 阶段仅生成任务，不会真实预约或叫车",
        )),
        BookingFlowAiMessage(id="m3", body="请查看预约信息，确认后再进入执行。这里只是预览任务。"),
    ]
    return BookingTodosPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        voice_input_icon_url=_VOICE_ICON_URL,
        flow=flow,
    )


def present_booking_checkout(plan: PlanOutput, plan_id: str) -> BookingCheckoutPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    venue_cards: list[BookingVenueDetailCardDto] = []
    if candidate:
        for stage in candidate.stages:
            if stage.selected_poi:
                poi = stage.selected_poi
                venue_cards.append(BookingVenueDetailCardDto(
                    id=poi.id or stage.stage_id,
                    title=poi.name or stage.name,
                    status_badge="待确认 · 未真实预约" if _needs_booking(stage) else "无需预约",
                    thumbnail_image_url=_generic_poi_image(poi.category),
                    rows=[
                        BookingVenueDetailRowDto(label="城市", value=poi.city or "当前城市"),
                        BookingVenueDetailRowDto(label="区域", value=poi.area or "待确认"),
                        BookingVenueDetailRowDto(
                            label="时长",
                            value=_format_duration(stage.duration_minutes),
                        ),
                        BookingVenueDetailRowDto(label="预算", value=_format_price(poi.avg_price)),
                    ],
                ))
    ride_legs = _build_ride_legs(candidate)
    has_ride_legs = bool(ride_legs)
    return BookingCheckoutPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        voice_input_icon_url=_VOICE_ICON_URL,
        top_progress_text="正在进行预约…",
        venue_cards=venue_cards,
        ride_card=BookingRideDetailCardDto(
            id="ride-card",
            title="叫车安排" if has_ride_legs else "当前无需额外叫车",
            status_badge="待确认 · 未真实叫车" if has_ride_legs else "无需处理",
            legs=ride_legs,
            tip_text=(
                "当前仍在 preview 阶段，仅生成可确认的执行任务；确认方案后才会进入真实执行。"
                if has_ride_legs
                else "这次只安排了一个核心地点，没有额外转场任务。"
            ),
        ),
        payment_prompt_text="确认后再执行预约/叫车",
    )


def present_payment_page(plan: PlanOutput, plan_id: str) -> PaymentPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    line_items = _build_payment_lines(candidate)
    amount_due = _sum_amount(line_items)
    return PaymentPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        voice_input_icon_url=_VOICE_ICON_URL,
        top_progress_text="正在生成费用预览…",
        breakdown_title="费用明细",
        line_items=line_items if line_items else [
            PaymentLineItemDto(
                id="placeholder",
                item_label="暂无明细",
                detail_text="确认方案后生成",
                amount_text="待确认",
            ),
        ],
        payment_section_title="付款方式",
        amount_due_badge_label="预估费用",
        amount_due_value=f"¥{amount_due}" if amount_due > 0 else "待确认",
        payment_methods=[
            PaymentMethodOptionDto(id="wechat", type="wechat", badge_text="微", label="微信支付"),
            PaymentMethodOptionDto(id="alipay", type="alipay", badge_text="支", label="支付宝"),
            PaymentMethodOptionDto(id="meituan", type="meituan", badge_text="美", label="美团支付"),
        ],
        default_selected_payment_method_id="wechat",
        tap_to_pay_hint="点击后会在后端记录待处理支付任务",
        query_banner_text="当前为预览费用；支付网关暂未接入，不会发起真实扣款",
    )


def present_trip_live_map(plan: PlanOutput, plan_id: str) -> TripLiveMapPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    stage_names = _stage_names(candidate)
    return TripLiveMapPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        map_image_url=_MAP_IMAGE_URL,
        map_stops=_build_map_stops(candidate),
        snapshot_card=TripLiveMapSnapshotCardDto(
            title="行程快照",
            timeline_text=" → ".join(stage_names) if stage_names else "暂无路线",
            footer_left=f"全程约 {_format_duration(_sum_stage_minutes(candidate))}",
            footer_emphasis=f"综合分 {_format_score(candidate.overall_score if candidate else 0)}",
        ),
        location_card=TripLiveMapLocationCardDto(
            title="当前位置与下一站",
            current_line=f"当前：{stage_names[0] if stage_names else '准备出发'}",
            next_step_line=f"下一步：{stage_names[1] if len(stage_names) > 1 else '按时间轴推进'}",
        ),
        reminders_card=TripLiveMapRemindersCardDto(
            title="行程提醒",
            reminder_lines=[
                "提前 15 分钟叫车",
                "留意天气变化",
                "预留缓冲时间",
            ],
        ),
        call_ride_button_label="叫车",
        ai_bubble_text="行程进行中，有任何需要随时告诉我。",
        voice_input_icon_url=_VOICE_ICON_URL,
    )


def _build_map_stops(candidate: PlanCandidate | None) -> list[TripLiveMapStopDto]:
    if not candidate or not candidate.stages:
        return []

    segments = _build_timeline_segments(candidate)
    positions = [
        (22.0, 33.0),
        (44.0, 50.0),
        (66.0, 63.0),
        (76.0, 77.0),
    ]
    total = max(len(candidate.stages) - 1, 1)
    stops: list[TripLiveMapStopDto] = []
    for index, stage in enumerate(candidate.stages):
        if index < len(positions):
            x_percent, y_percent = positions[index]
        else:
            progress = index / total
            x_percent = 22.0 + (54.0 * progress)
            y_percent = 33.0 + (44.0 * progress)
        stops.append(TripLiveMapStopDto(
            id=stage.stage_id or f"stop-{index + 1}",
            order=index + 1,
            title=stage.selected_poi.name if stage.selected_poi else stage.name,
            time=segments[index].schedule_label.split("-")[0] if index < len(segments) else "待定",
            status_text="进行中" if index == 0 else "待接入",
            x_percent=x_percent,
            y_percent=y_percent,
        ))
    return stops


def present_payment_confirmation(plan: PlanOutput, plan_id: str) -> PaymentConfirmationPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    line_items = _build_payment_lines(candidate)
    rows = [
        PaymentConfirmRowDto(
            id=item.id,
            item_label=item.item_label,
            detail_text=item.detail_text,
            status_kind="remind_later" if "到时" in item.amount_text else "pending_provider",
            status_text="到时提醒" if "到时" in item.amount_text else "待接入",
        )
        for item in line_items
    ]
    chips = _build_timeline_chips(candidate)
    return PaymentConfirmationPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        nav_title="确认单",
        hero_title="任务已记录",
        hero_subtitle="支付、预约和叫车外部服务暂未接入，当前仅记录后端待处理任务。",
        confirmation_section_title="待处理任务确认单",
        table_col_item="项目",
        table_col_detail="详情",
        table_col_status="状态",
        rows=rows if rows else [
            PaymentConfirmRowDto(
                id="placeholder",
                item_label="暂无预订",
                detail_text="确认方案后生成",
                status_kind="pending_provider",
                status_text="待生成",
            ),
        ],
        total_label="预估合计",
        total_value=f"¥{_sum_amount(line_items)}" if _sum_amount(line_items) > 0 else "待确认",
        recommended_section_title="推荐套餐",
        recommended_rows=_build_confirmation_recommended_rows(plan, candidate),
        timeline_section_title="行程时间线",
        timeline_chips=chips,
        help_section_title="还能帮你",
        help_actions=[
            PaymentConfirmHelpActionDto(id="h1", kind="share", label="分享行程"),
            PaymentConfirmHelpActionDto(id="h2", kind="calendar", label="加入日历"),
            PaymentConfirmHelpActionDto(id="h3", kind="bell", label="设置提醒"),
        ],
        help_summary_text="外部服务暂未接入，点击操作会继续记录为后端待处理任务。",
        voice_input_icon_url=_VOICE_ICON_URL,
    )


def present_itinerary_hub(plan: PlanOutput, plan_id: str) -> ItineraryHubPageDto:
    candidate = _find_candidate(plan, plan_id)
    frontend_plan_id = _frontend_plan_id(plan_id)
    stage_names = _stage_names(candidate)
    hub_nodes = _build_hub_timeline_nodes(candidate)
    return ItineraryHubPageDto(
        travel_id=plan.session_id,
        plan_id=frontend_plan_id,
        status_bar_image_url=_STATUS_BAR_URL,
        nav_title="行程主页",
        show_notifications_bell=True,
        overview_time_range=f"约 {_format_duration(_sum_stage_minutes(candidate))}",
        overview_flow_chips=[
            ItineraryHubFlowChipDto(
                id=f"flow-{i}",
                icon_emoji="🎯" if i == 0 else "📍",
                label=name,
            )
            for i, name in enumerate(stage_names[:4])
        ],
        overview_footer_line=(
            f"{candidate.title if candidate else '当前行程'}"
            f" · 综合分 {_format_score(candidate.overall_score if candidate else 0)}"
        ),
        current_stage_title=stage_names[0] if stage_names else "准备出发",
        current_stage_status_badge="进行中",
        timeline_nodes=hub_nodes,
        quick_actions=[
            ItineraryHubQuickActionDto(id="qa1", kind="map", label="查看地图"),
            ItineraryHubQuickActionDto(id="qa2", kind="share", label="分享行程"),
            ItineraryHubQuickActionDto(id="qa3", kind="calendar", label="加入日历"),
            ItineraryHubQuickActionDto(id="qa4", kind="edit", label="修改方案"),
            ItineraryHubQuickActionDto(id="qa5", kind="cancel", label="取消行程"),
        ],
        history_section_title="历史行程",
        history_items=[],
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_candidate(plan: PlanOutput, plan_id: str) -> PlanCandidate | None:
    backend_id = plan_id.replace("-", "_")
    for c in plan.plan_candidates:
        if c.plan_id == backend_id or c.plan_id == plan_id:
            return c
    return plan.plan_candidates[0] if plan.plan_candidates else None


def _frontend_plan_id(plan_id: str) -> str:
    return plan_id.replace("_", "-")


def _build_status_steps(plan: PlanOutput) -> list[TravelStatusStepDto]:
    if plan.state == "clarifying":
        return [
            TravelStatusStepDto(id="s1", text="正在理解你的出行意图…", icon="loader"),
            TravelStatusStepDto(id="s2", text="有几个关键点需要确认…", icon="alert"),
            TravelStatusStepDto(id="s3", text="也可以按安全默认假设继续…", icon="lightbulb"),
        ]
    return [
        TravelStatusStepDto(id="s1", text="已理解你的出行意图…", icon="loader"),
        TravelStatusStepDto(id="s2", text="已检查时间、天气、路线和排队风险…", icon="alert"),
        TravelStatusStepDto(id="s3", text="正在协调不同成员的偏好…", icon="arrows"),
        TravelStatusStepDto(
            id="s4",
            text=(
                "我已经按你的明确目标整理出一个推荐方案…"
                if len(plan.plan_candidates) == 1
                else f"有 {len(plan.plan_candidates) or 2} 个方案推荐给你…"
            ),
            icon="lightbulb",
        ),
    ]


def _build_clarification_card(plan: PlanOutput) -> ClarificationCardDto:
    questions = plan.clarification.questions if plan.clarification else []
    if questions:
        return ClarificationCardDto(
            title=(
                "想确认一下..."
                if (plan.clarification and plan.clarification.needs_clarification)
                else "这些假设可以吗？"
            ),
            skip_label=(
                "按默认继续"
                if (plan.clarification and plan.clarification.can_continue_with_assumptions)
                else "稍后回答"
            ),
            fields=[
                ClarificationFieldDto(
                    id=q.question_id,
                    kind="chips" if q.options else "supplementary",
                    question=q.question,
                    options=(
                        [ClarificationOptionDto(id=o, label=o) for o in q.options]
                        if q.options else None
                    ),
                    placeholder=q.default_assumption or q.reason,
                )
                for q in questions[:3]
            ],
        )
    assumptions = plan.assumptions or (
        plan.clarification.safe_assumptions if plan.clarification else []
    )
    return ClarificationCardDto(
        title="已整理好关键信息",
        skip_label="继续",
        fields=[
            ClarificationFieldDto(
                id="assumptions",
                kind="chips",
                question="我会先按这些假设规划：" if assumptions else "当前信息足够开始规划：",
                options=[
                    ClarificationOptionDto(id=a, label=a)
                    for a in (assumptions or ["中等预算", "3-4 小时", "路线不过度折返"])[:3]
                ],
            ),
        ],
    )


def _build_need_cards(plan: PlanOutput) -> list[ParticipantNeedCardDto]:
    roles = plan.inferred_context.roles
    if not roles:
        return [ParticipantNeedCardDto(
            id="n1",
            title="整体偏好",
            icon="✨",
            description=[plan.input_query or "希望安排轻松的周末活动"],
        )]
    return [
        ParticipantNeedCardDto(
            id=role.role_id,
            title=role.display_name,
            icon=_role_emoji(str(role.role_type)),
            description=(
                list(role.hard_constraints) + list(role.soft_preferences)
                + list(role.hidden_needs) + list(role.risk_points)
            )[:3],
        )
        for role in roles
    ]


def _build_top_status_text(plan: PlanOutput) -> str:
    if plan.state == "clarifying":
        return "还需要确认几个关键问题后再生成完整方案。"
    if len(plan.plan_candidates) == 1:
        return "这次需求很明确，我直接整理了一个更合适的推荐方案。"
    rec_id = plan.recommended_plan_id.replace("_", "-")
    return f"已生成 {len(plan.plan_candidates)} 个候选方案，推荐 {rec_id}"


def _build_assistant_message(plan: PlanOutput) -> str:
    parts = []
    if plan.assumptions:
        parts.append(f"我已按「{'、'.join(plan.assumptions)}」处理。")
    if plan.share_message:
        parts.append(plan.share_message)
        return " ".join(parts)
    if len(plan.plan_candidates) == 1:
        parts.append("你这次目标很明确，所以我没有硬凑多方案对比，直接给一个最合适的推荐。")
    else:
        parts.append("我先给你几种取舍不同的方案，推荐的是整体更稳的那个。")
    return " ".join(parts)


def _map_plan_card(plan: PlanOutput, candidate: PlanCandidate) -> TravelPlanCardDto:
    recommended = candidate.plan_id == plan.recommended_plan_id
    compensation_paragraphs = [
        p for p in [
            candidate.tradeoff_summary or None,
            candidate.recommendation_reason or None,
            *[s.compensation for s in candidate.satisfaction_scores if s.compensation],
        ]
        if p
    ][:3]
    return TravelPlanCardDto(
        id=candidate.plan_id.replace("_", "-"),
        plan_label=_label_for_plan(candidate, candidate.plan_id, len(plan.plan_candidates)),
        headline=f"{candidate.theme or candidate.title}{' · 推荐' if recommended else ''}",
        recommended=recommended,
        accent="warm" if candidate.plan_id.endswith("_a") else "cool",
        overall_score_label=f"综合 {_format_score(candidate.overall_score)}",
        activities=[
            _map_activity(
                s,
                group_type=str(plan.inferred_context.group_type),
            )
            for s in candidate.stages
        ],
        member_ratings=_build_member_ratings(plan, candidate),
        compensation_title="补偿设计（情绪/成本）" if candidate.tradeoff_summary else None,
        compensation_paragraphs=compensation_paragraphs or None,
    )


def _map_activity(stage: Stage, *, group_type: str = "unknown") -> PlanActivityDto:
    poi = stage.selected_poi
    return PlanActivityDto(
        id=stage.stage_id,
        title=poi.name if poi and poi.name else stage.name,
        duration_label=f"预计 {_format_duration(stage.duration_minutes)}",
        tags=_build_activity_tags(stage, group_type=group_type),
    )


def _build_activity_tags(
    stage: Stage,
    *,
    group_type: str = "unknown",
) -> list[PlanActivityTagDto]:
    poi = stage.selected_poi
    tags: list[str | None] = [
        f"体力 {stage.energy_level}/5",
        "室内" if poi and poi.indoor else ("户外" if poi and not poi.indoor else None),
        f"排队 {poi.queue_risk}" if poi and poi.queue_risk else None,
        poi.category if poi else None,
        *(_audience_tags_for_display(poi.suitable_for, group_type=group_type) if poi else []),
    ]
    return [
        PlanActivityTagDto(id=f"{stage.stage_id}-tag-{i}", label=t)
        for i, t in enumerate(tags)
        if t
    ]


def _audience_tags_for_display(
    values: list[str],
    *,
    group_type: str,
) -> list[str]:
    tags = list(values[:4])
    if group_type != "family":
        tags = [tag for tag in tags if not _has_any(tag, ("亲子", "孩子", "儿童", "宝宝"))]
    if group_type != "solo":
        tags = [tag for tag in tags if not _has_any(tag, ("独处", "单人", "一个人"))]
    return tags[:2]


def _has_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _build_member_ratings(plan: PlanOutput, candidate: PlanCandidate) -> list[PlanMemberRatingDto]:
    roles = {r.role_id: r for r in plan.inferred_context.roles}
    scores = candidate.satisfaction_scores
    if not scores:
        return [PlanMemberRatingDto(
            id="overall",
            label="整体",
            emoji="✨",
            score=candidate.overall_score,
            stars_filled=int(candidate.overall_score),
        )]
    return [
        PlanMemberRatingDto(
            id=s.role_id,
            label=roles[s.role_id].display_name if s.role_id in roles else s.role_id,
            emoji=_role_emoji(str(roles[s.role_id].role_type) if s.role_id in roles else ""),
            score=s.score,
            stars_filled=int(s.score),
        )
        for s in scores[:3]
    ]


def _build_timeline_segments(candidate: PlanCandidate | None) -> list[ItineraryTimelineSegmentDto]:
    if not candidate:
        return []
    timeline = candidate.timeline
    if timeline:
        route_lookup = _route_lookup(candidate)
        first_time = _parse_clock(timeline[0].time)
        current = first_time or datetime(2000, 1, 1, 14, 30)
        previous_poi_id: str | None = None
        segments: list[ItineraryTimelineSegmentDto] = []
        for i, item in enumerate(timeline):
            segment, duration = _timeline_item_to_segment(
                item,
                i,
                route_lookup,
                current,
                previous_poi_id,
            )
            segments.append(segment)
            current += timedelta(minutes=duration)
            if str(item.type) != "transport" and item.poi_id:
                previous_poi_id = item.poi_id
        return segments
    minute_offset = 0
    segments: list[ItineraryTimelineSegmentDto] = []
    for stage in candidate.stages:
        start = _minutes_to_clock(14 * 60 + 30 + minute_offset)
        minute_offset += stage.duration_minutes
        end = _minutes_to_clock(14 * 60 + 30 + minute_offset)
        poi = stage.selected_poi
        meta_lines: list[str] = [stage.experience_goal]
        if poi and poi.area:
            meta_lines.append(f"区域：{poi.area}")
        if poi and poi.queue_risk:
            meta_lines.append(f"排队风险：{poi.queue_risk}")
        segments.append(ItineraryTimelineSegmentDto(
            id=stage.stage_id,
            schedule_label=f"{start}-{end}",
            schedule_note=_format_duration(stage.duration_minutes),
            title=poi.name if poi and poi.name else stage.name,
            meta_lines=meta_lines,
            detail_lines=[stage.reasoning] if stage.reasoning else None,
            transport=_transport_for(str(stage.stage_type)),
        ))
    return segments


def _timeline_item_to_segment(
    item: Any,
    index: int,
    route_lookup: dict[tuple[str | None, str | None], dict[str, object]],
    current: datetime,
    previous_poi_id: str | None,
) -> tuple[ItineraryTimelineSegmentDto, int]:
    mode = item.mode
    duration = item.duration_minutes
    if str(item.type) == "transport":
        route = route_lookup.get((previous_poi_id, item.poi_id), {})
        if route:
            mode, duration = select_route_transport(route)
    return ItineraryTimelineSegmentDto(
        id=f"{item.poi_id or item.type}-{index}",
        schedule_label=current.strftime("%H:%M"),
        schedule_note=_format_duration(duration),
        title=item.poi_name or item.notes or str(item.type),
        meta_lines=[
            p for p in [
                f"方式：{mode}" if mode else None,
                f"预计费用：¥{item.estimated_cost}" if item.estimated_cost else None,
                item.notes or None,
            ]
            if p
        ],
        transport=_transport_for(str(item.type), mode),
    ), duration


def _route_lookup(candidate: PlanCandidate) -> dict[tuple[str | None, str | None], dict[str, object]]:
    return {
        (str(item.get("from")), str(item.get("to"))): item
        for item in candidate.route_segments
    }


def _parse_clock(value: str) -> datetime | None:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError:
        return None
    return datetime(2000, 1, 1, parsed.hour, parsed.minute)


def _build_ride_legs(candidate: PlanCandidate | None) -> list[BookingRideLegDto]:
    if not candidate:
        return []
    route_segments = candidate.route_segments
    if route_segments:
        return [
            BookingRideLegDto(
                id=f"route-{i}",
                leg_index=_number_circle(i + 1),
                category_label="路线",
                route=_route_name(seg, candidate),
                distance_label=_value_label(seg, ["distance_km", "distance"], "km"),
                duration_label=_value_label(seg, ["duration_minutes", "duration"], "min"),
                fee_label=_value_label(seg, ["estimated_cost", "cost"], "¥"),
                handling_label="确认后执行",
            )
            for i, seg in enumerate(route_segments)
        ]
    pois = [
        s.selected_poi.name if s.selected_poi and s.selected_poi.name else s.name
        for s in candidate.stages
    ]
    return [
        BookingRideLegDto(
            id=f"leg-{i}",
            leg_index=_number_circle(i + 1),
            category_label="转场",
            route=f"{pois[i]} → {pois[i + 1]}",
            distance_label="待估算",
            duration_label="约 15min",
            fee_label="到时支付",
            handling_label="提醒叫车",
        )
        for i in range(len(pois) - 1)
    ]


def _build_payment_lines(candidate: PlanCandidate | None) -> list[PaymentLineItemDto]:
    if not candidate:
        return []
    venue_lines = [
        PaymentLineItemDto(
            id=stage.selected_poi.id or stage.stage_id,
            item_label=stage.selected_poi.name or stage.name,
            detail_text=(
                f"{_format_duration(stage.duration_minutes)}"
                f" · {stage.selected_poi.category or str(stage.stage_type)}"
            ),
            amount_text=_format_price(stage.selected_poi.avg_price),
        )
        for stage in candidate.stages
        if stage.selected_poi
    ]
    ride_lines = [
        PaymentLineItemDto(
            id=leg.id,
            item_label=f"{leg.leg_index} 叫车",
            detail_text=leg.route,
            amount_text=leg.fee_label if leg.fee_label.startswith("¥") else "到时支付",
        )
        for leg in _build_ride_legs(candidate)
    ]
    return venue_lines + ride_lines


def _build_timeline_chips(candidate: PlanCandidate | None) -> list[PaymentConfirmTimelineChipDto]:
    segments = _build_timeline_segments(candidate)[:5]
    return [
        PaymentConfirmTimelineChipDto(
            id=seg.id,
            time=seg.schedule_label.split("-")[0],
            icon_emoji=seg.transport.emoji if seg.transport else "📍",
            label=seg.title or f"阶段 {i + 1}",
        )
        for i, seg in enumerate(segments)
    ]


def _build_confirmation_recommended_rows(
    plan: PlanOutput,
    candidate: PlanCandidate | None,
) -> list[PaymentConfirmRecommendedRowDto]:
    group_type = str(plan.inferred_context.group_type)
    if group_type == "family":
        return [
            PaymentConfirmRecommendedRowDto(
                id="rec-family",
                name="家庭友好提醒",
                audience_label="洗手间/休息点/低排队",
                price_text="待确认",
                thumb_emoji="🧸",
            )
        ]
    if group_type == "couple":
        return [
            PaymentConfirmRecommendedRowDto(
                id="rec-couple",
                name="约会体验提醒",
                audience_label="适合聊天/拍照/低转场",
                price_text="待确认",
                thumb_emoji="✨",
            )
        ]
    if group_type == "solo":
        return [
            PaymentConfirmRecommendedRowDto(
                id="rec-solo",
                name="独处节奏提醒",
                audience_label="安静/可久坐/少排队",
                price_text="待确认",
                thumb_emoji="☕",
            )
        ]
    if group_type == "friends":
        return [
            PaymentConfirmRecommendedRowDto(
                id="rec-friends",
                name="朋友局提醒",
                audience_label="预算/拍照/路线顺",
                price_text="待确认",
                thumb_emoji="📸",
            )
        ]
    primary_category = next(
        (
            stage.selected_poi.category
            for stage in (candidate.stages if candidate else [])
            if stage.selected_poi is not None and stage.selected_poi.category
        ),
        "轻出行",
    )
    return [
        PaymentConfirmRecommendedRowDto(
            id="rec-general",
            name="行程执行提醒",
            audience_label=f"{primary_category}/少排队/低转场",
            price_text="待确认",
            thumb_emoji="📍",
        )
    ]


def _build_hub_timeline_nodes(candidate: PlanCandidate | None) -> list[ItineraryHubTimelineNodeDto]:
    segments = _build_timeline_segments(candidate)[:6]
    return [
        ItineraryHubTimelineNodeDto(
            id=seg.id,
            kind="active" if i == 0 else "upcoming",
            time=seg.schedule_label.split("-")[0],
            title=seg.title,
            subtitle=seg.schedule_note,
            icon_emoji=seg.transport.emoji if seg.transport else "📍",
        )
        for i, seg in enumerate(segments)
    ]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _needs_booking(stage: Stage) -> bool:
    return str(stage.stage_type) in ("dine", "energy_release", "explore")


def _label_for_plan(
    candidate: PlanCandidate | None,
    fallback_plan_id: str,
    candidates_count: int | None = None,
) -> str:
    if candidates_count == 1:
        return "推荐方案"
    plan_type = candidate.plan_type if candidate else fallback_plan_id.replace("-", "_")
    if plan_type.endswith("_a"):
        suffix = "A"
    elif plan_type.endswith("_b"):
        suffix = "B"
    elif plan_type.endswith("_c"):
        suffix = "C"
    else:
        suffix = "A"
    return f"Plan {suffix}"


def _sum_stage_minutes(candidate: PlanCandidate | None) -> int:
    if not candidate:
        return 240
    total = sum(s.duration_minutes for s in candidate.stages)
    return total or 240


def _sum_amount(items: list[PaymentLineItemDto]) -> int:
    total = 0
    for item in items:
        m = re.search(r"¥(\d+)", item.amount_text)
        if m:
            total += int(m.group(1))
    return total


def _format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} 分钟"
    hours = minutes // 60
    rest = minutes % 60
    return f"{hours} 小时 {rest} 分钟" if rest else f"{hours} 小时"


def _format_price(price: int | None) -> str:
    if isinstance(price, (int, float)) and price > 0:
        return f"¥{price}"
    return "待确认"


def _format_score(score: float) -> str:
    s = f"{score:.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _role_emoji(role_type: str) -> str:
    emojis = {
        "child": "👧", "spouse": "👩", "user": "👤",
        "friend": "👥", "elder": "👵",
    }
    return emojis.get(role_type, "✨")


def _transport_for(type_: str, mode: str | None = None) -> ItineraryTransportDto:
    key = f"{type_} {mode or ''}"
    if "taxi" in key or "car" in key or "transport" in key:
        return ItineraryTransportDto(emoji="🚗", label=mode or "转场")
    if "dine" in key:
        return ItineraryTransportDto(emoji="🍴", label="用餐")
    if "buffer" in key or "relax" in key:
        return ItineraryTransportDto(emoji="☕", label="休息")
    return ItineraryTransportDto(emoji="📍", label="游玩")


def _minutes_to_clock(total_minutes: int) -> str:
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _number_circle(index: int) -> str:
    circles = ["①", "②", "③", "④", "⑤"]
    return circles[index - 1] if 1 <= index <= 5 else f"{index}."


def _generic_poi_image(category: str | None) -> str | None:
    # Mobile runtime must not depend on external thumbnail hosts.
    return None


def _value_label(segment: dict[str, Any], keys: list[str], unit: str) -> str:
    for key in keys:
        if key in segment and segment[key] is not None:
            val = segment[key]
            if isinstance(val, (int, float)):
                if unit == "¥":
                    return f"¥{round(val)}"
                return f"{round(val)}{unit}"
    return "到时支付" if unit == "¥" else "待估算"


def _route_name(segment: dict[str, Any], candidate: PlanCandidate) -> str:
    from_name = segment.get("from_poi_name") or segment.get("from_name")
    to_name = segment.get("to_poi_name") or segment.get("to_name")
    if from_name or to_name:
        return f"{from_name or '起点'} → {to_name or '终点'}"
    names = [
        s.selected_poi.name if s.selected_poi and s.selected_poi.name else s.name
        for s in candidate.stages
    ]
    return f"{names[0]} → {names[1]}" if len(names) > 1 else "路线待确认"


def _stage_names(candidate: PlanCandidate | None) -> list[str]:
    if not candidate:
        return []
    return [
        s.selected_poi.name if s.selected_poi and s.selected_poi.name else s.name
        for s in candidate.stages
    ]
