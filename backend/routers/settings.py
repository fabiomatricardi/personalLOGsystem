"""
Settings API router.
"""
from fastapi import APIRouter
from backend.services.config import load_config, save_config
from backend.models import AppConfig

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return load_config()


@router.post("")
async def update_settings(config: dict):
    save_config(config)
    return {"status": "ok", "config": load_config()}
