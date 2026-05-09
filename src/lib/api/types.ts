/** 与后端的契约类型；mock 与真实接口应返回同一结构 */

export type HomeSceneVariant = "couple" | "friends" | "family";

export type HomeSceneCardDto = {
  id: string;
  variant: HomeSceneVariant;
  title: string;
  subtitle: string;
  tag: string;
};

export type HomeHistoryItemDto = {
  id: string;
  title: string;
  metaLine: string;
};

/** GET /api/home/dashboard（建议路径，可与后端协商） */
export type HomeDashboardDto = {
  greetingLines: [string, string];
  mascotImageUrl: string;
  statusBarImageUrl: string;
  voiceInputIconUrl: string;
  sceneSectionTitle: string;
  scenes: HomeSceneCardDto[];
  filterTags: string[];
  historySectionTitle: string;
  history: HomeHistoryItemDto[];
};

export type StartTravelSessionBody = {
  message: string;
  userId?: string;
};

/** POST /api/travel/sessions（建议：用户从首页发送第一条消息时创建行程） */
export type StartTravelSessionResponse = {
  travelId: string;
};

export type TravelStatusIconKey = "loader" | "alert" | "arrows" | "lightbulb";

export type TravelStatusStepDto = {
  id: string;
  text: string;
  icon: TravelStatusIconKey;
};

export type ClarificationOptionDto = {
  id: string;
  label: string;
};

export type ClarificationFieldKind = "chips" | "supplementary";

export type ClarificationFieldDto = {
  id: string;
  kind: ClarificationFieldKind;
  question: string;
  options?: ClarificationOptionDto[];
  /** supplementary 类型的按钮文案占位 */
  placeholder?: string;
};

/** 「想确认一下」整块由后端驱动 */
export type ClarificationCardDto = {
  title: string;
  skipLabel: string;
  fields: ClarificationFieldDto[];
};

export type ParticipantNeedCardDto = {
  id: string;
  title: string;
  icon: string;
  description: string[];
};

export type NeedsSectionDto = {
  headerTitle: string;
  cards: ParticipantNeedCardDto[];
};

/** GET /api/travel/:travelId/conversation-page（建议：对话页一次拉齐状态条+澄清+需求） */
export type TravelConversationPageDto = {
  travelId: string;
  statusSteps: TravelStatusStepDto[];
  clarification: ClarificationCardDto;
  needsSection: NeedsSectionDto;
};

export type PlanActivityTagDto = {
  id: string;
  label: string;
};

export type PlanActivityDto = {
  id: string;
  title: string;
  durationLabel: string;
  tags: PlanActivityTagDto[];
};

/** 0–5 颗实心星（前端只负责展示，规则可由后端算好） */
export type PlanMemberRatingDto = {
  id: string;
  label: string;
  emoji: string;
  score: number;
  starsFilled: number;
};

export type TravelPlanCardDto = {
  id: string;
  /** 如 "Plan A" */
  planLabel: string;
  /** 副标题，如 "午后平衡 · 推荐" */
  headline: string;
  recommended?: boolean;
  /** 右上角综合分文案，如 "综合3.62" */
  overallScoreLabel: string;
  activities: PlanActivityDto[];
  memberRatings: PlanMemberRatingDto[];
  compensationTitle?: string;
  compensationParagraphs?: string[];
};

/** GET /api/travel/:travelId/plan-comparison（建议：双方案对比页） */
export type PlanComparisonPageDto = {
  travelId: string;
  statusBarImageUrl: string;
  topStatusText: string;
  plans: TravelPlanCardDto[];
  assistantMessage: string;
  voiceInputIconUrl: string;
};

/** 右侧交通/活动类型展示 */
export type ItineraryTransportDto = {
  emoji: string;
  label: string;
};

/** 时间轴卡片内一行；可选 `transport` 时右侧显示 emoji + 标签（如 打车 / 用餐） */
export type ItineraryTimelineSegmentDto = {
  id: string;
  /** 左侧时间列上行，如 14:30、14:45-16:15 */
  scheduleLabel: string;
  /** 左侧时间列下行，如 出发、90 分钟、返程 */
  scheduleNote?: string;
  title: string;
  /** #626262 小号说明，可多条 */
  metaLines: string[];
  detailLines?: string[];
  transport?: ItineraryTransportDto;
};

