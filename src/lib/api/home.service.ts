import { getApiBaseUrl } from "./config";
import { MOCK_HOME_DASHBOARD, MOCK_HOME_DASHBOARD_UNLOCKED } from "./mock/home.mock";
import type { HomeDashboardDto } from "./types";

export type FetchHomeDashboardOptions = {
  /** Mock：行程内容解锁后与稿 1:211 一致展示示例历史；接后端后由接口返回真实列表 */
  tripContentUnlocked?: boolean;
};

/**
 * 首页聚合数据
 * 建议后端：GET /api/home/dashboard
 */
export async function fetchHomeDashboard(
  opts?: FetchHomeDashboardOptions,
): Promise<HomeDashboardDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return opts?.tripContentUnlocked ? MOCK_HOME_DASHBOARD_UNLOCKED : MOCK_HOME_DASHBOARD;
  }
  const { apiRequest } = await import("./client");
  return apiRequest<HomeDashboardDto>("/api/home/dashboard");
}
