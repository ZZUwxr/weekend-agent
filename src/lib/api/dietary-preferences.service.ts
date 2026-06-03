import type {
  DietaryPreferencesPageDto,
  SaveDietaryPreferencesBody,
  UserPreferenceSaveResponseDto,
} from "./types";
import { apiRequest } from "./client";

/**
 * 第十三屏 · 饮食偏好
 *
 * **后端契约:** `GET /user/preferences/dietary`
 * 文档：`ENDPOINTS.md` §17。
 */
export async function fetchDietaryPreferencesPage(): Promise<DietaryPreferencesPageDto> {
  return apiRequest<DietaryPreferencesPageDto>("/user/preferences/dietary");
}

/**
 * **后端契约:** `PUT /user/preferences/dietary`
 * 请求体：{@link SaveDietaryPreferencesBody}
 */
export async function saveDietaryPreferences(
  body: SaveDietaryPreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>("/user/preferences/dietary", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
