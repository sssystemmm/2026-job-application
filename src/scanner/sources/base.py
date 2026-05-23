from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ..models import Job


class BaseFetcher(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch(self, client: httpx.AsyncClient) -> list[Job]:
        ...

    def _safe_fetch(self, items: list[Job]) -> list[Job]:
        return [j for j in items if j.title and j.url]
