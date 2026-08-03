"""
Import/Export API router.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from backend.services import excel_parser, database
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/import/excel")
async def import_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be .xlsx or .xls")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = await excel_parser.import_excel(tmp_path)
        os.unlink(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/excel")
async def export_excel():
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp_path = tmp.name

        result = await excel_parser.export_excel(tmp_path)
        return FileResponse(
            tmp_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="personal_log_export.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup")
async def backup_database():
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name

        result = await database.backup_database(tmp_path)
        if result["success"]:
            return FileResponse(
                tmp_path,
                media_type="application/octet-stream",
                filename=f"personal_log_backup_{result['timestamp'][:10]}.db"
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_database(file: UploadFile = File(...)):
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be .db file")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = await database.restore_database(tmp_path)
        os.unlink(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_database_info():
    return await database.get_database_info()
