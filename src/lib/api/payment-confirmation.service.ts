import type { PaymentConfirmationPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第九屏 · 外部任务确认单（Figma 1:1303）
 *
 * **后端契约:** `GET /travel/:travelId/payment-confirmation?planId=...`
 * 文档：`ENDPOINTS.md` §12.
 */
export async function fetchPaymentConfirmationPage(
  travelId: string,
  planId: string,
): Promise<PaymentConfirmationPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<PaymentConfirmationPageDto>(
    `/travel/${encodeURIComponent(travelId)}/payment-confirmation?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
