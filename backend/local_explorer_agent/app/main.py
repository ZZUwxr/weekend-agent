from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from local_explorer_agent.app.api.v1.router import router as api_v1_router
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.core.exceptions import LLMError, NotFoundError, classify_llm_error
from local_explorer_agent.app.core.logging import configure_logging

configure_logging()

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_v1_router, prefix="/api/v1")


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=404,
        content={"code": "not_found", "message": str(exc), "details": None},
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    del request
    status_code, code, message = classify_llm_error(exc)
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": {"provider": "openai_compatible"},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    del request
    detail = exc.detail
    if isinstance(detail, dict):
        code = str(detail.get("code") or f"http_{exc.status_code}")
        message = str(detail.get("message") or detail.get("detail") or exc.status_code)
        details = detail.get("details")
    else:
        code = f"http_{exc.status_code}"
        message = str(detail or exc.status_code)
        details = None
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": message, "details": details},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "请求参数不符合接口要求。",
            "details": exc.errors(),
        },
    )
