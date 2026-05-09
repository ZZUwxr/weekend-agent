import type { HomeDashboardDto } from "../types";

export const MOCK_HOME_DASHBOARD: HomeDashboardDto = {
  greetingLines: ["HI~ ✨", "今天有什么安排？"],
  mascotImageUrl:
    "https://www.figma.com/api/mcp/asset/29105d69-755f-4827-ad91-72d6a28de6db",
  statusBarImageUrl:
    "https://www.figma.com/api/mcp/asset/4fc51a7a-65d9-47f9-8cdf-2df5d8727811",
  voiceInputIconUrl:
    "https://www.figma.com/api/mcp/asset/5e275619-9db8-4c89-9253-5c8d3440b093",
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
      subtitle: "Friendship",
      tag: "释放压力",
    },
    {
      id: "scene_family",
      variant: "family",
      title: "家庭亲子",
      subtitle: "Family",
      tag: "寓教于乐",
    },
  ],
  filterTags: ["距离最近", "价格实惠", "休闲娱乐", "环境氛围"],
  historySectionTitle: "历史安排",
  history: [
    {
      id: "hist_1",
      title: "小小探险家的下午",
      metaLine: "上周六 · 家庭亲子 · 3人 · ¥388",
    },
    {
      id: "hist_2",
      title: "四人小馆觅食记",
      metaLine: "上上六 · 朋友 · 4人 · ¥530",
    },
  ],
};
