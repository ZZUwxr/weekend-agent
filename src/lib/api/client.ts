import { getApiBaseUrl } from "./config";

export class ApiNotImplementedError extends Error {
  constructor(method: string, path: string) {
    super(`API 尚未接入：${method} ${path}。请配置 VITE_API_BASE_URL 并实现 fetch。 `);
    this.name = "ApiNotImplementedError";
  }
}

/** 后端就绪后在此统一封装 fetch（鉴权、JSON、错误格式等） */
export async function apiRequest<T>(
  path: string,
  init?: RequestInit & { parseJson?: true },
): Promise<T> {
  const base = getApiBaseUrl();
  if (!base) {
    throw new ApiNotImplementedError(init?.method ?? "GET", path);
  }
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}
