from __future__ import annotations

import asyncio
import difflib

import httpx

from .config import LOCATION_KEYWORDS, TITLE_KEYWORDS
from .models import Job, ScanStatus
from .sources.arbeitnow import ArbeitnowFetcher
from .sources.authenticjobs import AuthenticJobsFetcher
from .sources.dribbble import DribbbleFetcher
from .sources.greenhouse import GreenhouseFetcher
from .sources.infojobs import InfojobsFetcher
from .sources.jobicy import JobicyFetcher
from .sources.remoteok import RemoteOKFetcher
from .sources.remotive import RemotiveFetcher
from .sources.torre import TorreFetcher
from .sources.uxjobsboard import UXJobsBoardFetcher
from .sources.wellfound import WellfoundFetcher
from .sources.workingnomads import WorkingNomadsFetcher

ALL_SOURCES = [
    RemotiveFetcher(),
    RemoteOKFetcher(),
    JobicyFetcher(),
    ArbeitnowFetcher(),
    WorkingNomadsFetcher(),
    AuthenticJobsFetcher(),
    WellfoundFetcher(),
    GreenhouseFetcher(),
    TorreFetcher(),
    InfojobsFetcher(),
    UXJobsBoardFetcher(),
    DribbbleFetcher(),
]

SOURCE_MAP = {s.name: s for s in ALL_SOURCES}


def filter_jobs(jobs: list[Job]) -> list[Job]:
    filtered = []
    for job in jobs:
        title_lower = job.title.lower()
        if not any(kw in title_lower for kw in TITLE_KEYWORDS):
            continue
        loc_lower = (job.location or "").lower()
        desc_lower = (job.description or "")[:500].lower()
        is_remote = job.job_type in ("remote", "remote-friendly")
        has_location = any(kw in loc_lower or kw in desc_lower for kw in LOCATION_KEYWORDS)
        if not (is_remote or has_location):
            continue
        filtered.append(job)
    return filtered


def deduplicate(jobs: list[Job], seen_ids: set[str]) -> list[Job]:
    new_jobs: list[Job] = []
    seen_fingerprints: set[str] = set()

    for job in jobs:
        if job.id in seen_ids:
            continue
        fingerprint = f"{job.title.lower().strip()}|{job.company.lower().strip()}"
        is_duplicate = False
        for existing in seen_fingerprints:
            ratio = difflib.SequenceMatcher(None, fingerprint, existing).ratio()
            if ratio > 0.85:
                is_duplicate = True
                break
        if not is_duplicate:
            new_jobs.append(job)
            seen_fingerprints.add(fingerprint)

    return new_jobs


async def fetch_all(
    source_names: list[str] | None = None,
    status: ScanStatus | None = None,
) -> list[Job]:
    sources = (
        [SOURCE_MAP[n] for n in source_names if n in SOURCE_MAP]
        if source_names
        else ALL_SOURCES
    )

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        tasks = [source.fetch(client) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: list[Job] = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)

    if status:
        status.fetched = len(all_jobs)

    return all_jobs
