export type CurrentTravel = {
  travelId: string;
  planId: string;
  updatedAt: number;
};

const LEGACY_STORAGE_KEY = "meituan_current_travel_v1";
const LAST_PLAN_STORAGE_KEY = "weekend_agent_last_plan_id_v1";
const EVENT = "current-travel-changed";
const DEFAULT_PLAN_ID = "plan-a";
let currentTravelSnapshot: CurrentTravel | null = null;

export function normalizePlanId(planId: string | null | undefined): string {
  const value = (planId || DEFAULT_PLAN_ID).trim();
  return value ? value.replace(/_/g, "-") : DEFAULT_PLAN_ID;
}

export function getCurrentTravel(): CurrentTravel | null {
  return currentTravelSnapshot;
}

export function resolveCurrentTravel(input?: {
  travelId?: string | null;
  planId?: string | null;
} | null): CurrentTravel {
  const current = getCurrentTravel();
  const travelId = input?.travelId?.trim() || current?.travelId || "";
  const planId = normalizePlanId(input?.planId || current?.planId || getLastPlanId());
  return { travelId, planId, updatedAt: current?.updatedAt ?? Date.now() };
}

export function setCurrentTravel(input: {
  travelId?: string | null;
  planId?: string | null;
}): CurrentTravel | null {
  const travelId = input.travelId?.trim() || "";
  const planId = normalizePlanId(input.planId);
  saveLastPlanId(planId);
  if (!travelId) {
    emitCurrentTravelChanged();
    return currentTravelSnapshot;
  }
  const value: CurrentTravel = {
    travelId,
    planId,
    updatedAt: Date.now(),
  };
  currentTravelSnapshot = value;
  emitCurrentTravelChanged();
  return value;
}

export function clearCurrentTravel(): void {
  currentTravelSnapshot = null;
  try {
    window.localStorage.removeItem(LEGACY_STORAGE_KEY);
  } catch {
    /* ignore */
  }
  emitCurrentTravelChanged();
}

export function subscribeCurrentTravel(cb: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  const handler = (): void => cb();
  window.addEventListener(EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}

function emitCurrentTravelChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(EVENT));
}

export async function refreshCurrentTravelFromBackend(): Promise<CurrentTravel | null> {
  const { fetchActiveTravel } = await import("./api");
  let active;
  try {
    active = await fetchActiveTravel();
  } catch (error) {
    clearCurrentTravel();
    throw error;
  }
  if (!active.travelId) {
    clearCurrentTravel();
    return null;
  }
  return setCurrentTravel({
    travelId: active.travelId,
    planId: active.planId || undefined,
  });
}

function getLastPlanId(): string {
  if (typeof window === "undefined") return DEFAULT_PLAN_ID;
  try {
    const raw = window.localStorage.getItem(LAST_PLAN_STORAGE_KEY);
    if (raw?.trim()) return normalizePlanId(raw);
    const legacyRaw = window.localStorage.getItem(LEGACY_STORAGE_KEY);
    if (legacyRaw) {
      const legacy = JSON.parse(legacyRaw) as { planId?: unknown };
      if (typeof legacy.planId === "string" && legacy.planId.trim()) {
        return normalizePlanId(legacy.planId);
      }
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_PLAN_ID;
}

function saveLastPlanId(planId: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LAST_PLAN_STORAGE_KEY, normalizePlanId(planId));
    window.localStorage.removeItem(LEGACY_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
