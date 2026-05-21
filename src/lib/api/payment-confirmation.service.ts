import type { PaymentConfirmationPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_PAYMENT_CONFIRMATION_PAGE } from "./mock/payment-confirmation.mock";

/**
 * 第九屏 · 支付成功与预订确认单（Figma 1:1303）
 *
 * **后端契约:** `GET /api/travel/:travelId/payment-confirmation?planId=...`
 * 文档：`ENDPOINTS.md` §12.
 */
export async function fetchPaymentConfirmationPage(
  travelId: string,
  planId: string,
): Promise<PaymentConfirmationPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_PAYMENT_CONFIRMATION_PAGE, travelId, planId };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<PaymentConfirmationPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/payment-confirmation?${q.toString()}`,
  );
}
