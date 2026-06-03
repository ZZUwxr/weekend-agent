import { Check, MessageSquareText, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppErrorState,
  AppIconButton,
  AppPageHeader,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { submitTravelFeedback } from "../../lib/api";
import { TRIP_FEEDBACK_DONE_PATH, TRIP_FEEDBACK_PATH, TRIP_WRAP_PATH } from "../../routes";

type FlowState = { travelId?: string; planId?: string };

const TAG_OPTIONS = [
  { id: "route", label: "路线安排合理" },
  { id: "time", label: "时间节奏刚好" },
  { id: "rec", label: "推荐内容靠谱" },
  { id: "comm", label: "沟通顺畅及时" },
  { id: "more", label: "还有可提升空间" },
] as const;

export const TripFeedbackScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as FlowState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const resolvingTravel = resolved.loading && !loc?.travelId;
  const flow = { travelId, planId };

  const [rating, setRating] = useState(0);
  const [tags, setTags] = useState<Set<string>>(() => new Set());
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRIP_FEEDBACK_PATH) {
      document.title = "行程反馈 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  const toggleTag = (id: string): void => {
    setTags((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const goDone = async (skip = false): Promise<void> => {
    if (!travelId) {
      setSubmitError(resolvingTravel ? "正在同步当前行程，请稍后再试。" : "没有当前行程，请先创建行程。");
      return;
    }
    setSubmitPending(true);
    setSubmitError(null);
    const tagIds = [...tags];
    try {
      await submitTravelFeedback(travelId, {
        rating: skip || rating === 0 ? null : rating,
        rawFeedback: input.trim(),
        tags: skip ? ["skipped"] : tagIds,
        payload: {
          planId,
          tagLabels: tagIds.map((id) => TAG_OPTIONS.find((tag) => tag.id === id)?.label ?? id),
          skipped: skip,
        },
      });
      navigate(TRIP_FEEDBACK_DONE_PATH, { state: { ...flow, rating, tagIds, skipped: skip } });
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "提交反馈失败");
    } finally {
      setSubmitPending(false);
    }
  };

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow={`${planId.toUpperCase()} · 体验反馈`}
          title="这次安排怎么样？"
          subtitle="只需要十几秒，你的选择会影响下次推荐的排序和避坑。"
          action={<AppIconButton label="返回" to={TRIP_WRAP_PATH} state={flow} />}
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          <div className="space-y-3">
            {submitError ? <AppErrorState message={submitError} /> : null}

            <AppCard>
              <h2 className="text-[17px] font-bold text-[#111827]">整体评分</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-[#64748b]">点击星星即可选择，触控区域已经放大。</p>
              <div className="mt-4 flex justify-between gap-1" role="group" aria-label="星级评分">
                {[1, 2, 3, 4, 5].map((n) => {
                  const on = rating >= n;
                  return (
                    <button
                      key={n}
                      type="button"
                      aria-label={`${n} 星`}
                      aria-pressed={on}
                      onClick={() => setRating(n)}
                      className="flex h-14 flex-1 items-center justify-center rounded-[14px] bg-[#f8fafc] transition active:scale-95"
                    >
                      <Star
                        className={`h-8 w-8 ${on ? "fill-[#ffd95a] text-[#8a5a00]" : "fill-transparent text-[#cbd5e1]"}`}
                        strokeWidth={1.8}
                      />
                    </button>
                  );
                })}
              </div>
            </AppCard>

            <AppCard>
              <h2 className="text-[17px] font-bold text-[#111827]">印象最深的点</h2>
              <p className="mt-1 text-[12px] font-medium leading-5 text-[#64748b]">可多选，选中后会有明确高亮。</p>
              <div className="mt-4 grid grid-cols-2 gap-2">
                {TAG_OPTIONS.map((tag) => {
                  const selected = tags.has(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => toggleTag(tag.id)}
                      className={`flex min-h-[58px] items-center gap-2 rounded-[14px] border px-3 py-2 text-left transition active:scale-[0.98] ${
                        selected
                          ? "border-[#2456a6] bg-[#edf5ff] text-[#2456a6]"
                          : "border-[#e5e7eb] bg-white text-[#374151]"
                      }`}
                    >
                      <span
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-[10px] ${
                          selected ? "bg-[#2456a6] text-white" : "bg-[#f1f5f9] text-[#94a3b8]"
                        }`}
                        aria-hidden
                      >
                        {selected ? <Check className="h-4 w-4" strokeWidth={2.6} /> : null}
                      </span>
                      <span className="text-[13px] font-bold leading-5">{tag.label}</span>
                    </button>
                  );
                })}
              </div>
            </AppCard>

            <AppCard>
              <h2 className="text-[17px] font-bold text-[#111827]">补充一句</h2>
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                rows={5}
                placeholder="例如：餐厅不错，但下一次希望少走路..."
                className="mt-3 w-full resize-none rounded-[14px] border border-[#dbe3ee] bg-[#f8fafc] px-3 py-3 text-[14px] leading-6 text-[#111827] outline-none placeholder:text-[#94a3b8] focus:border-[#2456a6]"
              />
            </AppCard>

            <AppStatusStrip
              Icon={MessageSquareText}
              title="反馈会写入你的偏好"
              detail="下次生成路线时，会自动参考这次评价中的活动、节奏和避坑点。"
            />
          </div>
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton
            tone="blue"
            disabled={submitPending || resolvingTravel || !travelId}
            onClick={() => void goDone(false)}
          >
            {resolvingTravel ? "同步行程中..." : submitPending ? "提交中..." : "提交反馈"}
          </AppActionButton>
          <button
            type="button"
            disabled={submitPending}
            onClick={() => void goDone(true)}
            className="min-h-11 rounded-[12px] bg-white text-[13px] font-bold text-[#64748b] shadow-[0_6px_18px_rgba(15,23,42,0.06)] disabled:opacity-60"
          >
            暂不评价
          </button>
          <AppBottomNav active="行程" journeyFlow={flow} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
};
