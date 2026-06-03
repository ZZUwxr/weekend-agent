import { Check, Loader2, Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppScreenShell } from "../../components/AppScreenShell";
import {
  AppBackdrop,
  AppCard,
  AppIconButton,
  AppPageHeader,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { streamTravelSession } from "../../lib/api";
import type { TravelPlanningStreamEvent } from "../../lib/api/types";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenPrimaryColumnPaddingXClass } from "../../lib/tabScreenDockLayout";
import { CHAT_PATH, HOME_PATH } from "../../routes";

type AiTaskLocationState = {
  message?: string;
  companionIds?: string[];
};

type TaskStep = {
  id: string;
  title: string;
  detail: string;
  done: boolean;
};

const DEFAULT_MESSAGE = "我和家人想在今天下午出门放松放松";

const INITIAL_STEPS: TaskStep[] = [
  { id: "intent", title: "理解需求", detail: "拆解同行人、时间、距离和偏好", done: false },
  { id: "context", title: "整理约束", detail: "识别饮食、体力、预算和天气风险", done: false },
  { id: "places", title: "检索地点", detail: "查找可去的活动、餐饮和备选点", done: false },
  { id: "route", title: "规划路线", detail: "计算转场、排队、停留与缓冲时间", done: false },
  { id: "score", title: "评分推荐", detail: "比较候选方案，选择更稳的路线", done: false },
  { id: "finish", title: "整理结果", detail: "生成可继续确认和修改的方案", done: false },
];

function stepIdForEvent(event: TravelPlanningStreamEvent): string {
  const text = `${event.event} ${String(event.data.tool_name ?? "")} ${String(event.data.tool ?? "")} ${String(event.data.summary ?? "")} ${String(event.data.decision_summary ?? "")}`;
  if (/understand|intent|理解|clarification|ask_clarification/.test(text)) return "intent";
  if (/conflict|constraint|validate|约束|冲突|校验/.test(text)) return "context";
  if (/poi|place|weather|queue|地点|天气|排队/.test(text)) return "places";
  if (/route|timeline|路线|时间轴|转场/.test(text)) return "route";
  if (/score|recommend|推荐|评分/.test(text)) return "score";
  if (/plan_complete|final|输出|完成/.test(text)) return "finish";
  return "context";
}

function valueText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function cleanUserMessage(text: string): string {
  const lower = text.toLowerCase();
  const hasInternalMarker =
    /[a-z]+_[a-z_]+/.test(text) ||
    /规则\s*\d+/.test(text) ||
    /当前状态/.test(text) ||
    /数据字段/.test(text);
  if (
    !text ||
    hasInternalMarker ||
    lower.includes("group_type") ||
    lower.includes("tool_name") ||
    lower.includes("function") ||
    text.includes("调用工具")
  ) {
    return "";
  }
  return text
    .replace(/^agent[_ ]action[:：]?\s*/i, "")
    .replace(/^tool[_ ]observation[:：]?\s*/i, "")
    .trim();
}

function labelForEvent(event: TravelPlanningStreamEvent): string {
  const explicit = cleanUserMessage(
    valueText(event.data.mobile_label) ||
      valueText(event.data.summary) ||
      valueText(event.data.decision_summary) ||
      valueText(event.data.message) ||
      valueText(event.data.label),
  );
  if (explicit) return explicit;

  const id = stepIdForEvent(event);
  if (event.event === "plan_complete") return "方案已经整理好，正在准备可确认的页面...";
  if (id === "intent") return "正在理解同行人、出发时间和这次出门的重点...";
  if (id === "context") return "正在检查预算、体力、饮食和天气等约束...";
  if (id === "places") return "正在筛选附近适合的地点和备选安排...";
  if (id === "route") return "正在比较路线、转场时间和缓冲空间...";
  if (id === "score") return "正在给候选方案打分，找出更稳的一条...";
  return "正在把规划结果整理成可继续修改的方案...";
}

