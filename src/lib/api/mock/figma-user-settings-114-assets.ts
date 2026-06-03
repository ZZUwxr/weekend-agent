import { FIGMA_PROFILE_150_471 } from "./figma-profile-150-471-assets";

/**
 * F「前端 ui」用户中心 · 偏好子页（与「我的」同文件体系）
 *
 * 路由与稿面对应（dev mode）：
 * - 114:3529 → TravelModeSettingsScreen · `/settings/travel-mode`
 * - 114:3829 → DietaryPreferencesScreen · `/settings/dietary-preferences`
 * - 114:4022 → ActivityPreferencesScreen · `/settings/activity-preferences`
 * - 114:4248 → BudgetPacePreferencesScreen · `/settings/budget-pace`
 *
 * 与 150:471 共用状态栏与背景 blob；若稿面单拆资源可在 MCP 中替换。
 */
export const FIGMA_USER_SETTINGS_114 = {
  statusBar: FIGMA_PROFILE_150_471.statusBar,
  bgBlobA: FIGMA_PROFILE_150_471.bgBlobA,
  bgBlobB: FIGMA_PROFILE_150_471.bgBlobB,
} as const;
