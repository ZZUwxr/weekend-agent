import type {
  ActivityPreferencesPageDto,
  SaveActivityPreferencesBody,
  UserPreferenceSaveResponseDto,
} from "./types";
import { apiRequest } from "./client";

/**
 * 第十四屏 · 活动偏好
 *
 * **后端契约:** `GET /user/preferences/activity`
 * 文档：`ENDPOINTS.md` §18。
 */
export async function fetchActivityPreferencesPage(): Promise<ActivityPreferencesPageDto> {
  return apiRequest<ActivityPreferencesPageDto>("/user/preferences/activity");
}

/**
 * **后端契约:** `PUT /user/preferences/activity`
 * 请求体：{@link SaveActivityPreferencesBody}
 */
export async function saveActivityPreferences(
  body: SaveActivityPreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>("/user/preferences/activity", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
