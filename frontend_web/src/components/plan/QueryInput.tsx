import { Loader2, MapPin, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "../common/button";
import { Card, CardBody } from "../common/card";
import { FieldLabel, TextArea } from "../common/field";
import type { PlanPreviewRequest } from "../../types/plan";

interface QueryInputProps {
  value: PlanPreviewRequest;
  disabled: boolean;
  isPlanning: boolean;
  onChange: (next: PlanPreviewRequest) => void;
  onSubmit: () => void;
}

const exampleQueries = [
  "今天下午想和老婆孩子出去玩几小时",
  "周末想和朋友出去喝咖啡拍照",
  "想带老人和孩子去公园走走",
];

const cityOptions = ["深圳", "广州", "上海", "北京"];
const durationOptions = Array.from({ length: 12 }, (_, index) => (index + 1) * 60);

export function QueryInput({
  value,
  disabled,
  isPlanning,
  onChange,
  onSubmit,
}: QueryInputProps) {
  return (
    <Card className="dark:border-slate-700 dark:bg-slate-900">
      <CardBody className="space-y-4">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_160px] lg:items-end">
          <div className="space-y-2">
            <FieldLabel htmlFor="query" className="dark:text-slate-200">
              描述你的周末计划
            </FieldLabel>
            <TextArea
              id="query"
              disabled={disabled}
              placeholder="例如：今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁"
              value={value.query}
              onChange={(event) => onChange({ ...value, query: event.target.value })}
              className="min-h-24 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>
          <Button
            className="h-11 w-full"
            disabled={disabled || value.query.trim().length === 0}
            onClick={onSubmit}
          >
            {isPlanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            开始规划
          </Button>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <SelectField
            label="城市"
            icon={<MapPin className="h-4 w-4" />}
            disabled={disabled}
            value={value.city}
            onChange={(city) => onChange({ ...value, city })}
            options={cityOptions.map((city) => ({ label: city, value: city }))}
          />
          <SelectField
            label="时长"
            disabled={disabled}
            value={String(value.duration_minutes)}
            onChange={(duration) => onChange({ ...value, duration_minutes: Number(duration) })}
            options={durationOptions.map((duration) => ({
              label: `${duration / 60}小时`,
              value: String(duration),
            }))}
          />
          <DateTimeField
            value={value.start_time}
            disabled={disabled}
            onChange={(startTime) => onChange({ ...value, start_time: startTime })}
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((query) => (
            <button
              key={query}
              type="button"
              disabled={disabled}
              className="rounded-md border border-border bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300"
              onClick={() => onChange({ ...value, query })}
            >
              {query}
            </button>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

function SelectField({
  label,
  value,
  options,
  disabled,
  icon,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ label: string; value: string }>;
  disabled: boolean;
  icon?: ReactNode;
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-2">
      <span className="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
        {icon}
        {label}
      </span>
      <select
        disabled={disabled}
        value={value}
        className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-teal-100 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function DateTimeField({
  value,
  disabled,
  onChange,
}: {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">开始时间</span>
      <input
        type="datetime-local"
        disabled={disabled}
        value={value.slice(0, 16)}
        className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-teal-100 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
        onChange={(event) => onChange(`${event.target.value}:00`)}
      />
    </label>
  );
}
