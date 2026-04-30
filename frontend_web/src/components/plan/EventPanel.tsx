import {
  CloudRain,
  Loader2,
  MessageSquareText,
  TimerReset,
  UserRoundX,
  UsersRound,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Badge } from "../common/badge";
import { Button } from "../common/button";
import type { EventType, PlanCandidate, PlanEvent, PlanOutput, Stage } from "../../types/plan";

interface EventPanelProps {
  plan: PlanOutput;
  previousPlan: PlanOutput | null;
  isReplanning: boolean;
  error: string | null;
  onReportEvent: (event: PlanEvent) => void;
}

const eventOptions: Array<{
  type: EventType;
  label: string;
  icon: LucideIcon;
  severity: number;
  payload: Record<string, unknown>;
}> = [
  {
    type: "weather_change",
    label: "天气变化",
    icon: CloudRain,
    severity: 4,
    payload: { condition: "小雨", outdoor_fit: false, rain_probability: 0.85 },
  },
  {
    type: "queue_overflow",
    label: "排队溢出",
    icon: UsersRound,
    severity: 4,
    payload: { queue_minutes: 45, risk: "high" },
  },
  {
    type: "booking_failed",
    label: "预订失败",
    icon: XCircle,
    severity: 4,
    payload: { reason: "mock reservation failed" },
  },
  {
    type: "time_overrun",
    label: "时间超支",
    icon: TimerReset,
    severity: 3,
    payload: { overrun_minutes: 25 },
  },
  {
    type: "user_feedback",
    label: "用户反馈",
    icon: MessageSquareText,
    severity: 2,
    payload: { feedback: "希望后续更轻松一点" },
  },
];

export function EventPanel({
  plan,
  previousPlan,
  isReplanning,
  error,
  onReportEvent,
}: EventPanelProps) {
  const changes = previousPlan ? summarizePlanChanges(previousPlan, plan) : [];

  return (
    <section className="rounded-lg border border-border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">模拟事件</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            触发局部重规划，当前版本 v{plan.plan_version}
          </p>
        </div>
        {isReplanning ? (
          <Badge tone="warning">
            <span className="inline-flex items-center gap-1">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              重规划中
            </span>
          </Badge>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {eventOptions.map((option) => (
          <EventButton
            key={option.type}
            option={option}
            disabled={isReplanning}
            onClick={() => onReportEvent(buildPlanEvent(plan, option))}
          />
        ))}
      </div>

      {error ? (
        <div className="mt-3 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-danger dark:border-red-900 dark:bg-red-950/30">
          {error}
        </div>
      ) : null}

      {previousPlan ? (
        <div className="mt-4 rounded-md border border-border bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              重规划对比
            </h4>
            <Badge tone={plan.plan_version > previousPlan.plan_version ? "success" : "neutral"}>
              v{previousPlan.plan_version} {"->"} v{plan.plan_version}
            </Badge>
          </div>
          {plan.replan_reason ? (
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {plan.replan_reason}
            </p>
          ) : null}
          {changes.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {changes.map((change) => (
                <li
                  key={`${change.planId}-${change.stageId}`}
                  className="rounded-md bg-white px-3 py-2 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300"
                >
                  <span className="font-medium text-ink dark:text-slate-100">
                    {change.stageName}
                  </span>
                  ：{change.before || "未选择"} {"->"} {change.after || "未选择"}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              本次事件没有替换地点，可能只调整了状态、时长或记录反馈。
            </p>
          )}
        </div>
      ) : null}
    </section>
  );
}

function EventButton({
  option,
  disabled,
  onClick,
}: {
  option: (typeof eventOptions)[number];
  disabled: boolean;
  onClick: () => void;
}) {
  const Icon = option.icon;
  return (
    <Button variant="secondary" size="sm" disabled={disabled} onClick={onClick}>
      <Icon className="h-4 w-4" />
      {option.label}
    </Button>
  );
}

function buildPlanEvent(
  plan: PlanOutput,
  option: (typeof eventOptions)[number],
): PlanEvent {
  const target = pickAffectedTarget(plan, option.type);
  return {
    session_id: plan.session_id,
    event_type: option.type,
    affected_poi_id: target?.selected_poi?.id ?? null,
    affected_stage_id: target?.stage_id ?? null,
    severity: option.severity,
    payload: option.payload,
  };
}

function pickAffectedTarget(plan: PlanOutput, eventType: EventType): Stage | null {
  const candidate = recommendedCandidate(plan);
  if (!candidate) {
    return null;
  }

  if (eventType === "queue_overflow" || eventType === "booking_failed") {
    return (
      candidate.stages.find((stage) => stage.stage_type === "dine" && stage.selected_poi) ??
      candidate.stages.find((stage) => stage.selected_poi) ??
      null
    );
  }

  if (eventType === "weather_change") {
    return (
      candidate.stages.find((stage) => stage.selected_poi && !stage.selected_poi.indoor) ??
      candidate.stages.find((stage) => stage.selected_poi) ??
      null
    );
  }

  if (eventType === "time_overrun") {
    return candidate.stages.find((stage) => stage.selected_poi) ?? null;
  }

  return null;
}

function recommendedCandidate(plan: PlanOutput): PlanCandidate | null {
  return (
    plan.plan_candidates.find((candidate) => candidate.plan_id === plan.recommended_plan_id) ??
    plan.plan_candidates[0] ??
    null
  );
}

export function summarizePlanChanges(before: PlanOutput, after: PlanOutput) {
  return after.plan_candidates.flatMap((afterCandidate) => {
    const beforeCandidate = before.plan_candidates.find(
      (candidate) => candidate.plan_id === afterCandidate.plan_id,
    );
    if (!beforeCandidate) {
      return [];
    }
    return afterCandidate.stages.flatMap((afterStage) => {
      const beforeStage = beforeCandidate.stages.find(
        (stage) => stage.stage_id === afterStage.stage_id,
      );
      const beforePoi = beforeStage?.selected_poi?.name ?? "";
      const afterPoi = afterStage.selected_poi?.name ?? "";
      if (beforePoi === afterPoi) {
        return [];
      }
      return [
        {
          planId: afterCandidate.plan_id,
          stageId: afterStage.stage_id,
          stageName: afterStage.name,
          before: beforePoi,
          after: afterPoi,
        },
      ];
    });
  });
}

export function changedStageIds(before: PlanOutput | null, after: PlanOutput | null): Set<string> {
  if (!before || !after) {
    return new Set();
  }
  return new Set(summarizePlanChanges(before, after).map((change) => change.stageId));
}
