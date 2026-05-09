import type { DietaryPreferencesPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_DIETARY_PREFERENCES_PAGE: DietaryPreferencesPageDto = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "饮食偏好",
  navSubtitle: "适用对象：全部成员 / 可分别设置",
  backLabel: "返回",
  specialNeedsSectionTitle: "特殊饮食需求（可多选）",
  needOptions: [
    { id: "need-lowcal", label: "低卡 / 健康轻食" },
    { id: "need-veg", label: "素食" },
    { id: "need-halal", label: "清真" },
    { id: "need-none", label: "无特殊", exclusive: true },
    { id: "need-allergen", label: "过敏源（展开填写）", expandWhenChecked: true },
  ],
  selectedNeedIds: ["need-lowcal"],
  familySectionTitle: "添加人物偏好",
  familyMembers: [
    {
      id: "f-son",
      name: "儿子",
      summaryLine: "偏好：儿童餐 · 不辣",
      avatarEmoji: "👦",
    },
    {
      id: "f-wife",
      name: "老婆",
      summaryLine: "约束：低卡 · 健康轻食",
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
