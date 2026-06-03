import type { ReactNode } from "react";
import { cn } from "../lib/utils";

/** 内层白框：flex 列 + 固定区域滚动；高度依赖外层 #app 满屏 */
const FRAME_BASE =
  "relative flex h-full min-h-0 w-full flex-col overflow-hidden";

type AppScreenShellProps = {
  children: ReactNode;
  /** 手机屏幕内背景；默认白底，传渐变色等会覆盖默认白底 */
  frameClassName?: string;
};

/** 全站统一的「手机框」：宽 max 402，高度铺满 #app（WebView 内核滚动在子层 overflow-y-auto） */
export function AppScreenShell({ children, frameClassName }: AppScreenShellProps): JSX.Element {
  return (
    <main className="box-border flex h-full min-h-0 w-full">
      <div className={cn(FRAME_BASE, "bg-white", frameClassName)}>{children}</div>
    </main>
  );
}
