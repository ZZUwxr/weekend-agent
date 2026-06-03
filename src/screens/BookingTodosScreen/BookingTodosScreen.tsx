import {
  CalendarCheck2,
  ChevronLeft,
  ClipboardCheck,
  MapPinned,
  MessageCircle,
  Search,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { RevisionNotice, type RevisionNoticeState } from "../../components/RevisionNotice";
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
import { fetchBookingTodosPage, reviseTravelPlan } from "../../lib/api";
import type {
  BookingFlowItemDto,
  BookingTodoCardDto,
  BookingTodoItemDto,
  BookingTodosPageDto,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { BOOKING_CHECKOUT_PATH, BOOKING_TODOS_PATH, TIMELINE_PATH } from "../../routes";

type BookingLocationState = { travelId?: string; planId?: string };

function collectTodoCards(flow: BookingFlowItemDto[]): BookingTodoCardDto[] {
  return flow.flatMap((item) => item.type === "todo_card" ? [item.card] : []);
}

function collectStatusMessages(flow: BookingFlowItemDto[]): string[] {
  return flow
    .filter((item) => item.type === "ai_message" || item.type === "progress_banner")
    .map((item) => item.type === "ai_message" ? item.body : item.body)
    .filter(Boolean);
}

function TodoItem({ item }: { item: BookingTodoItemDto }): JSX.Element {
  const [imageFailed, setImageFailed] = useState(false);
  const icon = item.kind === "rides" ? "🚕" : "📍";
  const showImage = Boolean(item.kind === "venue" && item.thumbnailImageUrl && !imageFailed);

  return (
    <article className="rounded-[14px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3">
      <div className="flex items-start gap-3">
        <div className="shrink-0">
          {showImage ? (
            <img
              src={item.thumbnailImageUrl}
              alt=""
              className="h-12 w-12 rounded-[12px] object-cover"
              onError={() => setImageFailed(true)}
            />
          ) : item.kind === "venue" ? (
            <span className="flex h-12 w-12 items-center justify-center rounded-[12px] bg-[#e8f1ff] text-[#2456a6] shadow-[0_4px_12px_rgba(15,23,42,0.06)]">
              <MapPinned className="h-5 w-5" strokeWidth={2.1} />
            </span>
          ) : (
            <span className="flex h-12 w-12 items-center justify-center rounded-[12px] bg-white text-[22px] shadow-[0_4px_12px_rgba(15,23,42,0.06)]">
              {icon}
            </span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="min-w-0 text-[14px] font-bold leading-5 text-[#111827]">{item.title}</h3>
            <AppPill className="min-h-6 shrink-0 bg-[#e8f1ff] px-2 text-[10px] text-[#2456a6]">
              {item.statusLabel}
            </AppPill>
          </div>
          {item.subtitle ? <p className="mt-1 text-[12px] leading-5 text-[#64748b]">{item.subtitle}</p> : null}
          {item.lines?.length ? (
            <div className="mt-2 space-y-1">
              {item.lines.map((line, index) => (
                <p key={`${item.id}-${index}`} className="text-[12px] leading-5 text-[#64748b]">{line}</p>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function TodoGroup({ card }: { card: BookingTodoCardDto }): JSX.Element {
  return (
    <AppCard>
      <div className="mb-3 flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#fff4d6] text-[#8a5a00]">
          <ClipboardCheck className="h-5 w-5" strokeWidth={2.1} />
        </span>
        <div className="min-w-0">
          <h2 className="text-[17px] font-bold text-[#111827]">{card.title}</h2>
          <p className="mt-0.5 text-[12px] text-[#64748b]">需要你确认的预约和转场事项</p>
        </div>
      </div>
      <div className="space-y-2">
        {card.items.map((item) => <TodoItem key={item.id} item={item} />)}
      </div>
      <div className="mt-3 rounded-[12px] bg-[#fff8dc] px-3 py-2">
        <p className="text-[12px] font-semibold leading-5 text-[#8a5a00]">{card.footerBannerText}</p>
      </div>
    </AppCard>
  );
}

export const BookingTodosScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as BookingLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<BookingTodosPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const [revisionNotice, setRevisionNotice] = useState<RevisionNoticeState>(null);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === BOOKING_TODOS_PATH) {
      document.title = "预约待办 · 出行助手";
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
    fetchBookingTodosPage(travelId, planId)
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

  const todoCards = useMemo(() => collectTodoCards(page?.flow ?? []), [page]);
  const statusMessages = useMemo(() => collectStatusMessages(page?.flow ?? []), [page]);

  function goToCheckout(): void {
    setCurrentTravel({ travelId, planId });
    navigate(BOOKING_CHECKOUT_PATH, { state: { travelId, planId } });
  }

  async function handleComposerSubmit(): Promise<void> {
    const text = input.trim();
    if (!text) {
      showToast("请输入想补充的预约需求，继续请点击主按钮");
      return;
    }

    setSubmitPending(true);
    setLoadError(null);
    setRevisionNotice(null);
    try {
      const revised = await reviseTravelPlan(travelId, {
        message: text,
        targetPlanId: planId,
        revisionMode: "partial",
      });
      setPage(revised.updatedBookingTodos ?? await fetchBookingTodosPage(travelId, planId));
      setRevisionNotice({ summary: revised.revisionSummary, warnings: revised.warnings });
      showToast("预约待办已更新");
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改预约需求失败");
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
        to={TIMELINE_PATH}
        state={{ travelId, planId }}
        label="返回时间轴"
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
                eyebrow={`${page.planId.replace("-", " ").toUpperCase()} · 预约阶段`}
                title="预约待办"
                subtitle="把需要确认的地点、交通和费用拆成可执行事项。"
              />

              <div className="space-y-4">
                <RevisionNotice notice={revisionNotice} />
                <AppStatusStrip
                  Icon={Search}
                  title={statusMessages[0] ?? "AI 正在整理预约事项"}
                  detail={statusMessages[1] ?? "你可以先检查待办，确认无误后进入支付。"}
                />

                {todoCards.map((card) => <TodoGroup key={card.title} card={card} />)}

                {statusMessages.slice(2).map((message) => (
                  <AppStatusStrip key={message} Icon={MessageCircle} title={message} />
                ))}

                {loadError ? (
                  <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                    {loadError}
                  </div>
                ) : null}
              </div>
            </div>

            <div className={tabScreenComposerDockMtAutoClass}>
              <AppActionButton tone="blue" Icon={CalendarCheck2} onClick={goToCheckout}>
                查看预约详情与支付
              </AppActionButton>
              <AppComposer
                value={input}
                onChange={setInput}
                onSubmit={() => void handleComposerSubmit()}
                pending={submitPending}
                placeholder={submitPending ? "正在修改预约任务…" : "补充预约需求，例如时间更早、少排队..."}
              />
              <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
            </div>
          </>
        )}
      </div>
    </AppScreenShell>
  );
};
