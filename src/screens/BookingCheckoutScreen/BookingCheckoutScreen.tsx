import {
  Banknote,
  Car,
  ChevronLeft,
  CreditCard,
  MapPinned,
  ShieldCheck,
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
import {
  fetchBookingCheckoutPage,
  postBookingCheckoutConfirm,
  reviseTravelPlan,
} from "../../lib/api";
import type {
  BookingCheckoutPageDto,
  BookingRideDetailCardDto,
  BookingVenueDetailCardDto,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { unlockTripContent } from "../../lib/tripContentUnlock";
import { BOOKING_CHECKOUT_PATH, BOOKING_TODOS_PATH, PAYMENT_PATH } from "../../routes";

type CheckoutLocationState = { travelId?: string; planId?: string };

function VenueCard({ card }: { card: BookingVenueDetailCardDto }): JSX.Element {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = Boolean(card.thumbnailImageUrl && !imageFailed);

  return (
    <AppCard>
      <div className="flex items-start gap-3">
        {showImage ? (
          <img
            src={card.thumbnailImageUrl}
            alt=""
            className="h-16 w-16 shrink-0 rounded-[14px] object-cover"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[14px] bg-[#e8f1ff] text-[#2456a6] shadow-[0_6px_18px_rgba(36,86,166,0.12)]">
            <MapPinned className="h-7 w-7" strokeWidth={2.1} />
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-[16px] font-bold leading-5 text-[#111827]">{card.title}</h3>
            <AppPill className="min-h-6 shrink-0 bg-[#e8f7f0] px-2 text-[10px] text-[#047857]">
              {card.statusBadge}
            </AppPill>
          </div>
          <div className="mt-3 space-y-2">
            {card.rows.map((row) => (
              <div key={`${card.id}-${row.label}`} className="flex items-start justify-between gap-3">
                <span className="text-[12px] font-semibold text-[#94a3b8]">{row.label}</span>
                <span className="text-right text-[12px] font-semibold leading-5 text-[#475569]">{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppCard>
  );
}

function RideCard({ card }: { card: BookingRideDetailCardDto }): JSX.Element {
  return (
    <AppCard>
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
          <Car className="h-5 w-5" strokeWidth={2.1} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-[17px] font-bold text-[#111827]">{card.title}</h2>
          <p className="mt-0.5 text-[12px] text-[#64748b]">{card.statusBadge}</p>
        </div>
      </div>

      <div className="space-y-2">
        {card.legs.map((leg) => (
          <article key={leg.id} className="rounded-[14px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[13px] font-bold text-[#111827]">
                  {leg.legIndex} {leg.categoryLabel}
                </p>
                <p className="mt-1 text-[12px] leading-5 text-[#64748b]">{leg.route}</p>
              </div>
              <AppPill className="min-h-6 shrink-0 bg-white px-2 text-[10px]">
                {leg.handlingLabel}
              </AppPill>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <div className="rounded-[10px] bg-white px-2 py-2">
                <p className="text-[10px] font-semibold text-[#94a3b8]">距离</p>
                <p className="mt-0.5 text-[12px] font-bold text-[#111827]">{leg.distanceLabel}</p>
              </div>
              <div className="rounded-[10px] bg-white px-2 py-2">
                <p className="text-[10px] font-semibold text-[#94a3b8]">用时</p>
                <p className="mt-0.5 text-[12px] font-bold text-[#111827]">{leg.durationLabel}</p>
              </div>
              <div className="rounded-[10px] bg-white px-2 py-2">
                <p className="text-[10px] font-semibold text-[#94a3b8]">费用</p>
                <p className="mt-0.5 text-[12px] font-bold text-[#111827]">{leg.feeLabel}</p>
              </div>
            </div>
          </article>
        ))}
      </div>

      <div className="mt-3 rounded-[12px] bg-[#fff8dc] px-3 py-2">
        <p className="text-[12px] font-semibold leading-5 text-[#8a5a00]">{card.tipText}</p>
      </div>
    </AppCard>
  );
}

export const BookingCheckoutScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as CheckoutLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<BookingCheckoutPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === BOOKING_CHECKOUT_PATH) {
      document.title = "预约确认 · 出行助手";
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
    fetchBookingCheckoutPage(travelId, planId)
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
      showToast("请输入想补充或修改的预约信息");
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
      setPage(revised.updatedBookingCheckout ?? await fetchBookingCheckoutPage(travelId, planId));
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改预约详情失败");
    } finally {
      setSubmitPending(false);
    }
  }

  async function confirmAndGoPayment(): Promise<void> {
    setSubmitPending(true);
    setLoadError(null);
    try {
      const result = await postBookingCheckoutConfirm(travelId, { planId, scope: "all" });
      if (!result.ok) {
        showToast(result.message || "真实预约服务暂未接入，已记录待处理任务");
      }
      unlockTripContent();
      setCurrentTravel({ travelId, planId });
      navigate(PAYMENT_PATH, { state: { travelId, planId } });
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "确认方案失败");
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
        to={BOOKING_TODOS_PATH}
        state={{ travelId, planId }}
        label="返回预约待办"
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
                eyebrow={`${page.planId.replace("-", " ").toUpperCase()} · 预约确认`}
                title="核对预约详情"
                subtitle="确认场馆、交通和费用后再进入付款。"
              />

              <div className="space-y-4">
                <AppStatusStrip Icon={ShieldCheck} title={page.topProgressText} detail={page.paymentPromptText} />

                <div className="space-y-3">
                  <div className="flex items-center gap-2 px-1">
                    <MapPinned className="h-4 w-4 text-[#2456a6]" strokeWidth={2.1} />
                    <h2 className="text-[15px] font-bold text-[#111827]">场馆预约</h2>
                  </div>
                  {page.venueCards.map((card) => <VenueCard key={card.id} card={card} />)}
                </div>

                <RideCard card={page.rideCard} />

                <AppCard className="bg-[linear-gradient(135deg,#fffdf5_0%,#ffffff_60%,#f1f6ff_100%)]">
                  <div className="flex items-center gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-full bg-[#fff4d6] text-[#8a5a00]">
                      <Banknote className="h-5 w-5" strokeWidth={2.1} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <h2 className="text-[16px] font-bold text-[#111827]">下一步付款</h2>
                      <p className="mt-1 text-[12px] leading-5 text-[#64748b]">{page.paymentPromptText}</p>
                    </div>
                  </div>
                </AppCard>

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
                onClick={() => void confirmAndGoPayment()}
              >
                {submitPending ? "确认中…" : "确认无误，前往支付"}
              </AppActionButton>
              <AppComposer
                value={input}
                onChange={setInput}
                onSubmit={() => void handleComposerSubmit()}
                pending={submitPending}
                placeholder={submitPending ? "正在处理…" : "补充预约问题，例如换个时间..."}
              />
              <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
            </div>
          </>
        )}
      </div>
    </AppScreenShell>
  );
};
