import { useEffect, useState } from "react";
import {
  isTripContentUnlocked,
  refreshTripContentUnlockFromBackend,
  subscribeTripContentUnlock,
} from "../lib/tripContentUnlock";

export function useTripContentUnlocked(): boolean {
  const [unlocked, setUnlocked] = useState(false);
  useEffect(() => {
    setUnlocked(isTripContentUnlocked());
    refreshTripContentUnlockFromBackend()
      .then(setUnlocked)
      .catch(() => setUnlocked(false));
    return subscribeTripContentUnlock(() => setUnlocked(isTripContentUnlocked()));
  }, []);
  return unlocked;
}
