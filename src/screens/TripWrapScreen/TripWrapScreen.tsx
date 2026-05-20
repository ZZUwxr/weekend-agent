import type { ReactNode } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { FIGMA_TRIP_WRAP_159 } from "../../lib/api/mock/figma-trip-wrap-159-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { ITINERARY_HUB_PATH, TRIP_FEEDBACK_PATH, TRIP_WRAP_PATH } from "../../routes";

type TripWrapLocationState = { travelId?: string; planId?: string };

function titleGradientClass(): string {
  return "bg-[linear-gradient(24.482deg,rgb(95,115,128)_16.391%,rgb(62,82,101)_73.16%,rgb(42,114,176)_96.32%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function TripGlowCardFrame({ children }: { children: ReactNode }): JSX.Element {
  return (
    <div className="relative overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_0px_#d0def8]">
      <img
        src={FIGMA_TRIP_WRAP_159.cardGlow1}
        alt=""
        className="pointer-events-none absolute left-[114px] top-[33px] z-0 h-[242px] w-[293px] max-w-none object-cover opacity-[0.32]"
      />
      <img
        src={FIGMA_TRIP_WRAP_159.cardGlow2}
        alt=""
        className="pointer-events-none absolute -left-[110px] -top-[147px] z-0 h-[220px] w-[271px] max-w-none object-cover opacity-[0.32]"
      />
      <div className="relative z-[2] isolate">{children}</div>
    </div>
  );
}

function ActionChip({ label }: { label: string }): JSX.Element {
  return (
    <button
      type="button"
      className="min-h-[35px] flex-1 rounded-[7px] border-[0.5px] border-[#faf2ac] bg-[radial-gradient(ellipse_at_center,rgba(250,242,171,0.65)_0%,rgba(255,255,255,0.95)_100%)] px-1 py-2 shadow-[0px_0.7px_1.4px_0px_#d1e8ff] transition-opacity hover:opacity-90"
    >
      <span className="[font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10px] font-semibold leading-tight text-[#343d43]">{label}</span>
    </button>
  );
}

