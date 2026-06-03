import type { BookingCheckoutPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第六屏 · 预约详情汇总与支付确认（Figma 1:818）
 *
 * **后端契约**
 * - 方法/路径：`GET /travel/:travelId/booking-checkout?planId=...`
 * - Path / Query：与第五屏相同
 * - 响应体：{@link BookingCheckoutPageDto}
 * - `venueCards`：场馆预约明细；`rideCard.legs`：叫车段次表格；`paymentPromptText`：底部确认文案
 * - 未配置 `VITE_API_BASE_URL`：抛出配置错误
 *
 * **建议错误语义：** `400` / `404` 与 §8 类似
 *
 * 真实支付、预约、叫车 provider 本轮未接入；写接口会记录待处理任务。
 *
 * 文档：`ENDPOINTS.md` §「Booking checkout」
 */
export async function fetchBookingCheckoutPage(
  travelId: string,
  planId: string,
): Promise<BookingCheckoutPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<BookingCheckoutPageDto>(
    `/travel/${encodeURIComponent(travelId)}/booking-checkout?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
