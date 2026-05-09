import type { DietaryPreferencesPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_DIETARY_PREFERENCES_PAGE } from "./mock/dietary-preferences.mock";

/**
 * 第十三屏 · 饮食偏好
 *
 * **后端契约:** `GET /api/user/preferences/dietary`
 * 文档：`ENDPOINTS.md` §17。
 */
export async function fetchDietaryPreferencesPage(): Promise<DietaryPreferencesPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_DIETARY_PREFERENCES_PAGE };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<DietaryPreferencesPageDto>("/api/user/preferences/dietary");
}
