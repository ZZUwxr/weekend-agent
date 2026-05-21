import { resetTripContentUnlockForDev } from "../lib/tripContentUnlock";
import { useTripContentUnlocked } from "../hooks/useTripContentUnlocked";

/**
 * 仅开发：显示当前是否已解锁「有行程」数据层；一键重置为无行程初始体验。
 * 正式环境不出现。
 */
export function DevTripExperienceReset(): JSX.Element | null {
  const unlocked = useTripContentUnlocked();
  if (!import.meta.env.DEV) return null;

  return (
    <div className="fixed bottom-28 left-2 z-[9998] max-w-[11rem] rounded-lg border border-white/20 bg-black/80 px-2 py-1.5 font-mono text-[10px] text-white shadow-lg">
      <div className="opacity-70">行程数据</div>
      <div className={unlocked ? "text-emerald-400" : "text-amber-400"}>
        {unlocked ? "已解锁（有路线图）" : "未解锁（初始空态）"}
      </div>
      <button
        type="button"
        className="mt-1 w-full rounded bg-white/15 px-1.5 py-0.5 text-left hover:bg-white/25"
        onClick={() => {
          resetTripContentUnlockForDev();
        }}
      >
        重置为首次体验
      </button>
    </div>
  );
}
