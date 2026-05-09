import type { ActivityPreferencesPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_ACTIVITY_PREFERENCES_PAGE } from "./mock/activity-preferences.mock";

/**
 * 第十四屏 · 活动偏好
 *
 * **后端契约:** `GET /api/user/preferences/activity`
 * 文档：`ENDPOINTS.md` §18。
 */
export async function fetchActivityPreferencesPage(): Promise<ActivityPreferencesPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_ACTIVITY_PREFERENCES_PAGE };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<ActivityPreferencesPageDto>("/api/user/preferences/activity");
}
