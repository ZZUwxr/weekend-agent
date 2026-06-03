import { Car, ChevronLeft, MapPin, Navigation, Share2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { RevisionNotice, type RevisionNoticeState } from "../../components/RevisionNotice";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import {
  AppActionButton,
  AppCard,
  AppComposer,
  AppPill,
  AppStatusStrip,
} from "../../components/AppUi";
import { executeTravelPlan, fetchTripLiveMapPage, reviseTravelPlan } from "../../lib/api";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import type {
  TripLiveMapLocationCardDto,
  TripLiveMapPageDto,
  TripLiveMapRemindersCardDto,
  TripLiveMapSnapshotCardDto,
  TripLiveMapStopDto,
} from "../../lib/api/types";
import { setCurrentTravel } from "../../lib/currentTravel";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { ITINERARY_HUB_PATH, TRIP_LIVE_MAP_PATH } from "../../routes";
import { TripLiveMapEmptyView } from "./TripLiveMapEmptyView";

type MapLocationState = { travelId?: string; planId?: string };

function resolveMapAssetUrl(url?: string | null): string {
  const value = url?.trim() ?? "";
  return value || "/map-empty-viewport.png";
}

function mapPath(stops: TripLiveMapStopDto[]): string {
  return stops
    .map((stop, index) => `${index === 0 ? "M" : "L"} ${stop.xPercent} ${stop.yPercent}`)
    .join(" ");
}

function DynamicMapBackground(): JSX.Element {
  return (
    <div className="absolute inset-0 z-[2] overflow-hidden bg-[#edf7ff]" aria-hidden>
      <div className="absolute -right-20 top-16 h-[115%] w-44 rotate-[28deg] rounded-full bg-[#bce8ff]/72" />
      <div className="absolute -right-12 top-12 h-[115%] w-4 rotate-[28deg] rounded-full bg-white/85" />
      <div className="absolute left-[-8%] top-[28%] h-4 w-[125%] rotate-[-19deg] rounded-full bg-white/82" />
      <div className="absolute left-[-16%] top-[55%] h-4 w-[130%] rotate-[22deg] rounded-full bg-white/76" />
      <div className="absolute left-[6%] top-[8%] h-3 w-[90%] rotate-[5deg] rounded-full bg-white/64" />
      <div className="absolute left-[18%] top-[-10%] h-[115%] w-3 rotate-[18deg] rounded-full bg-white/64" />
      <div className="absolute left-[53%] top-[-12%] h-[110%] w-3 rotate-[-8deg] rounded-full bg-white/64" />
      <div className="absolute bottom-8 left-8 h-24 w-40 rotate-[-16deg] rounded-[32px] bg-[#c8efd8]/58" />
      <div className="absolute right-20 top-28 h-16 w-24 rotate-[18deg] rounded-[24px] bg-white/38" />
      <div className="absolute left-10 top-20 h-12 w-16 rotate-[-18deg] rounded-[18px] bg-white/32" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.55)_0%,rgba(255,255,255,0.12)_42%,rgba(255,255,255,0.2)_100%)]" />
    </div>
  );
}

