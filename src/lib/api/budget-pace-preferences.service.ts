import type {
  BudgetPacePreferencesPageDto,
  SaveBudgetPacePreferencesBody,
  UserPreferenceSaveResponseDto,
} from "./types";
import { apiRequest } from "./client";

/**
 * 第十五屏 · 预算与节奏
 *
 * **后端契约:** `GET /user/preferences/budget-pace`
 * 文档：`ENDPOINTS.md` §19。
 */
export async function fetchBudgetPacePreferencesPage(): Promise<BudgetPacePreferencesPageDto> {
  return apiRequest<BudgetPacePreferencesPageDto>("/user/preferences/budget-pace");
}

/**
 * **后端契约:** `PUT /user/preferences/budget-pace`
 * 请求体：{@link SaveBudgetPacePreferencesBody}
 */
export async function saveBudgetPacePreferences(
  body: SaveBudgetPacePreferencesBody,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>("/user/preferences/budget-pace", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
