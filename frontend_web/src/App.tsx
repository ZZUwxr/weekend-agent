import { useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { Header } from "./components/layout/Header";
import { PlanResultView } from "./components/plan/PlanResultView";
import { QueryInput } from "./components/plan/QueryInput";
import { StreamProgress } from "./components/stream/StreamProgress";
import {
  useConfirmPlan,
  useExecutePlan,
  useHealth,
  usePlan,
  useSubmitPlanEvent,
} from "./hooks/usePlan";
import { useSSE } from "./hooks/useSSE";
import type { PlanEvent, PlanOutput, PlanPreviewRequest } from "./types/plan";

const defaultRequest: PlanPreviewRequest = {
  user_id: "u001",
  query: "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
  city: "深圳",
  start_time: "2026-05-10T14:00:00",
  duration_minutes: 240,
  location: {
    lat: 22.54,
    lon: 114.05,
  },
};

export default function App() {
  const [request, setRequest] = useState<PlanPreviewRequest>(defaultRequest);
  const [preReplanPlan, setPreReplanPlan] = useState<PlanOutput | null>(null);
  const healthQuery = useHealth();
  const confirmMutation = useConfirmPlan();
  const executeMutation = useExecutePlan();
  const replanMutation = useSubmitPlanEvent();
  const stream = useSSE();
  const streamPlanQuery = usePlan(stream.planResult?.session_id ?? null);

  const displayedPlan =
    executeMutation.data?.plan ??
    confirmMutation.data ??
    replanMutation.data ??
    streamPlanQuery.data ??
    null;
  const displayedError = streamPlanQuery.error?.message ?? null;
  const isPlanning = stream.isStreaming || streamPlanQuery.isFetching;

  return (
    <AppShell
      header={
        <Header
          health={healthQuery.data ?? null}
          isChecking={healthQuery.isFetching}
          error={healthQuery.error?.message ?? null}
        />
      }
    >
      <section className="space-y-5">
        <QueryInput
          value={request}
          disabled={isPlanning}
          isPlanning={isPlanning}
          onChange={setRequest}
          onSubmit={() => {
            confirmMutation.reset();
            executeMutation.reset();
            replanMutation.reset();
            setPreReplanPlan(null);
            stream.startStream(request);
          }}
        />
        <StreamProgress
          steps={stream.steps}
          toolCalls={stream.toolCalls}
          candidates={stream.candidates}
          planResult={stream.planResult}
          isConnected={stream.isConnected}
          isStreaming={stream.isStreaming}
          error={stream.error}
        />
      </section>

      <PlanResultView
        plan={displayedPlan}
        isLoading={streamPlanQuery.isFetching}
        error={displayedError}
        isConfirming={confirmMutation.isPending}
        isExecuting={executeMutation.isPending}
        isReplanning={replanMutation.isPending}
        confirmError={confirmMutation.error?.message ?? null}
        executeError={executeMutation.error?.message ?? null}
        replanError={replanMutation.error?.message ?? null}
        executionResult={executeMutation.data ?? null}
        previousPlan={preReplanPlan}
        onConfirm={(sessionId) => confirmMutation.mutate(sessionId)}
        onExecute={(sessionId) => executeMutation.mutate(sessionId)}
        onReportEvent={(event) => {
          if (!displayedPlan) {
            return;
          }
          setPreReplanPlan(displayedPlan);
          confirmMutation.reset();
          executeMutation.reset();
          replanMutation.mutate({ sessionId: event.session_id, event });
        }}
      />
    </AppShell>
  );
}
