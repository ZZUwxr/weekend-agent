import {
  Bell,
  Calendar,
  Check,
  ClipboardList,
  Map as MapIcon,
  Pencil,
  RefreshCw,
  Share2,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
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
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { fetchItineraryHubPage, reviseTravelPlan } from "../../lib/api";
import { executeTravelPlan } from "../../lib/api";
import type {
  ItineraryHubHistoryItemDto,
  ItineraryHubPageDto,
  ItineraryHubQuickActionDto,
  ItineraryHubTimelineNodeDto,
} from "../../lib/api/types";
import { setCurrentTravel } from "../../lib/currentTravel";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { cn } from "../../lib/utils";
import {
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PLANS_PATH,
  TIMELINE_PATH,
  TRIP_LIVE_MAP_PATH,
  TRIP_WRAP_PATH,
} from "../../routes";
import { ItineraryHubEmptyView } from "./ItineraryHubEmptyView";

type HubLocationState = { travelId?: string; planId?: string };

function TimelineNode({ node, isLast }: { node: ItineraryHubTimelineNodeDto; isLast: boolean }): JSX.Element {
  const isDone = node.kind === "done";
  const isActive = node.kind === "active";

  return (
    <li className="relative flex gap-3">
      <div className="flex w-9 shrink-0 flex-col items-center">
        <span
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full text-[15px] font-bold shadow-sm",
            isDone && "bg-[#0f766e] text-white",
            isActive && "bg-[#ffd95a] text-[#3f3421]",
            !isDone && !isActive && "border border-[#dbe3ee] bg-white text-[#475569]",
          )}
        >
          {isDone ? <Check className="h-4 w-4" strokeWidth={2.5} /> : node.iconEmoji}
        </span>
        {!isLast ? <span className="mt-1 h-full min-h-8 w-px bg-[#dbe3ee]" /> : null}
      </div>
      <div
        className={cn(
          "min-w-0 flex-1 rounded-[14px] px-3 py-2.5",
          isActive ? "border border-[#fde68a] bg-[#fff9db]" : "bg-white/70",
          !isLast && "mb-2",
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-bold leading-5 text-[#111827]">{node.title}</p>
            {node.subtitle ? (
              <p className="mt-0.5 text-[12px] leading-5 text-[#64748b]">{node.subtitle}</p>
            ) : null}
          </div>
          <span className="shrink-0 text-[12px] font-bold text-[#475569]">{node.time}</span>
        </div>
      </div>
    </li>
  );
}

function QuickAction({
  action,
  flow,
  onProviderAction,
}: {
  action: ItineraryHubQuickActionDto;
  flow: { travelId: string; planId: string };
  onProviderAction: (action: ItineraryHubQuickActionDto) => void;
}): JSX.Element {
  const Icon =
    action.kind === "map"
      ? MapIcon
      : action.kind === "share"
        ? Share2
        : action.kind === "calendar"
          ? Calendar
          : action.kind === "edit"
            ? Pencil
            : XCircle;
  const tone = action.kind === "cancel" ? "text-[#dc2626] bg-[#fff1f2]" : "text-[#2456a6] bg-[#edf5ff]";
  const classes =
    "flex min-h-[76px] flex-col items-center justify-center gap-2 rounded-[16px] border border-[#e5e7eb] bg-white px-2 text-center shadow-[0_8px_20px_rgba(15,23,42,0.05)] transition active:scale-[0.98]";

  if (action.kind === "map") {
    return (
      <Link to={TRIP_LIVE_MAP_PATH} state={flow} onClick={() => setCurrentTravel(flow)} className={classes}>
        <span className={cn("flex h-9 w-9 items-center justify-center rounded-full", tone)}>
          <Icon className="h-4 w-4" strokeWidth={2.1} />
        </span>
        <span className="text-[11px] font-bold leading-4 text-[#334155]">{action.label}</span>
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onProviderAction(action)}
      className={classes}
    >
      <span className={cn("flex h-9 w-9 items-center justify-center rounded-full", tone)}>
        <Icon className="h-4 w-4" strokeWidth={2.1} />
      </span>
      <span className={cn("text-[11px] font-bold leading-4", action.kind === "cancel" ? "text-[#dc2626]" : "text-[#334155]")}>
        {action.label}
      </span>
    </button>
  );
}

function HistoryCard({
  item,
}: {
  item: ItineraryHubHistoryItemDto;
}): JSX.Element {
  const flow = { travelId: item.id, planId: item.planId || "plan-a" };
  return (
    <AppCard as="article" className="p-3">
      <div className="flex gap-3">
        <div className="flex h-[74px] w-[74px] shrink-0 items-center justify-center overflow-hidden rounded-[14px] bg-[#f1f5f9] text-[28px]">
          {item.thumbImageUrl ? (
            <img src={item.thumbImageUrl} alt="" className="h-full w-full object-cover" />
          ) : (
            <span>{item.thumbEmoji ?? "📍"}</span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[12px] font-semibold leading-5 text-[#64748b]">{item.dateLine}</p>
          <h3 className="mt-0.5 text-[14px] font-bold leading-5 text-[#111827]">{item.routeSummary}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            <AppPill className="bg-[#fff7df] text-[#92400e]">{item.ratingStars} 星体验</AppPill>
            <AppPill className="bg-[#eefcf6] text-[#047857]">{item.priceText}</AppPill>
          </div>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Link
          to={TIMELINE_PATH}
          state={flow}
          className="flex min-h-11 items-center justify-center rounded-[12px] bg-[#f1f5f9] text-[13px] font-bold text-[#334155]"
        >
          查看详情
        </Link>
        <Link
          to={PLANS_PATH}
          state={flow}
          className="flex min-h-11 items-center justify-center gap-2 rounded-[12px] bg-[#111827] text-[13px] font-bold text-white"
        >
          <RefreshCw className="h-4 w-4" strokeWidth={2.1} />
          再来一次
        </Link>
      </div>
    </AppCard>
  );
}

export const ItineraryHubScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as HubLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;
  const flow = useMemo(() => ({ travelId, planId }), [travelId, planId]);

  const [page, setPage] = useState<ItineraryHubPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hubVoiceText, setHubVoiceText] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === ITINERARY_HUB_PATH) {
      document.title = "行程 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) {
      setPage(null);
      setLoadError(null);
      return;
    }
    let active = true;
    setCurrentTravel({ travelId, planId });
    setLoadError(null);
    setPage(null);
    fetchItineraryHubPage(travelId, planId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  async function handleHubComposerSubmit(): Promise<void> {
    const text = hubVoiceText.trim();
    if (!text) {
      showToast("请输入想调整的行程内容");
      return;
    }

    setSubmitPending(true);
    setLoadError(null);
    try {
      const revised = await reviseTravelPlan(travelId, {
        message: text,
        targetPlanId: planId,
        revisionMode: "partial",
      });
      setPage(revised.updatedItineraryHub ?? await fetchItineraryHubPage(travelId, planId));
      setHubVoiceText("");
      showToast("已更新当前行程");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改行程失败");
    } finally {
      setSubmitPending(false);
    }
  }

  async function handleQuickAction(action: ItineraryHubQuickActionDto): Promise<void> {
    if (action.kind === "edit") {
      showToast("可以在底部输入修改需求");
      return;
    }
    const actionMap: Partial<Record<ItineraryHubQuickActionDto["kind"], string>> = {
      share: "share_itinerary",
      calendar: "calendar_reminder",
      cancel: "cancel_trip",
    };
    const providerAction = actionMap[action.kind] ?? action.kind;
    setSubmitPending(true);
    setLoadError(null);
    try {
      const result = await executeTravelPlan(travelId, {
        planId,
        action: providerAction,
        metadata: { source: "itinerary_hub", label: action.label },
      });
      showToast(result.message || "外部服务暂未接入，已记录待处理任务");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "记录外部服务任务失败");
    } finally {
      setSubmitPending(false);
    }
  }

  if (!travelId && !resolvingTravel) {
    return <ItineraryHubEmptyView travelId={travelId} planId={planId} />;
  }

  const activeNode = page?.timelineNodes.find((node) => node.kind === "active");
  const nextNode = page?.timelineNodes.find((node) => node.kind === "upcoming");

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      {page ? (
        <EmbeddedStatusBarImage src={page.statusBarImageUrl} className="relative z-20" height={61} width={402} />
      ) : (
        <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/60" />
      )}

      <div className={cn("relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2", tabScreenPrimaryColumnPaddingXClass)}>
        <AppPageHeader
          eyebrow={`${planId.toUpperCase()} · 当前行程`}
          title={page?.navTitle ?? "行程"}
          subtitle={page ? `${page.overviewTimeRange} · ${page.overviewFooterLine}` : "正在同步你的行程"}
          action={
            page?.showNotificationsBell ? (
              <AppIconButton label="通知" onClick={() => showToast("暂无新的行程通知")}>
                <Bell className="h-5 w-5" strokeWidth={2.1} />
              </AppIconButton>
            ) : null
          }
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          {resolvingTravel ? (
            <AppLoadingState label="正在同步当前行程..." />
          ) : loadError && !page ? (
            <AppErrorState message={loadError} />
          ) : !page ? (
            <AppLoadingState label="正在加载行程..." />
          ) : (
            <div className="space-y-3">
              <AppCard className="overflow-hidden p-0">
                <div className="bg-[#111827] px-4 py-4 text-white">
                  <div className="flex items-start gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/14">
                      <Sparkles className="h-5 w-5 text-[#ffd95a]" strokeWidth={2.1} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-semibold leading-5 text-white/72">现在进行到</p>
                      <h2 className="mt-1 text-[20px] font-bold leading-6">{page.currentStageTitle}</h2>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <AppPill className="bg-white/12 text-white">{page.currentStageStatusBadge}</AppPill>
                        <AppPill className="bg-[#ffd95a] text-[#3f3421]">{planId.toUpperCase()}</AppPill>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    {page.overviewFlowChips.map((chip) => (
                      <AppPill key={chip.id} className="bg-[#f8fafc] text-[#334155]">
                        <span className="mr-1">{chip.iconEmoji}</span>
                        {chip.label}
                      </AppPill>
                    ))}
                  </div>
                </div>
              </AppCard>

              {activeNode || nextNode ? (
                <div className="grid grid-cols-2 gap-2">
                  {activeNode ? (
                    <AppStatusStrip
                      Icon={Check}
                      title={activeNode.title}
                      detail={`${activeNode.time}${activeNode.subtitle ? ` · ${activeNode.subtitle}` : ""}`}
                      className="h-full"
                    />
                  ) : null}
                  {nextNode ? (
                    <AppStatusStrip
                      Icon={Calendar}
                      title="下一步"
                      detail={`${nextNode.time} · ${nextNode.title}`}
                      className="h-full"
                    />
                  ) : null}
                </div>
              ) : null}

              <AppCard>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h2 className="text-[17px] font-bold text-[#111827]">路线进度</h2>
                  <Link to={TIMELINE_PATH} state={flow} className="text-[12px] font-bold text-[#2456a6]">
                    完整时间轴
                  </Link>
                </div>
                <ol>
                  {page.timelineNodes.map((node, index) => (
                    <TimelineNode
                      key={node.id}
                      node={node}
                      isLast={index === page.timelineNodes.length - 1}
                    />
                  ))}
                </ol>
              </AppCard>

              <div className="grid grid-cols-3 gap-2">
                {page.quickActions.map((action) => (
                  <QuickAction
                    key={action.id}
                    action={action}
                    flow={flow}
                    onProviderAction={(next) => void handleQuickAction(next)}
                  />
                ))}
              </div>

              <div>
                <div className="mb-2 flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-[#2456a6]" strokeWidth={2.1} />
                  <h2 className="text-[17px] font-bold text-[#111827]">{page.historySectionTitle}</h2>
                </div>
                <div className="space-y-2.5">
                  {page.historyItems.map((item) => (
                    <HistoryCard key={item.id} item={item} />
                  ))}
                </div>
              </div>

              {loadError ? (
                <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                  {loadError}
                </div>
              ) : null}
            </div>
          )}
        </div>

        <div className={tabScreenComposerDockClass}>
          <div className="grid grid-cols-2 gap-2">
            <AppActionButton tone="muted" onClick={() => navigate(PAYMENT_CONFIRMATION_PATH, { state: flow })}>
              查看确认单
            </AppActionButton>
            <AppActionButton tone="blue" onClick={() => navigate(TRIP_LIVE_MAP_PATH, { state: flow })}>
              实时地图
            </AppActionButton>
          </div>
          <AppActionButton tone="green" onClick={() => navigate(TRIP_WRAP_PATH, { state: flow })}>
            结束行程并反馈
          </AppActionButton>
          <AppComposer
            value={hubVoiceText}
            onChange={setHubVoiceText}
            onSubmit={() => void handleHubComposerSubmit()}
            pending={submitPending}
            placeholder={submitPending ? "正在修改行程..." : "补充想调整的行程内容..."}
          />
          <AppBottomNav active="行程" journeyFlow={flow} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
};
