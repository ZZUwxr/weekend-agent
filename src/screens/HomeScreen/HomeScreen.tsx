import { ArrowRight, CalendarDays, Check, ChevronLeft, ChevronRight, History, MapPin, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppComposer,
  AppErrorState,
  AppLoadingState,
  AppPageHeader,
  AppPill,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import { useCurrentTravel } from "../../hooks/useCurrentTravel";
import { fetchHomeDashboard } from "../../lib/api";
import type { HomeDashboardDto, HomeHistoryItemDto, HomeSceneCardDto, HomeSceneVariant } from "../../lib/api/types";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import { AI_TASK_PATH, HOME_PATH, HOME_PATH_ALT, ITINERARY_HUB_PATH } from "../../routes";

const DEFAULT_CHAT_MESSAGE = "我和家人想在今天下午出门放松放松";

const SCENE_CHAT_PROMPTS: Record<HomeSceneVariant, string> = {
  couple: "我们想安排一次情侣约会，帮我看看最近适合去哪、怎么安排",
  friends: "我想和朋友聚会放松一下，帮我推荐地点和玩法",
  family: "我们想安排家庭亲子出行，带娃一起出去玩",
  solo: "我想一个人出门转转，帮我规划一下行程",
};

const sceneTone: Record<HomeSceneVariant, { bg: string; icon: string; label: string }> = {
  couple: { bg: "bg-[#fff1f2]", icon: "text-[#be123c]", label: "约会" },
  friends: { bg: "bg-[#edf5ff]", icon: "text-[#2456a6]", label: "朋友" },
  family: { bg: "bg-[#fff7df]", icon: "text-[#8a5a00]", label: "亲子" },
  solo: { bg: "bg-[#eefcf6]", icon: "text-[#047857]", label: "独处" },
};

function SceneCard({
  scene,
  selected,
  onClick,
}: {
  scene: HomeSceneCardDto;
  selected: boolean;
  onClick: () => void;
}): JSX.Element {
  const tone = sceneTone[scene.variant];
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`flex min-h-[146px] w-full flex-col justify-between rounded-[18px] border p-4 text-left shadow-[0_8px_22px_rgba(15,23,42,0.06)] transition active:scale-[0.99] ${
        selected ? "border-[#2456a6] bg-white" : "border-[#e5e7eb] bg-white/92"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-[14px] ${tone.bg}`}>
          <Sparkles className={`h-5 w-5 ${tone.icon}`} strokeWidth={2.1} />
        </span>
        {selected ? (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#2456a6] text-white">
            <Check className="h-4 w-4" strokeWidth={2.6} />
          </span>
        ) : null}
      </div>
      <div>
        <div className="mb-2 flex flex-wrap gap-2">
          <AppPill className={selected ? "bg-[#edf5ff] text-[#2456a6]" : "bg-[#f1f5f9] text-[#64748b]"}>
            {tone.label}
          </AppPill>
          <AppPill className="bg-[#f8fafc] text-[#64748b]">{scene.tag}</AppPill>
        </div>
        <h2 className="text-[17px] font-bold leading-6 text-[#111827]">{scene.title}</h2>
        <p className="mt-1 line-clamp-2 text-[12px] font-medium leading-5 text-[#64748b]">{scene.subtitle}</p>
      </div>
    </button>
  );
}

