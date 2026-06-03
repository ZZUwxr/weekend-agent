from __future__ import annotations

import asyncio
from datetime import datetime

from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.interaction_tools import (
    IntakeUserRequirementsArgs,
    IntakeUserRequirementsTool,
)
from local_explorer_agent.app.agent.react.state import AgentState
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest


def _request(query: str) -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u_intake",
        query=query,
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-13T19:00:00"),
        duration_minutes=120,
    )


def test_intake_single_dining_asks_for_cuisine() -> None:
    state = AgentState(
        session_id="sess_intake",
        user_id="u_intake",
        request=_request("今晚只想吃个饭"),
    )

    result = asyncio.run(
        IntakeUserRequirementsTool().run(
            IntakeUserRequirementsArgs(query=state.request.query),
            state,
        )
    )

    assert result.success is True
    assert result.data["primary_intent"] == "dining"
    assert result.data["activity_count"]["max"] == 1
    assert result.data["clarification"]["needs_clarification"] is True
    assert result.data["clarification"]["questions"][0]["question_id"] == "q_cuisine"


def test_runtime_respects_single_dining_scope_after_answer(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    runtime = build_react_agent_runtime()

    first = asyncio.run(runtime.run(_request("今晚只想吃个饭")))
    assert first.state == PlanState.CLARIFYING
    assert first.clarification is not None

    state = runtime.last_state
    assert state is not None
    answered = state.model_copy(
        update={
            "requirement_intake": None,
            "clarification_response": None,
            "missing_slots": [],
            "clarification_answers": {
                "q_cuisine": "火锅",
                "q_group_size": "2人",
            },
            "status": "running",
        }
    )

    final = asyncio.run(runtime.run_from_state(answered))

    assert final.state == PlanState.PREVIEW
    assert len(final.plan_candidates) == 1
    assert len(final.plan_candidates[0].stages) == 1
    assert final.plan_candidates[0].stages[0].stage_type == "dine"
