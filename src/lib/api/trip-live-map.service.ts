import type { TripLiveMapPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第八屏 · 行程进行中地图与信息卡（Figma 1:734）
 *
 * **后端契约:** `GET /travel/:travelId/trip-live-map?planId=...`
 * 文档：`ENDPOINTS.md` §11.
 */
export async function fetchTripLiveMapPage(
  travelId: string,
  planId: string,
): Promise<TripLiveMapPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<TripLiveMapPageDto>(
    `/travel/${encodeURIComponent(travelId)}/trip-live-map?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