function DynamicMapOverlay({ stops }: { stops: TripLiveMapStopDto[] }): JSX.Element | null {
  if (!stops.length) return null;
  const activeStop = stops[0];
  const nextStops = stops.slice(1);

  return (
    <div className="pointer-events-none absolute inset-0 z-[5]" aria-hidden>
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <path
          d={mapPath(stops)}
          fill="none"
          stroke="#f5b700"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.4"
          strokeDasharray="none"
        />
        <path
          d={mapPath(stops.slice(1))}
          fill="none"
          stroke="#f5b700"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.2"
          strokeDasharray="2.4 2.4"
        />
      </svg>

      <div
        className="absolute -translate-x-1/2 -translate-y-1/2"
        style={{ left: `${activeStop.xPercent}%`, top: `${activeStop.yPercent}%` }}
      >
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-[#ffc400] text-white shadow-[0_8px_22px_rgba(245,183,0,0.35)] ring-[10px] ring-[#fff2bd]/80">
          <MapPin className="h-7 w-7" fill="currentColor" strokeWidth={1.8} />
        </span>
      </div>

      <div
        className="absolute max-w-[58%] -translate-y-full rounded-[14px] bg-white/95 px-3 py-2 text-[#111827] shadow-[0_6px_18px_rgba(15,23,42,0.14)]"
        style={{ left: `${Math.min(activeStop.xPercent + 12, 42)}%`, top: `${Math.max(activeStop.yPercent - 7, 20)}%` }}
      >
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ffc400] text-[11px] font-bold text-white">
            {activeStop.order}
          </span>
          <span className="truncate text-[12px] font-bold">{activeStop.title}</span>
        </div>
        <p className="mt-1 whitespace-nowrap text-[11px] font-semibold text-[#64748b]">
          {activeStop.time} · {activeStop.statusText}
        </p>
      </div>

      {nextStops.map((stop) => (
        <div
          key={stop.id}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${stop.xPercent}%`, top: `${stop.yPercent}%` }}
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[13px] font-bold text-[#b77900] shadow-[0_4px_14px_rgba(15,23,42,0.14)] ring-4 ring-[#ffd95a]">
            {stop.order}
          </span>
          <span className="absolute left-8 top-1/2 max-w-[9rem] -translate-y-1/2 whitespace-nowrap rounded-full bg-white/95 px-2 py-1 text-[11px] font-bold text-[#334155] shadow-[0_3px_10px_rgba(15,23,42,0.1)]">
            {stop.title}
          </span>
        </div>
      ))}
    </div>
  );
}

function SnapshotCard({ card }: { card: TripLiveMapSnapshotCardDto }): JSX.Element {
  return (
    <AppCard>
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#fff4d6] text-[#8a5a00]">
          <Sparkles className="h-5 w-5" strokeWidth={2.1} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-[17px] font-bold text-[#111827]">{card.title}</h2>
          <p className="mt-2 text-[13px] leading-5 text-[#475569]">{card.timelineText}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <AppPill>{card.footerLeft}</AppPill>
            <AppPill className="bg-[#e8f7f0] text-[#047857]">{card.footerEmphasis}</AppPill>
          </div>
        </div>
      </div>
    </AppCard>
  );
}

function LocationCard({ card }: { card: TripLiveMapLocationCardDto }): JSX.Element {
  return (
    <AppCard>
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
          <MapPin className="h-5 w-5" strokeWidth={2.1} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-[17px] font-bold text-[#111827]">{card.title}</h2>
          <p className="mt-2 text-[13px] leading-5 text-[#475569]">{card.currentLine}</p>
          <div className="mt-3 rounded-[12px] bg-[#f1f6ff] px-3 py-2">
            <p className="text-[12px] font-semibold leading-5 text-[#2456a6]">{card.nextStepLine}</p>
          </div>
        </div>
      </div>
    </AppCard>
  );
}

function RemindersCard({ card }: { card: TripLiveMapRemindersCardDto }): JSX.Element {
  return (
    <AppCard>
      <h2 className="text-[17px] font-bold text-[#111827]">{card.title}</h2>
      <div className="mt-3 space-y-2">
        {card.reminderLines.map((line, index) => (
          <div key={`${card.title}-${index}`} className="rounded-[12px] bg-[#f8fafc] px-3 py-2">
            <p className="text-[12px] font-semibold leading-5 text-[#475569]">{line}</p>
          </div>
        ))}
      </div>
    </AppCard>
  );
}

export const TripLiveMapScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as MapLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;
  const flow = { travelId, planId };

  const [page, setPage] = useState<TripLiveMapPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const [revisionNotice, setRevisionNotice] = useState<RevisionNoticeState>(null);
  const { toastMessage, showToast } = useAppToast();

  const goBack = (): void => {
    const hist = typeof window.history !== "undefined" ? window.history.state : null;
    const idx =
      typeof hist === "object" && hist !== null && "idx" in hist
        ? Number((hist as { idx?: unknown }).idx)
        : NaN;
    if (!Number.isNaN(idx) && idx > 0) navigate(-1);
    else navigate(ITINERARY_HUB_PATH, { state: flow });
  };

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_LIVE_MAP_PATH) {
      document.title = "实时地图 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) {
      setPage(null);
      setLoadError(null);
      return;
    }
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchTripLiveMapPage(travelId, planId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  useEffect(() => {
    if (!travelId) return;
    let active = true;
    setCurrentTravel({ travelId, planId });
    executeTravelPlan(travelId, planId)
      .then((result) => {
        if (active && !result.ok) {
          showToast(result.message || "外部执行服务暂未接入，已记录待处理任务");
        }
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "执行行程失败");
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  async function recordProviderAction(action: string, metadata?: Record<string, unknown>): Promise<void> {
    try {
      const result = await executeTravelPlan(travelId, { planId, action, metadata });
      showToast(result.message || "外部服务暂未接入，已记录待处理任务");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "记录外部服务任务失败");
    }
  }

  async function handleComposerSubmit(): Promise<void> {
    const text = input.trim();
    if (!text) {
      showToast("请输入想调整的行程信息");
      return;
    }

    setSubmitPending(true);
    setLoadError(null);
    setRevisionNotice(null);
    try {
      const revised = await reviseTravelPlan(travelId, {
        message: text,
        targetPlanId: planId,
        revisionMode: "partial",
      });
      setPage(revised.updatedTripLiveMap ?? await fetchTripLiveMapPage(travelId, planId));
      setRevisionNotice({ summary: revised.revisionSummary, warnings: revised.warnings });
      showToast("行程已更新");
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改行程失败");
    } finally {
      setSubmitPending(false);
    }
  }

  if (!travelId && !resolvingTravel) {
    return <TripLiveMapEmptyView travelId={travelId} planId={planId} />;
  }

  return (
    <AppScreenShell frameClassName="bg-white">
      <AppToast message={toastMessage} />
      {page ? (
        <EmbeddedStatusBarImage src={page.statusBarImageUrl} className="relative z-20" height={61} width={402} />
      ) : (
        <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/90" />
      )}

      <div className="relative flex min-h-0 flex-1 flex-col">
        <div className="relative z-10 w-full shrink-0 px-2 pt-1">
          <div className="relative h-[min(374px,52vh)] min-h-[300px] w-full overflow-hidden rounded-[30px] bg-[#e8f4fc] shadow-[inset_0_0_0_1px_rgba(80,169,254,0.12)]">
            {page?.mapBackdropImageUrl ? (
              <img src={page.mapBackdropImageUrl} alt="" className="absolute inset-0 z-0 h-full w-full object-cover object-top" />
            ) : null}
            <div className="pointer-events-none absolute inset-0 z-[1] bg-gradient-to-b from-white/20 via-transparent to-white/10" aria-hidden />
            {page ? (
              <>
                {page.mapStops.length ? (
                  <DynamicMapBackground />
                ) : (
                  <img src={resolveMapAssetUrl(page.mapImageUrl)} alt="" className="absolute inset-0 z-[2] h-full w-full object-cover object-center" />
                )}
                <div className="pointer-events-none absolute inset-0 z-[3] bg-white/10" aria-hidden />
                <DynamicMapOverlay stops={page.mapStops} />
              </>
            ) : (
              <div className="absolute inset-0 z-[2] flex items-center justify-center text-[13px] font-semibold text-[#6b7280]">
                地图加载中…
              </div>
            )}

            <div className="absolute left-3 top-3 z-[6]">
              <button
                type="button"
                aria-label="返回上一页"
                onClick={goBack}
                className="flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition active:scale-95"
              >
                <ChevronLeft className="h-[22px] w-[22px]" strokeWidth={1.85} aria-hidden />
              </button>
            </div>

            {page ? (
              <>
                <div className="absolute right-3 top-3 z-[6] flex gap-2">
                  <button
                    type="button"
                    aria-label="导航"
                    onClick={() => void recordProviderAction("navigation", { source: "trip_live_map" })}
                    className="flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition active:scale-95"
                  >
                    <Navigation className="h-[18px] w-[18px]" strokeWidth={1.75} />
                  </button>
                  <button
                    type="button"
                    aria-label="分享"
                    onClick={() => void recordProviderAction("share_itinerary", { source: "trip_live_map" })}
                    className="flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition active:scale-95"
                  >
                    <Share2 className="h-[18px] w-[18px]" strokeWidth={1.75} />
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => void recordProviderAction("call_ride", { source: "trip_live_map" })}
                  className="absolute bottom-4 right-3 z-[6] flex min-h-16 min-w-[4.5rem] flex-col items-center justify-center rounded-2xl bg-white px-3 py-2.5 text-[#334155] shadow-[0_4px_20px_rgba(15,23,42,0.14)] ring-1 ring-black/[0.04] transition active:scale-[0.98]"
                >
                  <Car className="h-7 w-7 text-[#fbbf24]" strokeWidth={1.5} />
                  <span className="mt-1 text-[10px] font-bold leading-none">{page.callRideButtonLabel}</span>
                </button>
              </>
            ) : null}
          </div>
        </div>

        <div className={`relative z-30 -mt-4 flex min-h-0 flex-1 flex-col rounded-t-[28px] bg-white pb-2 pt-4 shadow-[0px_-4px_24px_rgba(80,169,254,0.12)] ${tabScreenPrimaryColumnPaddingXClass}`}>
          <div className="min-h-0 flex-1 overflow-y-auto pb-3">
            {resolvingTravel ? (
              <p className="py-6 text-center text-[13px] text-[#6b7280]">正在同步当前行程…</p>
            ) : loadError && !page ? (
              <p className="py-4 text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="py-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <div className="space-y-3">
                <RevisionNotice notice={revisionNotice} />
                <SnapshotCard card={page.snapshotCard} />
                <LocationCard card={page.locationCard} />
                <RemindersCard card={page.remindersCard} />
                <AppStatusStrip Icon={Sparkles} title={page.aiBubbleText} />
                {loadError ? (
                  <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                    {loadError}
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className={tabScreenComposerDockClass}>
            <AppActionButton
              tone="blue"
              onClick={() => navigate(ITINERARY_HUB_PATH, { state: flow })}
            >
              查看行程主页
            </AppActionButton>
            <AppComposer
              value={input}
              onChange={setInput}
              onSubmit={() => void handleComposerSubmit()}
              pending={submitPending}
              placeholder={submitPending ? "正在修改行程…" : "补充行程问题，例如提醒我叫车..."}
            />
            <AppBottomNav active="地图" journeyFlow={{ travelId, planId }} />
          </div>
        </div>
      </div>
    </AppScreenShell>
  );
};
