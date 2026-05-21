import type { ItineraryHubPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_ITINERARY_HUB_PAGE: Omit<ItineraryHubPageDto, "travelId" | "planId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "行程",
  showNotificationsBell: true,
  overviewTimeRange: "今天下午 14:30 — 18:55",
  overviewFlowChips: [
    { id: "f1", iconEmoji: "🎯", label: "农场" },
    { id: "f2", iconEmoji: "🍽️", label: "晚餐" },
    { id: "f3", iconEmoji: "🌿", label: "散步" },
  ],
  overviewFooterLine: "约 4 小时 · 已付 ¥183",
  currentStageTitle: "当前阶段",
  currentStageStatusBadge: "进行中",
  timelineNodes: [
    {
      id: "t1",
      kind: "done",
      time: "14:30",
      title: "已出发 / 叫车完成",
      iconEmoji: "🚗",
    },
    {
      id: "t2",
      kind: "done",
      time: "14:45",
      title: "户外亲子农场 · 已入场",
      iconEmoji: "🎯",
    },
    {
      id: "t3",
      kind: "active",
      time: "16:15",
      title: "转场去素然花园",
      subtitle: "16:05 提醒叫车",
      iconEmoji: "🚕",
    },
    {
      id: "t4",
      kind: "upcoming",
      time: "17:00",
      title: "素然花园 · 晚餐订位",
      iconEmoji: "🍽️",
    },
    {
      id: "t5",
      kind: "upcoming",
      time: "18:10",
      title: "滨江绿道散步",
      iconEmoji: "🌿",
    },
    {
      id: "t6",
      kind: "upcoming",
      time: "18:40",
      title: "返程回家",
      iconEmoji: "🏠",
    },
  ],
  quickActions: [
    { id: "q1", kind: "map", label: "地图" },
    { id: "q2", kind: "share", label: "分享" },
    { id: "q3", kind: "calendar", label: "日历" },
    { id: "q4", kind: "edit", label: "编辑" },
    { id: "q5", kind: "cancel", label: "取消" },
  ],
  historySectionTitle: "历史行程",
  historyItems: [
    {
      id: "h1",
      thumbEmoji: "🌾",
      dateLine: "6 月 1 日",
      routeSummary: "亲子农场 · 半日游",
      ratingStars: 4,
      priceText: "¥156",
    },
    {
      id: "h2",
      thumbEmoji: "🌸",
      dateLine: "5 月 20 日",
      routeSummary: "滨江骑行 · 下午茶",
      ratingStars: 5,
      priceText: "¥98",
    },
  ],
};
