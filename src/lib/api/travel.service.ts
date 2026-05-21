import { getApiBaseUrl } from "./config";
import {
  MOCK_CONVERSATION_PAGE,
  MOCK_TRAVEL_ID,
} from "./mock/travel.mock";
import type {
  StartTravelSessionBody,
  StartTravelSessionResponse,
  TravelConversationPageDto,
} from "./types";

/**
 * 用户从首页提交第一句自然语言，创建行程会话
 * 建议后端：POST /api/travel/sessions
 * body: { message, userId? }
 */
export async function startTravelSession(
  body: StartTravelSessionBody,
): Promise<StartTravelSessionResponse> {
  const base = getApiBaseUrl();
  if (!base) {
    void body;
    return { travelId: MOCK_TRAVEL_ID };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<StartTravelSessionResponse>("/api/travel/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * 对话页数据：状态条 + 「想确认一下」+ 需求横向卡片
 * 建议后端：GET /api/travel/:travelId/conversation-page
 */
export async function fetchTravelConversationPage(
  travelId: string,
): Promise<TravelConversationPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return {
      ...MOCK_CONVERSATION_PAGE,
      travelId,
    };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<TravelConversationPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/conversation-page`,
  );
}
