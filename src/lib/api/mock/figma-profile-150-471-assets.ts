import { FIGMA_HOME_4737 } from "./figma-home-4737-assets";

/**
 * Figma「前端 ui」· node 150:471（无行程 · 我的 · 初始态）
 * 与稿面同文件；状态栏与装饰与首页体系一致。若 150:471 在 Figma 中单拆导出，可替换下列 URL（见 MCP 导出说明）。
 */
export const FIGMA_PROFILE_150_471 = {
  statusBar: FIGMA_HOME_4737.statusBar,
  bgBlobA: FIGMA_HOME_4737.bgBlobA,
  bgBlobB: FIGMA_HOME_4737.bgBlobB,
  /** 中部「尚未开通」区插画与首页历史空态同系视觉 */
  emptyPanelBg: FIGMA_HOME_4737.historyEmptyBg,
  emptyPanelCorner: FIGMA_HOME_4737.historyEmptyCorner,
  emptyPanelFigure: FIGMA_HOME_4737.historyEmptyFigure,
  sectionChevron: FIGMA_HOME_4737.sectionChevron,
} as const;
