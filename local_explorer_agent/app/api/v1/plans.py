import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from local_explorer_agent.app.api.deps import get_plan_service
from local_explorer_agent.app.domain.models import PlanOutput
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest, PlanPreviewStreamEvent
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
            await asyncio.to_thread(service.preview_plan, request, event_callback=emit)
        except Exception as exc:
            if not error_emitted:
                emit(PlanPreviewStreamEvent(event="error", data={"step": None, "error": str(exc)}))
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


def _format_sse_event(event: PlanPreviewStreamEvent) -> str:
    data = json.dumps(event.data, ensure_ascii=False, default=str)
    return f"event: {event.event}\ndata: {data}\n\n"
