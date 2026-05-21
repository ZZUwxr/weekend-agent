import { FIGMA_HOME_4737 } from "./figma-home-4737-assets";

/**
 * Figma「前端 ui」· node 148:254（行程 · 无行程 · 初始态）
 * 与首页 127:4737 共用状态栏、语音图标与背景装饰，保持跨屏一致。
 */
export const FIGMA_ITINERARY_HUB_148_254 = {
  statusBar: FIGMA_HOME_4737.statusBar,
  voiceInput: FIGMA_HOME_4737.voiceInput,
  bgBlobA: FIGMA_HOME_4737.bgBlobA,
  bgBlobB: FIGMA_HOME_4737.bgBlobB,
} as const;
