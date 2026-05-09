import {
  Bell,
  Calendar,
  Check,
  ClipboardList,
  Map as MapIcon,
  MapPin,
  Pencil,
  Share2,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { JourneyBottomNav } from "../../components/JourneyBottomNav";
import { Card, CardContent } from "../../components/ui/card";
import { fetchItineraryHubPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { ItineraryHubPageDto, ItineraryHubQuickActionDto } from "../../lib/api/types";
import {
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PLANS_PATH,
  TIMELINE_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../../routes";

type HubLocationState = { travelId?: string; planId?: string };

function StarRow({ n }: { n: number }): JSX.Element {
  return (
    <span className="text-[11px] text-amber-400" aria-label={`${n} 星`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i}>{i <= n ? "★" : "☆"}</span>
      ))}
    </span>
  );
}

function QuickActionButton({
  action,
  flow,
}: {
  action: ItineraryHubQuickActionDto;
  flow: { travelId: string; planId: string };
}): JSX.Element {
  const shell =
    "flex h-[4.25rem] w-full flex-col items-center justify-center gap-1 rounded-xl border border-[#e2e8f0] bg-white shadow-[0px_1px_6px_rgba(0,0,0,0.04)] transition-opacity hover:opacity-90 active:scale-[0.98]";
  const labelCls =
    "[font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#334155]";
  const iconBlue = "h-5 w-5 text-[#2563eb]";
  const iconRed = "h-5 w-5 text-red-500";

  if (action.kind === "map") {
    return (
      <Link to={TRIP_LIVE_MAP_PATH} state={flow} className={shell}>
        <MapIcon className={iconBlue} strokeWidth={1.75} />
        <span className={labelCls}>{action.label}</span>
      </Link>
    );
  }

  const Icon =
    action.kind === "share"
      ? Share2
      : action.kind === "calendar"
        ? Calendar
        : action.kind === "edit"
          ? Pencil
          : XCircle;
  const cls = action.kind === "cancel" ? iconRed : iconBlue;

  return (
    <button type="button" className={shell}>
      <Icon className={cls} strokeWidth={1.75} />
      <span className={action.kind === "cancel" ? `${labelCls} text-red-600` : labelCls}>
        {action.label}
      </span>
    </button>
  );
}

