from __future__ import annotations

from datetime import datetime

import httpx

from ..models import Job
from .base import BaseFetcher


class JobicyFetcher(BaseFetcher):
    name = "jobicy"
    _url = "https://jobicy.com/api/v2/remote-jobs"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(
                self._url,
                params={"count": 50, "tag": "design"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("jobs", []):
            job_id = str(item.get("id", ""))
            posted_raw = item.get("pubDate", "")
            try:
                posted_at = datetime.fromisoformat(posted_raw)
            except Exception:
                posted_at = None

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id or item.get("url", "")),
                    source=self.name,
                    title=item.get("jobTitle", ""),
                    company=item.get("companyName", ""),
                    url=item.get("url", ""),
                    description=item.get("jobDescription", ""),
                    location=item.get("jobGeo", "Remote"),
                    job_type="remote",
                    tags=[item.get("jobIndustry", ""), item.get("jobType", "")],
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
