import { Check, ChevronLeft, ChevronRight, Utensils, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchDietaryPreferencesPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type { DietaryNeedOptionDto, DietaryPreferencesPageDto } from "../../lib/api/types";
import { DIETARY_PREFERENCES_PATH, PROFILE_PATH } from "../../routes";

type SettingsLocationState = { travelId?: string; planId?: string };

export const DietaryPreferencesScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const navigate = useNavigate();
  const loc = state as SettingsLocationState | null;
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [page, setPage] = useState<DietaryPreferencesPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [allergenNote, setAllergenNote] = useState("");

  useEffect(() => {
    const prev = document.title;
    if (pathname === DIETARY_PREFERENCES_PATH) {
      document.title = "饮食偏好 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchDietaryPreferencesPage()
      .then((data) => {
        if (active) {
          setPage(data);
          setSelectedIds([...data.selectedNeedIds]);
        }
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  const toggleNeed = (opt: DietaryNeedOptionDto, allOptions: DietaryNeedOptionDto[]): void => {
    setSelectedIds((prev) => {
      if (opt.exclusive) {
        return prev.includes(opt.id) ? [] : [opt.id];
      }
      const withoutExclusive = prev.filter((id) => {
        const o = allOptions.find((x) => x.id === id);
        return !o?.exclusive;
      });
      if (withoutExclusive.includes(opt.id)) {
        return withoutExclusive.filter((id) => id !== opt.id);
      }
      return [...withoutExclusive, opt.id];
    });
  };

  const onSave = (): void => {
    navigate(PROFILE_PATH, { state: flow });
  };

  const needsLoaded = page != null;

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
          <header className="mb-3">
            <div className="flex items-center gap-1">
              <Link
                to={PROFILE_PATH}
                state={flow}
                className="flex shrink-0 items-center gap-0.5 text-[#2563eb] hover:opacity-80"
              >
                <ChevronLeft className="h-6 w-6" strokeWidth={1.75} />
                <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-medium">
                  {page?.backLabel ?? "返回"}
                </span>
              </Link>
              <div className="min-w-0 flex-1 text-center">
                <h1 className="[font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-semibold text-[#111827]">
                  {page?.navTitle ?? "饮食偏好"}
                </h1>
              </div>
              <span className="w-14 shrink-0" aria-hidden />
            </div>
            {page?.navSubtitle ? (
              <p className="mt-1 text-center [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#6b7280]">
                {page.navSubtitle}
              </p>
            ) : null}
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pb-4">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !needsLoaded ? (
              <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
            ) : (
              <>
                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <Utensils className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.specialNeedsSectionTitle}
                      </span>
                    </div>
                    {page.needOptions.map((opt, i) => {
                      const checked = selectedIds.includes(opt.id);
                      return (
                        <div key={opt.id}>
                          <button
                            type="button"
                            onClick={() => toggleNeed(opt, page.needOptions)}
                            className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
                              i < page.needOptions.length - 1 || (checked && opt.expandWhenChecked)
                                ? "border-b border-[#f3f4f6]"
                                : ""
                            }`}
                          >
                            <span
                              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 ${
                                checked
                                  ? "border-[#2563eb] bg-[#2563eb] text-white"
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
                          {checked && opt.expandWhenChecked ? (
                            <div className="border-b border-[#f3f4f6] px-3 pb-3 pl-11">
                              <textarea
                                value={allergenNote}
                                onChange={(e) => setAllergenNote(e.target.value)}
                                placeholder="请填写过敏源信息…"
                                rows={3}
                                className="w-full resize-none rounded-xl border border-[#e5e7eb] bg-[#fafafa] px-3 py-2 [font-family:'HYQiHei-Regular',Helvetica] text-[12px] text-[#374151] outline-none placeholder:text-[#9ca3af]"
                              />
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <Users className="h-4 w-4 text-[#2563eb]" strokeWidth={1.75} />
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.familySectionTitle}
                      </span>
                    </div>
                    {page.familyMembers.map((m, i) => (
                      <button
                        key={m.id}
                        type="button"
                        className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
                          i < page.familyMembers.length - 1 ? "border-b border-[#f3f4f6]" : ""
                        }`}
                      >
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#eff6ff] text-xl">
                          {m.avatarImageUrl ? (
                            <img src={m.avatarImageUrl} alt="" className="h-full w-full object-cover" />
                          ) : (
                            <span>{m.avatarEmoji ?? "👤"}</span>
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-bold text-[#111827]">
                            {m.name}
                          </p>
                          <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium text-[#6b7280]">
                            {m.summaryLine}
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 shrink-0 text-[#d1d5db]" strokeWidth={1.75} />
                      </button>
                    ))}
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
