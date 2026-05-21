import { useEffect, useLayoutEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import {
  BOOKING_CHECKOUT_PATH,
  BOOKING_TODOS_PATH,
  CHAT_PATH,
  HOME_PATH,
  HOME_PATH_ALT,
  ITINERARY_HUB_PATH,
  PAYMENT_CONFIRMATION_PATH,
  PAYMENT_PATH,
  PLANS_PATH,
  PROFILE_PATH,
  TIMELINE_PATH,
  ACTIVITY_PREFERENCES_PATH,
  BUDGET_PACE_PREFERENCES_PATH,
  DIETARY_PREFERENCES_PATH,
  TRAVEL_MODE_SETTINGS_PATH,
  TRIP_LIVE_MAP_PATH,
  TRIP_FEEDBACK_DONE_PATH,
  TRIP_FEEDBACK_PATH,
  TRIP_WRAP_PATH,
} from "./routes";
import { ActivityPreferencesScreen } from "./screens/ActivityPreferencesScreen";
import { BudgetPacePreferencesScreen } from "./screens/BudgetPacePreferencesScreen";
import { BookingCheckoutScreen } from "./screens/BookingCheckoutScreen";
import { ItineraryHubScreen } from "./screens/ItineraryHubScreen";
import { PaymentConfirmationScreen } from "./screens/PaymentConfirmationScreen";
import { PaymentScreen } from "./screens/PaymentScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { BookingTodosScreen } from "./screens/BookingTodosScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { IphonePro } from "./screens/IphonePro";
import { PlanCompareScreen } from "./screens/PlanCompareScreen";
import { TimelineRouteScreen } from "./screens/TimelineRouteScreen";
import { DietaryPreferencesScreen } from "./screens/DietaryPreferencesScreen";
import { TravelModeSettingsScreen } from "./screens/TravelModeSettingsScreen";
import { TripLiveMapScreen } from "./screens/TripLiveMapScreen";
import { TripFeedbackDoneScreen } from "./screens/TripFeedbackDoneScreen/TripFeedbackDoneScreen";
import { TripFeedbackScreen } from "./screens/TripFeedbackScreen/TripFeedbackScreen";
import { TripWrapScreen } from "./screens/TripWrapScreen/TripWrapScreen";
import { DevTripExperienceReset } from "./components/DevTripExperienceReset";

function DevRouterPathBadge(): JSX.Element | null {
  const { pathname } = useLocation();
  if (!import.meta.env.DEV) return null;
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed bottom-14 right-2 z-[9999] rounded bg-black/75 px-2 py-1 font-mono text-[10px] text-white opacity-70"
    >
      {pathname}
    </div>
  );
}

/** 任意路由切换后回到视口顶部，避免底栏跳回首页仍停在上一屏滚动位置 */
function ScrollToTop(): null {
  const location = useLocation();

  useEffect(() => {
    if ("scrollRestoration" in window.history) {
      window.history.scrollRestoration = "manual";
    }
  }, []);

  useLayoutEffect(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [location.pathname, location.key]);

  return null;
}

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <>
        <ScrollToTop />
        <DevTripExperienceReset />
        <DevRouterPathBadge />
        <Routes>
          <Route path={HOME_PATH_ALT} element={<HomeScreen />} />
          <Route path={HOME_PATH} element={<HomeScreen />} />
          <Route path={CHAT_PATH} element={<IphonePro />} />
          <Route path={PLANS_PATH} element={<PlanCompareScreen />} />
          <Route path={TIMELINE_PATH} element={<TimelineRouteScreen />} />
          <Route path={BOOKING_TODOS_PATH} element={<BookingTodosScreen />} />
          <Route path={BOOKING_CHECKOUT_PATH} element={<BookingCheckoutScreen />} />
          <Route path={PAYMENT_PATH} element={<PaymentScreen />} />
          <Route path={PAYMENT_CONFIRMATION_PATH} element={<PaymentConfirmationScreen />} />
          <Route path={TRIP_WRAP_PATH} element={<TripWrapScreen />} />
          <Route path={TRIP_FEEDBACK_PATH} element={<TripFeedbackScreen />} />
          <Route path={TRIP_FEEDBACK_DONE_PATH} element={<TripFeedbackDoneScreen />} />
          <Route path={ITINERARY_HUB_PATH} element={<ItineraryHubScreen />} />
          <Route path={PROFILE_PATH} element={<ProfileScreen />} />
          <Route path={TRAVEL_MODE_SETTINGS_PATH} element={<TravelModeSettingsScreen />} />
          <Route path={DIETARY_PREFERENCES_PATH} element={<DietaryPreferencesScreen />} />
          <Route path={ACTIVITY_PREFERENCES_PATH} element={<ActivityPreferencesScreen />} />
          <Route path={BUDGET_PACE_PREFERENCES_PATH} element={<BudgetPacePreferencesScreen />} />
          <Route path={TRIP_LIVE_MAP_PATH} element={<TripLiveMapScreen />} />
        </Routes>
      </>
    </BrowserRouter>
  );
}
