import type { ActivityPreferencesPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** Figma node 1:1301 · 活动偏好 */
export const MOCK_ACTIVITY_PREFERENCES_PAGE: ActivityPreferencesPageDto = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "活动偏好",
  backLabel: "返回",
  tagsSectionTitle: "偏好的活动类型（可多选）",
  tagOptions: [
    { id: "tag-nature", label: "户外自然（公园/农场/绿道）" },
    { id: "tag-interactive", label: "互动体验（手工/喂动物等）" },
    { id: "tag-art", label: "文艺展览（美术馆/博物馆）" },
    { id: "tag-shopping", label: "逛街购物（商场/市集）" },
    { id: "tag-sports", label: "运动健身（骑行/攀岩等）" },
    { id: "tag-quiet", label: "安静放松（咖啡/书店/SPA）" },
  ],
  selectedTagIds: ["tag-nature", "tag-interactive"],
  familySectionTitle: "添加人物偏好",
  familyMembers: [
    {
      id: "f-son",
      name: "儿子",
      summaryLine: "体力充沛 · 需互动体验",
      avatarEmoji: "👦",
    },
    {
      id: "f-wife",
      name: "老婆",
      summaryLine: "不喜太累 · 需有参与感",
      avatarEmoji: "👩",
    },
    {
      id: "f-me",
      name: "我",
      summaryLine: "无特殊",
      avatarEmoji: "🙋‍♂️",
    },
  ],
  saveButtonLabel: "保存修改",
};