/** 第十屏 · 与 Figma node 159:6179（iPhone 16 & 17 Pro - 35）对齐 */
export const TripWrapScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as TripWrapLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [input, setInput] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_WRAP_PATH) {
      document.title = "行程收尾 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  const summaryCopy =
    "总结一下：我们下午 2 点半出发，先去农场让孩子撒欢，傍晚在素然花园靠窗位，吃顿好的，饭后江边散步消食。\n\n老婆的缓冲时间和健康推荐都安排好了，孩子也尽兴。祝一家人玩得开心～ ";

  return (
    <AppScreenShell frameClassName="bg-white">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <img
            src={FIGMA_TRIP_WRAP_159.bgBlobA}
            alt=""
            className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
          />
          <img
            src={FIGMA_TRIP_WRAP_159.bgBlobB}
            alt=""
            className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-[0.93]"
          />
        </div>

        <EmbeddedStatusBarImage
          src={FIGMA_TRIP_WRAP_159.statusBar}
          className="relative z-[1]"
          height={61}
          width={402}
        />

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-[27px] pb-3 pt-3">
          <ContentFitZoom className="space-y-[18px] pb-8" recalcKey="trip-wrap">
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-[12px] border border-[#93c5fd] bg-white/95 px-3 py-2.5 shadow-[0px_2px_8px_rgba(37,99,235,0.08)] backdrop-blur-sm">
              <span className="max-w-[210px] [font-family:'PingFang_SC',sans-serif] text-[11px] font-medium leading-snug text-[#475569]">
                <span className="text-[#0f172a]">简短体验反馈</span>
                （不影响结束行程）
              </span>
              <Link
                to={TRIP_FEEDBACK_PATH}
                state={flow}
                aria-label="填写行程反馈"
                className="shrink-0 rounded-lg bg-[#ffd100] px-3 py-1.5 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-bold text-[#343d43] shadow-sm transition-opacity hover:opacity-95"
              >
                去填写
              </Link>
            </div>

            <TripGlowCardFrame>
              <div className="px-[10px] pb-3 pt-[14px]">
                <header className="relative mb-[11px] flex items-start gap-2 pr-7">
                  <img src={FIGMA_TRIP_WRAP_159.sparkle} alt="" width={24} height={24} className="h-6 w-6 shrink-0 object-contain" />
                  <h2
                    className={`min-w-0 flex-1 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-[20px] ${titleGradientClass()}`}
                  >
                    还能帮你
                  </h2>
                  <ChevronDown className="absolute right-1 top-2 h-[11px] w-[9px] shrink-0 text-[#9ca3af]" strokeWidth={2} aria-hidden />
                </header>
                <div className="flex gap-2">
                  <ActionChip label="分享行程" />
                  <ActionChip label="添加到日历" />
                  <ActionChip label="出发提醒" />
                </div>
              </div>
            </TripGlowCardFrame>

            <div className="max-w-[298px] rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white px-[13px] pb-4 pt-6 shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)]">
              <p className="whitespace-pre-wrap [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] font-semibold leading-[20px] text-[#626262]">
                {summaryCopy.trim()}
              </p>
            </div>

            <TripGlowCardFrame>
              <div className="px-3 pb-5 pt-4">
                <header className="relative mb-2 flex items-start gap-2 pr-7">
                  <img src={FIGMA_TRIP_WRAP_159.sparkle} alt="" width={24} height={24} className="h-6 w-6 shrink-0 object-contain" />
                  <h2
                    className={`min-w-0 flex-1 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold leading-[20px] ${titleGradientClass()}`}
                  >
                    这趟行程结束了吗？
                  </h2>
                  <ChevronDown className="absolute right-1 top-2 h-[11px] w-[9px] shrink-0 text-[#9ca3af]" strokeWidth={2} aria-hidden />
                </header>
                <p className="relative z-[3] mt-2 pr-6 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12.5px] font-normal leading-[20px] text-[#626262]">
                  已经到达预定结束时间，是否确认结束行程
                </p>
              </div>
            </TripGlowCardFrame>

            <div className="flex justify-end pr-3">
              <Link
                to={TRIP_FEEDBACK_PATH}
                state={flow}
                className="inline-flex min-w-[72px] items-center justify-center rounded-bl-[15.417px] rounded-br-[15.417px] rounded-tl-[15.417px] bg-[#ffd100] px-[27px] py-[2px] shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)] transition-opacity hover:opacity-95 active:opacity-90"
              >
                <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold leading-[26px] text-[#343d43]">
                  确认
                </span>
              </Link>
            </div>

            <div className="max-w-[298px] rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white px-2.5 py-4 shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)]">
              <p className="whitespace-pre-wrap [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[12px] font-semibold leading-[20px] text-[#626262]">
                好的，本次行程已结束，可在历史行程中再次查看～
              </p>
            </div>
          </ContentFitZoom>

          <div className="mt-auto flex flex-col gap-3 pt-2">
            <div className="flex items-center gap-2">
              <div className="relative flex min-h-[41px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-3 pr-[46px] shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
                <img
                  src={FIGMA_TRIP_WRAP_159.voiceChip}
                  alt=""
                  className="absolute right-3 top-1/2 z-[2] h-7 w-[34px] -translate-y-1/2 select-none object-contain"
                />
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder=""
                  className="min-w-0 flex-1 bg-transparent py-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#343d4380]"
                />
              </div>
              <Link
                to={ITINERARY_HUB_PATH}
                state={flow}
                aria-label="进入行程主页"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} aria-hidden />
              </Link>
            </div>
            <AppBottomNav active="首页" journeyFlow={{ travelId, planId }} />
          </div>
        </div>
    </AppScreenShell>
  );
};
