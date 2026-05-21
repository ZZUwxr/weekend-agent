import { ChevronDown, ChevronLeft, ChevronRight, Search, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchBookingTodosPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  BookingFlowItemDto,
  BookingTodoCardDto,
  BookingTodoItemDto,
  BookingTodosPageDto,
} from "../../lib/api/types";
import { BOOKING_CHECKOUT_PATH, BOOKING_TODOS_PATH, TIMELINE_PATH } from "../../routes";

type BookingLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function StatusPill({ label }: { label: string }): JSX.Element {
  return (
    <span className="rounded-lg border border-[#d8d8d8] bg-gradient-to-b from-[#e8f4ff]/90 to-white px-2 py-0.5 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] font-semibold text-[#343d43] shadow-[0px_0.8px_1.6px_#d1e8ff]">
      {label}
    </span>
  );
}

function TodoRow({ item }: { item: BookingTodoItemDto }): JSX.Element {
  return (
    <div className="flex gap-2.5 border-b border-[#efefef] py-2.5 last:border-b-0">
      <div className="shrink-0">
        {item.kind === "venue" && item.thumbnailImageUrl ? (
          <img
            src={item.thumbnailImageUrl}
            alt=""
            className="h-12 w-12 rounded-full object-cover"
            height={48}
            width={48}
          />
        ) : (
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#fff6cc] text-[20px]">
            🚕
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1 pt-0.5">
        <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[10px] font-semibold text-[#626262]">
          {item.title}
        </p>
        {item.subtitle ? (
          <p className="mt-0.5 [font-family:'PingFang_SC-Regular',Helvetica] text-[8.5px] leading-snug text-[#626262]">
            {item.subtitle}
          </p>
        ) : null}
        {item.lines?.map((line, i) => (
          <p
            key={`${item.id}-l-${i}`}
            className="mt-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[7.5px] leading-relaxed text-[#626262]"
          >
            {line}
          </p>
        ))}
      </div>
      <div className="flex shrink-0 flex-col items-end justify-start pt-1">
        <StatusPill label={item.statusLabel} />
      </div>
    </div>
  );
}

function TodoCard({ card }: { card: BookingTodoCardDto }): JSX.Element {
  return (
    <Card className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
      <CardContent className="relative border-0 p-0">
        <div className="relative bg-gradient-to-br from-[#fffef8] via-white to-[#f5f9ff] px-3 pt-3">
          <div className="mb-2 flex items-start gap-2">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
              <Sparkles className="h-3.5 w-3.5 text-[#f5c814]" strokeWidth={1.75} />
            </div>
            <p
              className={`flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-tight ${titleGradientClass()}`}
            >
              {card.title}
            </p>
            <ChevronDown className="h-4 w-4 shrink-0 text-[#9ca3af]" strokeWidth={2} />
          </div>
          <div className="pb-1">{card.items.map((it) => <TodoRow key={it.id} item={it} />)}</div>
        </div>
        <div className="flex items-center justify-end bg-[#ffd100] px-3 py-2">
          <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[8.5px] font-semibold text-[#343d43]">
            {card.footerBannerText}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function FlowBlock({ item }: { item: BookingFlowItemDto }): JSX.Element {
  switch (item.type) {
    case "ai_message":
      return (
        <div className="flex justify-start">
          <div className="max-w-[92%] rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
            <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold leading-snug text-[#626262]">
              {item.body}
            </p>
          </div>
        </div>
      );
    case "user_pill":
      return (
        <div className="flex justify-end">
          <div className="rounded-bl-[15px] rounded-br-[15px] rounded-tl-[15px] bg-[#ffd100] px-5 py-1.5 shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)]">
            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#343d43]">
              {item.label}
            </p>
          </div>
        </div>
      );
    case "progress_banner":
      return (
        <div className="flex items-start gap-2 rounded-br-[11.53px] rounded-bl-[11.53px] rounded-tr-[11.53px] bg-white px-3 py-2.5 shadow-[0px_2.88px_7.2px_rgba(0,0,0,0.03)]">
          <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={2} />
          <p className="min-w-0 flex-1 [font-family:'PingFang_SC-Regular',Helvetica] text-[12px] font-semibold leading-relaxed text-[#626262]">
            {item.body}
          </p>
          <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
        </div>
      );
    case "todo_card":
      return <TodoCard card={item.card} />;
  }
}

export const BookingTodosScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as BookingLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";

  const [page, setPage] = useState<BookingTodosPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === BOOKING_TODOS_PATH) {
      document.title = "行程预约 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchBookingTodosPage(travelId, planId)
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

  const timelineBack = { travelId, planId };

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#fffef5_0%,#ffffff_38%,#ffffff_100%)]">
        {page ? (
          <EmbeddedStatusBarImage src={page.statusBarImageUrl} height={61} width={402} />
        ) : (
          <EmbeddedStatusBarPlaceholder className="bg-white/80" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-8 pb-3 pt-2">
          <header className="mb-3 flex items-center gap-1">
            <Link
              to={TIMELINE_PATH}
              state={timelineBack}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
              aria-label="返回时间轴"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
            </Link>
            <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
              行程预约
            </span>
          </header>

          <ContentFitZoom className="space-y-3 pb-2" recalcKey={page?.flow?.length ?? 0}>
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page ? (
              <p className="pt-6 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <>
                {page.flow.map((item) => (
                  <FlowBlock key={item.id} item={item} />
                ))}
                <div className="flex justify-center pt-1">
                  <Link
                    to={BOOKING_CHECKOUT_PATH}
                    state={{ travelId, planId }}
                    className="rounded-full bg-[#50a9fe]/12 px-4 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#2a7bc8] transition-opacity hover:opacity-90"
                  >
                    查看预约详情与支付
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
                  placeholder="补充预约需求或修改指令…"
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
