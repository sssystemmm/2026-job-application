from __future__ import annotations

from datetime import datetime

import httpx

from ..config import settings
from ..models import Job
from .base import BaseFetcher

API_URL = "https://api.infojobs.net/api/9/offer"


class InfojobsFetcher(BaseFetcher):
    name = "infojobs"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        if not settings.infojobs_api_key:
            return []

        try:
            resp = await client.get(
                API_URL,
                params={
                    "q": "product design lead",
                    "province": "barcelona",
                    "teleworking": 1,
                    "maxResults": 50,
                },
                headers={"Authorization": f"Basic {settings.infojobs_api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("items", []):
            job_id = str(item.get("id", ""))
            posted_raw = item.get("published", "")
            try:
                posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
            except Exception:
                posted_at = None

            telework = item.get("teleworking", {})
            job_type = "remote" if telework.get("id") == 1 else "hybrid"

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id),
                    source=self.name,
                    title=item.get("title", ""),
                    company=item.get("author", {}).get("commercialName", ""),
                    url=item.get("link", ""),
                    description=item.get("description", ""),
                    location=item.get("city", "Barcelona"),
                    job_type=job_type,
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
