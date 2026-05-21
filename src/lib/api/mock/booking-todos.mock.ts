import type { BookingTodosPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** Mock 示意：晴天牧场/奶牛（避免深色夜景裁切）（接真实接口后由后端 URL 替换） */
const MOCK_THUMB_OUTDOOR_FARM =
  "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&w=256&h=256&fit=crop&q=80";

/** Mock 示意：花园/晚餐餐厅氛围（接真实接口后由后端 URL 替换） */
const MOCK_THUMB_GARDEN_DINING =
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=256&h=256&fit=crop&q=80";

export const MOCK_BOOKING_TODOS_PAGE: Omit<BookingTodosPageDto, "travelId" | "planId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
  flow: [
    {
      type: "ai_message",
      id: "m1",
      body: "已生成Plan A 的详细时间轴＆路线",
    },
    {
      type: "ai_message",
      id: "m2",
      body: "需要帮您把行程预定好吗？",
    },
    { type: "user_pill", id: "u1", label: "需要" },
    {
      type: "progress_banner",
      id: "p1",
      body: "正在生成预约信息…",
    },
    {
      type: "todo_card",
      id: "td1",
      card: {
        title: "待办事项",
        items: [
          {
            id: "farm",
            kind: "venue",
            title: "户外亲子农场",
            subtitle: "14:45 体验亲子互动，孩子尽情放电",
            thumbnailImageUrl: MOCK_THUMB_OUTDOOR_FARM,
            statusLabel: "待预约",
          },
          {
            id: "garden",
            kind: "venue",
            title: "素然花园",
            subtitle: "17:00 精致健康晚餐，已预约靠窗位",
            thumbnailImageUrl: MOCK_THUMB_GARDEN_DINING,
            statusLabel: "待预约",
          },
          {
            id: "rides",
            kind: "rides",
            title: "叫车安排",
            lines: [
              "① 家 → 亲子农场（现在约）",
              "② 农场 → 素然花园（到时提醒）",
              "③ 滨江绿道 → 家（到时提醒）",
            ],
            statusLabel: "待预约",
          },
        ],
        footerBannerText: "待预约",
      },
    },
    {
      type: "ai_message",
      id: "m3",
      body: "请查看预约信息，是否确认预约",
    },
    { type: "user_pill", id: "u2", label: "确认" },
  ],
};
