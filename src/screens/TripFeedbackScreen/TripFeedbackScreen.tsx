import type { ReactNode } from "react";
import { ChevronDown, ChevronRight, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { AppScreenShell } from "../../components/AppScreenShell";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { FIGMA_TRIP_FEEDBACK_187 } from "../../lib/api/mock/figma-trip-post-feedback-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { CHAT_PATH, TRIP_FEEDBACK_DONE_PATH, TRIP_WRAP_PATH } from "../../routes";

type FlowState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(24.482deg,rgb(95,115,128)_16.391%,rgb(62,82,101)_73.16%,rgb(42,114,176)_96.32%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function TripGlowCardFrame({ children }: { children: ReactNode }): JSX.Element {
  return (
    <div className="relative overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_0px_#d0def8]">
      <img
        src={FIGMA_TRIP_FEEDBACK_187.cardGlow1}
        alt=""
        className="pointer-events-none absolute left-[114px] top-[33px] z-0 h-[242px] w-[293px] max-w-none object-cover opacity-[0.32]"
      />
      <img
        src={FIGMA_TRIP_FEEDBACK_187.cardGlow2}
        alt=""
        className="pointer-events-none absolute -left-[110px] -top-[147px] z-0 h-[220px] w-[271px] max-w-none object-cover opacity-[0.32]"
      />
      <div className="relative z-[2] isolate">{children}</div>
    </div>
  );
}

const TAG_OPTIONS = [
  { id: "route", label: "路线安排合理" },
  { id: "time", label: "时间节奏刚好" },
  { id: "rec", label: "推荐内容靠谱" },
  { id: "comm", label: "沟通顺畅及时" },
  { id: "more", label: "还有可提升空间" },
] as const;

/**
 * Figma node 187:568 · 行程收尾后体验反馈（接在 trip-wrap 后）
 * 资源与 159:6179 同系；若稿面有单拆导出可替换 `figma-trip-post-feedback-assets`。
 */
export const TripFeedbackScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as FlowState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [rating, setRating] = useState(0);
  const [tags, setTags] = useState<Set<string>>(() => new Set());
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname.includes("trip-feedback") && !pathname.includes("done")) {
      document.title = "行程反馈 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  const toggleTag = (id: string): void => {
    setTags((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const goDone = (): void => {
    navigate(TRIP_FEEDBACK_DONE_PATH, { state: { ...flow, rating, tagIds: [...tags] } });
  };

  return (
    <AppScreenShell frameClassName="bg-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_TRIP_FEEDBACK_187.bgBlobA}
          alt=""
          className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
        />
        <img
          src={FIGMA_TRIP_FEEDBACK_187.bgBlobB}
          alt=""
          className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-[0.93]"
        />
      </div>

      <EmbeddedStatusBarImage
        src={FIGMA_TRIP_FEEDBACK_187.statusBar}
        className="relative z-[1]"
        height={61}
        width={402}
      />

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-[27px] pb-3 pt-3">
        <ContentFitZoom
          className="space-y-[18px] pb-8"
          recalcKey={`${rating}:${[...tags].sort().join(",")}`}
        >
          <Link
            to={TRIP_WRAP_PATH}
            state={flow}
            className="inline-block text-[12px] font-medium text-[#64748b] underline-offset-2 hover:text-[#2563eb] hover:underline"
          >
            ← 返回上一屏
          </Link>

          <TripGlowCardFrame>
            <div className="px-[10px] pb-4 pt-[14px]">
              <header className="relative mb-3 flex items-start gap-2 pr-7">
                <img src={FIGMA_TRIP_FEEDBACK_187.sparkle} alt="" width={24} height={24} className="h-6 w-6 shrink-0 object-contain" />
                <h2
                  className={`min-w-0 flex-1 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-[20px] ${titleGradientClass()}`}
                >
                  觉得这次安排怎么样？
                </h2>
                <ChevronDown className="absolute right-1 top-2 h-[11px] w-[9px] shrink-0 text-[#9ca3af]" strokeWidth={2} aria-hidden />
              </header>
              <p className="relative z-[3] mb-4 pr-6 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12.5px] font-normal leading-[20px] text-[#626262]">
                你的感受会帮我们更好地规划下一段出行～
              </p>
              <div className="flex justify-center gap-2 pb-2" role="group" aria-label="星级评分">
                {[1, 2, 3, 4, 5].map((n) => {
                  const on = rating >= n;
                  return (
                    <button
                      key={n}
                      type="button"
                      aria-label={`${n} 星`}
                      aria-pressed={on}
                      onClick={() => setRating(n)}
                      className="rounded-lg p-1 transition-transform active:scale-95"
                    >
                      <Star
                        className={`h-[26px] w-[26px] ${on ? "fill-[#fcd34d] text-[#eab308]" : "fill-transparent text-[#d1d5db]"}`}
                        strokeWidth={1.75}
                      />
                    </button>
                  );
                })}
              </div>
            </div>
          </TripGlowCardFrame>

          <TripGlowCardFrame>
            <div className="px-3 pb-5 pt-4">
              <header className="relative mb-2 flex items-start gap-2 pr-7">
                <img src={FIGMA_TRIP_FEEDBACK_187.sparkle} alt="" width={24} height={24} className="h-6 w-6 shrink-0 object-contain" />
                <h2
                  className={`min-w-0 flex-1 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-[20px] ${titleGradientClass()}`}
                >
                  哪些点让你印象深刻？
                </h2>
                <ChevronDown className="absolute right-1 top-2 h-[11px] w-[9px] shrink-0 text-[#9ca3af]" strokeWidth={2} aria-hidden />
              </header>
              <p className="relative z-[3] mb-3 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[11px] font-normal leading-[18px] text-[#626262]">
                可多选
              </p>
              <div className="flex flex-wrap gap-2">
                {TAG_OPTIONS.map((t) => {
                  const sel = tags.has(t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      aria-pressed={sel}
                      onClick={() => toggleTag(t.id)}
                      className={`min-h-[35px] rounded-[7px] border-[0.5px] px-2.5 py-2 shadow-[0px_0.7px_1.4px_0px_#d1e8ff] transition-opacity hover:opacity-90 ${
                        sel
                          ? "border-[#eab308] bg-[radial-gradient(ellipse_at_center,rgba(250,242,171,0.85)_0%,rgba(255,255,255,0.95)_100%)]"
                          : "border-[#faf2ac] bg-[radial-gradient(ellipse_at_center,rgba(250,242,171,0.45)_0%,rgba(255,255,255,0.95)_100%)]"
                      }`}
                    >
                      <span className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10px] font-semibold leading-tight text-[#343d43]">
                        {t.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </TripGlowCardFrame>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              type="button"
              onClick={goDone}
              className="min-w-[120px] rounded-bl-[15.417px] rounded-br-[15.417px] rounded-tl-[15.417px] rounded-tr-[15.417px] bg-[#ffd100] px-6 py-2 shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)] transition-opacity hover:opacity-95"
            >
              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold leading-[22px] text-[#343d43]">
                提交反馈
              </span>
            </button>
            <button
              type="button"
              onClick={goDone}
              className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#94a3b8] underline-offset-4 hover:text-[#64748b] hover:underline"
            >
              暂不评价
            </button>
          </div>
        </ContentFitZoom>

        <div className={tabScreenComposerDockMtAutoClass}>
          <div className="flex items-center gap-2">
            <div className="relative flex min-h-[41px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-3 pr-[46px] shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
              <img
                src={FIGMA_TRIP_FEEDBACK_187.voiceChip}
                alt=""
                className="absolute right-3 top-1/2 z-[2] h-7 w-[34px] -translate-y-1/2 select-none object-contain"
              />
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="补充想说的…"
                className="min-w-0 flex-1 bg-transparent py-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#343d4380]"
              />
            </div>
            <Link
              to={CHAT_PATH}
              state={{ message: input.trim() || "我想聊聊这次行程的体验", travelId }}
              aria-label="进入对话"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
            >
              <ChevronRight className="h-5 w-5" strokeWidth={2} aria-hidden />
            </Link>
          </div>
          <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </AppScreenShell>
  );
};
