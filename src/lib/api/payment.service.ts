import type { PaymentPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第七屏 · 费用明细与付款方式（Figma 1:999）
 *
 * **后端契约**
 * - `GET /travel/:travelId/payment?planId=...`
 * - 响应体：{@link PaymentPageDto}
 * - 未配置 `VITE_API_BASE_URL`：抛出配置错误
 *
 * 文档：`ENDPOINTS.md` §「Payment」
 */
export async function fetchPaymentPage(
  travelId: string,
  planId: string,
): Promise<PaymentPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<PaymentPageDto>(
    `/travel/${encodeURIComponent(travelId)}/payment?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
