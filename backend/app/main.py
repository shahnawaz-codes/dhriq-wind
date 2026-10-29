import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    InvalidParameterError,
    data_not_ready_handler,
    generic_exception_handler,
    http_exception_handler,
    invalid_parameter_handler,
    upstream_error_handler,
    validation_exception_handler,
)
from app.api.routes import health, meta, records, series, summary
from app.config import get_settings
from app.services.data_store import (
    DataNotReadyError,
    UpstreamError,
    get_data_store,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting UK Wind Generation Forecast Accuracy API v%s",
        settings.app_version,
    )
    logger.info(
        "Window: %s to %s | Default Cutoff: %s %s",
        settings.delivery_window_start,
        settings.delivery_window_end,
        settings.decision_cutoff_local_time,
        settings.decision_timezone,
    )

    if settings.preload_on_startup:
        logger.info("Initiating background preload of Elexon data...")
        store = get_data_store(settings)
        # Background task so server starts immediately without blocking liveness checks
        asyncio.create_task(store.get_data())

    yield

    logger.info("Shutting down API service.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="UK Wind Forecast Accuracy API",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(InvalidParameterError, invalid_parameter_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(UpstreamError, upstream_error_handler)
    app.add_exception_handler(DataNotReadyError, data_not_ready_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include Routes
    api_router = APIRouter(prefix="/api")
    api_router.include_router(health.router, tags=["Health"])
    api_router.include_router(meta.router, tags=["Metadata"])
    api_router.include_router(summary.router, tags=["Summary"])
    api_router.include_router(series.router, tags=["Series"])
    api_router.include_router(records.router, tags=["Records"])

    app.include_router(api_router)

    return app


app = create_app()
