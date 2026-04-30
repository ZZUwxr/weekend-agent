import { CalendarClock, MapPin, Route, Star } from "lucide-react";

import { Badge } from "../common/badge";
import { Card, CardBody, CardHeader } from "../common/card";
import type { PlanCandidate, PlanOutput, TimelineItem } from "../../types/plan";

interface PlanSummaryProps {
  plan: PlanOutput | null;
  isLoading?: boolean;
  error?: string | null;
}

export function PlanSummary({ plan, isLoading = false, error = null }: PlanSummaryProps) {
  const recommended = plan
    ? plan.plan_candidates.find((candidate) => candidate.plan_id === plan.recommended_plan_id)
    : null;

  return (
    <Card className="min-h-[520px]">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">方案结果</h2>
            {plan ? (
              <p className="mt-1 text-sm text-slate-500">{plan.session_id}</p>
            ) : null}
          </div>
          {plan ? <Badge tone="success">{plan.state}</Badge> : null}
        </div>
      </CardHeader>
      <CardBody>
        {isLoading ? <EmptyState text="正在读取最新方案" /> : null}
        {error ? <EmptyState text={error} tone="danger" /> : null}
        {!plan && !isLoading && !error ? <EmptyState text="等待规划输入" /> : null}
        {plan && recommended ? (
          <div className="space-y-5">
            <section>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-lg font-semibold">{recommended.title}</h3>
                <Badge>{recommended.plan_type}</Badge>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {recommended.recommendation_reason || recommended.tradeoff_summary}
              </p>
            </section>

            <ScoreStrip candidate={recommended} />

            <section className="grid gap-3 md:grid-cols-3">
              <Metric
                icon={<Star className="h-4 w-4" />}
                label="角色"
                value={`${plan.inferred_context.group_size} 人`}
              />
              <Metric
                icon={<MapPin className="h-4 w-4" />}
                label="冲突"
                value={`${plan.conflicts.length} 个`}
              />
              <Metric
                icon={<Route className="h-4 w-4" />}
                label="执行"
                value={`${plan.execution_graph.length} 项`}
              />
            </section>

            <section>
              <h4 className="mb-2 text-sm font-semibold text-slate-700">角色画像</h4>
              <div className="flex flex-wrap gap-2">
                {plan.inferred_context.roles.map((role) => (
                  <Badge key={role.role_id} tone="success">
                    {role.display_name}
                  </Badge>
                ))}
              </div>
            </section>

            <section>
              <h4 className="mb-2 text-sm font-semibold text-slate-700">时间轴</h4>
              <div className="space-y-3">
                {recommended.timeline.map((item, index) => (
                  <TimelineRow key={`${item.time}-${item.poi_id ?? item.type}-${index}`} item={item} />
                ))}
              </div>
            </section>

            <section>
              <h4 className="mb-2 text-sm font-semibold text-slate-700">候选方案</h4>
              <div className="grid gap-2">
                {plan.plan_candidates.map((candidate) => (
                  <CandidateRow
                    key={candidate.plan_id}
                    candidate={candidate}
                    active={candidate.plan_id === plan.recommended_plan_id}
                  />
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function ScoreStrip({ candidate }: { candidate: PlanCandidate }) {
  const scores = [
    ["综合", candidate.overall_score],
    ["最低满意", candidate.min_role_score],
    ["公平性", candidate.fairness_score],
  ] as const;

  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {scores.map(([label, value]) => (
        <div key={label} className="rounded-md border border-border bg-slate-50 px-3 py-2">
          <div className="text-xs text-slate-500">{label}</div>
          <div className="mt-1 text-lg font-semibold">{value.toFixed(1)}</div>
        </div>
      ))}
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-border bg-white px-3 py-2">
      <div className="text-accent">{icon}</div>
      <div>
        <div className="text-xs text-slate-500">{label}</div>
        <div className="text-sm font-semibold">{value}</div>
      </div>
    </div>
  );
}

function TimelineRow({ item }: { item: TimelineItem }) {
  return (
    <div className="grid grid-cols-[64px_1fr] gap-3 rounded-md border border-border bg-white p-3">
      <div className="flex items-start gap-1 text-sm font-semibold text-accent">
        <CalendarClock className="mt-0.5 h-4 w-4" />
        {item.time}
      </div>
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">{item.poi_name ?? item.type}</span>
          <Badge>{item.type}</Badge>
          {item.mode ? <Badge tone="success">{item.mode}</Badge> : null}
        </div>
        <p className="mt-1 text-sm text-slate-600">
          {item.duration_minutes} 分钟 · {item.notes}
        </p>
      </div>
    </div>
  );
}

function CandidateRow({ candidate, active }: { candidate: PlanCandidate; active: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-white px-3 py-2">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{candidate.title}</span>
          {active ? <Badge tone="success">推荐</Badge> : null}
        </div>
        <div className="mt-1 text-xs text-slate-500">{candidate.theme}</div>
      </div>
      <div className="text-right text-sm font-semibold">{candidate.overall_score.toFixed(1)}</div>
    </div>
  );
}

function EmptyState({ text, tone = "neutral" }: { text: string; tone?: "neutral" | "danger" }) {
  return (
    <div className="flex min-h-80 items-center justify-center rounded-md border border-dashed border-border bg-slate-50 text-sm text-slate-500">
      <span className={tone === "danger" ? "text-danger" : undefined}>{text}</span>
    </div>
  );
}
