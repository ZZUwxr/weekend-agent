import type { PaymentConfirmationPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** 第九屏 · 支付成功与预订确认（Figma node 1:1303 文案对齐） */
export const MOCK_PAYMENT_CONFIRMATION_PAGE: Omit<
  PaymentConfirmationPageDto,
  "travelId" | "planId"
> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "确认付款信息",
  heroTitle: "支付成功!",
  heroSubtitle: "下午的行程已全部就绪 ✨",
  confirmationSectionTitle: "预订确认单",
  tableColItem: "项目",
  tableColDetail: "详情",
  tableColStatus: "状态",
  rows: [
    {
      id: "r-farm",
      itemLabel: "户外亲子农场",
      detailText: "今天 14:45 · 3 人 · ¥168",
      statusKind: "paid",
      statusText: "已支付",
    },
    {
      id: "r-garden",
      itemLabel: "素然花园",
      detailText: "今天 17:00 · 3 人 · 靠窗",
      statusKind: "reserved",
      statusText: "已预约",
    },
    {
      id: "r-ride1",
      itemLabel: "第一段叫车",
      detailText: "14:30 家 → 户外亲子农场 · ¥15",
      statusKind: "paid",
      statusText: "已支付",
    },
    {
      id: "r-ride2",
      itemLabel: "第二段叫车",
      detailText: "农场 → 素然花园 · 约 ¥10",
      statusKind: "remind_later",
      statusText: "到时提醒",
    },
    {
      id: "r-ride3",
      itemLabel: "第三段叫车",
      detailText: "滨江 → 家 · 约 ¥15",
      statusKind: "remind_later",
      statusText: "到时提醒",
    },
  ],
  totalLabel: "合计已支付",
  totalValue: "¥183",
  recommendedSectionTitle: "素然花园 · 推荐套餐（到店扫美团码享优惠）",
  recommendedRows: [
    {
      id: "rec-1",
      name: "花园双人下午茶",
      audienceLabel: "妻子",
      priceText: "¥88",
      thumbEmoji: "🍰",
    },
    {
      id: "rec-2",
      name: "儿童农场体验加购",
      audienceLabel: "孩子",
      priceText: "¥39",
      thumbEmoji: "🐑",
    },
  ],
  timelineSectionTitle: "行程速览",
  timelineChips: [
    { id: "t1", time: "14:30", iconEmoji: "🚗", label: "出发" },
    { id: "t2", time: "14:45", iconEmoji: "🎯", label: "农场" },
    { id: "t3", time: "17:00", iconEmoji: "🍽️", label: "晚餐" },
    { id: "t4", time: "18:10", iconEmoji: "🌿", label: "散步" },
    { id: "t5", time: "18:40", iconEmoji: "🚗", label: "回家" },
  ],
  helpSectionTitle: "还能帮你",
  helpActions: [
    { id: "h1", kind: "share", label: "分享给家人" },
    { id: "h2", kind: "calendar", label: "加入日历" },
    { id: "h3", kind: "bell", label: "订阅行前提醒" },
  ],
  helpSummaryText: "行前 30 分钟会提醒叫车；到店后可在「我的订单」里查看核销码。",
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
};
