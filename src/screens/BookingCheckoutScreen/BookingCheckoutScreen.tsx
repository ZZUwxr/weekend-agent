import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Lightbulb,
  Search,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchBookingCheckoutPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { unlockTripContent } from "../../lib/tripContentUnlock";
import type {
  BookingCheckoutPageDto,
  BookingRideDetailCardDto,
  BookingVenueDetailCardDto,
} from "../../lib/api/types";
import { BOOKING_CHECKOUT_PATH, BOOKING_TODOS_PATH, PAYMENT_PATH } from "../../routes";

type CheckoutLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function StatusBadge({ children }: { children: ReactNode }): JSX.Element {
  return (
    <span className="shrink-0 rounded-lg border border-[#e8d4a0] bg-gradient-to-br from-[#fff6cc] via-[#fff9e3] to-white px-2 py-0.5 text-center shadow-[0px_0.8px_1.2px_#d1e8ff] [font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] font-semibold leading-tight text-[#343d43]">
      {children}
    </span>
  );
}

function VenueDetailCard({ card }: { card: BookingVenueDetailCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
        <div className="mb-2 flex items-start gap-2">
          <img
            src={card.thumbnailImageUrl}
            alt=""
            className="h-9 w-9 shrink-0 rounded-full object-cover"
            width={36}
            height={36}
          />
          <h3
            className={`min-w-0 flex-1 pt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
          >
            {card.title}
          </h3>
          <StatusBadge>{card.statusBadge}</StatusBadge>
        </div>
        <div className="flex gap-2.5">
          <div className="min-w-0 flex-1 space-y-2">
            {card.rows.map((row) => (
              <div
                key={`${card.id}-${row.label}`}
                className="flex items-baseline justify-between gap-2 border-b border-[#ececec] pb-2 last:border-0"
              >
                <span className="shrink-0 [font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-semibold text-[#626262]">
                  {row.label}
                </span>
                <span className="text-right [font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-semibold leading-snug text-[#626262]">
                  {row.value}
                </span>
              </div>
            ))}
          </div>
          <img
            src={card.thumbnailImageUrl}
            alt=""
            className="h-[86px] w-[134px] shrink-0 rounded-[9px] object-cover"
            width={134}
            height={86}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function RideDetailCard({ card }: { card: BookingRideDetailCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
        <div className="mb-2 flex items-start gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#fff6cc] text-[18px]">
            🚕
          </div>
          <h3
            className={`min-w-0 flex-1 pt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
          >
            {card.title}
          </h3>
          <StatusBadge>{card.statusBadge}</StatusBadge>
        </div>

        <div className="overflow-x-auto [-webkit-overflow-scrolling:touch]">
          <table className="w-full min-w-[310px] border-separate border-spacing-0 [font-family:'PingFang_SC-Regular',Helvetica] text-[8px] text-[#626262]">
            <thead>
              <tr className="border-b border-[#e0e0e0]">
                <th className="pb-1.5 pr-1 text-left font-semibold">段次</th>
                <th className="pb-1.5 px-0.5 text-left font-semibold">类别</th>
                <th className="pb-1.5 px-0.5 text-left font-semibold">路线</th>
                <th className="pb-1.5 px-0.5 text-left font-semibold">距离</th>
                <th className="pb-1.5 px-0.5 text-left font-semibold">用时</th>
                <th className="pb-1.5 px-0.5 text-left font-semibold">费用</th>
                <th className="pb-1.5 pl-0.5 text-left font-semibold">处理</th>
              </tr>
            </thead>
            <tbody>
              {card.legs.map((leg) => (
                <tr key={leg.id} className="border-b border-[#f0f0f0] last:border-0">
                  <td className="py-1.5 pr-1 align-top font-normal">{leg.legIndex}</td>
                  <td className="px-0.5 py-1.5 align-top font-normal">{leg.categoryLabel}</td>
                  <td className="px-0.5 py-1.5 align-top leading-snug">{leg.route}</td>
                  <td className="px-0.5 py-1.5 align-top whitespace-nowrap">{leg.distanceLabel}</td>
                  <td className="px-0.5 py-1.5 align-top whitespace-nowrap">{leg.durationLabel}</td>
                  <td className="px-0.5 py-1.5 align-top whitespace-nowrap">{leg.feeLabel}</td>
                  <td className="pl-0.5 py-1.5 align-top whitespace-nowrap">{leg.handlingLabel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-2 flex gap-2 rounded-[10px] bg-[#ffd100] px-2.5 py-2">
          <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#626262]" strokeWidth={2} />
          <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[7px] font-semibold leading-[1.35] text-[#626262]">
            {card.tipText}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export const BookingCheckoutScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as CheckoutLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<BookingCheckoutPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === BOOKING_CHECKOUT_PATH) {
      document.title = "预约详情 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchBookingCheckoutPage(travelId, planId)
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) {
          setLoadError(e instanceof Error ? e.message : "加载失败");
        }
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  const todosBack = { travelId, planId };

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffef5_0%,#ffffff_40%,#ffffff_100%)]">
        {page ? (
          <EmbeddedStatusBarImage src={page.statusBarImageUrl} height={61} width={402} />
        ) : (
          <EmbeddedStatusBarPlaceholder className="bg-white/80" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-8 pb-3 pt-2">
          <header className="mb-2 flex items-center gap-1">
            <Link
              to={BOOKING_TODOS_PATH}
              state={todosBack}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回行程预约"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
              预约确认
            </span>
          </header>

          {page ? (
            <div className="mb-3 flex items-start gap-2 rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
              <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={2} />
              <p className="min-w-0 flex-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold leading-relaxed text-[#626262]">
                {page.topProgressText}
              </p>
              <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
            </div>
          ) : null}

          <ContentFitZoom
            className="space-y-3 pb-2"
            recalcKey={page ? `${page.venueCards.length}:${page.rideCard.legs.length}:${page.paymentPromptText}` : ""}
          >
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="pt-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                {page.venueCards.map((c) => (
                  <VenueDetailCard key={c.id} card={c} />
                ))}
                <RideDetailCard card={page.rideCard} />
                <div className="flex flex-col items-start gap-2 pt-1">
                  <div className="rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
                    <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold text-[#626262]">
                      {page.paymentPromptText}
                    </p>
                  </div>
                  <Link
                    to={PAYMENT_PATH}
                    state={{ travelId, planId }}
                    onClick={() => {
                      unlockTripContent();
                    }}
                    className="rounded-full bg-[#0f6fdc] px-4 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-white shadow-[0px_2px_8px_rgba(15,109,220,0.35)] transition-opacity hover:opacity-90"
                  >
                    前往支付
                  </Link>
                </div>
              </>
            )}
          </ContentFitZoom>

          <div className="mt-auto flex flex-col gap-3 pt-4">
            <div className="flex items-center gap-2">
              <div className="relative flex min-h-[46px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_#00000008]">
                {page ? (
                  <img
                    src={page.voiceInputIconUrl}
                    alt=""
                    className="h-7 w-[34px] shrink-0 object-contain"
                    height={28}
                    width={34}
                  />
                ) : (
                  <div className="h-7 w-[34px] shrink-0" />
                )}
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="有疑问可以在这里补充…"
                  className="min-w-0 flex-1 bg-transparent py-2 pl-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#333c4380]"
                />
              </div>
              <button
                type="button"
                aria-label="发送"
                className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_#00000025] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} />
              </button>
            </div>
          </div>

          <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
        </div>
    </AppScreenShell>
  );
};
