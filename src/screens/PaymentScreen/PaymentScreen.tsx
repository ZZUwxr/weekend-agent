import {
  CheckCircle2,
  ChevronLeft,
  CreditCard,
  ReceiptText,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { PaymentBrandIcon } from "../../components/PaymentBrandIcon";
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
import {
  fetchPaymentPage,
  patchTravelPaymentOrderComplete,
  postTravelPaymentOrder,
  reviseTravelPlan,
} from "../../lib/api";
import type { PaymentMethodType, PaymentPageDto } from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import {
  BOOKING_CHECKOUT_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PAYMENT_PATH,
} from "../../routes";
import { cn } from "../../lib/utils";

type PaymentLocationState = { travelId?: string; planId?: string };

function paymentMethodIconShellClass(type: PaymentMethodType): string {
  const base =
    "flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] border shadow-[0_4px_12px_rgba(15,23,42,0.06)]";
  switch (type) {
    case "wechat":
      return `${base} border-[#bfe5d0] bg-[#ecf8f1]`;
    case "alipay":
      return `${base} border-[#b3d4ff] bg-[#eef5ff]`;
    case "meituan":
      return `${base} border-[#f0d78c] bg-[#fff9e6]`;
    default:
      return `${base} border-[#e8ecf0] bg-white`;
  }
}

export const PaymentScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as PaymentLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<PaymentPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [selectedMethodId, setSelectedMethodId] = useState<string | null>(null);
  const [submitPending, setSubmitPending] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === PAYMENT_PATH) {
      document.title = "付款 · 出行助手";
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
    fetchPaymentPage(travelId, planId)
      .then((data) => {
        if (active) {
          setPage(data);
          setSelectedMethodId(data.defaultSelectedPaymentMethodId);
        }
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
      showToast("请输入想补充或修改的付款信息");
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
      setPage(revised.updatedPayment ?? await fetchPaymentPage(travelId, planId));
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改付款信息失败");
    } finally {
      setSubmitPending(false);
    }
  }

  async function submitPayment(): Promise<void> {
    if (!selectedMethodId) {
      showToast("请先选择付款方式");
      return;
    }
    setSubmitPending(true);
    setLoadError(null);
    try {
      const order = await postTravelPaymentOrder(travelId, {
        planId,
        paymentMethodId: selectedMethodId,
      });
      if (!order.ok) {
        showToast(order.message || "支付服务暂未接入，已记录待处理任务");
      } else if (order.orderId) {
        const completed = await patchTravelPaymentOrderComplete(travelId, order.orderId, planId);
        if (!completed.ok) {
          showToast(completed.message || "支付确认服务暂未接入，已记录待处理任务");
        }
      }
      setCurrentTravel({ travelId, planId });
      navigate(PAYMENT_CONFIRMATION_PATH, { state: { travelId, planId } });
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "支付确认失败");
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
        to={BOOKING_CHECKOUT_PATH}
        state={{ travelId, planId }}
        label="返回预约确认"
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
                eyebrow={`${page.planId.replace("-", " ").toUpperCase()} · 费用确认`}
                title="付款确认"
                subtitle="当前为预览费用，确认后会在后端生成待处理支付任务。"
              />

              <div className="space-y-4">
                <AppCard className="border-[#f1c96d] bg-[linear-gradient(135deg,#fffdf5_0%,#ffffff_58%,#f1f6ff_100%)]">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <AppPill className="bg-[#fff4d6] text-[#8a5a00]">{page.amountDueBadgeLabel}</AppPill>
                      <p className="mt-3 text-[34px] font-bold leading-none tracking-[0] text-[#111827]">
                        {page.amountDueValue}
                      </p>
                      <p className="mt-2 text-[13px] leading-5 text-[#64748b]">{page.topProgressText}</p>
                    </div>
                    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#ffd95a] text-[#3f3421] shadow-[0_8px_18px_rgba(234,179,8,0.2)]">
                      <CreditCard className="h-6 w-6" strokeWidth={2.1} />
                    </span>
                  </div>
                </AppCard>

                <AppCard>
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
                      <ReceiptText className="h-5 w-5" strokeWidth={2.1} />
                    </span>
                    <h2 className="text-[17px] font-bold text-[#111827]">{page.breakdownTitle}</h2>
                  </div>
                  <div className="space-y-2">
                    {page.lineItems.map((row) => (
                      <div key={row.id} className="rounded-[12px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-[13px] font-bold text-[#111827]">{row.itemLabel}</p>
                            <p className="mt-1 text-[12px] leading-5 text-[#64748b]">{row.detailText}</p>
                          </div>
                          <p className="shrink-0 text-right text-[13px] font-bold text-[#111827]">{row.amountText}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </AppCard>

                <AppCard>
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f7f0] text-[#047857]">
                      <ShieldCheck className="h-5 w-5" strokeWidth={2.1} />
                    </span>
                    <div>
                      <h2 className="text-[17px] font-bold text-[#111827]">{page.paymentSectionTitle}</h2>
                      <p className="mt-0.5 text-[12px] text-[#64748b]">请选择一种付款方式</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {page.paymentMethods.map((method) => {
                      const selected = selectedMethodId === method.id;
                      return (
                        <button
                          key={method.id}
                          type="button"
                          onClick={() => {
                            setSelectedMethodId(method.id);
                            showToast(`已选择${method.label}`);
                          }}
                          className={cn(
                            "flex min-h-[64px] w-full items-center gap-3 rounded-[14px] border px-3 py-2 text-left transition active:scale-[0.99]",
                            selected ? "border-[#2456a6] bg-[#f1f6ff]" : "border-[#e5e7eb] bg-[#f8fafc]",
                          )}
                        >
                          <span className={paymentMethodIconShellClass(method.type)}>
                            <PaymentBrandIcon type={method.type} size={25} />
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className="text-[14px] font-bold text-[#111827]">{method.label}</p>
                            {method.subtitle ? <p className="mt-0.5 text-[12px] text-[#64748b]">{method.subtitle}</p> : null}
                          </div>
                          <span
                            className={cn(
                              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 bg-white",
                              selected ? "border-[#2456a6] text-[#2456a6]" : "border-[#cbd5e1]",
                            )}
                          >
                            {selected ? <CheckCircle2 className="h-4 w-4" strokeWidth={2.4} /> : null}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </AppCard>

                <AppStatusStrip Icon={ShieldCheck} title={page.tapToPayHint} detail={page.queryBannerText} />

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
                Icon={CreditCard}
                disabled={submitPending}
                onClick={() => void submitPayment()}
              >
                {submitPending ? "处理中…" : `记录支付任务 ${page.amountDueValue}`}
              </AppActionButton>
              <AppComposer
                value={input}
                onChange={setInput}
                onSubmit={() => void handleComposerSubmit()}
                pending={submitPending}
                placeholder={submitPending ? "正在处理…" : "补充付款问题，例如换个付款方式..."}
              />
              <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
            </div>
          </>
        )}
      </div>
    </AppScreenShell>
  );
};
