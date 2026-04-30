import {
  CloudSun,
  MapPin,
  Navigation,
  Search,
  UsersRound,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "../common/badge";
import type { ToolCallEvent } from "../../types/plan";

interface ToolCallCardProps {
  toolCall: ToolCallEvent;
  compact?: boolean;
}

const toolMeta: Record<
  string,
  {
    label: string;
    icon: LucideIcon;
    toneClass: string;
  }
> = {
  weather: {
    label: "查询天气",
    icon: CloudSun,
    toneClass: "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300",
  },
  poi: {
    label: "搜索 POI",
    icon: MapPin,
    toneClass: "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300",
  },
  poi_query: {
    label: "转换检索词",
    icon: Search,
    toneClass: "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
  },
  queue: {
    label: "查询排队状态",
    icon: UsersRound,
    toneClass: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  },
  route: {
    label: "计算路线",
    icon: Navigation,
    toneClass: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300",
  },
};

export function ToolCallCard({ toolCall, compact = false }: ToolCallCardProps) {
  const meta = toolMeta[toolCall.tool] ?? {
    label: toolCall.action || toolCall.tool,
    icon: Search,
    toneClass: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  };
  const Icon = meta.icon;
  const isMock = Boolean(toolCall.result.mock_scenario);

  return (
    <article className="animate-slide-in rounded-md border border-border bg-white p-3 shadow-sm transition dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${meta.toneClass}`}>
            <Icon className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <h4 className="truncate text-sm font-semibold text-ink dark:text-slate-100">
              {meta.label}
            </h4>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400">
              {toolCall.tool}.{toolCall.action}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {isMock ? <Badge tone="warning">Mock 数据</Badge> : null}
          <Badge tone={toolCall.result.success ? "success" : "danger"}>
            {toolCall.result.latency_ms}ms
          </Badge>
        </div>
      </div>

      <div className={compact ? "mt-2 space-y-1" : "mt-3 space-y-2"}>
        <InfoRow label="参数" value={formatParams(toolCall.params)} />
        <InfoRow label="结果" value={summarizeResult(toolCall)} />
        {!toolCall.result.success && toolCall.result.error_message ? (
          <InfoRow label="错误" value={toolCall.result.error_message} danger />
        ) : null}
      </div>
    </article>
  );
}

function InfoRow({
  label,
  value,
  danger = false,
}: {
  label: string;
  value: string;
  danger?: boolean;
}) {
  return (
    <div className="grid grid-cols-[44px_minmax(0,1fr)] gap-2 text-xs leading-5">
      <span className="text-slate-400 dark:text-slate-500">{label}</span>
      <span
        className={
          danger
            ? "break-words text-danger"
            : "break-words text-slate-600 dark:text-slate-300"
        }
      >
        {value || "-"}
      </span>
    </div>
  );
}

function formatParams(params: Record<string, unknown>): string {
  const pairs = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${key}=${formatValue(value)}`);
  return pairs.join("，");
}

function summarizeResult(toolCall: ToolCallEvent): string {
  const result = toolCall.result;
  if (!result.success && result.error_message) {
    return result.error_message;
  }

  if (toolCall.tool === "weather") {
    const condition = readString(result.condition) || readString(result.data);
    const temperature = readNumber(result.temperature);
    const outdoorFit = result.outdoor_fit === true ? "适合户外" : "";
    return [condition, temperature ? `${temperature}°C` : "", outdoorFit]
      .filter(Boolean)
      .join("，");
  }

  if (toolCall.tool === "poi") {
    const count = readNumber(result.count);
    const names = readStringArray(result.poi_names).slice(0, 3).join("、");
    return count > 0 ? `命中 ${count} 个地点${names ? `：${names}` : ""}` : "没有命中地点";
  }

  if (toolCall.tool === "poi_query") {
    const categories = readStringArray(result.categories).join("、");
    const tags = readStringArray(result.tags).slice(0, 6).join("、");
    return [
      categories ? `类别：${categories}` : "",
      tags ? `标签：${tags}` : "",
    ]
      .filter(Boolean)
      .join("；");
  }

  if (toolCall.tool === "queue") {
    const risk = readString(result.risk);
    const minutes = readNumber(result.queue_minutes);
    return [risk ? `风险 ${risk}` : "", minutes ? `预计 ${minutes} 分钟` : ""]
      .filter(Boolean)
      .join("，");
  }

  if (toolCall.tool === "route") {
    const meters = readNumber(result.distance_meters);
    const walking = readNumber(result.walking_minutes);
    const taxi = readNumber(result.taxi_minutes);
    return [
      meters ? `${meters} 米` : "",
      walking ? `步行 ${walking} 分钟` : "",
      taxi ? `打车 ${taxi} 分钟` : "",
    ]
      .filter(Boolean)
      .join("，");
  }

  return JSON.stringify(result);
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(formatValue).join("/");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
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
