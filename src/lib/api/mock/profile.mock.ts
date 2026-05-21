import type { ProfilePageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_PROFILE_PAGE: ProfilePageDto = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "我的",
  showNotificationsBell: true,
  userName: "小明",
  avatarEmoji: "👨‍💻",
  defaultStartLine: "默认起点：家（科技生活区）",
  archiveSectionTitle: "我的出行档案",
  archiveEditLabel: "编辑",
  archiveTags: [
    { id: "a1", iconEmoji: "👶", label: "儿子 · 5岁" },
    { id: "a2", iconEmoji: "💗", label: "老婆 · 减肥期" },
    { id: "a3", iconEmoji: "🙋", label: "我" },
  ],
  preferenceSectionTitle: "出行偏好",
  preferenceEditLabel: "编辑",
  preferenceRows: [
    {
      id: "p1",
      kind: "car",
      title: "出行方式与距离",
      summary: "打车 · 5km内 · 3–4小时",
    },
    {
      id: "p2",
      kind: "food",
      title: "饮食偏好",
      summary: "需低卡 · 需儿童餐",
    },
    {
      id: "p3",
      kind: "activity",
      title: "活动偏好",
      summary: "户外自然 · 互动体验",
    },
    {
      id: "p4",
      kind: "budget",
      title: "预算与节奏",
      summary: "中等 · 放松型",
    },
  ],
  memorySectionTitle: "记忆与偏好",
  memoryRows: [
    { id: "m1", kind: "agent_weights", label: "Agent 学到的偏好权重" },
    { id: "m2", kind: "last_feedback", label: "上次出行反馈" },
    { id: "m3", kind: "disliked_places", label: "不喜欢的地点" },
  ],
  templatesSectionTitle: "常用出行模板",
  templates: [
    {
      id: "t1",
      title: "周末家庭出行",
      usageBadge: "使用 3 次",
      thumbEmoji: "👨‍👩‍👧",
    },
    {
      id: "t2",
      title: "朋友聚会",
      usageBadge: "使用 2 次",
      thumbEmoji: "🍻",
    },
  ],
  quickFooterActions: [
    { id: "q1", kind: "share", label: "分享" },
    { id: "q2", kind: "rate", label: "评价" },
    { id: "q3", kind: "help", label: "帮助" },
    { id: "q4", kind: "about", label: "关于" },
  ],
};
