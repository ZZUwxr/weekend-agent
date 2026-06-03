import { Check, Plus, Trash2, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { AppStatusStrip } from "../../components/AppUi";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import {
  createCompanionProfile,
  deleteCompanionProfile,
  fetchCompanionProfiles,
  updateCompanionProfile,
} from "../../lib/api";
import type {
  CompanionProfileDto,
  CompanionProfileListDto,
  SaveCompanionProfileBody,
} from "../../lib/api/types";
import { COMPANION_PROFILES_PATH } from "../../routes";

type LocationState = { travelId?: string; planId?: string };

const roleOptions = [
  { id: "spouse", label: "伴侣" },
  { id: "child", label: "孩子" },
  { id: "elder", label: "长辈" },
  { id: "friend", label: "朋友" },
  { id: "user", label: "本人" },
];

type FormState = {
  companionId?: string;
  displayName: string;
  roleType: string;
  age: string;
  hardConstraints: string;
  softPreferences: string;
  riskPoints: string;
};

const emptyForm: FormState = {
  displayName: "",
  roleType: "friend",
  age: "",
  hardConstraints: "",
  softPreferences: "",
  riskPoints: "",
};

function formFromCompanion(companion: CompanionProfileDto): FormState {
  return {
    companionId: companion.companionId,
    displayName: companion.displayName,
    roleType: companion.roleType || "friend",
    age: companion.age == null ? "" : String(companion.age),
    hardConstraints: companion.hardConstraints.join("\n"),
    softPreferences: companion.softPreferences.join("\n"),
    riskPoints: companion.riskPoints.join("\n"),
  };
}

function splitList(value: string): string[] {
  return value
    .split(/[\n,，;；]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 12);
}

function toBody(form: FormState): SaveCompanionProfileBody {
  return {
    companionId: form.companionId,
    displayName: form.displayName.trim(),
    roleType: form.roleType,
    age: form.age.trim() ? Number(form.age) : null,
    hardConstraints: splitList(form.hardConstraints),
    softPreferences: splitList(form.softPreferences),
    riskPoints: splitList(form.riskPoints),
  };
}

export const CompanionProfilesScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as LocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;

  const [page, setPage] = useState<CompanionProfileListDto | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const editingExisting = Boolean(form.companionId);
  const selectedCompanion = useMemo(
    () => page?.companions.find((item) => item.companionId === form.companionId),
    [form.companionId, page?.companions],
  );

  const reload = async (): Promise<void> => {
    const data = await fetchCompanionProfiles();
    setPage(data);
    if (!form.companionId && data.companions[0]) {
      setForm(formFromCompanion(data.companions[0]));
    }
  };

  useEffect(() => {
    const prev = document.title;
    if (pathname === COMPANION_PROFILES_PATH) {
      document.title = "同行人出行档案 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    fetchCompanionProfiles()
      .then((data) => {
        if (!active) return;
        setPage(data);
        setForm(data.companions[0] ? formFromCompanion(data.companions[0]) : emptyForm);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const onSave = async (): Promise<void> => {
    const body = toBody(form);
    if (!body.displayName) {
      setSaveError("请填写人物名称");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const saved = editingExisting && form.companionId
        ? await updateCompanionProfile(form.companionId, body)
        : await createCompanionProfile(body);
      await reload();
      setForm(formFromCompanion(saved.companion));
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (): Promise<void> => {
    if (!form.companionId) return;
    setSaving(true);
    setSaveError(null);
    try {
      await deleteCompanionProfile(form.companionId);
      const data = await fetchCompanionProfiles();
      setPage(data);
      setForm(data.companions[0] ? formFromCompanion(data.companions[0]) : emptyForm);
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "删除失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <UserSettingsChrome
      travelId={travelId}
      planId={planId}
      navTitle={page?.navTitle ?? "同行人出行档案"}
      navSubtitle={page?.subtitle ?? "人物记忆会参与推荐。"}
      statusBarSrc={page?.statusBarImageUrl}
      footer={
        <button
          type="button"
          onClick={() => void onSave()}
          disabled={saving}
          className="mt-2 w-full shrink-0 rounded-[14px] bg-[#ffd100] py-3.5 text-[15px] font-bold text-[#343d43] shadow-[0px_4px_16px_rgba(245,200,20,0.38)] transition active:scale-[0.99] disabled:opacity-60"
        >
          {saving ? "保存中..." : editingExisting ? "保存人物档案" : "添加人物"}
        </button>
      }
    >
      <div className="space-y-3 pb-2">
        {loadError ? <p className="text-center text-[13px] text-red-600">{loadError}</p> : null}
        {saveError ? <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p> : null}

        <div className={userSettingsCardClass}>
          <div className="flex items-center justify-between border-b border-[#e5e7eb] px-3 py-3">
            <div className="flex items-center gap-2">
              <UserSettingsIconWrap>
                <UserRound className="h-4 w-4" strokeWidth={1.9} />
              </UserSettingsIconWrap>
              <span className="text-[15px] font-bold text-[#111827]">人物列表</span>
            </div>
            <button
              type="button"
              onClick={() => setForm(emptyForm)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f1f5f9] text-[#2456a6]"
              aria-label="添加人物"
            >
              <Plus className="h-5 w-5" strokeWidth={2.1} />
            </button>
          </div>
          <div className="space-y-2 p-3">
            {page?.companions.map((companion) => {
              const active = companion.companionId === form.companionId;
              return (
                <button
                  key={companion.companionId}
                  type="button"
                  onClick={() => setForm(formFromCompanion(companion))}
                  className={`flex w-full items-center gap-3 rounded-[14px] border px-3 py-3 text-left transition active:scale-[0.99] ${
                    active ? "border-[#2456a6] bg-[#edf5ff]" : "border-[#e5e7eb] bg-[#f8fafc]"
                  }`}
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white text-[22px] shadow-[0_4px_12px_rgba(15,23,42,0.05)]">
                    {companion.avatarEmoji}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[14px] font-bold text-[#111827]">{companion.displayName}</span>
                    <span className="mt-0.5 line-clamp-1 block text-[12px] font-medium text-[#64748b]">
                      {companion.roleLabel} · {companion.summary}
                    </span>
                  </span>
                  {active ? <Check className="h-4 w-4 shrink-0 text-[#2456a6]" strokeWidth={2.4} /> : null}
                </button>
              );
            })}
          </div>
        </div>

        <div className={userSettingsCardClass}>
          <div className="space-y-3 p-3">
            <AppStatusStrip
              Icon={UserRound}
              title={editingExisting ? `正在编辑：${selectedCompanion?.displayName ?? form.displayName}` : "添加新人物"}
              detail="约束会被严格考虑，偏好会作为推荐加分，风险点会尽量避开。"
            />

            <label className="block">
              <span className="text-[12px] font-bold text-[#64748b]">名称</span>
              <input
                value={form.displayName}
                onChange={(e) => setForm((prev) => ({ ...prev, displayName: e.target.value }))}
                className="mt-1 h-12 w-full rounded-[12px] border border-[#e5e7eb] bg-white px-3 text-[14px] font-semibold text-[#111827] outline-none focus:border-[#2456a6]"
                placeholder="例如：老婆、儿子、朋友A"
              />
            </label>

            <div className="grid grid-cols-2 gap-2">
              {roleOptions.map((option) => {
                const selected = form.roleType === option.id;
                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, roleType: option.id }))}
                    className={`min-h-11 rounded-[12px] border px-2 text-[13px] font-bold ${
                      selected ? "border-[#2456a6] bg-[#edf5ff] text-[#2456a6]" : "border-[#e5e7eb] bg-white text-[#475569]"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <label className="block">
              <span className="text-[12px] font-bold text-[#64748b]">年龄</span>
              <input
                value={form.age}
                inputMode="numeric"
                onChange={(e) => setForm((prev) => ({ ...prev, age: e.target.value.replace(/[^\d]/g, "").slice(0, 3) }))}
                className="mt-1 h-12 w-full rounded-[12px] border border-[#e5e7eb] bg-white px-3 text-[14px] font-semibold text-[#111827] outline-none focus:border-[#2456a6]"
                placeholder="可不填"
              />
            </label>

            <TextAreaField
              label="硬性约束"
              value={form.hardConstraints}
              placeholder="例如：减脂期，餐饮要低卡"
              onChange={(value) => setForm((prev) => ({ ...prev, hardConstraints: value }))}
            />
            <TextAreaField
              label="偏好"
              value={form.softPreferences}
              placeholder="例如：安静聊天、咖啡、展览"
              onChange={(value) => setForm((prev) => ({ ...prev, softPreferences: value }))}
            />
            <TextAreaField
              label="风险点"
              value={form.riskPoints}
              placeholder="例如：排队太久、太吵、步行太远"
              onChange={(value) => setForm((prev) => ({ ...prev, riskPoints: value }))}
            />

            {editingExisting ? (
              <button
                type="button"
                onClick={() => void onDelete()}
                disabled={saving}
                className="flex min-h-11 w-full items-center justify-center gap-2 rounded-[12px] border border-red-100 bg-red-50 text-[13px] font-bold text-red-600 disabled:opacity-60"
              >
                <Trash2 className="h-4 w-4" strokeWidth={2.1} />
                删除这个人物
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </UserSettingsChrome>
  );
};

function TextAreaField({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
}): JSX.Element {
  return (
    <label className="block">
      <span className="text-[12px] font-bold text-[#64748b]">{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        className="mt-1 w-full resize-none rounded-[12px] border border-[#e5e7eb] bg-white px-3 py-2 text-[14px] font-semibold leading-5 text-[#111827] outline-none focus:border-[#2456a6]"
        placeholder={placeholder}
      />
    </label>
  );
}
