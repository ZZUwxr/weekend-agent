import type { ItineraryHubPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第十屏 · 行程主页（当前阶段时间轴、快捷操作、历史行程）
 *
 * **后端契约:** `GET /travel/:travelId/itinerary-hub?planId=...`
 * 文档：`ENDPOINTS.md` §14。
 */
export async function fetchItineraryHubPage(
  travelId: string,
  planId: string,
): Promise<ItineraryHubPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<ItineraryHubPageDto>(
    `/travel/${encodeURIComponent(travelId)}/itinerary-hub?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
