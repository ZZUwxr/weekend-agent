import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { PaymentBrandIcon } from "../../components/PaymentBrandIcon";
import { fetchPaymentPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { PaymentMethodType, PaymentPageDto } from "../../lib/api/types";
import {
  BOOKING_CHECKOUT_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PAYMENT_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../../routes";

type PaymentLocationState = { travelId?: string; planId?: string };

function paymentMethodIconShellClass(type: PaymentMethodType): string {
  const base =
    "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border shadow-[0px_1px_2px_rgba(0,0,0,0.06)]";
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
  const { state, pathname } = useLocation();
  const loc = state as PaymentLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<PaymentPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [selectedMethodId, setSelectedMethodId] = useState<string | null>(null);

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
        if (active) {
          setLoadError(e instanceof Error ? e.message : "加载失败");
        }
      });
    return () => {
      active = false;
    };
  }, [travelId, planId]);

  const checkoutBack = { travelId, planId };

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
              to={BOOKING_CHECKOUT_PATH}
              state={checkoutBack}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回预约确认"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
              付款
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
            recalcKey={`${selectedMethodId ?? ""}:${page?.lineItems.length ?? 0}`}
          >
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="pt-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                <section className="overflow-hidden rounded-[14px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <div className="border-b border-[#e8f1fc] bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] px-3 py-2.5">
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#333c43]">
                      {page.breakdownTitle}
                    </h2>
                  </div>
                  <div className="px-2 py-2">
                    <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_auto] gap-x-1.5 gap-y-0 border-b border-[#eef2f7] px-1 pb-1.5 [font-family:'PingFang_SC-Regular',Helvetica] text-[9px] font-semibold text-[#9ca3af]">
                      <span>项目</span>
                      <span>详情</span>
                      <span className="text-right">金额</span>
                    </div>
                    {page.lineItems.map((row) => (
                      <div
                        key={row.id}
                        className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_auto] gap-x-1.5 gap-y-0 border-b border-[#f3f4f6] py-2.5 pl-1 pr-0.5 last:border-b-0"
                      >
                        <div className="border-l-[3px] border-[#50a9fe] pl-2 [font-family:'PingFang_SC-Regular',Helvetica] text-[11px] font-semibold leading-snug text-[#333c43]">
                          {row.itemLabel}
                        </div>
                        <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-medium leading-snug text-[#6b7280]">
                          {row.detailText}
                        </p>
                        <p className="self-center text-right [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold tabular-nums text-[#333c43]">
                          {row.amountText}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="relative overflow-hidden rounded-[14px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <div className="flex items-start justify-between gap-2 border-b border-[#e8f1fc] bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] px-3 py-2.5 pr-2">
                    <h2 className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#333c43]">
                      {page.paymentSectionTitle}
                    </h2>
                    <div className="shrink-0 rounded-lg border border-[#cfe6ff] bg-[#f3f9ff] px-2 py-1 text-right shadow-[0px_1px_3px_rgba(80,169,254,0.15)]">
                      <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[8px] font-semibold text-[#6b7280]">
                        {page.amountDueBadgeLabel}
                      </p>
                      <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold tabular-nums text-[#0f6fdc]">
                        {page.amountDueValue}
                      </p>
                    </div>
                  </div>
                  <ul className="divide-y divide-[#f0f4f8] px-2 py-1">
                    {page.paymentMethods.map((m) => {
                      const selected = selectedMethodId === m.id;
                      return (
                        <li key={m.id}>
                          <button
                            type="button"
                            onClick={() => setSelectedMethodId(m.id)}
                            className={`flex w-full items-center gap-2.5 rounded-[10px] px-2 py-2.5 text-left transition-colors ${
                              selected ? "bg-[#f5faff]" : "hover:bg-[#fafbfc]"
                            }`}
                          >
                            <span className={paymentMethodIconShellClass(m.type)}>
                              <PaymentBrandIcon type={m.type} size={24} />
                            </span>
                            <div className="min-w-0 flex-1">
                              <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#333c43]">
                                {m.label}
                              </p>
                              {m.subtitle ? (
                                <p className="mt-0.5 [font-family:'PingFang_SC-Regular',Helvetica] text-[9px] font-medium text-[#9ca3af]">
                                  {m.subtitle}
                                </p>
                              ) : null}
                            </div>
                            <span
                              className={`flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full border-2 ${
                                selected
                                  ? "border-[#0f6fdc] bg-white"
                                  : "border-[#d1d5db] bg-white"
                              }`}
                              aria-hidden
                            >
                              {selected ? (
                                <span className="h-2.5 w-2.5 rounded-full bg-[#0f6fdc]" />
                              ) : null}
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </section>

                <div className="flex justify-start pt-0.5">
                  <div className="max-w-[92%] rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
                    <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold text-[#626262]">
                      {page.tapToPayHint}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-[#f4f5f7] px-3 py-2">
                  <Search className="h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={2} />
                  <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[11px] font-semibold text-[#6b7280]">
                    {page.queryBannerText}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    to={TRIP_LIVE_MAP_PATH}
                    state={{ travelId, planId }}
                    className="inline-flex w-fit rounded-full border border-[#cfe6ff] bg-[#f3f9ff] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#0f6fdc] shadow-[0px_2px_8px_rgba(15,109,220,0.12)] transition-opacity hover:opacity-90"
                  >
                    查看实时行程地图
                  </Link>
                  <Link
                    to={PAYMENT_CONFIRMATION_PATH}
                    state={{ travelId, planId }}
                    className="inline-flex w-fit rounded-full border border-[#fde68a] bg-[#fffbeb] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#b45309] shadow-[0px_2px_8px_rgba(180,83,9,0.12)] transition-opacity hover:opacity-90"
                  >
                    支付成功凭据
                  </Link>
                </div>
              </>
            )}
          </ContentFitZoom>

          <div className={tabScreenComposerDockMtAutoClass}>
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
            <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
          </div>
        </div>
    </AppScreenShell>
  );
};
