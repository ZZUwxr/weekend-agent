import type { HomeDashboardDto } from "../types";
import { FIGMA_HOME_4737 } from "./figma-home-4737-assets";

/** 与 Figma node 127:4737（首页 · 初始态）对齐 · history 空 */
export const MOCK_HOME_DASHBOARD: HomeDashboardDto = {
  greetingLines: ["HI~", "今天有什么安排？"],
  mascotImageUrl: FIGMA_HOME_4737.mascot,
  statusBarImageUrl: FIGMA_HOME_4737.statusBar,
  voiceInputIconUrl: FIGMA_HOME_4737.voiceInput,
  sceneSectionTitle: "场景快选",
  scenes: [
    {
      id: "scene_couple",
      variant: "couple",
      title: "情侣约会",
      subtitle: "COUPLE",
      tag: "浪漫氛围",
    },
    {
      id: "scene_friends",
      variant: "friends",
      title: "朋友聚会",
      subtitle: "FRIENDSHIP",
      tag: "释放压力",
    },
    {
      id: "scene_family",
      variant: "family",
      title: "家庭亲子",
      subtitle: "FAMILY",
      tag: "寓教于乐",
    },
    {
      id: "scene_solo",
      variant: "solo",
      title: "个人出行",
      subtitle: "SOLO",
      tag: "自由随心",
    },
  ],
  filterTags: ["距离最近", "价格实惠", "休闲娱乐", "环境氛围"],
  historySectionTitle: "历史安排",
  history: [],
};

/**
 * Figma node 1:211 · 解锁态首页：与 127:4737 其余区块一致，仅「历史安排」多一条示例。
 */
export const MOCK_HOME_DASHBOARD_UNLOCKED: HomeDashboardDto = {
  ...MOCK_HOME_DASHBOARD,
  history: [
    {
      id: "hist-afternoon-balance-trio",
      title: "午后平衡三人行",
      metaLine: "星巴克臻选 · 滨江步道 · 轻松走走",
    },
  ],
};
