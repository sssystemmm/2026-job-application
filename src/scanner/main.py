from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from .config import settings
from .database import (
    get_analyzed_ids,
    get_jobs_with_analyses,
    get_seen_ids,
    init_db,
    save_analysis,
    save_jobs,
)
from .matcher import Matcher
from .models import ScanStatus
from .scanner import deduplicate, fetch_all, filter_jobs

DASHBOARD_HTML = Path(__file__).parent / "templates" / "dashboard.html"

_scan_status = ScanStatus()
_scheduler = AsyncIOScheduler()


async def run_scan() -> None:
    global _scan_status
    if _scan_status.running:
        return

    _scan_status = ScanStatus(running=True, started_at=datetime.utcnow(), message="Fetching jobs...")
    try:
        await init_db(settings.db_path)

        raw_jobs = await fetch_all(status=_scan_status)
        _scan_status.message = f"Fetched {_scan_status.fetched} jobs. Filtering..."

        filtered = filter_jobs(raw_jobs)
        _scan_status.filtered = len(filtered)
        _scan_status.message = f"Filtered to {len(filtered)} relevant jobs. Deduplicating..."

        seen_ids = await get_seen_ids(settings.db_path)
        new_jobs = deduplicate(filtered, seen_ids)
        _scan_status.new_jobs = len(new_jobs)
        _scan_status.message = f"Found {len(new_jobs)} new jobs. Saving..."

        await save_jobs(new_jobs, settings.db_path)

        if new_jobs and settings.anthropic_api_key:
            _scan_status.message = f"Scoring {len(new_jobs)} new jobs with AI..."
            already_analyzed = await get_analyzed_ids(settings.db_path)
            matcher = Matcher()
            analyses = await matcher.score_all(new_jobs, already_analyzed)
            for analysis in analyses:
                await save_analysis(analysis, settings.db_path)
            _scan_status.scored = len(analyses)

        _scan_status.message = "Scan complete."
    except Exception as e:
        _scan_status.message = f"Scan failed: {e}"
    finally:
        _scan_status.running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db_path)
    _scheduler.add_job(run_scan, "cron", hour=settings.scan_hour, id="daily_scan")
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(title="Job Scanner", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return FileResponse(DASHBOARD_HTML, media_type="text/html")


@app.get("/api/jobs")
async def list_jobs(min_score: float = 0.0, limit: int = 200):
    jobs = await get_jobs_with_analyses(
        min_score=min_score,
        limit=limit,
        db_path=settings.db_path,
    )
    return {"jobs": jobs, "total": len(jobs)}


@app.post("/api/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    if _scan_status.running:
        return {"status": "already_running", "message": _scan_status.message}
    background_tasks.add_task(run_scan)
    return {"status": "started"}


@app.get("/api/scan/status")
async def scan_status():
    return _scan_status.model_dump()


@app.get("/api/jobs/{job_id}/cover-letter")
async def get_cover_letter(job_id: str):
    from .database import get_analysis
    analysis = await get_analysis(job_id, settings.db_path)
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this job")
    if not analysis.cover_letter:
        raise HTTPException(status_code=404, detail="No cover letter generated for this job")
    return {"cover_letter": analysis.cover_letter, "job_id": job_id}
