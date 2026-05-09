import type { PlanComparisonPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_PLAN_COMPARISON: Omit<PlanComparisonPageDto, "travelId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  topStatusText: "准备为老婆和孩子安排行程……",
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
  assistantMessage: "好的，我基于你老婆、女儿的需求，结合你的体能偏好，帮你规划了行程方案。考虑到下午还有老婆的任务，和小朋友的体力，我给你了两个方案～",
  plans: [
    {
      id: "plan-a",
      planLabel: "Plan A",
      headline: "午后平衡 · 推荐",
      recommended: true,
      overallScoreLabel: "综合 3.62",
      activities: [
        {
          id: "a1",
          title: "北京野生动物园",
          durationLabel: "预计 2.5 h",
          tags: [
            { id: "a1t1", label: "体力 3.0/5" },
            { id: "a1t2", label: "儿童友好 4.5" },
          ],
        },
        {
          id: "a2",
          title: "午餐 · 野生动物园餐厅",
          durationLabel: "预计 1h",
          tags: [{ id: "a2t1", label: "老婆喜欢" }],
        },
        {
          id: "a3",
          title: "下午咖啡馆等孩子午睡",
          durationLabel: "预计 1.5h",
          tags: [
            { id: "a3t1", label: "放松 4.5" },
            { id: "a3t2", label: "老婆缓冲" },
          ],
        },
      ],
      memberRatings: [
        {
          id: "kid",
          label: "孩子",
          emoji: "👧",
          score: 4.5,
          starsFilled: 5,
        },
        {
          id: "wife",
          label: "老婆",
          emoji: "👩‍🦰",
          score: 4.2,
          starsFilled: 5,
        },
        {
          id: "user",
          label: "你",
          emoji: "👨🏻",
          score: 4,
          starsFilled: 4,
        },
      ],
      compensationTitle: "补偿设计（情绪/成本）",
      compensationParagraphs: [
        "动物园门票略贵一些，但孩子体验更好，老婆拍照也开心。",
        "体力稍紧，但你有午后咖啡缓冲。",
        "如果太累，你随时可以取消咖啡馆时段。",
      ],
    },
    {
      id: "plan-b",
      planLabel: "Plan B",
      headline: "午后节奏轻 · 缓冲优先",
      recommended: false,
      overallScoreLabel: "综合 3.55",
      activities: [
        {
          id: "b1",
          title: "城市动物园",
          durationLabel: "预计 2 h",
          tags: [
            { id: "b1t1", label: "体力 2.5/5" },
            { id: "b1t2", label: "老婆喜欢" },
          ],
        },
        {
          id: "b2",
          title: "公园野餐",
          durationLabel: "预计 1.5h",
          tags: [{ id: "b2t1", label: "孩子喜欢" }],
        },
      ],
      memberRatings: [
        {
          id: "kid",
          label: "孩子",
          emoji: "👧",
          score: 4.2,
          starsFilled: 5,
        },
        {
          id: "wife",
          label: "老婆",
          emoji: "👩‍🦰",
          score: 4.6,
          starsFilled: 5,
        },
        {
          id: "user",
          label: "你",
          emoji: "👨🏻",
          score: 4.1,
          starsFilled: 4,
        },
      ],
    },
  ],
};
