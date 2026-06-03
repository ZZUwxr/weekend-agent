import {
  Check,
  ChevronRight,
  CircleHelp,
  ClipboardList,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppErrorState,
  AppIconButton,
  AppLoadingState,
  AppPageHeader,
  AppPill,
  AppStatusStrip,
} from "../../components/AppUi";
import {
  answerTravelClarifications,
  fetchTravelConversationPage,
} from "../../lib/api/travel.service";
import { FIGMA_CHAT_177 } from "../../lib/api/mock/figma-chat-177-assets";
import type {
  ClarificationFieldDto,
  ParticipantNeedCardDto,
  TravelConversationPageDto,
} from "../../lib/api/types";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { setCurrentTravel } from "../../lib/currentTravel";
import { CHAT_PATH, HOME_PATH, PLANS_PATH } from "../../routes";
import { cn } from "../../lib/utils";

const DEFAULT_USER_MESSAGE = "我和家人想在今天下午出门放松放松";

type ChatLocationState = { message?: string; travelId?: string };

function UserMessageCard({ message }: { message: string }): JSX.Element {
  return (
    <div className="flex justify-end">
      <div className="max-w-[86%] rounded-[16px] rounded-tr-[4px] bg-[#ffd95a] px-4 py-3 shadow-[0_8px_20px_rgba(234,179,8,0.18)]">
        <p className="text-[14px] font-semibold leading-5 text-[#3f3421]">{message}</p>
      </div>
    </div>
  );
}

