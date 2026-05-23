from __future__ import annotations

from datetime import datetime

import httpx

from ..models import Job
from .base import BaseFetcher


class RemotiveFetcher(BaseFetcher):
    name = "remotive"
    _url = "https://remotive.com/api/remote-jobs"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(
                self._url,
                params={"search": "product design", "limit": 100},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("jobs", []):
            job_id = str(item.get("id", ""))
            posted_raw = item.get("publication_date", "")
            try:
                posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
            except Exception:
                posted_at = None

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id or item.get("url", "")),
                    source=self.name,
                    title=item.get("title", ""),
                    company=item.get("company_name", ""),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    location=item.get("candidate_required_location", "Remote"),
                    job_type=item.get("job_type", "remote"),
                    tags=item.get("tags", []),
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
