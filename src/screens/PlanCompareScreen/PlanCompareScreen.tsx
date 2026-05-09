import { ChevronDown, ChevronLeft, ChevronRight, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { Card, CardContent } from "../../components/ui/card";
import { fetchPlanComparisonPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { PlanComparisonPageDto, TravelPlanCardDto } from "../../lib/api/types";
import { CHAT_PATH, PLANS_PATH, TIMELINE_PATH } from "../../routes";

type PlansLocationState = { travelId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function StarRow({ filled }: { filled: number }): JSX.Element {
  const n = Math.max(0, Math.min(5, Math.round(filled)));
  return (
    <div className="flex justify-center gap-px text-[9px] leading-none text-[#f5c814]">
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < n ? "opacity-100" : "text-[#e5e7eb]"}>
          ★
        </span>
      ))}
    </div>
  );
}

function PlanTimeline({ plan }: { plan: TravelPlanCardDto }): JSX.Element {
  const items = plan.activities;
  return (
    <div className="mt-3 space-y-0">
      {items.map((act, idx) => {
        const last = idx === items.length - 1;
        return (
          <div key={act.id} className="flex gap-3">
            <div className="flex w-3 shrink-0 flex-col items-center pt-1.5">
              <div className="h-2 w-2 shrink-0 rounded-full bg-[#50a9fe]" />
              {!last ? <div className="mt-0.5 w-px flex-1 bg-[#d8d8d8]" aria-hidden /> : null}
            </div>
            <div className="min-w-0 flex-1 pb-4">
              <div className="flex items-start justify-between gap-2">
                <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-medium leading-snug text-[#0f1c2d]">
                  {act.title}
                </p>
                <span className="shrink-0 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] text-[#88a2b4]">
                  {act.durationLabel}
                </span>
              </div>
              {act.tags.length > 0 ? (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {act.tags.map((t) => (
                    <span
                      key={t.id}
                      className="rounded-md border border-[#cfe8ff] bg-[#f5faff] px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] text-[#45627a]"
                    >
                      {t.label}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PlanCard({
  plan,
  travelId,
}: {
  plan: TravelPlanCardDto;
  travelId: string;
}): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="p-3.5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-1 gap-2.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
              <Sparkles className="h-4 w-4 text-[#f5c814]" strokeWidth={1.75} />
            </div>
            <div className="min-w-0 pt-0.5">
              <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#6b7280]">
                {plan.planLabel}
              </p>
              <p
                className={`mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium leading-tight ${titleGradientClass()}`}
              >
                {plan.headline}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="rounded-full bg-[#e8f4ff] px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-medium text-[#2a7bc8]">
              {plan.overallScoreLabel}
            </span>
            {plan.recommended ? (
              <span className="rounded-full bg-[#ffd100]/90 px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] font-medium text-[#333c43]">
                推荐
              </span>
            ) : null}
            <ChevronDown className="h-4 w-4 text-[#9ca3af]" strokeWidth={2} />
          </div>
        </div>

        <PlanTimeline plan={plan} />

        <div className="mt-1 border-t border-[#e8f4ff] pt-3">
          <div className="grid grid-cols-3 gap-2">
            {plan.memberRatings.map((m) => (
              <div
                key={m.id}
                className="rounded-[10px] border border-[#dbeafe] bg-[#fafdff] px-1.5 py-1.5 text-center"
              >
                <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] leading-none">
                  {m.emoji}
                </p>
                <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] text-[#6b7280]">
                  {m.label}
                </p>
                <StarRow filled={m.starsFilled} />
                <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#0f1c2d]">
                  {m.score.toFixed(1)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {plan.compensationTitle && plan.compensationParagraphs && plan.compensationParagraphs.length > 0 ? (
          <div className="mt-3 rounded-[12px] border border-[#bfe8de] bg-[#f3fffb] px-3 py-2.5">
            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#0d5c4a]">
              {plan.compensationTitle}
            </p>
            <ul className="mt-1.5 list-inside list-disc space-y-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] leading-relaxed text-[#2d4a42]">
              {plan.compensationParagraphs.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-3 flex justify-center border-t border-[#f0f4f8] pt-3">
          <Link
            to={TIMELINE_PATH}
            state={{ travelId, planId: plan.id }}
            className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#2a7bc8] hover:underline"
          >
            查看详细时间轴与路线
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export const PlanCompareScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as PlansLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = "plan-a";

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

        <div className="flex min-h-0 flex-1 flex-col px-8 pb-3 pt-3">
          <header className="mb-3 flex items-center gap-1">
            <Link
              to={CHAT_PATH}
              state={chatBackState}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回对话"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
              双方案对比
            </span>
          </header>

          {page ? (
            <button
              type="button"
              className="mb-3 flex w-full items-center justify-between rounded-[11px] border border-[#e5e7eb] bg-[#fafafa] px-3 py-2 text-left"
            >
              <span className="line-clamp-2 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[11.5px] leading-snug text-[#0f1c2d]">
                {page.topStatusText}
              </span>
              <ChevronDown className="h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
            </button>
          ) : null}

          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pb-2">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="pt-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                {page.plans.map((p) => (
                  <PlanCard key={p.id} plan={p} travelId={page.travelId} />
                ))}
                <Card className="rounded-[15px] border-0 bg-[#f4f6f8] shadow-[0px_2px_10px_#00000008]">
                  <CardContent className="px-3.5 py-3">
                    <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12.5px] leading-[20px] text-[#333c43]">
                      {page.assistantMessage}
                    </p>
                  </CardContent>
                </Card>
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
                  placeholder="继续说说你的想法…"
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

          <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </main>
  );
};
