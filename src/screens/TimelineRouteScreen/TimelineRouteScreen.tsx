import { ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { fetchItineraryTimelinePage } from "../../lib/api";
import { FIGMA_TIMELINE_465 } from "../../lib/api/mock/figma-timeline-465-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  ItineraryTimelinePageDto,
  ItineraryTimelineSegmentDto,
} from "../../lib/api/types";
import { BOOKING_TODOS_PATH, PLANS_PATH, TIMELINE_PATH } from "../../routes";
import {
  embeddedBackButtonTopClass,
  embeddedPlanPillTopClass,
  embeddedTimelineAiStripMarginTopClass,
} from "../../lib/embeddedStatusBar";
import { cn } from "../../lib/utils";

type TimelineLocationState = { travelId?: string; planId?: string };

function cardTitleGradient(): string {
  return "bg-[linear-gradient(24.482deg,rgb(95,115,128)_16.391%,rgb(62,82,101)_73.16%,rgb(42,114,176)_96.32%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

/** 稿面拆分：两段 Semibold + 省略号（与 node 1:597 / Plan B mock 对齐） */
function parseTimelineAiStrip(text: string): { a: string; b: string; tail: string } | null {
  const variants: RegExp[] = [
    /^(您已确认PLan A，)(正在生成Plan A 的详细时间轴＆路线)(…)$/,
    /^(您已确认Plan A，)(正在生成Plan A 的详细时间轴＆路线)(…)$/,
    /^(您已确认Plan B，)(正在生成Plan B 的详细时间轴＆路线)(…)$/,
  ];
  for (const re of variants) {
    const m = text.match(re);
    if (m) return { a: m[1], b: m[2], tail: m[3] ?? "…" };
  }
  return null;
}

function parseCardHeadline(cardTitle: string): { core: string; tail: string } | null {
  const fixed = "时间轴＆路线";
  if (!cardTitle.startsWith(fixed)) return null;
  const tail = cardTitle.slice(fixed.length);
  if (tail !== "…" && tail !== "..." && tail !== "⋯") return null;
  return { core: fixed, tail: tail === "..." ? "…" : tail };
}

function TimelineAiCollapsedStrip({ text }: { text: string }): JSX.Element {
  const parsed = parseTimelineAiStrip(text);
  return (
    <div className="flex h-[52px] w-full shrink-0 items-center rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white px-3 shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)]">
      <img src={FIGMA_TIMELINE_465.topStripMagnifier} alt="" className="h-[10px] w-[10px] shrink-0 object-contain" />
      <div className="min-w-0 flex-1 pl-3 pr-5">
        {parsed ? (
          <p className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] leading-[17.288px] text-[#626262]">
            <span className="font-semibold text-[#626262]">{parsed.a}</span>
            <span className="font-semibold text-[#626262]">{parsed.b}</span>
            <span className="font-normal">{parsed.tail}</span>
          </p>
        ) : (
          <p className="line-clamp-2 font-semibold [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] leading-[17px] text-[#626262]">
            {text}
          </p>
        )}
      </div>
      <img src={FIGMA_TIMELINE_465.topStripChevron} alt="" className="mr-px h-[6px] w-[9px] shrink-0 object-contain opacity-80" />
    </div>
  );
}

function RowDivider(): JSX.Element {
  return (
    <div className="flex min-h-[0.5px] justify-center px-px">
      <img src={FIGMA_TIMELINE_465.rowDivider} alt="" className="h-[0.5px] w-[309px] max-w-full object-cover" />
    </div>
  );
}

/** 与稿面节点一致的圆环 + 实心点（竖线高度随段落 flex 铺满，避免 Spine 贴图固定 388px 截断） */
function TimelineSegmentNodeDot(): JSX.Element {
  return (
    <div className="relative z-[3] flex h-[10px] w-[10px] shrink-0 items-center justify-center rounded-full border-[1.75px] border-[#ffd100] bg-white">
      <div className="h-[4px] w-[4px] rounded-full bg-[#ffd100]" />
    </div>
  );
}

function TimelineSegmentBlock({
  seg,
  dividerAfter,
  index,
  total,
}: {
  seg: ItineraryTimelineSegmentDto;
  dividerAfter: boolean;
  index: number;
  total: number;
}): JSX.Element {
  const isFirst = index === 0;
  const isLast = index === total - 1;
  const spineBarClass = "w-[2px] flex-1 min-h-[2px] shrink-0 bg-[#ffd100]";

  return (
    <>
      <div className="flex gap-x-1 pr-1 pt-1">
        <div className="flex w-[20px] shrink-0 flex-col items-center pt-2">
          {/* 左轨：线与节点随右侧内容等高，整段连成一条 */}
          {isFirst ? <div className="h-[6px] shrink-0" aria-hidden /> : <div className={spineBarClass} />}
          <TimelineSegmentNodeDot />
          {!isLast ? <div className={spineBarClass} /> : <div className="h-[6px] shrink-0" aria-hidden />}
        </div>
        <div className="grid min-w-0 flex-1 grid-cols-[42px_minmax(0,1fr)_52px] gap-x-1">
          <div className="flex flex-col pl-1 pt-0.5">
            <p className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10px] font-normal leading-[17.288px] text-[#493f00]">
              {seg.scheduleLabel}
            </p>
            {seg.scheduleNote ? (
              <p className="mt-0.5 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[8.5px] font-normal leading-[17.288px] text-[#626262]">
                {seg.scheduleNote}
              </p>
            ) : null}
          </div>
          <div className="min-w-0 pt-0.5">
            <p className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10px] font-semibold leading-[17.288px] text-[#626262]">
              {seg.title}
            </p>
            {seg.metaLines.map((line, i) => (
              <p
                key={`${seg.id}-m-${i}`}
                className="mt-[2px] max-w-[210px] [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[7.5px] font-normal leading-[17.288px] text-[#626262]"
              >
                {line}
              </p>
            ))}
            {seg.detailLines?.map((line, i) => (
              <p
                key={`${seg.id}-d-${i}`}
                className="mt-[2px] max-w-[210px] [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[7.5px] font-normal leading-[10px] text-[#626262]"
              >
                {line}
              </p>
            ))}
          </div>
          <div className="flex flex-col items-center justify-start pb-2 pt-[2px] text-center text-[#626262]">
            {seg.transport ? (
              <>
                <span className="text-[15px] leading-none">{seg.transport.emoji}</span>
                <p className="mt-0.5 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[9px] leading-[17.288px]">
                  {seg.transport.label}
                </p>
              </>
            ) : null}
          </div>
        </div>
      </div>
      {dividerAfter ? <RowDivider /> : null}
    </>
  );
}

function ItineraryMainCard({
  cardTitle,
  segments,
  cardFooterSummary,
}: {
  cardTitle: string;
  segments: ItineraryTimelineSegmentDto[];
  cardFooterSummary: string;
}): JSX.Element {
  const titleParts = parseCardHeadline(cardTitle);
  return (
    <div className="relative mx-auto min-h-[506px] w-[calc(100%-2px)] max-w-[350px] overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_0px_#d0def8]">
      <img
        src={FIGMA_TIMELINE_465.cardGlow1}
        alt=""
        className="pointer-events-none absolute left-[46px] top-[23px] h-[388px] w-[293px] max-w-none object-cover opacity-95"
      />
      <img
        src={FIGMA_TIMELINE_465.cardGlow2}
        alt=""
        className="pointer-events-none absolute -left-[110px] -top-[147px] h-[220px] w-[271px] max-w-none object-cover opacity-[0.93]"
      />
      <div className="relative z-[2] flex flex-col pb-0 pl-[10px] pr-[10px] pt-[13px]">
        <header className="relative flex items-start gap-2 pr-3">
          <img src={FIGMA_TIMELINE_465.sparkleGold} alt="" width={24} height={24} className="h-6 w-6 shrink-0 overflow-hidden rounded-full object-cover" />
          <div className="min-w-0 flex-1">
            {titleParts ? (
              <h2 className={`[font-family:'HYQiHei-Regular',Helvetica] text-[15px] leading-[12.654px] ${cardTitleGradient()}`}>
                <span className="font-semibold">{titleParts.core}</span>
                <span className="font-normal">{titleParts.tail}</span>
              </h2>
            ) : (
              <h2 className={`break-words [font-family:'HYQiHei-Regular',Helvetica] text-[15px] leading-[12.654px] ${cardTitleGradient()}`}>
                {cardTitle}
              </h2>
            )}
          </div>
          <ChevronDown className="mt-px h-[10px] w-[10px] shrink-0 text-[#626262]" strokeWidth={2} aria-hidden />
        </header>

        <div className="relative mt-2 pb-10">
          <div className="relative pr-px pt-px">
            {segments.map((seg, idx) => (
              <TimelineSegmentBlock
                key={seg.id}
                seg={seg}
                dividerAfter={idx < segments.length - 1}
                index={idx}
                total={segments.length}
              />
            ))}
          </div>
        </div>

        <div className="-mx-[1px] -mb-px mt-auto bg-[#ffd100] px-3 py-[9px]">
          <p className="text-center [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10px] font-medium leading-[17.288px] text-[#343d43]">
            {cardFooterSummary}
          </p>
        </div>
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
  const bookingTodosState = { travelId, planId };
  const voiceFallback = FIGMA_TIMELINE_465.voiceChip;

  return (
    <AppScreenShell>
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <img
            src={FIGMA_TIMELINE_465.bgBlobA}
            alt=""
            className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
          />
          <img
            src={FIGMA_TIMELINE_465.bgBlobB}
            alt=""
            className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-[0.93]"
          />
        </div>

        <Link
          to={PLANS_PATH}
          state={plansBackState}
          className={cn(
            "absolute left-[10px] z-20 flex h-10 w-10 items-center justify-center rounded-full text-[#251e1e] hover:bg-black/[0.04]",
            embeddedBackButtonTopClass(),
          )}
          aria-label="返回方案对比"
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
        </Link>

        {page ? (
          <div
            className={cn(
              "absolute right-[37px] z-20 rounded-bl-[15.417px] rounded-br-[15.417px] rounded-tl-[15.417px] bg-[#ffd100] px-[14px] py-[5px] shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)]",
              embeddedPlanPillTopClass(),
            )}
          >
            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold leading-[26px] text-[#343d43]">
              {page.planPillLabel}
            </p>
          </div>
        ) : null}

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-x-hidden">
          <EmbeddedStatusBarImage src={page?.statusBarImageUrl ?? FIGMA_TIMELINE_465.statusBar} />
          <div className="flex min-h-0 flex-1 flex-col px-[29px] pb-3 pt-[10px]">
            {loadError && !page ? (
              <p className="py-24 text-center text-[13px] text-red-600">{loadError}</p>
            ) : null}
            {!page && !loadError ? (
              <p className="py-24 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : null}
            {page ? (
              <>
                <div className={cn("mb-[9px]", embeddedTimelineAiStripMarginTopClass())}>
                  <TimelineAiCollapsedStrip text={page.aiStatusMessage} />
                </div>

                <ContentFitZoom
                  className="pb-2"
                  recalcKey={page ? `${page.segments.length}:${page.cardTitle}` : ""}
                >
                  <ItineraryMainCard
                    cardTitle={page.cardTitle}
                    segments={page.segments}
                    cardFooterSummary={page.cardFooterSummary}
                  />
                </ContentFitZoom>

                <div className="mt-auto flex flex-col gap-3 pt-2">
                  <div className="flex items-center gap-2">
                    <div className="relative flex min-h-[46px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-3 pr-[46px] shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
                      <img
                        src={page.voiceInputIconUrl || voiceFallback}
                        alt=""
                        className="absolute right-4 top-1/2 z-[2] h-7 w-[34px] -translate-y-1/2 select-none object-contain"
                      />
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="继续说说你的想法…"
                        className="min-w-0 flex-1 bg-transparent py-2 pr-14 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#343d4380]"
                      />
                    </div>
                    <Link
                      to={BOOKING_TODOS_PATH}
                      state={bookingTodosState}
                      aria-label="进入行程预约"
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
                    >
                      <ChevronRight className="h-5 w-5" strokeWidth={2} aria-hidden />
                    </Link>
                  </div>

                  <div className="pb-2">
                    <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
    </AppScreenShell>
  );
};
