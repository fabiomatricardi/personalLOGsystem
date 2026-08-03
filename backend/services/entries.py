"""
Log entries CRUD service.
"""
from backend.database import get_db
from datetime import datetime
from typing import Optional


async def get_all_entries(
    entry_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    db = await get_db()
    try:
        query = "SELECT * FROM log_entries WHERE 1=1"
        params = []

        if entry_type:
            query += " AND type = ?"
            params.append(entry_type)

        if status:
            query += " AND status = ?"
            params.append(status)

        if search:
            query += " AND (activity LIKE ? OR follow_up LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        entries = []
        for row in rows:
            entry = dict(row)
            entry["tags"] = await _get_entry_tags(db, entry["id"])
            entries.append(entry)
        return entries
    finally:
        await db.close()


async def get_entry(entry_id: int) -> Optional[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM log_entries WHERE id = ?", (entry_id,))
        row = await cursor.fetchone()
        if row:
            entry = dict(row)
            entry["tags"] = await _get_entry_tags(db, entry["id"])
            return entry
        return None
    finally:
        await db.close()


async def create_entry(data: dict) -> dict:
    db = await get_db()
    try:
        now = datetime.now().isoformat()
        timestamp = data.get("timestamp") or now
        status = data.get("status") or ("LOG" if data.get("type") == "LOG" else "PENDING")

        cursor = await db.execute(
            """INSERT INTO log_entries (timestamp, activity, type, follow_up, status, reference_id, eta, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                timestamp,
                data["activity"],
                data["type"],
                data.get("follow_up"),
                status,
                data.get("reference_id"),
                data.get("eta"),
                now,
                now
            )
        )
        await db.commit()
        entry_id = cursor.lastrowid

        if "tags" in data:
            for tag_id in data["tags"]:
                await db.execute(
                    "INSERT INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
                    (entry_id, tag_id)
                )
            await db.commit()

        return await get_entry(entry_id)
    finally:
        await db.close()


async def update_entry(entry_id: int, data: dict) -> Optional[dict]:
    db = await get_db()
    try:
        existing = await get_entry(entry_id)
        if not existing:
            return None

        updates = []
        params = []

        for field in ["timestamp", "activity", "type", "follow_up", "status", "reference_id", "eta"]:
            if field in data and data[field] is not None:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(entry_id)

            query = f"UPDATE log_entries SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()

        if "tags" in data:
            await db.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
            for tag_id in data["tags"]:
                await db.execute(
                    "INSERT INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
                    (entry_id, tag_id)
                )
            await db.commit()

        return await get_entry(entry_id)
    finally:
        await db.close()


async def delete_entry(entry_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
        cursor = await db.execute("DELETE FROM log_entries WHERE id = ?", (entry_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def get_dashboard_stats() -> dict:
    db = await get_db()
    try:
        stats = {}

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries")
        stats["total_entries"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'LOG'")
        stats["total_logs"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TODO'")
        stats["total_todos"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TASK'")
        stats["total_tasks"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TASK' AND status = 'PENDING'")
        stats["pending_tasks"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TASK' AND status = 'ASSIGNED'")
        stats["assigned_tasks"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TASK' AND status = 'ONGOING'")
        stats["ongoing_tasks"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM log_entries WHERE type = 'TASK' AND status = 'COMPLETED'")
        stats["completed_tasks"] = (await cursor.fetchone())[0]

        now = datetime.now().isoformat()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM log_entries WHERE type IN ('TODO', 'TASK') AND eta < ? AND status != 'COMPLETED'",
            (now,)
        )
        stats["overdue_tasks"] = (await cursor.fetchone())[0]

        return stats
    finally:
        await db.close()


async def _get_entry_tags(db, entry_id: int) -> list[dict]:
    cursor = await db.execute(
        """SELECT t.id, t.name, t.color FROM tags t
           JOIN entry_tags et ON t.id = et.tag_id
           WHERE et.entry_id = ?""",
        (entry_id,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
