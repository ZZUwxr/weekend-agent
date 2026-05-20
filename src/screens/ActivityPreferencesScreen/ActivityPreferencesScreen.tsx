import { Check, ChevronRight, Target, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { fetchActivityPreferencesPage, saveActivityPreferences } from "../../lib/api";
import { FIGMA_USER_SETTINGS_114 } from "../../lib/api/mock/figma-user-settings-114-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { ActivityPreferencesPageDto } from "../../lib/api/types";
import { ACTIVITY_PREFERENCES_PATH, PROFILE_PATH } from "../../routes";

type SettingsLocationState = { travelId?: string; planId?: string };

export const ActivityPreferencesScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as SettingsLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
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
      <ContentFitZoom className="space-y-3 pb-2" recalcKey={selectedTags.join(",")}>
        {saveError ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p>
        ) : null}
        {loadError ? (
          <p className="text-center text-[13px] text-red-600">{loadError}</p>
        ) : !loaded ? (
          <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
        ) : (
          <>
            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#faf2ac]/90 px-3 py-2.5">
                  <UserSettingsIconWrap>
                    <Target className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                    {page.tagsSectionTitle}
                  </span>
                </div>
                {page.tagOptions.map((opt, i) => {
                  const checked = selectedTags.includes(opt.id);
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => toggleTag(opt.id)}
                      className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fffef8] ${
                        i < page.tagOptions.length - 1 ? "border-b border-[#faf2ac]/50" : ""
                      }`}
                    >
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 ${
                          checked
                            ? "border-[#eab308] bg-[#eab308] text-white"
                            : "border-[#d1d5db] bg-white"
                        }`}
                        aria-hidden
                      >
                        {checked ? <Check className="h-3 w-3" strokeWidth={3} /> : null}
                      </span>
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#374151]">
                        {opt.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#faf2ac]/90 px-3 py-2.5">
                  <UserSettingsIconWrap>
                    <Users className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                    {page.familySectionTitle}
                  </span>
                </div>
                {page.familyMembers.map((m, i) => (
                  <button
                    key={m.id}
                    type="button"
                    className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fffef8] ${
                      i < page.familyMembers.length - 1 ? "border-b border-[#faf2ac]/50" : ""
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
                      <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-bold text-[#1e293b]">
                        {m.name}
                      </p>
                      <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#6b7280]">
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
      </ContentFitZoom>
    </UserSettingsChrome>
  );
};
