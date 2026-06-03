from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState


def summarize_state(state: AgentState) -> str:
    """Return a short human-readable summary of the current agent state."""
    parts = [
        f"status={state.status}",
        f"step={state.step_count}",
        f"tool_calls={state.tool_call_count}",
    ]

    if state.inferred_context:
        parts.append(f"group={state.inferred_context.group_type}")

    if state.conflicts:
        parts.append(f"conflicts={len(state.conflicts)}")

    if state.candidate_plans:
        parts.append(f"candidates={len(state.candidate_plans)}")

    if state.recommended_plan_id:
        parts.append(f"recommended={state.recommended_plan_id}")

    if state.scoring_completed:
        parts.append("scored=yes")

    if state.execution_graph:
        parts.append(f"exec_tasks={len(state.execution_graph)}")

    return " | ".join(parts)
