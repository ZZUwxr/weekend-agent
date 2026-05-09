import {
  Bell,
  Car,
  ChevronRight,
  CircleHelp,
  Heart,
  HeartCrack,
  Info,
  LayoutGrid,
  Leaf,
  MapPin,
  MessageCircle,
  Share2,
  Sparkles,
  Star,
  Users,
  Utensils,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { JourneyBottomNav } from "../../components/JourneyBottomNav";
import { Card, CardContent } from "../../components/ui/card";
import { fetchProfilePage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  ProfileMemoryRowDto,
  ProfilePageDto,
  ProfilePreferenceRowDto,
  ProfileQuickFooterActionDto,
} from "../../lib/api/types";
import {
  ACTIVITY_PREFERENCES_PATH,
  BUDGET_PACE_PREFERENCES_PATH,
  CHAT_PATH,
  DIETARY_PREFERENCES_PATH,
  ITINERARY_HUB_PATH,
  PROFILE_PATH,
  TRAVEL_MODE_SETTINGS_PATH,
} from "../../routes";

type ProfileLocationState = { travelId?: string; planId?: string };

function PrefIcon({ row }: { row: ProfilePreferenceRowDto }): JSX.Element {
  const cls = "h-4 w-4 shrink-0 text-[#2563eb]";
  switch (row.kind) {
    case "car":
      return <Car className={cls} strokeWidth={1.75} />;
    case "food":
      return <Utensils className={cls} strokeWidth={1.75} />;
    case "activity":
      return <Leaf className={cls} strokeWidth={1.75} />;
    default:
      return <Wallet className={cls} strokeWidth={1.75} />;
  }
}

function MemoryIcon({ row }: { row: ProfileMemoryRowDto }): JSX.Element {
  const cls = "h-4 w-4 shrink-0 text-[#2563eb]";
  switch (row.kind) {
    case "agent_weights":
      return <Sparkles className={cls} strokeWidth={1.75} />;
    case "last_feedback":
      return <MessageCircle className={cls} strokeWidth={1.75} />;
    default:
      return <HeartCrack className={cls} strokeWidth={1.75} />;
  }
}

function FooterActionIcon({ a }: { a: ProfileQuickFooterActionDto }): JSX.Element {
  const cls = "h-5 w-5 text-[#2563eb]";
  switch (a.kind) {
    case "share":
      return <Share2 className={cls} strokeWidth={1.75} />;
    case "rate":
      return <Star className={cls} strokeWidth={1.75} />;
    case "help":
      return <CircleHelp className={cls} strokeWidth={1.75} />;
    default:
      return <Info className={cls} strokeWidth={1.75} />;
  }
}

export const ProfileScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as ProfileLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [page, setPage] = useState<ProfilePageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === PROFILE_PATH) {
      document.title = "我的 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchProfilePage()
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-[#f3f4f6]">
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
            <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[20px] font-bold text-[#111827]">
              {page?.navTitle ?? "我的"}
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
                <Link
                  to={CHAT_PATH}
                  state={{
                    message: "我想完善我的个人资料与起点设置",
                    travelId: flow.travelId,
                  }}
                  className="flex w-full items-center gap-3 rounded-[16px] border border-[#e5e7eb] bg-white p-3 text-left shadow-[0px_2px_12px_rgba(0,0,0,0.04)] transition-opacity hover:opacity-95 active:scale-[0.99]"
                >
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#e0f2fe] text-2xl">
                    {page.avatarImageUrl ? (
                      <img src={page.avatarImageUrl} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <span>{page.avatarEmoji ?? "👤"}</span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-bold text-[#111827]">
                      {page.userName}
                    </p>
                    <p className="mt-0.5 flex items-start gap-1 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium leading-snug text-[#6b7280]">
                      <MapPin className="mt-0.5 h-3 w-3 shrink-0 text-[#2563eb]" strokeWidth={2} />
                      <span>{page.defaultStartLine}</span>
                    </p>
                  </div>
                  <ChevronRight className="h-5 w-5 shrink-0 text-[#9ca3af]" strokeWidth={1.75} />
                </Link>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-3">
                    <div className="mb-2.5 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                          {page.archiveSectionTitle}
                        </span>
                      </div>
                      <Link
                        to={CHAT_PATH}
                        state={{
                          message: "我想编辑我的出行档案信息",
                          travelId: flow.travelId,
                        }}
                        className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#2563eb]"
                      >
                        {page.archiveEditLabel}
                      </Link>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {page.archiveTags.map((tag) => (
                        <span
                          key={tag.id}
                          className="inline-flex items-center gap-1 rounded-full bg-[#eff6ff] px-3 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#1e40af]"
                        >
                          <span>{tag.iconEmoji}</span>
                          {tag.label}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center justify-between border-b border-[#f3f4f6] px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Heart className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                          {page.preferenceSectionTitle}
                        </span>
                      </div>
                      <Link
                        to={TRAVEL_MODE_SETTINGS_PATH}
                        state={flow}
                        className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#2563eb]"
                      >
                        {page.preferenceEditLabel}
                      </Link>
                    </div>
                    {page.preferenceRows.map((row, i) => {
                      const rowCls = `flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
                        i < page.preferenceRows.length - 1 ? "border-b border-[#f3f4f6]" : ""
                      }`;
                      const inner = (
                        <>
                          <PrefIcon row={row} />
                          <div className="min-w-0 flex-1">
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#111827]">
                              {row.title}
                            </p>
                            <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] text-[#6b7280]">
                              {row.summary}
                            </p>
                          </div>
                          <ChevronRight className="h-4 w-4 shrink-0 text-[#d1d5db]" strokeWidth={1.75} />
                        </>
                      );
                      if (row.kind === "car") {
                        return (
                          <Link
                            key={row.id}
                            to={TRAVEL_MODE_SETTINGS_PATH}
                            state={flow}
                            className={rowCls}
                          >
                            {inner}
                          </Link>
                        );
                      }
                      if (row.kind === "food") {
                        return (
                          <Link
                            key={row.id}
                            to={DIETARY_PREFERENCES_PATH}
                            state={flow}
                            className={rowCls}
                          >
                            {inner}
                          </Link>
                        );
                      }
                      if (row.kind === "activity") {
                        return (
                          <Link
                            key={row.id}
                            to={ACTIVITY_PREFERENCES_PATH}
                            state={flow}
                            className={rowCls}
                          >
                            {inner}
                          </Link>
                        );
                      }
                      if (row.kind === "budget") {
                        return (
                          <Link
                            key={row.id}
                            to={BUDGET_PACE_PREFERENCES_PATH}
                            state={flow}
                            className={rowCls}
                          >
                            {inner}
                          </Link>
                        );
                      }
                      return (
                        <button key={row.id} type="button" className={rowCls}>
                          {inner}
                        </button>
                      );
                    })}
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="border-b border-[#f3f4f6] px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                          {page.memorySectionTitle}
                        </span>
                      </div>
                    </div>
                    {page.memoryRows.map((row, i) => (
                      <Link
                        key={row.id}
                        to={ITINERARY_HUB_PATH}
                        state={flow}
                        className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
                          i < page.memoryRows.length - 1 ? "border-b border-[#f3f4f6]" : ""
                        }`}
                      >
                        <MemoryIcon row={row} />
                        <span className="min-w-0 flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#374151]">
                          {row.label}
                        </span>
                        <ChevronRight className="h-4 w-4 shrink-0 text-[#d1d5db]" strokeWidth={1.75} />
                      </Link>
                    ))}
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-3">
                    <div className="mb-2.5 flex items-center gap-2">
                      <LayoutGrid className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.templatesSectionTitle}
                      </span>
                    </div>
                    <div className="space-y-2.5">
                      {page.templates.map((t) => (
                        <Link
                          key={t.id}
                          to={ITINERARY_HUB_PATH}
                          state={flow}
                          className="flex w-full items-center gap-3 rounded-xl border border-[#f3f4f6] bg-[#fafafa]/50 p-2 text-left hover:bg-[#f9fafb]"
                        >
                          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-white text-2xl shadow-sm">
                            {t.thumbImageUrl ? (
                              <img src={t.thumbImageUrl} alt="" className="h-full w-full object-cover" />
                            ) : (
                              <span>{t.thumbEmoji ?? "📋"}</span>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-bold text-[#111827]">
                              {t.title}
                            </p>
                            <span className="mt-1 inline-block rounded-md bg-[#dbeafe] px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] font-semibold text-[#1d4ed8]">
                              {t.usageBadge}
                            </span>
                          </div>
                          <ChevronRight className="h-4 w-4 shrink-0 text-[#d1d5db]" strokeWidth={1.75} />
                        </Link>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-4 gap-2 pb-1">
                  {page.quickFooterActions.map((a) =>
                    a.kind === "help" ? (
                      <Link
                        key={a.id}
                        to={CHAT_PATH}
                        state={{ message: "我需要使用帮助", travelId: flow.travelId }}
                        className="flex flex-col items-center gap-1 rounded-xl bg-white py-3 shadow-[0px_1px_6px_rgba(0,0,0,0.06)] transition-opacity hover:opacity-90"
                      >
                        <FooterActionIcon a={a} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#4b5563]">
                          {a.label}
                        </span>
                      </Link>
                    ) : (
                      <button
                        key={a.id}
                        type="button"
                        className="flex flex-col items-center gap-1 rounded-xl bg-white py-3 shadow-[0px_1px_6px_rgba(0,0,0,0.06)] transition-opacity hover:opacity-90"
                      >
                        <FooterActionIcon a={a} />
                        <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[9px] font-semibold text-[#4b5563]">
                          {a.label}
                        </span>
                      </button>
                    ),
                  )}
                </div>
              </>
            )}
          </div>

          <JourneyBottomNav active="我的" travelId={travelId} planId={planId} />
        </div>
      </div>
    </main>
  );
};