export const ItineraryHubScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as HubLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<ItineraryHubPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

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
    let active = true;
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

  const flow = { travelId, planId };

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-[#f3f6fa]">
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
          <div className="h-[61px] w-full shrink-0 bg-white/90" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-4 pb-2 pt-2">
          <header className="mb-3 flex items-center justify-between gap-2">
            <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-bold text-[#1e293b]">
              {page?.navTitle ?? "行程"}
            </h1>
            {page?.showNotificationsBell ? (
              <button
                type="button"
                aria-label="通知"
                className="flex h-10 w-10 items-center justify-center rounded-full text-[#64748b] hover:bg-black/[0.04]"
              >
                <Bell className="h-5 w-5" strokeWidth={1.75} />
              </button>
            ) : (
              <span className="w-10" />
            )}
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pb-2">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
            ) : (
              <>
                <div className="rounded-[18px] bg-gradient-to-br from-[#e3f0ff] to-[#dceaff] px-3 py-3 shadow-[inset_0_0_0_1px_rgba(74,144,226,0.12)]">
                  <div className="mb-2 flex items-center gap-2">
                    <Calendar className="h-4 w-4 shrink-0 text-[#2563eb]" strokeWidth={1.75} />
                    <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#1e3a5f]">
                      {page.overviewTimeRange}
                    </span>
                  </div>
                  <div className="mb-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#334155]">
                    {page.overviewFlowChips.map((c, idx) => (
                      <span key={c.id} className="inline-flex items-center gap-1">
                        {idx > 0 ? <span className="text-[#94a3b8]">→</span> : null}
                        <span className="text-base leading-none">{c.iconEmoji}</span>
                        <span>{c.label}</span>
                      </span>
                    ))}
                  </div>
                  <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#5b7aa6]">
                    {page.overviewFooterLine}
                  </p>
                </div>

                <Card className="overflow-hidden rounded-[18px] border border-[#dbeafe] bg-white shadow-[0px_4px_18px_rgba(74,144,226,0.1)]">
                  <CardContent className="p-3">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="flex min-w-0 items-center gap-2">
                        <MapPin className="h-4 w-4 shrink-0 text-[#2563eb]" strokeWidth={1.75} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                          {page.currentStageTitle}
                        </span>
                      </div>
                      <span className="shrink-0 rounded-full bg-[#e0f2fe] px-2.5 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#0369a1]">
                        {page.currentStageStatusBadge}
                      </span>
                    </div>

                    <ul className="relative space-y-0">
                      {page.timelineNodes.map((node, index) => {
                        const isLast = index === page.timelineNodes.length - 1;
                        const contentInner = (
                          <>
                            <div className="flex items-baseline gap-2">
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#0f172a]">
                                {node.time}
                              </span>
                              <span className="text-base leading-none">{node.iconEmoji}</span>
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#334155]">
                                {node.title}
                              </span>
                            </div>
                            {node.subtitle ? (
                              <p className="mt-0.5 pl-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-medium text-[#64748b]">
                                🕐 {node.subtitle}
                              </p>
                            ) : null}
                          </>
                        );

                        return (
                          <li key={node.id} className="relative flex gap-3">
                            <div className="flex w-8 shrink-0 flex-col items-center pt-0.5">
                              {node.kind === "done" ? (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white shadow-sm">
                                  <Check className="h-3.5 w-3.5" strokeWidth={2.5} />
                                </span>
                              ) : node.kind === "active" ? (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#2563eb] text-sm shadow-sm">
                                  {node.iconEmoji}
                                </span>
                              ) : (
                                <span className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-[#cbd5e1] bg-white text-sm">
                                  {node.iconEmoji}
                                </span>
                              )}
                              {!isLast ? (
                                <div className="mt-0.5 min-h-[1.25rem] w-0.5 flex-1 bg-[#e2e8f0]" />
                              ) : null}
                            </div>
                            <div className={`min-w-0 flex-1 ${!isLast ? "pb-3" : ""}`}>
                              {node.kind === "active" ? (
                                <div className="rounded-xl border border-sky-200 bg-[#f0f9ff] px-3 py-2 shadow-sm">
                                  {contentInner}
                                </div>
                              ) : (
                                <div
                                  className={
                                    node.kind === "upcoming" ? "rounded-lg py-0.5 opacity-95" : "py-0.5"
                                  }
                                >
                                  {contentInner}
                                </div>
                              )}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-5 gap-2">
                  {page.quickActions.map((a) => (
                    <QuickActionButton key={a.id} action={a} flow={flow} />
                  ))}
                </div>

                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <ClipboardList className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                      {page.historySectionTitle}
                    </h2>
                  </div>
                  <div className="space-y-2.5">
                    {page.historyItems.map((item) => (
                      <div
                        key={item.id}
                        className="flex gap-2.5 rounded-[14px] border border-[#e2e8f0] bg-white p-2.5 shadow-[0px_2px_8px_rgba(0,0,0,0.04)]"
                      >
                        <div className="flex h-[4.5rem] w-[4.5rem] shrink-0 items-center justify-center overflow-hidden rounded-xl bg-[#f1f5f9] text-2xl">
                          {item.thumbImageUrl ? (
                            <img
                              src={item.thumbImageUrl}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <span>{item.thumbEmoji ?? "📷"}</span>
                          )}
                        </div>
                        <div className="flex min-w-0 flex-1 flex-col justify-between py-0.5">
                          <div>
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#64748b]">
                              {item.dateLine}
                            </p>
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#1e293b]">
                              {item.routeSummary}
                            </p>
                            <div className="mt-0.5 flex flex-wrap items-center gap-2">
                              <StarRow n={item.ratingStars} />
                              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#ea580c]">
                                {item.priceText}
                              </span>
                            </div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            <Link
                              to={TIMELINE_PATH}
                              state={flow}
                              className="rounded-lg border border-[#bfdbfe] bg-white px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#2563eb] hover:bg-sky-50"
                            >
                              查看详情
                            </Link>
                            <Link
                              to={PLANS_PATH}
                              state={flow}
                              className="rounded-lg bg-[#2563eb] px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-white shadow-sm hover:opacity-90"
                            >
                              再来一次
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Link
                  to={PAYMENT_CONFIRMATION_PATH}
                  state={flow}
                  className="inline-flex text-[11px] font-medium text-[#64748b] underline-offset-2 hover:text-[#2563eb] hover:underline"
                >
                  上一屏：支付确认
                </Link>
              </>
            )}
          </div>

          <JourneyBottomNav active="行程" travelId={travelId} planId={planId} />
        </div>
      </div>
    </main>
  );
};
