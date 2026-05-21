import type { BudgetPacePreferencesPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

/** Figma node 1:1302 · 预算与节奏 */
export const MOCK_BUDGET_PACE_PREFERENCES_PAGE: BudgetPacePreferencesPageDto = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "预算与节奏",
  backLabel: "返回",
  budgetSectionTitle: "预算倾向",
  budgetOptions: [
    {
      id: "budget-value",
      title: "性价比优先",
      description: "更关注价格与实用，优先选择高性价比的行程安排。",
    },
    {
      id: "budget-medium",
      title: "中等（人均80-150）",
      description: "平衡预算与体验，兼顾性价比与舒适度。",
    },
    {
      id: "budget-quality",
      title: "品质体验优先",
      description: "更看重体验与服务，优先选择更高品质的安排。",
    },
  ],
  selectedBudgetId: "budget-medium",
  paceSectionTitle: "行程节奏偏好",
  paceOptions: [
    {
      id: "pace-tight",
      title: "紧凑充实（多打卡）",
      description: "行程安排紧凑，尽可能多看景点、打卡体验。",
    },
    {
      id: "pace-relaxed",
      title: "放松舒适（有缓冲休息）",
      description: "留出充足休息时间，行程从容不赶路。",
    },
    {
      id: "pace-spontaneous",
      title: "随性自由（走哪算哪）",
      description: "行程灵活随意，按当天心情自由安排。",
    },
  ],
  selectedPaceId: "pace-relaxed",
  saveButtonLabel: "保存修改",
};
