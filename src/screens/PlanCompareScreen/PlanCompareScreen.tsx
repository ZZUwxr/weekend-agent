import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { fetchPlanComparisonPage } from "../../lib/api";
import { FIGMA_PLANS_1119 } from "../../lib/api/mock/figma-plans-1119-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  PlanActivityDto,
  PlanComparisonPageDto,
  PlanMemberRatingDto,
  TravelPlanCardDto,
} from "../../lib/api/types";
import {
  CHAT_PATH,
  PLANS_PATH,
  TIMELINE_PATH,
} from "../../routes";
import { embeddedBackButtonTopClass } from "../../lib/embeddedStatusBar";
import { cn } from "../../lib/utils";

type PlansLocationState = { travelId?: string };

/** 用户在第三页输入里表达选 A/B 即进入对应时间轴（第四页） */
function detectPlanChoiceFromInput(text: string): "plan-a" | "plan-b" | null {
  const raw = text.trim();
  if (!raw) return null;
  const spaced = raw.toLowerCase().replace(/\s+/g, " ");
  const compactAlpha = spaced.replace(/\s/g, "");

  const hasB =
    /\bplan\s*[-_]?\s*b\b/i.test(spaced) ||
    /\bb\s+plan\b/i.test(spaced) ||
    /方案\s*[-_]?\s*b(?:\s|$|[,，.。!])/i.test(raw) ||
    /^planb$/i.test(compactAlpha);
  const hasA =
    /\bplan\s*[-_]?\s*a\b/i.test(spaced) ||
    /\ba\s+plan\b/i.test(spaced) ||
    /方案\s*[-_]?\s*a(?:\s|$|[,，.。!])/i.test(raw) ||
    /^plana$/i.test(compactAlpha);

  if (hasB && !hasA) return "plan-b";
  if (hasA && !hasB) return "plan-a";
  return null;
}

function planCardTitleClass(accent: "warm" | "cool"): string {
  /** 不用 bg-clip-text：父级 zoom 时 WebView 上常把渐变字绘成「透明」，Plan B 标题会消失 */
  return accent === "warm"
    ? "[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-semibold leading-[1.35] text-[#1e293b]"
    : "[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-semibold leading-[1.35] text-[#1e3a4c]";
}

function compensationTitleClass(): string {
  return "[font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold leading-snug text-[#475569]";
}

function parseTopStrip(text: string): { semi: string; tail: string } | null {
  const m = text.match(/^(.*?)(…|⋯|\.\.\.?)$/);
  if (!m || !text.includes("详细时间轴")) return null;
  return { semi: m[1], tail: m[2] ?? "…" };
}

function StarRow({ filled, accent }: { filled: number; accent: "warm" | "cool" }): JSX.Element {
  const n = Math.max(0, Math.min(5, Math.round(filled)));
  const on = accent === "warm" ? "#f5c814" : "#50a9fe";
  const off = "#d1d5db";
  return (
    <div className="flex justify-center gap-px pt-px text-[11px] leading-none">
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} style={{ color: i < n ? on : off }}>
          ★
        </span>
      ))}
    </div>
  );
}

function TagPill({ label }: { label: string }): JSX.Element {
  return (
    <span className="inline-flex items-center rounded-[6px] border-[0.5px] border-[#d8d8d8] bg-[linear-gradient(rgba(225,240,255,0.44)_23.58%,rgba(255,255,255,0.44)_100%)] px-[5px] py-px shadow-[0px_0.6px_1.2px_0px_#d1e8ff] [font-family:'HYQiHei-Regular',Helvetica] text-[6.2px] font-normal leading-tight text-[#343d43]">
      {label}
    </span>
  );
}

