from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime

import anthropic

from .config import render_resume_text, settings
from .models import Job, JobAnalysis

RESUME_TEXT = render_resume_text()

HAIKU_PROMPT = """\
You are a job-match analyst. Respond ONLY with valid JSON, no prose outside the JSON.

## Candidate Resume
{resume}

## Job Posting
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

## Task
Score this job for the candidate on a 1–10 scale. Be strict.

Score rubric:
9-10: Perfect fit — apply immediately
7-8: Strong match, minor gaps
5-6: Partial match, worth reading
3-4: Stretch role, significant gaps
1-2: Poor fit

Return this exact JSON structure:
{{
  "score": <number 1-10>,
  "matched_skills": ["<skill>", ...],
  "gaps": ["<gap>", ...],
  "rationale": "<2-3 sentence explanation>"
}}"""

SONNET_PROMPT = """\
You are a job-match analyst and senior career advisor for a world-class product design leader.
Respond ONLY with valid JSON.

## Candidate Resume
{resume}

## Job Posting
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

## Task
Provide a detailed match analysis and write a tailored cover letter.

Return this exact JSON structure:
{{
  "score": <number 1-10, can refine the initial score>,
  "matched_skills": ["<skill>", ...],
  "gaps": ["<gap>", ...],
  "rationale": "<2-3 sentence explanation>",
  "detailed_analysis": "<3-4 paragraph analysis of fit, company context, and how the candidate's background maps to this role>",
  "cover_letter": "<300-word cover letter in the candidate's voice: confident, thoughtful, design-led. Reference AI interaction design work and proven outcomes. Avoid generic phrases. Address the hiring manager as 'Dear Hiring Team' unless a name is in the posting.>"
}}"""


def _build_prompt(template: str, job: Job) -> str:
    return template.format(
        resume=RESUME_TEXT,
        title=job.title,
        company=job.company,
        location=job.location,
        description=(job.description or "")[:4000],
    )


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(text)


class Matcher:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._semaphore = asyncio.Semaphore(settings.concurrency_limit)

    async def _call_claude(self, model: str, prompt: str) -> dict:
        async with self._semaphore:
            msg = await self._client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text
            return _parse_json_response(text)

    async def score_job(self, job: Job, model: str) -> JobAnalysis:
        is_sonnet = model == settings.sonnet_model
        prompt = _build_prompt(SONNET_PROMPT if is_sonnet else HAIKU_PROMPT, job)
        try:
            result = await self._call_claude(model, prompt)
        except Exception as e:
            return JobAnalysis(
                job_id=job.id,
                score=0.0,
                rationale=f"Analysis failed: {e}",
                model_used=model,
            )

        return JobAnalysis(
            job_id=job.id,
            score=float(result.get("score", 0)),
            rationale=result.get("rationale", ""),
            key_matches=result.get("matched_skills", []),
            gaps=result.get("gaps", []),
            detailed_analysis=result.get("detailed_analysis", ""),
            cover_letter=result.get("cover_letter", ""),
            model_used=model,
            analyzed_at=datetime.utcnow(),
        )

    async def score_all(
        self,
        jobs: list[Job],
        already_analyzed: set[str],
        top_n_for_sonnet: int | None = None,
    ) -> list[JobAnalysis]:
        if top_n_for_sonnet is None:
            top_n_for_sonnet = settings.top_n_for_sonnet

        new_jobs = [j for j in jobs if j.id not in already_analyzed]
        if not new_jobs:
            return []

        haiku_tasks = [self.score_job(j, settings.haiku_model) for j in new_jobs]
        haiku_results: list[JobAnalysis] = await asyncio.gather(*haiku_tasks)

        haiku_results.sort(key=lambda a: a.score, reverse=True)
        top_jobs_map = {
            a.job_id: j
            for a, j in zip(haiku_results[:top_n_for_sonnet], new_jobs[:top_n_for_sonnet])
            if a.score >= 7.0
        }

        final: list[JobAnalysis] = []
        job_map = {j.id: j for j in new_jobs}

        for analysis in haiku_results:
            if analysis.job_id in top_jobs_map:
                sonnet_analysis = await self.score_job(
                    top_jobs_map[analysis.job_id], settings.sonnet_model
                )
                final.append(sonnet_analysis)
            else:
                final.append(analysis)

        return final
