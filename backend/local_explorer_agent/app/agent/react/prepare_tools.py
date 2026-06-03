"""Preview-safe execution prepare tools for the ReAct runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from local_explorer_agent.app.domain.enums import ExecutionAction
from local_explorer_agent.app.domain.models import ExecutionTask
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState


class BookingPrepareArgs(BaseModel):
    poi_id: str
    time: str | None = None
    party_size: int | None = Field(default=None, ge=1, le=30)
    note: str | None = None


class TaxiPrepareArgs(BaseModel):
    from_location: dict | None = None
    to_location: dict | None = None
    from_poi_id: str | None = None
    to_poi_id: str | None = None
    time: str | None = None


class SharePrepareArgs(BaseModel):
    channel: str = "link"
    recipients: list[str] = Field(default_factory=list)
    message: str | None = None


class BookingPrepareTool:
    name = "booking_prepare"
    description = "preview 阶段生成需要用户确认的预约 ExecutionTask，不真实预订"
    args_schema = BookingPrepareArgs
    is_execution_tool = False
    requires_confirmation = True
    prepare_tool = True

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, BookingPrepareArgs)
        task = ExecutionTask(
            task_id=f"task_prepare_booking_{args.poi_id}",
            action=ExecutionAction.BOOK_RESTAURANT,
            poi_id=args.poi_id,
            params={
                "time": args.time,
                "party_size": args.party_size,
                "note": args.note,
                "prepare_only": True,
            },
            requires_user_confirmation=True,
            risk_level=2,
            reversible=True,
            preconditions=["plan_confirmed"],
            human_readable_confirmation=f"确认后预约 POI {args.poi_id}",
        )
        return ToolResult(success=True, data={"execution_task": task.model_dump()})


class TaxiPrepareTool:
    name = "taxi_prepare"
    description = "preview 阶段生成需要用户确认的叫车 ExecutionTask，不真实叫车"
    args_schema = TaxiPrepareArgs
    is_execution_tool = False
    requires_confirmation = True
    prepare_tool = True

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, TaxiPrepareArgs)
        from_ref = args.from_poi_id or "from_location"
        to_ref = args.to_poi_id or "to_location"
        task = ExecutionTask(
            task_id=f"task_prepare_taxi_{from_ref}_{to_ref}",
            action=ExecutionAction.CALL_TAXI,
            params={
                "from_location": args.from_location,
                "to_location": args.to_location,
                "from_poi_id": args.from_poi_id,
                "to_poi_id": args.to_poi_id,
                "time": args.time,
                "prepare_only": True,
            },
            requires_user_confirmation=True,
            risk_level=2,
            reversible=True,
            preconditions=["plan_confirmed"],
            human_readable_confirmation="确认后按计划叫车",
        )
        return ToolResult(success=True, data={"execution_task": task.model_dump()})


class SharePrepareTool:
    name = "share_prepare"
    description = "preview 阶段生成需要用户确认的分享 ExecutionTask，不真实分享"
    args_schema = SharePrepareArgs
    is_execution_tool = False
    requires_confirmation = True
    prepare_tool = True

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, SharePrepareArgs)
        task = ExecutionTask(
            task_id=f"task_prepare_share_{args.channel}",
            action=ExecutionAction.SHARE_PLAN,
            params={
                "channel": args.channel,
                "recipients": args.recipients,
                "message": args.message,
                "prepare_only": True,
            },
            requires_user_confirmation=True,
            risk_level=1,
            reversible=True,
            preconditions=["plan_confirmed"],
            human_readable_confirmation=f"确认后通过 {args.channel} 分享行程",
        )
        return ToolResult(success=True, data={"execution_task": task.model_dump()})
