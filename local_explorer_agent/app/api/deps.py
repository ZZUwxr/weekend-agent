from functools import lru_cache
from pathlib import Path

from local_explorer_agent.app.agent.llm.base import BaseLLMClient
from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.agent.llm.mock_client import MockLLMClient
from local_explorer_agent.app.agent.llm.openai_client import OpenAICompatibleLLMClient
from local_explorer_agent.app.agent.orchestrator import Orchestrator
from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.place_selection import PlaceSelectionSkill
from local_explorer_agent.app.agent.skills.replanning import ReplanningSkill
from local_explorer_agent.app.agent.skills.routing import RoutingSkill
from local_explorer_agent.app.agent.skills.timeline_builder import TimelineBuilderSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.core.config import Settings, get_settings
from local_explorer_agent.app.repositories.booking_repository import BookingRepository
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.repositories.postgres_repository import (
    PostgresPOIRepository,
    PostgresQueueRepository,
    PostgresRouteRepository,
)
from local_explorer_agent.app.repositories.queue_repository import QueueRepository
from local_explorer_agent.app.repositories.route_repository import RouteRepository
from local_explorer_agent.app.repositories.weather_repository import WeatherRepository
from local_explorer_agent.app.services.execution_service import ExecutionService
from local_explorer_agent.app.services.feedback_service import FeedbackService
from local_explorer_agent.app.services.plan_service import PlanService
from local_explorer_agent.app.tools.booking_tool import BookingTool
from local_explorer_agent.app.tools.poi_query_tool import POIQueryRewriteTool
from local_explorer_agent.app.tools.poi_tool import POITool
from local_explorer_agent.app.tools.queue_tool import QueueTool
from local_explorer_agent.app.tools.route_tool import RouteTool
from local_explorer_agent.app.tools.share_tool import ShareTool
from local_explorer_agent.app.tools.taxi_tool import TaxiTool
from local_explorer_agent.app.tools.weather_tool import WeatherTool


def _data_dir(settings: Settings) -> Path:
    return settings.data_dir if settings.data_dir.is_absolute() else Path.cwd() / settings.data_dir


def _prompt_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "agent" / "prompts"


@lru_cache
def get_session_store() -> SessionStore:
    return SessionStore()


@lru_cache
def get_poi_repository():
    settings = get_settings()
    if settings.data_backend == "postgres":
        return PostgresPOIRepository(
            settings.database_url,
            connect_timeout=settings.database_connect_timeout_seconds,
        )
    return POIRepository(_data_dir(settings))


@lru_cache
def get_route_repository():
    settings = get_settings()
    if settings.data_backend == "postgres":
        return PostgresRouteRepository(
            settings.database_url,
            connect_timeout=settings.database_connect_timeout_seconds,
        )
    return RouteRepository(_data_dir(settings))


@lru_cache
def get_queue_repository():
    settings = get_settings()
    if settings.data_backend == "postgres":
        return PostgresQueueRepository(
            settings.database_url,
            connect_timeout=settings.database_connect_timeout_seconds,
        )
    return QueueRepository(_data_dir(settings))


@lru_cache
def get_weather_repository() -> WeatherRepository:
    return WeatherRepository(_data_dir(get_settings()))


@lru_cache
def get_booking_repository() -> BookingRepository:
    return BookingRepository(_data_dir(get_settings()))


@lru_cache
def get_poi_tool() -> POITool:
    return POITool(get_poi_repository())


@lru_cache
def get_poi_query_tool() -> POIQueryRewriteTool:
    return POIQueryRewriteTool(get_poi_repository())


@lru_cache
def get_route_tool() -> RouteTool:
    return RouteTool(get_route_repository(), get_poi_repository())


@lru_cache
def get_queue_tool() -> QueueTool:
    return QueueTool(get_queue_repository())


@lru_cache
def get_weather_tool() -> WeatherTool:
    return WeatherTool(get_weather_repository())


@lru_cache
def get_booking_tool() -> BookingTool:
    return BookingTool(get_booking_repository())


@lru_cache
def get_taxi_tool() -> TaxiTool:
    return TaxiTool()


@lru_cache
def get_share_tool() -> ShareTool:
    return ShareTool()


@lru_cache
def get_llm_client() -> BaseLLMClient:
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAICompatibleLLMClient(
            api_key=settings.effective_llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            temperature=settings.llm_temperature,
            api_style=settings.llm_api_style,
            use_structured_output=settings.llm_use_structured_output,
            trust_env=settings.llm_trust_env,
        )
    return MockLLMClient()


@lru_cache
def get_json_prompt_runner() -> JSONPromptRunner:
    settings = get_settings()
    return JSONPromptRunner(
        prompt_dir=_prompt_dir(),
        llm_client=get_llm_client(),
        max_retries=settings.llm_max_retries,
        allow_rule_based_fallback=(
            settings.llm_provider == "mock" or settings.llm_allow_rule_based_fallback
        ),
    )


@lru_cache
def get_orchestrator() -> Orchestrator:
    prompt_runner = get_json_prompt_runner()
    place_selection_skill = PlaceSelectionSkill(
        poi_query_tool=get_poi_query_tool(),
        poi_tool=get_poi_tool(),
        queue_tool=get_queue_tool(),
        weather_tool=get_weather_tool(),
    )
    return Orchestrator(
        session_store=get_session_store(),
        user_understanding_skill=UserUnderstandingSkill(prompt_runner=prompt_runner),
        conflict_detection_skill=ConflictDetectionSkill(prompt_runner=prompt_runner),
        negotiation_skill=NegotiationSkill(prompt_runner=prompt_runner),
        experience_planning_skill=ExperiencePlanningSkill(prompt_runner=prompt_runner),
        place_selection_skill=place_selection_skill,
        routing_skill=RoutingSkill(get_route_tool()),
        timeline_builder_skill=TimelineBuilderSkill(),
        replanning_skill=ReplanningSkill(),
    )


@lru_cache
def get_plan_service() -> PlanService:
    return PlanService(orchestrator=get_orchestrator(), session_store=get_session_store())


@lru_cache
def get_execution_service() -> ExecutionService:
    return ExecutionService(
        session_store=get_session_store(),
        booking_tool=get_booking_tool(),
        taxi_tool=get_taxi_tool(),
        share_tool=get_share_tool(),
    )


@lru_cache
def get_feedback_service() -> FeedbackService:
    return FeedbackService(session_store=get_session_store())
