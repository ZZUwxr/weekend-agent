from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from local_explorer_agent.app.api.v1.router import router as api_v1_router
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.core.exceptions import NotFoundError
from local_explorer_agent.app.core.logging import configure_logging

configure_logging()

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(api_v1_router, prefix="/api/v1")


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    del request
    return JSONResponse(status_code=404, content={"detail": str(exc)})
