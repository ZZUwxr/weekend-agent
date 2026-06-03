import { Check, ChevronRight, Target, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { AppStatusStrip } from "../../components/AppUi";
import { fetchActivityPreferencesPage, saveActivityPreferences } from "../../lib/api";
import { FIGMA_USER_SETTINGS_114 } from "../../lib/api/mock/figma-user-settings-114-assets";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import type { ActivityPreferencesPageDto } from "../../lib/api/types";
import { ACTIVITY_PREFERENCES_PATH, PROFILE_PATH } from "../../routes";

type SettingsLocationState = { travelId?: string; planId?: string };

export const ActivityPreferencesScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as SettingsLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const flow = { travelId, planId };

  const [page, setPage] = useState<ActivityPreferencesPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === ACTIVITY_PREFERENCES_PATH) {
      document.title = "活动偏好 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchActivityPreferencesPage()
      .then((data) => {
        if (active) {
          setPage(data);
          setSelectedTags([...data.selectedTagIds]);
        }
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const toggleTag = (id: string): void => {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const onSave = async (): Promise<void> => {
    if (!page) return;
    setSaveError(null);
    setSaving(true);
    try {
      await saveActivityPreferences({ selectedTagIds: selectedTags });
      navigate(PROFILE_PATH, { state: flow });
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const loaded = page != null;
  const statusBarSrc = page?.statusBarImageUrl ?? FIGMA_USER_SETTINGS_114.statusBar;

  return (
    <UserSettingsChrome
      travelId={travelId}
      planId={planId}
      navTitle={page?.navTitle ?? "活动偏好"}
      navSubtitle={page?.navSubtitle}
      backLabel={page?.backLabel ?? "返回"}
      statusBarSrc={statusBarSrc}
      footer={
        page ? (
          <button
            type="button"
            onClick={() => {
              void onSave();
            }}
            disabled={saving}
            className="mt-2 w-full shrink-0 rounded-[14px] bg-[#ffd100] py-3.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-[#343d43] shadow-[0px_4px_16px_rgba(245,200,20,0.38)] transition-opacity hover:opacity-95 active:scale-[0.99] disabled:opacity-60"
          >
            {saving ? "保存中…" : page.saveButtonLabel}
          </button>
        ) : null
      }
    >
      <div className="space-y-3 pb-2">
        {saveError ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p>
        ) : null}
        {loadError ? (
          <p className="text-center text-[13px] text-red-600">{loadError}</p>
        ) : !loaded ? (
          <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
        ) : (
          <>
            <AppStatusStrip
              Icon={Target}
              title={selectedTags.length > 0 ? `已选择 ${selectedTags.length} 个活动偏好` : "选择你更想要的活动类型"}
              detail={
                selectedTags.length > 0
                  ? page.tagOptions
                      .filter((opt) => selectedTags.includes(opt.id))
                      .map((opt) => opt.label)
                      .join("、")
                  : "可多选，AI 会用它筛掉不合适的安排。"
              }
            />

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#e5e7eb] px-3 py-3">
                  <UserSettingsIconWrap>
                    <Target className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="text-[15px] font-bold text-[#111827]">
                    {page.tagsSectionTitle}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 p-3">
                  {page.tagOptions.map((opt) => {
                    const checked = selectedTags.includes(opt.id);
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => toggleTag(opt.id)}
                        aria-pressed={checked}
                        className={`flex min-h-[58px] items-center gap-2 rounded-[14px] border px-3 py-2 text-left transition active:scale-[0.98] ${
                          checked
                            ? "border-[#2456a6] bg-[#edf5ff] text-[#2456a6]"
                            : "border-[#e5e7eb] bg-white text-[#374151]"
                        }`}
                      >
                        <span
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-[10px] ${
                            checked ? "bg-[#2456a6] text-white" : "bg-[#f1f5f9] text-[#94a3b8]"
                          }`}
                          aria-hidden
                        >
                          {checked ? <Check className="h-4 w-4" strokeWidth={2.6} /> : null}
                        </span>
                        <span className="text-[13px] font-bold leading-5">{opt.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#e5e7eb] px-3 py-3">
                  <UserSettingsIconWrap>
                    <Users className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="text-[15px] font-bold text-[#111827]">
                    {page.familySectionTitle}
                  </span>
                </div>
                {page.familyMembers.map((m, i) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`flex min-h-[72px] w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#f8fafc] ${
                      i < page.familyMembers.length - 1 ? "border-b border-[#e5e7eb]" : ""
                    }`}
                  >
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#fffbeb] text-xl ring-1 ring-[#fef3c7]">
                      {m.avatarImageUrl ? (
                        <img src={m.avatarImageUrl} alt="" className="h-full w-full object-cover" />
                      ) : (
                        <span>{m.avatarEmoji ?? "👤"}</span>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[14px] font-bold text-[#111827]">
                        {m.name}
                      </p>
                      <p className="mt-0.5 text-[12px] font-medium leading-5 text-[#64748b]">
                        {m.summaryLine}
                      </p>
                    </div>
                    <ChevronRight className="h-4 w-4 shrink-0 text-[#d1d5db]" strokeWidth={1.75} />
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </UserSettingsChrome>
  );
};
