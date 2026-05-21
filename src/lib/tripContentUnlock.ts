/**
 * 单一用户体验：未解锁前地图 / 行程主页 / 我的均为「初始无行程」稿；
 * 用户在 **预约确认页** 点击「前往支付」进入付款流时解锁（见 `BookingCheckoutScreen`），此后三处再拉接口展示完整内容。
 */
const STORAGE_KEY = "meituan_trip_content_unlocked_v1";
const EVENT = "trip-content-unlock-changed";

/** 一次性迁移旧版手动 shell 开关（避免残留 key 干扰） */
function migrateLegacyShellFlagOnce(): void {
  try {
    const legacy = window.localStorage.getItem("ai_journey_shell_mode");
    if (legacy != null) {
      if (window.localStorage.getItem(STORAGE_KEY) == null) {
        window.localStorage.setItem(STORAGE_KEY, legacy === "active" ? "1" : "0");
      }
      window.localStorage.removeItem("ai_journey_shell_mode");
    }
  } catch {
    /* ignore */
  }
}

export function isTripContentUnlocked(): boolean {
  if (typeof window === "undefined") return false;
  migrateLegacyShellFlagOnce();
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** 在用户从预约确认页点击「前往支付」、动身进入付款流时调用 */
export function unlockTripContent(): void {
  if (isTripContentUnlocked()) return;
  try {
    window.localStorage.setItem(STORAGE_KEY, "1");
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event(EVENT));
}

/** 仅开发调试用：恢复「首次打开、尚无行程」体验 */
export function resetTripContentUnlockForDev(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event(EVENT));
}

export function subscribeTripContentUnlock(cb: () => void): () => void {
  const handler = (): void => cb();
  window.addEventListener(EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}
