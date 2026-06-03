import { Bot, Check, KeyRound, Link as LinkIcon } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { AppStatusStrip } from "../../components/AppUi";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { fetchLLMSettings } from "../../lib/api";
import type { LLMSettingsDto } from "../../lib/api/types";
import {
  loadLocalLLMSettings,
  previewLocalApiKey,
  saveLocalLLMSettings,
} from "../../lib/llmSettings";
import { LLM_SETTINGS_PATH } from "../../routes";

type LocationState = { travelId?: string; planId?: string };

export const LLMSettingsScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as LocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;

  const [page, setPage] = useState<LLMSettingsDto | null>(null);
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [apiKeyPreview, setApiKeyPreview] = useState<string | null>(null);
  const didLoadRef = useRef(false);
  const lastSavedSignatureRef = useRef("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === LLM_SETTINGS_PATH) {
      document.title = "设置 · LLM 配置";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    const local = loadLocalLLMSettings();
    setProvider(local.provider);
    setModel(local.model);
    setBaseUrl(local.baseUrl);
    setApiKey(local.apiKey);
    setApiKeyConfigured(Boolean(local.apiKey.trim()));
    setApiKeyPreview(previewLocalApiKey(local.apiKey));
    lastSavedSignatureRef.current = buildSaveSignature(
      local.provider,
      local.model,
      local.baseUrl,
      local.apiKey,
    );
    didLoadRef.current = true;
    setLoadError(null);
    fetchLLMSettings()
      .then((data) => {
        if (!active) return;
        setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const canAutoSave = useMemo(() => {
    if (provider === "mock") return true;
    return Boolean(model.trim() && baseUrl.trim() && apiKey.trim());
  }, [apiKey, baseUrl, model, provider]);

  useEffect(() => {
    if (!didLoadRef.current || !canAutoSave) return;

    const signature = buildSaveSignature(provider, model, baseUrl, apiKey);
    if (signature === lastSavedSignatureRef.current) return;

    const timer = window.setTimeout(() => {
      setSaving(true);
      setSaveError(null);
      try {
        saveLocalLLMSettings({
          provider: provider === "mock" ? "mock" : "openai",
          model,
          baseUrl,
          apiKey,
        });
        lastSavedSignatureRef.current = signature;
        setSavedAt(new Date().toISOString());
        setApiKeyConfigured(Boolean(apiKey.trim()));
        setApiKeyPreview(previewLocalApiKey(apiKey));
      } catch (e: unknown) {
        setSaveError(e instanceof Error ? e.message : "保存失败");
      } finally {
        setSaving(false);
      }
    }, 350);

    return () => window.clearTimeout(timer);
  }, [apiKey, baseUrl, canAutoSave, model, provider]);

  const statusDetail = (() => {
    if (loadError) return "设置页样式加载失败，但本机配置仍可编辑保存。";
    if (!canAutoSave) return "请填写模型、URL 和 API Key，填完整后会自动保存到本机。";
    if (saving) return "正在自动保存到本机...";
    if (saveError) return saveError;
    if (savedAt) return "已自动保存到本机。";
    if (apiKeyConfigured) return `API Key：${apiKeyPreview ?? "已保存"}`;
    return "填写完整后会自动保存到本机，任务请求时临时发送给后端使用。";
  })();

  const savePill = (() => {
    if (saving) return "保存中";
    if (!canAutoSave) return "待填写";
    if (saveError) return "保存失败";
    return "本机自动保存";
  })();

  const savePillClass = (() => {
    if (saveError) return "bg-red-50 text-red-700";
    if (!canAutoSave) return "bg-[#f8fafc] text-[#64748b]";
    return "bg-[#edf5ff] text-[#2456a6]";
  })();

  const onApiKeyChange = (value: string): void => {
    setApiKey(value);
    setApiKeyConfigured(Boolean(value.trim()));
    setApiKeyPreview(previewLocalApiKey(value));
  };

  return (
    <UserSettingsChrome
      travelId={travelId}
      planId={planId}
      navTitle={page?.navTitle ?? "设置"}
      backLabel={page?.backLabel ?? "返回"}
      statusBarSrc={page?.statusBarImageUrl}
      footer={
        <div className={`mt-2 w-full shrink-0 rounded-[14px] px-4 py-3 text-center text-[13px] font-bold ${savePillClass}`}>
          {savePill}
        </div>
      }
    >
      <div className="space-y-3 pb-2">
        {saveError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p> : null}

        <AppStatusStrip
          Icon={Bot}
          title={provider === "openai" ? "真实 Agent API" : "Mock 模式"}
          detail={statusDetail}
        />

        <div className={userSettingsCardClass}>
          <div className="space-y-3 p-3">
            <div className="flex items-center gap-2">
              <UserSettingsIconWrap>
                <Bot className="h-4 w-4" strokeWidth={1.9} />
              </UserSettingsIconWrap>
              <span className="text-[15px] font-bold text-[#111827]">模型来源</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "openai", label: "真实 API" },
                { id: "mock", label: "Mock" },
              ].map((option) => {
                const selected = provider === option.id;
                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setProvider(option.id)}
                    className={`flex min-h-11 items-center justify-center gap-2 rounded-[12px] border px-3 text-[13px] font-bold ${
                      selected ? "border-[#2456a6] bg-[#edf5ff] text-[#2456a6]" : "border-[#e5e7eb] bg-white text-[#475569]"
                    }`}
                  >
                    {selected ? <Check className="h-4 w-4" strokeWidth={2.4} /> : null}
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className={userSettingsCardClass}>
          <div className="space-y-3 p-3">
            <SettingsInput
              icon={<Bot className="h-4 w-4" strokeWidth={1.9} />}
              label="模型"
              value={model}
              placeholder="mimo-v2.5-pro"
              onChange={setModel}
            />
            <SettingsInput
              icon={<LinkIcon className="h-4 w-4" strokeWidth={1.9} />}
              label="URL"
              value={baseUrl}
              placeholder="https://token-plan-cn.xiaomimimo.com/v1"
              onChange={setBaseUrl}
            />
            <SettingsInput
              icon={<KeyRound className="h-4 w-4" strokeWidth={1.9} />}
              label="API Key"
              value={apiKey}
              placeholder={apiKeyConfigured ? "已保存，输入新 key 会覆盖" : "填写 API Key"}
              onChange={onApiKeyChange}
              type="password"
            />
          </div>
        </div>
      </div>
    </UserSettingsChrome>
  );
};

function buildSaveSignature(
  provider: string,
  model: string,
  baseUrl: string,
  apiKey: string,
): string {
  return JSON.stringify({
    provider,
    model: model.trim(),
    baseUrl: baseUrl.trim(),
    apiKey: apiKey.trim(),
  });
}

function SettingsInput({
  icon,
  label,
  value,
  placeholder,
  onChange,
  type = "text",
}: {
  icon: JSX.Element;
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  type?: string;
}): JSX.Element {
  return (
    <label className="block">
      <span className="mb-1 flex items-center gap-2 text-[12px] font-bold text-[#64748b]">
        <UserSettingsIconWrap>{icon}</UserSettingsIconWrap>
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-12 w-full rounded-[12px] border border-[#e5e7eb] bg-white px-3 text-[14px] font-semibold text-[#111827] outline-none focus:border-[#2456a6]"
        placeholder={placeholder}
      />
    </label>
  );
}
