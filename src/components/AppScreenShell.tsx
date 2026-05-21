import type { ReactNode } from "react";
import { cn } from "../lib/utils";

/** 内层白框：flex 列 + 固定区域滚动；高度依赖外层 #app 满屏 */
const FRAME_BASE =
  "relative flex h-full min-h-0 w-full max-w-[402px] flex-col overflow-hidden shadow-[0_0_1px_rgba(0,0,0,0.06),0_16px_48px_rgba(15,23,42,0.07)]";

type AppScreenShellProps = {
  children: ReactNode;
  /** 手机屏幕内背景；默认白底，传渐变色等会覆盖默认白底 */
  frameClassName?: string;
};

/** 全站统一的「手机框」：宽 max 402，高度铺满 #app（WebView 内核滚动在子层 overflow-y-auto） */
export function AppScreenShell({ children, frameClassName }: AppScreenShellProps): JSX.Element {
  return (
    <main className="box-border flex h-full min-h-0 w-full justify-center bg-[#eceef2]">
      <div className={cn(FRAME_BASE, "bg-white", frameClassName)}>{children}</div>
    </main>
  );
}
