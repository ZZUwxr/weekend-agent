import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useResolvedTravel } from "../../hooks/useResolvedTravel";
import { fetchProfilePage } from "../../lib/api";
import type { ProfilePageDto } from "../../lib/api/types";
import { PROFILE_PATH } from "../../routes";
import { ProfileP2View } from "./ProfileEmptyView";

type ProfileLocationState = { travelId?: string; planId?: string };

export const ProfileScreen = (): JSX.Element => {
  const { state, pathname } = useLocation();
  const loc = state as ProfileLocationState | null;
  const resolved = useResolvedTravel(loc);
  const travelId = resolved.travelId;
  const planId = resolved.planId;

  const [page, setPage] = useState<ProfilePageDto | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.title;
    if (pathname === PROFILE_PATH) {
      document.title = "我的 · 出行助手";
    }
    return () => {
      document.title = prev;
    };
  }, [pathname]);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    setPage(null);
    fetchProfilePage()
      .then((data) => {
        if (active) setPage(data);
      })
      .catch((e: unknown) => {
        if (active) setLoadError(e instanceof Error ? e.message : "加载失败");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <ProfileP2View
      mode="unlocked"
      page={page}
      loadError={loadError}
      travelId={travelId}
      planId={planId}
    />
  );
};
