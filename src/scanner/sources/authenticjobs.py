from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

from ..models import Job
from .base import BaseFetcher

RSS_URL = "https://authenticjobs.com/jobs/feed/?job-type=full-time&keywords=design+lead"


class AuthenticJobsFetcher(BaseFetcher):
    name = "authenticjobs"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        try:
            resp = await client.get(RSS_URL, timeout=30)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except Exception:
            return []

        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        items = root.findall(".//item")
        jobs = []
        for item in items:
            def text(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""

            title = text("title")
            url = text("link") or text("guid")
            company = text("dc:creator") or text("{http://purl.org/dc/elements/1.1/}creator")
            description = text("description")
            pub_date_str = text("pubDate")
            posted_at = None
            try:
                posted_at = parsedate_to_datetime(pub_date_str) if pub_date_str else None
            except Exception:
                pass

            jobs.append(
                Job(
                    id=Job.make_id(self.name, url or title),
                    source=self.name,
                    title=title,
                    company=company,
                    url=url,
                    description=description,
                    location="Remote",
                    job_type="remote",
                    posted_at=posted_at,
                )
            )
        return self._safe_fetch(jobs)
