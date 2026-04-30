import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

import type {
  CandidateCompleteEvent,
  CandidateStartEvent,
  CandidateState,
  PlanCompleteEvent,
  PlanPreviewRequest,
  PlanPreviewStreamEvent,
  PlanStreamErrorEvent,
  StepCompleteEvent,
  StepStartEvent,
  StepState,
  ToolCallEvent,
  ToolCallResult,
} from "../types/plan";

type StreamStatus = "idle" | "streaming" | "completed" | "error";

interface ActiveStreamRequest {
  request: PlanPreviewRequest;
  nonce: number;
}

interface UseSSEResult {
  isConnected: boolean;
  isStreaming: boolean;
  error: string | null;
  steps: StepState[];
  toolCalls: ToolCallEvent[];
  candidates: CandidateState[];
  planResult: PlanCompleteEvent | null;
  startStream: (request: PlanPreviewRequest) => void;
  reset: () => void;
  events: PlanPreviewStreamEvent[];
  status: StreamStatus;
  stop: () => void;
}

const STREAM_ENDPOINT = "/api/v1/plans/preview/stream";
const MAX_RECONNECT_ATTEMPTS = 1;
const RECONNECT_DELAY_MS = 800;

const stepDefinitions = [
  { step: 1, name: "user_understanding", label: "识别用户意图" },
  { step: 2, name: "conflict_detection", label: "识别群体冲突" },
  { step: 3, name: "negotiation", label: "生成协商策略" },
  { step: 4, name: "experience_planning", label: "生成体验骨架" },
  { step: 5, name: "place_selection", label: "选择主备地点" },
  { step: 6, name: "routing", label: "规划转场路线" },
  { step: 7, name: "timeline_builder", label: "生成时间轴" },
  { step: 8, name: "scoring_recommendation", label: "评分与推荐" },
] as const;

export function useSSE(): UseSSEResult {
  const [activeRequest, setActiveRequest] = useState<ActiveStreamRequest | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<PlanPreviewStreamEvent[]>([]);
  const [steps, setSteps] = useState<StepState[]>(createInitialSteps);
  const [toolCalls, setToolCalls] = useState<ToolCallEvent[]>([]);
  const [candidates, setCandidates] = useState<CandidateState[]>([]);
  const [planResult, setPlanResult] = useState<PlanCompleteEvent | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setActiveRequest(null);
    setIsConnected(false);
    setIsStreaming(false);
  }, []);

  const reset = useCallback(() => {
    stop();
    setError(null);
    setEvents([]);
    setSteps(createInitialSteps());
    setToolCalls([]);
    setCandidates([]);
    setPlanResult(null);
  }, [stop]);

  const startStream = useCallback((request: PlanPreviewRequest) => {
    abortRef.current?.abort();
    setError(null);
    setEvents([]);
    setSteps(createInitialSteps());
    setToolCalls([]);
    setCandidates([]);
    setPlanResult(null);
    setIsConnected(false);
    setIsStreaming(true);
    setActiveRequest({ request, nonce: Date.now() });
  }, []);

  useEffect(() => {
    if (!activeRequest) {
      return undefined;
    }

    let disposed = false;
    let completed = false;
    const controller = new AbortController();
    abortRef.current = controller;

    const handleEvent = (event: PlanPreviewStreamEvent) => {
      if (disposed) {
        return;
      }
      setEvents((current) => [...current, event]);
      applyStreamEvent(event, {
        setSteps,
        setToolCalls,
        setCandidates,
        setPlanResult,
        setError,
        setIsConnected,
        setIsStreaming,
      });
      if (event.event === "plan_complete") {
        completed = true;
      }
    };

    const connectWithRetry = async (attempt: number): Promise<void> => {
      try {
        setIsConnected(true);
        await fetchSse(activeRequest.request, handleEvent, controller.signal);
        if (!disposed && !controller.signal.aborted) {
          setIsConnected(false);
          if (!completed && attempt < MAX_RECONNECT_ATTEMPTS) {
            await delay(RECONNECT_DELAY_MS, controller.signal);
            if (!disposed && !controller.signal.aborted) {
              await connectWithRetry(attempt + 1);
            }
            return;
          }
          if (!completed) {
            const message = "SSE 连接已断开，未收到规划完成事件";
            setError(message);
            markStepError(setSteps, message);
          }
          setIsStreaming(false);
        }
      } catch (caught) {
        if (disposed || controller.signal.aborted) {
          return;
        }
        setIsConnected(false);

        if (!completed && attempt < MAX_RECONNECT_ATTEMPTS) {
          await delay(RECONNECT_DELAY_MS, controller.signal);
          if (!disposed && !controller.signal.aborted) {
            await connectWithRetry(attempt + 1);
          }
          return;
        }

        const message = caught instanceof Error ? caught.message : "SSE 连接失败";
        setError(message);
        setIsStreaming(false);
        markStepError(setSteps, message);
      }
    };

    void connectWithRetry(0);

    return () => {
      disposed = true;
      controller.abort();
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      setIsConnected(false);
    };
  }, [activeRequest]);

  const status = useMemo<StreamStatus>(() => {
    if (error) {
      return "error";
    }
    if (isStreaming) {
      return "streaming";
    }
    if (planResult) {
      return "completed";
    }
    return "idle";
  }, [error, isStreaming, planResult]);

  return {
    isConnected,
    isStreaming,
    error,
    steps,
    toolCalls,
    candidates,
    planResult,
    startStream,
    reset,
    events,
    status,
    stop,
  };
}

