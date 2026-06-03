import { getApiBaseUrl } from "./config";
import { ApiNotImplementedError, apiRequest, normalizeNetworkError, parseApiError } from "./client";
import { getDeviceUserId } from "./device-user";
import { localLLMSettingsToRuntimeConfig } from "../llmSettings";
import type {
  ActiveTravelDto,
  MobileRevisionResponse,
  TravelClarificationAnswerBody,
  StartTravelSessionBody,
  StartTravelSessionResponse,
  TravelPlanningStreamEvent,
  TravelRevisionBody,
  TravelConversationPageDto,
} from "./types";

/**
 * 用户从首页提交第一句自然语言，创建行程会话
 * 建议后端：POST /travel/sessions
 * body: { message, userId? }
 */
export async function startTravelSession(
  body: StartTravelSessionBody,
): Promise<StartTravelSessionResponse> {
  return apiRequest<StartTravelSessionResponse>("/travel/sessions", {
    method: "POST",
    body: JSON.stringify(withLocalLLMConfig(body)),
  });
}

export async function fetchActiveTravel(): Promise<ActiveTravelDto> {
  return apiRequest<ActiveTravelDto>("/travel/active");
}

export async function streamTravelSession(
  body: StartTravelSessionBody,
  onEvent: (event: TravelPlanningStreamEvent) => void,
): Promise<StartTravelSessionResponse> {
  const base = getApiBaseUrl();
  if (!base) {
    throw new ApiNotImplementedError("POST", "/travel/sessions/stream");
  }

  let response: Response;
  try {
    response = await fetch(`${base}/travel/sessions/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Device-User-Id": getDeviceUserId(),
      },
      body: JSON.stringify(withLocalLLMConfig(body)),
    });
  } catch (error) {
    throw normalizeNetworkError(error);
  }
  if (!response.ok || !response.body) {
    throw await parseApiError(response);
  }

  let travelId = "";
  const decoder = new TextDecoder();
  let buffer = "";
  for await (const chunk of streamResponseChunks(response.body)) {
    buffer += decoder.decode(chunk, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const parsed = parseSseChunk(part);
      if (!parsed) continue;
      onEvent(parsed);
      if (parsed.event === "plan_complete") {
        travelId = String(parsed.data.travel_id || parsed.data.session_id || "");
      }
      if (parsed.event === "error") {
        throw new Error(String(parsed.data.message || parsed.data.error || "规划失败"));
      }
    }
  }
  if (!travelId) {
    throw new Error("规划流结束但未返回 travelId");
  }
  return { travelId };
}

/**
 * 对话页数据：状态条 + 「想确认一下」+ 需求横向卡片
 * 建议后端：GET /travel/:travelId/conversation-page
 */
export async function fetchTravelConversationPage(
  travelId: string,
): Promise<TravelConversationPageDto> {
  assertTravelId(travelId);
  return apiRequest<TravelConversationPageDto>(
    `/travel/${encodeURIComponent(travelId)}/conversation-page`,
  );
}

async function* streamResponseChunks(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<Uint8Array> {
  const reader = body.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) yield value;
    }
  } finally {
    reader.releaseLock();
  }
}

function parseSseChunk(chunk: string): TravelPlanningStreamEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of chunk.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }
  if (!dataLines.length) return null;
  try {
    return { event, data: JSON.parse(dataLines.join("\n")) as Record<string, unknown> };
  } catch {
    return { event, data: { message: dataLines.join("\n") } };
  }
}

/** POST /travel/:travelId/clarifications — 回答澄清问题并继续生成方案 */
export async function answerTravelClarifications(
  travelId: string,
  body: TravelClarificationAnswerBody,
): Promise<TravelConversationPageDto> {
  assertTravelId(travelId);
  return apiRequest<TravelConversationPageDto>(
    `/travel/${encodeURIComponent(travelId)}/clarifications`,
    {
      method: "POST",
      body: JSON.stringify(withLocalLLMConfig(body)),
    },
  );
}

/** POST /travel/:travelId/revise — 按用户自然语言修改方案 */
export async function reviseTravelPlan(
  travelId: string,
  body: TravelRevisionBody,
): Promise<MobileRevisionResponse> {
  assertTravelId(travelId);
  return apiRequest<MobileRevisionResponse>(
    `/travel/${encodeURIComponent(travelId)}/revise`,
    {
      method: "POST",
      body: JSON.stringify(withLocalLLMConfig(body)),
    },
  );
}

function withLocalLLMConfig<T extends { llmConfig?: unknown }>(body: T): T {
  if (body.llmConfig) return body;
  const llmConfig = localLLMSettingsToRuntimeConfig();
  return llmConfig ? { ...body, llmConfig } : body;
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) {
    throw new Error("缺少当前行程，请先从首页创建一条行程。");
  }
}
