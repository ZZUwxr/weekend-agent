import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Route,
  SendHorizontal,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { RevisionNotice, type RevisionNoticeState } from "../../components/RevisionNotice";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { embeddedBackButtonTopClass } from "../../lib/embeddedStatusBar";
import { fetchPlanComparisonPage, reviseTravelPlan } from "../../lib/api";
import { FIGMA_PLANS_1119 } from "../../lib/api/mock/figma-plans-1119-assets";
import type {
  PlanActivityDto,
  PlanComparisonPageDto,
  PlanMemberRatingDto,
  TravelPlanCardDto,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { cn } from "../../lib/utils";
import { CHAT_PATH, PLANS_PATH, TIMELINE_PATH } from "../../routes";

type PlansLocationState = { travelId?: string; planId?: string };
type PlanChoiceLetter = "a" | "b" | "c";

type PlanTheme = {
  badge: string;
  border: string;
  button: string;
  dot: string;
  faint: string;
  progress: string;
  ring: string;
  softText: string;
};

const PLAN_LETTERS = ["A", "B", "C", "D", "E"];

const PLAN_THEMES: PlanTheme[] = [
  {
    badge: "bg-[#fff4d6] text-[#8a5a00]",
    border: "border-[#f1c96d]",
    button: "bg-[#1f2937] text-white shadow-[0_8px_18px_rgba(31,41,55,0.18)]",
    dot: "bg-[#f5b740]",
    faint: "bg-[#fff9ea]",
    progress: "bg-[#f5b740]",
    ring: "ring-[#f5b740]/25",
    softText: "text-[#8a5a00]",
  },
  {
    badge: "bg-[#e8f1ff] text-[#1d4ed8]",
    border: "border-[#93b9f8]",
    button: "bg-[#2456a6] text-white shadow-[0_8px_18px_rgba(36,86,166,0.2)]",
    dot: "bg-[#3b82f6]",
    faint: "bg-[#f1f6ff]",
    progress: "bg-[#3b82f6]",
    ring: "ring-[#3b82f6]/20",
    softText: "text-[#1d4ed8]",
  },
  {
    badge: "bg-[#e8f7f0] text-[#047857]",
    border: "border-[#8dd8b8]",
    button: "bg-[#0f766e] text-white shadow-[0_8px_18px_rgba(15,118,110,0.18)]",
    dot: "bg-[#10b981]",
    faint: "bg-[#f0fbf7]",
    progress: "bg-[#10b981]",
    ring: "ring-[#10b981]/20",
    softText: "text-[#047857]",
  },
];

/** 用户在第三页输入里表达选 A/B/C 即进入对应时间轴（第四页） */
function detectPlanChoiceFromInput(text: string): PlanChoiceLetter | null {
  const raw = text.trim();
  if (!raw) return null;

  const compact = raw.toLowerCase().replace(/\s+/g, "");
  const direct = compact.match(/^(?:plan)?([abc])$/);
  if (direct?.[1]) return direct[1] as PlanChoiceLetter;

  const hits = (["a", "b", "c"] as PlanChoiceLetter[]).filter((letter) => {
    const planPattern = new RegExp(`\\bplan\\s*[-_]?\\s*${letter}\\b`, "i");
    const reversePattern = new RegExp(`\\b${letter}\\s*plan\\b`, "i");
    const chinesePattern = new RegExp(`方案\\s*[-_]?\\s*${letter}`, "i");
    const choosePattern = new RegExp(`(?:选|选择|要|用|定|看)\\s*(?:plan\\s*)?${letter}`, "i");
    return (
      planPattern.test(raw) ||
      reversePattern.test(raw) ||
      chinesePattern.test(raw) ||
      choosePattern.test(raw)
    );
  });

  return hits.length === 1 ? hits[0] : null;
}

function resolveChoicePlanId(
  choice: PlanChoiceLetter,
  plans: TravelPlanCardDto[] | undefined,
): string {
  const upper = choice.toUpperCase();
  const matched = (plans ?? []).find((plan) => {
    const id = plan.id.toLowerCase();
    const label = `${plan.planLabel} ${plan.headline}`.toUpperCase();
    return (
      id === `plan-${choice}` ||
      id.endsWith(`-${choice}`) ||
      label.includes(`PLAN ${upper}`) ||
      label.includes(`方案${upper}`)
    );
  });
  return matched?.id ?? `plan-${choice}`;
}

function getPlanTheme(plan: TravelPlanCardDto, index: number): PlanTheme {
  if (plan.accent === "warm") return PLAN_THEMES[0];
  if (plan.accent === "cool") return PLAN_THEMES[1];
  return PLAN_THEMES[index % PLAN_THEMES.length];
}

function getPlanName(plan: TravelPlanCardDto, index: number): string {
  const raw = (plan.planLabel ?? "")
    .replace(/\s*[·•|:：-]\s*$/u, "")
    .trim();
  if (raw) return raw;
  return `Plan ${PLAN_LETTERS[index] ?? index + 1}`;
}

function getPlanHeadline(plan: TravelPlanCardDto, index: number): string {
  const label = plan.planLabel?.trim() ?? "";
  let headline = plan.headline?.trim() ?? "";
  if (label && headline.startsWith(label)) {
    headline = headline.slice(label.length).trim();
  }
  headline = headline.replace(/^[·•|:：-]\s*/u, "");
  return headline || getPlanName(plan, index);
}

function getPlanTags(plan: TravelPlanCardDto, limit = 6): string[] {
  const seen = new Set<string>();
  const tags: string[] = [];
  for (const activity of plan.activities ?? []) {
    for (const tag of activity.tags ?? []) {
      const label = tag.label.trim();
      if (!label || seen.has(label)) continue;
      seen.add(label);
      tags.push(label);
      if (tags.length >= limit) return tags;
    }
  }
  return tags;
}

function getScorePercent(member: PlanMemberRatingDto): number {
  const value = Number.isFinite(member.score) ? member.score : 0;
  return Math.max(0, Math.min(100, (value / 5) * 100));
}

function getFirstReason(plan: TravelPlanCardDto): string | null {
  return plan.compensationParagraphs?.find((line) => line.trim().length > 0) ?? null;
}

function selectRecommendedPlan(plans: TravelPlanCardDto[]): {
  plan: TravelPlanCardDto | null;
  index: number;
} {
  const index = Math.max(0, plans.findIndex((plan) => plan.recommended));
  return { plan: plans[index] ?? null, index };
}

function LoadingState(): JSX.Element {
  return (
    <div className="flex min-h-0 flex-1 flex-col px-[14px] py-5">
      <div className="mb-4 h-9 w-36 animate-pulse rounded-[8px] bg-[#e5e7eb]" />
      <div className="mb-4 h-28 animate-pulse rounded-[16px] bg-white shadow-[0_8px_24px_rgba(15,23,42,0.06)]" />
      <div className="space-y-3">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-44 animate-pulse rounded-[16px] bg-white shadow-[0_8px_24px_rgba(15,23,42,0.06)]"
          />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }): JSX.Element {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center px-[22px] text-center">
      <div className="rounded-[16px] border border-red-100 bg-white px-5 py-5 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
        <p className="text-[15px] font-semibold text-[#991b1b]">方案加载失败</p>
        <p className="mt-2 text-[12px] leading-5 text-[#64748b]">{message}</p>
      </div>
    </div>
  );
}

