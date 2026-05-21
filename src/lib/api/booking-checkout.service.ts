import type { BookingCheckoutPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_BOOKING_CHECKOUT_PAGE } from "./mock/booking-checkout.mock";

/**
 * 第六屏 · 预约详情汇总与支付确认（Figma 1:818）
 *
 * **后端契约**
 * - 方法/路径：`GET /api/travel/:travelId/booking-checkout?planId=...`
 * - Path / Query：与第五屏相同
 * - 响应体：{@link BookingCheckoutPageDto}
 * - `venueCards`：场馆预约明细；`rideCard.legs`：叫车段次表格；`paymentPromptText`：底部确认文案
 * - 未配置 `VITE_API_BASE_URL`：合并 {@link MOCK_BOOKING_CHECKOUT_PAGE} 与入参 `travelId`、`planId`
 *
 * **建议错误语义：** `400` / `404` 与 §8 类似
 *
 * 真实支付、扣款请另接支付中台（非本 GET 职责）。
 *
 * 文档：`ENDPOINTS.md` §「Booking checkout」
 */
export async function fetchBookingCheckoutPage(
  travelId: string,
  planId: string,
): Promise<BookingCheckoutPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_BOOKING_CHECKOUT_PAGE, travelId, planId };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<BookingCheckoutPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/booking-checkout?${q.toString()}`,
  );
}
