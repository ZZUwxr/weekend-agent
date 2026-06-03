import { useEffect, useState } from "react";
import {
  getCurrentTravel,
  refreshCurrentTravelFromBackend,
  subscribeCurrentTravel,
  type CurrentTravel,
} from "../lib/currentTravel";

export type CurrentTravelStatus = {
  current: CurrentTravel | null;
  loading: boolean;
  error: string | null;
};

export function useCurrentTravelStatus(): CurrentTravelStatus {
  const [status, setStatus] = useState<CurrentTravelStatus>({
    current: getCurrentTravel(),
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    setStatus({ current: getCurrentTravel(), loading: true, error: null });
    refreshCurrentTravelFromBackend()
      .then((value) => {
        if (active) setStatus({ current: value, loading: false, error: null });
      })
      .catch((e: unknown) => {
        if (!active) return;
        setStatus({
          current: null,
          loading: false,
          error: e instanceof Error ? e.message : "同步当前行程失败",
        });
      });
    const unsubscribe = subscribeCurrentTravel(() => {
      setStatus((prev) => ({
        ...prev,
        current: getCurrentTravel(),
      }));
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  return status;
}

export function useCurrentTravel(): CurrentTravel | null {
  return useCurrentTravelStatus().current;
}
