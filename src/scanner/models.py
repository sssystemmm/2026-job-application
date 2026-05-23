from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Job(BaseModel):
    id: str
    source: str
    title: str
    company: str
    url: str
    description: str
    location: str = ""
    job_type: str = "remote"
    tags: list[str] = Field(default_factory=list)
    posted_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("description", mode="before")
    @classmethod
    def truncate_description(cls, v: str) -> str:
        return (v or "")[:8000]

    @staticmethod
    def make_id(source: str, external_id: str) -> str:
        raw = f"{source}:{external_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]


class JobAnalysis(BaseModel):
    job_id: str
    score: float
    rationale: str = ""
    key_matches: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    detailed_analysis: str = ""
    cover_letter: str = ""
    model_used: str = ""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ScanStatus(BaseModel):
    running: bool = False
    started_at: Optional[datetime] = None
    message: str = ""
    fetched: int = 0
    filtered: int = 0
    new_jobs: int = 0
    scored: int = 0
