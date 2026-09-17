import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.chat import router as chat_router
from app.api.common import fail
from app.api.feedback import router as feedback_router
from app.api.hotspots import router as hotspots_router
from app.db.session import SessionLocal
from app.schemas.api import HealthResponse

app = FastAPI(title="公考晨报 API", version="0.1.0")
app.include_router(hotspots_router)
app.include_router(chat_router)
app.include_router(feedback_router)


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": detail.get("code", "HTTP_ERROR"),
                "message": detail.get("message", "请求失败"),
                "retryable": detail.get("retryable", False),
                "request_id": request.state.request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, _exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数无效",
                "retryable": False,
                "request_id": request.state.request_id,
            }
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> dict[str, str]:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        fail(503, "DATABASE_UNAVAILABLE", "数据库不可用", retryable=True)
    return {"status": "ok", "database": "ok"}
