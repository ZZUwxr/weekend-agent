import type { TravelModeSettingsPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_TRAVEL_MODE_SETTINGS_PAGE } from "./mock/travel-mode-settings.mock";

/**
 * 第十二屏 · 出行方式与距离
 *
 * **后端契约:** `GET /api/user/preferences/travel-mode`
 * 文档：`ENDPOINTS.md` §16。
 */
export async function fetchTravelModeSettingsPage(): Promise<TravelModeSettingsPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_TRAVEL_MODE_SETTINGS_PAGE };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<TravelModeSettingsPageDto>("/api/user/preferences/travel-mode");
}
