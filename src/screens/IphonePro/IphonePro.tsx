import { ChevronLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { tabScreenComposerDockMtAutoClass } from "../../lib/tabScreenDockLayout";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { EmbeddedStatusBarImage } from "../../components/EmbeddedStatusBar";
import { AppScreenShell } from "../../components/AppScreenShell";
import { CHAT_PATH, HOME_PATH, PLANS_PATH } from "../../routes";
import {
  fetchTravelConversationPage,
} from "../../lib/api/travel.service";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { TravelConversationPageDto } from "../../lib/api/types";
import { NeedsStatusAccordionSection } from "./sections/NeedsStatusAccordionSection";
import { TravelIntentPromptSection } from "./sections/TravelIntentPromptSection";
import { FIGMA_CHAT_177 } from "../../lib/api/mock/figma-chat-177-assets";
import { embeddedBackButtonTopClass } from "../../lib/embeddedStatusBar";
import { cn } from "../../lib/utils";

const DEFAULT_USER_MESSAGE = "我和家人想在今天下午出门放松放松";

type ChatLocationState = { message?: string; travelId?: string };

function UserYellowBubble({ children, className = "" }: { children: string; className?: string }): JSX.Element {
  return (
    <div
      className={`ml-auto w-[261px] max-w-full rounded-bl-[15.417px] rounded-br-[15.417px] rounded-tl-[15.417px] bg-[#ffd100] px-[15px] py-[5px] shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)] ${className}`}
    >
      <p className="text-right [font-family:'HYQiHei-Regular',Helvetica] text-[13.604px] font-normal leading-[26.318px] text-[#343d43]">
        {children}
      </p>
    </div>
  );
}

function UserYellowBubbleWide({ children }: { children: string }): JSX.Element {
  return (
    <div className="flex w-full justify-end">
      <div className="max-w-full overflow-x-auto [-webkit-overflow-scrolling:touch] [scrollbar-width:thin] [&::-webkit-scrollbar]:h-[3px]">
        <div className="inline-flex rounded-bl-[15.417px] rounded-br-[15.417px] rounded-tl-[15.417px] bg-[#ffd100] px-[15px] py-[5px] shadow-[0px_2.675px_0.964px_rgba(0,0,0,0.05)]">
          <p className="m-0 whitespace-nowrap text-right [font-family:'HYQiHei-Regular',Helvetica] text-[13.604px] font-normal leading-[26.318px] text-[#343d43]">
            {children}
          </p>
        </div>
      </div>
    </div>
  );
}

function AiStatusStrip({
  text,
  variant,
  className = "",
  navigateTo,
  navigateState,
}: {
  text: string;
  variant: "first" | "rest";
  className?: string;
  navigateTo?: string;
  navigateState?: { travelId?: string };
}): JSX.Element {
  const iconSrc = variant === "first" ? FIGMA_CHAT_177.statusIconFirst : FIGMA_CHAT_177.statusIconRest;
  const plCls = variant === "first" ? "pl-[9px]" : "pl-[14px]";
  const shell = `flex h-[36px] w-full items-center gap-[5.76px] rounded-bl-[11.525px] rounded-br-[11.525px] rounded-tr-[11.525px] bg-white pr-[13px] shadow-[0px_2.881px_7.203px_rgba(0,0,0,0.03)] ${plCls} ${className}`;
  const body = (
    <>
      <img src={iconSrc} alt="" className="h-[10px] w-[10px] shrink-0 object-contain" />
      <p className="min-w-0 flex-1 [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[11.525px] font-normal leading-[17.288px] text-[#0f1c2d]">
        {text}
      </p>
      <img src={FIGMA_CHAT_177.statusChevron} alt="" className="h-[6px] w-[9px] shrink-0 object-contain opacity-80" />
    </>
  );
  if (navigateTo) {
    return (
      <Link
        to={navigateTo}
        state={navigateState}
        className={`${shell} cursor-pointer text-inherit no-underline outline-none transition-opacity hover:opacity-95 active:opacity-[0.92]`}
      >
        {body}
      </Link>
    );
  }
  return <div className={shell}>{body}</div>;
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

  const firstStep = bundle?.statusSteps[0];
  const restSteps = bundle?.statusSteps.slice(1) ?? [];

  const journeyFlow = { travelId, planId: "plan-a" };

  return (
    <AppScreenShell>
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <img
            src={FIGMA_CHAT_177.bgBlobA}
            alt=""
            className="absolute -left-[551px] -top-[321px] h-[795px] w-[1293px] max-w-none opacity-95"
          />
          <img
            src={FIGMA_CHAT_177.bgBlobB}
            alt=""
            className="absolute -left-[122px] top-[100px] h-[1046px] w-[1507px] max-w-none opacity-95"
          />
        </div>

        <Link
          to={HOME_PATH}
          className={cn(
            "absolute left-[10px] z-20 flex h-10 w-10 items-center justify-center rounded-full text-[#251e1e] hover:bg-black/[0.04]",
            embeddedBackButtonTopClass(),
          )}
          aria-label="返回首页"
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
        </Link>

        <div className="relative z-[1] flex min-h-0 flex-1 flex-col overflow-x-hidden">
          <EmbeddedStatusBarImage src={FIGMA_CHAT_177.statusBar} />

          <ContentFitZoom
            className="px-[29px] pb-3 pt-3 [touch-action:pan-y]"
            recalcKey={`${loadError ?? ""}:${bundle?.statusSteps?.length ?? 0}:${bundle?.followUpUserMessage ?? ""}`}
          >
            {loadError ? (
              <p className="py-12 text-center text-[13px] text-red-600">{loadError}</p>
            ) : !bundle ? (
              <p className="py-12 text-center text-[13px] text-[#6b7280]">加载中…</p>
            ) : (
              <div className="flex flex-col gap-[18px]">
                <UserYellowBubble>{userMessage}</UserYellowBubble>

                {firstStep ? (
                  <AiStatusStrip variant="first" text={firstStep.text} />
                ) : null}

                <TravelIntentPromptSection data={bundle.clarification} />

                {bundle.followUpUserMessage ? (
                  <UserYellowBubbleWide>{bundle.followUpUserMessage}</UserYellowBubbleWide>
                ) : null}

                <NeedsStatusAccordionSection data={bundle.needsSection} />

                {restSteps.map((step, idx) => {
                  const toPlans = step.id === "s4" || /两个方案/.test(step.text);
                  return (
                    <AiStatusStrip
                      key={step.id}
                      variant="rest"
                      text={step.text}
                      className={idx === restSteps.length - 1 ? "mb-1" : ""}
                      navigateTo={toPlans ? PLANS_PATH : undefined}
                      navigateState={toPlans ? { travelId } : undefined}
                    />
                  );
                })}
              </div>
            )}
          </ContentFitZoom>

          <div
            className={cn(tabScreenComposerDockMtAutoClass, "relative z-[1] bg-white px-3 pb-2")}
          >
            {/* 对话页不属于「首页」四 tab：高亮任一 tab 会使人误以为路由未跳转 */}
            <AppBottomNav active="首页" journeyFlow={journeyFlow} />
          </div>
        </div>
    </AppScreenShell>
  );
};
