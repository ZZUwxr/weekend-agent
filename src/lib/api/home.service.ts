import { apiRequest } from "./client";
import type { HomeDashboardDto } from "./types";

/**
 * 首页聚合数据
 * 后端契约：GET /home/dashboard
 */
export async function fetchHomeDashboard(): Promise<HomeDashboardDto> {
  return apiRequest<HomeDashboardDto>("/home/dashboard");
}
