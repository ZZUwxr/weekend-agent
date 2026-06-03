import type { LLMRuntimeConfig } from "./api/types";

const STORAGE_KEY = "weekend-agent.llm-settings.v1";

export type LocalLLMSettings = {
  provider: "mock" | "openai";
  model: string;
  baseUrl: string;
  apiKey: string;
};

export function emptyLLMSettings(): LocalLLMSettings {
  return {
    provider: "openai",
    model: "",
    baseUrl: "",
    apiKey: "",
  };
}

export function loadLocalLLMSettings(): LocalLLMSettings {
  if (typeof window === "undefined") return emptyLLMSettings();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyLLMSettings();
    const parsed = JSON.parse(raw) as Partial<LocalLLMSettings>;
    return {
      provider: parsed.provider === "mock" ? "mock" : "openai",
      model: String(parsed.model ?? ""),
      baseUrl: String(parsed.baseUrl ?? ""),
      apiKey: String(parsed.apiKey ?? ""),
    };
  } catch {
    return emptyLLMSettings();
  }
}

export function saveLocalLLMSettings(settings: LocalLLMSettings): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      provider: settings.provider === "mock" ? "mock" : "openai",
      model: settings.model.trim(),
      baseUrl: settings.baseUrl.trim(),
      apiKey: settings.apiKey.trim(),
    }),
  );
}

export function localLLMSettingsToRuntimeConfig(): LLMRuntimeConfig | null {
  const settings = loadLocalLLMSettings();
  if (settings.provider === "mock") {
    return { provider: "mock" };
  }
  const model = settings.model.trim();
  const baseUrl = settings.baseUrl.trim();
  const apiKey = settings.apiKey.trim();
  if (!model || !baseUrl || !apiKey) return null;
  return {
    provider: "openai",
    model,
    baseUrl,
    apiKey,
  };
}

export function previewLocalApiKey(apiKey: string): string | null {
  const text = apiKey.trim();
  if (!text) return null;
  if (text.length <= 8) return "已保存";
  return `${text.slice(0, 4)}...${text.slice(-4)}`;
}
