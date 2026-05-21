import { ChevronLeft } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AppScreenShell } from "./AppScreenShell";
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
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffbeb_0%,#fffef9_38%,#ffffff_100%)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_USER_SETTINGS_114.bgBlobA}
          alt=""
          className="absolute -right-[200px] -top-[220px] h-[720px] w-[1150px] max-w-none opacity-[0.28]"
        />
        <img
          src={FIGMA_USER_SETTINGS_114.bgBlobB}
          alt=""
          className="absolute -left-[140px] top-[32%] h-[900px] w-[1260px] max-w-none opacity-[0.22]"
        />
      </div>

      <EmbeddedStatusBarImage
        src={statusBarSrc ?? FIGMA_USER_SETTINGS_114.statusBar}
        className="relative z-[2]"
        height={61}
        width={402}
      />

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-4 pb-6 pt-2">
        <header className="mb-3 shrink-0">
          <div className="flex items-center gap-1">
            <Link
              to={PROFILE_PATH}
              state={flow}
              className="flex shrink-0 items-center gap-0.5 text-[#475569] transition-opacity hover:opacity-80"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium">{backLabel}</span>
            </Link>
            <div className="min-w-0 flex-1 text-center">
              <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-bold text-[#1e293b]">
                {navTitle}
              </h1>
            </div>
            <span className="w-[4.5rem] shrink-0" aria-hidden />
          </div>
          {navSubtitle ? (
            <p className="mt-1 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#64748b]">
              {navSubtitle}
            </p>
          ) : null}
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{children}</div>

        {footer}
      </div>
    </AppScreenShell>
  );
}

/** 与 150:471「我的」卡片同系：浅金描边白底 */
export const userSettingsCardClass =
  "overflow-hidden rounded-[16px] border-[0.76px] border-[#faf2ac] bg-white shadow-[0px_2px_14px_rgba(0,0,0,0.05)]";

/** 分区标题行左侧图标衬底（用户中心金色体系） */
export function UserSettingsIconWrap({ children }: { children: ReactNode }): JSX.Element {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#fff6cc] text-[#ca8a04] shadow-[inset_0_0_0_1px_rgba(234,179,8,0.25)]">
      {children}
    </span>
  );
}
