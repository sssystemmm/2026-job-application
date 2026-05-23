from __future__ import annotations

import json
import re

import httpx

from ..models import Job
from .base import BaseFetcher

SEARCH_URL = "https://dribbble.com/jobs?location=remote&skills=product-design"
JSON_LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)


class DribbbleFetcher(BaseFetcher):
    name = "dribbble"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            }
            resp = await client.get(SEARCH_URL, headers=headers, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text
        except Exception:
            return []

        jobs = []
        for match in JSON_LD_RE.finditer(html):
            try:
                data = json.loads(match.group(1))
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            items = data if data.get("@type") == "JobPosting" else None
            if data.get("@type") == "ItemList":
                items_list = data.get("itemListElement", [])
                for elem in items_list:
                    item = elem.get("item", elem)
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        job = self._parse_job_posting(item)
                        if job:
                            jobs.append(job)
                continue

            if items:
                job = self._parse_job_posting(items)
                if job:
                    jobs.append(job)

        return self._safe_fetch(jobs)

    def _parse_job_posting(self, item: dict) -> Job | None:
        title = item.get("title", "") or item.get("name", "")
        url = item.get("url", "") or item.get("@id", "")
        company = ""
        org = item.get("hiringOrganization", {})
        if isinstance(org, dict):
            company = org.get("name", "")

        desc = item.get("description", "")
        location = item.get("jobLocation", {})
        if isinstance(location, dict):
            addr = location.get("address", {})
            location_str = addr.get("addressLocality", "Remote") if isinstance(addr, dict) else "Remote"
        else:
            location_str = "Remote"

        if not title or not url:
            return None

        return Job(
            id=Job.make_id(self.name, url),
            source=self.name,
            title=title,
            company=company,
            url=url,
            description=desc,
            location=location_str,
            job_type="remote",
        )