/** GET /api/travel/:travelId/itinerary-timeline?planId=（第四屏 · 时间轴＆路线） */
export type ItineraryTimelinePageDto = {
  travelId: string;
  /** 与双方案卡片 id 对齐，如 plan-a */
  planId: string;
  statusBarImageUrl: string;
  voiceInputIconUrl: string;
  /** 右上角黄底标签，如 Plan A */
  planPillLabel: string;
  /** 顶部白色折叠条文案 */
  aiStatusMessage: string;
  /** 大卡片标题，如 时间轴＆路线… */
  cardTitle: string;
  segments: ItineraryTimelineSegmentDto[];
  /** 卡片内底部黄条总结 */
  cardFooterSummary: string;
  /** 卡片下方：前半句渐变强调 + 后半句灰色补充 */
  pageFooterSummaryParts: { highlight: string; rest: string };
};

/** 待办卡片中的一条（景点 / 叫车分组） */
export type BookingTodoItemDto = {
  id: string;
  kind: "venue" | "rides";
  title: string;
  /** kind=venue 时副标题 */
  subtitle?: string;
  /** kind=rides 时枚举行 */
  lines?: string[];
  thumbnailImageUrl?: string;
  /** 右侧状态角标，如 待预约 */
  statusLabel: string;
};

export type BookingTodoCardDto = {
  /** 卡片标题，如 待办事项 */
  title: string;
  items: BookingTodoItemDto[];
  /** 卡片底部黄条内主文案 */
  footerBannerText: string;
};

/**
 * 第五屏预约流：AI 气泡、用户黄按钮、进度条、待办卡片
 * GET /api/travel/:travelId/booking-todos?planId=
 */
export type BookingFlowItemDto =
  | { type: "ai_message"; id: string; body: string }
  | { type: "user_pill"; id: string; label: string }
  | { type: "progress_banner"; id: string; body: string }
  | { type: "todo_card"; id: string; card: BookingTodoCardDto };

/** GET /api/travel/:travelId/booking-todos?planId=（第五屏 · 行程预约与待办） */
export type BookingTodosPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  voiceInputIconUrl: string;
  /** 按顺序渲染整块预约对话流 */
  flow: BookingFlowItemDto[];
};

/** 第六屏 · 场馆预约卡片一行 */
export type BookingVenueDetailRowDto = {
  label: string;
  value: string;
};

export type BookingVenueDetailCardDto = {
  id: string;
  title: string;
  statusBadge: string;
  thumbnailImageUrl: string;
  rows: BookingVenueDetailRowDto[];
};

/** 叫车表格一行 */
export type BookingRideLegDto = {
  id: string;
  /** 如 ① */
  legIndex: string;
  /** 表头「时间 / 人数 / 门票」列在该行的文案 */
  categoryLabel: string;
  route: string;
  distanceLabel: string;
  durationLabel: string;
  feeLabel: string;
  handlingLabel: string;
};

export type BookingRideDetailCardDto = {
  id: string;
  title: string;
  statusBadge: string;
  /** 卡片标题旁小图，可选 */
  headerThumbnailUrl?: string;
  legs: BookingRideLegDto[];
  /** 底部黄条说明 */
  tipText: string;
};

/** GET /api/travel/:travelId/booking-checkout?planId=（第六屏 · 预约详情与支付） */
export type BookingCheckoutPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  voiceInputIconUrl: string;
  /** 顶部进度条，如 正在进行预约… */
  topProgressText: string;
  venueCards: BookingVenueDetailCardDto[];
  rideCard: BookingRideDetailCardDto;
  /** 底部 AI 气泡，如 是否确认支付 */
  paymentPromptText: string;
};

/** 付款明细表一行（第七屏 · 费用明细） */
export type PaymentLineItemDto = {
  id: string;
  /** 项目列，如场馆或「第一段叫车」 */
  itemLabel: string;
  /** 详情列 */
  detailText: string;
  /** 金额列，如 ¥98.00 或 到时支付 */
  amountText: string;
};

