import { ChevronLeft } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AppScreenShell } from "./AppScreenShell";
import { AppBackdrop } from "./AppUi";
import { EmbeddedStatusBarImage } from "./EmbeddedStatusBar";
import { FIGMA_USER_SETTINGS_114 } from "../lib/api/mock/figma-user-settings-114-assets";
import { PROFILE_PATH } from "../routes";

/** 与用户中心 Figma 114:* 子页一致：渐变底、blob、状态栏、顶栏 */
export function UserSettingsChrome({
  travelId,
  planId,
  navTitle,
  navSubtitle,
  backLabel = "返回",
  statusBarSrc,
  children,
  footer,
}: {
  travelId: string;
  planId: string;
  navTitle: string;
  navSubtitle?: string | null;
  backLabel?: string;
  /** 有数据时用接口字段，加载中用稿面默认条 */
  statusBarSrc?: string | null;
  children: ReactNode;
  footer?: ReactNode;
}): JSX.Element {
  const flow = { travelId, planId };

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />

      <EmbeddedStatusBarImage
        src={statusBarSrc ?? FIGMA_USER_SETTINGS_114.statusBar}
        className="relative z-[2]"
        height={61}
        width={402}
      />

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-4 pb-5 pt-2">
        <header className="mb-4 shrink-0">
          <div className="flex items-center gap-2">
            <Link
              to={PROFILE_PATH}
              state={flow}
              className="flex min-h-11 shrink-0 items-center gap-0.5 rounded-full bg-white/86 py-0 pl-2 pr-3 text-[#475569] shadow-[0_6px_18px_rgba(15,23,42,0.07)] transition active:scale-95"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
              <span className="text-[14px] font-semibold">{backLabel}</span>
            </Link>
            <div className="min-w-0 flex-1 text-center">
              <h1 className="text-[18px] font-bold leading-6 text-[#111827]">
                {navTitle}
              </h1>
            </div>
            <span className="w-[4.5rem] shrink-0" aria-hidden />
          </div>
          {navSubtitle ? (
            <p className="mt-2 text-center text-[12px] font-semibold leading-5 text-[#64748b]">
              {navSubtitle}
            </p>
          ) : null}
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto pb-3">{children}</div>

        {footer}
      </div>
    </AppScreenShell>
  );
}

/** 与 150:471「我的」卡片同系：浅金描边白底 */
export const userSettingsCardClass =
  "overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0_8px_24px_rgba(15,23,42,0.06)]";

/** 分区标题行左侧图标衬底（用户中心金色体系） */
export function UserSettingsIconWrap({ children }: { children: ReactNode }): JSX.Element {
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#edf5ff] text-[#2456a6]">
      {children}
    </span>
  );
}
