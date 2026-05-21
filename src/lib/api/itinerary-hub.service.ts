import type { ItineraryHubPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_ITINERARY_HUB_PAGE } from "./mock/itinerary-hub.mock";

/**
 * 第十屏 · 行程主页（当前阶段时间轴、快捷操作、历史行程）
 *
 * **后端契约:** `GET /api/travel/:travelId/itinerary-hub?planId=...`
 * 文档：`ENDPOINTS.md` §14。
 */
export async function fetchItineraryHubPage(
  travelId: string,
  planId: string,
): Promise<ItineraryHubPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_ITINERARY_HUB_PAGE, travelId, planId };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<ItineraryHubPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/itinerary-hub?${q.toString()}`,
  );
}