export type PaymentMethodType = "wechat" | "alipay" | "meituan";

export type PaymentMethodOptionDto = {
  id: string;
  type: PaymentMethodType;
  /** 角标内短字，如 微 / 支 / 美 */
  badgeText: string;
  label: string;
  subtitle?: string;
};

/** GET /api/travel/:travelId/payment?planId=（第七屏 · 付款方式与明细） */
export type PaymentPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  voiceInputIconUrl: string;
  /** 顶部条文案，如 正在生成付款… */
  topProgressText: string;
  breakdownTitle: string;
  lineItems: PaymentLineItemDto[];
  paymentSectionTitle: string;
  /** 付款方式卡片右上角徽标，如 本次需支付 */
  amountDueBadgeLabel: string;
  /** 如 ¥168 */
  amountDueValue: string;
  paymentMethods: PaymentMethodOptionDto[];
  defaultSelectedPaymentMethodId: string;
  /** 如 请点击支付 */
  tapToPayHint: string;
  /** 底部灰色提示条，如 支付查询中… */
  queryBannerText: string;
};

/** 第八屏 · 行程快照卡片 */
export type TripLiveMapSnapshotCardDto = {
  title: string;
  /** 一行时间轴文案，可含 emoji */
  timelineText: string;
  /** 如 全程约 4 小时 */
  footerLeft: string;
  /** 如 已支付 ¥183（展示为加粗） */
  footerEmphasis: string;
};

/** 第八屏 · 当前位置与下一站 */
export type TripLiveMapLocationCardDto = {
  title: string;
  currentLine: string;
  /** 写入底部浅色小标签内，如 下一步：🕒 16:15 叫车… */
  nextStepLine: string;
};

/** 第八屏 · 内置提醒 */
export type TripLiveMapRemindersCardDto = {
  title: string;
  reminderLines: string[];
};

/** GET /api/travel/:travelId/trip-live-map?planId=（第八屏 · 行程中与地图） */
export type TripLiveMapPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  /** 地图上层氛围/远景（Figma image 722，可选） */
  mapBackdropImageUrl?: string;
  /** 主路线地图（Figma image 723） */
  mapImageUrl: string;
  /** 地图内右上角控件（Figma image 724，可选） */
  mapCornerImageUrl?: string;
  snapshotCard: TripLiveMapSnapshotCardDto;
  locationCard: TripLiveMapLocationCardDto;
  remindersCard: TripLiveMapRemindersCardDto;
  /** 地图右下角「叫车」按钮文案 */
  callRideButtonLabel: string;
  /** 底部 AI 灰气泡 */
  aiBubbleText: string;
  voiceInputIconUrl: string;
};

/** 第九屏 · 预订确认单行状态 */
export type PaymentConfirmRowStatusKind = "paid" | "reserved" | "remind_later";

/** 第九屏 · 预订确认表一行 */
export type PaymentConfirmRowDto = {
  id: string;
  itemLabel: string;
  detailText: string;
  statusKind: PaymentConfirmRowStatusKind;
  statusText: string;
};

/** 第九屏 · 推荐套餐一行 */
export type PaymentConfirmRecommendedRowDto = {
  id: string;
  name: string;
  audienceLabel: string;
  priceText: string;
  thumbEmoji?: string;
};

/** 第九屏 · 横向行程节点 */
export type PaymentConfirmTimelineChipDto = {
  id: string;
  time: string;
  iconEmoji: string;
  label: string;
};

/** 第九屏 · 「还能帮你」操作 */
export type PaymentConfirmHelpActionDto = {
  id: string;
  kind: "share" | "calendar" | "bell";
  label: string;
};

/** GET /api/travel/:travelId/payment-confirmation?planId=（第九屏 · 支付成功与确认单） */
export type PaymentConfirmationPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  navTitle: string;
  heroTitle: string;
  heroSubtitle: string;
  heroFigureImageUrl?: string;
  confirmationSectionTitle: string;
  tableColItem: string;
  tableColDetail: string;
  tableColStatus: string;
  rows: PaymentConfirmRowDto[];
  totalLabel: string;
  totalValue: string;
  recommendedSectionTitle: string;
  recommendedRows: PaymentConfirmRecommendedRowDto[];
  timelineSectionTitle: string;
  timelineChips: PaymentConfirmTimelineChipDto[];
  helpSectionTitle: string;
  helpActions: PaymentConfirmHelpActionDto[];
  helpSummaryText: string;
  voiceInputIconUrl: string;
};

