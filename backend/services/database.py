"""
Database backup and restore service for portability.
"""
import aiosqlite
import shutil
import json
from pathlib import Path
from datetime import datetime
from backend.database import get_db_path


async def backup_database(backup_path: str) -> dict:
    db_path = get_db_path()

    if not Path(db_path).exists():
        raise ValueError("Database file not found")

    try:
        shutil.copy2(db_path, backup_path)

        db = await aiosqlite.connect(db_path)
        cursor = await db.execute("SELECT COUNT(*) FROM log_entries")
        count = (await cursor.fetchone())[0]
        await db.close()

        return {
            "success": True,
            "backup_path": backup_path,
            "entries_count": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def restore_database(backup_path: str) -> dict:
    if not Path(backup_path).exists():
        raise ValueError("Backup file not found")

    db_path = get_db_path()

    try:
        if Path(db_path).exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = f"{db_path}.pre_restore_{timestamp}"
            shutil.copy2(db_path, pre_restore_backup)

        shutil.copy2(backup_path, db_path)

        db = await aiosqlite.connect(db_path)
        cursor = await db.execute("SELECT COUNT(*) FROM log_entries")
        count = (await cursor.fetchone())[0]
        await db.close()

        return {
            "success": True,
            "entries_count": count,
            "message": f"Database restored successfully with {count} entries"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_database_info() -> dict:
    db_path = get_db_path()

    if not Path(db_path).exists():
        return {"exists": False}

    file_size = Path(db_path).stat().st_size

    db = await aiosqlite.connect(db_path)
    cursor = await db.execute("SELECT COUNT(*) FROM log_entries")
    entry_count = (await cursor.fetchone())[0]

    cursor = await db.execute("SELECT MIN(timestamp), MAX(timestamp) FROM log_entries")
    date_range = await cursor.fetchone()

    await db.close()

    return {
        "exists": True,
        "path": db_path,
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "entry_count": entry_count,
        "date_range": {
            "earliest": date_range[0],
            "latest": date_range[1]
        }
    }
