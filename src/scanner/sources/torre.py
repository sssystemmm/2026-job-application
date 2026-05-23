from __future__ import annotations

import httpx

from ..models import Job
from .base import BaseFetcher

SEARCH_URL = "https://torre.ai/api/opportunities/_search"


class TorreFetcher(BaseFetcher):
    name = "torre"

    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        payload = {
            "and": [
                {"skill": "product design"},
            ],
            "remote": True,
            "size": 50,
            "from": 0,
        }
        try:
            resp = await client.post(
                SEARCH_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        jobs = []
        opportunities = data.get("results", []) or data.get("opportunities", [])
        for item in opportunities:
            opp = item.get("opportunity", item)
            job_id = str(opp.get("id", opp.get("publicId", "")))
            locations = opp.get("locations", [])
            location = ", ".join(loc.get("name", "") for loc in locations) if locations else "Remote"
            org = opp.get("organizations", [{}])
            company = org[0].get("name", "") if org else ""

            jobs.append(
                Job(
                    id=Job.make_id(self.name, job_id),
                    source=self.name,
                    title=opp.get("objective", ""),
                    company=company,
                    url=f"https://torre.ai/opportunities/{opp.get('publicId', job_id)}",
                    description=opp.get("details", ""),
                    location=location or "Remote",
                    job_type="remote" if opp.get("remote", True) else "hybrid",
                )
            )
        return self._safe_fetch(jobs)
