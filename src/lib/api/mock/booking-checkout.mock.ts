import type { BookingCheckoutPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** 与第五页 mock 一致，晴天牧场 */
const MOCK_THUMB_FARM =
  "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&w=400&h=300&fit=crop&q=80";

/** 与第五页 mock 一致，晚餐/餐厅氛围 */
const MOCK_THUMB_GARDEN =
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&w=400&h=300&fit=crop&q=80";

export const MOCK_BOOKING_CHECKOUT_PAGE: Omit<BookingCheckoutPageDto, "travelId" | "planId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
  topProgressText: "正在进行预约…",
  venueCards: [
    {
      id: "farm",
      title: "户外亲子农场",
      statusBadge: "已预约 · 待支付",
      thumbnailImageUrl: MOCK_THUMB_FARM,
      rows: [
        { label: "日期", value: "今天" },
        { label: "时间", value: "14:45" },
        { label: "人数", value: "3人" },
        { label: "门票", value: "3人 × ¥56 ＝ ¥168" },
      ],
    },
    {
      id: "garden",
      title: "素然花园",
      statusBadge: "已预约 · 待支付",
      thumbnailImageUrl: MOCK_THUMB_GARDEN,
      rows: [
        { label: "日期", value: "今天" },
        { label: "时间", value: "17:00" },
        { label: "人数", value: "3人" },
        { label: "位置", value: "靠窗5号（傍晚观景更佳）" },
      ],
    },
  ],
  rideCard: {
    id: "rides",
    title: "叫车安排",
    statusBadge: "已安排 · 待支付",
    legs: [
      {
        id: "l1",
        legIndex: "①",
        categoryLabel: "时间",
        route: "家 → 亲子农场",
        distanceLabel: "3km",
        durationLabel: "12-17min",
        feeLabel: "¥15",
        handlingLabel: "现在约好",
      },
      {
        id: "l2",
        legIndex: "②",
        categoryLabel: "人数",
        route: "亲子农场 → 素然花园",
        distanceLabel: "1.5km",
        durationLabel: "8-15min",
        feeLabel: "¥10",
        handlingLabel: "提醒叫车",
      },
      {
        id: "l3",
        legIndex: "③",
        categoryLabel: "门票",
        route: "滨江绿道 → 家",
        distanceLabel: "3km",
        durationLabel: "15-20min",
        feeLabel: "¥15",
        handlingLabel: "提醒叫车",
      },
    ],
    tipText:
      "后面两段不用现在确定，到时候提醒您一键叫车，第一段先帮您约好，14:30准时出发。",
  },
  paymentPromptText: "是否确认支付",
};
