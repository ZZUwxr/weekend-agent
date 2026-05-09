import {
  ChevronLeft,
  CircleAlert as AlertCircle,
  ArrowLeftRight,
  ChevronRight,
  Lightbulb,
  Loader as Loader2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { Card, CardContent } from "../../components/ui/card";
import {
  CHAT_PATH,
  HOME_PATH,
  PLANS_PATH,
} from "../../routes";
import {
  fetchTravelConversationPage,
} from "../../lib/api/travel.service";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { TravelConversationPageDto, TravelStatusStepDto } from "../../lib/api/types";
import { NeedsStatusAccordionSection } from "./sections/NeedsStatusAccordionSection";
import { TravelIntentPromptSection } from "./sections/TravelIntentPromptSection";

const DEFAULT_USER_MESSAGE = "我和家人想在在今天下午出门放松放松";

const STATUS_ICONS = {
  loader: Loader2,
  alert: AlertCircle,
  arrows: ArrowLeftRight,
  lightbulb: Lightbulb,
} as const;

type ChatLocationState = { message?: string; travelId?: string };

type ProgressRow = {
  stepId: string;
  text: string;
  Icon: (typeof STATUS_ICONS)[keyof typeof STATUS_ICONS];
};

type MainFlowBlock =
  | { id: "progress"; row: ProgressRow }
  | { id: "travelPrompt" };

function stepToRow(step: TravelStatusStepDto): ProgressRow {
  return {
    stepId: step.id,
    text: step.text,
    Icon: STATUS_ICONS[step.icon],
  };
}

function buildMainFlow(bundle: TravelConversationPageDto): MainFlowBlock[] {
  const { statusSteps } = bundle;
  if (statusSteps.length === 0) {
    return [{ id: "travelPrompt" }];
  }
  return [
    { id: "progress", row: stepToRow(statusSteps[0]) },
    { id: "travelPrompt" },
    ...statusSteps.slice(1).map((s) => ({ id: "progress", row: stepToRow(s) }) as const),
  ];
}

function StatusProgressCard({ text, Icon }: Omit<ProgressRow, "stepId">): JSX.Element {
  return (
    <Card className="rounded-[0px_11.53px_11.53px_11.53px] border-0 bg-white shadow-[0px_2.88px_14.41px_#00000008]">
      <CardContent className="flex min-h-9 items-center justify-between gap-3 px-[11px] py-[9px]">
        <div className="flex min-w-0 items-center gap-[5.76px]">
          <Icon className="h-[14px] w-[14px] shrink-0 text-[#0f1c2d]" strokeWidth={1.75} />
          <p className="[font-family:'PingFang_SC-Regular',Helvetica] text-[11.5px] font-normal leading-[17.3px] tracking-[0] text-[#0f1c2d]">
            {text}
          </p>
        </div>
        <ChevronRight className="h-[12px] w-[12px] shrink-0 text-[#6b7280]" strokeWidth={1.75} />
      </CardContent>
    </Card>
  );
}

export const IphonePro = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as ChatLocationState | null;
  const userMessage = loc?.message?.trim() || DEFAULT_USER_MESSAGE;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;

  const [bundle, setBundle] = useState<TravelConversationPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === CHAT_PATH) {
      document.title = "对话 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
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

  const mainFlowBlocks = useMemo(
    () => (bundle ? buildMainFlow(bundle) : []),
    [bundle],
  );

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-white">
      <div className="relative mx-auto flex min-h-[874px] w-full max-w-[402px] flex-col px-8 pb-3 pt-[52px]">
        <header className="mb-5 flex items-center gap-1">
          <Link
            to={HOME_PATH}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[#0f1c2d] hover:bg-black/[0.04]"
            aria-label="返回首页"
          >
            <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
          </Link>
          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium text-[#333c43]">
            出行助手 · 对话
          </span>
        </header>
        <section className="flex justify-end">
          <Card className="w-[261px] rounded-[15.42px_0px_15.42px_15.42px] border-0 bg-[#ffd100] shadow-[0px_2.68px_1.93px_#0000000d]">
            <CardContent className="px-[15px] py-[5px]">
              <p className="[font-family:'HYQiHei-Regular',Helvetica] text-right text-[13.6px] font-normal leading-[26.3px] tracking-[0] text-[#333c43]">
                {userMessage}
              </p>
            </CardContent>
          </Card>
        </section>

        {loadError ? (
          <p className="mt-4 text-center text-[13px] text-red-600">{loadError}</p>
        ) : !bundle ? (
          <p className="mt-8 text-center text-[13px] text-[#6b7280]">加载中…</p>
        ) : (
          <>
            <section className="mt-4 flex flex-col gap-4">
              {mainFlowBlocks.map((block) =>
                block.id === "travelPrompt" ? (
                  <TravelIntentPromptSection
                    key="block-travel-prompt"
                    data={bundle.clarification}
                  />
                ) : (
                  <StatusProgressCard key={block.row.stepId} text={block.row.text} Icon={block.row.Icon} />
                ),
              )}
            </section>
            <section className="mt-4">
              <NeedsStatusAccordionSection data={bundle.needsSection} />
            </section>
            <div className="mt-5 flex justify-center">
              <Link
                to={PLANS_PATH}
                state={{ travelId }}
                className="rounded-full bg-[#50a9fe]/12 px-4 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium text-[#2a7bc8] transition-opacity hover:opacity-90"
              >
                查看双方案对比
              </Link>
            </div>
          </>
        )}
        <AppBottomNav active={null} journeyFlow={{ travelId, planId: "plan-a" }} />
      </div>
    </main>
  );
};
