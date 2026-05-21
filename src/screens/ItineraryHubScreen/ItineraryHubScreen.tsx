import {
  Bell,
  Calendar,
  Check,
  ChevronRight,
  ClipboardList,
  Map as MapIcon,
  MapPin,
  Pencil,
  Share2,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { JourneyBottomNav } from "../../components/JourneyBottomNav";
import {
  tabScreenComposerDockMtAutoClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { useTripContentUnlocked } from "../../hooks/useTripContentUnlocked";
import { fetchItineraryHubPage } from "../../lib/api";
import { FIGMA_ITINERARY_HUB_111_1754 } from "../../lib/api/mock/figma-itinerary-hub-111-1754-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { cn } from "../../lib/utils";
import type { ItineraryHubPageDto, ItineraryHubQuickActionDto } from "../../lib/api/types";
import {
  CHAT_PATH,
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PLANS_PATH,
  TIMELINE_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../../routes";
import { ItineraryHubEmptyView } from "./ItineraryHubEmptyView";

type HubLocationState = { travelId?: string; planId?: string };

function StarRow({ n }: { n: number }): JSX.Element {
  return (
    <span className="text-[11px] text-amber-400" aria-label={`${n} 星`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i}>{i <= n ? "★" : "☆"}</span>
      ))}
    </span>
  );
}

function QuickActionButton({
  action,
  flow,
}: {
  action: ItineraryHubQuickActionDto;
  flow: { travelId: string; planId: string };
}): JSX.Element {
  const shell =
    "flex h-[4.25rem] w-full flex-col items-center justify-center gap-1 rounded-xl border-[0.76px] border-[#faf2ac] bg-[#fffef8] shadow-[0px_1px_6px_rgba(0,0,0,0.04)] transition-opacity hover:opacity-90 active:scale-[0.98]";
  const labelCls =
    "[font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#334155]";
  const iconAmber = "h-5 w-5 text-[#ca8a04]";
  const iconRed = "h-5 w-5 text-red-500";

  if (action.kind === "map") {
    return (
      <Link to={TRIP_LIVE_MAP_PATH} state={flow} className={shell}>
        <MapIcon className={iconAmber} strokeWidth={1.75} />
        <span className={labelCls}>{action.label}</span>
      </Link>
    );
  }

  const Icon =
    action.kind === "share"
      ? Share2
      : action.kind === "calendar"
        ? Calendar
        : action.kind === "edit"
          ? Pencil
          : XCircle;
  const cls = action.kind === "cancel" ? iconRed : iconAmber;

  return (
    <button type="button" className={shell}>
      <Icon className={cls} strokeWidth={1.75} />
      <span className={action.kind === "cancel" ? `${labelCls} text-red-600` : labelCls}>
        {action.label}
      </span>
    </button>
  );
}

function SectionSparkle(): JSX.Element {
  return (
    <Sparkles className="h-4 w-4 shrink-0 text-[#eab308] drop-shadow-[0_0_8px_rgba(234,179,8,0.55)]" strokeWidth={1.75} />
  );
}

