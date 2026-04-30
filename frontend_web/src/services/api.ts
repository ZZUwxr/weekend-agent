import type {
  ExecutionResponse,
  FeedbackRequest,
  FeedbackResponse,
  HealthResponse,
  PlanEvent,
  PlanOutput,
  PlanPreviewRequest,
} from "../types/plan";

const API_BASE = "/api/v1";

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export async function previewPlan(request: PlanPreviewRequest): Promise<PlanOutput> {
  return requestJson<PlanOutput>("/plans/preview", {
    method: "POST",
    body: request,
  });
}

export async function getPlan(sessionId: string): Promise<PlanOutput> {
  return requestJson<PlanOutput>(`/plans/${encodeURIComponent(sessionId)}`);
}

export async function confirmPlan(sessionId: string): Promise<PlanOutput> {
  return requestJson<PlanOutput>(`/plans/${encodeURIComponent(sessionId)}/confirm`, {
    method: "POST",
  });
}

export async function executePlan(sessionId: string): Promise<ExecutionResponse> {
  return requestJson<ExecutionResponse>(`/plans/${encodeURIComponent(sessionId)}/execute`, {
    method: "POST",
  });
}

export async function submitPlanEvent(
  sessionId: string,
  event: PlanEvent,
): Promise<PlanOutput> {
  return requestJson<PlanOutput>(`/plans/${encodeURIComponent(sessionId)}/events`, {
    method: "POST",
    body: event,
  });
}

export async function submitFeedback(
  sessionId: string,
  request: FeedbackRequest,
): Promise<FeedbackResponse> {
  return requestJson<FeedbackResponse>(`/plans/${encodeURIComponent(sessionId)}/feedback`, {
    method: "POST",
    body: request,
  });
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: object;
  signal?: AbortSignal;
}

async function requestJson<TResponse>(
  path: string,
  options: RequestOptions = {},
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    const detail = await readErrorMessage(response);
    throw new Error(detail || `请求失败：${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

async function readErrorMessage(response: Response): Promise<string | null> {
  try {
    const parsed: unknown = await response.json();
    if (isRecord(parsed) && typeof parsed.detail === "string") {
      return parsed.detail;
    }
    return null;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
