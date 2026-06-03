import type { ItineraryTimelinePageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第四屏 · 已选方案详细时间轴与路线（Figma 1:465）
 *
 * **后端契约**
 * - 方法/路径：`GET /travel/:travelId/itinerary-timeline?planId=...`
 * - Path：`travelId` — 与 `conversation-page`、`plan-comparison` 使用同一会话 id
 * - Query：`planId` — **必填**；与双方案页 `TravelPlanCardDto.id` 一致（如 `plan-a`、`plan-b`）
 * - 响应体：JSON，结构与 {@link ItineraryTimelinePageDto} 一致（字段名请与类型对齐）
 * - 前端封装：`apiRequest`，base 来自环境变量 `VITE_API_BASE_URL`（移动端 BFF 根路径）
 * - 未配置 `VITE_API_BASE_URL` 时：抛出配置错误
 *
 * **建议错误语义**
 * - `404`：`travelId` 不存在，或该会话下没有 `planId` 对应方案 / 尚未生成时间轴
 * - `400`：`planId` 缺失或非法
 *
 * 文档：`ENDPOINTS.md` §「Itinerary timeline」
 */
export async function fetchItineraryTimelinePage(
  travelId: string,
  planId: string,
): Promise<ItineraryTimelinePageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<ItineraryTimelinePageDto>(
    `/travel/${encodeURIComponent(travelId)}/itinerary-timeline?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
