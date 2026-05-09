import type { TripLiveMapPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** 以下资源与 Figma「第八屏」node 1:734 导出一致（MCP asset，约 7 天有效；后端可换持久 CDN） */
const FIGMA_MAP_BACKDROP =
  "https://www.figma.com/api/mcp/asset/f0839aab-b9ae-4b72-9fce-88fbae753e9c";
const FIGMA_MAP_ROUTE =
  "https://www.figma.com/api/mcp/asset/ffc7f232-b731-4680-ba85-ff94f7a3f1d4";
const FIGMA_MAP_CORNER =
  "https://www.figma.com/api/mcp/asset/9aa8ed5c-6733-491e-a7bc-729a769ad169";

export const MOCK_TRIP_LIVE_MAP_PAGE: Omit<TripLiveMapPageDto, "travelId" | "planId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  mapBackdropImageUrl: FIGMA_MAP_BACKDROP,
  mapImageUrl: FIGMA_MAP_ROUTE,
  mapCornerImageUrl: FIGMA_MAP_CORNER,
  snapshotCard: {
    title: "行程快照",
    timelineText: "14:30 🚗 出发 → 14:45 🎯 农场 → 17:00 🍽️ 晚餐 → 18:10 🌿 散步",
    footerLeft: "全程约 4 小时",
    footerEmphasis: "已支付 ¥183",
  },
  locationCard: {
    title: "当前位置与下一站",
    currentLine: "当前：📍 户外亲子农场 · 剩余 45 分钟",
    nextStepLine: "下一步：🕒 16:15 叫车前往素然花园",
  },
  remindersCard: {
    title: "内置提醒",
    reminderLines: ["🔔 16:05 提醒你叫车去餐厅", "🔔 18:35 提醒叫车回家"],
  },
  callRideButtonLabel: "叫车",
  aiBubbleText: "请查看预约信息，是否确认预约",
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
};