function ClarificationField({
  field,
  pending,
  selectedValue,
  onSelect,
}: {
  field: ClarificationFieldDto;
  pending: boolean;
  selectedValue?: string;
  onSelect: (fieldId: string, answer: string) => void;
}): JSX.Element {
  const selectedDefault = selectedValue || field.selectedOptionIds?.[0] || "";

  return (
    <div className="border-t border-[#eef2f7] pt-4 first:border-t-0 first:pt-0">
      <p className="text-[14px] font-bold leading-5 text-[#111827]">{field.question}</p>
      {field.kind === "chips" && field.options ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {field.options.map((option) => {
            const selected = selectedDefault === option.id;
            return (
              <button
                key={option.id}
                type="button"
                disabled={pending}
                aria-pressed={selected}
                onClick={() => onSelect(field.id, option.id)}
                className={cn(
                  "min-h-11 rounded-full border px-4 text-[13px] font-semibold transition active:scale-[0.98] disabled:opacity-60",
                  selected
                    ? "border-[#2456a6] bg-[#e8f1ff] text-[#1d4ed8] shadow-[0_6px_16px_rgba(36,86,166,0.12)]"
                    : "border-[#e5e7eb] bg-white text-[#475569]",
                )}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      ) : (
        <button
          type="button"
          disabled={pending}
          onClick={() => onSelect(field.id, field.placeholder ?? "按默认继续")}
          className={cn(
            "mt-3 flex min-h-11 w-full items-center justify-between rounded-[12px] border px-3 text-left text-[13px] font-semibold transition active:scale-[0.99] disabled:opacity-60",
            selectedDefault
              ? "border-[#2456a6] bg-[#e8f1ff] text-[#1d4ed8]"
              : "border-[#e5e7eb] bg-white text-[#64748b]",
          )}
        >
          {selectedDefault || field.placeholder || "补充一下"}
          <ChevronRight className="h-4 w-4" strokeWidth={2.1} />
        </button>
      )}
    </div>
  );
}

function NeedCard({ card }: { card: ParticipantNeedCardDto }): JSX.Element {
  const bodyText = card.description
    .map((line) => line.trim())
    .filter(Boolean)
    .join("");

  return (
    <article className="min-w-[148px] rounded-[14px] border border-[#e5e7eb] bg-[#f8fafc] px-3 py-3">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-[17px] shadow-[0_4px_12px_rgba(15,23,42,0.06)]">
          {card.icon === "baby" ? "👶" : card.icon}
        </span>
        <p className="min-w-0 truncate text-[13px] font-bold text-[#111827]">{card.title}</p>
      </div>
      {bodyText ? <p className="mt-2 line-clamp-3 text-[12px] leading-5 text-[#64748b]">{bodyText}</p> : null}
    </article>
  );
}

function buildClarificationAnswers(
  fields: ClarificationFieldDto[],
  selectedByFieldId: Record<string, string>,
): Record<string, string> {
  const answers: Record<string, string> = {};
  for (const field of fields) {
    answers[field.id] =
      selectedByFieldId[field.id] ||
      field.selectedOptionIds?.[0] ||
      field.options?.[0]?.id ||
      field.placeholder ||
      "按默认继续";
  }
  return answers;
}

export const IphonePro = (): JSX.Element => {
  const navigate = useNavigate();
  const { state, pathname } = useLocation();
  const loc = state as ChatLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const resolvingTravel = resolved.loading && !loc?.travelId;

  const [bundle, setBundle] = useState<TravelConversationPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedClarifications, setSelectedClarifications] = useState<Record<string, string>>({});
  const [clarificationPending, setClarificationPending] = useState(false);
  const { toastMessage, showToast } = useAppToast();

  useEffect(() => {
    const prev = document.title;
    if (pathname === CHAT_PATH) {
      document.title = "确认偏好 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    if (!travelId) return;
    let active = true;
    setLoadError(null);
    setBundle(null);
    fetchTravelConversationPage(travelId)
      .then((data) => {
        if (active) setBundle(data);
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

  const clarificationFields = useMemo(
    () => bundle?.clarification.fields.filter((field) => field.id !== "assumptions") ?? [],
    [bundle],
  );
  const userMessage = bundle?.inputMessage?.trim() || loc?.message?.trim() || DEFAULT_USER_MESSAGE;
  const completedFields = clarificationFields.filter((field) => {
    return selectedClarifications[field.id] || field.selectedOptionIds?.length;
  }).length;
  const journeyFlow = { travelId, planId: "plan-a" };

  function selectClarification(fieldId: string, answer: string): void {
    setSelectedClarifications((prev) => ({ ...prev, [fieldId]: answer }));
  }

  async function submitClarifications(answersByField: Record<string, string>): Promise<void> {
    if (!bundle || clarificationPending) return;
    const normalizedAnswers = buildClarificationAnswers(clarificationFields, answersByField);
    const answers = clarificationFields
      .map((field) => {
        const selected = normalizedAnswers[field.id];
        const answer =
          field.options?.find((option) => option.id === selected)?.label ||
          selected ||
          field.placeholder ||
          "按默认继续";
        return { questionId: field.id, answer };
      })
      .filter((answer) => answer.questionId && answer.answer);

    setClarificationPending(true);
    setLoadError(null);
    try {
      if (travelId && answers.length > 0) {
        await answerTravelClarifications(travelId, { answers });
      }
      setCurrentTravel({ travelId, planId: "plan-a" });
      navigate(PLANS_PATH, { state: { travelId } });
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "提交澄清失败");
    } finally {
      setClarificationPending(false);
    }
  }

  function skipClarifications(): void {
    const defaults = buildClarificationAnswers(clarificationFields, {});
    setSelectedClarifications(defaults);
    showToast("已按默认偏好继续");
    void submitClarifications(defaults);
  }

  return (
    <AppScreenShell frameClassName="bg-[#f6f7fb]">
      <AppToast message={toastMessage} />
      <AppBackdrop />
      <AppIconButton
        to={HOME_PATH}
        label="返回首页"
        className="absolute left-3 top-[61px] z-20"
      />

      <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-hidden">
        <EmbeddedStatusBarImage src={FIGMA_CHAT_177.statusBar} />

        {resolvingTravel ? (
          <AppLoadingState label="正在同步当前行程..." />
        ) : loadError && !bundle ? (
          <AppErrorState message={loadError} />
        ) : !bundle ? (
          <AppLoadingState />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col px-[14px] pb-3 pt-2">
            <div className="min-h-0 flex-1 overflow-y-auto pb-5">
              <AppPageHeader
                className="pb-4 pl-12"
                eyebrow="出行助手"
                title="确认几个偏好"
                subtitle="选中后再继续，AI 会据此生成更贴近实际的方案。"
              />

              <div className="space-y-4">
                <UserMessageCard message={userMessage} />

                <AppStatusStrip
                  Icon={Sparkles}
                  title={bundle.statusSteps[0]?.text ?? "我已经理解你的安排"}
                  detail="接下来只需要确认关键偏好，避免推荐结果偏离你的真实需求。"
                />

                <AppCard>
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#e8f1ff] text-[#2456a6]">
                        <CircleHelp className="h-5 w-5" strokeWidth={2.1} />
                      </span>
                      <div className="min-w-0">
                        <h2 className="text-[17px] font-bold leading-6 text-[#111827]">
                          {bundle.clarification.title}
                        </h2>
                        <p className="mt-0.5 text-[12px] font-medium text-[#64748b]">
                          已确认 {completedFields}/{clarificationFields.length || 1}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={clarificationPending}
                      onClick={skipClarifications}
                      className="min-h-10 shrink-0 rounded-full bg-[#f1f5f9] px-3 text-[12px] font-semibold text-[#475569] disabled:opacity-60"
                    >
                      {clarificationPending ? "处理中…" : bundle.clarification.skipLabel}
                    </button>
                  </div>

                  <div className="space-y-4">
                    {clarificationFields.map((field) => (
                      <ClarificationField
                        key={field.id}
                        field={field}
                        pending={clarificationPending}
                        selectedValue={selectedClarifications[field.id]}
                        onSelect={selectClarification}
                      />
                    ))}
                  </div>

                  <AppActionButton
                    className="mt-5"
                    disabled={clarificationPending}
                    onClick={() => void submitClarifications(selectedClarifications)}
                    Icon={ChevronRight}
                  >
                    {clarificationPending ? "正在生成方案…" : "继续生成方案"}
                  </AppActionButton>
                </AppCard>

                <AppCard>
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#fff4d6] text-[#8a5a00]">
                      <ClipboardList className="h-5 w-5" strokeWidth={2.1} />
                    </span>
                    <div className="min-w-0">
                      <h2 className="text-[16px] font-bold text-[#111827]">{bundle.needsSection.headerTitle}</h2>
                      <p className="mt-0.5 text-[12px] text-[#64748b]">AI 会把这些约束带入方案评分。</p>
                    </div>
                  </div>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {bundle.needsSection.cards.map((card) => (
                      <NeedCard key={card.id} card={card} />
                    ))}
                  </div>
                </AppCard>

                {bundle.followUpUserMessage ? <UserMessageCard message={bundle.followUpUserMessage} /> : null}

                <div className="space-y-2">
                  {bundle.statusSteps.slice(1).map((step) => {
                    const toPlans = step.id === "s4" || /两个方案/.test(step.text);
                    if (toPlans) {
                      return (
                        <Link
                          key={step.id}
                          to={PLANS_PATH}
                          state={{ travelId }}
                          className="block"
                          onClick={() => setCurrentTravel({ travelId, planId: "plan-a" })}
                        >
                          <AppStatusStrip Icon={Check} title={step.text} detail="点击查看推荐方案。" />
                        </Link>
                      );
                    }
                    return <AppStatusStrip key={step.id} Icon={UserRound} title={step.text} />;
                  })}
                </div>

                {loadError ? (
                  <div className="rounded-[14px] border border-red-100 bg-white px-4 py-3 text-[12px] font-semibold leading-5 text-red-700">
                    {loadError}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="mt-auto flex min-w-0 w-full shrink-0 flex-col gap-3 pt-3">
              <div className="flex flex-wrap gap-2">
                <AppPill className="bg-white text-[#475569]">当前方案将按这些偏好生成</AppPill>
              </div>
              <AppBottomNav active="首页" journeyFlow={journeyFlow} />
            </div>
          </div>
        )}
      </div>
    </AppScreenShell>
  );
};
