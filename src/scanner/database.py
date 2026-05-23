from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from .models import Job, JobAnalysis

DB_PATH = Path("data/jobs.db")

CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    location TEXT,
    job_type TEXT,
    tags TEXT,
    posted_at TEXT,
    fetched_at TEXT NOT NULL
)
"""

CREATE_ANALYSES = """
CREATE TABLE IF NOT EXISTS job_analyses (
    job_id TEXT PRIMARY KEY,
    score REAL,
    rationale TEXT,
    key_matches TEXT,
    gaps TEXT,
    detailed_analysis TEXT,
    cover_letter TEXT,
    model_used TEXT,
    analyzed_at TEXT NOT NULL
)
"""


async def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_JOBS)
        await db.execute(CREATE_ANALYSES)
        await db.commit()


async def get_seen_ids(db_path: Path = DB_PATH) -> set[str]:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id FROM jobs") as cursor:
            rows = await cursor.fetchall()
    return {row[0] for row in rows}


async def save_jobs(jobs: list[Job], db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        for job in jobs:
            await db.execute(
                """INSERT OR IGNORE INTO jobs
                   (id, source, title, company, url, description, location, job_type, tags, posted_at, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.id,
                    job.source,
                    job.title,
                    job.company,
                    job.url,
                    job.description,
                    job.location,
                    job.job_type,
                    json.dumps(job.tags),
                    job.posted_at.isoformat() if job.posted_at else None,
                    job.fetched_at.isoformat(),
                ),
            )
        await db.commit()


async def save_analysis(analysis: JobAnalysis, db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT OR REPLACE INTO job_analyses
               (job_id, score, rationale, key_matches, gaps, detailed_analysis, cover_letter, model_used, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis.job_id,
                analysis.score,
                analysis.rationale,
                json.dumps(analysis.key_matches),
                json.dumps(analysis.gaps),
                analysis.detailed_analysis,
                analysis.cover_letter,
                analysis.model_used,
                analysis.analyzed_at.isoformat(),
            ),
        )
        await db.commit()


async def get_jobs_with_analyses(
    min_score: float = 0.0,
    limit: int = 200,
    db_path: Path = DB_PATH,
) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT j.*, a.score, a.rationale, a.key_matches, a.gaps,
                      a.detailed_analysis, a.cover_letter, a.model_used, a.analyzed_at
               FROM jobs j
               LEFT JOIN job_analyses a ON j.id = a.job_id
               WHERE a.score IS NULL OR a.score >= ?
               ORDER BY COALESCE(a.score, 0) DESC, j.fetched_at DESC
               LIMIT ?""",
            (min_score, limit),
        ) as cursor:
            rows = await cursor.fetchall()

    results = []
    for row in rows:
        d = dict(row)
        d["tags"] = json.loads(d["tags"] or "[]")
        d["key_matches"] = json.loads(d["key_matches"] or "[]")
        d["gaps"] = json.loads(d["gaps"] or "[]")
        results.append(d)
    return results


async def get_analysis(job_id: str, db_path: Path = DB_PATH) -> Optional[JobAnalysis]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM job_analyses WHERE job_id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    d["key_matches"] = json.loads(d["key_matches"] or "[]")
    d["gaps"] = json.loads(d["gaps"] or "[]")
    return JobAnalysis(**d)


async def get_analyzed_ids(db_path: Path = DB_PATH) -> set[str]:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT job_id FROM job_analyses") as cursor:
            rows = await cursor.fetchall()
    return {row[0] for row in rows}
