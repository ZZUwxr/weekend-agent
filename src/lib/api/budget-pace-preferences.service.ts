import type {
  BudgetPacePreferencesPageDto,
  SaveBudgetPacePreferencesBody,
  UserPreferenceSaveResponseDto,
} from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_BUDGET_PACE_PREFERENCES_PAGE } from "./mock/budget-pace-preferences.mock";

/**
 * 第十五屏 · 预算与节奏
 *
 * **后端契约:** `GET /api/user/preferences/budget-pace`
 * 文档：`ENDPOINTS.md` §19。
 */
export async function fetchBudgetPacePreferencesPage(): Promise<BudgetPacePreferencesPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_BUDGET_PACE_PREFERENCES_PAGE };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<BudgetPacePreferencesPageDto>("/api/user/preferences/budget-pace");
}

/**
 * **后端契约:** `PUT /api/user/preferences/budget-pace`
 * 请求体：{@link SaveBudgetPacePreferencesBody}
 */
export async function saveBudgetPacePreferences(
  body: SaveBudgetPacePreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 80));
    return { ok: true };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<UserPreferenceSaveResponseDto>("/api/user/preferences/budget-pace", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
