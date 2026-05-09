import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { Card, CardContent } from "../../components/ui/card";
import { fetchItineraryTimelinePage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  ItineraryTimelinePageDto,
  ItineraryTimelineSegmentDto,
} from "../../lib/api/types";
import { BOOKING_TODOS_PATH, PLANS_PATH, TIMELINE_PATH } from "../../routes";

type TimelineLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function TimelineSegmentRow({ seg }: { seg: ItineraryTimelineSegmentDto }): JSX.Element {
  return (
    <div className="grid grid-cols-[52px_minmax(0,1fr)_42px] gap-x-1.5 border-b border-[#ececec] py-2.5 last:border-b-0">
      <div className="flex flex-col pt-0.5">
        <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-normal leading-snug text-[#493f00]">
          {seg.scheduleLabel}
        </p>
        {seg.scheduleNote ? (
          <p className="mt-0.5 [font-family:'PingFang_SC-Regular',Helvetica] text-[8.5px] leading-snug text-[#626262]">
            {seg.scheduleNote}
          </p>
        ) : null}
      </div>
      <div className="min-w-0 pt-0.5">
        <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-semibold leading-snug text-[#626262]">
          {seg.title}
        </p>
        {seg.metaLines.map((line, i) => (
          <p
            key={`${seg.id}-m-${i}`}
            className="mt-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[7.5px] leading-relaxed text-[#626262]"
          >
            {line}
          </p>
        ))}
        {seg.detailLines?.map((line, i) => (
          <p
            key={`${seg.id}-d-${i}`}
            className="mt-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[7.5px] leading-relaxed text-[#626262]"
          >
            {line}
          </p>
        ))}
      </div>
      <div className="flex flex-col items-center justify-start pt-1 text-center">
        {seg.transport ? (
          <>
            <span className="text-[15px] leading-none">{seg.transport.emoji}</span>
            <p className="mt-0.5 [font-family:'PingFang_SC-Regular',Helvetica] text-[9px] text-[#626262]">
              {seg.transport.label}
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}

export const TimelineRouteScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as TimelineLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<ItineraryTimelinePageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === TIMELINE_PATH) {
      document.title = "行程时间轴 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchItineraryTimelinePage(travelId, planId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) {
          setLoadError(e instanceof Error ? e.message : "加载失败");
        }
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  const plansBackState = { travelId };

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-white">
      <div className="relative mx-auto flex min-h-[874px] w-full max-w-[402px] flex-col">
        {page ? (
          <img
            src={page.statusBarImageUrl}
            alt=""
            className="h-[61px] w-full shrink-0 object-cover object-top"
            height={61}
            width={402}
          />
        ) : (
          <div className="h-[61px] w-full shrink-0 bg-white/80" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-8 pb-3 pt-2">
          <div className="mb-2 flex items-center justify-between gap-2">
            <Link
              to={PLANS_PATH}
              state={plansBackState}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回方案对比"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            {page ? (
              <div className="rounded-bl-[15px] rounded-br-[15px] rounded-tl-[15px] bg-[#ffd100] px-4 py-1 shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)]">
                <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#343d43]">
                  {page.planPillLabel}
                </p>
              </div>
            ) : (
              <div className="h-8 w-16" />
            )}
          </div>

          {page ? (
            <div className="mb-3 flex items-start gap-2 rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2.5 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
              <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={2} />
              <p className="min-w-0 flex-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold leading-relaxed text-[#626262]">
                {page.aiStatusMessage}
              </p>
              <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
            </div>
          ) : null}

          <div className="min-h-0 flex-1 overflow-y-auto pb-2">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="pt-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <CardContent className="relative border-0 p-0">
                    <div className="relative overflow-hidden bg-gradient-to-br from-[#fffef5] via-white to-[#f8fbff] px-3.5 pt-3">
                      <div className="mb-2 flex items-start gap-2 pb-2">
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
                          <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
                        </div>
                        <p
                          className={`flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
                        >
                          {page.cardTitle}
                        </p>
                        <ChevronDown className="h-4 w-4 shrink-0 text-[#9ca3af]" strokeWidth={2} />
                      </div>
                      <div className="pb-1">
                        {page.segments.map((seg) => (
                          <TimelineSegmentRow key={seg.id} seg={seg} />
                        ))}
                      </div>
                    </div>
                    <div className="bg-[#ffd100] px-3 py-2.5">
                      <p className="text-center [font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-medium leading-snug text-[#343d43]">
                        {page.cardFooterSummary}
                      </p>
                    </div>
                  </CardContent>
                </Card>
                <p className="mt-3 px-1 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[10px] leading-relaxed">
                  <span className={`font-semibold ${titleGradientClass()}`}>
                    {page.pageFooterSummaryParts.highlight}
                  </span>
                  <span className="text-[#565454]">{page.pageFooterSummaryParts.rest}</span>
                </p>
                <div className="mt-4 flex justify-center">
                  <Link
                    to={BOOKING_TODOS_PATH}
                    state={{ travelId, planId }}
                    className="rounded-full bg-[#50a9fe]/12 px-4 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#2a7bc8] transition-opacity hover:opacity-90"
                  >
                    继续：行程预约与待办
                  </Link>
                </div>
              </>
            )}
          </div>

          <div className="mt-auto flex flex-col gap-3 pt-4">
            <div className="flex items-center gap-2">
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
                  placeholder="说说路上还想调整的细节…"
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
          </div>

          <AppBottomNav active="行程" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </main>
  );
};
