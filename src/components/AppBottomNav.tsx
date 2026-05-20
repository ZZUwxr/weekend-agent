import { CalendarDays, CircleUser, Compass, House } from "lucide-react";
import { Link } from "react-router-dom";
import {
  HOME_PATH,
  ITINERARY_HUB_PATH,
  PROFILE_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../routes";
import { MOCK_TRAVEL_ID } from "../lib/api/mock/travel.mock";
import { Button } from "./ui/button";

type ItemLabel = "首页" | "地图" | "行程" | "我的";

type Item = { label: ItemLabel; Icon: typeof House; to: string };

const items: Item[] = [
  { label: "首页", Icon: House, to: HOME_PATH },
  { label: "地图", Icon: Compass, to: TRIP_LIVE_MAP_PATH },
  { label: "行程", Icon: CalendarDays, to: ITINERARY_HUB_PATH },
  { label: "我的", Icon: CircleUser, to: PROFILE_PATH },
];

export type AppJourneyFlowState = { travelId: string; planId: string };

type AppBottomNavProps = {
  /** 高亮底栏项；`null` 表示四项均为弱态（少用；对话等与首页同构时一般用「首页」）。 */
  active: ItemLabel | null;
  /**
   * 与 `JourneyBottomNav` 一致。未传时使用默认 mock 行程，便于从首页直达地图、行程、我的。
   */
  journeyFlow?: AppJourneyFlowState;
};

export function AppBottomNav({ active, journeyFlow }: AppBottomNavProps): JSX.Element {
  const flow = journeyFlow ?? { travelId: MOCK_TRAVEL_ID, planId: "plan-a" };

  return (
    <div className="mt-auto pt-8">
      <nav aria-label="底部导航" className="grid grid-cols-4 items-end">
        {items.map((item) => {
          const isActive = active != null && item.label === active;
          const inner = (
            <>
              <item.Icon
                className={`shrink-0 ${isActive ? "text-black" : "text-[#9ca3af]"}`}
                style={{ width: 20, height: 20 }}
                strokeWidth={isActive ? 2.35 : 1.75}
              />
              <span
                className={`[font-family:'Pacifico',Helvetica] text-[6px] leading-[16.5px] tracking-[0] ${
                  isActive ? "font-semibold text-black" : "font-normal text-[#9ca3af]"
                }`}
              >
                {item.label}
              </span>
            </>
          );
          return (
            <Button
              key={item.label}
              asChild
              type="button"
              variant="ghost"
              className="h-auto flex-col gap-1 rounded-none px-0 py-0 hover:bg-transparent"
            >
              <Link to={item.to} state={flow} className="flex flex-col items-center gap-1">
                {inner}
              </Link>
            </Button>
          );
        })}
      </nav>
      <div className="mt-3 flex justify-center">
        <div className="h-[5px] w-[115px] rounded-[30px] bg-[#251d1d]" />
      </div>
    </div>
  );
}
