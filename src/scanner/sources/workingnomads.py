from __future__ import annotations

from datetime import datetime

import httpx

from ..models import Job
from .base import BaseFetcher


class WorkingNomadsFetcher(BaseFetcher):
    name = "workingnomads"
    _url = "https://www.workingnomads.com/api/exposed_jobs/"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(
                self._url,
                params={"category": "design"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data if isinstance(data, list) else data.get("results", []):
            job_id = str(item.get("id", ""))
            posted_raw = item.get("pub_date", "")
            try:
                posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
            except Exception:
                posted_at = None

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id or item.get("url", "")),
                    source=self.name,
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    location="Remote",
                    job_type="remote",
                    tags=[item.get("category", "")],
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
