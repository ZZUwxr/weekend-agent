import { Car, ChevronLeft, ChevronRight, Navigation, Share2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { Card, CardContent } from "../../components/ui/card";
import { useTripContentUnlocked } from "../../hooks/useTripContentUnlocked";
import { fetchTripLiveMapPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  TripLiveMapLocationCardDto,
  TripLiveMapPageDto,
  TripLiveMapRemindersCardDto,
  TripLiveMapSnapshotCardDto,
} from "../../lib/api/types";
import { ITINERARY_HUB_PATH, TRIP_LIVE_MAP_PATH } from "../../routes";
import { TripLiveMapEmptyView } from "./TripLiveMapEmptyView";

type MapLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function SnapshotCard({ card }: { card: TripLiveMapSnapshotCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
        <div className="mb-2 flex items-start gap-2">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
            <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
          </div>
          <p
            className={`min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
          >
            {card.title}
          </p>
        </div>
        <p className="pl-8 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium leading-relaxed text-[#343d43]">
          {card.timelineText}
        </p>
        <div className="mt-2.5 pl-8">
          <span className="inline-block rounded-md border border-[#d8d8d8] bg-gradient-to-b from-[#e8f4ff]/90 to-white px-2 py-0.5 shadow-[0px_0.8px_1.6px_#d1e8ff] [font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] text-[#343d43]">
            {card.footerLeft}
            <span className="mx-1 text-[#9ca3af]">·</span>
            <span className="font-bold">{card.footerEmphasis}</span>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function LocationCard({ card }: { card: TripLiveMapLocationCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
        <div className="mb-2 flex items-start gap-2">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
            <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
          </div>
          <p
            className={`min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
          >
            {card.title}
          </p>
        </div>
        <p className="pl-8 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium leading-relaxed text-[#343d43]">
          {card.currentLine}
        </p>
        <div className="mt-2.5 pl-8">
          <span className="inline-block max-w-full rounded-md border border-[#d8d8d8] bg-gradient-to-b from-[#e8f4ff]/90 to-white px-2 py-0.5 shadow-[0px_0.8px_1.6px_#d1e8ff] [font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] font-semibold leading-snug text-[#343d43]">
            {card.nextStepLine}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function RemindersCard({ card }: { card: TripLiveMapRemindersCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
        <div className="mb-2 flex items-start gap-2">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
            <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
          </div>
          <p
            className={`min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
          >
            {card.title}
          </p>
        </div>
        <ul className="space-y-1.5 pl-8">
          {card.reminderLines.map((line, i) => (
            <li
              key={`r-${i}`}
              className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium leading-relaxed text-[#343d43]"
            >
              {line}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export const TripLiveMapScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as MapLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const goBack = (): void => {
    const hist = typeof window.history !== "undefined" ? window.history.state : null;
    const idx =
      typeof hist === "object" && hist !== null && "idx" in hist
        ? Number((hist as { idx?: unknown }).idx)
        : NaN;
    if (!Number.isNaN(idx) && idx > 0) navigate(-1);
    else navigate(ITINERARY_HUB_PATH, { state: flow });
  };

  const [page, setPage] = useState<TripLiveMapPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_LIVE_MAP_PATH) {
      document.title = "地图 · 出行助手";
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
  }, [travelId, planId, unlocked]);

  if (!unlocked) {
    return <TripLiveMapEmptyView travelId={travelId} planId={planId} />;
  }

  return (
    <AppScreenShell frameClassName="bg-white">
        {page ? (
          <EmbeddedStatusBarImage
            src={page.statusBarImageUrl}
            className="relative z-20"
            height={61}
            width={402}
          />
        ) : (
          <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/90" />
        )}

      <div className="relative flex min-h-0 flex-1 flex-col">
        <div className="relative z-10 w-full shrink-0 px-2 pt-1">
          <div className="relative h-[min(374px,52vh)] min-h-[300px] w-full overflow-hidden rounded-[36px] bg-[#e8f4fc] shadow-[inset_0_0_0_1px_rgba(80,169,254,0.12)]">
            {page?.mapBackdropImageUrl ? (
              <img
                src={page.mapBackdropImageUrl}
                alt=""
                className="absolute inset-0 z-0 h-full w-full object-cover object-top"
              />
            ) : null}
            <div
              className="pointer-events-none absolute inset-0 z-[1] bg-gradient-to-b from-white/20 via-transparent to-white/10"
              aria-hidden
            />
            {page ? (
              <img
                src={page.mapImageUrl}
                alt=""
                className="absolute inset-0 z-[2] h-full w-full object-cover object-center"
              />
            ) : (
              <div className="absolute inset-0 z-[2] flex items-center justify-center [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#6b7280]">
                地图加载中…
              </div>
            )}

            <div className="absolute left-3 top-3 z-[6]">
              <button
                type="button"
                aria-label="返回上一页"
                onClick={goBack}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition-opacity hover:opacity-95"
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
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition-opacity hover:opacity-95"
                  >
                    <Navigation className="h-[18px] w-[18px]" strokeWidth={1.75} />
                  </button>
                  <button
                    type="button"
                    aria-label="分享"
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.1)] backdrop-blur-sm transition-opacity hover:opacity-95"
                  >
                    <Share2 className="h-[18px] w-[18px]" strokeWidth={1.75} />
                  </button>
                </div>

                <button
                  type="button"
                  className="absolute bottom-4 right-3 z-[6] flex min-w-[4.5rem] flex-col items-center justify-center rounded-2xl bg-white px-3 py-2.5 text-[#334155] shadow-[0_4px_20px_rgba(15,23,42,0.14)] ring-1 ring-black/[0.04] transition-transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Car className="h-7 w-7 text-[#fbbf24]" strokeWidth={1.5} />
                  <span className="mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-bold leading-none">
                    {page.callRideButtonLabel}
                  </span>
                </button>
              </>
            ) : null}
          </div>
        </div>

        <div className="relative z-30 -mt-4 flex min-h-0 flex-1 flex-col rounded-t-[28px] bg-white px-4 pb-2 pt-4 shadow-[0px_-4px_24px_rgba(80,169,254,0.12)]">
          {loadError ? (
            <p className="py-4 text-center text-[13px] text-red-600">{loadError}</p>
          ) : !page ? (
            <p className="py-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
          ) : (
            <ContentFitZoom
              className="space-y-2.5 pb-2"
              recalcKey={`${page.snapshotCard.timelineText}|${page.remindersCard.reminderLines.join("|")}|${page.aiBubbleText.slice(0, 40)}`}
            >
              <SnapshotCard card={page.snapshotCard} />
              <LocationCard card={page.locationCard} />
              <RemindersCard card={page.remindersCard} />
              <div className="mb-2 flex justify-start pt-1">
                <div className="max-w-[92%] rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
                  <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold text-[#626262]">
                    {page.aiBubbleText}
                  </p>
                </div>
              </div>
            </ContentFitZoom>
          )}

          <div className="flex items-center gap-2 pt-1">
            <div className="relative flex min-h-[46px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_#00000008]">
              {page ? (
                <img
                  src={page.voiceInputIconUrl}
                  alt=""
                  className="h-7 w-[34px] shrink-0 object-contain"
                  height={28}
                  width={34}
                />
              ) : (
                <div className="h-7 w-[34px] shrink-0" />
              )}
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="有疑问可以在这里补充…"
                className="min-w-0 flex-1 bg-transparent py-2 pl-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#333c4380]"
              />
            </div>
            <button
              type="button"
              aria-label="发送"
              className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_#00000025] transition-opacity hover:opacity-90"
            >
              <ChevronRight className="h-5 w-5" strokeWidth={2} />
            </button>
          </div>

          <AppBottomNav active="地图" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </AppScreenShell>
  );
};
