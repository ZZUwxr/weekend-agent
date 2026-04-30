import {
  Car,
  Clock3,
  Coffee,
  Footprints,
  Gamepad2,
  MapPin,
  Utensils,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Badge } from "../common/badge";
import type { TimelineItem, TimelineItemType } from "../../types/plan";

interface TimelineViewProps {
  items: TimelineItem[];
}

const typeMeta: Record<
  TimelineItemType,
  {
    label: string;
    icon: LucideIcon;
    dotClass: string;
    cardClass: string;
  }
> = {
  activity: {
    label: "活动",
    icon: Gamepad2,
    dotClass: "bg-sky-100 text-sky-700 ring-sky-200 dark:bg-sky-950 dark:text-sky-300 dark:ring-sky-900",
    cardClass: "border-sky-100 bg-sky-50/50 dark:border-sky-900 dark:bg-sky-950/20",
  },
  dining: {
    label: "用餐",
    icon: Utensils,
    dotClass: "bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-900",
    cardClass: "border-amber-100 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20",
  },
  transport: {
    label: "转场",
    icon: Footprints,
    dotClass: "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700",
    cardClass: "border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900",
  },
  buffer: {
    label: "缓冲",
    icon: Clock3,
    dotClass: "bg-zinc-100 text-zinc-600 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700",
    cardClass: "border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900",
  },
};

export function TimelineView({ items }: TimelineViewProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
        暂无时间轴
      </div>
    );
  }

  return (
    <ol className="relative space-y-3">
      {items.map((item, index) => (
        <TimelineRow key={`${item.time}-${item.type}-${item.poi_id ?? index}`} item={item} />
      ))}
    </ol>
  );
}

function TimelineRow({ item }: { item: TimelineItem }) {
  const meta = typeMeta[item.type];
  const Icon = transportIcon(item) ?? meta.icon;

  return (
    <li className="grid grid-cols-[64px_24px_minmax(0,1fr)] gap-3 sm:grid-cols-[72px_28px_minmax(0,1fr)]">
      <time className="pt-3 text-sm font-semibold tabular-nums text-slate-500 dark:text-slate-400">
        {item.time}
      </time>
      <div className="relative flex justify-center">
        <span className="absolute bottom-[-14px] top-10 w-px bg-border dark:bg-slate-700" />
        <span
          className={`relative z-10 mt-2 inline-flex h-8 w-8 items-center justify-center rounded-full ring-4 ${meta.dotClass}`}
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className={`rounded-md border px-3 py-2 ${meta.cardClass}`}>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-ink dark:text-slate-100">
                {item.poi_name ?? meta.label}
              </h4>
              <Badge>{meta.label}</Badge>
              {item.mode ? <Badge tone="success">{item.mode}</Badge> : null}
            </div>
            <p className="mt-1 text-sm leading-5 text-slate-600 dark:text-slate-300">
              {item.notes || "按计划执行"}
            </p>
          </div>
          <div className="shrink-0 text-right text-xs text-slate-500 dark:text-slate-400">
            <div>{item.duration_minutes}min</div>
            {item.estimated_cost > 0 ? <div>¥{item.estimated_cost.toFixed(0)}</div> : null}
          </div>
        </div>
        {item.poi_id ? (
          <div className="mt-2 inline-flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500">
            <MapPin className="h-3 w-3" />
            {item.poi_id}
          </div>
        ) : null}
      </div>
    </li>
  );
}

function transportIcon(item: TimelineItem): LucideIcon | null {
  if (item.type !== "transport") {
    return null;
  }
  if (item.mode === "taxi") {
    return Car;
  }
  if (item.mode === "walk") {
    return Footprints;
  }
  return Coffee;
}
