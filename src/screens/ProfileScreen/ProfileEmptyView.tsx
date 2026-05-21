import {
  Bell,
  Car,
  ChevronRight,
  HelpCircle,
  Leaf,
  MapPin,
  Sparkles,
  Utensils,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";
import { JourneyBottomNav } from "../../components/JourneyBottomNav";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { FIGMA_PROFILE_150_471 } from "../../lib/api/mock/figma-profile-150-471-assets";
import type { ProfilePageDto, ProfilePreferenceRowDto } from "../../lib/api/types";
import { cn } from "../../lib/utils";
import {
  ACTIVITY_PREFERENCES_PATH,
  BUDGET_PACE_PREFERENCES_PATH,
  CHAT_PATH,
  DIETARY_PREFERENCES_PATH,
  TRAVEL_MODE_SETTINGS_PATH,
} from "../../routes";

type Props = { travelId: string; planId: string };

/** 与稿面一致：浅金描边 + 白底圆角卡（p2 · 初始 / 解锁共用） */
export const PROFILE_GOLD_CARD_CLASS =
  "rounded-[16px] border-[0.76px] border-[#faf2ac] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.05)]";

const linkAccent =
  "[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#b45309] hover:text-[#92400e]";

export function PrefIcon({ row }: { row: ProfilePreferenceRowDto }): JSX.Element {
  switch (row.kind) {
    case "car":
      return <Car className="h-4 w-4 shrink-0 text-[#2563eb]" strokeWidth={1.75} />;
    case "food":
      return <Utensils className="h-4 w-4 shrink-0 text-[#ea580c]" strokeWidth={1.75} />;
    case "activity":
      return <Leaf className="h-4 w-4 shrink-0 text-[#16a34a]" strokeWidth={1.75} />;
    default:
      return <Wallet className="h-4 w-4 shrink-0 text-[#9333ea]" strokeWidth={1.75} />;
  }
}

export type ProfileP2ViewProps = {
  travelId: string;
  planId: string;
  /** locked = 未解锁 Jack 稿；unlocked = 与 p2 同结构，填充接口数据 */
  mode: "locked" | "unlocked";
  /** 仅 unlocked 使用；loading 时为 null */
  page: ProfilePageDto | null;
  loadError?: string | null;
};

/**
 * Figma p2：三卡（用户 / ✨出行档案 / ✨记忆与偏好四行）+ 底栏输入 + JourneyBottomNav。
 * 不使用 p1 的独立「出行偏好」卡、记忆三行、模板区、底栏四快捷。
 */
export function ProfileP2View({ travelId, planId, mode, page, loadError }: ProfileP2ViewProps): JSX.Element {
  const flow = { travelId, planId };
  const statusBarSrc =
    mode === "unlocked" ? (page?.statusBarImageUrl ?? FIGMA_PROFILE_150_471.statusBar) : FIGMA_PROFILE_150_471.statusBar;

  const showBell = mode === "locked" || page?.showNotificationsBell;
  const navTitle = mode === "locked" ? "我的" : (page?.navTitle ?? "我的");

  const memoryRowsStatic: { to: string; label: string; icon: JSX.Element }[] = [
    {
      to: TRAVEL_MODE_SETTINGS_PATH,
      label: "出行方式与距离",
      icon: <Car className="h-4 w-4 shrink-0 text-[#2563eb]" strokeWidth={1.75} />,
    },
    {
      to: DIETARY_PREFERENCES_PATH,
      label: "饮食偏好",
      icon: <Utensils className="h-4 w-4 shrink-0 text-[#ea580c]" strokeWidth={1.75} />,
    },
    {
      to: ACTIVITY_PREFERENCES_PATH,
      label: "活动偏好",
      icon: <Leaf className="h-4 w-4 shrink-0 text-[#16a34a]" strokeWidth={1.75} />,
    },
    {
      to: BUDGET_PACE_PREFERENCES_PATH,
      label: "预算与节奏",
      icon: <Wallet className="h-4 w-4 shrink-0 text-[#9333ea]" strokeWidth={1.75} />,
    },
  ];

  function preferenceRowClass(i: number, len: number): string {
    return `flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[#fafafa] ${
      i < len - 1 ? "border-b border-[#f3f4f6]" : ""
    }`;
  }

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffbeb_0%,#fffef9_38%,#ffffff_100%)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_PROFILE_150_471.bgBlobA}
          alt=""
          className="absolute -left-[320px] -top-[280px] h-[795px] w-[1293px] max-w-none opacity-[0.35]"
        />
        <img
          src={FIGMA_PROFILE_150_471.bgBlobB}
          alt=""
          className="absolute -left-[100px] top-[120px] h-[1046px] w-[1507px] max-w-none opacity-[0.32]"
        />
      </div>

      <EmbeddedStatusBarImage src={statusBarSrc} className="relative z-[2]" height={61} width={402} />

      <div
        className={cn(
          "relative z-[1] flex min-h-0 flex-1 flex-col pb-2 pt-2",
          tabScreenPrimaryColumnPaddingXClass,
        )}
      >
        <header className="mb-3 flex items-center justify-between gap-2">
          <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-bold text-[#1e293b]">
            {navTitle}
          </h1>
          {showBell ? (
            <button
              type="button"
              aria-label="通知"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#64748b] hover:bg-black/[0.04]"
            >
              <Bell className="h-5 w-5" strokeWidth={1.75} />
            </button>
          ) : (
            <span className="w-10 shrink-0" />
          )}
        </header>

        <ContentFitZoom
          className="space-y-3 pb-2"
          recalcKey={`${mode}:${page?.preferenceRows?.map((r) => r.id).join(",") ?? ""}:${page?.archiveTags?.map((t) => t.id).join(",") ?? ""}`}
        >
          {mode === "locked" ? (
            <>
              <section className={`${PROFILE_GOLD_CARD_CLASS} p-4`}>
                <div className="flex items-center gap-3">
                  <div className="flex h-[56px] w-[56px] shrink-0 items-center justify-center rounded-full bg-[#ffd100] shadow-[0_2px_8px_rgba(245,200,20,0.35)]">
                    <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[28px] leading-none" aria-hidden>
                      🧑‍💼
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[17px] font-bold leading-tight text-[#1e293b]">
                      Jack
                    </p>
                    <p className="mt-1 flex items-center gap-1 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#94a3b8]">
                      <MapPin className="h-3.5 w-3.5 shrink-0 text-[#eab308]" strokeWidth={2} />
                      <span>默认起点：暂无</span>
                    </p>
                  </div>
                </div>
              </section>

              <section className={`${PROFILE_GOLD_CARD_CLASS} px-4 pb-4 pt-3`}>
                <div className="mb-3 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 shrink-0 text-[#f5c814]" strokeWidth={1.75} />
                  <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#1e293b]">
                    我的出行档案
                  </h2>
                </div>
                <Link
                  to={CHAT_PATH}
                  state={{ message: "我想添加出行档案成员", travelId }}
                  className="inline-flex min-h-[36px] min-w-[48px] items-center justify-center rounded-[10px] border-[0.5px] border-[#bfdbfe] bg-gradient-to-b from-white to-[#eff6ff] px-5 py-1.5 shadow-[0px_1px_4px_rgba(147,197,253,0.45)] transition-opacity hover:opacity-90"
                  aria-label="添加出行档案"
                >
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-light leading-none text-[#475569]">
                    +
                  </span>
                </Link>
              </section>

              <section className={`${PROFILE_GOLD_CARD_CLASS} overflow-hidden`}>
                <div className="flex items-center justify-between border-b border-[#f3f4f6] px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 shrink-0 text-[#f5c814]" strokeWidth={1.75} />
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#1e293b]">
                      记忆与偏好
                    </h2>
                  </div>
                  <button
                    type="button"
                    aria-label="说明"
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#f3f4f6] text-[#9ca3af]"
                  >
                    <HelpCircle className="h-4 w-4" strokeWidth={1.5} />
                  </button>
                </div>
                <div className="px-0 pb-1">
                  {memoryRowsStatic.map((row, i) => (
                    <Link
                      key={row.label}
                      to={row.to}
                      state={flow}
                      className={`flex items-center gap-3 px-4 py-3 transition-colors hover:bg-[#fafafa] ${
                        i < memoryRowsStatic.length - 1 ? "border-b border-[#f3f4f6]" : ""
                      }`}
                    >
                      {row.icon}
                      <span className="min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#334155]">
                        {row.label}
                      </span>
                      <span className="shrink-0 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#9ca3af]">
                        暂无
                      </span>
                      <ChevronRight className="h-4 w-4 shrink-0 text-[#cbd5e1]" strokeWidth={1.75} />
                    </Link>
                  ))}
                </div>
              </section>
            </>
          ) : loadError ? (
            <p className="text-center text-[13px] text-red-600">{loadError}</p>
          ) : !page ? (
            <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
          ) : (
            <>
              <Link
                to={CHAT_PATH}
                state={{
                  message: "我想完善我的个人资料与起点设置",
                  travelId,
                }}
                className={`flex w-full items-center gap-3 p-4 text-left transition-opacity hover:opacity-95 active:scale-[0.99] ${PROFILE_GOLD_CARD_CLASS}`}
              >
                <div
                  className={`flex h-[56px] w-[56px] shrink-0 items-center justify-center overflow-hidden rounded-full text-[28px] leading-none ${
                    page.avatarImageUrl
                      ? "ring-2 ring-[#fde68a] ring-offset-2 ring-offset-white"
                      : "bg-[#ffd100] shadow-[0_2px_8px_rgba(245,200,20,0.35)]"
                  }`}
                >
                  {page.avatarImageUrl ? (
                    <img src={page.avatarImageUrl} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <span aria-hidden>{page.avatarEmoji ?? "👤"}</span>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[17px] font-bold leading-tight text-[#1e293b]">
                    {page.userName}
                  </p>
                  <p className="mt-1 flex items-center gap-1 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#94a3b8]">
                    <MapPin className="h-3.5 w-3.5 shrink-0 text-[#eab308]" strokeWidth={2} />
                    <span>{page.defaultStartLine}</span>
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 shrink-0 text-[#cbd5e1]" strokeWidth={1.75} />
              </Link>

              <section className={`${PROFILE_GOLD_CARD_CLASS} px-4 pb-4 pt-3`}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <Sparkles className="h-4 w-4 shrink-0 text-[#f5c814]" strokeWidth={1.75} />
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#1e293b]">
                      {page.archiveSectionTitle}
                    </h2>
                  </div>
                  {page.archiveTags.length > 0 ? (
                    <Link
                      to={CHAT_PATH}
                      state={{
                        message: "我想编辑我的出行档案信息",
                        travelId,
                      }}
                      className={`shrink-0 ${linkAccent}`}
                    >
                      {page.archiveEditLabel}
                    </Link>
                  ) : null}
                </div>
                {page.archiveTags.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {page.archiveTags.map((tag) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center gap-1 rounded-full bg-[#fef3c7] px-3 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#92400e]"
                      >
                        <span>{tag.iconEmoji}</span>
                        {tag.label}
                      </span>
                    ))}
                  </div>
                ) : (
                  <Link
                    to={CHAT_PATH}
                    state={{ message: "我想添加出行档案成员", travelId }}
                    className="inline-flex min-h-[36px] min-w-[48px] items-center justify-center rounded-[10px] border-[0.5px] border-[#bfdbfe] bg-gradient-to-b from-white to-[#eff6ff] px-5 py-1.5 shadow-[0px_1px_4px_rgba(147,197,253,0.45)] transition-opacity hover:opacity-90"
                    aria-label="添加出行档案"
                  >
                    <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-light leading-none text-[#475569]">
                      +
                    </span>
                  </Link>
                )}
              </section>

              <section className={`${PROFILE_GOLD_CARD_CLASS} overflow-hidden`}>
                <div className="flex items-center justify-between border-b border-[#f3f4f6] px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 shrink-0 text-[#f5c814]" strokeWidth={1.75} />
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#1e293b]">
                      {page.memorySectionTitle}
                    </h2>
                  </div>
                  <button
                    type="button"
                    aria-label="说明"
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#f3f4f6] text-[#9ca3af]"
                  >
                    <HelpCircle className="h-4 w-4" strokeWidth={1.5} />
                  </button>
                </div>
                <div className="px-0 pb-1">
                  {page.preferenceRows.map((row, i) => {
                    const inner = (
                      <>
                        <PrefIcon row={row} />
                        <div className="min-w-0 flex-1">
                          <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#334155]">
                            {row.title}
                          </p>
                          <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] text-[#94a3b8]">
                            {row.summary?.trim() ? row.summary : "暂无"}
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 shrink-0 text-[#cbd5e1]" strokeWidth={1.75} />
                      </>
                    );
                    const cls = `${preferenceRowClass(i, page.preferenceRows.length)} cursor-pointer`;
                    if (row.kind === "car") {
                      return (
                        <Link key={row.id} to={TRAVEL_MODE_SETTINGS_PATH} state={flow} className={cls}>
                          {inner}
                        </Link>
                      );
                    }
                    if (row.kind === "food") {
                      return (
                        <Link key={row.id} to={DIETARY_PREFERENCES_PATH} state={flow} className={cls}>
                          {inner}
                        </Link>
                      );
                    }
                    if (row.kind === "activity") {
                      return (
                        <Link key={row.id} to={ACTIVITY_PREFERENCES_PATH} state={flow} className={cls}>
                          {inner}
                        </Link>
                      );
                    }
                    if (row.kind === "budget") {
                      return (
                        <Link key={row.id} to={BUDGET_PACE_PREFERENCES_PATH} state={flow} className={cls}>
                          {inner}
                        </Link>
                      );
                    }
                    return (
                      <button key={row.id} type="button" className={cls}>
                        {inner}
                      </button>
                    );
                  })}
                </div>
              </section>
            </>
          )}
        </ContentFitZoom>

        <div className={tabScreenComposerDockClass}>
        <div className="relative flex min-h-[42px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white px-2 shadow-[0px_2px_8px_#00000008]">
            <span className="min-w-0 flex-1 px-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] text-[#94a3b8]">
              有疑问可以在这里补充…
            </span>
            <Link
              to={CHAT_PATH}
              state={{ travelId, planId }}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white"
              aria-label="进入对话"
            >
              <ChevronRight className="h-4 w-4" strokeWidth={2} />
            </Link>
          </div>
        <JourneyBottomNav active="我的" travelId={travelId} planId={planId} />
        </div>
      </div>
    </AppScreenShell>
  );
}

/** 未解锁：p2 初始稿（Jack） */
export function ProfileEmptyView({ travelId, planId }: Props): JSX.Element {
  return <ProfileP2View mode="locked" page={null} travelId={travelId} planId={planId} />;
}
