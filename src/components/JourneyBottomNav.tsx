import { AppBottomNav } from "./AppBottomNav";

type Tab = "首页" | "地图" | "行程" | "我的";

type JourneyBottomNavProps = {
  active: Tab;
  travelId?: string;
  planId: string;
};

/** 行程 Tab 流程套壳：渲染与首页同一套四项底栏几何，仅用 journey 色变体区分稿面。 */
export function JourneyBottomNav({ active, travelId, planId }: JourneyBottomNavProps) {
  return <AppBottomNav active={active} journeyFlow={{ travelId: travelId ?? "", planId }} variant="journey" />;
}
