import { ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { useTripContentUnlocked } from "../../hooks/useTripContentUnlocked";
import { fetchHomeDashboard, startTravelSession } from "../../lib/api";
import type { HomeDashboardDto, HomeSceneCardDto, HomeSceneVariant } from "../../lib/api/types";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { CHAT_PATH, HOME_PATH, HOME_PATH_ALT, ITINERARY_HUB_PATH } from "../../routes";
import { FIGMA_HOME_4737 } from "../../lib/api/mock/figma-home-4737-assets";

const DEFAULT_CHAT_MESSAGE = "我和家人想在今天下午出门放松放松";

/** Figma node 127:4737 · 分区标题渐变 */
function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

/** Figma node 127:4737 · HI 区渐变字 */
function greetingGradientClass(): string {
  return "bg-[linear-gradient(58.9deg,rgb(0,0,0)_16%,rgb(62,82,101)_73%,rgb(42,114,176)_96%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function SectionHeading({
  title,
  chevronSrc,
}: {
  title: string;
  chevronSrc?: string;
}): JSX.Element {
  return (
    <div className="mb-3 flex items-center gap-2 pr-1">
      <div className="h-4 w-[5px] shrink-0 rounded-[5px] bg-gradient-to-b from-[#1a1a1a] from-[70%] to-[#ffd927]" />
      <h2
        className={`flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-normal leading-tight tracking-[0.02em] ${titleGradientClass()}`}
      >
        {title}
      </h2>
      {chevronSrc ? (
        <img src={chevronSrc} alt="" className="h-[6px] w-2 shrink-0 object-contain opacity-70" />
      ) : (
        <ChevronDown className="h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
      )}
    </div>
  );
}

type SceneDeckSlot = "left" | "center" | "right";

/** 三卡叠放占位：略大于卡片，避免并排时被裁切（Figma 127:4737 · 直立卡片无 rotation） */
const SCENE_SHELL: Record<SceneDeckSlot, string> = {
  left: "relative z-[1] flex h-[178px] w-[152px] shrink-0 items-end justify-center pb-1 pr-px -mr-[64px]",
  center: "relative z-[3] flex h-[178px] w-[172px] shrink-0 items-end justify-center pb-1",
  right: "relative z-[2] flex h-[178px] w-[152px] shrink-0 items-end justify-center pb-1 pl-px -ml-[64px]",
};

const sceneCarouselBtnCls =
  "rounded-lg border-0 bg-transparent p-0 outline-none hover:opacity-95 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[#50a9fe] focus-visible:ring-offset-2";

const SCENE_STYLES: Record<
  HomeSceneVariant,
  { card: string; gradient: string; subtitleCls: string; badge: string }
> = {
  couple: {
    card: "rounded-[22px] border-[0.76px] border-[#beb8b7] bg-white shadow-[0px_4px_20px_rgba(0,0,0,0.07)]",
    gradient: "from-pink-50 via-rose-50/98 to-white",
    subtitleCls: "text-[#94a3b8]",
    badge:
      "rounded-[10px] border border-rose-200/70 bg-white/95 px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] font-medium text-[#861043] shadow-sm",
  },
  friends: {
    card: "rounded-[22px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]",
    gradient: "from-[#e8f4ff] via-white to-[#fff9e6]",
    subtitleCls: "text-[#88a2b4]",
    badge:
      "rounded-[10px] border border-[#a0d5fa]/60 bg-white/95 px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] font-medium text-[#4a5e70] shadow-sm",
  },
  family: {
    card: "rounded-[22px] border-[0.77px] border-[#eab308] bg-white shadow-[0px_4px_20px_rgba(251,191,36,0.22)]",
    gradient: "from-amber-50 via-yellow-50/95 to-white",
    subtitleCls: "text-[#a88a06]",
    badge:
      "rounded-[10px] border border-[#fcd34d]/70 bg-white/95 px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] font-medium text-[#713f12] shadow-sm",
  },
  solo: {
    card: "rounded-[22px] border border-[#2dd4bf]/75 bg-white shadow-[0px_4px_20px_rgba(45,212,191,0.22)]",
    gradient: "from-teal-50 via-emerald-50/92 to-white",
    subtitleCls: "text-[#5b8780]",
    badge:
      "rounded-[10px] border border-teal-200/80 bg-white/95 px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] font-medium text-[#115e59] shadow-sm",
  },
};

