import { useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { ChevronDown, ChevronRight, Loader2, Play, Trophy } from "lucide-react";

import { Badge } from "../common/badge";
import { Button } from "../common/button";
import { Card, CardBody, CardHeader } from "../common/card";
import { EventPanel, changedStageIds } from "./EventPanel";
import { SatisfactionBreakdown, scoreTone } from "./SatisfactionBreakdown";
import { ScoreComparison } from "./ScoreComparison";
import { TimelineView } from "./TimelineView";
import type { ExecutionResponse, PlanCandidate, PlanEvent, PlanOutput } from "../../types/plan";

interface PlanResultViewProps {
  plan: PlanOutput | null;
  isLoading?: boolean;
  error?: string | null;
  isConfirming?: boolean;
  isExecuting?: boolean;
  confirmError?: string | null;
  executeError?: string | null;
  replanError?: string | null;
  isReplanning?: boolean;
  executionResult?: ExecutionResponse | null;
  previousPlan?: PlanOutput | null;
  onConfirm?: (sessionId: string) => void;
  onExecute?: (sessionId: string) => void;
  onReportEvent?: (event: PlanEvent) => void;
}

export function PlanResultView({
  plan,
  isLoading = false,
  error = null,
  isConfirming = false,
  isExecuting = false,
  confirmError = null,
  executeError = null,
  replanError = null,
  isReplanning = false,
  executionResult = null,
  previousPlan = null,
  onConfirm,
  onExecute,
  onReportEvent,
}: PlanResultViewProps) {
  const recommended = useMemo(() => findRecommended(plan), [plan]);
  const highlightedStageIds = useMemo(
    () => changedStageIds(previousPlan, plan),
    [previousPlan, plan],
  );
  const [expandedPlanIds, setExpandedPlanIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (recommended) {
      setExpandedPlanIds((current) => new Set(current).add(recommended.plan_id));
    }
  }, [recommended]);

  const otherCandidates = plan
    ? plan.plan_candidates.filter((candidate) => candidate.plan_id !== plan.recommended_plan_id)
    : [];
  const canConfirm = Boolean(plan && onConfirm && plan.state === "pending");
  const canExecute = Boolean(
    plan && onExecute && (plan.state === "confirmed" || plan.state === "completed"),
  );

  return (
    <Card className="min-h-[620px] overflow-hidden dark:border-slate-700 dark:bg-slate-900">
      <CardHeader className="dark:border-slate-700">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink dark:text-slate-100">规划结果</h2>
            {plan ? (
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {plan.session_id} · version {plan.plan_version}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {plan ? <Badge tone={plan.state === "confirmed" ? "success" : "neutral"}>{plan.state}</Badge> : null}
            <Button
              disabled={!canConfirm || isConfirming}
              onClick={() => {
                if (plan) {
                  onConfirm?.(plan.session_id);
                }
              }}
            >
              {isConfirming ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {plan?.state === "confirmed" ? "已确认" : "确认方案"}
            </Button>
            <Button
              variant="secondary"
              disabled={!canExecute || isExecuting || plan?.state === "completed"}
              onClick={() => {
                if (plan) {
                  onExecute?.(plan.session_id);
                }
              }}
            >
              {isExecuting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {plan?.state === "completed" ? "已执行" : "执行方案"}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardBody className="space-y-5">
        {isLoading ? <EmptyState text="正在读取最新方案" /> : null}
        {error ? <EmptyState text={error} tone="danger" /> : null}
        {confirmError ? <EmptyState text={confirmError} tone="danger" compact /> : null}
        {executeError ? <EmptyState text={executeError} tone="danger" compact /> : null}
        {replanError ? <EmptyState text={replanError} tone="danger" compact /> : null}
        {!plan && !isLoading && !error ? <EmptyState text="等待规划输入" /> : null}

        {plan && recommended ? (
          <>
            {onReportEvent ? (
              <EventPanel
                plan={plan}
                previousPlan={previousPlan}
                isReplanning={isReplanning}
                error={replanError}
                onReportEvent={onReportEvent}
              />
            ) : null}

            <CandidatePanel
              candidate={recommended}
              plan={plan}
              title="推荐方案"
              recommended
              highlightedStageIds={highlightedStageIds}
              expanded={expandedPlanIds.has(recommended.plan_id)}
              onToggle={() => togglePlan(setExpandedPlanIds, recommended.plan_id)}
            />

            <ScoreComparison
              candidates={plan.plan_candidates}
              recommendedPlanId={plan.recommended_plan_id}
              roles={plan.inferred_context.roles}
            />

            {otherCandidates.length > 0 ? (
              <section className="rounded-lg border border-border bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/50">
                <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
                  其他方案
                </h3>
                <div className="space-y-3">
                  {otherCandidates.map((candidate) => (
                    <CandidatePanel
                      key={candidate.plan_id}
                      candidate={candidate}
                      plan={plan}
                      title={planTypeLabel(candidate)}
                      highlightedStageIds={highlightedStageIds}
                      expanded={expandedPlanIds.has(candidate.plan_id)}
                      onToggle={() => togglePlan(setExpandedPlanIds, candidate.plan_id)}
                    />
                  ))}
                </div>
              </section>
            ) : null}

            {executionResult ? <ExecutionResultPanel result={executionResult} /> : null}
          </>
        ) : null}
      </CardBody>
    </Card>
  );
}

function ExecutionResultPanel({ result }: { result: ExecutionResponse }) {
  return (
    <section className="rounded-lg border border-border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">执行结果</h3>
        <Badge tone={result.success ? "success" : "danger"}>
          {result.success ? "执行完成" : "执行失败"}
        </Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {result.tasks.map((task) => (
          <div
            key={task.task_id}
            className="rounded-md border border-border bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-950"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-ink dark:text-slate-100">
                {task.action}
              </span>
              <Badge tone={task.status === "confirmed" ? "success" : "neutral"}>
                {task.status}
              </Badge>
            </div>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {task.poi_id ?? task.task_id}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CandidatePanel({
  candidate,
  plan,
  title,
  recommended = false,
  highlightedStageIds,
  expanded,
  onToggle,
}: {
  candidate: PlanCandidate;
  plan: PlanOutput;
  title: string;
  recommended?: boolean;
  highlightedStageIds: Set<string>;
  expanded: boolean;
  onToggle: () => void;
}) {
  const changedStages = candidate.stages.filter((stage) => highlightedStageIds.has(stage.stage_id));
  return (
    <section
      className={`rounded-lg border p-4 transition ${
        recommended
          ? "border-teal-200 bg-teal-50/70 dark:border-teal-900 dark:bg-teal-950/20"
          : "border-border bg-white dark:border-slate-700 dark:bg-slate-900"
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {recommended ? (
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                <Trophy className="h-4 w-4" />
              </span>
            ) : null}
            <Badge tone={recommended ? "success" : "neutral"}>{title}</Badge>
            <h3 className="text-lg font-semibold text-ink dark:text-slate-100">
              {candidate.title}
            </h3>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {candidate.theme}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onToggle}>
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          {expanded ? "收起详细" : "展开查看详细"}
        </Button>
      </div>

      <ScoreLine candidate={candidate} />

      {changedStages.length > 0 ? (
        <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
          已局部调整：{changedStages.map((stage) => stage.name).join("、")}
        </div>
      ) : null}

      {expanded ? (
        <div className="mt-4 animate-slide-in space-y-5">
          <TimelineView items={candidate.timeline} />

          <section>
            <h4 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
              角色满意度
            </h4>
            <SatisfactionBreakdown
              scores={candidate.satisfaction_scores}
              roles={plan.inferred_context.roles}
            />
          </section>

          <section className="rounded-md border border-border bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              推荐理由
            </h4>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {candidate.recommendation_reason || candidate.tradeoff_summary || "暂无推荐理由"}
            </p>
          </section>
        </div>
      ) : null}
    </section>
  );
}

function ScoreLine({ candidate }: { candidate: PlanCandidate }) {
  const scores = [
    ["综合评分", candidate.overall_score],
    ["最低满意度", candidate.min_role_score],
    ["公平性", candidate.fairness_score],
  ] as const;

  return (
    <div className="mt-4 grid gap-2 sm:grid-cols-3">
      {scores.map(([label, value]) => (
        <div
          key={label}
          className="rounded-md border border-border bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-950"
        >
          <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
          <div className={`mt-1 text-lg font-semibold ${scoreTextClass(value)}`}>
            {value.toFixed(1)}
          </div>
        </div>
      ))}
    </div>
  );
}

function findRecommended(plan: PlanOutput | null): PlanCandidate | null {
  if (!plan) {
    return null;
  }
  return (
    plan.plan_candidates.find((candidate) => candidate.plan_id === plan.recommended_plan_id) ??
    plan.plan_candidates.find((candidate) => candidate.plan_type === "recommended") ??
    plan.plan_candidates[0] ??
    null
  );
}

function togglePlan(
  setter: Dispatch<SetStateAction<Set<string>>>,
  planId: string,
) {
  setter((current) => {
    const next = new Set(current);
    if (next.has(planId)) {
      next.delete(planId);
    } else {
      next.add(planId);
    }
    return next;
  });
}

function planTypeLabel(candidate: PlanCandidate): string {
  if (candidate.plan_type === "plan_a") {
    return "方案A";
  }
  if (candidate.plan_type === "plan_b") {
    return "方案B";
  }
  return "方案";
}

function scoreTextClass(score: number): string {
  const tone = scoreTone(score);
  if (tone === "success") {
    return "text-teal-700 dark:text-teal-300";
  }
  if (tone === "warning") {
    return "text-amber-700 dark:text-amber-300";
  }
  return "text-red-700 dark:text-red-300";
}

function EmptyState({
  text,
  tone = "neutral",
  compact = false,
}: {
  text: string;
  tone?: "neutral" | "danger";
  compact?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-center rounded-md border border-dashed border-border bg-slate-50 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400 ${
        compact ? "min-h-12 px-4 py-3" : "min-h-80"
      }`}
    >
      <span className={tone === "danger" ? "text-danger" : undefined}>{text}</span>
    </div>
  );
}
