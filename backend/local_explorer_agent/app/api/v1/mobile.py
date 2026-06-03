"""Mobile BFF API routes.

Provides page-level DTOs for the phone frontend, backed by the existing
PlanService and domain models.  No new business logic -- purely presentation.
"""

from __future__ import annotations

import re
import json
import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from local_explorer_agent.app.api.deps import (
    get_execution_service,
    get_feedback_service,
    get_mobile_state_repository,
    get_poi_query_tool,
    get_poi_tool,
    get_plan_service,
    get_queue_tool,
    get_route_tool,
    get_session_store,
    get_user_memory_repository,
    get_weather_tool,
)
from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.openai_client import OpenAICompatibleLLMClient
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.llm_decider import LLMReActDecider
from local_explorer_agent.app.agent.react.mock_decider import MockReActDecider
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.memory import UserMemoryCompanion
from local_explorer_agent.app.mobile.presenter import (
    present_booking_checkout,
    present_booking_todos,
    present_conversation_page,
    present_itinerary_hub,
    present_payment_confirmation,
    present_payment_page,
    present_plan_comparison,
    present_timeline_page,
    present_trip_live_map,
)
from local_explorer_agent.app.mobile.presets import (
    ACTIVITY_PREFERENCES,
    BUDGET_PACE_PREFERENCES,
    DIETARY_PREFERENCES,
    HOME_DASHBOARD,
    PROFILE_PAGE,
    TRAVEL_MODE_SETTINGS,
)
from local_explorer_agent.app.mobile.schemas import (
    ActiveTravelDto,
    ActivityPreferencesPageDto,
    BookingCheckoutPageDto,
    BookingTodosPageDto,
    BudgetPacePreferencesPageDto,
    BookingTodoActionResponseDto,
    CompanionProfileDto,
    CompanionProfileListDto,
    CompanionProfileSaveBody,
    CompanionProfileSaveResponseDto,
    DietaryPreferencesPageDto,
    HomeDashboardDto,
    HomeHistoryItemDto,
    ItineraryHubHistoryItemDto,
    ItineraryHubPageDto,
    ItineraryTimelinePageDto,
    LLMSettingsDto,
    MobileExecutionTaskDto,
    MobilePlanActionResponseDto,
    MobileRevisionResponse,
    PaymentConfirmationPageDto,
    PaymentPageDto,
    PlanComparisonPageDto,
    PlanPatchDto,
    ProfilePageDto,
    SaveLLMSettingsBody,
    StartTravelSessionBody,
    StartTravelSessionResponse,
    TravelConversationPageDto,
    TravelModeSettingsPageDto,
    TravelPaymentSubmitResponseDto,
    TravelSimpleOkResponseDto,
    UserPreferenceSaveResponseDto,
    TripLiveMapPageDto,
)
from local_explorer_agent.app.repositories.mobile_state_repository import (
    MobileStateRepository,
)
from local_explorer_agent.app.repositories.user_memory_repository import (
    UserMemoryRepository,
)
from local_explorer_agent.app.services.execution_service import ExecutionService
from local_explorer_agent.app.services.feedback_service import FeedbackService
from local_explorer_agent.app.services.plan_service import PlanService
from local_explorer_agent.app.domain.enums import EventType, PlanState
from local_explorer_agent.app.domain.models import PlanEvent
from local_explorer_agent.app.domain.schemas import PlanPreviewStreamEvent
from local_explorer_agent.app.core.exceptions import classify_llm_error

router = APIRouter(prefix="/mobile", tags=["mobile"])

_KNOWN_CITIES = ["深圳", "北京", "上海", "广州", "杭州", "成都"]
_DEFAULT_MOBILE_USER_ID = "phone_user"
_DEVICE_USER_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")
_INTERNAL_REVISION_WARNING_MARKERS = (
    "violation_type",
    "suggested_repair_action",
    "affected_poi_id",
    "affected_plan_id",
    "planned",
    "api_key",
    "traceback",
    "schema",
    "provider",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _infer_city(message: str) -> str:
    for city in _KNOWN_CITIES:
        if city in message:
            return city
    return "深圳"


def _infer_duration_minutes(message: str) -> int:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(个)?小时", message)
    if m:
        return min(720, max(60, round(float(m.group(1)) * 60)))
    if "半天" in message:
        return 240
    if "一整天" in message or "全天" in message:
        return 480
    return 240


def _infer_start_time(message: str, now: datetime) -> datetime:
    if "今晚" in message or "晚上" in message:
        target = now.replace(hour=19, minute=0, second=0, microsecond=0)
    elif "下午" in message:
        target = now.replace(hour=14, minute=0, second=0, microsecond=0)
    elif "中午" in message or "午饭" in message:
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        return now + timedelta(minutes=30)
    if target <= now:
        return target + timedelta(days=1)
    return target


def _norm_plan_id(plan_id: str | None, default: str = "plan_a") -> str:
    """Convert frontend ``plan-a`` to backend ``plan_a``."""
    return (plan_id or default).replace("-", "_")


def _resolve_plan_id(
    plan_id: str | None,
    legacy_plan_id: str | None,
    default: str = "plan_a",
) -> str:
    return _norm_plan_id(plan_id or legacy_plan_id, default=default)


def _dict_value(data: dict, *keys: str, default=None):
    for key in keys:
        if key in data:
            return data[key]
    return default


def _list_value(data: dict, *keys: str) -> list:
    value = _dict_value(data, *keys, default=[])
    return value if isinstance(value, list) else []


def _ok_with_timestamp(updated_at: str | None = None) -> UserPreferenceSaveResponseDto:
    return UserPreferenceSaveResponseDto(
        ok=True,
        updated_at=updated_at or datetime.now(timezone.utc).isoformat(),
    )


def _mobile_user_id(
    x_device_user_id: Annotated[str | None, Header(alias="X-Device-User-Id")] = None,
) -> str:
    user_id = (x_device_user_id or _DEFAULT_MOBILE_USER_ID).strip() or _DEFAULT_MOBILE_USER_ID
    if (
        not _DEVICE_USER_ID_RE.fullmatch(user_id)
        or "/" in user_id
        or "\\" in user_id
        or ".." in user_id
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_device_user_id",
                "message": "X-Device-User-Id 格式不合法。",
                "details": {"header": "X-Device-User-Id"},
            },
        )
    return user_id


