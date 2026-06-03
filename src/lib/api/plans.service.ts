import type { PlanComparisonPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第三屏 · 双方案对比（Plan A / Plan B）
 *
 * **后端契约**
 * - 方法/路径：`GET /travel/:travelId/plan-comparison`
 * - Path：`travelId` — 与 `POST /travel/sessions`、`GET .../conversation-page` 使用同一会话 id
 * - 响应体：JSON，结构与 {@link PlanComparisonPageDto} 一致（字段名请与类型对齐）
 * - 前端封装：`apiRequest`，base 来自环境变量 `VITE_API_BASE_URL`（移动端 BFF 根路径）
 * - 未配置 `VITE_API_BASE_URL` 时：抛出配置错误
 *
 * 文档：`ENDPOINTS.md` §「Plan comparison」
 */
export async function fetchPlanComparisonPage(
  travelId: string,
): Promise<PlanComparisonPageDto> {
  assertTravelId(travelId);
  return apiRequest(
    `/travel/${encodeURIComponent(travelId)}/plan-comparison`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
