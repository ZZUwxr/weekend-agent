import { ChevronDown, ChevronRight } from "lucide-react";

import { Button } from "../common/button";
import { ToolCallCard } from "./ToolCallCard";
import type { StepState } from "../../types/plan";

interface StepDetailProps {
  step: StepState;
  expanded: boolean;
  onToggle: () => void;
}

export function StepDetail({ step, expanded, onToggle }: StepDetailProps) {
  const hasDetails = Boolean(step.result) || step.toolCalls.length > 0;

  return (
    <div className="mt-2 pl-10 sm:pl-12">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <p className="min-w-0 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {summaryForStep(step)}
        </p>
        {hasDetails ? (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-fit shrink-0 px-2 text-xs text-slate-500 dark:text-slate-300"
            onClick={onToggle}
          >
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            {expanded ? "收起" : "展开"}
          </Button>
        ) : null}
      </div>

      {expanded && hasDetails ? (
        <div className="mt-3 animate-slide-in space-y-3 rounded-md border border-border bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/70">
          {step.result ? (
            <div>
              <h4 className="mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                步骤结果
              </h4>
              <pre className="max-h-56 overflow-auto rounded-md bg-white p-3 text-xs leading-5 text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                {JSON.stringify(step.result, null, 2)}
              </pre>
            </div>
          ) : null}

          {step.toolCalls.length > 0 ? (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                工具调用
              </h4>
              {step.toolCalls.map((toolCall, index) => (
                <ToolCallCard
                  key={`${step.step}-${toolCall.tool}-${toolCall.action}-${index}`}
                  toolCall={toolCall}
                />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function summaryForStep(step: StepState): string {
  if (step.status === "pending") {
    return "等待中";
  }
  if (step.status === "running") {
    return step.toolCalls.length > 0
      ? `正在处理，已完成 ${step.toolCalls.length} 次工具调用`
      : "进行中...";
  }
  if (step.status === "error") {
    return "执行失败，请展开查看错误信息";
  }
  if (!step.result) {
    return "已完成";
  }

  if (step.name === "user_understanding") {
    const groupType = readString(step.result.group_type);
    const groupSize = readNumber(step.result.group_size);
    const roleIds = readStringArray(step.result.role_ids);
    return `识别到：${groupType || "未知场景"}，${groupSize || roleIds.length} 人`;
  }

  if (step.name === "conflict_detection") {
    const count = readNumber(step.result.conflicts_count);
    const ids = readStringArray(step.result.conflict_ids).slice(0, 2).join("、");
    return `发现 ${count} 个冲突${ids ? `：${ids}` : ""}`;
  }

  if (step.name === "negotiation") {
    const count = readNumber(step.result.strategies_count);
    const types = readStringArray(step.result.strategy_types).slice(0, 2).join("、");
    return `${count} 种策略${types ? `：${types}` : ""}`;
  }

  if (step.name === "experience_planning") {
    const candidates = step.result.candidates;
    const count = Array.isArray(candidates) ? candidates.length : 0;
    return `${count} 个候选方案`;
  }

  if (step.name === "place_selection") {
    return `地点选择完成，累计 ${step.toolCalls.length} 次工具调用`;
  }

  if (step.name === "routing") {
    return `路线计算完成，累计 ${step.toolCalls.length} 次工具调用`;
  }

  if (step.name === "timeline_builder") {
    const candidates = step.result.candidates;
    const count = Array.isArray(candidates) ? candidates.length : 0;
    return `已构建 ${count} 个时间轴`;
  }

  if (step.name === "scoring_recommendation") {
    const recommended = readString(step.result.recommended_plan_id);
    return recommended ? `推荐方案：${recommended}` : "评分与推荐完成";
  }

  return "已完成";
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readNumber(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}
