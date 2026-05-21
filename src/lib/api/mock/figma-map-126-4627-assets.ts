import { FIGMA_HOME_4737 } from "./figma-home-4737-assets";

/** 第八屏地图图层（与 trip-live-map.mock / Figma 1:734 同源），空态作弱底纹 */
const FIGMA_MAP_EMPTY_BACKDROP =
  "https://www.figma.com/api/mcp/asset/f0839aab-b9ae-4b72-9fce-88fbae753e9c";

/**
 * Figma「前端 ui」· node 126:4627（无行程 · 地图 · 初始态）
 * 状态栏与装饰与首页体系统一；地图弱纹理可换稿面独立导出。
 */
export const FIGMA_MAP_126_4627 = {
  statusBar: FIGMA_HOME_4737.statusBar,
  bgBlobA: FIGMA_HOME_4737.bgBlobA,
  bgBlobB: FIGMA_HOME_4737.bgBlobB,
  mapBackdropSoft: FIGMA_MAP_EMPTY_BACKDROP,
} as const;
