import { getApiBaseUrl } from "./config";
import { getDeviceUserId } from "./device-user";

export class ApiNotImplementedError extends Error {
  constructor(method: string, path: string) {
    super(`API 未配置：${method} ${path}。请配置 VITE_API_BASE_URL 并启动后端服务。`);
    this.name = "ApiNotImplementedError";
  }
}

export class ApiRequestError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details;
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
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-Device-User-Id": getDeviceUserId(),
        ...init?.headers,
      },
    });
  } catch (error) {
    throw normalizeNetworkError(error);
  }
  if (!res.ok) {
    throw await parseApiError(res);
  }
  return (await res.json()) as T;
}

export function normalizeNetworkError(error: unknown): ApiRequestError {
  if (error instanceof ApiRequestError) {
    return error;
  }
  return new ApiRequestError(
    0,
    "network_error",
    "网络连接失败，请稍后重试。",
    { originalMessage: error instanceof Error ? error.message : String(error) },
  );
}

export async function parseApiError(res: Response): Promise<ApiRequestError> {
  const text = await res.text();
  try {
    const payload = JSON.parse(text) as {
      code?: string;
      message?: string;
      detail?: string;
      details?: unknown;
    };
    return new ApiRequestError(
      res.status,
      payload.code || `http_${res.status}`,
      payload.message || payload.detail || res.statusText,
      payload.details,
    );
  } catch {
    return new ApiRequestError(
      res.status,
      `http_${res.status}`,
      text || res.statusText,
    );
  }
}
