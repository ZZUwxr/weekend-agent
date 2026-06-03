import { CheckCircle2, Home, History, Sparkles } from "lucide-react";
import { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppIconButton,
  AppPageHeader,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { HOME_PATH, ITINERARY_HUB_PATH, TRIP_FEEDBACK_DONE_PATH, TRIP_FEEDBACK_PATH } from "../../routes";

type FlowState = { travelId?: string; planId?: string };

export const TripFeedbackDoneScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as FlowState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const flow = { travelId, planId };

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_FEEDBACK_DONE_PATH) {
      document.title = "感谢反馈 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow="反馈已记录"
          title="谢谢你的反馈"
          subtitle="这次体验会成为下一次规划的偏好记忆。"
          action={<AppIconButton label="返回反馈" to={TRIP_FEEDBACK_PATH} state={flow} />}
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            <AppCard className="overflow-hidden p-0 text-center">
              <div className="bg-[#111827] px-5 py-7 text-white">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#0f766e] text-white shadow-[0_10px_24px_rgba(15,118,110,0.25)]">
                  <CheckCircle2 className="h-8 w-8" strokeWidth={2.2} />
                </div>
                <h2 className="mt-5 text-[24px] font-bold leading-8">已更新你的出行记忆</h2>
                <p className="mt-2 text-[13px] font-medium leading-5 text-white/72">
                  下次推荐时，我会更关注你刚才提到的节奏、路线和活动偏好。
                </p>
              </div>
              <div className="px-4 py-4">
                <AppStatusStrip
                  Icon={Sparkles}
                  title="历史行程已保留"
                  detail="你可以随时回到行程页查看这次安排，或基于它再生成一次。"
                />
              </div>
            </AppCard>

            <div className="grid grid-cols-2 gap-2">
              <Link
                to={ITINERARY_HUB_PATH}
                state={flow}
                className="flex min-h-[92px] flex-col justify-between rounded-[16px] border border-[#e5e7eb] bg-white p-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
              >
                <History className="h-5 w-5 text-[#2456a6]" strokeWidth={2.1} />
                <span className="text-[13px] font-bold leading-5 text-[#111827]">查看历史行程</span>
              </Link>
              <Link
                to={HOME_PATH}
                state={flow}
                className="flex min-h-[92px] flex-col justify-between rounded-[16px] border border-[#e5e7eb] bg-white p-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
              >
                <Home className="h-5 w-5 text-[#0f766e]" strokeWidth={2.1} />
                <span className="text-[13px] font-bold leading-5 text-[#111827]">回到首页</span>
              </Link>
            </div>
          </div>
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton tone="blue" onClick={() => navigate(ITINERARY_HUB_PATH, { state: flow })}>
            查看行程主页
          </AppActionButton>
          <AppBottomNav active="行程" journeyFlow={flow} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
};
