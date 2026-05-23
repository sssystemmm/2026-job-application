from __future__ import annotations

from datetime import datetime

import httpx

from ..models import Job
from .base import BaseFetcher


class ArbeitnowFetcher(BaseFetcher):
    name = "arbeitnow"
    _url = "https://www.arbeitnow.com/api/job-board-api"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(self._url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("data", []):
            slug = item.get("slug", "")
            posted_raw = item.get("created_at", 0)
            try:
                posted_at = datetime.utcfromtimestamp(int(posted_raw)) if posted_raw else None
            except Exception:
                posted_at = None

            remote = item.get("remote", False)
            location = "Remote" if remote else item.get("location", "")

            jobs.append(
                Job(
                    id=Job.make_id(self.name, slug),
                    source=self.name,
                    title=item.get("title", ""),
                    company=item.get("company_name", ""),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    location=location,
                    job_type="remote" if remote else "onsite",
                    tags=item.get("tags", []) or [],
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
