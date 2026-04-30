import type { InputHTMLAttributes, LabelHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export function FieldLabel({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("text-sm font-medium text-slate-700", className)} {...props} />;
}

export function TextInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-teal-100",
        className,
      )}
      {...props}
    />
  );
}

export function TextArea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-28 w-full resize-none rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-teal-100",
        className,
      )}
      {...props}
    />
  );
}
