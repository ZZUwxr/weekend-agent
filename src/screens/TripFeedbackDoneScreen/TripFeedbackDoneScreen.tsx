import { ChevronRight } from "lucide-react";
import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { FIGMA_TRIP_FEEDBACK_DONE_211 } from "../../lib/api/mock/figma-trip-post-feedback-assets";
import { FIGMA_HOME_4737 } from "../../lib/api/mock/figma-home-4737-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { CHAT_PATH, HOME_PATH, ITINERARY_HUB_PATH, TRIP_FEEDBACK_PATH } from "../../routes";

type FlowState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(24.482deg,rgb(95,115,128)_16.391%,rgb(62,82,101)_73.16%,rgb(42,114,176)_96.32%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

/**
 * Figma node 211:344 · 行程反馈完成感谢页（接在 187:568 后）
 */
export const TripFeedbackDoneScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as FlowState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  useEffect(() => {
    const prev = document.title;
    if (pathname.includes("trip-feedback-done")) {
      document.title = "感谢反馈 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  return (
    <AppScreenShell frameClassName="bg-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <img
          src={FIGMA_TRIP_FEEDBACK_DONE_211.bgBlobA}
          alt=""
          className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
        />
        <img
          src={FIGMA_TRIP_FEEDBACK_DONE_211.bgBlobB}
          alt=""
          className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-[0.93]"
        />
      </div>

      <EmbeddedStatusBarImage src={FIGMA_TRIP_FEEDBACK_DONE_211.statusBar} className="relative z-[1]" height={61} width={402} />

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-[27px] pb-3 pt-3">
        <ContentFitZoom className="pb-8 pt-4" recalcKey="feedback-done">
          <Link
            to={TRIP_FEEDBACK_PATH}
            state={flow}
            className="mb-6 inline-block text-[12px] font-medium text-[#64748b] underline-offset-2 hover:text-[#2563eb] hover:underline"
          >
            ← 返回反馈
          </Link>

          <div className="relative mx-auto flex max-w-[298px] flex-col items-center rounded-[15px] border border-[#50a9fe] bg-white px-5 pb-6 pt-8 shadow-[0px_4px_20px_#d0def8]">
            <img src={FIGMA_TRIP_FEEDBACK_DONE_211.sparkle} alt="" width={40} height={40} className="mb-4 h-10 w-10 object-contain" />
            <h1
              className={`mb-2 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[17px] font-semibold leading-snug ${titleGradientClass()}`}
            >
              感谢你的反馈
            </h1>
            <p className="mb-8 text-center [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] font-medium leading-relaxed text-[#626262]">
              你的每一条建议我们都在认真记录，
              <br />
              下次会为你和家人安排得更贴心～
            </p>

            <div className="relative mx-auto mb-8 flex h-[120px] w-full max-w-[220px] items-end justify-center">
              <img
                src={FIGMA_HOME_4737.historyEmptyBg}
                alt=""
                className="pointer-events-none absolute inset-x-0 bottom-0 top-2 mx-auto w-[92%] object-contain object-bottom opacity-90"
              />
              <img
                src={FIGMA_HOME_4737.historyEmptyFigure}
                alt=""
                className="relative z-[1] h-[100px] w-auto max-w-[90%] object-contain object-bottom"
              />
            </div>

            <Link
              to={HOME_PATH}
              state={flow}
              className="mb-4 w-full rounded-[14px] bg-[#ffd100] px-6 py-3 text-center shadow-[0px_4px_16px_rgba(245,200,20,0.38)] transition-opacity hover:opacity-95 active:opacity-90"
            >
              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#343d43]">返回首页</span>
            </Link>
            <Link
              to={ITINERARY_HUB_PATH}
              state={flow}
              className="text-center [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#2563eb] underline-offset-4 hover:underline"
            >
              查看历史行程
            </Link>
          </div>
        </ContentFitZoom>

        <div className="mt-auto flex flex-col gap-3 pt-2">
          <div className="flex items-center gap-2">
            <Link
              to={CHAT_PATH}
              state={{ message: "关于刚才的反馈我还想补充几句", travelId }}
              className="flex flex-1 items-center justify-between rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white px-4 py-3 shadow-[0px_2px_8px_rgba(0,0,0,0.06)] transition-opacity hover:opacity-95"
            >
              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#94a3b8]">
                还有想说的？进对话继续说
              </span>
              <ChevronRight className="h-5 w-5 shrink-0 text-[#343d43]" strokeWidth={2} aria-hidden />
            </Link>
          </div>
          <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </AppScreenShell>
  );
};
