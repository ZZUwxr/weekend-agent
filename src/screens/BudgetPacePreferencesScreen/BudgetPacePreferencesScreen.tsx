import { Check, Footprints, JapaneseYen } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { AppStatusStrip } from "../../components/AppUi";
import { fetchBudgetPacePreferencesPage, saveBudgetPacePreferences } from "../../lib/api";
import { FIGMA_USER_SETTINGS_114 } from "../../lib/api/mock/figma-user-settings-114-assets";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import type { BudgetPacePreferencesPageDto, BudgetPaceRadioOptionDto } from "../../lib/api/types";
import { BUDGET_PACE_PREFERENCES_PATH, PROFILE_PATH } from "../../routes";

type SettingsLocationState = { travelId?: string; planId?: string };

function RadioRows({
  options,
  selectedId,
  onSelect,
}: {
  options: BudgetPaceRadioOptionDto[];
  selectedId: string;
  onSelect: (id: string) => void;
}): JSX.Element {
  return (
    <>
      {options.map((opt, i) => {
        const selected = opt.id === selectedId;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onSelect(opt.id)}
            aria-pressed={selected}
            className={`flex min-h-[74px] w-full items-start gap-3 px-3 py-3 text-left transition active:scale-[0.995] ${
              selected ? "bg-[#f1f6ff]" : "bg-white hover:bg-[#f8fafc]"
            } ${i < options.length - 1 ? "border-b border-[#e5e7eb]" : ""}`}
          >
            <span
              className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                selected ? "bg-[#2456a6] text-white" : "border border-[#d1d5db] bg-white"
            }`}
              aria-hidden
            >
              {selected ? <Check className="h-4 w-4" strokeWidth={2.6} /> : null}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-bold text-[#111827]">
                {opt.title}
              </p>
              <p className="mt-0.5 text-[12px] font-medium leading-5 text-[#64748b]">
                {opt.description}
              </p>
            </div>
          </button>
        );
      })}
    </>
  );
}

export const BudgetPacePreferencesScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as SettingsLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;
  const flow = { travelId, planId };

  const [page, setPage] = useState<BudgetPacePreferencesPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [budgetId, setBudgetId] = useState<string>("");
  const [paceId, setPaceId] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === BUDGET_PACE_PREFERENCES_PATH) {
      document.title = "预算与节奏 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchBudgetPacePreferencesPage()
      .then((data) => {
        if (active) {
          setPage(data);
          setBudgetId(data.selectedBudgetId);
          setPaceId(data.selectedPaceId);
        }
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const onSave = async (): Promise<void> => {
    if (!page) return;
    setSaveError(null);
    setSaving(true);
    try {
      await saveBudgetPacePreferences({
        selectedBudgetId: budgetId,
        selectedPaceId: paceId,
      });
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
      navTitle={page?.navTitle ?? "预算与节奏"}
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
              Icon={JapaneseYen}
              title="当前预算与节奏"
              detail={`${page.budgetOptions.find((opt) => opt.id === budgetId)?.title ?? "未选择"} · ${page.paceOptions.find((opt) => opt.id === paceId)?.title ?? "未选择"}`}
            />

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#e5e7eb] px-3 py-3">
                  <UserSettingsIconWrap>
                    <JapaneseYen className="h-4 w-4" strokeWidth={2} />
                  </UserSettingsIconWrap>
                  <span className="text-[15px] font-bold text-[#111827]">
                    {page.budgetSectionTitle}
                  </span>
                </div>
                <RadioRows options={page.budgetOptions} selectedId={budgetId} onSelect={setBudgetId} />
              </div>
            </div>

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#e5e7eb] px-3 py-3">
                  <UserSettingsIconWrap>
                    <Footprints className="h-4 w-4" strokeWidth={2} />
                  </UserSettingsIconWrap>
                  <span className="text-[15px] font-bold text-[#111827]">
                    {page.paceSectionTitle}
                  </span>
                </div>
                <RadioRows options={page.paceOptions} selectedId={paceId} onSelect={setPaceId} />
              </div>
            </div>
          </>
        )}
      </div>
    </UserSettingsChrome>
  );
};
