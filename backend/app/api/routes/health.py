from fastapi import APIRouter, Response

from app.api.schemas import HealthResponse
from app.config import get_settings
from app.services.data_store import get_data_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health(response: Response) -> HealthResponse:
    """Liveness probe. Does not call Elexon or block on data loading."""
    response.headers["Cache-Control"] = "no-store"
    settings = get_settings()
    store = get_data_store(settings)
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        data_loaded=store.is_loaded,
    )
