import type { TripLiveMapPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_TRIP_LIVE_MAP_PAGE } from "./mock/trip-live-map.mock";

/**
 * 第八屏 · 行程进行中地图与信息卡（Figma 1:734）
 *
 * **后端契约:** `GET /api/travel/:travelId/trip-live-map?planId=...`
 * 文档：`ENDPOINTS.md` §11.
 */
export async function fetchTripLiveMapPage(
  travelId: string,
  planId: string,
): Promise<TripLiveMapPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_TRIP_LIVE_MAP_PAGE, travelId, planId };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<TripLiveMapPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/trip-live-map?${q.toString()}`,
  );
}
