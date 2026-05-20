import { Car, Clock, MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ContentFitZoom } from "../../components/ContentFitZoom";
import { UserSettingsChrome, UserSettingsIconWrap, userSettingsCardClass } from "../../components/UserSettingsChrome";
import { fetchTravelModeSettingsPage, saveTravelModePreferences } from "../../lib/api";
import { FIGMA_USER_SETTINGS_114 } from "../../lib/api/mock/figma-user-settings-114-assets";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { TravelModeMethodOptionId, TravelModeSettingsPageDto } from "../../lib/api/types";
import { PROFILE_PATH, TRAVEL_MODE_SETTINGS_PATH } from "../../routes";

type SettingsLocationState = { travelId?: string; planId?: string };

function formatRadiusKm(template: string, km: number): string {
  return template.replace(/\{km\}/g, String(km));
}

export const TravelModeSettingsScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as SettingsLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [page, setPage] = useState<TravelModeSettingsPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [methodId, setMethodId] = useState<TravelModeMethodOptionId | null>(null);
  const [radiusKm, setRadiusKm] = useState<number | null>(null);
  const [durationId, setDurationId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === TRAVEL_MODE_SETTINGS_PATH) {
      document.title = "出行方式与距离 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchTravelModeSettingsPage()
      .then((data) => {
        if (active) {
          setPage(data);
          setMethodId(data.selectedMethodId);
          setRadiusKm(data.selectedRadiusKm);
          setDurationId(data.selectedDurationId);
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
    if (!page || methodId == null || radiusKm == null || durationId == null) return;
    setSaveError(null);
    setSaving(true);
    try {
      await saveTravelModePreferences({
        selectedMethodId: methodId,
        selectedRadiusKm: radiusKm,
        selectedDurationId: durationId,
      });
      navigate(PROFILE_PATH, { state: flow });
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const statusBarSrc = page?.statusBarImageUrl ?? FIGMA_USER_SETTINGS_114.statusBar;
  const navTitle = page?.navTitle ?? "出行方式与距离";

  return (
    <UserSettingsChrome
      travelId={travelId}
      planId={planId}
      navTitle={navTitle}
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
      <ContentFitZoom className="space-y-3 pb-2" recalcKey={methodId ?? ""}>
        {saveError ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-center text-[13px] text-red-600">{saveError}</p>
        ) : null}
        {loadError ? (
          <p className="text-center text-[13px] text-red-600">{loadError}</p>
        ) : !page || methodId == null || radiusKm == null || durationId == null ? (
          <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
        ) : (
          <>
            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#faf2ac]/90 px-3 py-2.5">
                  <UserSettingsIconWrap>
                    <Car className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                    {page.methodSectionTitle}
                  </span>
                </div>
                {page.methodOptions.map((opt, i) => {
                  const selected = methodId === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setMethodId(opt.id)}
                      className={`flex w-full items-center justify-between px-3 py-3 text-left hover:bg-[#fffef8] ${
                        i < page.methodOptions.length - 1 ? "border-b border-[#faf2ac]/50" : ""
                      }`}
                    >
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#374151]">
                        {opt.label}
                      </span>
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                          selected ? "border-[#eab308] bg-[#eab308]" : "border-[#d1d5db] bg-white"
                        }`}
                        aria-hidden
                      >
                        {selected ? <span className="block h-2 w-2 rounded-full bg-white" /> : null}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className={userSettingsCardClass}>
              <div className="p-3">
                <div className="mb-3 flex items-center gap-2">
                  <UserSettingsIconWrap>
                    <MapPin className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                    {page.radiusSectionTitle}
                  </span>
                </div>
                <p className="mb-3 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[22px] font-bold text-[#ca8a04]">
                  {formatRadiusKm(page.radiusValueFormat, radiusKm)}
                </p>
                <input
                  type="range"
                  min={page.radiusSliderMinKm}
                  max={page.radiusSliderMaxKm}
                  step={page.radiusSliderStepKm}
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                  className="mb-1 h-2 w-full cursor-pointer appearance-none rounded-full bg-[#fef3c7] accent-[#eab308]"
                />
                <div className="mt-3 flex gap-2">
                  {page.radiusPresets.map((p) => {
                    const active = radiusKm === p.valueKm;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setRadiusKm(p.valueKm)}
                        className={`flex-1 rounded-full border py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold transition-colors ${
                          active
                            ? "border-[#eab308] bg-[#fffbeb] text-[#a16207]"
                            : "border-[#e5e7eb] bg-white text-[#6b7280]"
                        }`}
                      >
                        {p.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className={userSettingsCardClass}>
              <div className="p-0">
                <div className="flex items-center gap-2 border-b border-[#faf2ac]/90 px-3 py-2.5">
                  <UserSettingsIconWrap>
                    <Clock className="h-4 w-4" strokeWidth={1.75} />
                  </UserSettingsIconWrap>
                  <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#1e293b]">
                    {page.durationSectionTitle}
                  </span>
                </div>
                {page.durationOptions.map((opt, i) => {
                  const selected = durationId === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setDurationId(opt.id)}
                      className={`flex w-full items-center justify-between px-3 py-3 text-left hover:bg-[#fffef8] ${
                        i < page.durationOptions.length - 1 ? "border-b border-[#faf2ac]/50" : ""
                      }`}
                    >
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#374151]">
                        {opt.label}
                      </span>
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                          selected ? "border-[#eab308] bg-[#eab308]" : "border-[#d1d5db] bg-white"
                        }`}
                        aria-hidden
                      >
                        {selected ? <span className="block h-2 w-2 rounded-full bg-white" /> : null}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </ContentFitZoom>
    </UserSettingsChrome>
  );
};