function PlanTimelineActivities({
  plan,
  spineSrc,
}: {
  plan: TravelPlanCardDto;
  spineSrc: string;
}): JSX.Element {
  return (
    <div className="relative mt-[2px] flex gap-3 pl-0">
      <div className="relative w-[22px] shrink-0 pt-1">
        <img src={spineSrc} alt="" className="absolute left-[1px] top-0 h-[93px] w-4 max-w-none object-cover object-center" />
      </div>
      <div className="min-w-0 flex-1 space-y-2.5 pt-px">
        {plan.activities.map((act: PlanActivityDto) => (
          <div key={act.id}>
            <p className="whitespace-normal [font-family:'HYQiHei-Regular',Helvetica] text-[10.5px] font-normal leading-tight tracking-normal text-[#343d43]">
              {act.title}
              {act.durationLabel ? `\u3000${act.durationLabel}` : null}
            </p>
            {act.tags.length > 0 ? (
              <div className="mt-[6px] flex flex-wrap gap-x-2 gap-y-2">{act.tags.map((t) => <TagPill key={t.id} label={t.label} />)}</div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function MemberRatingCell({
  m,
  accent,
}: {
  m: PlanMemberRatingDto;
  accent: "warm" | "cool";
}): JSX.Element {
  return (
    <div className="flex flex-col rounded-[8.5px] border-[0.474px] border-[#c8c8c8] px-[2px] py-[5px] [font-family:'HYQiHei-Regular',Helvetica]">
      <div className="flex items-start justify-between gap-1 px-1 text-[15px] leading-none text-black">
        <span aria-hidden>{m.emoji}</span>
      </div>
      <div className="mt-px flex justify-between px-2 text-[8px] text-[#343d43]">
        <span>{m.label}</span>
        <span>{m.score.toFixed(2)}</span>
      </div>
      <StarRow filled={m.starsFilled} accent={accent} />
    </div>
  );
}

function ComparisonPlanCard({ plan }: { plan: TravelPlanCardDto }): JSX.Element {
  const accent = plan.accent ?? "warm";
  const glow1 = accent === "warm" ? FIGMA_PLANS_1119.cardGlowA1 : FIGMA_PLANS_1119.cardGlowB1;
  const glow2 = accent === "warm" ? FIGMA_PLANS_1119.cardGlowA2 : FIGMA_PLANS_1119.cardGlowB2;
  const spineSrc = accent === "warm" ? FIGMA_PLANS_1119.timelineSpineA : FIGMA_PLANS_1119.timelineSpineB;
  const sparkleImg = accent === "warm" ? FIGMA_PLANS_1119.sparkleGold : FIGMA_PLANS_1119.sparkleBlue;
  const titleCls = planCardTitleClass(accent);

  return (
    <div className="relative mx-auto w-[calc(100%-6px)] max-w-[342px] overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_0px_#d0def8] lg:mx-auto">
      <img
        src={glow1}
        alt=""
        className="pointer-events-none absolute right-[-72px] top-[33px] z-0 h-[242px] w-[293px] max-w-none object-cover opacity-95"
      />
      <img
        src={glow2}
        alt=""
        className="pointer-events-none absolute -left-[110px] -top-[147px] z-0 h-[220px] w-[271px] max-w-none object-cover opacity-[0.93]"
      />
      <div className="relative z-10 pb-2 pl-[10px] pr-[12px] pt-3">
        <header className="relative flex gap-2 pb-2 pr-3">
          <img src={sparkleImg} alt="" width={24} height={24} className="h-5 w-5 shrink-0 overflow-hidden rounded-full object-cover" />
          <div className="min-w-0 flex-1 pr-[76px]">
            <h2 className={cn("break-words", titleCls)}>
              {plan.planLabel}
              {plan.headline}
            </h2>
          </div>
          <div className="pointer-events-none absolute right-[6px] top-3 z-[20]">
            <TagPill label={plan.overallScoreLabel} />
          </div>
        </header>

        <PlanTimelineActivities plan={plan} spineSrc={spineSrc} />

        <div className="my-2 h-px bg-[linear-gradient(transparent,#e8e9eb,transparent)]" aria-hidden />

        <div className="grid grid-cols-3 gap-x-1.5 gap-y-2">
          {plan.memberRatings.map((m: PlanMemberRatingDto) => (
            <MemberRatingCell key={m.id + plan.id} m={m} accent={accent} />
          ))}
        </div>

        {plan.compensationTitle && plan.compensationParagraphs && plan.compensationParagraphs.length > 0 ? (
          <section className="mt-2 rounded-[11px] border border-transparent bg-transparent px-[2px] pt-2">
            <div className="flex items-start gap-1.5">
              <img src={sparkleImg} alt="" width={24} height={24} className="h-5 w-5 shrink-0 rounded-full object-cover" />
              <div className="min-w-0">
                <h3 className={compensationTitleClass()}>{plan.compensationTitle}</h3>
                <div className="mt-[5px] space-y-1 text-[9px] font-normal leading-[13px] text-[#343d43]">
                  {plan.compensationParagraphs.map((para, idx) => (
                    <p key={idx}>{para}</p>
                  ))}
                </div>
              </div>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}

function CollapsedGeneratingStrip({ text }: { text: string }): JSX.Element {
  const parsed = parseTopStrip(text);
  return (
    <div className="flex h-8 w-full items-center rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white px-2.5 shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)]">
      <img src={FIGMA_PLANS_1119.topStripIconLeft} alt="" className="h-[10px] w-[10px] shrink-0 object-contain" />
      <div className="min-w-0 flex-1 pl-[14px] pr-6">
        {parsed ? (
          <p className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] leading-[17.288px] text-[#626262]">
            <span className="font-semibold text-[#626262]">
              {parsed.semi}
            </span>
            <span className="font-normal">{parsed.tail}</span>
          </p>
        ) : (
          <p className="line-clamp-2 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] leading-[17px] text-[#626262]">{text}</p>
        )}
      </div>
      <img src={FIGMA_PLANS_1119.topStripChevron} alt="" className="mr-px h-[6px] w-[9px] shrink-0 object-contain opacity-80" />
    </div>
  );
}

export const PlanCompareScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as PlansLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const navPlanFallback = "plan-a";

  const [page, setPage] = useState<PlanComparisonPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === PLANS_PATH) {
      document.title = "双方案对比 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchPlanComparisonPage(travelId)
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
  }, [travelId]);

  const chatBackState = { travelId };
  const journeyFlow = { travelId, planId: navPlanFallback };

  const voiceFallback = FIGMA_PLANS_1119.voiceChip;

  function trySubmitPlanChoice(): void {
    const choice = detectPlanChoiceFromInput(input);
    if (!choice) return;
    navigate(TIMELINE_PATH, { state: { travelId, planId: choice } });
    setInput("");
  }

  return (
    <AppScreenShell>
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <img
            src={FIGMA_PLANS_1119.bgBlobA}
            alt=""
            className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
          />
          <img
            src={FIGMA_PLANS_1119.bgBlobB}
            alt=""
            className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-[0.93]"
          />
        </div>

        <Link
          to={CHAT_PATH}
          state={chatBackState}
          className={cn(
            "absolute left-[10px] z-20 flex h-10 w-10 items-center justify-center rounded-full text-[#251e1e] hover:bg-black/[0.04]",
            embeddedBackButtonTopClass(),
          )}
          aria-label="返回对话"
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
        </Link>

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-x-hidden">
          <EmbeddedStatusBarImage src={page?.statusBarImageUrl ?? FIGMA_PLANS_1119.statusBar} />
          <div className="flex min-h-0 flex-1 flex-col px-[29px] pb-3 pt-3">
            {loadError ? (
              <p className="py-12 text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="py-12 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <div className="flex min-h-0 flex-1 flex-col">
                <ContentFitZoom
                  className="space-y-2 pb-2"
                  recalcKey={`${page.plans?.length ?? 0}:${(page.assistantMessage ?? "").slice(0, 120)}`}
                >
                  <CollapsedGeneratingStrip text={page.topStatusText ?? ""} />
                  {(Array.isArray(page.plans) ? page.plans : []).map((p: TravelPlanCardDto) => (
                    <ComparisonPlanCard key={p.id} plan={p} />
                  ))}
                  <div className="max-w-[277px] rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white px-3 py-2 shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)]">
                    <p className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[11px] font-semibold leading-snug text-[#626262]">
                      {page.assistantMessage ?? ""}
                    </p>
                  </div>
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
                        placeholder="输入 plan A / plan B 进入对应时间轴…"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") trySubmitPlanChoice();
                        }}
                        className="min-w-0 flex-1 bg-transparent py-2 pr-14 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#343d4380]"
                      />
                    </div>
                    <button
                      type="button"
                      aria-label="发送"
                      onClick={() => trySubmitPlanChoice()}
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
                    >
                      <ChevronRight className="h-5 w-5" strokeWidth={2} />
                    </button>
                  </div>

                  <div className="pb-2">
                    <AppBottomNav active="首页" journeyFlow={journeyFlow} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
    </AppScreenShell>
  );
};
