import asyncio
import json
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from local_explorer_agent.app.api.deps import get_plan_service
from local_explorer_agent.app.domain.models import PlanOutput
from local_explorer_agent.app.domain.schemas import (
    ClarificationAnswerRequest,
    PlanPreviewRequest,
    PlanPreviewStreamEvent,
    PlanRevisionRequest,
    PlanRevisionResponse,
)
from local_explorer_agent.app.core.exceptions import classify_llm_error
from local_explorer_agent.app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/preview", response_model=PlanOutput)
def preview_plan(
    request: PlanPreviewRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.preview_plan(request)


@router.post("/preview/stream")
async def preview_plan_stream(
    request: PlanPreviewRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> StreamingResponse:
    return _stream_plan_events(
        lambda emit: service.preview_plan(request, event_callback=emit)
    )


@router.post("/{session_id}/clarifications/stream")
async def answer_clarifications_stream(
    session_id: str,
    request: ClarificationAnswerRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> StreamingResponse:
    return _stream_plan_events(
        lambda emit: service.answer_clarifications(
            session_id,
            request,
            event_callback=emit,
        )
    )


def _stream_plan_events(
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


@router.get("/{session_id}", response_model=PlanOutput)
def get_plan(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.get_plan(session_id)


@router.post("/{session_id}/confirm", response_model=PlanOutput)
def confirm_plan(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.confirm_plan(session_id)


@router.post("/{session_id}/clarifications", response_model=PlanOutput)
def answer_clarifications(
    session_id: str,
    request: ClarificationAnswerRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    try:
        return service.answer_clarifications(session_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{session_id}/revise", response_model=PlanRevisionResponse)
def revise_plan(
    session_id: str,
    request: PlanRevisionRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanRevisionResponse:
    try:
        return service.revise_plan(session_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _format_sse_event(event: PlanPreviewStreamEvent) -> str:
    data = json.dumps(event.data, ensure_ascii=False, default=str)
    return f"event: {event.event}\ndata: {data}\n\n"
