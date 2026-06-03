import { Bell, ChevronLeft, MapPin, Navigation, Route, Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppComposer,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { AI_TASK_PATH, ITINERARY_HUB_PATH } from "../../routes";

type Props = { travelId: string; planId: string };

export function TripLiveMapEmptyView({ travelId, planId }: Props): JSX.Element {
  const navigate = useNavigate();
  const flow = { travelId, planId };
  const [text, setText] = useState("");
  const { toastMessage, showToast } = useAppToast();

  const goBack = (): void => {
    const hist = typeof window.history !== "undefined" ? window.history.state : null;
    const idx =
      typeof hist === "object" && hist !== null && "idx" in hist
        ? Number((hist as { idx?: unknown }).idx)
        : NaN;
    if (!Number.isNaN(idx) && idx > 0) navigate(-1);
    else navigate(ITINERARY_HUB_PATH, { state: flow });
  };

  const startMessage = text.trim() || "我想开始规划今天的行程";

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className="relative z-10 w-full shrink-0 px-2 pt-1">
        <div className="relative h-[min(374px,52vh)] min-h-[300px] overflow-hidden rounded-[30px] bg-[#dbeafe] shadow-[inset_0_0_0_1px_rgba(80,169,254,0.12)]">
          <div className="absolute inset-0 bg-[linear-gradient(135deg,#dbeafe_0%,#eff6ff_48%,#dcfce7_100%)]" />
          <div className="absolute left-[14%] top-[23%] h-20 w-20 rounded-full border border-white/70 bg-white/40" />
          <div className="absolute right-[18%] top-[34%] h-28 w-28 rounded-full border border-white/70 bg-white/35" />
          <div className="absolute bottom-[18%] left-[-8%] h-28 w-[120%] rotate-[-12deg] rounded-full bg-white/38" />
          <div className="absolute bottom-[31%] left-[-8%] h-16 w-[120%] rotate-[15deg] rounded-full bg-white/30" />
          <div className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-[#2456a6] text-white shadow-[0_14px_30px_rgba(36,86,166,0.25)]">
            <MapPin className="h-8 w-8" strokeWidth={2.2} />
          </div>

          <button
            type="button"
            aria-label="返回上一页"
            onClick={goBack}
            className="absolute left-3 top-3 z-10 flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.12)] backdrop-blur-sm transition active:scale-95"
          >
            <ChevronLeft className="h-[22px] w-[22px]" strokeWidth={1.85} aria-hidden />
          </button>

          <button
            type="button"
            aria-label="地图说明"
            onClick={() => showToast("创建行程后，实时位置与下一站会显示在这里")}
            className="absolute right-3 top-3 z-10 flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.12)] backdrop-blur-sm transition active:scale-95"
          >
            <Navigation className="h-[18px] w-[18px]" strokeWidth={2.1} />
          </button>
        </div>
      </div>

      <div className={`relative z-30 -mt-4 flex min-h-0 flex-1 flex-col rounded-t-[28px] bg-white pb-2 pt-4 shadow-[0px_-4px_24px_rgba(80,169,254,0.12)] ${tabScreenPrimaryColumnPaddingXClass}`}>
        <div className="min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            <AppCard>
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#edf5ff] text-[#2456a6]">
                  <Sparkles className="h-5 w-5" strokeWidth={2.1} />
                </span>
                <div className="min-w-0 flex-1">
                  <h1 className="text-[20px] font-bold leading-7 text-[#111827]">开始你的第一条行程</h1>
                  <p className="mt-2 text-[13px] font-medium leading-5 text-[#64748b]">
                    创建行程后，这里会显示当前位置、下一站、叫车提醒和途中调整入口。
                  </p>
                </div>
              </div>
            </AppCard>

            <AppStatusStrip
              Icon={MapPin}
              title="智能推荐地点"
              detail="根据同行人、距离、预算和时间筛选适合地点。"
            />
            <AppStatusStrip
              Icon={Route}
              title="自动规划路线"
              detail="生成转场时间、缓冲区间和完整时间轴。"
            />
            <AppStatusStrip
              Icon={Bell}
              title="途中提醒与调整"
              detail="行程开始后可实时修改，空输入不会误触推进。"
            />
          </div>
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton
            tone="blue"
            onClick={() => navigate(AI_TASK_PATH, { state: { message: startMessage, travelId } })}
          >
            立即开始规划
          </AppActionButton>
          <AppComposer
            value={text}
            onChange={setText}
            onSubmit={() => navigate(AI_TASK_PATH, { state: { message: startMessage, travelId } })}
            placeholder="例如：今天下午和家人轻松玩一下..."
          />
          <AppBottomNav active="地图" journeyFlow={{ travelId, planId }} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
}
