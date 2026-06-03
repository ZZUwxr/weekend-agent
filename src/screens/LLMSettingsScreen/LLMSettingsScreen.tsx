import { Bot, Check, KeyRound, Link as LinkIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppStatusStrip } from "../../components/AppUi";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { fetchLLMSettings, saveLLMSettings } from "../../lib/api";
import type { LLMSettingsDto } from "../../lib/api/types";
import { LLM_SETTINGS_PATH, PROFILE_PATH } from "../../routes";

type LocationState = { travelId?: string; planId?: string };

export const LLMSettingsScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as LocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const flow = { travelId, planId };

  const [page, setPage] = useState<LLMSettingsDto | null>(null);
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
    setLoadError(null);
    fetchLLMSettings()
      .then((data) => {
        if (!active) return;
        setPage(data);
        setProvider(data.provider === "openai" ? "openai" : "mock");
        setModel(data.model);
        setBaseUrl(data.baseUrl);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const onSave = async (): Promise<void> => {
    if (provider === "openai" && (!model.trim() || !baseUrl.trim())) {
      setSaveError("请填写模型和 URL");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await saveLLMSettings({
        provider,
        model: model.trim(),
        baseUrl: baseUrl.trim(),
        apiKey: apiKey.trim() || null,
      });
      navigate(PROFILE_PATH, { state: flow });
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <UserSettingsChrome
      travelId={travelId}
      planId={planId}
      navTitle={page?.navTitle ?? "设置"}
      backLabel={page?.backLabel ?? "返回"}
      statusBarSrc={page?.statusBarImageUrl}
      footer={
        <button
          type="button"
          onClick={() => void onSave()}
          disabled={saving}
          className="mt-2 w-full shrink-0 rounded-[14px] bg-[#ffd100] py-3.5 text-[15px] font-bold text-[#343d43] shadow-[0px_4px_16px_rgba(245,200,20,0.38)] transition active:scale-[0.99] disabled:opacity-60"
        >
          {saving ? "保存中..." : page?.saveButtonLabel ?? "保存设置"}
        </button>
      }
    >
      <div className="space-y-3 pb-2">
        {loadError ? <p className="text-center text-[13px] text-red-600">{loadError}</p> : null}
        {saveError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p> : null}

        <AppStatusStrip
          Icon={Bot}
          title={provider === "openai" ? "真实 Agent API" : "本地 Mock 模式"}
          detail={page?.apiKeyConfigured ? `API Key：${page.apiKeyPreview ?? "已配置"}` : "保存 API Key 后，首页任务会使用这组配置。"}
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
              placeholder={page?.apiKeyConfigured ? "留空表示继续使用已保存的 key" : "填写 API Key"}
              onChange={setApiKey}
              type="password"
            />
          </div>
        </div>
      </div>
    </UserSettingsChrome>
  );
};

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
