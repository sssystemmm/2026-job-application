from __future__ import annotations

from datetime import datetime

import httpx

from ..models import Job
from .base import BaseFetcher

HEADERS = {"User-Agent": "job-scanner-personal/1.0"}


class RemoteOKFetcher(BaseFetcher):
    name = "remoteok"
    _url = "https://remoteok.com/api"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(
                self._url,
                params={"tags": "design"},
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data:
            if not isinstance(item, dict) or not item.get("position"):
                continue
            job_id = str(item.get("id", item.get("slug", "")))
            epoch = item.get("epoch", 0)
            try:
                posted_at = datetime.utcfromtimestamp(int(epoch)) if epoch else None
            except Exception:
                posted_at = None

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id),
                    source=self.name,
                    title=item.get("position", ""),
                    company=item.get("company", ""),
                    url=item.get("url", f"https://remoteok.com/remote-jobs/{job_id}"),
                    description=item.get("description", ""),
                    location=item.get("location", "Remote"),
                    job_type="remote",
                    tags=item.get("tags", []) or [],
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
