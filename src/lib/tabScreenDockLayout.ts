/**
 * 底部「语音/入口条 + 四项 Tab 导航」的统一布局类。
 * 各页拼装方式不一致时，`mt-auto` / 重复的 `padding-top` 会导致底栏在首页与地图间上下漂移，
 * 故由页面用同一常量包裹整块区域。
 */

/** Tab 四页主内容与底栏共用水平基准（与首页 `px-[14px]` 对齐；勿再混用 `px-4`） */
export const tabScreenPrimaryColumnPaddingXClass = "px-[14px]";

export const tabScreenComposerDockClass =
  "flex min-w-0 w-full shrink-0 flex-col gap-3 pt-3";

/** 与 {@link tabScreenComposerDockClass} 相同语义，在时间轴等有内层分包层时用 `mt-auto` 整块贴底。 */
export const tabScreenComposerDockMtAutoClass =
  "mt-auto flex min-w-0 w-full shrink-0 flex-col gap-3 pt-3";
