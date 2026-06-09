"""Health check liviano."""
from fastapi import APIRouter

from app import __version__

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
