import type { PlanComparisonPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_PLAN_COMPARISON } from "./mock/plans.mock";

/**
 * 第三屏 · 双方案对比（Plan A / Plan B）
 *
 * **后端契约**
 * - 方法/路径：`GET /api/travel/:travelId/plan-comparison`
 * - Path：`travelId` — 与 `POST /api/travel/sessions`、`GET .../conversation-page` 使用同一会话 id
 * - 响应体：JSON，结构与 {@link PlanComparisonPageDto} 一致（字段名请与类型对齐）
 * - 前端封装：`apiRequest`，base 来自环境变量 `VITE_API_BASE_URL`（仅 origin，不含 path）
 * - 未配置 `VITE_API_BASE_URL` 时：不请求网络，返回 {@link MOCK_PLAN_COMPARISON} 与入参 `travelId` 的组合
 *
 * 文档：`ENDPOINTS.md` §「Plan comparison」
 */
export async function fetchPlanComparisonPage(
  travelId: string,
): Promise<PlanComparisonPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 160));
    return { ...MOCK_PLAN_COMPARISON, travelId };
  }
  const { apiRequest } = await import("./client");
  return apiRequest(
    `/api/travel/${encodeURIComponent(travelId)}/plan-comparison`,
  );
}