def _build_preview_request(body: StartTravelSessionBody, user_id: str):
    from local_explorer_agent.app.domain.schemas import PlanPreviewRequest

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return PlanPreviewRequest(
        user_id=(body.user_id or user_id or _DEFAULT_MOBILE_USER_ID).strip(),
        query=body.message,
        city=_infer_city(body.message),
        start_time=_infer_start_time(body.message, now),
        duration_minutes=_infer_duration_minutes(body.message),
        companion_ids=[
            str(item).strip()
            for item in body.companion_ids
            if str(item).strip() and str(item).strip() != "self"
        ],
    )


def _active_travel_dto(active: dict | None) -> ActiveTravelDto:
    if not active:
        return ActiveTravelDto()
    return ActiveTravelDto(
        travel_id=active.get("travel_id"),
        plan_id=active.get("plan_id"),
        state=active.get("state"),
        updated_at=active.get("updated_at"),
    )


def _provider_pending_action_response(action: dict) -> TravelSimpleOkResponseDto:
    return TravelSimpleOkResponseDto(
        ok=False,
        status=str(action.get("status") or "pending_provider"),
        code=str(action.get("code") or "provider_unavailable"),
        message=str(action.get("message") or "外部服务暂未接入，已在后端记录为待处理任务。"),
    )


def _mark_active_travel(
    state_repo: MobileStateRepository,
    user_id: str,
    *,
    session_id: str,
    plan_id: str | None,
    state: str | None,
) -> None:
    state_repo.set_active_travel(
        user_id,
        travel_id=session_id,
        plan_id=plan_id,
        state=state,
    )


