import { useEffect, useState } from "react";
import { isTripContentUnlocked, subscribeTripContentUnlock } from "../lib/tripContentUnlock";

export function useTripContentUnlocked(): boolean {
  const [unlocked, setUnlocked] = useState(isTripContentUnlocked);
  useEffect(() => {
    setUnlocked(isTripContentUnlocked());
    return subscribeTripContentUnlock(() => setUnlocked(isTripContentUnlocked()));
  }, []);
  return unlocked;
}
