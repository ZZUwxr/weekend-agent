import { CalendarDays, CircleUser, Compass, House } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import {
  HOME_PATH,
  ITINERARY_HUB_PATH,
  PROFILE_PATH,
  TRIP_LIVE_MAP_PATH,
} from "../routes";

type Tab = "首页" | "地图" | "行程" | "我的";

/** 与 AppBottomNav 一致：第一项为首页 `/`，便于从行程/我的与从地图回主流程时行为统一 */
const items: { label: Tab; Icon: typeof House; to: string; withFlow: boolean }[] = [
  { label: "首页", Icon: House, to: HOME_PATH, withFlow: true },
  { label: "地图", Icon: Compass, to: TRIP_LIVE_MAP_PATH, withFlow: true },
  { label: "行程", Icon: CalendarDays, to: ITINERARY_HUB_PATH, withFlow: true },
  { label: "我的", Icon: CircleUser, to: PROFILE_PATH, withFlow: true },
];

type JourneyBottomNavProps = {
  active: Tab;
  travelId: string;
  planId: string;
};

export function JourneyBottomNav({ active, travelId, planId }: JourneyBottomNavProps): JSX.Element {
  const flow = { travelId, planId };
  return (
    <div className="mt-auto pt-6">
      <nav aria-label="底部导航" className="grid grid-cols-4 items-end">
        {items.map((item) => {
          const isActive = item.label === active;
          const inner = (
            <>
              <item.Icon
                className={`shrink-0 ${isActive ? "text-[#2563eb]" : "text-[#9ca3af]"}`}
                style={{ width: 20, height: 20 }}
                strokeWidth={1.75}
              />
              <span
                className={`[font-family:'Pacifico',Helvetica] text-[6px] font-normal leading-[16.5px] tracking-[0] ${
                  isActive ? "text-[#2563eb]" : "text-[#9ca3af]"
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
              <Link
                to={item.to}
                state={item.withFlow ? flow : undefined}
                className="flex flex-col items-center gap-1"
              >
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
