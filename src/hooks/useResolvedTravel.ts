import { useMemo } from "react";
import { useCurrentTravelStatus } from "./useCurrentTravel";
import { resolveCurrentTravel } from "../lib/currentTravel";

export type ResolvedTravel = {
  travelId: string;
  planId: string;
  loading: boolean;
  error: string | null;
};

export function useResolvedTravel(
  input?: { travelId?: string | null; planId?: string | null } | null,
): ResolvedTravel {
  const { current, loading, error } = useCurrentTravelStatus();
  return useMemo(() => {
    const resolved = resolveCurrentTravel(input ?? current);
    return { ...resolved, loading, error };
  }, [
    input?.travelId,
    input?.planId,
    current?.travelId,
    current?.planId,
    loading,
    error,
  ]);
}
