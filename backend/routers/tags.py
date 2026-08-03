"""
Tags API router.
"""
from fastapi import APIRouter, HTTPException
from backend.models import TagCreate
from backend.services import tags

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("")
async def list_tags():
    return await tags.get_all_tags()


@router.post("")
async def create_tag(tag: TagCreate):
    try:
        return await tags.create_tag(tag.name, tag.color)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    success = await tags.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"status": "deleted"}
