import { useMutation, useQuery } from "@tanstack/react-query";

import {
  confirmPlan,
  executePlan,
  getHealth,
  getPlan,
  previewPlan,
  submitPlanEvent,
} from "../services/api";
import type {
  ExecutionResponse,
  PlanEvent,
  HealthResponse,
  PlanOutput,
  PlanPreviewRequest,
} from "../types/plan";

export function usePreviewPlan() {
  return useMutation<PlanOutput, Error, PlanPreviewRequest>({
    mutationFn: previewPlan,
  });
}

export function usePlan(sessionId: string | null) {
  return useQuery<PlanOutput, Error>({
    queryKey: ["plan", sessionId],
    queryFn: () => {
      if (!sessionId) {
        throw new Error("缺少 session_id");
      }
      return getPlan(sessionId);
    },
    enabled: Boolean(sessionId),
  });
}

export function useConfirmPlan() {
  return useMutation<PlanOutput, Error, string>({
    mutationFn: confirmPlan,
  });
}

export function useExecutePlan() {
  return useMutation<ExecutionResponse, Error, string>({
    mutationFn: executePlan,
  });
}

export function useSubmitPlanEvent() {
  return useMutation<PlanOutput, Error, { sessionId: string; event: PlanEvent }>({
    mutationFn: ({ sessionId, event }) => submitPlanEvent(sessionId, event),
  });
}

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });
}
