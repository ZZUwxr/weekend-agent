import type { ReactNode } from "react";

interface AppShellProps {
  header: ReactNode;
  children: ReactNode;
}

export function AppShell({ header, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-ink dark:bg-slate-950 dark:text-slate-100">
      {header}
      <main className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-6 sm:px-6">
        {children}
      </main>
    </div>
  );
}
