import { Trophy } from "lucide-react";

import { Badge } from "../common/badge";
import { scoreTone } from "./SatisfactionBreakdown";
import type { PlanCandidate, RoleProfile } from "../../types/plan";

interface ScoreComparisonProps {
  candidates: PlanCandidate[];
  recommendedPlanId: string;
  roles: RoleProfile[];
}

export function ScoreComparison({
  candidates,
  recommendedPlanId,
  roles,
}: ScoreComparisonProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        {candidates.map((candidate) => (
          <ScoreCard
            key={candidate.plan_id}
            candidate={candidate}
            active={candidate.plan_id === recommendedPlanId}
          />
        ))}
      </div>

      <div className="rounded-md border border-border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-ink dark:text-slate-100">角色满意度雷达</h3>
          <Badge>0-5</Badge>
        </div>
        <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
          <RadarChart candidates={candidates} roles={roles} recommendedPlanId={recommendedPlanId} />
          <div className="grid gap-2">
            {roles.map((role) => (
              <div
                key={role.role_id}
                className="grid grid-cols-[120px_minmax(0,1fr)] items-center gap-3 text-sm"
              >
                <span className="truncate text-slate-600 dark:text-slate-300">
                  {role.display_name}
                </span>
                <div className="flex flex-wrap gap-2">
                  {candidates.map((candidate) => {
                    const score = candidate.satisfaction_scores.find(
                      (item) => item.role_id === role.role_id,
                    )?.score;
                    return (
                      <Badge
                        key={`${candidate.plan_id}-${role.role_id}`}
                        tone={scoreTone(score ?? 0)}
                      >
                        {candidate.title}: {score?.toFixed(1) ?? "-"}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ScoreCard({ candidate, active }: { candidate: PlanCandidate; active: boolean }) {
  return (
    <article
      className={`rounded-md border p-4 transition ${
        active
          ? "border-teal-200 bg-teal-50 ring-2 ring-teal-100 dark:border-teal-800 dark:bg-teal-950/30 dark:ring-teal-900"
          : "border-border bg-white dark:border-slate-700 dark:bg-slate-900"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-ink dark:text-slate-100">{candidate.title}</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{candidate.theme}</p>
        </div>
        {active ? (
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
            <Trophy className="h-4 w-4" />
          </span>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <ScorePill label="综合" value={candidate.overall_score} />
        <ScorePill label="最低" value={candidate.min_role_score} />
        <ScorePill label="公平" value={candidate.fairness_score} />
      </div>
    </article>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-white px-2 py-2 text-center shadow-sm dark:bg-slate-950">
      <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
      <div className={`mt-1 text-base font-semibold ${scoreTextClass(value)}`}>
        {value.toFixed(1)}
      </div>
    </div>
  );
}

function RadarChart({
  candidates,
  roles,
  recommendedPlanId,
}: {
  candidates: PlanCandidate[];
  roles: RoleProfile[];
  recommendedPlanId: string;
}) {
  const labels: Array<Pick<RoleProfile, "role_id" | "display_name">> =
    roles.length > 0 ? roles : [{ role_id: "overall", display_name: "综合" }];
  const center = 100;
  const radius = 76;
  const rings = [1, 2, 3, 4, 5];
  const palette = ["#0f766e", "#2563eb", "#d97706"];

  return (
    <svg viewBox="0 0 200 200" className="mx-auto h-56 w-56 overflow-visible">
      {rings.map((ring) => (
        <polygon
          key={ring}
          points={polygonPoints(labels.length, center, (radius * ring) / 5)}
          fill="none"
          stroke="currentColor"
          className="text-slate-200 dark:text-slate-700"
          strokeWidth="1"
        />
      ))}
      {labels.map((role, index) => {
        const point = pointFor(index, labels.length, center, radius + 16);
        return (
          <text
            key={role.role_id}
            x={point.x}
            y={point.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-slate-500 text-[9px] dark:fill-slate-400"
          >
            {role.display_name}
          </text>
        );
      })}
      {candidates.map((candidate, index) => {
        const color = palette[index % palette.length];
        const points = labels
          .map((role, roleIndex) => {
            const score =
              candidate.satisfaction_scores.find((item) => item.role_id === role.role_id)?.score ??
              candidate.overall_score;
            return pointFor(roleIndex, labels.length, center, (radius * score) / 5);
          })
          .map((point) => `${point.x},${point.y}`)
          .join(" ");
        const active = candidate.plan_id === recommendedPlanId;
        return (
          <polygon
            key={candidate.plan_id}
            points={points}
            fill={color}
            fillOpacity={active ? 0.22 : 0.1}
            stroke={color}
            strokeWidth={active ? 2.5 : 1.5}
          />
        );
      })}
    </svg>
  );
}

function polygonPoints(count: number, center: number, radius: number): string {
  return Array.from({ length: count }, (_, index) => {
    const point = pointFor(index, count, center, radius);
    return `${point.x},${point.y}`;
  }).join(" ");
}

function pointFor(index: number, count: number, center: number, radius: number) {
  const angle = -Math.PI / 2 + (2 * Math.PI * index) / count;
  return {
    x: center + radius * Math.cos(angle),
    y: center + radius * Math.sin(angle),
  };
}

function scoreTextClass(score: number): string {
  if (score >= 4) {
    return "text-teal-700 dark:text-teal-300";
  }
  if (score >= 3) {
    return "text-amber-700 dark:text-amber-300";
  }
  return "text-red-700 dark:text-red-300";
}
