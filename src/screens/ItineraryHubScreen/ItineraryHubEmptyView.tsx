import { Bell, CalendarPlus, Clock3, MapPinned, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppComposer,
  AppIconButton,
  AppPageHeader,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { AI_TASK_PATH, HOME_PATH } from "../../routes";

type Props = { travelId: string; planId: string };

export function ItineraryHubEmptyView({ travelId, planId }: Props): JSX.Element {
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const { toastMessage, showToast } = useAppToast();
  const flow = { travelId, planId };

  const startMessage = text.trim() || "我想创建一条周末出行计划";

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow="行程"
          title="还没有正在进行的行程"
          subtitle="创建一次计划后，这里会同步显示路线、预约、提醒和历史记录。"
          action={
            <AppIconButton label="通知" onClick={() => showToast("暂无新的行程通知")}>
              <Bell className="h-5 w-5" strokeWidth={2.1} />
            </AppIconButton>
          }
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            <AppCard className="overflow-hidden p-0">
              <div className="bg-[#111827] px-4 py-5 text-white">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white/12 text-[#ffd95a]">
                  <Sparkles className="h-6 w-6" strokeWidth={2.1} />
                </span>
                <h2 className="mt-4 text-[22px] font-bold leading-7">从一句话开始安排</h2>
                <p className="mt-2 text-[13px] font-medium leading-5 text-white/72">
                  说出同行人、时间和大概想法，AI 会先生成执行中的规划动画，再进入方案对比。
                </p>
              </div>
              <div className="space-y-2 px-4 py-4">
                <AppStatusStrip
                  Icon={Clock3}
                  title="实时规划进度"
                  detail="推荐过程会在下一屏实时展示，不再像静态等待页。"
                />
                <AppStatusStrip
                  Icon={MapPinned}
                  title="后续自动同步"
                  detail="支付、地图、行程主页都会使用同一个 travelId。"
                />
              </div>
            </AppCard>

            <div className="grid grid-cols-2 gap-2">
              <Link
                to={AI_TASK_PATH}
                state={{ message: "帮我安排一个亲子周末半日游", travelId }}
                className="flex min-h-[92px] flex-col justify-between rounded-[16px] border border-[#e5e7eb] bg-white p-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
              >
                <CalendarPlus className="h-5 w-5 text-[#2456a6]" strokeWidth={2.1} />
                <span className="text-[13px] font-bold leading-5 text-[#111827]">亲子半日游</span>
              </Link>
              <Link
                to={AI_TASK_PATH}
                state={{ message: "帮我安排今天晚上轻松一点的约会", travelId }}
                className="flex min-h-[92px] flex-col justify-between rounded-[16px] border border-[#e5e7eb] bg-white p-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)]"
              >
                <Sparkles className="h-5 w-5 text-[#8a5a00]" strokeWidth={2.1} />
                <span className="text-[13px] font-bold leading-5 text-[#111827]">轻松约会</span>
              </Link>
            </div>
          </div>
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton
            tone="blue"
            onClick={() => navigate(AI_TASK_PATH, { state: { message: startMessage, travelId } })}
          >
            创建第一条行程
          </AppActionButton>
          <AppComposer
            value={text}
            onChange={setText}
            onSubmit={() => navigate(AI_TASK_PATH, { state: { message: startMessage, travelId } })}
            placeholder="例如：明天下午带孩子和家人轻松玩一下..."
          />
          <AppBottomNav active="行程" journeyFlow={flow} variant="journey" />
          <Link to={HOME_PATH} className="sr-only">
            返回首页
          </Link>
        </div>
      </div>
    </AppScreenShell>
  );
}
