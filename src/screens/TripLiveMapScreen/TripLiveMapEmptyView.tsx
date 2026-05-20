import { Bell, ChevronLeft, MapPin, Route, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { FIGMA_MAP_126_4627 } from "../../lib/api/mock/figma-map-126-4627-assets";
import { CHAT_PATH, ITINERARY_HUB_PATH } from "../../routes";

type Props = { travelId: string; planId: string };

/** 圆角视窗内仅一张稿图：勿再叠 DOM（图钉/文案/按钮），否则与图重复 */
const mapViewportClass =
  "relative h-[min(374px,52vh)] min-h-[280px] w-full overflow-hidden rounded-[24px] border border-[#dbeafe]/90 bg-[#dbeafe]/40 shadow-[0px_4px_20px_rgba(80,169,254,0.12)]";

const MAP_EMPTY_VIEWPORT = `${import.meta.env.BASE_URL}map-empty-viewport.png`;

export function TripLiveMapEmptyView({ travelId, planId }: Props): JSX.Element {
  const navigate = useNavigate();
  const flow = { travelId, planId };

  const goBack = (): void => {
    const hist = typeof window.history !== "undefined" ? window.history.state : null;
    const idx =
      typeof hist === "object" && hist !== null && "idx" in hist
        ? Number((hist as { idx?: unknown }).idx)
        : NaN;
    if (!Number.isNaN(idx) && idx > 0) navigate(-1);
    else navigate(ITINERARY_HUB_PATH, { state: flow });
  };

  return (
    <AppScreenShell frameClassName="bg-[linear-gradient(180deg,#e8f2fc_0%,#eef5f9_45%,#f4f6f8_100%)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-90">
        <img
          src={FIGMA_MAP_126_4627.bgBlobB}
          alt=""
          className="absolute -left-[120px] top-[40%] h-[900px] w-[1200px] max-w-none opacity-25"
        />
      </div>

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col pt-1">
        <div className="relative z-10 w-full shrink-0 px-3 pt-2">
          <div className={mapViewportClass}>
            <div className="absolute left-2.5 top-2 z-[10]">
              <button
                type="button"
                aria-label="返回上一页"
                onClick={goBack}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.12)] backdrop-blur-sm transition-opacity hover:opacity-95"
              >
                <ChevronLeft className="h-[22px] w-[22px]" strokeWidth={1.85} aria-hidden />
              </button>
            </div>
            {/* 裁掉静帧顶部系统状态栏（截图自带），勿与宿主状态栏重复 */}
            <img
              src={MAP_EMPTY_VIEWPORT}
              alt=""
              className="absolute inset-0 z-0 h-full w-full object-cover object-top [clip-path:inset(10%_0_0_0)]"
            />
          </div>
        </div>

        <div className="relative z-30 -mt-5 flex min-h-0 flex-1 flex-col rounded-t-[22px] bg-white px-4 pb-3 pt-1 shadow-[0px_-8px_32px_rgba(15,23,42,0.08)]">
          <div className="mx-auto mb-3 h-1 w-10 shrink-0 rounded-full bg-[#d1d5db]" aria-hidden />

          <ContentFitZoom className="space-y-3 pb-2" recalcKey="trip-map-empty">
            <div className="flex gap-3 rounded-[14px] border border-[#e2e8f0] bg-white p-3.5 shadow-[0_1px_8px_rgba(15,23,42,0.04)]">
              <Sparkles className="mt-0.5 h-[18px] w-[18px] shrink-0 text-[#f5c814]" strokeWidth={1.75} />
              <div className="min-w-0 flex-1">
                <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold leading-snug text-[#374151]">
                  开始你的第一条行程
                </p>
                <p className="mt-1.5 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] font-medium leading-relaxed text-[#9ca3af]">
                  还没有安排，先告诉我你想和谁出门、想玩多久
                </p>
              </div>
              <Link
                to={CHAT_PATH}
                state={{ message: "我想开始规划今天的行程", travelId }}
                className="shrink-0 self-center rounded-full bg-[#fffbeb] px-3.5 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#374151] shadow-[inset_0_0_0_1px_#fde68a] transition-opacity hover:opacity-90"
              >
                立即开始
              </Link>
            </div>

            <div className="rounded-[14px] border border-[#e2e8f0] bg-white p-3.5 shadow-[0_1px_8px_rgba(15,23,42,0.04)]">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-[18px] w-[18px] text-[#f5c814]" strokeWidth={1.75} />
                <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#374151]">为你提供</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-[#fffbeb] px-2.5 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#57534e] shadow-[inset_0_0_0_1px_#fef3c7]">
                  <MapPin className="h-3 w-3 text-[#eab308]" strokeWidth={2} />
                  智能推荐地点
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-[#fffbeb] px-2.5 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#57534e] shadow-[inset_0_0_0_1px_#fef3c7]">
                  <Route className="h-3 w-3 text-[#eab308]" strokeWidth={2} />
                  自动规划路线
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-[#fffbeb] px-2.5 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-semibold text-[#57534e] shadow-[inset_0_0_0_1px_#fef3c7]">
                  <Bell className="h-3 w-3 text-[#eab308]" strokeWidth={2} />
                  途中提醒与调整
                </span>
              </div>
            </div>
          </ContentFitZoom>

          <AppBottomNav active="地图" journeyFlow={{ travelId, planId }} />
        </div>
      </div>
    </AppScreenShell>
  );
}
