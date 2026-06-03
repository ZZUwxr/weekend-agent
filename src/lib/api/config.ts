import { Capacitor } from "@capacitor/core";

/**
 * 后端 base URL。在 .env 中配置：VITE_API_BASE_URL=https://api.example.com
 * 不配置或为空时，service 会抛出明确的 API 配置错误。
 *
 * Android 模拟器里的 localhost 指向模拟器自身，不能访问电脑后端。
 * 因此 Capacitor Android 运行时会把 localhost/127.0.0.1 映射为 10.0.2.2。
 * 真机调试可额外配置 VITE_API_ANDROID_BASE_URL=http://电脑局域网IP:8000/api/v1/mobile。
 */
export function getApiBaseUrl(): string {
  const base = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL as string | undefined);
  if (!base) return "";

  if (Capacitor.getPlatform() !== "android") {
    return base;
  }

  const androidOverride = normalizeBaseUrl(
    import.meta.env.VITE_API_ANDROID_BASE_URL as string | undefined,
  );
  if (androidOverride) {
    return androidOverride;
  }

  return base
    .replace("://localhost:", "://10.0.2.2:")
    .replace("://127.0.0.1:", "://10.0.2.2:");
}

function normalizeBaseUrl(url: string | undefined): string {
  return url?.trim().replace(/\/$/, "") ?? "";
}