export const ItineraryHubScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as HubLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<ItineraryHubPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hubVoiceText, setHubVoiceText] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === ITINERARY_HUB_PATH) {
      document.title = "行程 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  const unlocked = useTripContentUnlocked();

  useEffect(() => {
    if (!unlocked) {
      setPage(null);
      setLoadError(null);
      return;
    }
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchItineraryHubPage(travelId, planId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, [travelId, planId, unlocked]);

  const flow = { travelId, planId };

  if (!unlocked) {
    return <ItineraryHubEmptyView travelId={travelId} planId={planId} />;
  }

  const statusBarSrc = page?.statusBarImageUrl ?? FIGMA_ITINERARY_HUB_111_1754.statusBar;

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffbeb_0%,#fffef9_38%,#ffffff_100%)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_ITINERARY_HUB_111_1754.bgBlobB}
          alt=""
          className="absolute -left-[100px] top-[42%] h-[760px] w-[1080px] max-w-none opacity-[0.06]"
        />
      </div>

      <EmbeddedStatusBarImage src={statusBarSrc} className="relative z-[2]" height={61} width={402} />

      <div
        className={cn(
          "relative z-[1] flex min-h-0 flex-1 flex-col pb-2 pt-2",
          tabScreenPrimaryColumnPaddingXClass,
        )}
      >
        <header className="mb-3 flex shrink-0 items-center justify-between gap-2">
          <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-bold text-[#1e293b]">
            {page?.navTitle ?? "行程"}
          </h1>
          {page?.showNotificationsBell ? (
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

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ContentFitZoom
            className="space-y-3 pb-2"
            recalcKey={
              page
                ? `${page.timelineNodes.length}:${page.historyItems.length}:${page.quickActions.map((a) => a.id).join(",")}`
                : ""
            }
          >
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
            ) : (
              <>
                {/* Figma 111:1754 · 今日行程 + 时间轴（单卡黄头白身） */}
                <div className="overflow-hidden rounded-[18px] border-[0.76px] border-[#faf2ac] bg-white shadow-[0px_6px_24px_rgba(15,23,42,0.06)]">
                  <div className="bg-[linear-gradient(95deg,#fde047_0%,#fef08a_42%,#fef9c3_100%)] px-4 py-3.5">
                    <div className="flex items-start gap-2.5">
                      <SectionSparkle />
                      <div className="min-w-0 flex-1">
                        <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-bold leading-tight text-[#1e293b]">
                          今日行程
                        </p>
                        <div className="mt-1 flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 shrink-0 text-[#ca8a04]" strokeWidth={1.75} />
                          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#ca8a04]">
                            {page.overviewTimeRange}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#334155]">
                          {page.overviewFlowChips.map((c, idx) => (
                            <span key={c.id} className="inline-flex items-center gap-1">
                              {idx > 0 ? <span className="text-[#94a3b8]">→</span> : null}
                              <span className="text-base leading-none">{c.iconEmoji}</span>
                              <span>{c.label}</span>
                            </span>
                          ))}
                        </div>
                        <p className="mt-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#92400e]/90">
                          {page.overviewFooterLine}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-[#fef3c7] bg-white px-3 pb-3 pt-3">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="flex min-w-0 items-center gap-2">
                        <MapPin className="h-4 w-4 shrink-0 text-[#ca8a04]" strokeWidth={1.75} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                          {page.currentStageTitle}
                        </span>
                      </div>
                      <span className="shrink-0 rounded-full bg-[#fef3c7] px-2.5 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#92400e]">
                        {page.currentStageStatusBadge}
                      </span>
                    </div>

                    <ul className="relative space-y-0">
                      {page.timelineNodes.map((node, index) => {
                        const isLast = index === page.timelineNodes.length - 1;
                        const contentInner = (
                          <>
                            <div className="flex items-baseline gap-2">
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#0f172a]">
                                {node.time}
                              </span>
                              <span className="text-base leading-none">{node.iconEmoji}</span>
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#334155]">
                                {node.title}
                              </span>
                            </div>
                            {node.subtitle ? (
                              <p className="mt-0.5 pl-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-medium text-[#64748b]">
                                🕐 {node.subtitle}
                              </p>
                            ) : null}
                          </>
                        );

                        return (
                          <li key={node.id} className="relative flex gap-3">
                            <div className="flex w-8 shrink-0 flex-col items-center pt-0.5">
                              {node.kind === "done" ? (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white shadow-sm">
                                  <Check className="h-3.5 w-3.5" strokeWidth={2.5} />
                                </span>
                              ) : node.kind === "active" ? (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#eab308] text-sm shadow-sm">
                                  {node.iconEmoji}
                                </span>
                              ) : (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-[#fde68a] bg-white text-sm">
                                  {node.iconEmoji}
                                </span>
                              )}
                              {!isLast ? (
                                <div className="mt-0.5 min-h-[1.25rem] w-0.5 flex-1 bg-[#fde68a]/70" />
                              ) : null}
                            </div>
                            <div className={`min-w-0 flex-1 ${!isLast ? "pb-3" : ""}`}>
                              {node.kind === "active" ? (
                                <div className="rounded-xl border border-[#fde68a] bg-[#fffbeb] px-3 py-2 shadow-sm">
                                  {contentInner}
                                </div>
                              ) : (
                                <div
                                  className={
                                    node.kind === "upcoming" ? "rounded-lg py-0.5 opacity-95" : "py-0.5"
                                  }
                                >
                                  {contentInner}
                                </div>
                              )}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>

                <div className="grid grid-cols-5 gap-2">
                  {page.quickActions.map((a) => (
                    <QuickActionButton key={a.id} action={a} flow={flow} />
                  ))}
                </div>

                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <SectionSparkle />
                    <ClipboardList className="h-4 w-4 text-[#ca8a04]" strokeWidth={1.75} />
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                      {page.historySectionTitle}
                    </h2>
                  </div>
                  <div className="space-y-2.5">
                    {page.historyItems.map((item) => (
                      <div
                        key={item.id}
                        className="flex gap-2.5 rounded-[14px] border-[0.76px] border-[#faf2ac] bg-[#fffef9] p-2.5 shadow-[0px_2px_8px_rgba(0,0,0,0.04)]"
                      >
                        <div className="flex h-[4.5rem] w-[4.5rem] shrink-0 items-center justify-center overflow-hidden rounded-xl bg-[#fef3c7]/40 text-2xl">
                          {item.thumbImageUrl ? (
                            <img
                              src={item.thumbImageUrl}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <span>{item.thumbEmoji ?? "📷"}</span>
                          )}
                        </div>
                        <div className="flex min-w-0 flex-1 flex-col justify-between py-0.5">
                          <div>
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#64748b]">
                              {item.dateLine}
                            </p>
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#1e293b]">
                              {item.routeSummary}
                            </p>
                            <div className="mt-0.5 flex flex-wrap items-center gap-2">
                              <StarRow n={item.ratingStars} />
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#ea580c]">
                                {item.priceText}
                              </span>
                            </div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            <Link
                              to={TIMELINE_PATH}
                              state={flow}
                              className="rounded-lg border-[0.76px] border-[#fde68a] bg-white px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#b45309] hover:bg-[#fffbeb]"
                            >
                              查看详情
                            </Link>
                            <Link
                              to={PLANS_PATH}
                              state={flow}
                              className="rounded-lg bg-[#ffd100] px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#78350f] shadow-[0px_2px_6px_rgba(245,200,20,0.35)] hover:opacity-95"
                            >
                              再来一次
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Link
                  to={PAYMENT_CONFIRMATION_PATH}
                  state={flow}
                  className="inline-flex text-[11px] font-medium text-[#64748b] underline-offset-2 hover:text-[#ca8a04] hover:underline"
                >
                  上一屏：支付确认
                </Link>
              </>
            )}
          </ContentFitZoom>

          <div className={tabScreenComposerDockMtAutoClass}>
            <div className="flex min-w-0 items-center gap-2">
              <div className="relative flex min-h-[46px] min-w-0 flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
                <img
                  src={FIGMA_ITINERARY_HUB_111_1754.voiceInput}
                  alt=""
                  className="h-7 w-[34px] shrink-0 object-contain"
                  height={28}
                  width={34}
                />
                <input
                  type="text"
                  value={hubVoiceText}
                  onChange={(e) => setHubVoiceText(e.target.value)}
                  placeholder="有疑问可以在这里补充…"
                  className="min-w-0 flex-1 bg-transparent py-2 pl-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#333c4380]"
                />
              </div>
              <Link
                to={CHAT_PATH}
                state={{ message: hubVoiceText.trim() || "我想继续调整行程", travelId }}
                aria-label="进入对话"
                className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} />
              </Link>
            </div>

            <JourneyBottomNav active="行程" travelId={travelId} planId={planId} />
          </div>
        </div>
      </div>
    </AppScreenShell>
  );
};
