import type { ImgHTMLAttributes } from "react";
import { EMBEDDED_STATUS_BAR_H, shouldDrawEmbeddedStatusBarImage } from "../lib/embeddedStatusBar";
import { cn } from "../lib/utils";

const slotHClass = "h-[61px] w-full shrink-0";

type ImageProps = ImgHTMLAttributes<HTMLImageElement> & { src: string };

/**
 * 顶栏：Web / 非 Android 原生 显示稿图状态栏；
 * Android 原生仅保留与稿图同高的**空白占位**（不画上移），把可视区留给系统时间/电量。
 */
export function EmbeddedStatusBarImage({ src, className, ...rest }: ImageProps) {
  if (shouldDrawEmbeddedStatusBarImage()) {
    return (
      <img
        src={src}
        alt=""
        className={cn(slotHClass, "object-cover object-top", className)}
        {...rest}
      />
    );
  }

  return (
    <div
      aria-hidden
      style={{ minHeight: EMBEDDED_STATUS_BAR_H }}
      className={cn(slotHClass, "bg-transparent", className)}
    />
  );
}

type PlaceholderProps = { className?: string };

/** 加载中：Web 等为浅底条；Android 仅占位不铺灰底，避免像「又画了一条栏」 */
export function EmbeddedStatusBarPlaceholder({ className }: PlaceholderProps) {
  if (shouldDrawEmbeddedStatusBarImage()) {
    return <div className={cn(slotHClass, className)} aria-hidden />;
  }
  return (
    <div
      aria-hidden
      style={{ minHeight: EMBEDDED_STATUS_BAR_H }}
      className={cn(slotHClass, "bg-transparent")}
    />
  );
}