function HistoryItem({
  item,
}: {
  item: HomeHistoryItemDto;
}): JSX.Element {
  const flow = { travelId: item.id, planId: item.planId || "plan-a" };
  return (
    <Link
      to={ITINERARY_HUB_PATH}
      state={flow}
      className="flex min-h-[72px] items-center gap-3 rounded-[16px] border border-[#e5e7eb] bg-white px-3 py-3 shadow-[0_8px_20px_rgba(15,23,42,0.05)] transition active:scale-[0.99]"
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[14px] bg-[#edf5ff] text-[#2456a6]">
        <CalendarDays className="h-5 w-5" strokeWidth={2.1} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-bold leading-5 text-[#111827]">{item.title}</p>
        <p className="mt-0.5 line-clamp-1 text-[12px] font-medium leading-5 text-[#64748b]">{item.metaLine}</p>
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-[#94a3b8]" strokeWidth={2.1} />
    </Link>
  );
}

export const HomeScreen = (): JSX.Element => {
  const [text, setText] = useState("");
  const [dashboard, setDashboard] = useState<HomeDashboardDto | null>(null);
  const [homeError, setHomeError] = useState<string | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);
  const [selectedCompanionIds, setSelectedCompanionIds] = useState<string[]>(["self"]);
  const currentTravel = useCurrentTravel();
  const hasActiveTravel = Boolean(currentTravel?.travelId);
  const navigate = useNavigate();
  const location = useLocation();
  const journeyFlow = { travelId: currentTravel?.travelId ?? "", planId: currentTravel?.planId ?? "plan-a" };
  const { toastMessage, showToast } = useAppToast();

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
    fetchHomeDashboard()
      .then((d) => {
        if (active) setDashboard(d);
      })
      .catch((e: unknown) => {
        if (active) setHomeError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, [hasActiveTravel]);

  useEffect(() => {
    setSceneIndex(0);
  }, [hasActiveTravel]);

  useEffect(() => {
    const sceneCount = dashboard?.scenes.length ?? 0;
    if (sceneCount <= 0) return;
    setSceneIndex((index) => Math.max(0, Math.min(sceneCount - 1, index)));
  }, [dashboard?.scenes.length]);

  useEffect(() => {
    const sceneCount = dashboard?.scenes.length ?? 0;
    const isHomeRoute = location.pathname === HOME_PATH || location.pathname === HOME_PATH_ALT;
    if (!isHomeRoute || sceneCount < 2) return;
    const onKey = (event: KeyboardEvent): void => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const el = event.target as HTMLElement | null;
      if (el?.tagName === "INPUT" || el?.tagName === "TEXTAREA" || el?.isContentEditable) return;
      event.preventDefault();
      setSceneIndex((index) => (index + (event.key === "ArrowLeft" ? -1 : 1) + sceneCount) % sceneCount);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dashboard?.scenes.length, location.pathname]);

  const selectedScene = dashboard?.scenes[sceneIndex];
  const companionOptions = dashboard?.companionOptions ?? [];

  const goToTask = (message: string): void => {
    const companionIds = selectedCompanionIds.filter((id) => id !== "self");
    navigate(AI_TASK_PATH, { state: { message, companionIds } });
  };

  const buildMessage = (base: string): string => {
    const suffix = selectedFilter ? `，优先考虑${selectedFilter}` : "";
    return `${base}${suffix}`;
  };

  const goFromComposer = (): void => {
    goToTask(buildMessage(text.trim() || DEFAULT_CHAT_MESSAGE));
  };

  const goFromScene = (scene: HomeSceneCardDto): void => {
    goToTask(buildMessage(SCENE_CHAT_PROMPTS[scene.variant]));
  };

  useEffect(() => {
    if (!dashboard?.companionOptions.length) return;
    const defaults = dashboard.companionOptions
      .filter((option) => option.selectedByDefault)
      .map((option) => option.id);
    setSelectedCompanionIds(defaults.length ? defaults : ["self"]);
  }, [dashboard?.companionOptions]);

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      {dashboard ? (
        <EmbeddedStatusBarImage src={dashboard.statusBarImageUrl} className="relative z-20" height={61} width={402} />
      ) : (
        <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />
      )}

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow="Weekend Agent"
          title={dashboard?.greetingLines.join(" ") ?? "今天有什么安排？"}
          subtitle="选择一个场景，或直接说出你的想法。我会先展示实时规划进度，再给出可修改的方案。"
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          {homeError ? (
            <AppErrorState message={homeError} />
          ) : !dashboard ? (
            <AppLoadingState label="正在加载首页..." />
          ) : (
            <div className="space-y-3">
              <AppCard className="overflow-hidden p-0">
                <div className="bg-[#111827] px-4 py-5 text-white">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-semibold leading-5 text-white/72">当前推荐场景</p>
                      <h2 className="mt-1 text-[24px] font-bold leading-8">{selectedScene?.title ?? "自由规划"}</h2>
                      <p className="mt-2 line-clamp-2 text-[13px] font-medium leading-5 text-white/72">
                        {selectedScene?.subtitle ?? "说出你想去哪里、和谁一起、玩多久。"}
                      </p>
                    </div>
                    {dashboard.mascotImageUrl ? (
                      <img src={dashboard.mascotImageUrl} alt="" className="h-[92px] w-[78px] shrink-0 object-contain" />
                    ) : null}
                  </div>
                  <AppActionButton
                    tone="gold"
                    Icon={ArrowRight}
                    onClick={() => selectedScene ? goFromScene(selectedScene) : goFromComposer()}
                    className="mt-4"
                  >
                    用这个场景推荐
                  </AppActionButton>
                </div>
              </AppCard>

              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h2 className="text-[17px] font-bold text-[#111827]">{dashboard.sceneSectionTitle}</h2>
                  {dashboard.scenes.length > 1 ? (
                    <div className="flex gap-1">
                      <button
                        type="button"
                        aria-label="上一个场景"
                        onClick={() => setSceneIndex((index) => (index - 1 + dashboard.scenes.length) % dashboard.scenes.length)}
                        className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[#334155] shadow-[0_6px_16px_rgba(15,23,42,0.06)]"
                      >
                        <ChevronLeft className="h-5 w-5" strokeWidth={2.1} />
                      </button>
                      <button
                        type="button"
                        aria-label="下一个场景"
                        onClick={() => setSceneIndex((index) => (index + 1) % dashboard.scenes.length)}
                        className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[#334155] shadow-[0_6px_16px_rgba(15,23,42,0.06)]"
                      >
                        <ChevronRight className="h-5 w-5" strokeWidth={2.1} />
                      </button>
                    </div>
                  ) : null}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {dashboard.scenes.map((scene, index) => (
                    <SceneCard
                      key={scene.id}
                      scene={scene}
                      selected={index === sceneIndex}
                      onClick={() => {
                        setSceneIndex(index);
                        showToast(`已选择${scene.title}`);
                      }}
                    />
                  ))}
                </div>
              </div>

              <AppCard>
                <h2 className="text-[17px] font-bold text-[#111827]">筛选优先级</h2>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {dashboard.filterTags.map((label) => {
                    const selected = selectedFilter === label;
                    return (
                      <button
                        key={label}
                        type="button"
                        onClick={() => {
                          setSelectedFilter((prev) => (prev === label ? null : label));
                          showToast(selected ? "已取消筛选" : `已优先考虑${label}`);
                        }}
                        aria-pressed={selected}
                        className={`flex min-h-11 items-center justify-center rounded-[12px] border px-3 text-[13px] font-bold transition active:scale-[0.98] ${
                          selected
                            ? "border-[#2456a6] bg-[#edf5ff] text-[#2456a6]"
                            : "border-[#e5e7eb] bg-[#f8fafc] text-[#475569]"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </AppCard>

              {companionOptions.length ? (
                <AppCard>
                  <h2 className="text-[17px] font-bold text-[#111827]">{dashboard.companionSectionTitle}</h2>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {companionOptions.map((option) => {
                      const selected = selectedCompanionIds.includes(option.id);
                      return (
                        <button
                          key={option.id}
                          type="button"
                          onClick={() => {
                            setSelectedCompanionIds((prev) => {
                              if (option.id === "self") return ["self"];
                              const withoutSelf = prev.filter((id) => id !== "self");
                              if (withoutSelf.includes(option.id)) {
                                const next = withoutSelf.filter((id) => id !== option.id);
                                return next.length ? next : ["self"];
                              }
                              return [...withoutSelf, option.id];
                            });
                            showToast(selected ? "已取消同行人" : `已选择${option.label}`);
                          }}
                          aria-pressed={selected}
                          className={`min-h-[76px] rounded-[14px] border px-3 py-2 text-left transition active:scale-[0.99] ${
                            selected ? "border-[#2456a6] bg-[#edf5ff]" : "border-[#e5e7eb] bg-[#f8fafc]"
                          }`}
                        >
                          <span className="flex items-center gap-2">
                            <span className="text-[20px]">{option.avatarEmoji}</span>
                            <span className="min-w-0">
                              <span className="block text-[13px] font-bold text-[#111827]">{option.label}</span>
                              <span className="block text-[11px] font-semibold text-[#64748b]">{option.roleLabel}</span>
                            </span>
                          </span>
                          <span className="mt-1 line-clamp-1 block text-[11px] font-medium leading-4 text-[#64748b]">
                            {option.summary}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </AppCard>
              ) : null}

              <div>
                <div className="mb-2 flex items-center gap-2">
                  <History className="h-4 w-4 text-[#2456a6]" strokeWidth={2.1} />
                  <h2 className="text-[17px] font-bold text-[#111827]">{dashboard.historySectionTitle}</h2>
                </div>
                {dashboard.history.length > 0 ? (
                  <div className="space-y-2">
                    {dashboard.history.map((item) => (
                      <HistoryItem key={item.id} item={item} />
                    ))}
                  </div>
                ) : (
                  <AppStatusStrip
                    Icon={MapPin}
                    title="还没有历史安排"
                    detail="创建第一条行程后，历史记录会在这里出现。"
                  />
                )}
              </div>
            </div>
          )}
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppComposer
            value={text}
            onChange={setText}
            onSubmit={goFromComposer}
            placeholder="例如：今天下午和家人轻松玩一下..."
          />
          <AppBottomNav active="首页" journeyFlow={journeyFlow} />
        </div>
      </div>
    </AppScreenShell>
  );
};
