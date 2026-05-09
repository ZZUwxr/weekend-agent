/**
 * 后端 base URL。在 .env 中配置：VITE_API_BASE_URL=https://api.example.com
 * 不配置或为空时，各 service 仅走 mock，不发起网络请求。
 */
export function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";
}
