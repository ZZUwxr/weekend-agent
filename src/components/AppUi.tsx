import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ArrowLeft, SendHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../lib/utils";

type Tone = "dark" | "blue" | "gold" | "green" | "muted";

const toneClasses: Record<Tone, string> = {
  dark: "bg-[#111827] text-white shadow-[0_10px_22px_rgba(17,24,39,0.22)]",
  blue: "bg-[#2456a6] text-white shadow-[0_10px_22px_rgba(36,86,166,0.2)]",
  gold: "bg-[#ffd95a] text-[#3f3421] shadow-[0_10px_22px_rgba(234,179,8,0.22)]",
  green: "bg-[#0f766e] text-white shadow-[0_10px_22px_rgba(15,118,110,0.18)]",
  muted: "bg-[#f1f5f9] text-[#334155] shadow-[0_6px_18px_rgba(15,23,42,0.06)]",
};

export function AppBackdrop({ className }: { className?: string }): JSX.Element {
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
      <div className="absolute inset-0 bg-[linear-gradient(180deg,#eef5ff_0%,#f8fafc_52%,#fff8e6_100%)]" />
      <div className="absolute inset-x-0 top-0 h-32 bg-[linear-gradient(180deg,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0)_100%)]" />
      <div className="absolute inset-x-0 bottom-0 h-36 bg-[linear-gradient(0deg,rgba(255,255,255,0.86)_0%,rgba(255,255,255,0)_100%)]" />
    </div>
  );
}

export function AppIconButton({
  children,
  className,
  label,
  onClick,
  to,
  state,
}: {
  children?: ReactNode;
  className?: string;
  label: string;
  onClick?: () => void;
  to?: string;
  state?: unknown;
}): JSX.Element {
  const classes = cn(
    "flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-white/75 bg-white/86 text-[#111827] shadow-[0_6px_18px_rgba(15,23,42,0.08)] backdrop-blur transition active:scale-95",
    className,
  );
  if (to) {
    return (
      <Link to={to} state={state} className={classes} aria-label={label}>
        {children ?? <ArrowLeft className="h-5 w-5" strokeWidth={2.1} />}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className={classes} aria-label={label}>
      {children ?? <ArrowLeft className="h-5 w-5" strokeWidth={2.1} />}
    </button>
  );
}

export function AppPageHeader({
  title,
  subtitle,
  eyebrow,
  action,
  className,
}: {
  title: string;
  subtitle?: string | null;
  eyebrow?: string | null;
  action?: ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <header className={cn("flex shrink-0 items-start justify-between gap-3", className)}>
      <div className="min-w-0 flex-1">
        {eyebrow ? (
          <p className="text-[12px] font-semibold leading-5 text-[#64748b]">{eyebrow}</p>
        ) : null}
        <h1 className="text-[26px] font-bold leading-[1.12] tracking-[0] text-[#111827]">
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-2 text-[13px] font-medium leading-5 text-[#64748b]">{subtitle}</p>
        ) : null}
      </div>
      {action}
    </header>
  );
}

export function AppCard({
  children,
  className,
  as = "section",
}: {
  children: ReactNode;
  className?: string;
  as?: "article" | "section" | "div";
}): JSX.Element {
  const Component = as;
  return (
    <Component
      className={cn(
        "rounded-[16px] border border-[#e5e7eb] bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.06)]",
        className,
      )}
    >
      {children}
    </Component>
  );
}

export function AppPill({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex min-h-7 items-center rounded-full bg-[#f1f5f9] px-3 text-[11px] font-semibold leading-none text-[#475569]",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function AppActionButton({
  children,
  className,
  disabled,
  Icon,
  onClick,
  tone = "dark",
  type = "button",
}: {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  Icon?: LucideIcon;
  onClick?: () => void;
  tone?: Tone;
  type?: "button" | "submit";
}): JSX.Element {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex min-h-11 w-full items-center justify-center gap-2 rounded-[12px] px-4 text-[14px] font-semibold transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-55",
        toneClasses[tone],
        className,
      )}
    >
      {children}
      {Icon ? <Icon className="h-4 w-4" strokeWidth={2.2} /> : null}
    </button>
  );
}

export function AppStatusStrip({
  title,
  detail,
  Icon,
  className,
}: {
  title: string;
  detail?: string | null;
  Icon?: LucideIcon;
  className?: string;
}): JSX.Element {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-[14px] border border-[#dbeafe] bg-white/90 px-3 py-3 shadow-[0_6px_18px_rgba(37,99,235,0.08)]",
        className,
      )}
    >
      {Icon ? (
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
          <Icon className="h-4 w-4" strokeWidth={2.1} />
        </span>
      ) : null}
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-bold leading-5 text-[#111827]">{title}</p>
        {detail ? <p className="mt-0.5 text-[12px] leading-5 text-[#64748b]">{detail}</p> : null}
      </div>
    </div>
  );
}

export function AppComposer({
  value,
  onChange,
  onSubmit,
  placeholder,
  pending,
  submitLabel = "发送",
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder: string;
  pending?: boolean;
  submitLabel?: string;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("flex min-w-0 items-center gap-2", className)}>
      <div className="flex min-h-[48px] flex-1 items-center rounded-[16px] border border-[#dbe3ee] bg-white px-4 shadow-[0_6px_18px_rgba(15,23,42,0.06)] focus-within:border-[#94a3b8]">
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onSubmit();
          }}
          disabled={pending}
          placeholder={placeholder}
          className="min-w-0 flex-1 bg-transparent py-3 text-[13px] text-[#1f2937] outline-none placeholder:text-[#94a3b8]"
        />
      </div>
      <button
        type="button"
        aria-label={submitLabel}
        disabled={pending}
        onClick={onSubmit}
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[16px] bg-[#111827] text-white shadow-[0_8px_18px_rgba(17,24,39,0.22)] transition active:scale-95 disabled:opacity-50"
      >
        <SendHorizontal className="h-5 w-5" strokeWidth={2.2} />
      </button>
    </div>
  );
}

export function AppLoadingState({ label = "加载中…" }: { label?: string }): JSX.Element {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center px-6">
      <div className="rounded-[16px] border border-[#e5e7eb] bg-white px-5 py-4 text-[13px] font-semibold text-[#64748b] shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
        {label}
      </div>
    </div>
  );
}

export function AppErrorState({ message }: { message: string }): JSX.Element {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center px-6 text-center">
      <div className="rounded-[16px] border border-red-100 bg-white px-5 py-5 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
        <p className="text-[15px] font-semibold text-[#991b1b]">加载失败</p>
        <p className="mt-2 text-[12px] leading-5 text-[#64748b]">{message}</p>
      </div>
    </div>
  );
}
