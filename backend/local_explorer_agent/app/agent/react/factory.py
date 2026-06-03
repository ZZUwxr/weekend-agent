"""Factory for building a fully-wired ReActAgentRuntime."""

from __future__ import annotations

from local_explorer_agent.app.agent.react.executor import ActionExecutor
from local_explorer_agent.app.agent.react.fact_tools import (
    POIDetailTool,
    POISearchTool,
    QueueLookupTool,
    RouteSearchTool,
    WeatherLookupTool,
)
from local_explorer_agent.app.agent.react.interaction_tools import (
    AddFollowupStageTool,
    ApplyPlanPatchTool,
    ClarifyRequirementsTool,
    ExplainChangesTool,
    IntakeUserRequirementsTool,
    InterpretRevisionRequestTool,
    RebuildTimelineTool,
    RemoveFollowupStageTool,
    ReplacePOITool,
    ReviseDiningStageTool,
)
from local_explorer_agent.app.agent.react.memory_tools import ReadUserMemoryTool
from local_explorer_agent.app.agent.react.mock_decider import MockReActDecider
from local_explorer_agent.app.agent.react.policy import AgentPolicy
from local_explorer_agent.app.agent.react.prepare_tools import (
    BookingPrepareTool,
    SharePrepareTool,
    TaxiPrepareTool,
)
from local_explorer_agent.app.agent.react.reducer import StateReducer
from local_explorer_agent.app.agent.react.runtime import ReActAgentRuntime
from local_explorer_agent.app.agent.react.skill_tools import (
    BuildTimelineTool,
    CalculateRoutesTool,
    DetectConflictsTool,
    DraftExperiencePlanTool,
    GenerateNegotiationStrategyTool,
    ScoreCandidatesTool,
    SelectPlacesTool,
    UnderstandUserTool,
)
from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry
from local_explorer_agent.app.agent.react.validation_tools import (
    ConstraintValidatorTool,
    PlanRepairTool,
)
from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.place_selection import PlaceSelectionSkill
from local_explorer_agent.app.agent.skills.routing import RoutingSkill
from local_explorer_agent.app.agent.skills.timeline_builder import TimelineBuilderSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.scoring import choose_recommended_candidate, score_candidate


def build_react_agent_runtime(
    *,
    prompt_runner=None,
    poi_query_tool=None,
    poi_tool=None,
    queue_tool=None,
    weather_tool=None,
    route_tool=None,
    user_memory_repository=None,
    max_steps: int | None = None,
    max_tool_calls: int | None = None,
    decider=None,
) -> ReActAgentRuntime:
    """Build a ReActAgentRuntime with all skill tools registered.

    All tool/skill dependencies can be injected for testing.
    When called without arguments, uses the same defaults as the legacy Orchestrator wiring.
    When decider is not provided, selects LLMReActDecider for openai provider,
    or MockReActDecider for mock provider.
    """
    # Lazy imports to avoid circular deps when called from deps.py
    from local_explorer_agent.app.api.deps import (
        get_json_prompt_runner,
        get_poi_query_tool,
        get_poi_tool,
        get_queue_tool,
        get_route_tool,
        get_user_memory_repository,
        get_weather_tool,
    )

    settings = get_settings()
    _max_steps = max_steps or settings.agent_max_steps
    _max_tool_calls = max_tool_calls or settings.agent_max_tool_calls

    _prompt_runner = prompt_runner or get_json_prompt_runner()
    _poi_query_tool = poi_query_tool or get_poi_query_tool()
    _poi_tool = poi_tool or get_poi_tool()
    _queue_tool = queue_tool or get_queue_tool()
    _weather_tool = weather_tool or get_weather_tool()
    _route_tool = route_tool or get_route_tool()
    _user_memory_repository = user_memory_repository or get_user_memory_repository()

    # Build skills (same as legacy Orchestrator)
    user_understanding = UserUnderstandingSkill(prompt_runner=_prompt_runner)
    conflict_detection = ConflictDetectionSkill(prompt_runner=_prompt_runner)
    negotiation = NegotiationSkill(prompt_runner=_prompt_runner)
    experience_planning = ExperiencePlanningSkill(prompt_runner=_prompt_runner)
    place_selection = PlaceSelectionSkill(
        poi_query_tool=_poi_query_tool,
        poi_tool=_poi_tool,
        queue_tool=_queue_tool,
        weather_tool=_weather_tool,
    )
    routing = RoutingSkill(_route_tool)
    timeline_builder = TimelineBuilderSkill()

    # Register skill tools
    registry = ToolRegistry()
    registry.register(ReadUserMemoryTool(_user_memory_repository))
    registry.register(UnderstandUserTool(user_understanding))
    registry.register(DetectConflictsTool(conflict_detection))
    registry.register(GenerateNegotiationStrategyTool(negotiation))
    registry.register(DraftExperiencePlanTool(experience_planning))
    registry.register(SelectPlacesTool(place_selection))
    registry.register(CalculateRoutesTool(routing))
    registry.register(BuildTimelineTool(timeline_builder))
    registry.register(
        ScoreCandidatesTool(
            score_fn=score_candidate,
            choose_fn=choose_recommended_candidate,
        )
    )
    registry.register(POISearchTool(_poi_tool))
    registry.register(POIDetailTool(_poi_tool))
    registry.register(RouteSearchTool(_route_tool, _poi_tool))
    registry.register(WeatherLookupTool(_weather_tool))
    registry.register(QueueLookupTool(_queue_tool))
    registry.register(BookingPrepareTool())
    registry.register(TaxiPrepareTool())
    registry.register(SharePrepareTool())
    registry.register(IntakeUserRequirementsTool())
    registry.register(ClarifyRequirementsTool())
    registry.register(InterpretRevisionRequestTool())
    registry.register(ApplyPlanPatchTool())
    registry.register(AddFollowupStageTool(_poi_tool))
    registry.register(RemoveFollowupStageTool())
    registry.register(ReviseDiningStageTool(_poi_tool))
    registry.register(ReplacePOITool(_poi_tool))
    registry.register(RebuildTimelineTool())
    registry.register(ExplainChangesTool())
    registry.register(ConstraintValidatorTool())
    registry.register(PlanRepairTool())

    # Build runtime
    if decider is None:
        decider = _build_decider(settings, _prompt_runner)

    policy = AgentPolicy(
        max_steps=_max_steps,
        max_tool_calls=_max_tool_calls,
        max_repair_attempts=settings.agent_max_repair_attempts,
        max_revision_attempts=settings.agent_max_revision_attempts,
    )
    executor = ActionExecutor(registry)
    reducer = StateReducer()

    return ReActAgentRuntime(
        tool_registry=registry,
        decider=decider,
        policy=policy,
        executor=executor,
        reducer=reducer,
        max_steps=_max_steps,
        max_tool_calls=_max_tool_calls,
    )


def _build_decider(settings, prompt_runner):
    """Select decider based on LLM provider configuration."""
    if settings.llm_provider == "openai":
        from local_explorer_agent.app.agent.react.llm_decider import LLMReActDecider

        fallback = MockReActDecider()
        return LLMReActDecider(
            llm_client=prompt_runner.llm_client,
            max_retries=settings.agent_action_parse_retries,
            fallback_decider=fallback,
            allow_fallback=True,
            deterministic_preview=True,
        )
    return MockReActDecider()
