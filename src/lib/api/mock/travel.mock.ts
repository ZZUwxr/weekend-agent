import type { ClarificationCardDto, TravelConversationPageDto } from "../types";

export const MOCK_TRAVEL_ID = "mock_travel_001";

export const MOCK_CLARIFICATION: ClarificationCardDto = {
  title: "想确认一下...",
  skipLabel: "直接开始",
  fields: [
    {
      id: "child_age",
      kind: "chips",
      question: "孩子多大？",
      options: [
        { id: "age_3_5", label: "3-5岁" },
        { id: "age_6_8", label: "6-8岁" },
        { id: "age_9p", label: "9岁＋" },
      ],
    },
    {
      id: "diet",
      kind: "chips",
      question: "爱人的饮食偏好？",
      options: [
        { id: "diet_lowcal", label: "正在减肥/低卡" },
        { id: "diet_veg", label: "素食" },
        { id: "diet_spicy", label: "喜辣" },
        { id: "diet_any", label: "无特殊偏好" },
      ],
    },
    {
      id: "extra",
      kind: "supplementary",
      question: "还有需要补充的吗？",
      placeholder: "补充一下...",
    },
  ],
};

export const MOCK_CONVERSATION_PAGE: TravelConversationPageDto = {
  travelId: MOCK_TRAVEL_ID,
  statusSteps: [
    { id: "s1", text: "正在理解你的出行意图…", icon: "loader" },
    { id: "s2", text: "检测到你们的需求有冲突…", icon: "alert" },
    { id: "s3", text: "正在协调你们的矛盾…", icon: "arrows" },
    { id: "s4", text: "有两个方案推荐给你…", icon: "lightbulb" },
  ],
  clarification: MOCK_CLARIFICATION,
  needsSection: {
    headerTitle: "正在分析每个人的需求…",
    cards: [
      {
        id: "n1",
        title: "5岁孩子",
        icon: "baby",
        description: ["需要儿童友好设施，指定清淡面", "食"],
      },
      {
        id: "n2",
        title: "老婆",
        icon: "👩",
        description: ["减脂期，低卡健康餐，偏好参与", "感强活动"],
      },
      {
        id: "n3",
        title: "老婆",
        icon: "👩",
        description: ["减脂期，低卡健康餐，偏好参与", "感强活动"],
      },
    ],
  },
};