def _stream_mobile_events(
    runner: Callable[[Callable[[PlanPreviewStreamEvent], None]], object],
) -> StreamingResponse:
    queue: asyncio.Queue[PlanPreviewStreamEvent | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    error_emitted = False

    def emit(event: PlanPreviewStreamEvent) -> None:
        nonlocal error_emitted
        if event.event == "error":
            error_emitted = True
        loop.call_soon_threadsafe(queue.put_nowait, event)

    async def run_preview() -> None:
        try:
            await asyncio.to_thread(runner, emit)
        except Exception as exc:
            if not error_emitted:
                _status_code, code, message = classify_llm_error(exc)
                emit(PlanPreviewStreamEvent(
                    event="error",
                    data={
                        "step": None,
                        "code": code,
                        "message": message,
                        "error": message,
                    },
                ))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    async def event_generator() -> AsyncIterator[str]:
        task = asyncio.create_task(run_preview())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _format_sse_event(event)
        finally:
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _format_sse_event(event: PlanPreviewStreamEvent) -> str:
    data = json.dumps(_mobile_safe_stream_data(event), ensure_ascii=False, default=str)
    return f"event: {event.event}\ndata: {data}\n\n"


def _mobile_safe_stream_data(event: PlanPreviewStreamEvent) -> dict:
    data = dict(event.data)
    label = _mobile_stream_label(event.event, data)
    if label:
        data["mobile_label"] = label
    for key in ("summary", "decision_summary", "message", "label"):
        if key in data and _looks_internal_stream_text(str(data[key])):
            data.pop(key, None)
    return data


def _mobile_stream_label(event_name: str, data: dict) -> str:
    text = " ".join(
        str(data.get(key) or "")
        for key in ("tool_name", "tool", "name", "action_type", "summary", "decision_summary")
    )
    if event_name == "plan_complete":
        return "方案已经整理好，正在准备可确认的页面..."
    if "score" in text or "recommend" in text or "评分" in text or "推荐" in text:
        return "正在给候选方案打分，找出更稳的一条..."
    if "route" in text or "timeline" in text or "路线" in text or "时间轴" in text:
        return "正在比较路线、转场时间和缓冲空间..."
    if (
        "poi" in text
        or "place" in text
        or "weather" in text
        or "queue" in text
        or "地点" in text
        or "天气" in text
    ):
        return "正在筛选附近适合的地点和备选安排..."
    if (
        "conflict" in text
        or "constraint" in text
        or "validate" in text
        or "约束" in text
        or "冲突" in text
    ):
        return "正在检查预算、体力、饮食和天气等约束..."
    if (
        "understand" in text
        or "intent" in text
        or "intake" in text
        or "clarification" in text
        or "理解" in text
    ):
        return "正在理解同行人、出发时间和这次出门的重点..."
    return "正在把规划结果整理成可继续修改的方案..."


def _looks_internal_stream_text(text: str) -> bool:
    lower = text.lower()
    return (
        bool(re.search(r"[a-z]+_[a-z_]+", text))
        or bool(re.search(r"规则\s*\d+", text))
        or "当前状态" in text
        or "数据字段" in text
        or "tool_name" in lower
        or "function" in lower
        or "调用工具" in text
    )


# ---------------------------------------------------------------------------
# Travel session & pages
# ---------------------------------------------------------------------------


@router.post("/travel/sessions", response_model=StartTravelSessionResponse)
def start_session(
    body: StartTravelSessionBody,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> StartTravelSessionResponse:
    request = _build_preview_request(body, user_id)
    service = _plan_service_for_user_llm_config(state_repo, user_id) or service
    plan = service.preview_plan(request)
    state_repo.record_plan(user_id, plan, plan_id=plan.recommended_plan_id)
    return StartTravelSessionResponse(travel_id=plan.session_id)


@router.post("/travel/sessions/stream")
async def start_session_stream(
    body: StartTravelSessionBody,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> StreamingResponse:
    request = _build_preview_request(body, user_id)
    runtime_service = _plan_service_for_user_llm_config(state_repo, user_id) or service

    def run(emit: Callable[[PlanPreviewStreamEvent], None]) -> None:
        plan = runtime_service.preview_plan(request, event_callback=emit)
        state_repo.record_plan(user_id, plan, plan_id=plan.recommended_plan_id)
        emit(PlanPreviewStreamEvent(
            event="plan_complete",
            data={
                "session_id": plan.session_id,
                "travel_id": plan.session_id,
                "state": plan.state,
                "recommended_plan_id": plan.recommended_plan_id,
                "candidates_count": len(plan.plan_candidates),
            },
        ))

    return _stream_mobile_events(run)


@router.get(
    "/travel/{session_id}/conversation-page",
    response_model=TravelConversationPageDto,
)
def get_conversation_page(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> TravelConversationPageDto:
    plan = service.get_plan(session_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=plan.recommended_plan_id,
        state=str(plan.state),
    )
    return present_conversation_page(plan)


@router.get(
    "/travel/{session_id}/plan-comparison",
    response_model=PlanComparisonPageDto,
)
def get_plan_comparison(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> PlanComparisonPageDto:
    plan = service.get_plan(session_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=plan.recommended_plan_id,
        state=str(plan.state),
    )
    return present_plan_comparison(plan)


@router.get(
    "/travel/{session_id}/itinerary-timeline",
    response_model=ItineraryTimelinePageDto,
)
def get_timeline(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> ItineraryTimelinePageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_timeline_page(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/booking-todos",
    response_model=BookingTodosPageDto,
)
def get_booking_todos(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> BookingTodosPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_booking_todos(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/booking-checkout",
    response_model=BookingCheckoutPageDto,
)
def get_booking_checkout(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> BookingCheckoutPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_booking_checkout(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/payment",
    response_model=PaymentPageDto,
)
def get_payment(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> PaymentPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_payment_page(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/payment-confirmation",
    response_model=PaymentConfirmationPageDto,
)
def get_payment_confirmation(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> PaymentConfirmationPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_payment_confirmation(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/trip-live-map",
    response_model=TripLiveMapPageDto,
)
def get_trip_live_map(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> TripLiveMapPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    return present_trip_live_map(plan, resolved_plan_id)


@router.get(
    "/travel/{session_id}/itinerary-hub",
    response_model=ItineraryHubPageDto,
)
def get_itinerary_hub(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
    legacy_plan_id: Annotated[str | None, Query(alias="plan_id")] = None,
) -> ItineraryHubPageDto:
    plan = service.get_plan(session_id)
    resolved_plan_id = _resolve_plan_id(plan_id, legacy_plan_id)
    _mark_active_travel(
        state_repo,
        user_id,
        session_id=session_id,
        plan_id=resolved_plan_id,
        state=str(plan.state),
    )
    page = present_itinerary_hub(plan, resolved_plan_id)
    page.history_items = [
        _history_to_hub_item(item)
        for item in state_repo.list_history(user_id)
        if item.get("travel_id") != session_id
    ][:10]
    return page


@router.get("/travel/active", response_model=ActiveTravelDto)
def get_active_travel(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> ActiveTravelDto:
    return _active_travel_dto(state_repo.get_active_travel(user_id))


# ---------------------------------------------------------------------------
# Action endpoints (clarify / revise)
# ---------------------------------------------------------------------------


@router.post(
    "/travel/{session_id}/clarifications",
    response_model=TravelConversationPageDto,
)
def answer_clarifications(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> TravelConversationPageDto:
    from local_explorer_agent.app.domain.schemas import (
        ClarificationAnswer,
        ClarificationAnswerRequest,
    )

    raw_answers = body.get("answers", [])
    request = ClarificationAnswerRequest(
        answers=[
            ClarificationAnswer(
                question_id=_dict_value(a, "question_id", "questionId"),
                answer=a["answer"],
            )
            for a in raw_answers
        ]
    )
    try:
        plan = service.answer_clarifications(session_id, request)
    except ValueError as e:
        if str(e) == "Plan is not waiting for clarification":
            plan = service.get_plan(session_id)
            state_repo.record_plan(user_id, plan, plan_id=plan.recommended_plan_id)
            return present_conversation_page(plan)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "clarification_conflict",
                "message": str(e),
                "details": {"travel_id": session_id},
            },
        ) from e
    state_repo.record_plan(user_id, plan, plan_id=plan.recommended_plan_id)
    return present_conversation_page(plan)


@router.post(
    "/travel/{session_id}/revise",
    response_model=MobileRevisionResponse,
)
def revise_plan(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> MobileRevisionResponse:
    from local_explorer_agent.app.domain.schemas import PlanRevisionRequest

    plan = service.get_plan(session_id)
    target_plan_id = _dict_value(body, "target_plan_id", "targetPlanId")
    normalized_target_plan_id = _norm_plan_id(target_plan_id)

    if plan.state not in {PlanState.PREVIEW, PlanState.REVISING}:
        message = str(body.get("message", "")).strip() or "用户补充了行程偏好"
        event = PlanEvent(
            session_id=session_id,
            event_type=EventType.USER_PREFERENCE_CHANGE,
            payload={
                "message": message,
                "source": "mobile_revise",
                "target_plan_id": normalized_target_plan_id,
            },
        )
        updated = service.handle_event(session_id, event)
        state_repo.record_plan(
            user_id,
            updated,
            plan_id=normalized_target_plan_id,
            status=str(updated.state),
        )
        return _mobile_revision_response(
            updated,
            summary=updated.replan_reason or "已根据当前行程状态记录你的补充。",
            plan_id=normalized_target_plan_id,
        )

    request = PlanRevisionRequest(
        message=body.get("message", ""),
        target_plan_id=target_plan_id,
        locked_items=_dict_value(body, "locked_items", "lockedItems", default=[]),
        revision_mode=_dict_value(body, "revision_mode", "revisionMode", default="partial"),
    )
    try:
        result = service.revise_plan(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    state_repo.record_plan(
        user_id,
        result.plan,
        plan_id=normalized_target_plan_id,
        status=str(result.plan.state),
    )
    return _mobile_revision_response(
        result.plan,
        summary=result.revision.summary,
        plan_id=normalized_target_plan_id,
        patches=[
            PlanPatchDto(
                patch_id=p.patch_id,
                patch_type=p.patch_type,
                target_plan_id=p.target_plan_id,
                target_stage_id=p.target_stage_id,
                old_value=p.old_value,
                new_value=p.new_value,
                reason=p.reason,
            )
            for p in result.revision.patches
        ],
        warnings=result.revision.warnings,
    )


@router.post(
    "/travel/{session_id}/confirm",
    response_model=MobilePlanActionResponseDto,
)
def confirm_travel_plan(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> MobilePlanActionResponseDto:
    plan_id = _dict_value(body, "plan_id", "planId", default=None)
    plan = service.confirm_plan(session_id)
    state_repo.record_plan(user_id, plan, plan_id=plan_id or plan.recommended_plan_id)
    return MobilePlanActionResponseDto(
        ok=True,
        travel_id=plan.session_id,
        state=str(plan.state),
        message="方案已确认，后续支付/执行会基于当前方案进行。",
    )


@router.post(
    "/travel/{session_id}/execute",
    response_model=MobilePlanActionResponseDto,
)
def execute_travel_plan(
    session_id: str,
    body: dict,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> MobilePlanActionResponseDto:
    plan_id = _dict_value(body, "plan_id", "planId", default=None)
    requested_action = str(_dict_value(body, "action", "actionType", default="execute_plan") or "execute_plan")
    action_type = re.sub(r"[^A-Za-z0-9_.-]+", "_", requested_action).strip("._-") or "execute_plan"
    action = state_repo.record_action(
        user_id,
        session_id=session_id,
        plan_id=plan_id,
        action_type=action_type,
        payload=body,
        message=_provider_action_message(action_type),
    )
    plan = service.session_store.get(session_id)
    state_repo.record_plan(user_id, plan, plan_id=plan_id or plan.recommended_plan_id)
    return MobilePlanActionResponseDto(
        ok=False,
        travel_id=plan.session_id,
        state=str(plan.state),
        message=str(action["message"]),
        tasks=[
            MobileExecutionTaskDto(
                task_id=str(action["action_id"]),
                action=str(action["action_type"]),
                status=str(action["status"]),
                result={
                    "code": action["code"],
                    "message": action["message"],
                },
            )
        ],
    )


def _provider_action_message(action_type: str) -> str:
    labels = {
        "execute_plan": "预约、叫车和分享第三方服务暂未接入，已记录为待执行任务。",
        "share_itinerary": "分享服务暂未接入，已记录为待处理分享任务。",
        "calendar_reminder": "日历服务暂未接入，已记录为待处理提醒任务。",
        "schedule_reminder": "提醒服务暂未接入，已记录为待处理提醒任务。",
        "call_ride": "叫车服务暂未接入，已记录为待处理叫车任务。",
        "navigation": "导航服务暂未接入，已记录为待处理导航任务。",
        "cancel_trip": "取消服务暂未接入，已记录为待处理取消任务。",
    }
    return labels.get(action_type, "外部服务暂未接入，已在后端记录为待处理任务。")


@router.post(
    "/travel/{session_id}/feedback",
    response_model=MobilePlanActionResponseDto,
)
def submit_travel_feedback(
    session_id: str,
    body: dict,
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> MobilePlanActionResponseDto:
    from local_explorer_agent.app.domain.schemas import FeedbackRequest

    response = service.submit_feedback(
        session_id,
        FeedbackRequest(
            rating=body.get("rating"),
            raw_feedback=str(_dict_value(body, "raw_feedback", "rawFeedback", default="")),
            tags=list(body.get("tags") or []),
            payload=dict(body.get("payload") or {}),
        ),
    )
    feedback_id = str(response.saved_feedback.get("feedback_id") or "")
    state_repo.record_feedback(
        user_id,
        session_id=session_id,
        rating=body.get("rating"),
        raw_feedback=str(_dict_value(body, "raw_feedback", "rawFeedback", default="")),
        tags=list(body.get("tags") or []),
        feedback_id=feedback_id,
    )
    return MobilePlanActionResponseDto(
        ok=response.success,
        travel_id=response.session_id,
        state="feedback",
        message="反馈已保存，并会用于之后的出行偏好。",
        feedback_id=feedback_id,
    )


# ---------------------------------------------------------------------------
# Static / preset endpoints
# ---------------------------------------------------------------------------


@router.get("/home/dashboard", response_model=HomeDashboardDto)
def get_home_dashboard(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> HomeDashboardDto:
    page = HOME_DASHBOARD.model_copy(deep=True)
    page.companion_options = [
        *_self_home_companion_options(),
        *[
            _companion_to_home_option(companion)
            for companion in memory_repo.list_companions(user_id)
        ],
    ]
    page.history = [
        _history_to_home_item(item)
        for item in state_repo.list_history(user_id)
    ][:8]
    return page


@router.get("/user/profile", response_model=ProfilePageDto)
def get_user_profile(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> ProfilePageDto:
    page = PROFILE_PAGE.model_copy(deep=True)
    travel_mode = state_repo.get_preference(user_id, "travel_mode")
    dietary = state_repo.get_preference(user_id, "dietary")
    activity = state_repo.get_preference(user_id, "activity")
    budget_pace = state_repo.get_preference(user_id, "budget_pace")
    companions = memory_repo.list_companions(user_id)
    page.user_name = ""
    page.avatar_emoji = None
    page.avatar_image_url = None
    page.archive_section_title = "同行人出行档案"
    page.archive_edit_label = "管理"
    page.archive_tags = [_companion_to_archive_tag(companion) for companion in companions]
    page.preference_rows = [
        row.model_copy(update={"summary": _travel_mode_summary(travel_mode)})
        if row.kind == "car" else
        row.model_copy(update={"summary": _dietary_summary(dietary)})
        if row.kind == "food" else
        row.model_copy(update={"summary": _activity_summary(activity)})
        if row.kind == "activity" else
        row.model_copy(update={"summary": _budget_pace_summary(budget_pace)})
        if row.kind == "budget" else row
        for row in page.preference_rows
    ]
    history = state_repo.list_history(user_id)
    if history:
        page.templates = [
            t.model_copy(update={"usage_badge": f"使用 {len(history)} 次"})
            if index == 0 else t
            for index, t in enumerate(page.templates)
        ]
        latest = history[0]
        page.memory_rows = [
            row.model_copy(update={"label": f"上次反馈：{latest.get('last_feedback') or '暂无文字反馈'}"})
            if row.kind == "last_feedback" else row
            for row in page.memory_rows
        ]
    return page


@router.get("/user/companions", response_model=CompanionProfileListDto)
def list_user_companions(
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> CompanionProfileListDto:
    return CompanionProfileListDto(
        status_bar_image_url=PROFILE_PAGE.status_bar_image_url,
        companions=[
            _companion_to_profile(companion)
            for companion in memory_repo.list_companions(user_id)
        ],
    )


@router.post("/user/companions", response_model=CompanionProfileSaveResponseDto)
def create_user_companion(
    body: CompanionProfileSaveBody,
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> CompanionProfileSaveResponseDto:
    companion = _body_to_companion(body, companion_id=f"comp_{uuid4().hex[:10]}")
    saved = memory_repo.upsert_companion(user_id, companion)
    return CompanionProfileSaveResponseDto(
        ok=True,
        companion=_companion_to_profile(saved),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.put("/user/companions/{companion_id}", response_model=CompanionProfileSaveResponseDto)
def update_user_companion(
    companion_id: str,
    body: CompanionProfileSaveBody,
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> CompanionProfileSaveResponseDto:
    companion = _body_to_companion(body, companion_id=companion_id)
    saved = memory_repo.upsert_companion(user_id, companion)
    return CompanionProfileSaveResponseDto(
        ok=True,
        companion=_companion_to_profile(saved),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.delete("/user/companions/{companion_id}", response_model=UserPreferenceSaveResponseDto)
def delete_user_companion(
    companion_id: str,
    memory_repo: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    deleted = memory_repo.delete_companion(user_id, companion_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Companion not found")
    return _ok_with_timestamp()


@router.get("/user/settings/llm", response_model=LLMSettingsDto)
def get_llm_settings(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> LLMSettingsDto:
    settings = get_settings()
    saved = state_repo.get_preference(user_id, "llm")
    api_key = str(saved.get("api_key") or "").strip()
    return LLMSettingsDto(
        status_bar_image_url=PROFILE_PAGE.status_bar_image_url,
        provider=str(saved.get("provider") or settings.llm_provider),
        model=str(saved.get("model") or settings.llm_model),
        base_url=str(saved.get("base_url") or settings.llm_base_url),
        api_key_configured=bool(api_key or settings.effective_llm_api_key),
        api_key_preview=_api_key_preview(api_key or settings.effective_llm_api_key),
    )


@router.put("/user/settings/llm", response_model=UserPreferenceSaveResponseDto)
def save_llm_settings(
    body: SaveLLMSettingsBody,
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    provider = "openai" if body.provider == "openai" else "mock"
    existing = state_repo.get_preference(user_id, "llm")
    api_key = (body.api_key or "").strip()
    payload = {
        "provider": provider,
        "model": body.model.strip(),
        "base_url": body.base_url.strip(),
    }
    if api_key:
        payload["api_key"] = api_key
    elif existing.get("api_key"):
        payload["api_key"] = existing.get("api_key")
    updated_at = state_repo.save_preference(user_id, "llm", payload)
    return _ok_with_timestamp(updated_at)


@router.get("/user/preferences/travel-mode", response_model=TravelModeSettingsPageDto)
def get_travel_mode(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> TravelModeSettingsPageDto:
    saved = state_repo.get_preference(user_id, "travel_mode")
    return TRAVEL_MODE_SETTINGS.model_copy(update={
        "selected_method_id": saved.get("selected_method_id")
        or saved.get("selectedMethodId")
        or TRAVEL_MODE_SETTINGS.selected_method_id,
        "selected_radius_km": saved.get("selected_radius_km")
        or saved.get("selectedRadiusKm")
        or TRAVEL_MODE_SETTINGS.selected_radius_km,
        "selected_duration_id": saved.get("selected_duration_id")
        or saved.get("selectedDurationId")
        or TRAVEL_MODE_SETTINGS.selected_duration_id,
    })


@router.put("/user/preferences/travel-mode", response_model=UserPreferenceSaveResponseDto)
def save_travel_mode(
    body: dict,
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    updated_at = state_repo.save_preference(user_id, "travel_mode", {
        "selected_method_id": _dict_value(body, "selected_method_id", "selectedMethodId"),
        "selected_radius_km": _dict_value(body, "selected_radius_km", "selectedRadiusKm"),
        "selected_duration_id": _dict_value(body, "selected_duration_id", "selectedDurationId"),
    })
    return _ok_with_timestamp(updated_at)


@router.get("/user/preferences/dietary", response_model=DietaryPreferencesPageDto)
def get_dietary(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> DietaryPreferencesPageDto:
    saved = state_repo.get_preference(user_id, "dietary")
    return DIETARY_PREFERENCES.model_copy(update={
        "selected_need_ids": saved.get("selected_need_ids")
        or saved.get("selectedNeedIds")
        or DIETARY_PREFERENCES.selected_need_ids,
    })


@router.put("/user/preferences/dietary", response_model=UserPreferenceSaveResponseDto)
def save_dietary(
    body: dict,
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    updated_at = state_repo.save_preference(user_id, "dietary", {
        "selected_need_ids": _dict_value(body, "selected_need_ids", "selectedNeedIds", default=[]),
        "allergen_note": _dict_value(body, "allergen_note", "allergenNote", default=""),
    })
    return _ok_with_timestamp(updated_at)


@router.get("/user/preferences/activity", response_model=ActivityPreferencesPageDto)
def get_activity(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> ActivityPreferencesPageDto:
    saved = state_repo.get_preference(user_id, "activity")
    return ACTIVITY_PREFERENCES.model_copy(update={
        "selected_tag_ids": saved.get("selected_tag_ids")
        or saved.get("selectedTagIds")
        or ACTIVITY_PREFERENCES.selected_tag_ids,
    })


@router.put("/user/preferences/activity", response_model=UserPreferenceSaveResponseDto)
def save_activity(
    body: dict,
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    updated_at = state_repo.save_preference(user_id, "activity", {
        "selected_tag_ids": _dict_value(body, "selected_tag_ids", "selectedTagIds", default=[]),
    })
    return _ok_with_timestamp(updated_at)


@router.get("/user/preferences/budget-pace", response_model=BudgetPacePreferencesPageDto)
def get_budget_pace(
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> BudgetPacePreferencesPageDto:
    saved = state_repo.get_preference(user_id, "budget_pace")
    return BUDGET_PACE_PREFERENCES.model_copy(update={
        "selected_budget_id": saved.get("selected_budget_id")
        or saved.get("selectedBudgetId")
        or BUDGET_PACE_PREFERENCES.selected_budget_id,
        "selected_pace_id": saved.get("selected_pace_id")
        or saved.get("selectedPaceId")
        or BUDGET_PACE_PREFERENCES.selected_pace_id,
    })


@router.put("/user/preferences/budget-pace", response_model=UserPreferenceSaveResponseDto)
def save_budget_pace(
    body: dict,
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> UserPreferenceSaveResponseDto:
    updated_at = state_repo.save_preference(user_id, "budget_pace", {
        "selected_budget_id": _dict_value(body, "selected_budget_id", "selectedBudgetId"),
        "selected_pace_id": _dict_value(body, "selected_pace_id", "selectedPaceId"),
    })
    return _ok_with_timestamp(updated_at)


@router.post(
    "/travel/{session_id}/booking-todos/actions",
    response_model=BookingTodoActionResponseDto,
)
def post_booking_todo_action(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> BookingTodoActionResponseDto:
    service.get_plan(session_id)
    action = state_repo.record_action(
        user_id,
        session_id=session_id,
        plan_id=_dict_value(body, "plan_id", "planId"),
        action_type="booking_todo_action",
        payload=body,
    )
    return BookingTodoActionResponseDto(
        ok=False,
        booking_todos_page_url=f"/travel/{session_id}/booking-todos",
        status=str(action["status"]),
        code=str(action["code"]),
        message=str(action["message"]),
    )


@router.post(
    "/travel/{session_id}/booking-checkout/confirm",
    response_model=TravelSimpleOkResponseDto,
)
def post_booking_checkout_confirm(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> TravelSimpleOkResponseDto:
    plan = service.confirm_plan(session_id)
    plan_id = _dict_value(body, "plan_id", "planId", default=plan.recommended_plan_id)
    state_repo.record_plan(user_id, plan, plan_id=plan_id)
    action = state_repo.record_action(
        user_id,
        session_id=session_id,
        plan_id=plan_id,
        action_type="booking_checkout_confirm",
        payload=body,
        message="真实预约服务暂未接入，已记录为待处理预约任务。",
    )
    return _provider_pending_action_response(action)


@router.post(
    "/travel/{session_id}/payment/orders",
    response_model=TravelPaymentSubmitResponseDto,
)
def post_payment_order(
    session_id: str,
    body: dict,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
) -> TravelPaymentSubmitResponseDto:
    plan = service.get_plan(session_id)
    plan_id = _dict_value(body, "plan_id", "planId", default=plan.recommended_plan_id)
    method = str(_dict_value(body, "payment_method_id", "paymentMethodId", default="manual"))
    action = state_repo.create_payment_order(
        user_id,
        session_id=session_id,
        plan_id=plan_id,
        payment_method_id=method,
        payload=body,
    )
    return TravelPaymentSubmitResponseDto(
        ok=False,
        order_id=str(action["order_id"]),
        status=str(action["status"]),
        code=str(action["code"]),
        message=str(action["message"]),
    )


@router.patch(
    "/travel/{session_id}/payment/orders/{order_id}/complete",
    response_model=TravelSimpleOkResponseDto,
)
def complete_payment_order(
    session_id: str,
    order_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
    state_repo: Annotated[MobileStateRepository, Depends(get_mobile_state_repository)],
    user_id: Annotated[str, Depends(_mobile_user_id)],
    plan_id: Annotated[str | None, Query(alias="planId")] = None,
) -> TravelSimpleOkResponseDto:
    plan = service.get_plan(session_id)
    state_repo.record_plan(user_id, plan, plan_id=plan_id or plan.recommended_plan_id)
    action = state_repo.record_action(
        user_id,
        session_id=session_id,
        plan_id=plan_id or plan.recommended_plan_id,
        action_type="payment_order_complete",
        payload={"order_id": order_id},
        message="支付网关暂未接入，无法确认真实付款，已记录待处理状态。",
    )
    return _provider_pending_action_response(action)


def _mobile_revision_response(
    plan,
    *,
    summary: str,
    plan_id: str,
    patches: list[PlanPatchDto] | None = None,
    warnings: list[str] | None = None,
) -> MobileRevisionResponse:
    return MobileRevisionResponse(
        travel_id=plan.session_id,
        revision_summary=_clean_revision_summary(summary),
        plan_page=present_conversation_page(plan),
        patches=patches or [],
        warnings=_clean_revision_warnings(warnings),
        updated_plan_comparison=present_plan_comparison(plan),
        updated_timeline=present_timeline_page(plan, plan_id),
        updated_booking_todos=present_booking_todos(plan, plan_id),
        updated_booking_checkout=present_booking_checkout(plan, plan_id),
        updated_payment=present_payment_page(plan, plan_id),
        updated_payment_confirmation=present_payment_confirmation(plan, plan_id),
        updated_trip_live_map=present_trip_live_map(plan, plan_id),
        updated_itinerary_hub=present_itinerary_hub(plan, plan_id),
    )


def _plan_service_for_user_llm_config(
    state_repo: MobileStateRepository,
    user_id: str,
) -> PlanService | None:
    saved = state_repo.get_preference(user_id, "llm")
    provider = str(saved.get("provider") or "").strip()
    if provider != "openai":
        return None

    settings = get_settings()
    api_key = str(saved.get("api_key") or settings.effective_llm_api_key or "").strip()
    base_url = str(saved.get("base_url") or "").strip()
    model = str(saved.get("model") or "").strip()
    if not (api_key and base_url and model):
        return None

    llm_client = OpenAICompatibleLLMClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        temperature=settings.llm_temperature,
        api_style=settings.llm_api_style,
        use_structured_output=settings.llm_use_structured_output,
        trust_env=settings.llm_trust_env,
    )
    prompt_runner = JSONPromptRunner(
        prompt_dir=Path(__file__).resolve().parents[2] / "agent" / "prompts",
        llm_client=llm_client,
        max_retries=settings.llm_max_retries,
        allow_rule_based_fallback=True,
    )
    runtime = build_react_agent_runtime(
        prompt_runner=prompt_runner,
        poi_query_tool=get_poi_query_tool(),
        poi_tool=get_poi_tool(),
        queue_tool=get_queue_tool(),
        weather_tool=get_weather_tool(),
        route_tool=get_route_tool(),
        user_memory_repository=get_user_memory_repository(),
        decider=LLMReActDecider(
            llm_client=llm_client,
            max_retries=settings.agent_action_parse_retries,
            fallback_decider=MockReActDecider(),
            allow_fallback=True,
            deterministic_preview=True,
        ),
    )
    return PlanService(
        session_store=get_session_store(),
        react_runtime=runtime,
        feedback_followup_service=None,
    )


def _clean_revision_summary(summary: str | None) -> str:
    text = str(summary or "").strip()
    if not text:
        return "已根据你的意见完成调整。"
    parts = [
        re.sub(r"[。.\s]*原因[:：].*$", "", part).strip()
        for part in re.split(r"[；;]", text)
    ]
    cleaned = "；".join(part for part in parts if part)
    return cleaned or "已根据你的意见完成调整。"


def _clean_revision_warnings(warnings: list[str] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for warning in warnings or []:
        text = str(warning or "").strip()
        if not text or _is_internal_revision_warning(text):
            continue
        text = _clean_revision_summary(text)
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _is_internal_revision_warning(text: str) -> bool:
    stripped = text.strip()
    lowered = stripped.lower()
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        return True
    if re.search(r"['\"][a-z_]+['\"]\s*:", stripped, flags=re.IGNORECASE):
        return True
    return any(marker in lowered for marker in _INTERNAL_REVISION_WARNING_MARKERS)


def _map_execution_task(task) -> MobileExecutionTaskDto:
    return MobileExecutionTaskDto(
        task_id=task.task_id,
        action=str(task.action),
        status=str(task.status),
        poi_id=task.poi_id,
        human_readable_confirmation=task.human_readable_confirmation or None,
        result=task.result or {},
    )


def _history_to_home_item(item: dict) -> HomeHistoryItemDto:
    return HomeHistoryItemDto(
        id=str(item.get("id") or item.get("travel_id") or ""),
        title=str(item.get("title") or "历史行程"),
        meta_line=str(item.get("meta_line") or item.get("route_summary") or "已生成行程"),
        plan_id=str(item.get("plan_id") or "plan-a"),
    )


def _self_home_companion_options():
    return HOME_DASHBOARD.companion_options


def _companion_to_home_option(companion: UserMemoryCompanion):
    from local_explorer_agent.app.mobile.schemas import HomeCompanionOptionDto

    return HomeCompanionOptionDto(
        id=companion.companion_id,
        label=companion.display_name,
        role_label=_role_label(companion.role_type),
        summary=_companion_summary(companion),
        avatar_emoji=_role_emoji(companion.role_type),
        selected_by_default=False,
    )


def _companion_to_archive_tag(companion: UserMemoryCompanion):
    from local_explorer_agent.app.mobile.schemas import ProfileArchiveTagDto

    age = f" · {companion.age}岁" if companion.age is not None else ""
    return ProfileArchiveTagDto(
        id=companion.companion_id,
        icon_emoji=_role_emoji(companion.role_type),
        label=f"{companion.display_name}{age}",
    )


def _companion_to_profile(companion: UserMemoryCompanion) -> CompanionProfileDto:
    return CompanionProfileDto(
        companion_id=companion.companion_id,
        display_name=companion.display_name,
        role_type=companion.role_type,
        role_label=_role_label(companion.role_type),
        age=companion.age,
        avatar_emoji=_role_emoji(companion.role_type),
        summary=_companion_summary(companion),
        hard_constraints=companion.hard_constraints,
        soft_preferences=companion.soft_preferences,
        risk_points=companion.risk_points,
    )


def _body_to_companion(
    body: CompanionProfileSaveBody,
    *,
    companion_id: str,
) -> UserMemoryCompanion:
    return UserMemoryCompanion(
        companion_id=companion_id,
        display_name=body.display_name.strip() or "同行人",
        role_type=_normalize_role_type(body.role_type),
        age=body.age,
        hard_constraints=_clean_text_list(body.hard_constraints),
        soft_preferences=_clean_text_list(body.soft_preferences),
        risk_points=_clean_text_list(body.risk_points),
    )


def _clean_text_list(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text[:80])
    return result[:12]


def _normalize_role_type(role_type: str) -> str:
    value = str(role_type or "").strip()
    return value if value in {"spouse", "child", "elder", "friend", "user"} else "friend"


def _role_label(role_type: str) -> str:
    return {
        "spouse": "伴侣",
        "child": "孩子",
        "elder": "长辈",
        "friend": "朋友",
        "user": "本人",
    }.get(role_type, "同行人")


def _role_emoji(role_type: str) -> str:
    return {
        "spouse": "💗",
        "child": "👶",
        "elder": "👵",
        "friend": "🙂",
        "user": "🙋",
    }.get(role_type, "🙂")


def _companion_summary(companion: UserMemoryCompanion) -> str:
    parts = [
        *companion.hard_constraints[:1],
        *companion.soft_preferences[:1],
        *companion.risk_points[:1],
    ]
    if companion.age is not None:
        parts.insert(0, f"{companion.age}岁")
    return " · ".join(parts) or "暂无偏好，点击补充"


def _api_key_preview(api_key: str | None) -> str | None:
    text = str(api_key or "").strip()
    if not text:
        return None
    if len(text) <= 8:
        return "已配置"
    return f"{text[:3]}***{text[-4:]}"


def _history_to_hub_item(item: dict) -> ItineraryHubHistoryItemDto:
    rating = item.get("rating")
    return ItineraryHubHistoryItemDto(
        id=str(item.get("id") or item.get("travel_id") or ""),
        thumb_emoji="🗺️",
        plan_id=str(item.get("plan_id") or "plan-a"),
        date_line=str(item.get("date_line") or item.get("updated_at") or "最近"),
        route_summary=str(item.get("route_summary") or item.get("title") or "历史行程"),
        rating_stars=float(rating if rating is not None else 0),
        price_text=str(item.get("price_text") or "费用待确认"),
    )


def _travel_mode_summary(value: dict) -> str:
    method_labels = {
        "taxi": "打车",
        "self_drive": "自驾",
        "transit": "地铁/公交",
    }
    method = value.get("selected_method_id") or value.get("selectedMethodId") or "taxi"
    radius = value.get("selected_radius_km") or value.get("selectedRadiusKm") or 5
    duration = value.get("selected_duration_id") or value.get("selectedDurationId") or "dur-afternoon"
    duration_labels = {
        "dur-afternoon": "3–4小时",
        "dur-short": "2小时内",
        "dur-half": "半天",
        "dur-full": "全天",
    }
    return f"{method_labels.get(method, str(method))} · {radius}km内 · {duration_labels.get(duration, str(duration))}"


def _dietary_summary(value: dict) -> str:
    ids = value.get("selected_need_ids") or value.get("selectedNeedIds") or ["need-lowcal"]
    labels = {
        "need-lowcal": "低卡",
        "need-veg": "素食",
        "need-halal": "清真",
        "need-none": "无特殊",
        "need-allergen": "过敏源",
    }
    return " · ".join(labels.get(str(i), str(i)) for i in ids) or "无特殊"


def _activity_summary(value: dict) -> str:
    ids = value.get("selected_tag_ids") or value.get("selectedTagIds") or ["tag-nature", "tag-interactive"]
    labels = {
        "tag-nature": "户外自然",
        "tag-interactive": "互动体验",
        "tag-art": "文艺展览",
        "tag-shopping": "逛街购物",
        "tag-sports": "运动健身",
        "tag-quiet": "安静放松",
    }
    return " · ".join(labels.get(str(i), str(i)) for i in ids) or "暂无偏好"


def _budget_pace_summary(value: dict) -> str:
    budget = value.get("selected_budget_id") or value.get("selectedBudgetId") or "budget-medium"
    pace = value.get("selected_pace_id") or value.get("selectedPaceId") or "pace-relaxed"
    budget_labels = {
        "budget-value": "性价比",
        "budget-medium": "中等",
        "budget-quality": "品质优先",
    }
    pace_labels = {
        "pace-tight": "紧凑",
        "pace-relaxed": "放松",
        "pace-spontaneous": "随性",
    }
    return f"{budget_labels.get(budget, str(budget))} · {pace_labels.get(pace, str(pace))}"
