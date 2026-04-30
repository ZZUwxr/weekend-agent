import { Bot, CircleCheck, CircleOff, Loader2 } from "lucide-react";

import { Badge } from "../common/badge";
import type { HealthResponse } from "../../types/plan";

interface HeaderProps {
  health: HealthResponse | null;
  isChecking: boolean;
  error: string | null;
}

export function Header({ health, isChecking, error }: HeaderProps) {
  const healthy = health?.status === "ok";

  return (
    <header className="border-b border-border bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-accent dark:bg-teal-950/50 dark:text-teal-300">
            <Bot className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-ink dark:text-slate-100">Weekend Agent</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              本地探索 / 周末活动规划 AI
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={healthy ? "success" : error ? "danger" : "neutral"}>
            <span className="inline-flex items-center gap-1">
              {isChecking ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : healthy ? (
                <CircleCheck className="h-3.5 w-3.5" />
              ) : (
                <CircleOff className="h-3.5 w-3.5" />
              )}
              后端 {healthy ? "在线" : error ? "异常" : "检查中"}
            </span>
          </Badge>
          <span className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300">
            {health ? `${health.app} · ${health.env}` : "API /api/v1"}
          </span>
        </div>
      </div>
    </header>
  );
}
