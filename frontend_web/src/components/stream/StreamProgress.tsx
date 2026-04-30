import { useMemo, useState } from "react";
import { Check, Circle, Loader2, Radio, X } from "lucide-react";

import { Badge } from "../common/badge";
import { Card } from "../common/card";
import { StepDetail } from "./StepDetail";
import { ToolCallCard } from "./ToolCallCard";
import type {
  CandidateState,
  PlanCompleteEvent,
  StepState,
  StepStatus,
  ToolCallEvent,
} from "../../types/plan";

interface StreamProgressProps {
  steps: StepState[];
  toolCalls: ToolCallEvent[];
  candidates: CandidateState[];
  planResult: PlanCompleteEvent | null;
  isConnected: boolean;
  isStreaming: boolean;
  error: string | null;
}

export function StreamProgress({
  steps,
  toolCalls,
  candidates,
  planResult,
  isConnected,
  isStreaming,
  error,
}: StreamProgressProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const activeStep = useMemo(
    () => steps.find((step) => step.status === "running")?.step ?? null,
    [steps],
  );

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((current) => {
      const next = new Set(current);
      if (next.has(stepNumber)) {
        next.delete(stepNumber);
      } else {
        next.add(stepNumber);
      }
      return next;
    });
  };

  return (
    <Card className="overflow-hidden dark:border-slate-700 dark:bg-slate-900">
      <div className="border-b border-border bg-white px-5 py-4 dark:border-slate-700 dark:bg-slate-900">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink dark:text-slate-100">
              Weekend Agent - {isStreaming ? "AI 规划中..." : "AI 规划过程"}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              实时展示步骤状态、工具调用和候选方案推进。
            </p>
          </div>
          <Badge tone={badgeTone({ error, planResult, isConnected })}>
            {statusText({ error, planResult, isConnected, isStreaming })}
          </Badge>
        </div>
      </div>

      <div className="space-y-1 px-4 py-4 sm:px-5">
        {steps.map((step) => (
          <StepProgressRow
            key={step.step}
            step={step}
            expanded={expandedSteps.has(step.step)}
            isActive={activeStep === step.step}
            onToggle={() => toggleStep(step.step)}
          />
        ))}
      </div>

      {toolCalls.length > 0 ? (
        <section className="border-t border-border bg-slate-50 px-5 py-4 dark:border-slate-700 dark:bg-slate-950/60">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              最新工具调用
            </h3>
            <Badge>{toolCalls.length} 次</Badge>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {toolCalls.slice(-4).map((toolCall, index) => (
              <ToolCallCard
                key={`${toolCall.step}-${toolCall.tool}-${toolCall.action}-${index}`}
                toolCall={toolCall}
                compact
              />
            ))}
          </div>
        </section>
      ) : null}

      {candidates.length > 0 || planResult || error ? (
        <footer className="border-t border-border px-5 py-4 dark:border-slate-700">
          <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
            <CandidateStrip candidates={candidates} />
            {planResult ? (
              <Badge tone="success">完成 {planResult.candidates_count} 个候选方案</Badge>
            ) : null}
            {error ? <p className="text-sm text-danger">{error}</p> : null}
          </div>
        </footer>
      ) : null}
    </Card>
  );
}

function StepProgressRow({
  step,
  expanded,
  isActive,
  onToggle,
}: {
  step: StepState;
  expanded: boolean;
  isActive: boolean;
  onToggle: () => void;
}) {
  return (
    <article
      className={`rounded-md px-2 py-3 transition-all duration-200 sm:px-3 ${
        isActive
          ? "bg-sky-50 ring-1 ring-sky-100 dark:bg-sky-950/30 dark:ring-sky-900"
          : "hover:bg-slate-50 dark:hover:bg-slate-800/70"
      } ${step.status === "completed" ? "animate-pop-complete" : ""}`}
    >
      <div className="grid grid-cols-[28px_minmax(0,1fr)_auto] gap-3">
        <div className="pt-0.5">{statusIcon(step.status)}</div>
        <div className="min-w-0">
          <div className="flex min-w-0 flex-col gap-1 sm:flex-row sm:items-center">
            <h3 className="truncate text-sm font-semibold text-ink dark:text-slate-100">
              {step.step}. {normalizedLabel(step)}
            </h3>
            <span className="text-xs text-slate-400 dark:text-slate-500">{step.name}</span>
          </div>
        </div>
        <div className="text-right text-xs text-slate-500 dark:text-slate-400">
          {durationText(step)}
        </div>
      </div>
      <StepDetail step={step} expanded={expanded} onToggle={onToggle} />
    </article>
  );
}

