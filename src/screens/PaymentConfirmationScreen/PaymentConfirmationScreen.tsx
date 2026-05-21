import {
  Bell,
  CalendarPlus,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock,
  Share2,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchPaymentConfirmationPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  PaymentConfirmationPageDto,
  PaymentConfirmHelpActionDto,
  PaymentConfirmRowDto,
  PaymentConfirmRowStatusKind,
} from "../../lib/api/types";
import {
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PAYMENT_PATH,
  TRIP_LIVE_MAP_PATH,
  TRIP_WRAP_PATH,
} from "../../routes";

type PaymentConfirmLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function RowStatus({ kind, text }: { kind: PaymentConfirmRowStatusKind; text: string }): JSX.Element {
  const base =
    "inline-flex items-center gap-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold";
  if (kind === "paid") {
    return (
      <span className={`${base} text-emerald-600`}>
        <Check className="h-3 w-3 shrink-0" strokeWidth={2.5} />
        {text}
      </span>
    );
  }
  if (kind === "reserved") {
    return <span className={`${base} text-emerald-600`}>{text}</span>;
  }
  return (
    <span className={`${base} text-amber-600`}>
      <Clock className="h-3 w-3 shrink-0" strokeWidth={2} />
      {text}
    </span>
  );
}

function ConfirmTable({ rows, page }: { rows: PaymentConfirmRowDto[]; page: PaymentConfirmationPageDto }): JSX.Element {
  return (
    <div className="overflow-hidden rounded-xl border border-[#d8e8f8] bg-white/90">
      <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_auto] gap-x-1 border-b border-[#eef2f6] bg-[#f8fafc] px-2 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#64748b]">
        <span>{page.tableColItem}</span>
        <span>{page.tableColDetail}</span>
        <span className="text-right">{page.tableColStatus}</span>
      </div>
      {rows.map((row) => (
        <div
          key={row.id}
          className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_auto] gap-x-1 border-b border-[#f1f5f9] px-2 py-2 last:border-b-0"
        >
          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#1e293b]">
            {row.itemLabel}
          </span>
          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[9.5px] font-medium leading-snug text-[#475569]">
            {row.detailText}
          </span>
          <div className="flex justify-end">
            <RowStatus kind={row.statusKind} text={row.statusText} />
          </div>
        </div>
      ))}
      <div className="flex items-center justify-end gap-2 border-t border-[#e2e8f0] bg-[#f8fafc] px-2 py-2">
        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#64748b]">
          {page.totalLabel}
        </span>
        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-bold text-[#0f172a]">
          {page.totalValue}
        </span>
      </div>
    </div>
  );
}

function HelpActionIcon({ kind }: { kind: PaymentConfirmHelpActionDto["kind"] }): JSX.Element {
  const shell =
    "flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-b from-[#e8f4ff] to-white shadow-[0px_1px_4px_#d1e8ff]";
  switch (kind) {
    case "share":
      return (
        <span className={shell}>
          <Share2 className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
        </span>
      );
    case "calendar":
      return (
        <span className={shell}>
          <CalendarPlus className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
        </span>
      );
    default:
      return (
        <span className={shell}>
          <Bell className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
        </span>
      );
  }
}

export const PaymentConfirmationScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as PaymentConfirmLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<PaymentConfirmationPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === PAYMENT_CONFIRMATION_PATH) {
      document.title = "支付确认 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchPaymentConfirmationPage(travelId, planId)
      .then((data) => {
        if (active) {
          setPage(data);
        }
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
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffef5_0%,#ffffff_38%,#ffffff_100%)]">
        {page ? (
          <EmbeddedStatusBarImage src={page.statusBarImageUrl} height={61} width={402} />
        ) : (
          <EmbeddedStatusBarPlaceholder className="bg-white/80" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-4 pb-3 pt-2">
          <header className="mb-2 flex items-center gap-1">
            <Link
              to={PAYMENT_PATH}
              state={flow}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回付款"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
              {page?.navTitle ?? "确认付款信息"}
            </span>
          </header>

          <ContentFitZoom className="space-y-3 pb-2" recalcKey={page?.rows?.length ?? 0}>
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="py-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                <div
                  className="relative overflow-hidden rounded-2xl border border-[#fcd34d]/60 bg-[linear-gradient(105deg,#fff7d6_0%,#ffec9e_45%,#fff4c8_100%)] px-3 py-3 shadow-[0px_4px_16px_rgba(245,200,20,0.2)]"
                  role="status"
                >
                  {page.heroFigureImageUrl ? (
                    <img
                      src={page.heroFigureImageUrl}
                      alt=""
                      className="pointer-events-none absolute -right-2 -top-2 h-24 w-24 object-contain opacity-90"
                    />
                  ) : null}
                  <p className="relative [font-family:'HYQiHei-Regular',Helvetica] text-[17px] font-bold text-[#78350f]">
                    {page.heroTitle}
                  </p>
                  <p className="relative mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#92400e]/90">
                    {page.heroSubtitle}
                  </p>
                </div>

                <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <CardContent className="bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
                    <div className="mb-2 flex items-start gap-2">
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
                        <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
                      </div>
                      <p
                        className={`min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-semibold leading-tight ${titleGradientClass()}`}
                      >
                        {page.confirmationSectionTitle}
                      </p>
                    </div>
                    <ConfirmTable rows={page.rows} page={page} />
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <CardContent className="bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
                    <p
                      className={`mb-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold leading-snug ${titleGradientClass()}`}
                    >
                      {page.recommendedSectionTitle}
                    </p>
                    <div className="space-y-2 pl-1">
                      {page.recommendedRows.map((r) => (
                        <div
                          key={r.id}
                          className="flex items-center gap-2 rounded-xl border border-[#e2e8f0] bg-white/80 px-2.5 py-2"
                        >
                          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#f1f5f9] text-lg">
                            {r.thumbEmoji ?? "📦"}
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#1e293b]">
                              {r.name}
                            </p>
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[9px] text-[#64748b]">
                              适合 {r.audienceLabel}
                            </p>
                          </div>
                          <span className="shrink-0 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#ea580c]">
                            {r.priceText}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <CardContent className="bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
                    <p
                      className={`mb-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold ${titleGradientClass()}`}
                    >
                      {page.timelineSectionTitle}
                    </p>
                    <div className="-mx-1 flex gap-2 overflow-x-auto pb-1 pl-1 pr-1 pt-0.5 [scrollbar-width:thin]">
                      {page.timelineChips.map((c, i) => (
                        <div key={c.id} className="flex shrink-0 items-center">
                          <div className="flex min-w-[4.5rem] flex-col items-center rounded-xl border border-[#cfe6ff] bg-white px-2 py-1.5 shadow-[0px_1px_6px_rgba(80,169,254,0.12)]">
                            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-bold text-[#0f6fdc]">
                              {c.time}
                            </span>
                            <span className="text-sm leading-none">{c.iconEmoji}</span>
                            <span className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#334155]">
                              {c.label}
                            </span>
                          </div>
                          {i < page.timelineChips.length - 1 ? (
                            <span className="mx-1 text-[10px] text-[#94a3b8]" aria-hidden>
                              →
                            </span>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                  <CardContent className="bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] p-3">
                    <p
                      className={`mb-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold ${titleGradientClass()}`}
                    >
                      {page.helpSectionTitle}
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {page.helpActions.map((a) => (
                        <button
                          key={a.id}
                          type="button"
                          className="flex flex-col items-center gap-1.5 rounded-xl border border-[#e2e8f0] bg-white/90 py-2.5 shadow-sm transition-opacity hover:opacity-90 active:scale-[0.98]"
                        >
                          <HelpActionIcon kind={a.kind} />
                          <span className="px-1 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold leading-tight text-[#334155]">
                            {a.label}
                          </span>
                        </button>
                      ))}
                    </div>
                    <div className="mt-3 rounded-xl border border-[#fcd34d]/70 bg-[#fffbeb] px-3 py-2.5">
                      <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[11px] font-semibold leading-relaxed text-[#713f12]">
                        {page.helpSummaryText}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex flex-wrap gap-2">
                  <Link
                    to={TRIP_WRAP_PATH}
                    state={flow}
                    className="inline-flex w-fit rounded-full border border-[#fde68a] bg-[#fffbeb] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#b45309] shadow-[0px_2px_8px_rgba(180,83,9,0.1)] transition-opacity hover:opacity-90"
                  >
                    行程结束确认
                  </Link>
                  <Link
                    to={TRIP_LIVE_MAP_PATH}
                    state={flow}
                    className="inline-flex w-fit rounded-full border border-[#cfe6ff] bg-[#f3f9ff] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#0f6fdc] shadow-[0px_2px_8px_rgba(15,109,220,0.12)] transition-opacity hover:opacity-90"
                  >
                    查看实时行程地图
                  </Link>
                  <Link
                    to={ITINERARY_HUB_PATH}
                    state={flow}
                    className="inline-flex w-fit rounded-full border border-[#c7d2fe] bg-[#eef2ff] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#4338ca] shadow-[0px_2px_8px_rgba(67,56,202,0.12)] transition-opacity hover:opacity-90"
                  >
                    行程主页
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
              <Link
                to={TRIP_WRAP_PATH}
                state={flow}
                aria-label="进入行程结束确认"
                className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_#00000025] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} />
              </Link>
            </div>
            <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
          </div>
        </div>
    </AppScreenShell>
  );
};
