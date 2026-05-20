import type { ItineraryTimelinePageDto } from "./types";
import { getApiBaseUrl } from "./config";
import { MOCK_ITINERARY_TIMELINE } from "./mock/timeline.mock";

/** Mock：按所选方案替换角标与顶部条文案（与第三页 Plan A/B id 对齐） */
function mergeTimelineMockWithPlan(
  base: Omit<ItineraryTimelinePageDto, "travelId" | "planId">,
  travelId: string,
  planId: string,
): ItineraryTimelinePageDto {
  const isB = planId === "plan-b";
  if (!isB) {
    return { ...base, travelId, planId };
  }
  return {
    ...base,
    travelId,
    planId,
    planPillLabel: "Plan B",
    aiStatusMessage: "您已确认Plan B，正在生成Plan B 的详细时间轴＆路线…",
  };
}

/**
 * 第四屏 · 已选方案详细时间轴与路线（Figma 1:465）
 *
 * **后端契约**
 * - 方法/路径：`GET /api/travel/:travelId/itinerary-timeline?planId=...`
 * - Path：`travelId` — 与 `conversation-page`、`plan-comparison` 使用同一会话 id
 * - Query：`planId` — **必填**；与双方案页 `TravelPlanCardDto.id` 一致（如 `plan-a`、`plan-b`）
 * - 响应体：JSON，结构与 {@link ItineraryTimelinePageDto} 一致（字段名请与类型对齐）
 * - 前端封装：`apiRequest`，base 来自环境变量 `VITE_API_BASE_URL`（仅 origin，不含 path）
 * - 未配置 `VITE_API_BASE_URL` 时：不请求网络，返回 {@link MOCK_ITINERARY_TIMELINE} 与入参 `travelId`、`planId` 的合并结果
 *
 * **建议错误语义**
 * - `404`：`travelId` 不存在，或该会话下没有 `planId` 对应方案 / 尚未生成时间轴
 * - `400`：`planId` 缺失或非法
 *
 * 文档：`ENDPOINTS.md` §「Itinerary timeline」
 */
export async function fetchItineraryTimelinePage(
  travelId: string,
  planId: string,
): Promise<ItineraryTimelinePageDto> {
  const base = getApiBaseUrl();
  if (!base) {
    await new Promise((r) => setTimeout(r, 140));
    return mergeTimelineMockWithPlan(MOCK_ITINERARY_TIMELINE, travelId, planId);
  }
  const { apiRequest } = await import("./client");
  const q = new URLSearchParams({ planId });
  return apiRequest<ItineraryTimelinePageDto>(
    `/api/travel/${encodeURIComponent(travelId)}/itinerary-timeline?${q.toString()}`,
  );
}
