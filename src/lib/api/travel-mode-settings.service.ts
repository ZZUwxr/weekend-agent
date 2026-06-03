import type { TravelModeSettingsPageDto, SaveTravelModePreferencesBody, UserPreferenceSaveResponseDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第十二屏 · 出行方式与距离
 *
 * **后端契约:** `GET /user/preferences/travel-mode`
 * 文档：`ENDPOINTS.md` §16。
 */
export async function fetchTravelModeSettingsPage(): Promise<TravelModeSettingsPageDto> {
  return apiRequest<TravelModeSettingsPageDto>("/user/preferences/travel-mode");
}

/**
 * 保存出行方式与距离偏好
 *
 * **后端契约:** `PUT /user/preferences/travel-mode`
 * 请求体：{@link SaveTravelModePreferencesBody}
 * 文档：`ENDPOINTS.md` §16（PUT）。
 */
export async function saveTravelModePreferences(
  body: SaveTravelModePreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>("/user/preferences/travel-mode", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
