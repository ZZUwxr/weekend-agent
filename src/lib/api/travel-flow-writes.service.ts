import { getApiBaseUrl } from "./config";
import type {
  BookingTodoActionBody,
  BookingTodoActionResponseDto,
  TravelBookingCheckoutConfirmBody,
  TravelPaymentSubmitBody,
  TravelPaymentSubmitResponseDto,
  TravelSimpleOkResponseDto,
} from "./types";

/**
 * 行程相关 **写操作**（预订流按钮、支付下单等）。
 * 未配置 `VITE_API_BASE_URL` 时均立即 `{ ok: true }`，不阻塞 UI。
 *
 * 路径与请求体可与后端协商后微调，保持类型与页面入参一致即可。
 */

/** POST /api/travel/:travelId/booking-todos/actions — 预约待办条上的确认/需要等 */
export async function postBookingTodoAction(
  travelId: string,
  body: BookingTodoActionBody,
): Promise<BookingTodoActionResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return { ok: true };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<BookingTodoActionResponseDto>(
    `/api/travel/${encodeURIComponent(travelId)}/booking-todos/actions`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** POST /api/travel/:travelId/booking-checkout/confirm — 预约核对页「确认」类操作 */
export async function postBookingCheckoutConfirm(
  travelId: string,
  body: TravelBookingCheckoutConfirmBody,
): Promise<TravelSimpleOkResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return { ok: true };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<TravelSimpleOkResponseDto>(
    `/api/travel/${encodeURIComponent(travelId)}/booking-checkout/confirm`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** POST /api/travel/:travelId/payment/orders — 发起支付单（返回收银台 URL 等） */
export async function postTravelPaymentOrder(
  travelId: string,
  body: TravelPaymentSubmitBody,
): Promise<TravelPaymentSubmitResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return { ok: true, orderId: "mock-order" };
  }
  const { apiRequest } = await import("./client");
  return apiRequest<TravelPaymentSubmitResponseDto>(
    `/api/travel/${encodeURIComponent(travelId)}/payment/orders`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** PATCH /api/travel/:travelId/payment/orders/:orderId/complete — 前端轮询或同步获知支付成功后的确认（可选） */
export async function patchTravelPaymentOrderComplete(
  travelId: string,
  orderId: string,
  planId: string,
): Promise<TravelSimpleOkResponseDto> {
  const base = getApiBaseUrl();
  if (!base) {
    return { ok: true };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<TravelSimpleOkResponseDto>(
    `/api/travel/${encodeURIComponent(travelId)}/payment/orders/${encodeURIComponent(orderId)}/complete?${q.toString()}`,
    { method: "PATCH" },
  );
}
