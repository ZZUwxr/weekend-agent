import { BrowserRouter, Route, Routes } from "react-router-dom";
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

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
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
        <Route path={ITINERARY_HUB_PATH} element={<ItineraryHubScreen />} />
        <Route path={PROFILE_PATH} element={<ProfileScreen />} />
        <Route path={TRAVEL_MODE_SETTINGS_PATH} element={<TravelModeSettingsScreen />} />
        <Route path={DIETARY_PREFERENCES_PATH} element={<DietaryPreferencesScreen />} />
        <Route path={ACTIVITY_PREFERENCES_PATH} element={<ActivityPreferencesScreen />} />
        <Route path={BUDGET_PACE_PREFERENCES_PATH} element={<BudgetPacePreferencesScreen />} />
        <Route path={TRIP_LIVE_MAP_PATH} element={<TripLiveMapScreen />} />
      </Routes>
    </BrowserRouter>
  );
}
