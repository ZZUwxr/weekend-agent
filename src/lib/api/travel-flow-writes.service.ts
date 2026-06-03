import { apiRequest } from "./client";
import type {
  BookingTodoActionBody,
  BookingTodoActionResponseDto,
  MobilePlanActionResponseDto,
  TravelFeedbackBody,
  TravelBookingCheckoutConfirmBody,
  TravelExecuteActionBody,
  TravelPaymentSubmitBody,
  TravelPaymentSubmitResponseDto,
  TravelSimpleOkResponseDto,
} from "./types";

/**
 * 行程相关 **写操作**（预订流按钮、支付下单等）。
 * 路径与请求体按 `ENDPOINTS.md` 的移动端 BFF 契约执行。
 */

/** POST /travel/:travelId/booking-todos/actions — 预约待办条上的确认/需要等 */
export async function postBookingTodoAction(
  travelId: string,
  body: BookingTodoActionBody,
): Promise<BookingTodoActionResponseDto> {
  assertTravelId(travelId);
  return apiRequest<BookingTodoActionResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/booking-todos/actions`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** POST /travel/:travelId/booking-checkout/confirm — 预约核对页「确认」类操作 */
export async function postBookingCheckoutConfirm(
  travelId: string,
  body: TravelBookingCheckoutConfirmBody,
): Promise<TravelSimpleOkResponseDto> {
  assertTravelId(travelId);
  return apiRequest<TravelSimpleOkResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/booking-checkout/confirm`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** POST /travel/:travelId/payment/orders — 创建后端支付任务记录 */
export async function postTravelPaymentOrder(
  travelId: string,
  body: TravelPaymentSubmitBody,
): Promise<TravelPaymentSubmitResponseDto> {
  assertTravelId(travelId);
  return apiRequest<TravelPaymentSubmitResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/payment/orders`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** PATCH /travel/:travelId/payment/orders/:orderId/complete — 记录支付确认尝试 */
export async function patchTravelPaymentOrderComplete(
  travelId: string,
  orderId: string,
  planId: string,
): Promise<TravelSimpleOkResponseDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<TravelSimpleOkResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/payment/orders/${encodeURIComponent(orderId)}/complete?${q.toString()}`,
    { method: "PATCH" },
  );
}

/** POST /travel/:travelId/confirm — 确认当前方案，后端进入 confirmed 状态 */
export async function confirmTravelPlan(
  travelId: string,
  planId: string,
): Promise<MobilePlanActionResponseDto> {
  assertTravelId(travelId);
  return apiRequest<MobilePlanActionResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/confirm`,
    {
      method: "POST",
      body: JSON.stringify({ planId }),
    },
  );
}

/** POST /travel/:travelId/execute — 记录预约/叫车/分享执行尝试 */
export async function executeTravelPlan(
  travelId: string,
  planIdOrBody: string | TravelExecuteActionBody,
): Promise<MobilePlanActionResponseDto> {
  assertTravelId(travelId);
  const body = typeof planIdOrBody === "string" ? { planId: planIdOrBody } : planIdOrBody;
  return apiRequest<MobilePlanActionResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/execute`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

/** POST /travel/:travelId/feedback — 保存体验反馈并更新用户记忆 */
export async function submitTravelFeedback(
  travelId: string,
  body: TravelFeedbackBody,
): Promise<MobilePlanActionResponseDto> {
  assertTravelId(travelId);
  return apiRequest<MobilePlanActionResponseDto>(
    `/travel/${encodeURIComponent(travelId)}/feedback`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) {
    throw new Error("缺少当前行程，请先从首页创建一条行程。");
  }
}
