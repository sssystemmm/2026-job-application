from __future__ import annotations

import re

import httpx

from ..models import Job
from .base import BaseFetcher

SEARCH_URL = "https://uxjobsboard.com/?s=design+lead&job_type=remote"
JOB_BLOCK_RE = re.compile(
    r'class="job_listing[^"]*"[^>]*>(.*?)</li>',
    re.DOTALL,
)
TITLE_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL)
COMPANY_RE = re.compile(r'class="company"[^>]*>(.*?)</strong>', re.DOTALL)
LINK_RE = re.compile(r'href="(https://uxjobsboard\.com/job/[^"]+)"')


class UXJobsBoardFetcher(BaseFetcher):
    name = "uxjobsboard"

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
        for block in JOB_BLOCK_RE.finditer(html):
            content = block.group(1)
            title_m = TITLE_RE.search(content)
            company_m = COMPANY_RE.search(content)
            link_m = LINK_RE.search(content)

            if not (title_m and link_m):
                continue

            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            company = re.sub(r"<[^>]+>", "", company_m.group(1)).strip() if company_m else ""
            url = link_m.group(1)

            jobs.append(
                Job(
                    id=Job.make_id(self.name, url),
                    source=self.name,
                    title=title,
                    company=company,
                    url=url,
                    description="",
                    location="Remote",
                    job_type="remote",
                )
            )
        return self._safe_fetch(jobs)
