import { ShieldCheck, Sparkles } from "lucide-react";

import { Badge } from "../common/badge";
import type { RoleProfile, SatisfactionScore } from "../../types/plan";

interface SatisfactionBreakdownProps {
  scores: SatisfactionScore[];
  roles: RoleProfile[];
}

export function SatisfactionBreakdown({ scores, roles }: SatisfactionBreakdownProps) {
  if (scores.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border px-4 py-6 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
        暂无角色满意度数据
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {scores.map((score) => {
        const role = roles.find((item) => item.role_id === score.role_id);
        return <RoleScoreCard key={score.role_id} score={score} displayName={role?.display_name ?? score.role_id} />;
      })}
    </div>
  );
}

function RoleScoreCard({
  score,
  displayName,
}: {
  score: SatisfactionScore;
  displayName: string;
}) {
  return (
    <article className="rounded-md border border-border bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-accent" />
            <h4 className="text-sm font-semibold text-ink dark:text-slate-100">{displayName}</h4>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{score.role_id}</p>
        </div>
        <Badge tone={scoreTone(score.score)}>{score.score.toFixed(1)}</Badge>
      </div>

      <ScoreBar value={score.score} />

      {score.reasons.length > 0 ? (
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          {score.reasons.join("；")}
        </p>
      ) : null}

      {score.sacrificed_points.length > 0 || score.compensation ? (
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {score.sacrificed_points.length > 0 ? (
            <DetailBlock title="牺牲点" values={score.sacrificed_points} />
          ) : null}
          {score.compensation ? (
            <div className="rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800 dark:bg-teal-950/40 dark:text-teal-200">
              <div className="mb-1 flex items-center gap-1 text-xs font-semibold">
                <Sparkles className="h-3.5 w-3.5" />
                补偿
              </div>
              {score.compensation}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function DetailBlock({
  title,
  values,
}: {
  title: string;
  values: string[];
}) {
  return (
    <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
      <div className="mb-1 text-xs font-semibold">{title}</div>
      <ul className="space-y-1">
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}

function ScoreBar({ value }: { value: number }) {
  const width = `${Math.max(0, Math.min(100, (value / 5) * 100))}%`;
  return (
    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
      <div className={`h-full rounded-full ${scoreBarClass(value)}`} style={{ width }} />
    </div>
  );
}

export function scoreTone(score: number): "success" | "warning" | "danger" {
  if (score >= 4) {
    return "success";
  }
  if (score >= 3) {
    return "warning";
  }
  return "danger";
}

function scoreBarClass(score: number): string {
  if (score >= 4) {
    return "bg-teal-500";
  }
  if (score >= 3) {
    return "bg-amber-500";
  }
  return "bg-red-500";
}
