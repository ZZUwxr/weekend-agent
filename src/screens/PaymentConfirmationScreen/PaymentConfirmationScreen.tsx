import {
  Bell,
  CalendarCheck2,
  CalendarPlus,
  CheckCircle2,
  ChevronLeft,
  Map,
  ReceiptText,
  Share2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
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
import { executeTravelPlan, fetchPaymentConfirmationPage, reviseTravelPlan } from "../../lib/api";
import type {
  PaymentConfirmationPageDto,
  PaymentConfirmHelpActionDto,
  PaymentConfirmRowDto,
  PaymentConfirmRowStatusKind,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import {
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PAYMENT_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../../routes";

type PaymentConfirmLocationState = { travelId?: string; planId?: string };

function statusTone(kind: PaymentConfirmRowStatusKind): string {
  if (kind === "pending_provider") return "bg-[#edf5ff] text-[#2456a6]";
  return "bg-[#fff4d6] text-[#8a5a00]";
}

function ConfirmationRow({ row }: { row: PaymentConfirmRowDto }): JSX.Element {
  return (
    <div className="rounded-[12px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-[#111827]">{row.itemLabel}</p>
          <p className="mt-1 text-[12px] leading-5 text-[#64748b]">{row.detailText}</p>
        </div>
        <AppPill className={`min-h-6 shrink-0 px-2 text-[10px] ${statusTone(row.statusKind)}`}>
          {row.statusText}
        </AppPill>
      </div>
    </div>
  );
}

function HelpActionIcon({ kind }: { kind: PaymentConfirmHelpActionDto["kind"] }): JSX.Element {
  if (kind === "share") return <Share2 className="h-5 w-5" strokeWidth={2.1} />;
  if (kind === "calendar") return <CalendarPlus className="h-5 w-5" strokeWidth={2.1} />;
  return <Bell className="h-5 w-5" strokeWidth={2.1} />;
}

export const PaymentConfirmationScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as PaymentConfirmLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<PaymentConfirmationPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === PAYMENT_CONFIRMATION_PATH) {
      document.title = "任务确认 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) return;
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchPaymentConfirmationPage(travelId, planId)
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

  async function handleComposerSubmit(): Promise<void> {
    const text = input.trim();
    if (!text) {
      showToast("请输入想补充或修改的确认信息");
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
      setPage(revised.updatedPaymentConfirmation ?? await fetchPaymentConfirmationPage(travelId, planId));
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改确认信息失败");
    } finally {
      setSubmitPending(false);
    }
  }

  async function executeAndNavigate(to: string): Promise<void> {
    setSubmitPending(true);
    setLoadError(null);
    try {
      const result = await executeTravelPlan(travelId, planId);
      if (!result.ok) {
        showToast(result.message || "外部执行服务暂未接入，已记录待处理任务");
      }
      setCurrentTravel({ travelId, planId });
      navigate(to, { state: { travelId, planId } });
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "执行行程失败");
    } finally {
      setSubmitPending(false);
    }
  }

  async function recordProviderAction(
    action: PaymentConfirmHelpActionDto["kind"],
    label: string,
  ): Promise<void> {
    const actionMap: Record<PaymentConfirmHelpActionDto["kind"], string> = {
      share: "share_itinerary",
      calendar: "calendar_reminder",
      bell: "schedule_reminder",
    };
    setSubmitPending(true);
    setLoadError(null);
    try {
      const result = await executeTravelPlan(travelId, {
        planId,
        action: actionMap[action],
        metadata: { source: "payment_confirmation", label },
      });
      showToast(result.message || "外部服务暂未接入，已记录待处理任务");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "记录外部服务任务失败");
    } finally {
      setSubmitPending(false);
    }
  }

  return (
    <AppScreenShell frameClassName="bg-[#f6f7fb]">
      <AppToast message={toastMessage} />
      <AppBackdrop />
      {page ? (
        <EmbeddedStatusBarImage src={page.statusBarImageUrl} height={61} width={402} />
      ) : (
        <EmbeddedStatusBarPlaceholder />
      )}
      <AppIconButton
        to={PAYMENT_PATH}
        state={{ travelId, planId }}
        label="返回付款"
        className="absolute left-3 top-[61px] z-20"
      >
        <ChevronLeft className="h-5 w-5" strokeWidth={2.1} />
      </AppIconButton>

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-[14px] pb-3 pt-2">
        {resolvingTravel ? (
          <AppLoadingState label="正在同步当前行程..." />
        ) : loadError && !page ? (
          <AppErrorState message={loadError} />
        ) : !page ? (
          <AppLoadingState />
        ) : (
          <>
            <div className="min-h-0 flex-1 overflow-y-auto pb-5">
              <AppPageHeader
                className="pb-4 pl-12"
                eyebrow={page.navTitle}
                title={page.heroTitle}
                subtitle={page.heroSubtitle}
              />

              <div className="space-y-4">
                <AppCard className="border-[#8dd8b8] bg-[linear-gradient(135deg,#f0fbf7_0%,#ffffff_58%,#f1f6ff_100%)]">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <AppPill className="bg-[#fff4d6] text-[#8a5a00]">待接入</AppPill>
                      <h2 className="mt-3 text-[24px] font-bold leading-[1.18] text-[#111827]">
                        外部任务已记录
                      </h2>
                      <p className="mt-2 text-[13px] leading-5 text-[#64748b]">
                        支付、预约和叫车还没有接第三方平台，当前只会保留后端待处理记录。
                      </p>
                    </div>
                    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#e8f7f0] text-[#047857] shadow-[0_8px_18px_rgba(15,118,110,0.14)]">
                      <CheckCircle2 className="h-6 w-6" strokeWidth={2.2} />
                    </span>
                  </div>
                </AppCard>

                <AppCard>
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
                        <ReceiptText className="h-5 w-5" strokeWidth={2.1} />
                      </span>
                      <div>
                        <h2 className="text-[17px] font-bold text-[#111827]">{page.confirmationSectionTitle}</h2>
                        <p className="mt-0.5 text-[12px] text-[#64748b]">{page.totalLabel} {page.totalValue}</p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {page.rows.map((row) => <ConfirmationRow key={row.id} row={row} />)}
                  </div>
                </AppCard>

                <AppCard>
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#fff4d6] text-[#8a5a00]">
                      <CalendarCheck2 className="h-5 w-5" strokeWidth={2.1} />
                    </span>
                    <div>
                      <h2 className="text-[17px] font-bold text-[#111827]">{page.timelineSectionTitle}</h2>
                      <p className="mt-0.5 text-[12px] text-[#64748b]">接下来会按这些节点推进</p>
                    </div>
                  </div>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {page.timelineChips.map((chip) => (
                      <div key={chip.id} className="min-w-[92px] rounded-[14px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3 text-center">
                        <p className="text-[12px] font-bold text-[#2456a6]">{chip.time}</p>
                        <p className="mt-1 text-[20px] leading-none">{chip.iconEmoji}</p>
                        <p className="mt-1 text-[11px] font-semibold text-[#475569]">{chip.label}</p>
                      </div>
                    ))}
                  </div>
                </AppCard>

                <AppCard>
                  <h2 className="text-[17px] font-bold text-[#111827]">{page.helpSectionTitle}</h2>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {page.helpActions.map((action) => (
                      <button
                        key={action.id}
                        type="button"
                        onClick={() => void recordProviderAction(action.kind, action.label)}
                        className="flex min-h-[72px] flex-col items-center justify-center gap-2 rounded-[14px] border border-[#e5e7eb] bg-[#f8fafc] px-2 text-[#2456a6] transition active:scale-[0.98]"
                      >
                        <HelpActionIcon kind={action.kind} />
                        <span className="text-[11px] font-semibold leading-4 text-[#475569]">{action.label}</span>
                      </button>
                    ))}
                  </div>
                  <div className="mt-3 rounded-[12px] bg-[#fff8dc] px-3 py-2">
                    <p className="text-[12px] font-semibold leading-5 text-[#8a5a00]">{page.helpSummaryText}</p>
                  </div>
                </AppCard>

                <AppStatusStrip Icon={Map} title="下一步可以查看实时地图" detail="地图页会显示规划路线；叫车、导航、分享会记录为待处理任务。" />

                {loadError ? (
                  <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                    {loadError}
                  </div>
                ) : null}
              </div>
            </div>

            <div className={tabScreenComposerDockMtAutoClass}>
              <AppActionButton
                tone="blue"
                Icon={Map}
                disabled={submitPending}
                onClick={() => void executeAndNavigate(TRIP_LIVE_MAP_PATH)}
              >
                {submitPending ? "处理中…" : "查看实时行程地图"}
              </AppActionButton>
              <div className="grid grid-cols-2 gap-2">
                <AppActionButton
                  tone="muted"
                  disabled={submitPending}
                  onClick={() => void executeAndNavigate(ITINERARY_HUB_PATH)}
                >
                  行程主页
                </AppActionButton>
                <AppActionButton
                  tone="muted"
                  disabled={submitPending}
                  onClick={() => showToast("推荐套餐已收起，可稍后在行程主页查看")}
                >
                  稍后再看
                </AppActionButton>
              </div>
              <AppComposer
                value={input}
                onChange={setInput}
                onSubmit={() => void handleComposerSubmit()}
                pending={submitPending}
                placeholder={submitPending ? "正在处理…" : "补充确认问题，例如改提醒时间..."}
              />
              <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
            </div>
          </>
        )}
      </div>
    </AppScreenShell>
  );
};
