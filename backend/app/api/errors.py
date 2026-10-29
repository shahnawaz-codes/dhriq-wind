import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.data_store import DataNotReadyError, UpstreamError

logger = logging.getLogger(__name__)


class InvalidParameterError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


async def invalid_parameter_handler(
    request: Request, exc: InvalidParameterError
) -> JSONResponse:
    details = [{"field": exc.field}] if exc.field else []
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_PARAMETER",
                "message": exc.message,
                "details": details,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = []
    messages = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = str(loc[-1]) if loc else None
        msg = err.get("msg", "Invalid value")
        details.append({"field": field_name})
        messages.append(f"{field_name}: {msg}" if field_name else msg)

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "; ".join(messages) or "Request validation failed",
                "details": details,
            }
        },
    )


async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    logger.error("Upstream error occurred: %s", exc)
    return JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "UPSTREAM_ERROR",
                "message": "Failed to fetch upstream data from Elexon Insights API",
                "details": [],
            }
        },
    )


async def data_not_ready_handler(
    request: Request, exc: DataNotReadyError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": "5"},
        content={
            "error": {
                "code": "DATA_NOT_READY",
                "message": "Initial dataset loading is currently in progress",
                "details": [],
            }
        },
    )


async def http_exception_handler(
    request: Request, exc: HTTPException | StarletteHTTPException
) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
                "details": [],
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "details": [],
            }
        },
    )