/** 场景快选：四品类统一直立排版（对齐 187:219 / 127:4737） */
function SceneFaceCard({
  scene,
  size,
}: {
  scene: HomeSceneCardDto;
  size: "side" | "center";
}): JSX.Element {
  const skin = SCENE_STYLES[scene.variant];
  const box = size === "center" ? "h-[172px] w-[172px]" : "h-[156px] w-[156px]";
  const pt = size === "center" ? "pt-6" : "pt-5";
  const px = size === "center" ? "px-4" : "px-3.5";
  const titleSz = size === "center" ? "text-[15px]" : "text-[13px]";
  const subtitleSz = size === "center" ? "text-[10px]" : "text-[9px]";

  return (
    <div className={`relative ${box} overflow-hidden ${skin.card}`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${skin.gradient}`} />
      <div className={`relative z-[1] ${pt} ${px} pb-4`}>
        <p
          className={`[font-family:'HYQiHei-Regular',Helvetica] font-medium leading-snug ${titleSz} ${titleGradientClass()}`}
        >
          {scene.title}
        </p>
        <p
          className={`mt-1 [font-family:'HYQiHei-Regular',Helvetica] leading-relaxed ${subtitleSz} ${skin.subtitleCls}`}
        >
          {scene.subtitle}
        </p>
      </div>
      <span className={`absolute bottom-3 left-3 z-[1] ${skin.badge}`}>{scene.tag}</span>
    </div>
  );
}

/** 外侧箭头：与卡片区垂直大致对齐 */
const sceneNavArrowCls =
  "relative z-[5] flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[#cfe8fb] bg-white/95 text-[#3b6f9a] shadow-[0px_2px_10px_rgba(80,169,254,0.2)] outline-none transition hover:bg-[#f0f7ff] active:scale-95 focus-visible:ring-2 focus-visible:ring-[#50a9fe]";

const SCENE_CHAT_PROMPTS: Record<HomeSceneVariant, string> = {
  couple: "我们想安排一次情侣约会，帮我看看最近适合去哪、怎么安排",
  friends: "我想和朋友聚会放松一下，帮我推荐地点和玩法",
  family: "我们想安排家庭亲子出行，带娃一起出去玩",
  solo: "我想一个人出门转转，帮我规划一下行程",
};

function FilterChip({ label, emphasis }: { label: string; emphasis: "first" | "mid" | "last" }): JSX.Element {
  const borderCls =
    emphasis === "first"
      ? "border-[0.84px] border-white"
      : "border-[0.84px] border-[#fdffea]";
  const gradientCls =
    emphasis === "first"
      ? "bg-gradient-to-b from-[#b1d4f7] to-white"
      : emphasis === "mid"
        ? "bg-gradient-to-b from-[#d1e8ff] to-white"
        : "bg-gradient-to-b from-[#b1d4f7] to-[#fffce6]";
  return (
    <button
      type="button"
      className={`flex h-[30px] w-full min-w-0 items-center justify-center rounded-[10px] px-1.5 shadow-[0px_2px_2px_rgba(0,0,0,0.25)] ${borderCls} ${gradientCls} transition-opacity hover:opacity-95`}
    >
      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[10.5px] font-semibold leading-none text-[#343d43]">
        {label}
      </span>
    </button>
  );
}

const FILTER_EMPHASIS: Array<"first" | "mid" | "last"> = ["first", "mid", "last", "last"];

/** Figma 127:4737 · 历史安排空状态 ~326×131 */
function HistoryEmptyCard(): JSX.Element {
  return (
    <div className="relative mx-auto box-border h-[131px] w-full max-w-[326px] overflow-hidden rounded-[15px] border border-[#50a9fe] bg-[linear-gradient(135deg,#f8fbff_0%,#ffffff_55%,#fffdf6_100%)] shadow-[0px_4px_20px_#d0def8]">
      <img
        src={FIGMA_HOME_4737.historyEmptyBg}
        alt=""
        className="pointer-events-none absolute inset-y-0 right-0 h-full w-[52%] max-w-[170px] object-cover object-right opacity-90"
      />
      <img
        src={FIGMA_HOME_4737.historyEmptyCorner}
        alt=""
        className="pointer-events-none absolute bottom-0 right-[6%] h-[68px] w-[68px] object-contain opacity-95"
      />
      <img
        src={FIGMA_HOME_4737.historyEmptyFigure}
        alt=""
        className="pointer-events-none absolute bottom-1 right-[8%] h-[82px] w-[82px] max-h-[calc(100%-8px)] max-w-[42%] object-contain object-bottom"
      />
      <div className="relative z-[1] flex h-full min-w-0 flex-col justify-center px-3.5 py-3 pr-[46%]">
        <p className={`[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold leading-snug ${titleGradientClass()}`}>
          你还没有历史安排
        </p>
        <p className="mt-1 max-w-[168px] [font-family:'HYQiHei-Regular',Helvetica] text-[10px] leading-relaxed text-[#586b79]">
          创建第一条行程后，它会出现在这里，方便你随时回看。
        </p>
      </div>
    </div>
  );
}

export const HomeScreen = (): JSX.Element => {
  const [text, setText] = useState("");
  const [dashboard, setDashboard] = useState<HomeDashboardDto | null>(null);
  const [homeError, setHomeError] = useState<string | null>(null);
  /** 场景快选三连卡：中部为当前选项，左右点击查看上一 / 下一品类（四轮播） */
  const [sceneCarouselIndex, setSceneCarouselIndex] = useState(0);
  const unlocked = useTripContentUnlocked();
  const navigate = useNavigate();
  const location = useLocation();
  const journeyFlow = { travelId: MOCK_TRAVEL_ID, planId: "plan-a" };

  useEffect(() => {
    const prev = document.title;
    document.title = "首页 · 今天有什么安排";
    return () => {
      document.title = prev;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setHomeError(null);
    setDashboard(null);
    fetchHomeDashboard({ tripContentUnlocked: unlocked })
      .then((d) => {
        if (active) setDashboard(d);
      })
      .catch((e: unknown) => {
        if (active) setHomeError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, [unlocked]);

  useEffect(() => {
    setSceneCarouselIndex(0);
  }, [unlocked]);

  const sceneCount = dashboard?.scenes.length ?? 0;
  const isHomeRoute =
    location.pathname === HOME_PATH || location.pathname === HOME_PATH_ALT;

  const bumpSceneCarousel = useCallback((delta: 1 | -1) => {
    if (sceneCount < 2) return;
    setSceneCarouselIndex((x) => (x + delta + sceneCount) % sceneCount);
  }, [sceneCount]);

  /** 首页下 ← / → 轮换场景（输入框内不拦截） */
  useEffect(() => {
    if (!isHomeRoute || sceneCount < 2) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      const el = e.target as HTMLElement | null;
      if (
        el &&
        (el.tagName === "INPUT" ||
          el.tagName === "TEXTAREA" ||
          el.tagName === "SELECT" ||
          el.isContentEditable)
      ) {
        return;
      }
      e.preventDefault();
      bumpSceneCarousel(e.key === "ArrowLeft" ? -1 : 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [bumpSceneCarousel, isHomeRoute, sceneCount]);

  const goToChat = () => {
    const message = text.trim() || DEFAULT_CHAT_MESSAGE;
    void (async () => {
      try {
        const { travelId } = await startTravelSession({ message });
        navigate(CHAT_PATH, { state: { message, travelId } });
      } catch {
        navigate(CHAT_PATH, { state: { message } });
      }
    })();
  };

  /** 正中场景卡：按所选品类带好默认 prompt 进入对话 */
  const goToChatFromScene = (scene: HomeSceneCardDto) => {
    const message = SCENE_CHAT_PROMPTS[scene.variant];
    void (async () => {
      try {
        const { travelId } = await startTravelSession({ message });
        navigate(CHAT_PATH, { state: { message, travelId } });
      } catch {
        navigate(CHAT_PATH, { state: { message } });
      }
    })();
  };

  return (
    <AppScreenShell>
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <img
            src={FIGMA_HOME_4737.bgBlobA}
            alt=""
            className="absolute -left-[320px] -top-[348px] h-[795px] w-[1293px] max-w-none opacity-[0.95]"
          />
          <img
            src={FIGMA_HOME_4737.bgBlobB}
            alt=""
            className="absolute -left-[430px] -top-[94px] h-[795px] w-[1293px] max-w-none opacity-[0.85]"
          />
          <img
            src={FIGMA_HOME_4737.bgBlobC}
            alt=""
            className="absolute -left-[200px] top-[280px] h-[1046px] w-[1507px] max-w-none opacity-90"
          />
          <img
            src={FIGMA_HOME_4737.bgBlobD}
            alt=""
            className="absolute -left-[80px] top-[80px] h-[1046px] w-[1507px] max-w-none opacity-[0.88]"
          />
        </div>

        <div className="relative z-[1] flex min-h-0 w-full flex-1 flex-col overflow-x-hidden">
        {dashboard ? (
          <EmbeddedStatusBarImage src={dashboard.statusBarImageUrl} height={61} width={402} />
        ) : (
          <EmbeddedStatusBarPlaceholder className="bg-white/90" />
        )}

        <div className="flex min-h-0 min-w-0 flex-1 flex-col px-[14px] pb-2 pt-2">
          <ContentFitZoom
            className="[touch-action:pan-y]"
            recalcKey={`${homeError ?? ""}:${dashboard?.history.length ?? 0}:${sceneCarouselIndex}`}
          >
          {homeError ? (
            <p className="text-center text-[13px] text-red-600">{homeError}</p>
          ) : !dashboard ? (
            <p className="py-16 text-center text-[13px] text-[#64748b]">加载中…</p>
          ) : (
            <>
              <div className="mx-auto box-border w-full max-w-[373px] overflow-hidden rounded-[15px] bg-[rgba(255,255,255,0.72)] px-3 pb-4 pt-3 shadow-[0px_8px_40px_rgba(80,169,254,0.08)] backdrop-blur-[12px] ring-1 ring-white/80">
                <header className="relative flex min-h-[112px] items-start justify-between gap-2 overflow-x-hidden overflow-y-visible pl-1 pr-0">
                  <div className="min-w-0 max-w-[min(100%,252px)] shrink pt-2">
                    <div className="flex flex-wrap items-center gap-x-1 gap-y-0.5">
                      <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[18px] font-normal leading-[24px] tracking-normal text-black">
                        {dashboard.greetingLines[0]}
                      </p>
                      <img
                        src={FIGMA_HOME_4737.greetingSparkle}
                        alt=""
                        className="h-[23px] w-[23px] shrink-0 object-contain"
                        height={23}
                        width={23}
                      />
                    </div>
                    <p
                      className={`mt-1.5 block pb-px [font-family:'HYQiHei-Regular',Helvetica] text-[18px] font-normal leading-[24px] tracking-normal ${greetingGradientClass()}`}
                    >
                      {dashboard.greetingLines[1]}
                    </p>
                  </div>
                  <img
                    src={dashboard.mascotImageUrl}
                    alt=""
                    className="pointer-events-none h-[102px] w-[84px] shrink-0 object-contain object-bottom"
                    height={102}
                    width={84}
                  />
                </header>

                <section className="mt-4">
                  <SectionHeading title={dashboard.sceneSectionTitle} chevronSrc={FIGMA_HOME_4737.sectionChevron} />

                  {/* Figma · 187:219 / 127:4737：直立三卡 + 箭头 / 键盘 ← → 轮换 */}
                  <div className="relative mx-auto mt-1 flex w-full max-w-[380px] items-center justify-center gap-1 px-0 sm:gap-2">
                    <button
                      type="button"
                      aria-label="上一场景"
                      className={`${sceneNavArrowCls} pointer-events-auto touch-manipulation disabled:pointer-events-none disabled:opacity-40`}
                      disabled={dashboard.scenes.length < 2}
                      onClick={() => bumpSceneCarousel(-1)}
                    >
                      <ChevronLeft className="h-5 w-5" strokeWidth={2} />
                    </button>
                    <div className="relative h-[188px] min-w-0 flex-1 max-w-[349px] overflow-hidden [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                      <div className="absolute inset-x-0 bottom-0 flex items-end justify-center">
                        {dashboard.scenes.length > 0
                          ? (() => {
                              const scenes = dashboard.scenes;
                              const n = scenes.length;
                              const ci = sceneCarouselIndex % n;
                              const leftScene = scenes[(ci - 1 + n) % n];
                              const centerScene = scenes[ci];
                              const rightScene = scenes[(ci + 1) % n];
                              return (
                                <>
                                  <button
                                    type="button"
                                    className={`${SCENE_SHELL.left} ${sceneCarouselBtnCls} cursor-pointer touch-manipulation`}
                                    aria-label={`上一场景：${leftScene.title}`}
                                    onClick={() => setSceneCarouselIndex((x) => (x - 1 + n) % n)}
                                  >
                                    <SceneFaceCard scene={leftScene} size="side" />
                                  </button>
                                  <button
                                    type="button"
                                    className={`${SCENE_SHELL.center} ${sceneCarouselBtnCls} cursor-pointer touch-manipulation active:scale-[0.99]`}
                                    aria-label={`${centerScene.title}：进入对话`}
                                    onClick={() => goToChatFromScene(centerScene)}
                                  >
                                    <SceneFaceCard scene={centerScene} size="center" />
                                  </button>
                                  <button
                                    type="button"
                                    className={`${SCENE_SHELL.right} ${sceneCarouselBtnCls} cursor-pointer touch-manipulation`}
                                    aria-label={`下一场景：${rightScene.title}`}
                                    onClick={() => setSceneCarouselIndex((x) => (x + 1) % n)}
                                  >
                                    <SceneFaceCard scene={rightScene} size="side" />
                                  </button>
                                </>
                              );
                            })()
                          : null}
                      </div>
                    </div>
                    <button
                      type="button"
                      aria-label="下一场景"
                      className={`${sceneNavArrowCls} pointer-events-auto touch-manipulation disabled:pointer-events-none disabled:opacity-40`}
                      disabled={dashboard.scenes.length < 2}
                      onClick={() => bumpSceneCarousel(1)}
                    >
                      <ChevronRight className="h-5 w-5" strokeWidth={2} />
                    </button>
                  </div>
                </section>

                <section className="mt-5 grid w-full grid-cols-4 gap-x-2 gap-y-2 px-0">
                  {dashboard.filterTags.map((label, i) => (
                    <div key={label} className="flex min-w-0 justify-center">
                      <FilterChip label={label} emphasis={FILTER_EMPHASIS[i] ?? "last"} />
                    </div>
                  ))}
                </section>

                <section className="mt-6">
                  <SectionHeading title={dashboard.historySectionTitle} chevronSrc={FIGMA_HOME_4737.sectionChevron} />

                  <div className="flex flex-col gap-3">
                    {dashboard.history.length === 0 ? (
                      <HistoryEmptyCard />
                    ) : (
                      dashboard.history.map((item) => (
                        <Link
                          key={item.id}
                          to={ITINERARY_HUB_PATH}
                          state={journeyFlow}
                          className="block transition-opacity hover:opacity-95 active:scale-[0.99]"
                        >
                          <div className="overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                            <div className="relative flex items-center gap-3 px-3 py-3">
                              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
                                <SparklesGlyph />
                              </div>
                              <div className="min-w-0 flex-1">
                                <p
                                  className={`[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold leading-snug ${titleGradientClass()}`}
                                >
                                  {item.title}
                                </p>
                                <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10.5px] text-[#343d43]">
                                  {item.metaLine}
                                </p>
                              </div>
                              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={1.75} />
                            </div>
                          </div>
                        </Link>
                      ))
                    )}
                  </div>
                </section>
              </div>
            </>
          )}
          </ContentFitZoom>

          <div className="flex shrink-0 flex-col gap-3 pt-6">
            <div className="flex min-w-0 items-center gap-2 px-0">
              <div className="relative flex min-h-[46px] min-w-0 flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_rgba(0,0,0,0.06)]">
                {dashboard ? (
                  <img
                    src={dashboard.voiceInputIconUrl}
                    alt=""
                    className="h-7 w-[34px] shrink-0 object-contain"
                    height={28}
                    width={34}
                  />
                ) : (
                  <div className="h-7 w-[34px] shrink-0" />
                )}
                <input
                  type="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") goToChat();
                  }}
                  placeholder="说说你的想法，例如今天想去哪、跟谁一起…"
                  className="min-w-0 flex-1 bg-transparent py-2 pl-2 pr-2 [font-family:'HYQiHei-Regular',Helvetica] text-[13px] text-[#333c43] outline-none placeholder:text-[#333c4380]"
                />
              </div>
              <button
                type="button"
                onClick={goToChat}
                aria-label="发送并进入对话"
                className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_rgba(0,0,0,0.18)] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} />
              </button>
            </div>
          </div>

          <AppBottomNav active="首页" journeyFlow={journeyFlow} />

          <div className="mx-auto mt-3 h-[5px] w-[115px] shrink-0 rounded-[30px] bg-[#251d1d]" aria-hidden />
        </div>
      </div>
    </AppScreenShell>
  );
};

/** 历史卡片左侧星芒 · 近似稿中小图标 */
function SparklesGlyph(): JSX.Element {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden className="text-[#f5c814]">
      <path
        d="M12 2l1.2 4.2L17 8l-3.8 1.8L12 14l-1.2-4.2L7 8l3.8-1.8L12 2z"
        fill="currentColor"
        opacity="0.95"
      />
      <path d="M18 14l.8 2.8 2.8.8-2.8.8-.8 2.8-.8-2.8-2.8-.8 2.8-.8.8-2.8z" fill="currentColor" opacity="0.75" />
    </svg>
  );
}
