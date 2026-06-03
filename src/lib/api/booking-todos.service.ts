import type { BookingTodosPageDto } from "./types";
import { apiRequest } from "./client";

/**
 * 第五屏 · 行程预约与待办（Figma 1:635）
 *
 * **后端契约**
 * - 方法/路径：`GET /travel/:travelId/booking-todos?planId=...`
 * - Path：`travelId` — 与同会话下 `conversation-page`、`plan-comparison`、`itinerary-timeline` 一致
 * - Query：`planId` — **必填**；与 `TravelPlanCardDto.id` 一致（如 `plan-a`）
 * - 响应体：JSON，结构与 {@link BookingTodosPageDto} 一致；`flow` 数组须**按展示顺序**返回，元素 `id` 在同页内唯一（供前端列表 key）
 * - `flow[].type`：`ai_message` | `user_pill` | `progress_banner` | `todo_card`（见 {@link BookingFlowItemDto}）
 * - 前端封装：`apiRequest`，base 来自 `VITE_API_BASE_URL`（移动端 BFF 根路径）
 * - 未配置 `VITE_API_BASE_URL` 时：抛出配置错误
 *
 * **建议错误语义**
 * - `400`：`planId` 缺失或非法
 * - `404`：`travelId` 不存在，或该会话下暂无预约/待办数据（或尚未生成）
 *
 * 用户点击「需要」「确认」等若需落库，可另增 `POST` 契约（当前页面仅展示接口下发的 `flow`）。
 *
 * 文档：`ENDPOINTS.md` §「Booking todos」
 */
export async function fetchBookingTodosPage(
  travelId: string,
  planId: string,
): Promise<BookingTodosPageDto> {
  assertTravelId(travelId);
  const q = new URLSearchParams({ planId });
  return apiRequest<BookingTodosPageDto>(
    `/travel/${encodeURIComponent(travelId)}/booking-todos?${q.toString()}`,
  );
}

function assertTravelId(travelId: string): void {
  if (!travelId?.trim()) throw new Error("缺少当前行程，请先从首页创建一条行程。");
}