function createInitialSteps(): StepState[] {
  return stepDefinitions.map((definition) => ({
    ...definition,
    status: "pending",
    toolCalls: [],
  }));
}

async function fetchSse(
  request: PlanPreviewRequest,
  onEvent: (event: PlanPreviewStreamEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(STREAM_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(`流式规划失败：${response.status}`);
  }
  if (!response.body) {
    throw new Error("浏览器未返回可读流");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) {
        onEvent(event);
      }
    }
  }

  const tail = buffer + decoder.decode();
  if (tail.trim()) {
    const event = parseSseBlock(tail);
    if (event) {
      onEvent(event);
    }
  }
}

function parseSseBlock(block: string): PlanPreviewStreamEvent | null {
  const lines = block.split(/\r?\n/);
  const eventName = lines
    .find((line) => line.startsWith("event:"))
    ?.replace(/^event:\s*/, "")
    .trim();
  const dataText = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.replace(/^data:\s*/, ""))
    .join("\n");

  if (!eventName || !dataText) {
    return null;
  }

  const parsed: unknown = JSON.parse(dataText);
  if (!isRecord(parsed)) {
    return null;
  }

  return toStreamEvent(eventName, parsed);
}

function toStreamEvent(
  eventName: string,
  data: Record<string, unknown>,
): PlanPreviewStreamEvent | null {
  switch (eventName) {
    case "step_start":
      return { event: "step_start", data: toStepStartEvent(data) };
    case "step_complete":
      return { event: "step_complete", data: toStepCompleteEvent(data) };
    case "tool_call":
      return { event: "tool_call", data: toToolCallEvent(data) };
    case "candidate_start":
      return { event: "candidate_start", data: toCandidateStartEvent(data) };
    case "candidate_complete":
      return { event: "candidate_complete", data: toCandidateCompleteEvent(data) };
    case "plan_complete":
      return { event: "plan_complete", data: toPlanCompleteEvent(data) };
    case "error":
      return { event: "error", data: toErrorEvent(data) };
    default:
      return null;
  }
}

function applyStreamEvent(
  event: PlanPreviewStreamEvent,
  setters: {
    setSteps: Dispatch<SetStateAction<StepState[]>>;
    setToolCalls: Dispatch<SetStateAction<ToolCallEvent[]>>;
    setCandidates: Dispatch<SetStateAction<CandidateState[]>>;
    setPlanResult: Dispatch<SetStateAction<PlanCompleteEvent | null>>;
    setError: Dispatch<SetStateAction<string | null>>;
    setIsConnected: Dispatch<SetStateAction<boolean>>;
    setIsStreaming: Dispatch<SetStateAction<boolean>>;
  },
): void {
  const now = Date.now();
  switch (event.event) {
    case "step_start":
      setters.setSteps((current) =>
        updateStep(current, event.data.step, {
          name: event.data.name,
          label: event.data.label,
          status: "running",
          startTime: now,
        }),
      );
      break;
    case "step_complete":
      setters.setSteps((current) =>
        updateStep(current, event.data.step, {
          name: event.data.name,
          label: event.data.label,
          status: "completed",
          result: event.data.result,
          endTime: now,
        }),
      );
      break;
    case "tool_call":
      setters.setToolCalls((current) => [...current, event.data]);
      setters.setSteps((current) =>
        current.map((step) =>
          step.step === event.data.step
            ? { ...step, toolCalls: [...step.toolCalls, event.data] }
            : step,
        ),
      );
      break;
    case "candidate_start":
      setters.setCandidates((current) => upsertCandidate(current, event.data, "running"));
      break;
    case "candidate_complete":
      setters.setCandidates((current) => upsertCandidate(current, event.data, "completed"));
      break;
    case "plan_complete":
      setters.setPlanResult(event.data);
      setters.setIsConnected(false);
      setters.setIsStreaming(false);
      break;
    case "error":
      setters.setError(event.data.error);
      setters.setIsConnected(false);
      setters.setIsStreaming(false);
      if (typeof event.data.step === "number") {
        const failedStep = event.data.step;
        setters.setSteps((current) =>
          updateStep(current, failedStep, {
            status: "error",
            endTime: now,
          }),
        );
      }
      break;
  }
}

