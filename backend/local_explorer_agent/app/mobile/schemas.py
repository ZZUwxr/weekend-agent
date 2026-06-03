"""Mobile BFF response schemas -- mirrors frontend_phone/src/lib/api/types.ts exactly."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class MobileModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Home Dashboard
# ---------------------------------------------------------------------------


class HomeSceneCardDto(MobileModel):
    id: str
    variant: Literal["couple", "friends", "family", "solo"]
    title: str
    subtitle: str
    tag: str


class HomeHistoryItemDto(MobileModel):
    id: str
    title: str
    meta_line: str
    plan_id: str | None = None


class HomeCompanionOptionDto(MobileModel):
    id: str
    label: str
    role_label: str
    summary: str
    avatar_emoji: str
    selected_by_default: bool = False


class HomeDashboardDto(MobileModel):
    greeting_lines: tuple[str, str]
    mascot_image_url: str
    status_bar_image_url: str
    voice_input_icon_url: str
    scene_section_title: str
    scenes: list[HomeSceneCardDto]
    filter_tags: list[str]
    companion_section_title: str = "同行人"
    companion_options: list[HomeCompanionOptionDto] = Field(default_factory=list)
    history_section_title: str
    history: list[HomeHistoryItemDto]


# ---------------------------------------------------------------------------
# Travel Session / Conversation
# ---------------------------------------------------------------------------


class LLMRuntimeConfigBody(MobileModel):
    provider: Literal["mock", "openai"] = "mock"
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class StartTravelSessionBody(MobileModel):
    message: str
    user_id: str | None = None
    companion_ids: list[str] = Field(default_factory=list)
    llm_config: LLMRuntimeConfigBody | None = None


class StartTravelSessionResponse(MobileModel):
    travel_id: str


class ActiveTravelDto(MobileModel):
    travel_id: str | None = None
    plan_id: str | None = None
    state: str | None = None
    updated_at: str | None = None


class TravelStatusStepDto(MobileModel):
    id: str
    text: str
    icon: Literal["loader", "alert", "arrows", "lightbulb"]


class ClarificationOptionDto(MobileModel):
    id: str
    label: str


class ClarificationFieldDto(MobileModel):
    id: str
    kind: Literal["chips", "supplementary"]
    question: str
    options: list[ClarificationOptionDto] | None = None
    placeholder: str | None = None
    selected_option_ids: list[str] | None = None


class ClarificationCardDto(MobileModel):
    title: str
    skip_label: str
    fields: list[ClarificationFieldDto]


class ParticipantNeedCardDto(MobileModel):
    id: str
    title: str
    icon: str
    description: list[str]


class NeedsSectionDto(MobileModel):
    header_title: str
    cards: list[ParticipantNeedCardDto]


class TravelConversationPageDto(MobileModel):
    travel_id: str
    input_message: str | None = None
    status_steps: list[TravelStatusStepDto]
    clarification: ClarificationCardDto
    needs_section: NeedsSectionDto
    follow_up_user_message: str | None = None


# ---------------------------------------------------------------------------
# Plan Comparison
# ---------------------------------------------------------------------------


class PlanActivityTagDto(MobileModel):
    id: str
    label: str


class PlanActivityDto(MobileModel):
    id: str
    title: str
    duration_label: str
    tags: list[PlanActivityTagDto]


class PlanMemberRatingDto(MobileModel):
    id: str
    label: str
    emoji: str
    score: float
    stars_filled: int


class TravelPlanCardDto(MobileModel):
    id: str
    plan_label: str
    headline: str
    recommended: bool = False
    accent: Literal["warm", "cool"] | None = None
    overall_score_label: str
    activities: list[PlanActivityDto]
    member_ratings: list[PlanMemberRatingDto]
    compensation_title: str | None = None
    compensation_paragraphs: list[str] | None = None


class PlanComparisonPageDto(MobileModel):
    travel_id: str
    status_bar_image_url: str
    top_status_text: str
    plans: list[TravelPlanCardDto]
    assistant_message: str
    voice_input_icon_url: str


# ---------------------------------------------------------------------------
# Itinerary Timeline
# ---------------------------------------------------------------------------


class ItineraryTransportDto(MobileModel):
    emoji: str
    label: str


class ItineraryTimelineSegmentDto(MobileModel):
    id: str
    schedule_label: str
    schedule_note: str | None = None
    title: str
    meta_lines: list[str]
    detail_lines: list[str] | None = None
    transport: ItineraryTransportDto | None = None


class PageFooterSummaryParts(MobileModel):
    highlight: str
    rest: str


class ItineraryTimelinePageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    voice_input_icon_url: str
    plan_pill_label: str
    ai_status_message: str
    card_title: str
    segments: list[ItineraryTimelineSegmentDto]
    card_footer_summary: str
    page_footer_summary_parts: PageFooterSummaryParts


# ---------------------------------------------------------------------------
# Booking Todos
# ---------------------------------------------------------------------------


class BookingTodoItemDto(MobileModel):
    id: str
    kind: Literal["venue", "rides"]
    title: str
    subtitle: str | None = None
    lines: list[str] | None = None
    thumbnail_image_url: str | None = None
    status_label: str


class BookingTodoCardDto(MobileModel):
    title: str
    items: list[BookingTodoItemDto]
    footer_banner_text: str


class BookingFlowAiMessage(MobileModel):
    type: Literal["ai_message"] = "ai_message"
    id: str
    body: str


class BookingFlowUserPill(MobileModel):
    type: Literal["user_pill"] = "user_pill"
    id: str
    label: str


class BookingFlowProgressBanner(MobileModel):
    type: Literal["progress_banner"] = "progress_banner"
    id: str
    body: str


class BookingFlowTodoCard(MobileModel):
    type: Literal["todo_card"] = "todo_card"
    id: str
    card: BookingTodoCardDto


BookingFlowItemDto = Annotated[
    BookingFlowAiMessage | BookingFlowUserPill | BookingFlowProgressBanner | BookingFlowTodoCard,
    Field(discriminator="type"),
]


class BookingTodosPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    voice_input_icon_url: str
    flow: list[BookingFlowItemDto]


# ---------------------------------------------------------------------------
# Booking Checkout
# ---------------------------------------------------------------------------


class BookingVenueDetailRowDto(MobileModel):
    label: str
    value: str


class BookingVenueDetailCardDto(MobileModel):
    id: str
    title: str
    status_badge: str
    thumbnail_image_url: str | None = None
    rows: list[BookingVenueDetailRowDto]


class BookingRideLegDto(MobileModel):
    id: str
    leg_index: str
    category_label: str
    route: str
    distance_label: str
    duration_label: str
    fee_label: str
    handling_label: str


class BookingRideDetailCardDto(MobileModel):
    id: str
    title: str
    status_badge: str
    header_thumbnail_url: str | None = None
    legs: list[BookingRideLegDto]
    tip_text: str


class BookingCheckoutPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    voice_input_icon_url: str
    top_progress_text: str
    venue_cards: list[BookingVenueDetailCardDto]
    ride_card: BookingRideDetailCardDto
    payment_prompt_text: str


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


class PaymentLineItemDto(MobileModel):
    id: str
    item_label: str
    detail_text: str
    amount_text: str


class PaymentMethodOptionDto(MobileModel):
    id: str
    type: Literal["wechat", "alipay", "meituan"]
    badge_text: str
    label: str
    subtitle: str | None = None


class PaymentPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    voice_input_icon_url: str
    top_progress_text: str
    breakdown_title: str
    line_items: list[PaymentLineItemDto]
    payment_section_title: str
    amount_due_badge_label: str
    amount_due_value: str
    payment_methods: list[PaymentMethodOptionDto]
    default_selected_payment_method_id: str
    tap_to_pay_hint: str
    query_banner_text: str


# ---------------------------------------------------------------------------
# Trip Live Map
# ---------------------------------------------------------------------------


class TripLiveMapSnapshotCardDto(MobileModel):
    title: str
    timeline_text: str
    footer_left: str
    footer_emphasis: str


class TripLiveMapLocationCardDto(MobileModel):
    title: str
    current_line: str
    next_step_line: str


class TripLiveMapRemindersCardDto(MobileModel):
    title: str
    reminder_lines: list[str]


class TripLiveMapStopDto(MobileModel):
    id: str
    order: int
    title: str
    time: str
    status_text: str
    x_percent: float
    y_percent: float


class TripLiveMapPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    map_backdrop_image_url: str | None = None
    map_image_url: str
    map_corner_image_url: str | None = None
    map_stops: list[TripLiveMapStopDto]
    snapshot_card: TripLiveMapSnapshotCardDto
    location_card: TripLiveMapLocationCardDto
    reminders_card: TripLiveMapRemindersCardDto
    call_ride_button_label: str
    ai_bubble_text: str
    voice_input_icon_url: str


# ---------------------------------------------------------------------------
# Payment Confirmation
# ---------------------------------------------------------------------------


class PaymentConfirmRowDto(MobileModel):
    id: str
    item_label: str
    detail_text: str
    status_kind: Literal["pending_provider", "remind_later"]
    status_text: str


class PaymentConfirmRecommendedRowDto(MobileModel):
    id: str
    name: str
    audience_label: str
    price_text: str
    thumb_emoji: str | None = None


class PaymentConfirmTimelineChipDto(MobileModel):
    id: str
    time: str
    icon_emoji: str
    label: str


class PaymentConfirmHelpActionDto(MobileModel):
    id: str
    kind: Literal["share", "calendar", "bell"]
    label: str


class PaymentConfirmationPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    nav_title: str
    hero_title: str
    hero_subtitle: str
    hero_figure_image_url: str | None = None
    confirmation_section_title: str
    table_col_item: str
    table_col_detail: str
    table_col_status: str
    rows: list[PaymentConfirmRowDto]
    total_label: str
    total_value: str
    recommended_section_title: str
    recommended_rows: list[PaymentConfirmRecommendedRowDto]
    timeline_section_title: str
    timeline_chips: list[PaymentConfirmTimelineChipDto]
    help_section_title: str
    help_actions: list[PaymentConfirmHelpActionDto]
    help_summary_text: str
    voice_input_icon_url: str


# ---------------------------------------------------------------------------
# Itinerary Hub
# ---------------------------------------------------------------------------


class ItineraryHubTimelineNodeDto(MobileModel):
    id: str
    kind: Literal["done", "active", "upcoming"]
    time: str
    title: str
    subtitle: str | None = None
    icon_emoji: str


class ItineraryHubFlowChipDto(MobileModel):
    id: str
    icon_emoji: str
    label: str


class ItineraryHubQuickActionDto(MobileModel):
    id: str
    kind: Literal["map", "share", "calendar", "edit", "cancel"]
    label: str


class ItineraryHubHistoryItemDto(MobileModel):
    id: str
    thumb_image_url: str | None = None
    thumb_emoji: str | None = None
    plan_id: str | None = None
    date_line: str
    route_summary: str
    rating_stars: float
    price_text: str


class ItineraryHubPageDto(MobileModel):
    travel_id: str
    plan_id: str
    status_bar_image_url: str
    nav_title: str
    show_notifications_bell: bool
    overview_time_range: str
    overview_flow_chips: list[ItineraryHubFlowChipDto]
    overview_footer_line: str
    current_stage_title: str
    current_stage_status_badge: str
    timeline_nodes: list[ItineraryHubTimelineNodeDto]
    quick_actions: list[ItineraryHubQuickActionDto]
    history_section_title: str
    history_items: list[ItineraryHubHistoryItemDto]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class ProfileArchiveTagDto(MobileModel):
    id: str
    icon_emoji: str
    label: str


class CompanionProfileDto(MobileModel):
    companion_id: str
    display_name: str
    role_type: str
    role_label: str
    age: int | None = None
    avatar_emoji: str = "🙂"
    summary: str = ""
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)


class CompanionProfileListDto(MobileModel):
    status_bar_image_url: str
    nav_title: str = "同行人出行档案"
    subtitle: str = "这些人物记忆会在首页选择后参与推荐。"
    companions: list[CompanionProfileDto]


class CompanionProfileSaveBody(MobileModel):
    companion_id: str | None = None
    display_name: str
    role_type: str = "friend"
    age: int | None = Field(default=None, ge=0, le=120)
    avatar_emoji: str | None = None
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)


class CompanionProfileSaveResponseDto(MobileModel):
    ok: bool
    companion: CompanionProfileDto
    updated_at: str | None = None


class ProfilePreferenceRowDto(MobileModel):
    id: str
    kind: Literal["car", "food", "activity", "budget"]
    title: str
    summary: str


class ProfileMemoryRowDto(MobileModel):
    id: str
    kind: Literal["agent_weights", "last_feedback", "disliked_places"]
    label: str


class ProfileTravelTemplateDto(MobileModel):
    id: str
    title: str
    usage_badge: str
    thumb_emoji: str | None = None
    thumb_image_url: str | None = None


class ProfileQuickFooterActionDto(MobileModel):
    id: str
    kind: Literal["share", "rate", "help", "about", "settings"]
    label: str


class ProfilePageDto(MobileModel):
    status_bar_image_url: str
    nav_title: str
    show_notifications_bell: bool
    user_name: str
    avatar_image_url: str | None = None
    avatar_emoji: str | None = None
    default_start_line: str
    archive_section_title: str
    archive_edit_label: str
    archive_tags: list[ProfileArchiveTagDto]
    preference_section_title: str
    preference_edit_label: str
    preference_rows: list[ProfilePreferenceRowDto]
    memory_section_title: str
    memory_rows: list[ProfileMemoryRowDto]
    templates_section_title: str
    templates: list[ProfileTravelTemplateDto]
    quick_footer_actions: list[ProfileQuickFooterActionDto]


class LLMSettingsDto(MobileModel):
    status_bar_image_url: str
    nav_title: str = "设置"
    back_label: str = "返回"
    provider: str = "mock"
    model: str = ""
    base_url: str = ""
    api_key_configured: bool = False
    api_key_preview: str | None = None
    save_button_label: str = "保存设置"


class SaveLLMSettingsBody(MobileModel):
    provider: str = "openai"
    model: str
    base_url: str
    api_key: str | None = None


class TravelClarificationAnswerDto(MobileModel):
    question_id: str
    answer: str


class TravelClarificationAnswerBody(MobileModel):
    answers: list[TravelClarificationAnswerDto] = Field(default_factory=list)
    llm_config: LLMRuntimeConfigBody | None = None


class TravelRevisionBody(MobileModel):
    message: str
    target_plan_id: str | None = None
    locked_items: list[dict[str, Any]] = Field(default_factory=list)
    revision_mode: str = "partial"
    llm_config: LLMRuntimeConfigBody | None = None



# ---------------------------------------------------------------------------
# Travel Mode Settings
# ---------------------------------------------------------------------------


class TravelModeMethodOptionDto(MobileModel):
    id: Literal["taxi", "self_drive", "transit"]
    label: str


class TravelRadiusPresetDto(MobileModel):
    id: str
    label: str
    value_km: float


class TravelDurationOptionDto(MobileModel):
    id: str
    label: str


class TravelModeSettingsPageDto(MobileModel):
    status_bar_image_url: str
    nav_title: str
    back_label: str
    method_section_title: str
    method_options: list[TravelModeMethodOptionDto]
    selected_method_id: Literal["taxi", "self_drive", "transit"]
    radius_section_title: str
    radius_value_format: str
    radius_slider_min_km: float
    radius_slider_max_km: float
    radius_slider_step_km: float
    selected_radius_km: float
    radius_presets: list[TravelRadiusPresetDto]
    duration_section_title: str
    duration_options: list[TravelDurationOptionDto]
    selected_duration_id: str
    save_button_label: str


# ---------------------------------------------------------------------------
# Dietary Preferences
# ---------------------------------------------------------------------------


class DietaryNeedOptionDto(MobileModel):
    id: str
    label: str
    exclusive: bool = False
    expand_when_checked: bool = False


class DietaryFamilyMemberRowDto(MobileModel):
    id: str
    name: str
    summary_line: str
    avatar_emoji: str | None = None
    avatar_image_url: str | None = None


class DietaryPreferencesPageDto(MobileModel):
    status_bar_image_url: str
    nav_title: str
    nav_subtitle: str
    back_label: str
    special_needs_section_title: str
    need_options: list[DietaryNeedOptionDto]
    selected_need_ids: list[str]
    family_section_title: str
    family_members: list[DietaryFamilyMemberRowDto]
    save_button_label: str


# ---------------------------------------------------------------------------
# Activity Preferences
# ---------------------------------------------------------------------------


class ActivityTagOptionDto(MobileModel):
    id: str
    label: str


class ActivityPreferencesPageDto(MobileModel):
    status_bar_image_url: str
    nav_title: str
    nav_subtitle: str | None = None
    back_label: str
    tags_section_title: str
    tag_options: list[ActivityTagOptionDto]
    selected_tag_ids: list[str]
    family_section_title: str
    family_members: list[DietaryFamilyMemberRowDto]
    save_button_label: str


# ---------------------------------------------------------------------------
# Budget & Pace Preferences
# ---------------------------------------------------------------------------


class BudgetPaceRadioOptionDto(MobileModel):
    id: str
    title: str
    description: str


class BudgetPacePreferencesPageDto(MobileModel):
    status_bar_image_url: str
    nav_title: str
    back_label: str
    budget_section_title: str
    budget_options: list[BudgetPaceRadioOptionDto]
    selected_budget_id: str
    pace_section_title: str
    pace_options: list[BudgetPaceRadioOptionDto]
    selected_pace_id: str
    save_button_label: str


# ---------------------------------------------------------------------------
# Write operation responses
# ---------------------------------------------------------------------------


class UserPreferenceSaveResponseDto(MobileModel):
    ok: bool
    updated_at: str | None = None


class BookingTodoActionResponseDto(MobileModel):
    ok: bool
    booking_todos_page_url: str | None = None
    status: str | None = None
    code: str | None = None
    message: str | None = None


class TravelPaymentSubmitResponseDto(MobileModel):
    ok: bool
    order_id: str | None = None
    payment_url: str | None = None
    status: str | None = None
    code: str | None = None
    message: str | None = None


class TravelSimpleOkResponseDto(MobileModel):
    ok: bool
    status: str | None = None
    code: str | None = None
    message: str | None = None


class MobileExecutionTaskDto(MobileModel):
    task_id: str
    action: str
    status: str
    poi_id: str | None = None
    human_readable_confirmation: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class MobilePlanActionResponseDto(MobileModel):
    ok: bool
    travel_id: str
    state: str
    message: str | None = None
    tasks: list[MobileExecutionTaskDto] = Field(default_factory=list)
    feedback_id: str | None = None


# ---------------------------------------------------------------------------
# Revision wrapper (for POST /mobile/travel/{id}/revise)
# ---------------------------------------------------------------------------


class PlanPatchDto(MobileModel):
    patch_id: str
    patch_type: str
    target_plan_id: str | None = None
    target_stage_id: str | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    reason: str


class MobileRevisionResponse(MobileModel):
    travel_id: str
    revision_summary: str
    plan_page: TravelConversationPageDto
    patches: list[PlanPatchDto] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    updated_plan_comparison: PlanComparisonPageDto | None = None
    updated_timeline: ItineraryTimelinePageDto | None = None
    updated_booking_todos: BookingTodosPageDto | None = None
    updated_booking_checkout: BookingCheckoutPageDto | None = None
    updated_payment: PaymentPageDto | None = None
    updated_payment_confirmation: PaymentConfirmationPageDto | None = None
    updated_trip_live_map: TripLiveMapPageDto | None = None
    updated_itinerary_hub: ItineraryHubPageDto | None = None
