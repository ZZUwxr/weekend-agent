import type {
  CompanionProfileListDto,
  CompanionProfileSaveResponseDto,
  LLMSettingsDto,
  ProfilePageDto,
  SaveCompanionProfileBody,
  SaveLLMSettingsBody,
  UserPreferenceSaveResponseDto,
} from "./types";
import { apiRequest } from "./client";

/**
 * 第十一屏 · 我的（档案、偏好、模板）
 *
 * **后端契约:** `GET /user/profile`
 * 文档：`ENDPOINTS.md` §15。
 */
export async function fetchProfilePage(): Promise<ProfilePageDto> {
  return apiRequest<ProfilePageDto>("/user/profile");
}

export async function fetchCompanionProfiles(): Promise<CompanionProfileListDto> {
  return apiRequest<CompanionProfileListDto>("/user/companions");
}

export async function createCompanionProfile(
  body: SaveCompanionProfileBody,
): Promise<CompanionProfileSaveResponseDto> {
  return apiRequest<CompanionProfileSaveResponseDto>("/user/companions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateCompanionProfile(
  companionId: string,
  body: SaveCompanionProfileBody,
): Promise<CompanionProfileSaveResponseDto> {
  return apiRequest<CompanionProfileSaveResponseDto>(
    `/user/companions/${encodeURIComponent(companionId)}`,
    {
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export async function deleteCompanionProfile(
  companionId: string,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>(
    `/user/companions/${encodeURIComponent(companionId)}`,
    { method: "DELETE" },
  );
}

export async function fetchLLMSettings(): Promise<LLMSettingsDto> {
  return apiRequest<LLMSettingsDto>("/user/settings/llm");
}

export async function saveLLMSettings(
  body: SaveLLMSettingsBody,
): Promise<UserPreferenceSaveResponseDto> {
  return apiRequest<UserPreferenceSaveResponseDto>("/user/settings/llm", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