function TaskStepRow({ step, active }: { step: TaskStep; active: boolean }): JSX.Element {
  return (
    <div className="flex gap-3 rounded-[16px] border border-[#e5e7eb] bg-white px-3 py-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)]">
      <div
        className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
          step.done ? "bg-[#0f766e] text-white" : active ? "bg-[#edf5ff] text-[#2456a6]" : "bg-[#f1f5f9] text-[#94a3b8]"
        }`}
      >
        {step.done ? (
          <Check className="h-4 w-4" strokeWidth={2.4} />
        ) : active ? (
          <Loader2 className="h-4 w-4 animate-spin" strokeWidth={2.1} />
        ) : (
          <Search className="h-4 w-4" strokeWidth={2.1} />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-bold leading-5 text-[#111827]">{step.title}</p>
        <p className="mt-1 text-[12px] font-medium leading-5 text-[#64748b]">{step.detail}</p>
      </div>
    </div>
  );
}

export const AiTaskProgressScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as AiTaskLocationState | null;
  const message = loc?.message?.trim() || DEFAULT_MESSAGE;
  const companionIds = useMemo(
    () => (Array.isArray(loc?.companionIds) ? loc.companionIds.filter(Boolean) : []),
    [loc?.companionIds],
  );

  const [steps, setSteps] = useState<TaskStep[]>(INITIAL_STEPS);
  const [currentStepId, setCurrentStepId] = useState("intent");
  const [liveMessage, setLiveMessage] = useState("AI 正在理解你的安排...");
  const [error, setError] = useState<string | null>(null);

  const completedCount = useMemo(() => steps.filter((step) => step.done).length, [steps]);
  const percent = Math.max(8, Math.round((completedCount / steps.length) * 100));

  useEffect(() => {
    const prev = document.title;
    document.title = "AI 执行中 · 出行助手";
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    const markEvent = (event: TravelPlanningStreamEvent): void => {
      const id = stepIdForEvent(event);
      const detail = labelForEvent(event);
      setCurrentStepId(id);
      setLiveMessage(detail);
      setSteps((prev) => prev.map((step) => {
        if (event.event === "plan_complete") {
          return { ...step, done: true, detail: step.id === "finish" ? "规划完成，正在进入确认页" : step.detail };
        }
        if (step.id === id) {
          return { ...step, done: event.event === "tool_observation" || event.event === "score_updated", detail };
        }
        const currentIndex = INITIAL_STEPS.findIndex((item) => item.id === id);
        const stepIndex = INITIAL_STEPS.findIndex((item) => item.id === step.id);
        return stepIndex < currentIndex ? { ...step, done: true } : step;
      }));
    };

    void (async () => {
      try {
        const { travelId } = await streamTravelSession({ message, companionIds }, markEvent);
        if (!active) return;
        setCurrentTravel({ travelId, planId: "plan-a" });
        setSteps((prev) => prev.map((step) => ({ ...step, done: true })));
        setLiveMessage("规划完成，正在进入确认页...");
        window.setTimeout(() => {
          if (active) navigate(CHAT_PATH, { state: { message, travelId } });
        }, 520);
      } catch (e: unknown) {
        if (active) {
          setError(e instanceof Error ? e.message : "AI 规划失败");
          setLiveMessage("规划遇到问题，可以返回重试。");
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [companionIds, message, navigate]);

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-5 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow="AI 正在推荐"
          title="正在执行当前任务"
          subtitle={message}
          action={<AppIconButton label="返回首页" to={HOME_PATH} />}
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            <AppCard className="overflow-hidden p-0">
              <div className="bg-[#111827] px-4 py-5 text-white">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white/12 text-[#ffd95a]">
                  <Sparkles className="h-6 w-6" strokeWidth={2.1} />
                </span>
                <h2 className="mt-4 text-[22px] font-bold leading-7">实时规划中</h2>
                <p className="mt-2 text-[13px] font-medium leading-5 text-white/72">{liveMessage}</p>
                <div className="mt-4">
                  <div className="mb-2 flex items-center justify-between text-[12px] font-bold">
                    <span className="text-white/72">阶段进度</span>
                    <span>{percent}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/12">
                    <div
                      className="h-full rounded-full bg-[#ffd95a] transition-[width] duration-500"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              </div>
            </AppCard>

            <AppStatusStrip Icon={Sparkles} title={liveMessage} detail="我会把关键进度同步在这里。" />

            <section className="space-y-2">
              {steps.map((step) => (
                <TaskStepRow key={step.id} step={step} active={step.id === currentStepId && !step.done} />
              ))}
            </section>

            {error ? (
              <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                {error}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </AppScreenShell>
  );
};
