import { ChevronLeft, Footprints, JapaneseYen } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent } from "../../components/ui/card";
import { fetchBudgetPacePreferencesPage } from "../../lib/api";
import { MOCK_TRAVEL_ID } from "../../lib/api/mock/travel.mock";
import type {
  BudgetPacePreferencesPageDto,
  BudgetPaceRadioOptionDto,
} from "../../lib/api/types";
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
            className={`flex w-full items-start gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
              i < options.length - 1 ? "border-b border-[#f3f4f6]" : ""
            }`}
          >
            <span
              className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                selected ? "border-[#2563eb] bg-white" : "border-[#d1d5db] bg-white"
              }`}
              aria-hidden
            >
              {selected ? <span className="h-2.5 w-2.5 rounded-full bg-[#2563eb]" /> : null}
            </span>
            <div className="min-w-0 flex-1">
              <p className="[font-family:'HYQiHei-Regular',Helvetica] text-[13px] font-bold text-[#111827]">
                {opt.title}
              </p>
              <p className="mt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[11px] font-medium leading-relaxed text-[#6b7280]">
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
  const travelId = loc?.travelId ?? MOCK_TRAVEL_ID;
  const planId = loc?.planId ?? "plan-a";
  const flow = { travelId, planId };

  const [page, setPage] = useState<BudgetPacePreferencesPageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [budgetId, setBudgetId] = useState<string>("");
  const [paceId, setPaceId] = useState<string>("");

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

  const onSave = (): void => {
    navigate(PROFILE_PATH, { state: flow });
  };

  const loaded = page != null;

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
                  {page?.navTitle ?? "预算与节奏"}
                </h1>
              </div>
              <span className="w-14 shrink-0" aria-hidden />
            </div>
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pb-4">
            {loadError ? (
              <p className="text-center text-[13px] text-red-600">{loadError}</p>
            ) : !loaded ? (
              <p className="py-8 text-center text-[13px] text-[#64748b]">加载中…</p>
            ) : (
              <>
                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#2563eb]">
                        <JapaneseYen className="h-3.5 w-3.5 text-white" strokeWidth={2.25} />
                      </div>
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.budgetSectionTitle}
                      </span>
                    </div>
                    <RadioRows
                      options={page.budgetOptions}
                      selectedId={budgetId}
                      onSelect={setBudgetId}
                    />
                  </CardContent>
                </Card>

                <Card className="overflow-hidden rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0px_2px_12px_rgba(0,0,0,0.04)]">
                  <CardContent className="p-0">
                    <div className="flex items-center gap-2 border-b border-[#f3f4f6] px-3 py-2.5">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#2563eb]">
                        <Footprints className="h-3.5 w-3.5 text-white" strokeWidth={2.25} />
                      </div>
                      <span className="[font-family:'HYQiHei-Regular',Helvetica] text-[14px] font-bold text-[#111827]">
                        {page.paceSectionTitle}
                      </span>
                    </div>
                    <RadioRows options={page.paceOptions} selectedId={paceId} onSelect={setPaceId} />
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
