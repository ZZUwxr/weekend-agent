import { useCallback, useEffect, useState } from "react";
import { cn } from "../lib/utils";

export function AppToast({
  message,
  className,
}: {
  message: string | null;
  className?: string;
}): JSX.Element | null {
  if (!message) return null;
  return (
    <div
      className={cn(
        "pointer-events-none fixed inset-x-0 bottom-[calc(env(safe-area-inset-bottom,0px)+92px)] z-[9997] flex justify-center px-6",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <div className="max-w-[22rem] rounded-full bg-[#111827]/92 px-4 py-2.5 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold leading-snug text-white shadow-[0_8px_24px_rgba(15,23,42,0.24)] backdrop-blur">
        {message}
      </div>
    </div>
  );
}

export function useAppToast(durationMs = 1800): {
  toastMessage: string | null;
  showToast: (message: string) => void;
  clearToast: () => void;
} {
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!toastMessage) return undefined;
    const t = window.setTimeout(() => setToastMessage(null), durationMs);
    return () => window.clearTimeout(t);
  }, [durationMs, toastMessage]);

  const showToast = useCallback((message: string) => {
    setToastMessage(message);
  }, []);

  const clearToast = useCallback(() => {
    setToastMessage(null);
  }, []);

  return { toastMessage, showToast, clearToast };
}
