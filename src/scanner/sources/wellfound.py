from __future__ import annotations

import json
import re

import httpx

from ..models import Job
from .base import BaseFetcher

SEARCH_URL = "https://wellfound.com/jobs?role=product-designer&remote=true"
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)


class WellfoundFetcher(BaseFetcher):
    name = "wellfound"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
            resp = await client.get(SEARCH_URL, headers=headers, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text
        except Exception:
            return []

        match = NEXT_DATA_RE.search(html)
        if not match:
            return []

        try:
            next_data = json.loads(match.group(1))
            listings = (
                next_data.get("props", {})
                .get("pageProps", {})
                .get("jobListings", {})
                .get("jobs", [])
            )
        except Exception:
            return []

        jobs = []
        for item in listings:
            job_id = str(item.get("id", ""))
            startup = item.get("startup", {})
            company = startup.get("name", "") if isinstance(startup, dict) else ""
            slug = item.get("slug", job_id)

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id or slug),
                    source=self.name,
                    title=item.get("title", ""),
                    company=company,
                    url=f"https://wellfound.com/jobs/{slug}",
                    description=item.get("description", ""),
                    location=item.get("locationNames", ["Remote"])[0] if item.get("locationNames") else "Remote",
                    job_type="remote" if item.get("remote", True) else "hybrid",
                )
            )
        return self._safe_fetch(jobs)