function updateStep(
  steps: StepState[],
  stepNumber: number,
  patch: Partial<StepState>,
): StepState[] {
  return steps.map((step) => (step.step === stepNumber ? { ...step, ...patch } : step));
}

function upsertCandidate(
  candidates: CandidateState[],
  event: CandidateStartEvent | CandidateCompleteEvent,
  status: CandidateState["status"],
): CandidateState[] {
  const next: CandidateState = {
    candidate_index: event.candidate_index,
    plan_type: event.plan_type,
    title: event.title,
    status,
    ...(status === "completed" && "overall_score" in event
      ? {
          overall_score: event.overall_score,
          min_role_score: event.min_role_score,
          fairness_score: event.fairness_score,
        }
      : {}),
  };
  const exists = candidates.some((candidate) => candidate.candidate_index === event.candidate_index);
  if (!exists) {
    return [...candidates, next].sort((left, right) => left.candidate_index - right.candidate_index);
  }
  return candidates.map((candidate) =>
    candidate.candidate_index === event.candidate_index
      ? { ...candidate, ...next }
      : candidate,
  );
}

function markStepError(
  setSteps: Dispatch<SetStateAction<StepState[]>>,
  message: string,
): void {
  setSteps((current) =>
    current.map((step) =>
      step.status === "running"
        ? {
            ...step,
            status: "error",
            result: { error: message },
            endTime: Date.now(),
          }
        : step,
    ),
  );
}

function toStepStartEvent(data: Record<string, unknown>): StepStartEvent {
  return {
    step: readNumber(data.step),
    name: readString(data.name),
    label: readString(data.label),
  };
}

function toStepCompleteEvent(data: Record<string, unknown>): StepCompleteEvent {
  return {
    ...toStepStartEvent(data),
    result: readRecord(data.result),
  };
}

function toToolCallEvent(data: Record<string, unknown>): ToolCallEvent {
  return {
    step: readNumber(data.step),
    tool: readString(data.tool),
    action: readString(data.action),
    params: readRecord(data.params),
    result: toToolCallResult(readRecord(data.result)),
  };
}

function toCandidateStartEvent(data: Record<string, unknown>): CandidateStartEvent {
  return {
    candidate_index: readNumber(data.candidate_index),
    plan_type: readString(data.plan_type),
    title: readString(data.title),
  };
}

function toCandidateCompleteEvent(data: Record<string, unknown>): CandidateCompleteEvent {
  return {
    ...toCandidateStartEvent(data),
    overall_score: readNumber(data.overall_score),
    min_role_score: readNumber(data.min_role_score),
    fairness_score: readNumber(data.fairness_score),
  };
}

function toPlanCompleteEvent(data: Record<string, unknown>): PlanCompleteEvent {
  return {
    session_id: readString(data.session_id),
    recommended_plan_id: readString(data.recommended_plan_id),
    candidates_count: readNumber(data.candidates_count),
  };
}

function toErrorEvent(data: Record<string, unknown>): PlanStreamErrorEvent {
  return {
    step: typeof data.step === "number" ? data.step : null,
    error: readString(data.error) || "规划流发生错误",
  };
}

function toToolCallResult(data: Record<string, unknown>): ToolCallResult {
  return {
    ...data,
    success: readBoolean(data.success),
    latency_ms: readNumber(data.latency_ms),
    data: data.data,
    error_message: readOptionalString(data.error_message),
    mock_scenario: readOptionalString(data.mock_scenario),
    error_code: readOptionalString(data.error_code),
  };
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function readNumber(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function readBoolean(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

function readRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timeoutId);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}
