import { Capacitor } from "@capacitor/core";

/**
 * Figma 稿里的「假状态栏」高度（时间/电量条），与历史布局一致。
 */
export const EMBEDDED_STATUS_BAR_H = 61;

/**
 * 是否在 WebView 内绘制 Figma 状态栏**图片**（时间/电量示意图）。
 * Android（真机/浏览器/WebView）一律不画稿图：由系统状态栏显示，避免叠两层。
 * 仍保留 {@link EMBEDDED_STATUS_BAR_H} 占位，下方内容不上移。
 *
 * 说明：仅依赖 Capacitor 在少数构建里可能判不准；用 UA 兜底。
 */
export function shouldDrawEmbeddedStatusBarImage(): boolean {
  try {
    if (typeof navigator !== "undefined" && /Android/i.test(navigator.userAgent)) {
      return false;
    }
    if (!Capacitor.isNativePlatform()) return true;
    return Capacitor.getPlatform() !== "android";
  } catch {
    if (typeof navigator !== "undefined" && /Android/i.test(navigator.userAgent)) {
      return false;
    }
    return true;
  }
}

export function embeddedBackButtonTopClass(): string {
  return "top-[61px]";
}

/** 时间轴页方案 pill（在顶区下方） */
export function embeddedPlanPillTopClass(): string {
  return "top-[110px]";
}

/** 时间轴 AI 条：稿图顶区下方留白 */
export function embeddedTimelineAiStripMarginTopClass(): string {
  return "mt-[93px]";
}