/** 第十屏 · 行程总览时间轴节点 */
export type ItineraryHubTimelineNodeKind = "done" | "active" | "upcoming";

export type ItineraryHubTimelineNodeDto = {
  id: string;
  kind: ItineraryHubTimelineNodeKind;
  time: string;
  title: string;
  /** 附注，如「16:05 提醒叫车」 */
  subtitle?: string;
  iconEmoji: string;
};

/** 第十屏 · 顶部行程摘要一步 */
export type ItineraryHubFlowChipDto = {
  id: string;
  iconEmoji: string;
  label: string;
};

/** 第十屏 · 快捷操作 */
export type ItineraryHubQuickActionKind = "map" | "share" | "calendar" | "edit" | "cancel";

export type ItineraryHubQuickActionDto = {
  id: string;
  kind: ItineraryHubQuickActionKind;
  label: string;
};

/** 第十屏 · 历史行程卡片 */
export type ItineraryHubHistoryItemDto = {
  id: string;
  /** 列表缩略图，可与 thumbEmoji 二选一 */
  thumbImageUrl?: string;
  thumbEmoji?: string;
  dateLine: string;
  routeSummary: string;
  ratingStars: number;
  priceText: string;
};

/** GET /api/travel/:travelId/itinerary-hub?planId=（第十屏 · 行程主页） */
export type ItineraryHubPageDto = {
  travelId: string;
  planId: string;
  statusBarImageUrl: string;
  navTitle: string;
  /** 顶栏右侧是否显示通知铃（后端可扩展 href） */
  showNotificationsBell: boolean;
  overviewTimeRange: string;
  overviewFlowChips: ItineraryHubFlowChipDto[];
  overviewFooterLine: string;
  currentStageTitle: string;
  currentStageStatusBadge: string;
  timelineNodes: ItineraryHubTimelineNodeDto[];
  quickActions: ItineraryHubQuickActionDto[];
  historySectionTitle: string;
  historyItems: ItineraryHubHistoryItemDto[];
};

/** 第十一屏 · 出行档案标签 */
export type ProfileArchiveTagDto = {
  id: string;
  iconEmoji: string;
  label: string;
};

/** 第十一屏 · 出行偏好行 kind 仅用于前端图标映射 */
export type ProfilePreferenceRowKind = "car" | "food" | "activity" | "budget";

export type ProfilePreferenceRowDto = {
  id: string;
  kind: ProfilePreferenceRowKind;
  title: string;
  summary: string;
};

/** 第十一屏 · 记忆与偏好行 */
export type ProfileMemoryRowKind = "agent_weights" | "last_feedback" | "disliked_places";

export type ProfileMemoryRowDto = {
  id: string;
  kind: ProfileMemoryRowKind;
  label: string;
};

/** 第十一屏 · 常用模板 */
export type ProfileTravelTemplateDto = {
  id: string;
  title: string;
  usageBadge: string;
  thumbEmoji?: string;
  thumbImageUrl?: string;
};

/** 第十一屏 · 底栏快捷入口 */
export type ProfileQuickFooterActionKind = "share" | "rate" | "help" | "about";

export type ProfileQuickFooterActionDto = {
  id: string;
  kind: ProfileQuickFooterActionKind;
  label: string;
};

/** GET /api/user/profile（第十一屏 · 我的） */
export type ProfilePageDto = {
  statusBarImageUrl: string;
  navTitle: string;
  showNotificationsBell: boolean;
  userName: string;
  avatarImageUrl?: string;
  avatarEmoji?: string;
  defaultStartLine: string;
  archiveSectionTitle: string;
  archiveEditLabel: string;
  archiveTags: ProfileArchiveTagDto[];
  preferenceSectionTitle: string;
  preferenceEditLabel: string;
  preferenceRows: ProfilePreferenceRowDto[];
  memorySectionTitle: string;
  memoryRows: ProfileMemoryRowDto[];
  templatesSectionTitle: string;
  templates: ProfileTravelTemplateDto[];
  quickFooterActions: ProfileQuickFooterActionDto[];
};

