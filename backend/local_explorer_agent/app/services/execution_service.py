from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.enums import ExecutionAction, ExecutionStatus, PlanState
from local_explorer_agent.app.domain.schemas import ExecutionResponse
from local_explorer_agent.app.tools.booking_tool import BookingTool
from local_explorer_agent.app.tools.share_tool import ShareTool
from local_explorer_agent.app.tools.taxi_tool import TaxiTool


class ExecutionService:
    def __init__(
        self,
        *,
        session_store: SessionStore,
        booking_tool: BookingTool,
        taxi_tool: TaxiTool,
        share_tool: ShareTool,
    ) -> None:
        self.session_store = session_store
        self.booking_tool = booking_tool
        self.taxi_tool = taxi_tool
        self.share_tool = share_tool

    def execute(self, session_id: str) -> ExecutionResponse:
        plan = self.session_store.get(session_id)
        if plan.state == PlanState.COMPLETED:
            return ExecutionResponse(
                success=True,
                tasks=plan.execution_graph,
                plan=plan,
            )
        if plan.state != PlanState.CONFIRMED:
            return ExecutionResponse(
                success=False,
                tasks=plan.execution_graph,
                plan=plan,
            )
        plan.state = PlanState.EXECUTING
        finished_task_ids: set[str] = set()

        for task in plan.execution_graph:
            if any(dep not in finished_task_ids for dep in task.depends_on):
                continue
            task.status = ExecutionStatus.RUNNING
            result = self._execute_task(session_id, plan.share_message, task)
            task.result = result.data or {}
            task.status = ExecutionStatus.CONFIRMED if result.success else ExecutionStatus.FAILED
            finished_task_ids.add(task.task_id)

        plan.state = (
            PlanState.COMPLETED
            if all(task.status == ExecutionStatus.CONFIRMED for task in plan.execution_graph)
            else PlanState.FAILED
        )
        self.session_store.update(plan)
        return ExecutionResponse(
            success=plan.state == PlanState.COMPLETED,
            tasks=plan.execution_graph,
            plan=plan,
        )

    def _execute_task(self, session_id: str, share_message: str, task):
        if task.action in {ExecutionAction.BOOK_RESTAURANT, ExecutionAction.BOOK_ACTIVITY}:
            return self.booking_tool.book(
                poi_id=task.poi_id or "",
                action=task.action,
                params=task.params,
            )
        if task.action == ExecutionAction.CALL_TAXI:
            return self.taxi_tool.call_taxi(
                from_poi_id=task.params.get("from_poi_id"),
                to_poi_id=task.params.get("to_poi_id"),
            )
        if task.action == ExecutionAction.SHARE_PLAN:
            return self.share_tool.share_plan(session_id=session_id, message=share_message)
        return self.booking_tool.book(
            poi_id=task.poi_id or "",
            action=task.action,
            params=task.params,
        )
