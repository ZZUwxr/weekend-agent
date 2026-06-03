import { CalendarPlus, CheckCircle2, MessageSquareText, Share2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppErrorState,
  AppIconButton,
  AppLoadingState,
  AppPageHeader,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { executeTravelPlan, fetchItineraryHubPage } from "../../lib/api";
import type { ItineraryHubTimelineNodeDto } from "../../lib/api/types";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { ITINERARY_HUB_PATH, TRIP_FEEDBACK_PATH, TRIP_WRAP_PATH } from "../../routes";

type TripWrapLocationState = { travelId?: string; planId?: string };

function summarizeNodes(nodes: ItineraryHubTimelineNodeDto[]): { title: string; detail: string }[] {
  return nodes.slice(0, 5).map((node) => ({
    title: `${node.time} ${node.title}`,
    detail: node.subtitle ?? "已按当前方案完成安排。",
  }));
}

export const TripWrapScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as TripWrapLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;
  const flow = { travelId, planId };
  const { toastMessage, showToast } = useAppToast();
  const [actionPending, setActionPending] = useState(false);
  const [summaryItems, setSummaryItems] = useState<{ title: string; detail: string }[]>([]);
  const [overview, setOverview] = useState("正在整理本次行程摘要。");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_WRAP_PATH) {
      document.title = "行程收尾 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) return;
    let active = true;
    setLoadError(null);
    fetchItineraryHubPage(travelId, planId)
      .then((page) => {
        if (!active) return;
        setSummaryItems(summarizeNodes(page.timelineNodes));
        setOverview(`${page.overviewTimeRange} · ${page.overviewFooterLine}`);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载行程摘要失败");
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  async function recordProviderAction(action: string, label: string): Promise<void> {
    setActionPending(true);
    try {
      const result = await executeTravelPlan(travelId, {
        planId,
        action,
        metadata: { source: "trip_wrap", label },
      });
      showToast(result.message || "外部服务暂未接入，已记录待处理任务");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "记录外部服务任务失败");
    } finally {
      setActionPending(false);
    }
  }

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow={`${planId.toUpperCase()} · 行程收尾`}
          title="这趟行程可以结束了"
          subtitle="我已经把今天的关键安排整理好，确认后会进入简短反馈。"
          action={
            <AppIconButton label="行程主页" to={ITINERARY_HUB_PATH} state={flow}>
              <CheckCircle2 className="h-5 w-5" strokeWidth={2.1} />
            </AppIconButton>
          }
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            <AppCard className="overflow-hidden p-0">
              <div className="bg-[#111827] px-4 py-5 text-white">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white/12 text-[#ffd95a]">
                  <Sparkles className="h-6 w-6" strokeWidth={2.1} />
                </span>
                <h2 className="mt-4 text-[22px] font-bold leading-7">今日安排已完成</h2>
                <p className="mt-2 text-[13px] font-medium leading-5 text-white/72">
                  {overview}
                </p>
              </div>
              <div className="space-y-2 px-4 py-4">
                {loadError ? <AppErrorState message={loadError} /> : null}
                {resolvingTravel ? <AppLoadingState label="正在同步当前行程…" /> : null}
                {!resolvingTravel && !loadError && !summaryItems.length ? <AppLoadingState label="正在加载行程摘要…" /> : null}
                {summaryItems.map((item) => (
                  <div key={item.title} className="rounded-[14px] bg-[#f8fafc] px-3 py-3">
                    <p className="text-[14px] font-bold leading-5 text-[#111827]">{item.title}</p>
                    <p className="mt-0.5 text-[12px] font-medium leading-5 text-[#64748b]">{item.detail}</p>
                  </div>
                ))}
              </div>
            </AppCard>

            <AppCard>
              <h2 className="text-[17px] font-bold text-[#111827]">还能帮你</h2>
              <div className="mt-3 grid grid-cols-3 gap-2">
                <button
                  type="button"
                  disabled={actionPending}
                  onClick={() => void recordProviderAction("share_itinerary", "分享行程")}
                  className="flex min-h-[76px] flex-col items-center justify-center gap-2 rounded-[14px] bg-[#f8fafc] px-2 text-[11px] font-bold text-[#334155]"
                >
                  <Share2 className="h-5 w-5 text-[#2456a6]" strokeWidth={2.1} />
                  分享行程
                </button>
                <button
                  type="button"
                  disabled={actionPending}
                  onClick={() => void recordProviderAction("calendar_reminder", "加入日历")}
                  className="flex min-h-[76px] flex-col items-center justify-center gap-2 rounded-[14px] bg-[#f8fafc] px-2 text-[11px] font-bold text-[#334155]"
                >
                  <CalendarPlus className="h-5 w-5 text-[#0f766e]" strokeWidth={2.1} />
                  加入日历
                </button>
                <button
                  type="button"
                  onClick={() => showToast("可以在反馈里补充体验细节")}
                  className="flex min-h-[76px] flex-col items-center justify-center gap-2 rounded-[14px] bg-[#f8fafc] px-2 text-[11px] font-bold text-[#334155]"
                >
                  <MessageSquareText className="h-5 w-5 text-[#8a5a00]" strokeWidth={2.1} />
                  补充感受
                </button>
              </div>
            </AppCard>

            <AppStatusStrip
              Icon={CheckCircle2}
              title="确认结束后不会删除行程"
              detail="你仍然可以在行程主页查看历史记录，也可以再次使用这个计划。"
            />
          </div>
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton tone="blue" onClick={() => navigate(TRIP_FEEDBACK_PATH, { state: flow })}>
            确认结束，填写反馈
          </AppActionButton>
          <Link
            to={ITINERARY_HUB_PATH}
            state={flow}
            className="flex min-h-11 items-center justify-center rounded-[12px] bg-white text-[13px] font-bold text-[#475569] shadow-[0_6px_18px_rgba(15,23,42,0.06)]"
          >
            稍后再评价
          </Link>
          <AppBottomNav active="行程" journeyFlow={flow} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
};
