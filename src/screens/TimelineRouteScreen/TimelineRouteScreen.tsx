import {
  CalendarCheck2,
  ChevronDown,
  ChevronLeft,
  Clock3,
  MapPin,
  Route,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { RevisionNotice, type RevisionNoticeState } from "../../components/RevisionNotice";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppComposer,
  AppErrorState,
  AppIconButton,
  AppLoadingState,
  AppPageHeader,
  AppPill,
  AppStatusStrip,
} from "../../components/AppUi";
import { fetchItineraryTimelinePage, reviseTravelPlan } from "../../lib/api";
import { FIGMA_TIMELINE_465 } from "../../lib/api/mock/figma-timeline-465-assets";
import type {
  ItineraryTimelinePageDto,
  ItineraryTimelineSegmentDto,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { BOOKING_TODOS_PATH, PLANS_PATH, TIMELINE_PATH } from "../../routes";
import { cn } from "../../lib/utils";

type TimelineLocationState = { travelId?: string; planId?: string };

function TimelineRow({
  seg,
  index,
  isLast,
}: {
  seg: ItineraryTimelineSegmentDto;
  index: number;
  isLast: boolean;
}): JSX.Element {
  return (
    <div className="grid grid-cols-[44px_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#ffd95a] text-[13px] font-bold text-[#3f3421] shadow-[0_6px_16px_rgba(234,179,8,0.18)]">
          {index + 1}
        </span>
        {!isLast ? <span className="mt-2 h-full min-h-6 w-px bg-[#d9dee7]" /> : null}
      </div>
      <div className={cn("min-w-0", !isLast && "pb-4")}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[14px] font-bold leading-5 text-[#111827]">{seg.title}</p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-[#f1f5f9] px-2 py-1 text-[10px] font-semibold text-[#64748b]">
                <Clock3 className="h-3 w-3" strokeWidth={2} />
                {seg.scheduleLabel}
              </span>
              {seg.scheduleNote ? (
                <span className="rounded-full bg-[#f8fafc] px-2 py-1 text-[10px] font-semibold text-[#64748b]">
                  {seg.scheduleNote}
                </span>
              ) : null}
            </div>
          </div>
          {seg.transport ? (
            <span className="shrink-0 rounded-full bg-[#e8f1ff] px-2.5 py-1 text-[11px] font-semibold text-[#2456a6]">
              {seg.transport.emoji} {seg.transport.label}
            </span>
          ) : null}
        </div>

        {seg.metaLines.length > 0 ? (
          <div className="mt-2 space-y-1">
            {seg.metaLines.slice(0, 2).map((line, lineIndex) => (
              <p key={`${seg.id}-m-${lineIndex}`} className="text-[12px] leading-5 text-[#64748b]">
                {line}
              </p>
            ))}
          </div>
        ) : null}

        {seg.detailLines?.length ? (
          <div className="mt-2 rounded-[12px] bg-[#f8fafc] px-3 py-2">
            {seg.detailLines.slice(0, 2).map((line, lineIndex) => (
              <p key={`${seg.id}-d-${lineIndex}`} className="text-[11px] leading-5 text-[#64748b]">
                {line}
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function HeroRouteSummary({ page }: { page: ItineraryTimelinePageDto }): JSX.Element {
  const first = page.segments[0];
  const next = page.segments[1];
  const last = page.segments[page.segments.length - 1];

  return (
    <AppCard className="border-[#f1c96d] bg-[linear-gradient(135deg,#fffdf5_0%,#ffffff_58%,#f1f6ff_100%)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <AppPill className="bg-[#fff4d6] text-[#8a5a00]">{page.planPillLabel} · 已选择</AppPill>
          <h2 className="mt-3 text-[22px] font-bold leading-[1.18] text-[#111827]">
            今天按这条路线走
          </h2>
          <p className="mt-2 text-[13px] leading-5 text-[#64748b]">{page.pageFooterSummaryParts.highlight}{page.pageFooterSummaryParts.rest}</p>
        </div>
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#ffd95a] text-[#3f3421] shadow-[0_8px_18px_rgba(234,179,8,0.2)]">
          <Route className="h-6 w-6" strokeWidth={2.1} />
        </span>
      </div>

      <div className="mt-4 grid gap-2">
        {first ? (
          <div className="rounded-[12px] bg-white/80 px-3 py-3">
            <p className="text-[11px] font-semibold text-[#94a3b8]">第一站</p>
            <p className="mt-1 text-[14px] font-bold text-[#111827]">{first.scheduleLabel} · {first.title}</p>
          </div>
        ) : null}
        {next ? (
          <div className="rounded-[12px] bg-white/80 px-3 py-3">
            <p className="text-[11px] font-semibold text-[#94a3b8]">下一段重点</p>
            <p className="mt-1 text-[14px] font-bold text-[#111827]">{next.title}</p>
          </div>
        ) : null}
        {last && last.id !== first?.id ? (
          <div className="rounded-[12px] bg-white/80 px-3 py-3">
            <p className="text-[11px] font-semibold text-[#94a3b8]">结束安排</p>
            <p className="mt-1 text-[14px] font-bold text-[#111827]">{last.scheduleLabel} · {last.title}</p>
          </div>
        ) : null}
      </div>
    </AppCard>
  );
}

export const TimelineRouteScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as TimelineLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<ItineraryTimelinePageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const [revisionNotice, setRevisionNotice] = useState<RevisionNoticeState>(null);
  const [showAll, setShowAll] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === TIMELINE_PATH) {
      document.title = "路线时间轴 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) return;
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

  const bookingTodosState = { travelId, planId };
  const visibleSegments = useMemo(() => {
    if (!page) return [];
    return showAll ? page.segments : page.segments.slice(0, 3);
  }, [page, showAll]);

  async function handleComposerSubmit(): Promise<void> {
    const text = input.trim();
    if (!text) {
      showToast("请输入想调整的路线要求，继续请点下方主按钮");
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
      setPage(revised.updatedTimeline ?? await fetchItineraryTimelinePage(travelId, planId));
      setRevisionNotice({ summary: revised.revisionSummary, warnings: revised.warnings });
      showToast("时间轴已更新");
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改时间轴失败");
    } finally {
      setSubmitPending(false);
    }
  }

  function continueToBooking(): void {
    setCurrentTravel({ travelId, planId });
    navigate(BOOKING_TODOS_PATH, { state: bookingTodosState });
  }

  return (
    <AppScreenShell frameClassName="bg-[#f6f7fb]">
      <AppToast message={toastMessage} />
      <AppBackdrop />
      <AppIconButton
        to={PLANS_PATH}
        state={{ travelId }}
        label="返回方案"
        className="absolute left-3 top-[61px] z-20"
      >
        <ChevronLeft className="h-5 w-5" strokeWidth={2.1} />
      </AppIconButton>

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-hidden">
        <EmbeddedStatusBarImage src={page?.statusBarImageUrl ?? FIGMA_TIMELINE_465.statusBar} />

        {resolvingTravel ? (
          <AppLoadingState label="正在同步当前行程..." />
        ) : loadError && !page ? (
          <AppErrorState message={loadError} />
        ) : !page ? (
          <AppLoadingState />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col px-[14px] pb-3 pt-2">
            <div className="min-h-0 flex-1 overflow-y-auto pb-5">
              <AppPageHeader
                className="pb-4 pl-12"
                eyebrow={page.aiStatusMessage}
                title="路线时间轴"
                subtitle="先看关键节点，完整细节可以展开。"
                action={<AppPill className="mt-1 shrink-0 bg-[#fff4d6] text-[#8a5a00]">{page.planPillLabel}</AppPill>}
              />

              <div className="space-y-4">
                <RevisionNotice notice={revisionNotice} />
                <HeroRouteSummary page={page} />

                <AppStatusStrip
                  Icon={Sparkles}
                  title="AI 已把路线按转场和停留时间排好"
                  detail={page.cardFooterSummary}
                />

                <AppCard>
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
                        <MapPin className="h-5 w-5" strokeWidth={2.1} />
                      </span>
                      <div>
                        <h2 className="text-[17px] font-bold text-[#111827]">关键节点</h2>
                        <p className="mt-0.5 text-[12px] text-[#64748b]">
                          {showAll ? `全部 ${page.segments.length} 个节点` : "默认展示前三个重点"}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowAll((value) => !value)}
                      className="inline-flex min-h-10 items-center gap-1 rounded-full bg-[#f1f5f9] px-3 text-[12px] font-semibold text-[#475569]"
                    >
                      {showAll ? "收起" : "展开全部"}
                      <ChevronDown className={cn("h-4 w-4 transition", showAll && "rotate-180")} strokeWidth={2} />
                    </button>
                  </div>

                  <div>
                    {visibleSegments.map((seg, index) => (
                      <TimelineRow
                        key={seg.id}
                        seg={seg}
                        index={index}
                        isLast={index === visibleSegments.length - 1}
                      />
                    ))}
                  </div>
                </AppCard>

                {loadError ? (
                  <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                    {loadError}
                  </div>
                ) : null}
              </div>
            </div>

            <div className={tabScreenComposerDockMtAutoClass}>
              <AppActionButton Icon={CalendarCheck2} onClick={continueToBooking} tone="blue">
                确认路线，进入预约
              </AppActionButton>
              <AppComposer
                value={input}
                onChange={setInput}
                onSubmit={() => void handleComposerSubmit()}
                pending={submitPending}
                placeholder={submitPending ? "正在修改路线…" : "想调整哪里，例如少走路、提前吃饭..."}
              />
              <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
            </div>
          </div>
        )}
      </div>
    </AppScreenShell>
  );
};
