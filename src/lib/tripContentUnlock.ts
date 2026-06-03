import { clearCurrentTravel, getCurrentTravel, refreshCurrentTravelFromBackend } from "./currentTravel";

/**
 * 单一用户体验：未解锁前地图 / 行程主页 / 我的均为「初始无行程」稿；
 * 新流程以后端 active travel 同步到本地的 `currentTravel` 为主状态来源。
 * 本模块只保留事件广播和开发重置能力，不再维护独立的解锁开关。
 */
const STORAGE_KEY = "meituan_trip_content_unlocked_v1";
const EVENT = "trip-content-unlock-changed";

/** 清理旧版手动 shell / unlock 开关，避免残留 key 干扰后端 active travel。 */
function removeLegacyShellFlags(): void {
  try {
    window.localStorage.removeItem("ai_journey_shell_mode");
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function isTripContentUnlocked(): boolean {
  if (typeof window === "undefined") return false;
  removeLegacyShellFlags();
  return Boolean(getCurrentTravel()?.travelId);
}

export async function refreshTripContentUnlockFromBackend(): Promise<boolean> {
  const current = await refreshCurrentTravelFromBackend();
  return Boolean(current?.travelId);
}

/** 兼容旧调用点：只广播状态变化；是否有行程由 currentTravel/后端 active travel 决定。 */
export function unlockTripContent(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(EVENT));
}

/** 仅开发调试用：恢复「首次打开、尚无行程」体验 */
export function resetTripContentUnlockForDev(): void {
  removeLegacyShellFlags();
  clearCurrentTravel();
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(EVENT));
}

export function subscribeTripContentUnlock(cb: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  const handler = (): void => cb();
  window.addEventListener(EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}
