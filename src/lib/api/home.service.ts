import { getApiBaseUrl } from "./config";
import { MOCK_HOME_DASHBOARD } from "./mock/home.mock";
import type { HomeDashboardDto } from "./types";

/**
 * 首页聚合数据
 * 建议后端：GET /api/home/dashboard
 */
export async function fetchHomeDashboard(): Promise<HomeDashboardDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return MOCK_HOME_DASHBOARD;
  }
  const { apiRequest } = await import("./client");
  return apiRequest<HomeDashboardDto>("/api/home/dashboard");
}