function SmallPill({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex min-h-7 items-center rounded-full px-3 text-[11px] font-semibold leading-none",
        className,
      )}
    >
      {children}
    </span>
  );
}

function RecommendationPanel({
  page,
  onSelectPlan,
}: {
  page: PlanComparisonPageDto;
  onSelectPlan: (planId: string) => void;
}): JSX.Element {
  const plans = Array.isArray(page.plans) ? page.plans : [];
  const { plan: recommended, index } = selectRecommendedPlan(plans);
  const theme = recommended ? getPlanTheme(recommended, index) : PLAN_THEMES[0];
  const tags = recommended ? getPlanTags(recommended, 3) : [];
  const name = recommended ? getPlanName(recommended, index) : "推荐方案";
  const headline = recommended ? getPlanHeadline(recommended, index) : "正在整理更合适的安排";

  return (
    <section className="rounded-[16px] border border-[#e5e7eb] bg-white p-4 shadow-[0_10px_26px_rgba(15,23,42,0.07)]">
      <div className="flex items-center gap-2 text-[12px] font-semibold text-[#475569]">
        <span className={cn("flex h-7 w-7 items-center justify-center rounded-full", theme.faint)}>
          <Sparkles className={cn("h-4 w-4", theme.softText)} strokeWidth={2.2} />
        </span>
        推荐结果
      </div>

      <div className="mt-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-[22px] font-bold leading-[1.18] tracking-[0] text-[#111827]">
            我更推荐 {name}
          </h1>
          <p className="mt-2 text-[14px] font-semibold leading-5 text-[#374151]">{headline}</p>
        </div>
        {recommended?.overallScoreLabel ? (
          <SmallPill className={cn("shrink-0", theme.badge)}>
            {recommended.overallScoreLabel}
          </SmallPill>
        ) : null}
      </div>

      {page.assistantMessage ? (
        <p className="mt-3 line-clamp-3 text-[13px] leading-5 text-[#64748b]">
          {page.assistantMessage}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <SmallPill className="bg-[#f1f5f9] text-[#475569]">共 {plans.length} 个方案</SmallPill>
        {tags.map((tag) => (
          <SmallPill key={tag} className="bg-[#f8fafc] text-[#64748b]">
            {tag}
          </SmallPill>
        ))}
      </div>

      {recommended ? (
        <button
          type="button"
          onClick={() => onSelectPlan(recommended.id)}
          className={cn(
            "mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-[12px] text-[14px] font-semibold transition active:scale-[0.99]",
            theme.button,
          )}
        >
          直接查看路线
          <ChevronRight className="h-4 w-4" strokeWidth={2.2} />
        </button>
      ) : null}
    </section>
  );
}

function RouteStep({
  activity,
  index,
  isLast,
  theme,
}: {
  activity: PlanActivityDto;
  index: number;
  isLast: boolean;
  theme: PlanTheme;
}): JSX.Element {
  const tags = (activity.tags ?? []).slice(0, 3);

  return (
    <div className="grid grid-cols-[30px_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className={cn("flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-bold text-white", theme.dot)}>
          {index + 1}
        </span>
        {!isLast ? <span className="mt-2 h-full min-h-5 w-px bg-[#d9dee7]" /> : null}
      </div>
      <div className={cn("min-w-0", !isLast && "pb-4")}>
        <div className="flex items-start justify-between gap-3">
          <p className="min-w-0 text-[14px] font-semibold leading-5 text-[#1f2937]">
            {activity.title}
          </p>
          {activity.durationLabel ? (
            <span className="mt-0.5 inline-flex shrink-0 items-center gap-1 rounded-full bg-[#f1f5f9] px-2 py-1 text-[10px] font-semibold text-[#64748b]">
              <Clock3 className="h-3 w-3" strokeWidth={2} />
              {activity.durationLabel}
            </span>
          ) : null}
        </div>
        {tags.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-full bg-[#f8fafc] px-2 py-1 text-[10px] font-medium text-[#64748b]"
              >
                {tag.label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function MemberFitRow({
  member,
  theme,
}: {
  member: PlanMemberRatingDto;
  theme: PlanTheme;
}): JSX.Element {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2 border-t border-[#edf0f4] py-2 first:border-t-0 first:pt-0 last:pb-0">
      <span className="flex h-7 w-7 items-center justify-center text-[18px]" aria-hidden>
        {member.emoji}
      </span>
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-[12px] font-semibold text-[#475569]">{member.label}</p>
          <p className="shrink-0 text-[11px] font-bold text-[#111827]">
            {member.score.toFixed(1)}
          </p>
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#e5e7eb]">
          <div
            className={cn("h-full rounded-full", theme.progress)}
            style={{ width: `${getScorePercent(member)}%` }}
          />
        </div>
      </div>
      <CheckCircle2 className={cn("h-4 w-4", theme.softText)} strokeWidth={2.1} />
    </div>
  );
}

function ComparisonPlanCard({
  plan,
  index,
  onSelect,
}: {
  plan: TravelPlanCardDto;
  index: number;
  onSelect: () => void;
}): JSX.Element {
  const theme = getPlanTheme(plan, index);
  const name = getPlanName(plan, index);
  const headline = getPlanHeadline(plan, index);
  const tags = getPlanTags(plan, 5);
  const activities = (plan.activities ?? []).slice(0, 4);
  const remainingActivities = Math.max(0, (plan.activities?.length ?? 0) - activities.length);
  const reason = getFirstReason(plan);

  return (
    <article
      onClick={onSelect}
      className={cn(
        "rounded-[16px] border bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.06)] transition active:scale-[0.995]",
        theme.border,
        plan.recommended && "ring-4",
        plan.recommended && theme.ring,
      )}
    >
      <header className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <SmallPill className={theme.badge}>{name}</SmallPill>
          {plan.recommended ? (
            <SmallPill className="bg-[#111827] text-white">
              <CheckCircle2 className="mr-1 h-3.5 w-3.5" strokeWidth={2.2} />
              推荐
            </SmallPill>
          ) : null}
        </div>
        {plan.overallScoreLabel ? (
          <span className="shrink-0 text-[12px] font-bold text-[#111827]">
            {plan.overallScoreLabel}
          </span>
        ) : null}
      </header>

      <h2 className="mt-3 text-[18px] font-bold leading-[1.25] tracking-[0] text-[#111827]">
        {headline}
      </h2>

      {tags.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className={cn("rounded-full px-2.5 py-1 text-[11px] font-semibold", theme.faint, theme.softText)}
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {activities.length > 0 ? (
        <section className="mt-4 border-y border-[#edf0f4] py-4">
          <div className="mb-3 flex items-center gap-2 text-[13px] font-bold text-[#111827]">
            <Route className={cn("h-4 w-4", theme.softText)} strokeWidth={2.2} />
            路线安排
          </div>
          <div>
            {activities.map((activity, activityIndex) => (
              <RouteStep
                key={activity.id}
                activity={activity}
                index={activityIndex}
                isLast={activityIndex === activities.length - 1}
                theme={theme}
              />
            ))}
          </div>
          {remainingActivities > 0 ? (
            <p className="mt-3 text-[11px] font-medium text-[#94a3b8]">
              还有 {remainingActivities} 个行程细节会在时间轴里展开
            </p>
          ) : null}
        </section>
      ) : null}

      {plan.memberRatings?.length ? (
        <section className="mt-4">
          <div className="mb-2 flex items-center gap-2 text-[13px] font-bold text-[#111827]">
            <UsersRound className={cn("h-4 w-4", theme.softText)} strokeWidth={2.2} />
            成员匹配
          </div>
          <div>
            {plan.memberRatings.map((member) => (
              <MemberFitRow key={`${plan.id}-${member.id}`} member={member} theme={theme} />
            ))}
          </div>
        </section>
      ) : null}

      {reason ? (
        <section className={cn("mt-4 rounded-[12px] px-3 py-3", theme.faint)}>
          <p className={cn("text-[12px] font-bold", theme.softText)}>
            {plan.compensationTitle || "安排理由"}
          </p>
          <p className="mt-1.5 line-clamp-3 text-[12px] leading-5 text-[#475569]">{reason}</p>
        </section>
      ) : null}

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onSelect();
        }}
        className={cn(
          "mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-[12px] text-[14px] font-semibold transition active:scale-[0.99]",
          theme.button,
        )}
      >
        选择并查看路线
        <ChevronRight className="h-4 w-4" strokeWidth={2.2} />
      </button>
    </article>
  );
}

function ComposerDock({
  input,
  onInputChange,
  onSubmit,
  submitPending,
  journeyFlow,
}: {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  submitPending: boolean;
  journeyFlow: { travelId: string; planId: string };
}): JSX.Element {
  return (
    <div className={tabScreenComposerDockMtAutoClass}>
      <div className="flex items-center gap-2">
        <div className="flex min-h-[48px] flex-1 items-center rounded-[16px] border border-[#dbe3ee] bg-white px-4 shadow-[0_6px_18px_rgba(15,23,42,0.06)] focus-within:border-[#94a3b8]">
          <input
            type="text"
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder={submitPending ? "正在修改方案…" : "告诉我想改哪里，例如更近一点、少排队..."}
            disabled={submitPending}
            onKeyDown={(event) => {
              if (event.key === "Enter") onSubmit();
            }}
            className="min-w-0 flex-1 bg-transparent py-3 text-[13px] text-[#1f2937] outline-none placeholder:text-[#94a3b8]"
          />
        </div>
        <button
          type="button"
          aria-label="发送"
          disabled={submitPending}
          onClick={onSubmit}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[16px] bg-[#111827] text-white shadow-[0_8px_18px_rgba(17,24,39,0.22)] transition active:scale-95 disabled:opacity-50"
        >
          <SendHorizontal className="h-5 w-5" strokeWidth={2.2} />
        </button>
      </div>

      <AppBottomNav active="首页" journeyFlow={journeyFlow} />
    </div>
  );
}

export const PlanCompareScreen = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as PlansLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [page, setPage] = useState<PlanComparisonPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [submitPending, setSubmitPending] = useState(false);
  const [revisionNotice, setRevisionNotice] = useState<RevisionNoticeState>(null);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === PLANS_PATH) {
      document.title = "推荐方案 · 出行助手";
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
    fetchPlanComparisonPage(travelId)
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
  }, [travelId]);

  const plans = Array.isArray(page?.plans) ? page.plans : [];
  const navPlanFallback =
    loc?.planId ??
    resolved.planId ??
    plans.find((plan) => plan.recommended)?.id ??
    plans[0]?.id ??
    "plan-a";
  const chatBackState = { travelId };
  const journeyFlow = { travelId, planId: navPlanFallback };

  function handleSelectPlan(planId: string): void {
    setCurrentTravel({ travelId, planId });
    navigate(TIMELINE_PATH, { state: { travelId, planId } });
  }

  async function handleComposerSubmit(): Promise<void> {
    const text = input.trim();
    const choice = detectPlanChoiceFromInput(text);
    if (choice) {
      const planId = resolveChoicePlanId(choice, plans);
      setInput("");
      handleSelectPlan(planId);
      return;
    }
    if (!text) {
      showToast("请先选择一个方案，或输入想调整的内容");
      return;
    }

    setSubmitPending(true);
    setLoadError(null);
    setRevisionNotice(null);
    try {
      const revised = await reviseTravelPlan(travelId, {
        message: text,
        targetPlanId: navPlanFallback,
        revisionMode: "partial",
      });
      if (revised.updatedPlanComparison) {
        setPage(revised.updatedPlanComparison);
      } else {
        setPage(await fetchPlanComparisonPage(travelId));
      }
      setRevisionNotice({ summary: revised.revisionSummary, warnings: revised.warnings });
      showToast("方案已根据你的要求更新");
      setInput("");
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "修改方案失败");
    } finally {
      setSubmitPending(false);
    }
  }

  return (
    <AppScreenShell frameClassName="bg-[#f6f7fb]">
      <AppToast message={toastMessage} />

      <div className="pointer-events-none absolute inset-x-0 top-0 h-[210px] bg-[linear-gradient(180deg,#eef5ff_0%,#f6f7fb_100%)]" />

      <Link
        to={CHAT_PATH}
        state={chatBackState}
        className={cn(
          "absolute left-[10px] z-20 flex h-11 w-11 items-center justify-center rounded-full border border-white/70 bg-white/80 text-[#111827] shadow-[0_6px_18px_rgba(15,23,42,0.08)] backdrop-blur-sm transition-colors hover:bg-white",
          embeddedBackButtonTopClass(),
        )}
        aria-label="返回对话"
      >
        <ChevronLeft className="h-6 w-6" strokeWidth={1.8} />
      </Link>

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-hidden">
        <EmbeddedStatusBarImage src={page?.statusBarImageUrl ?? FIGMA_PLANS_1119.statusBar} />

        {resolvingTravel ? (
          <LoadingState />
        ) : loadError ? (
          <ErrorState message={loadError} />
        ) : !page ? (
          <LoadingState />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col px-[14px] pb-3 pt-2">
            <div className="min-h-0 flex-1 overflow-y-auto pb-5">
              <header className="pb-3 pl-12 pr-1">
                <p className="text-[12px] font-semibold text-[#64748b]">{page.topStatusText}</p>
                <h1 className="mt-1 text-[26px] font-bold leading-[1.12] tracking-[0] text-[#111827]">
                  推荐方案
                </h1>
              </header>

              <div className="space-y-4">
                <RevisionNotice notice={revisionNotice} />
                <RecommendationPanel page={page} onSelectPlan={handleSelectPlan} />

                <section className="space-y-3" aria-label="方案列表">
                  {plans.map((plan, index) => (
                    <ComparisonPlanCard
                      key={plan.id}
                      plan={plan}
                      index={index}
                      onSelect={() => handleSelectPlan(plan.id)}
                    />
                  ))}
                </section>
              </div>
            </div>

            <ComposerDock
              input={input}
              onInputChange={setInput}
              onSubmit={() => void handleComposerSubmit()}
              submitPending={submitPending}
              journeyFlow={journeyFlow}
            />
          </div>
        )}
      </div>
    </AppScreenShell>
  );
};
