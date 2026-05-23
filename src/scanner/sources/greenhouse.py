from __future__ import annotations

import asyncio

import httpx

from ..config import GREENHOUSE_COMPANY_SLUGS, TITLE_KEYWORDS
from ..models import Job
from .base import BaseFetcher


class GreenhouseFetcher(BaseFetcher):
    name = "greenhouse"
    _base = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        tasks = [self._fetch_company(client, slug) for slug in GREENHOUSE_COMPANY_SLUGS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        jobs: list[Job] = []
        for result in results:
            if isinstance(result, list):
                jobs.extend(result)
        return self._safe_fetch(jobs)

    async def _fetch_company(self, client: httpx.AsyncClient, slug: str) -> list[Job]:
        try:
            resp = await client.get(
                self._base.format(slug=slug),
                params={"content": "true"},
                timeout=20,
            )
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        for item in data.get("jobs", []):
            title = item.get("title", "")
            if not any(kw in title.lower() for kw in TITLE_KEYWORDS):
                continue

            location_list = item.get("offices", []) or item.get("location", {})
            if isinstance(location_list, list):
                location = ", ".join(o.get("name", "") for o in location_list if isinstance(o, dict)) or "Remote"
            elif isinstance(location_list, dict):
                location = location_list.get("name", "Remote")
            else:
                location = "Remote"

            job_id = str(item.get("id", ""))
            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id),
                    source=self.name,
                    title=title,
                    company=slug.capitalize(),
                    url=item.get("absolute_url", ""),
                    description=item.get("content", ""),
                    location=location,
                    job_type="remote",
                )
            )
        return jobs
