"""
Analysis API router for LLM-powered reports.
"""
from fastapi import APIRouter, HTTPException
from backend.models import AnalysisRequest
from backend.services import llm_service, entries
from backend.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def get_week_date_range(year: int, week_number: int) -> tuple[str, str]:
    """Get start and end dates for a specific week number."""
    jan4 = datetime(year, 1, 4)
    start_of_week1 = jan4 - timedelta(days=jan4.weekday())
    start_date = start_of_week1 + timedelta(weeks=week_number - 1)
    end_date = start_date + timedelta(days=6)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def get_entries_for_week(entries_list: list[dict], year: int, week_number: int) -> list[dict]:
    """Filter entries to only those within a specific week."""
    start_str, end_str = get_week_date_range(year, week_number)
    start_date = datetime.fromisoformat(start_str)
    end_date = datetime.fromisoformat(end_str) + timedelta(days=1)

    filtered = []
    for entry in entries_list:
        try:
            ts = entry.get('timestamp', '')
            if ts:
                entry_date = datetime.fromisoformat(ts.replace('Z', '+00:00').split('+')[0])
                if start_date <= entry_date < end_date:
                    filtered.append(entry)
        except (ValueError, TypeError):
            continue
    return filtered


@router.post("/generate")
async def generate_analysis(request: AnalysisRequest):
    try:
        # Get all entries first
        all_entries = await entries.get_all_entries(limit=500)

        if request.report_type == "weekly":
            # Filter by week if specified
            if request.year and request.week_number:
                entries_list = get_entries_for_week(all_entries, request.year, request.week_number)
                week_label = f"Week {request.week_number}, {request.year}"
            else:
                # Default to current week
                now = datetime.now()
                entries_list = get_entries_for_week(all_entries, now.year, now.isocalendar()[1])
                week_label = f"Current Week (Week {now.isocalendar()[1]}, {now.year})"

            if not entries_list:
                content = f"## {week_label}\n\nNo entries found for this period."
            else:
                content = await llm_service.generate_weekly_summary(entries_list, week_label)

        elif request.report_type == "comprehensive":
            # Generate a comprehensive report covering all data
            stats = await entries.get_dashboard_stats()
            pending = [e for e in all_entries if e.get('status') in ('PENDING', 'ASSIGNED', 'ONGOING')]
            completed = [e for e in all_entries if e.get('status') == 'COMPLETED']
            content = await llm_service.generate_comprehensive_report(all_entries, stats, pending, completed)

        elif request.report_type == "overdue":
            now = datetime.now()
            overdue = []
            for e in all_entries:
                if e.get('eta') and e.get('status') != 'COMPLETED':
                    try:
                        eta = datetime.fromisoformat(e['eta'].replace('Z', '+00:00').split('+')[0])
                        if eta < now:
                            overdue.append(e)
                    except (ValueError, TypeError):
                        continue
            content = await llm_service.detect_overdue_tasks(overdue)

        elif request.report_type == "next_steps":
            recent = all_entries[:10]
            pending = [e for e in all_entries if e.get('status') in ('PENDING', 'ASSIGNED')]
            content = await llm_service.suggest_next_steps(recent, pending)

        elif request.report_type == "patterns":
            content = await llm_service.analyze_patterns(all_entries[:100])

        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

        # Save report to database
        db = await get_db()
        try:
            period_start = request.start_date
            period_end = request.end_date
            if request.report_type == "weekly" and request.year and request.week_number:
                period_start, period_end = get_week_date_range(request.year, request.week_number)

            await db.execute(
                """INSERT INTO analysis_reports (report_type, period_start, period_end, content, generated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    request.report_type,
                    period_start,
                    period_end,
                    content,
                    datetime.now().isoformat()
                )
            )
            await db.commit()
        finally:
            await db.close()

        return {"content": content, "report_type": request.report_type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weeks")
async def list_available_weeks():
    """Get list of weeks that have entries."""
    all_entries = await entries.get_all_entries(limit=5000)
    weeks = {}

    for entry in all_entries:
        try:
            ts = entry.get('timestamp', '')
            if ts:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00').split('+')[0])
                iso = dt.isocalendar()
                key = (iso[0], iso[1])
                if key not in weeks:
                    weeks[key] = {"year": iso[0], "week": iso[1], "count": 0}
                weeks[key]["count"] += 1
        except (ValueError, TypeError):
            continue

    sorted_weeks = sorted(weeks.values(), key=lambda x: (x["year"], x["week"]), reverse=True)
    return sorted_weeks


@router.get("/reports")
async def list_reports(limit: int = 20):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM analysis_reports ORDER BY generated_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


@router.get("/reports/{report_id}")
async def get_report(report_id: int):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM analysis_reports WHERE id = ?",
            (report_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        return dict(row)
    finally:
        await db.close()


@router.delete("/reports/{report_id}")
async def delete_report(report_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM analysis_reports WHERE id = ?", (report_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"status": "deleted"}
    finally:
        await db.close()


@router.delete("/reports")
async def delete_all_reports():
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM analysis_reports")
        await db.commit()
        return {"status": "deleted", "count": cursor.rowcount}
    finally:
        await db.close()


@router.get("/reports/{report_id}/download")
async def download_report(report_id: int):
    """Download report as markdown file."""
    from fastapi.responses import Response
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM analysis_reports WHERE id = ?",
            (report_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")

        report = dict(row)
        filename = f"{report['report_type']}_{report['generated_at'][:10]}.md"

        # Add metadata header
        content = f"""---
report_type: {report['report_type']}
period_start: {report.get('period_start', 'N/A')}
period_end: {report.get('period_end', 'N/A')}
generated_at: {report['generated_at']}
---

{report['content']}
"""
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    finally:
        await db.close()


@router.get("/reports/download-all")
async def download_all_reports():
    """Download all reports as a combined markdown file."""
    from fastapi.responses import Response
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM analysis_reports ORDER BY generated_at DESC"
        )
        rows = await cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No reports found")

        content = "# Personal Log Manager - All Reports\n\n"
        for row in rows:
            report = dict(row)
            content += f"""---

## {report['report_type'].title()} Report
**Generated:** {report['generated_at']}
**Period:** {report.get('period_start', 'N/A')} to {report.get('period_end', 'N/A')}

{report['content']}

"""

        filename = f"all_reports_{datetime.now().strftime('%Y-%m-%d')}.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    finally:
        await db.close()


@router.get("/test-llm")
async def test_llm_connection():
    """Test the LLM connection with a simple prompt."""
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'LLM connection successful!' in 5 words or less."}
        ]
        result = await llm_service.call_llm(messages)
        return {"status": "success", "response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
