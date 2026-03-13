from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
async def get_config():
    return {
        "base_url": settings.app_base_url,
        "auth_mode": "oauth" if settings.google_client_id and settings.google_client_secret else "dev",
    }
