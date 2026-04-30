from fastapi import APIRouter

from local_explorer_agent.app.api.v1 import events, execution, feedback, plans
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.schemas import (
    DataHealthResponse,
    HealthResponse,
    MetaSchemasResponse,
    build_meta_schemas,
)
from local_explorer_agent.app.repositories.data_health import check_data_health

router = APIRouter()
router.include_router(plans.router)
router.include_router(events.router)
router.include_router(execution.router)
router.include_router(feedback.router)


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name, env=settings.app_env)


@router.get("/meta/schemas", response_model=MetaSchemasResponse, tags=["meta"])
def meta_schemas() -> MetaSchemasResponse:
    return build_meta_schemas()


@router.get("/meta/data-health", response_model=DataHealthResponse, tags=["meta"])
def data_health() -> DataHealthResponse:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    return DataHealthResponse.model_validate(check_data_health(data_dir))


@router.get("/meta/runtime", tags=["meta"])
def runtime_meta() -> dict[str, object]:
    settings = get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_allow_rule_based_fallback": settings.llm_allow_rule_based_fallback,
        "data_backend": settings.data_backend,
        "database_url_set": bool(settings.database_url),
    }
