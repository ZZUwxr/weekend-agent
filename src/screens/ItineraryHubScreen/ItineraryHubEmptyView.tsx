import { Bell, ChevronRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { JourneyBottomNav } from "../../components/JourneyBottomNav";
import {
  tabScreenComposerDockMtAutoClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { FIGMA_HOME_4737 } from "../../lib/api/mock/figma-home-4737-assets";
import { FIGMA_ITINERARY_HUB_148_254 } from "../../lib/api/mock/figma-itinerary-hub-148-254-assets";
import { cn } from "../../lib/utils";
import { CHAT_PATH } from "../../routes";

type Props = { travelId: string; planId: string };

function SectionSparkle(): JSX.Element {
  return <Sparkles className="h-4 w-4 shrink-0 text-[#eab308] drop-shadow-[0_0_8px_rgba(234,179,8,0.55)]" strokeWidth={1.75} />;
}

/** Figma 148:254 · 行程 Tab 初始态：今日行程 / 当前阶段 / 历史行程（与稿面一致） */
export function ItineraryHubEmptyView({ travelId, planId }: Props): JSX.Element {
  const [text, setText] = useState("");

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffbeb_0%,#fffef9_38%,#ffffff_100%)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_ITINERARY_HUB_148_254.bgBlobB}
          alt=""
          className="absolute -left-[100px] top-[42%] h-[760px] w-[1080px] max-w-none opacity-[0.06]"
        />
      </div>

      <EmbeddedStatusBarImage src={FIGMA_ITINERARY_HUB_148_254.statusBar} className="relative z-[2]" height={61} width={402} />

      <div
        className={cn(
          "relative z-[1] flex min-h-0 flex-1 flex-col pb-2 pt-3",
          tabScreenPrimaryColumnPaddingXClass,
        )}
      >
        <header className="mb-3 flex shrink-0 items-center justify-between gap-2">
          <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-bold text-[#1e293b]">行程</h1>
          <button
            type="button"
            aria-label="通知"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#64748b] hover:bg-black/[0.04]"
          >
            <Bell className="h-5 w-5" strokeWidth={1.75} />
          </button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ContentFitZoom className="space-y-3 pb-3" recalcKey="itinerary-hub-empty">
            {/* 今日行程 + 当前阶段（单卡上下分区） */}
            <div className="overflow-hidden rounded-[18px] border border-[#e5e7eb]/90 bg-white shadow-[0px_6px_24px_rgba(15,23,42,0.06)]">
              <div className="bg-[linear-gradient(95deg,#fde047_0%,#fef08a_42%,#fef9c3_100%)] px-4 py-3.5">
                <div className="flex items-start gap-2.5">
                  <SectionSparkle />
                  <div className="min-w-0">
                    <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-bold leading-tight text-[#1e293b]">
                      今日行程
                    </p>
                    <p className="mt-1 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[13px] font-semibold text-[#ca8a04]">
                      还没有安排
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-t border-[#f1f5f9] bg-white px-4 pb-4 pt-4">
                <div className="mb-2.5 flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-start gap-2">
                    <div className="mt-0.5">
                      <SectionSparkle />
                    </div>
                    <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#334155]">当前阶段</span>
                  </div>
                  <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-[#f1f5f9] px-2.5 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#64748b]">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#94a3b8]" aria-hidden />
                    未开始
                  </span>
                </div>
                <p className="mb-4 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] font-medium leading-relaxed text-[#94a3b8]">
                  创建行程后，这里会显示出发到达与途中提醒
                </p>
                <Link
                  to={CHAT_PATH}
                  state={{ message: "我想创建第一条行程", travelId }}
                  className="flex w-full items-center justify-center rounded-[12px] bg-[#ffd100] py-3.5 shadow-[0px_4px_14px_rgba(245,200,20,0.35)] transition-opacity hover:opacity-95"
                >
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-semibold text-[#78350f]">
                    立即创建第一条行程
                  </span>
                </Link>
              </div>
            </div>

            {/* 历史行程 */}
            <div className="overflow-hidden rounded-[16px] border border-[#e2e8f0] bg-white shadow-[0px_2px_12px_rgba(15,23,42,0.04)]">
              <div className="flex items-center gap-2 border-b border-[#f1f5f9] px-4 py-3">
                <SectionSparkle />
                <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#334155]">历史行程</span>
              </div>
              <div className="relative flex flex-col items-center px-4 pb-6 pt-5">
                <div className="relative mx-auto flex h-[130px] w-full max-w-[220px] items-end justify-center">
                  <img
                    src={FIGMA_HOME_4737.historyEmptyBg}
                    alt=""
                    className="pointer-events-none absolute inset-x-0 bottom-0 top-0 mx-auto max-h-full w-[85%] object-contain object-bottom opacity-90"
                  />
                  <img
                    src={FIGMA_HOME_4737.historyEmptyCorner}
                    alt=""
                    className="pointer-events-none absolute bottom-1 right-[14%] z-[2] h-14 w-14 object-contain opacity-95"
                  />
                  <img
                    src={FIGMA_HOME_4737.historyEmptyFigure}
                    alt=""
                    className="relative z-[1] h-[115px] w-auto max-w-[90%] object-contain object-bottom"
                  />
                </div>
                <p className="mt-2 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#64748b]">
                  你还没有历史安排
                </p>
              </div>
            </div>
          </ContentFitZoom>

          <div className={tabScreenComposerDockMtAutoClass}>
            <div className="flex min-w-0 items-center gap-2">
              <div className="relative flex min-h-[46px] min-w-0 flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
                <img
                  src={FIGMA_ITINERARY_HUB_148_254.voiceInput}
                  alt=""
                  className="h-7 w-[34px] shrink-0 object-contain"
                  height={28}
                  width={34}
                />
                <input
                  type="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="有疑问可以在这里补充…"
                  className="min-w-0 flex-1 bg-transparent py-2 pl-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#333c4380]"
                />
              </div>
              <Link
                to={CHAT_PATH}
                state={{ message: text.trim() || "我想开始一段新的出行计划", travelId }}
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
}
