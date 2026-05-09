import type { ProfilePageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_PROFILE_PAGE } from "./mock/profile.mock";

/**
 * 第十一屏 · 我的（档案、偏好、模板）
 *
 * **后端契约:** `GET /api/user/profile`
 * 文档：`ENDPOINTS.md` §15。
 */
export async function fetchProfilePage(): Promise<ProfilePageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_PROFILE_PAGE };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<ProfilePageDto>("/api/user/profile");
}
