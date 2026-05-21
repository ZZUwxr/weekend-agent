import type { TravelModeSettingsPageDto, SaveTravelModePreferencesBody, UserPreferenceSaveResponseDto } from "./types";
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

/**
 * 保存出行方式与距离偏好
 *
 * **后端契约:** `PUT /api/user/preferences/travel-mode`
 * 请求体：{@link SaveTravelModePreferencesBody}
 * 文档：`ENDPOINTS.md` §16（PUT）。
 *
 * 未配置 `VITE_API_BASE_URL` 时本地直接成功，便于离线开发。
 */
export async function saveTravelModePreferences(
  body: SaveTravelModePreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 80));
    return { ok: true };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<UserPreferenceSaveResponseDto>("/api/user/preferences/travel-mode", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
