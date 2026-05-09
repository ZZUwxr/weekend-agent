import { ChevronDown, ChevronRight, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";
import { fetchHomeDashboard, startTravelSession } from "../../lib/api";
import type { HomeDashboardDto, HomeSceneCardDto } from "../../lib/api/types";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import { CHAT_PATH, ITINERARY_HUB_PATH } from "../../routes";

const DEFAULT_CHAT_MESSAGE = "我和家人想在在今天下午出门放松放松";

function titleGradientClass(): string {
  return "bg-[linear-gradient(48deg,rgba(95,115,128,1)_16%,rgba(62,82,101,1)_73%,rgba(42,114,176,1)_100%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

function SceneCard({ scene }: { scene: HomeSceneCardDto }): JSX.Element {
  if (scene.variant === "couple") {
    return (
      <div className="w-[112px] shrink-0 rotate-[-6deg] self-center">
        <Card className="overflow-hidden rounded-[15px] border border-[#8a8a89] bg-white shadow-[0px_3px_12px_#00000010]">
          <CardContent className="relative h-[132px] bg-gradient-to-br from-pink-100 via-rose-50 to-white p-3">
            <p
              className={`[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium leading-tight ${titleGradientClass()}`}
            >
              {scene.title}
            </p>
            <p className="mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] text-white drop-shadow-sm">
              {scene.subtitle}
            </p>
            <span className="absolute bottom-2 left-2 rounded-md bg-white/80 px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[6.5px] text-[#586b79]">
              {scene.tag}
            </span>
          </CardContent>
        </Card>
      </div>
    );
  }
  if (scene.variant === "friends") {
    return (
      <Card className="relative w-[172px] shrink-0 overflow-hidden rounded-[22px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
        <CardContent className="relative h-[172px] bg-gradient-to-br from-[#e3f0ff] via-white to-[#fff9e0] p-4">
          <p
            className={`[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium ${titleGradientClass()}`}
          >
            {scene.title}
          </p>
          <p className="mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[10px] text-[#88a2b4]">
            {scene.subtitle}
          </p>
          <span className="absolute bottom-3 left-3 rounded-lg border border-[#a0d5fa]/60 bg-white/90 px-2 py-1 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] text-[#4a5e70]">
            {scene.tag}
          </span>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className="w-[112px] shrink-0 rotate-[6deg] self-center">
      <Card className="overflow-hidden rounded-[15px] border border-[#f5c814] bg-white shadow-[0px_3px_15px_#d0def8]">
        <CardContent className="relative h-[132px] bg-gradient-to-br from-amber-50 via-yellow-50 to-white p-3">
          <p
            className={`[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-medium leading-tight ${titleGradientClass()}`}
          >
            {scene.title}
          </p>
          <p className="mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[9px] text-white drop-shadow-sm">
            {scene.subtitle}
          </p>
          <span className="absolute bottom-2 left-2 rounded-md bg-white/80 px-2 py-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[7px] text-[#586b79]">
            {scene.tag}
          </span>
        </CardContent>
      </Card>
    </div>
  );
}

export const HomeScreen = (): JSX.Element => {
  const [text, setText] = useState("");
  const [dashboard, setDashboard] = useState<HomeDashboardDto | null>(null);
  const [homeError, setHomeError] = useState<string | null>(null);
  const navigate = useNavigate();
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
  }, []);

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

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-white">
      <div className="relative mx-auto flex min-h-[874px] w-full max-w-[402px] flex-col">
        {dashboard ? (
          <img
            src={dashboard.statusBarImageUrl}
            alt=""
            className="h-[61px] w-full shrink-0 object-cover object-top"
            height={61}
            width={402}
          />
        ) : (
          <div className="h-[61px] w-full shrink-0 bg-white/80" />
        )}
        <div className="flex flex-1 flex-col px-8 pb-3 pt-3">
          {homeError ? (
            <p className="text-center text-[13px] text-red-600">{homeError}</p>
          ) : !dashboard ? (
            <p className="text-center text-[13px] text-[#6b7280]">加载中…</p>
          ) : (
            <>
              <header className="relative flex items-start justify-between gap-3">
                <div className="max-w-[200px] pt-1">
                  <p
                    className={`[font-family:'HYQiHei-Regular',Helvetica] text-[18px] font-normal leading-[1.35] tracking-[0] ${titleGradientClass()}`}
                  >
                    {dashboard.greetingLines[0]}
                  </p>
                  <p
                    className={`mt-1 [font-family:'HYQiHei-Regular',Helvetica] text-[18px] font-normal leading-[1.35] tracking-[0] ${titleGradientClass()}`}
                  >
                    {dashboard.greetingLines[1]}
                  </p>
                </div>
                <img
                  src={dashboard.mascotImageUrl}
                  alt=""
                  className="h-[92px] w-[76px] shrink-0 object-contain object-bottom"
                />
              </header>

              <section className="mt-6">
                <div className="mb-3 flex items-center gap-2 pr-1">
                  <div className="h-4 w-1 rounded-sm bg-gradient-to-b from-[#1a1a1a] to-[#ffd100]" />
                  <h2
                    className={`flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-normal leading-tight ${titleGradientClass()}`}
                  >
                    {dashboard.sceneSectionTitle}
                  </h2>
                  <ChevronDown className="h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
                </div>

                <div className="flex gap-3 overflow-x-auto pb-1 pt-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                  {dashboard.scenes.map((scene) => (
                    <SceneCard key={scene.id} scene={scene} />
                  ))}
                </div>
              </section>

              <section className="mt-5 flex flex-wrap gap-2">
                {dashboard.filterTags.map((label) => (
                  <Button
                    key={label}
                    type="button"
                    variant="outline"
                    className="h-auto rounded-[10px] border-[0.84px] border-[#fdffea] bg-gradient-to-b from-[#b1d4f7] to-white px-3 py-1.5 text-[10.5px] font-normal text-[#343d43] shadow-[0px_2px_2px_#00000020] [font-family:'HYQiHei-Regular',Helvetica] hover:from-[#b1d4f7] hover:to-white"
                  >
                    {label}
                  </Button>
                ))}
              </section>

              <section className="mt-6">
                <div className="mb-3 flex items-center gap-2 pr-1">
                  <div className="h-4 w-1 rounded-sm bg-gradient-to-b from-[#1a1a1a] to-[#ffd100]" />
                  <h2
                    className={`flex-1 [font-family:'HYQiHei-Regular',Helvetica] text-[16px] font-normal leading-tight ${titleGradientClass()}`}
                  >
                    {dashboard.historySectionTitle}
                  </h2>
                  <ChevronDown className="h-4 w-4 shrink-0 text-[#6b7280]" strokeWidth={2} />
                </div>
                <div className="flex flex-col gap-3">
                  {dashboard.history.map((item) => (
                    <Link
                      key={item.id}
                      to={ITINERARY_HUB_PATH}
                      state={journeyFlow}
                      className="block transition-opacity hover:opacity-95"
                    >
                      <Card className="rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_#d0def8]">
                        <CardContent className="flex items-center gap-3 px-3 py-3">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#fff6cc]">
                            <Sparkles className="h-4 w-4 text-[#f5c814]" strokeWidth={1.75} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p
                              className={`[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-medium leading-snug ${titleGradientClass()}`}
                            >
                              {item.title}
                            </p>
                            <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[10.5px] text-[#343d43]">
                              {item.metaLine}
                            </p>
                          </div>
                          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#9ca3af]" strokeWidth={1.75} />
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </section>
            </>
          )}

          <div className="mt-auto flex flex-col gap-3 pt-8">
            <div className="flex items-center gap-2">
              <div className="relative flex min-h-[46px] flex-1 items-center rounded-[30px] border-[0.5px] border-[#50a9fe] bg-white pl-2 pr-2 shadow-[0px_2px_8px_#00000008]">
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
                className="flex h-[40px] w-[40px] shrink-0 items-center justify-center rounded-full bg-[#251e1e] text-white shadow-[0px_2px_8px_#00000025] transition-opacity hover:opacity-90"
              >
                <ChevronRight className="h-5 w-5" strokeWidth={2} />
              </button>
            </div>
          </div>

          <AppBottomNav active="首页" journeyFlow={journeyFlow} />
        </div>
      </div>
    </main>
  );
};