/** 第十二屏 · 默认出行方式 */
export type TravelModeMethodOptionId = "taxi" | "self_drive" | "transit";

export type TravelModeMethodOptionDto = {
  id: TravelModeMethodOptionId;
  label: string;
};

export type TravelRadiusPresetDto = {
  id: string;
  label: string;
  valueKm: number;
};

export type TravelDurationOptionDto = {
  id: string;
  label: string;
};

/** GET /api/user/preferences/travel-mode（第十二屏 · 出行方式与距离） */
export type TravelModeSettingsPageDto = {
  statusBarImageUrl: string;
  navTitle: string;
  backLabel: string;
  methodSectionTitle: string;
  methodOptions: TravelModeMethodOptionDto[];
  selectedMethodId: TravelModeMethodOptionId;
  radiusSectionTitle: string;
  /** 展示半径，可含占位 `{km}`，如 `{km}km内` */
  radiusValueFormat: string;
  radiusSliderMinKm: number;
  radiusSliderMaxKm: number;
  radiusSliderStepKm: number;
  selectedRadiusKm: number;
  radiusPresets: TravelRadiusPresetDto[];
  durationSectionTitle: string;
  durationOptions: TravelDurationOptionDto[];
  selectedDurationId: string;
  saveButtonLabel: string;
};

/** 第十三屏 · 特殊饮食需求选项 */
export type DietaryNeedOptionDto = {
  id: string;
  label: string;
  /** 勾选时仅保留该项，与「无特殊」互斥 */
  exclusive?: boolean;
  /** 为 true 时前端可展示「展开填写」子区域（如过敏源） */
  expandWhenChecked?: boolean;
};

/** 第十三屏 · 人物偏好列表行 */
export type DietaryFamilyMemberRowDto = {
  id: string;
  name: string;
  /** 完整说明行，可含「偏好：」「约束：」等前缀 */
  summaryLine: string;
  avatarEmoji?: string;
  avatarImageUrl?: string;
};

/** GET /api/user/preferences/dietary（第十三屏 · 饮食偏好） */
export type DietaryPreferencesPageDto = {
  statusBarImageUrl: string;
  navTitle: string;
  navSubtitle: string;
  backLabel: string;
  specialNeedsSectionTitle: string;
  needOptions: DietaryNeedOptionDto[];
  /** 多选已勾选 id */
  selectedNeedIds: string[];
  familySectionTitle: string;
  familyMembers: DietaryFamilyMemberRowDto[];
  saveButtonLabel: string;
};

/** 第十四屏 · 活动类型标签 */
export type ActivityTagOptionDto = {
  id: string;
  label: string;
};

/** GET /api/user/preferences/activity（第十四屏 · 活动偏好，Figma 1:1301） */
export type ActivityPreferencesPageDto = {
  statusBarImageUrl: string;
  navTitle: string;
  /** 设计稿无副标题时可省略 */
  navSubtitle?: string;
  backLabel: string;
  tagsSectionTitle: string;
  tagOptions: ActivityTagOptionDto[];
  selectedTagIds: string[];
  /** 如「添加人物偏好」 */
  familySectionTitle: string;
  familyMembers: DietaryFamilyMemberRowDto[];
  saveButtonLabel: string;
};

/** 第十五屏 · 预算/节奏单选项（标题 + 说明文案） */
export type BudgetPaceRadioOptionDto = {
  id: string;
  title: string;
  description: string;
};

/** GET /api/user/preferences/budget-pace（第十五屏 · 预算与节奏，Figma 1:1302） */
export type BudgetPacePreferencesPageDto = {
  statusBarImageUrl: string;
  navTitle: string;
  backLabel: string;
  budgetSectionTitle: string;
  budgetOptions: BudgetPaceRadioOptionDto[];
  selectedBudgetId: string;
  paceSectionTitle: string;
  paceOptions: BudgetPaceRadioOptionDto[];
  selectedPaceId: string;
  saveButtonLabel: string;
};
