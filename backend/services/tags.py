"""
Tags management service.
"""
from backend.database import get_db
from typing import Optional


async def get_all_tags() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tags ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def create_tag(name: str, color: str = "#3b82f6") -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO tags (name, color) VALUES (?, ?)",
            (name, color)
        )
        await db.commit()
        tag_id = cursor.lastrowid
        return {"id": tag_id, "name": name, "color": color}
    finally:
        await db.close()


async def delete_tag(tag_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM entry_tags WHERE tag_id = ?", (tag_id,))
        cursor = await db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
