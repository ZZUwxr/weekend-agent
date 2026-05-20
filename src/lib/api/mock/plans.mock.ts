import type { PlanComparisonPageDto } from "../types";
import { FIGMA_PLANS_1119 } from "./figma-plans-1119-assets";

/** 文案与评分与 Figma node 1:1119「双方案对比」一致 */
export const MOCK_PLAN_COMPARISON: Omit<PlanComparisonPageDto, "travelId"> = {
  statusBarImageUrl: FIGMA_PLANS_1119.statusBar,
  topStatusText: "正在生成Plan A 的详细时间轴＆路线…",
  voiceInputIconUrl: FIGMA_PLANS_1119.voiceChip,
  assistantMessage:
    "当前方案评分接近，更推荐平衡方案，你更想选择哪一个？",
  plans: [
    {
      id: "plan-a",
      planLabel: "Plan A· ",
      headline: "午后平衡 · 推荐",
      recommended: true,
      accent: "warm",
      overallScoreLabel: "综合3.62",
      activities: [
        {
          id: "a1",
          title: "户外亲子农场（90min）",
          durationLabel: "",
          tags: [
            { id: "a1t1", label: "体力3/5" },
            { id: "a1t2", label: "儿童友好4.5" },
          ],
        },
        {
          id: "a2",
          title: "素然花园（60min）",
          durationLabel: "",
          tags: [{ id: "a2t1", label: "放松4.5" }],
        },
        {
          id: "a3",
          title: "滨江绿道散步（30min）",
          durationLabel: "",
          tags: [{ id: "a3t1", label: "老婆缓冲" }],
        },
      ],
      memberRatings: [
        {
          id: "kid",
          label: "孩子",
          emoji: "👦",
          score: 4.41,
          starsFilled: 5,
        },
        {
          id: "wife",
          label: "老婆",
          emoji: "👩",
          score: 2.78,
          starsFilled: 3,
        },
        {
          id: "user",
          label: "用户",
          emoji: "👨",
          score: 3.88,
          starsFilled: 4,
        },
      ],
      compensationTitle: "补偿设计",
      compensationParagraphs: [
        "本方案主动为老婆在晚餐后加入江边缓冲散步，属于她的放松时间。虽然花园用餐环境更好，低卡选择更丰富。",
        "孩子放电强度略低于Plan A，但依然尽兴，整体节奏更舒适。 ",
      ],
    },
    {
      id: "plan-b",
      planLabel: "Plan B · ",
      headline: "探险总动员",
      recommended: false,
      accent: "cool",
      overallScoreLabel: "综合3.55",
      activities: [
        {
          id: "b1",
          title: "星球探险亲子乐园（90min）",
          durationLabel: "",
          tags: [
            { id: "b1t1", label: "无特殊偏好" },
            { id: "b1t2", label: "无特殊偏好" },
          ],
        },
        {
          id: "b2",
          title: "半野轻食（60min）",
          durationLabel: "",
          tags: [{ id: "b2t1", label: "无特殊偏好" }],
        },
        {
          id: "b3",
          title: "书店（30min）",
          durationLabel: "",
          tags: [],
        },
      ],
      memberRatings: [
        {
          id: "kid",
          label: "孩子",
          emoji: "👦",
          score: 4.51,
          starsFilled: 5,
        },
        {
          id: "wife",
          label: "老婆",
          emoji: "👩",
          score: 2.47,
          starsFilled: 3,
        },
        {
          id: "user",
          label: "用户",
          emoji: "👨",
          score: 3.67,
          starsFilled: 4,
        },
      ],
    },
  ],
};
