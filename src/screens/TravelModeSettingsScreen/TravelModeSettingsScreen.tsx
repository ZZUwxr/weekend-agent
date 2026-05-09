import { Car, ChevronLeft, Clock, MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchTravelModeSettingsPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  TravelModeMethodOptionId,
  TravelModeSettingsPageDto,
} from "../../lib/api/types";
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

  const onSave = (): void => {
    navigate(PROFILE_PATH, { state: flow });
  };

  return (
    <main className="relative min-h-[874px] w-full overflow-hidden bg-[#f3f4f6]">
      <div className="relative mx-auto flex min-h-[874px] w-full max-w-[402px] flex-col">
        {page ? (
          <img
            src={page.statusBarImageUrl}
            alt=""
            className="h-[61px] w-full shrink-0 object-cover object-top"
            height={61}
            width={402}
          />
        ) : (
          <div className="h-[61px] w-full shrink-0 bg-white/90" />
        )}

        <div className="flex min-h-0 flex-1 flex-col px-4 pb-6 pt-1">
          <header className="mb-3 flex items-center gap-1">
            <Link
              to={PROFILE_PATH}
              state={flow}
              className="flex items-center gap-0.5 text-[#2563eb] hover:opacity-80"
            >
              <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
              <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium">
                {page?.backLabel ?? "返回"}
              </span>
            </Link>
            <h1 className="flex-1 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold text-[#111827]">
              {page?.navTitle ?? "出行方式与距离"}
            </h1>
            <span className="w-14 shrink-0" aria-hidden />
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pb-4">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !page || methodId == null || radiusKm == null || durationId == null ? (
              <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
            ) : (
              <>
                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <Car className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
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
                          className={`flex w-full items-center justify-between px-3 py-3 text-left hover:bg-[#fafafa] ${
                            i < page.methodOptions.length - 1 ? "border-b border-[#f3f4f6]" : ""
                          }`}
                        >
                          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-semibold text-[#374151]">
                            {opt.label}
                          </span>
                          <span
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                              selected
                                ? "border-[#2563eb] bg-[#2563eb]"
                                : "border-[#d1d5db] bg-white"
                            }`}
                            aria-hidden
                          >
                            {selected ? (
                              <span className="block h-2 w-2 rounded-full bg-white" />
                            ) : null}
                          </span>
                        </button>
                      );
                    })}
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-3">
                    <div className="mb-3 flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.radiusSectionTitle}
                      </span>
                    </div>
                    <p className="mb-3 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[22px] font-bold text-[#2563eb]">
                      {formatRadiusKm(page.radiusValueFormat, radiusKm)}
                    </p>
                    <input
                      type="range"
                      min={page.radiusSliderMinKm}
                      max={page.radiusSliderMaxKm}
                      step={page.radiusSliderStepKm}
                      value={radiusKm}
                      onChange={(e) => setRadiusKm(Number(e.target.value))}
                      className="mb-1 h-2 w-full cursor-pointer appearance-none rounded-full bg-[#e5e7eb] accent-[#2563eb]"
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
                                ? "border-[#2563eb] bg-[#eff6ff] text-[#2563eb]"
                                : "border-[#e5e7eb] bg-white text-[#6b7280]"
                            }`}
                          >
                            {p.label}
                          </button>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <Clock className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
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
                          className={`flex w-full items-center justify-between px-3 py-3 text-left hover:bg-[#fafafa] ${
                            i < page.durationOptions.length - 1 ? "border-b border-[#f3f4f6]" : ""
                          }`}
                        >
                          <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[12px] font-semibold text-[#374151]">
                            {opt.label}
                          </span>
                          <span
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                              selected
                                ? "border-[#2563eb] bg-[#2563eb]"
                                : "border-[#d1d5db] bg-white"
                            }`}
                            aria-hidden
                          >
                            {selected ? (
                              <span className="block h-2 w-2 rounded-full bg-white" />
                            ) : null}
                          </span>
                        </button>
                      );
                    })}
                  </CardContent>
                </Card>
              </>
            )}
          </div>

          {page ? (
            <button
              type="button"
              onClick={onSave}
              className="mt-auto w-full rounded-[14px] bg-[#2563eb] py-3.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-bold text-white shadow-[0px_4px_14px_rgba(37,99,235,0.35)] transition-opacity hover:opacity-95 active:scale-[0.99]"
            >
              {page.saveButtonLabel}
            </button>
          ) : null}
        </div>
      </div>
    </main>
  );
};
