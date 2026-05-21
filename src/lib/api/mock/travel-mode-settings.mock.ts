import type { TravelModeSettingsPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_TRAVEL_MODE_SETTINGS_PAGE: TravelModeSettingsPageDto = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  navTitle: "出行方式与距离",
  backLabel: "返回",
  methodSectionTitle: "默认出行方式",
  methodOptions: [
    { id: "taxi", label: "打车" },
    { id: "self_drive", label: "自驾" },
    { id: "transit", label: "地铁/公交" },
  ],
  selectedMethodId: "taxi",
  radiusSectionTitle: "默认出行半径",
  radiusValueFormat: "{km}km内",
  radiusSliderMinKm: 1,
  radiusSliderMaxKm: 15,
  radiusSliderStepKm: 1,
  selectedRadiusKm: 5,
  radiusPresets: [
    { id: "r3", label: "3km", valueKm: 3 },
    { id: "r5", label: "5km", valueKm: 5 },
    { id: "r10", label: "10km", valueKm: 10 },
  ],
  durationSectionTitle: "默认出行时长",
  durationOptions: [
    { id: "dur-afternoon", label: "3–4 小时（下午半天）" },
    { id: "dur-short", label: "2 小时内（短暂出行）" },
    { id: "dur-half", label: "半天（4–6 小时）" },
    { id: "dur-full", label: "全天" },
  ],
  selectedDurationId: "dur-afternoon",
  saveButtonLabel: "保存修改",
};