function CandidateStrip({ candidates }: { candidates: CandidateState[] }) {
  if (candidates.length === 0) {
    return <span className="text-sm text-slate-500 dark:text-slate-400">候选方案等待生成</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {candidates.map((candidate) => (
        <span
          key={candidate.candidate_index}
          className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900"
        >
          <span className="font-medium text-slate-700 dark:text-slate-200">
            {candidate.title}
          </span>
          <Badge tone={candidate.status === "completed" ? "success" : "neutral"}>
            {candidate.status}
          </Badge>
          {typeof candidate.overall_score === "number" ? (
            <span className="font-semibold text-accent">{candidate.overall_score.toFixed(1)}</span>
          ) : null}
        </span>
      ))}
    </div>
  );
}

function statusIcon(status: StepStatus) {
  if (status === "pending") {
    return <Circle className="h-5 w-5 text-slate-300 dark:text-slate-600" />;
  }
  if (status === "running") {
    return (
      <span className="relative inline-flex h-5 w-5 items-center justify-center">
        <span className="absolute h-5 w-5 animate-ping rounded-full bg-sky-300 opacity-50" />
        <Loader2 className="relative h-5 w-5 animate-spin text-sky-600 dark:text-sky-300" />
      </span>
    );
  }
  if (status === "completed") {
    return (
      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
        <Check className="h-3.5 w-3.5" />
      </span>
    );
  }
  return (
    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300">
      <X className="h-3.5 w-3.5" />
    </span>
  );
}

function durationText(step: StepState): string {
  if (step.status === "pending") {
    return "等待中";
  }
  if (step.status === "running" || !step.endTime) {
    return "进行中...";
  }
  if (!step.startTime) {
    return "已完成";
  }
  return `${((step.endTime - step.startTime) / 1000).toFixed(1)}s`;
}

function normalizedLabel(step: StepState): string {
  const labels: Record<string, string> = {
    user_understanding: "识别用户意图",
    conflict_detection: "检测角色冲突",
    negotiation: "生成协商策略",
    experience_planning: "规划体验方案",
    place_selection: "选择地点",
    routing: "计算路线",
    timeline_builder: "构建时间轴",
    scoring_recommendation: "评分与推荐",
    scoring: "评分与推荐",
  };
  return labels[step.name] ?? step.label;
}

function statusText({
  error,
  planResult,
  isConnected,
  isStreaming,
}: {
  error: string | null;
  planResult: PlanCompleteEvent | null;
  isConnected: boolean;
  isStreaming: boolean;
}) {
  if (error) {
    return "失败";
  }
  if (planResult) {
    return "已完成";
  }
  if (isConnected) {
    return "连接中";
  }
  if (isStreaming) {
    return "启动中";
  }
  return (
    <span className="inline-flex items-center gap-1">
      <Radio className="h-3 w-3" />
      待开始
    </span>
  );
}

function badgeTone({
  error,
  planResult,
  isConnected,
}: {
  error: string | null;
  planResult: PlanCompleteEvent | null;
  isConnected: boolean;
}): "neutral" | "success" | "warning" | "danger" {
  if (error) {
    return "danger";
  }
  if (planResult) {
    return "success";
  }
  if (isConnected) {
    return "warning";
  }
  return "neutral";
}
