import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "success" | "warning" | "danger";
}

const toneClass: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-slate-100 text-slate-700",
  success: "bg-teal-50 text-teal-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
};

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-full px-2.5 text-xs font-medium",
        toneClass[tone],
        className,
      )}
      {...props}
    />
  );
}
