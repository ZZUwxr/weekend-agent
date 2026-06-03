import { AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "../lib/utils";

export type RevisionNoticeState = {
  summary: string;
  warnings?: string[];
} | null;

const INTERNAL_WARNING_MARKERS = [
  "violation_type",
  "suggested_repair_action",
  "affected_poi_id",
  "affected_plan_id",
  "planned",
  "api_key",
  "traceback",
  "schema",
  "provider",
];

function stripRevisionReason(text?: string): string {
  if (!text) return "";
  return text
    .split(/[；;]/)
    .map((part) => part.replace(/[。.\s]*原因[:：].*$/u, "").trim())
    .filter(Boolean)
    .join("；")
    .trim();
}

function looksInternalWarning(text: string): boolean {
  const normalized = text.toLowerCase();
  if (
    (text.startsWith("{") && text.endsWith("}")) ||
    (text.startsWith("[") && text.endsWith("]"))
  ) {
    return true;
  }
  if (/['"][a-z_]+['"]\s*:/i.test(text)) return true;
  return INTERNAL_WARNING_MARKERS.some((marker) => normalized.includes(marker));
}

function sanitizeWarnings(warnings?: string[]): string[] {
  const seen = new Set<string>();
  const cleaned: string[] = [];

  for (const warning of warnings ?? []) {
    const raw = String(warning ?? "").trim();
    if (!raw || looksInternalWarning(raw)) continue;

    const text = stripRevisionReason(raw);
    if (!text || seen.has(text)) continue;
    seen.add(text);
    cleaned.push(text);
  }

  return cleaned;
}

export function RevisionNotice({
  notice,
  className,
}: {
  notice: RevisionNoticeState;
  className?: string;
}): JSX.Element | null {
  const summary = stripRevisionReason(notice?.summary);
  const warnings = sanitizeWarnings(notice?.warnings);

  if (!summary && !warnings.length) return null;
  const hasWarnings = Boolean(warnings.length);
  const Icon = hasWarnings ? AlertCircle : CheckCircle2;
  return (
    <div
      className={cn(
        "rounded-[14px] border bg-white px-3 py-3 shadow-[0_6px_18px_rgba(15,23,42,0.06)]",
        hasWarnings ? "border-amber-200" : "border-emerald-100",
        className,
      )}
    >
      <div className="flex items-start gap-2">
        <Icon
          className={cn("mt-0.5 h-4 w-4 shrink-0", hasWarnings ? "text-amber-600" : "text-emerald-600")}
          strokeWidth={2.1}
        />
        <div className="min-w-0 flex-1">
          {summary ? (
            <p className="text-[12px] font-semibold leading-5 text-[#334155]">{summary}</p>
          ) : null}
          {warnings.length ? (
            <div className="mt-1 space-y-0.5">
              {warnings.slice(0, 2).map((warning, index) => (
                <p key={`${warning}-${index}`} className="text-[11px] font-medium leading-4 text-[#92400e]">
                  {warning}
                </p>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
