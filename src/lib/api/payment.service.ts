import type { PaymentPageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_PAYMENT_PAGE } from "./mock/payment.mock";

/**
 * 第七屏 · 费用明细与付款方式（Figma 1:999）
 *
 * **后端契约**
 * - `GET /api/travel/:travelId/payment?planId=...`
 * - 响应体：{@link PaymentPageDto}
 * - 未配置 `VITE_API_BASE_URL`：返回带当前 `travelId` / `planId` 的 mock
 *
 * 文档：`ENDPOINTS.md` §「Payment」
 */
export async function fetchPaymentPage(
  travelId: string,
  planId: string,
): Promise<PaymentPageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 120));
    return { ...MOCK_PAYMENT_PAGE, travelId, planId };
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<PaymentPageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/payment?${q.toString()}`,
  );
}
