from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Vercel sets VERCEL=1 automatically; use /tmp for ephemeral SQLite
_on_vercel = bool(os.environ.get("VERCEL"))
_default_db = Path("/tmp/jobs.db") if _on_vercel else Path("data/jobs.db")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="")
    haiku_model: str = "claude-haiku-4-5-20251001"
    sonnet_model: str = "claude-sonnet-4-6"
    top_n_for_sonnet: int = 5
    scan_hour: int = 8
    min_score_display: float = 5.0
    request_timeout: int = 30
    concurrency_limit: int = 5
    infojobs_api_key: str = Field(default="")

    db_path: Path = Field(default=_default_db)


settings = Settings()


RESUME = {
    "name": "Marcel Darienzo",
    "current_role": "UX Lead, Alef Education (Abu Dhabi, UAE)",
    "target_roles": [
        "Product Design Lead",
        "UX Lead",
        "Head of Product Design",
        "Head of UX",
        "Lead Product Designer",
        "Principal Designer",
        "Design Director",
    ],
    "summary": (
        "Award-winning Product Design Lead specialising in human-AI interaction, "
        "adaptive intelligence systems, and behavioural product design at global scale. "
        "Translates complex research and emerging technologies into intuitive, high-impact "
        "products. Aligns multidisciplinary teams to deliver measurable outcomes and "
        "large-scale product transformation."
    ),
    "core_skills": [
        "AI Interaction Design",
        "Trust & Identity UX / Self-Sovereign Identity (SSI)",
        "Behavioural Product Design",
        "Product Strategy",
        "Design Leadership",
        "Cross-functional Team Leadership",
        "User Research",
        "Prototyping",
        "Design Systems",
        "Stakeholder Management",
        "Figma",
        "FigJam",
        "Miro",
        "Amplitude",
        "Maze",
        "Jira / Confluence",
        "EdTech",
        "Web3 / Blockchain UX",
    ],
    "highlights": [
        "Led full redesign of personalised adaptive AI learning platform — +41% unique active users",
        "Alef Pathways awarded 'Best Educational Resource/Product' at GESS Education Awards 2025",
        "Gamification system: +15% level completion and improved measurable learning outcomes",
        "Personalised comms system: +91% click-through rate",
        "Course builder redesign: -80% task completion time",
        "Established SSI UX vision that helped Twinds Foundation secure Horizon Europe funding",
        "13-year independent practice across 5 countries; collaborated with Tate Modern, Serpentine, ICA London, Manifesta 11",
    ],
    "education": [
        "Doctoral Research (In Progress) — Freie Universität Berlin. Thesis: 'Simulation Realness: Art in the Age of Consciousness'",
        "MFA Fine Arts (Pass with Merit) — Goldsmiths, University of London",
        "BA Fine Arts (Highest Honors 10/10) — FAAP, São Paulo",
        "Behavioural Design Certification — Hyper Island (2025)",
        "UX/UI Bootcamp — Ironhack, Berlin (2020)",
    ],
    "languages": ["Portuguese (native)", "English (fluent)", "Spanish (advanced)", "German (intermediate)"],
    "target_locations": ["remote", "são paulo", "sao paulo", "barcelona", "spain", "brazil"],
    "contact": {
        "email": "mdarienzo@gmail.com",
        "linkedin": "https://linkedin.com/in/marceldarienzo",
        "portfolio": "https://marceldarienzo.com",
    },
}


def render_resume_text() -> str:
    r = RESUME
    skills = ", ".join(r["core_skills"])
    highlights = "\n".join(f"• {h}" for h in r["highlights"])
    education = "\n".join(f"• {e}" for e in r["education"])
    languages = ", ".join(r["languages"])
    target_roles = ", ".join(r["target_roles"])

    return f"""## Candidate: {r['name']}
Current role: {r['current_role']}
Target roles: {target_roles}

### Summary
{r['summary']}

### Core Skills
{skills}

### Key Achievements
{highlights}

### Education
{education}

### Languages
{languages}

### Location Preference
Open to fully remote (globally accessible), or hybrid in São Paulo (Brazil) or Barcelona (Spain).
Italian-Brazilian EU citizen — no visa sponsorship needed for EU roles."""


TITLE_KEYWORDS = [
    "product design lead",
    "design lead",
    "ux lead",
    "lead designer",
    "lead product designer",
    "head of design",
    "head of ux",
    "head of product design",
    "principal designer",
    "design director",
    "director of design",
    "director of ux",
    "vp design",
    "vp of design",
    "senior product designer",
    "senior ux designer",
]

LOCATION_KEYWORDS = [
    "remote",
    "anywhere",
    "worldwide",
    "global",
    "brazil",
    "brasil",
    "são paulo",
    "sao paulo",
    "barcelona",
    "spain",
    "españa",
    "latam",
    "latin america",
    "europe",
    "eu",
]

GREENHOUSE_COMPANY_SLUGS = [
    "figma",
    "canva",
    "duolingo",
    "notion",
    "miro",
    "intercom",
    "typeform",
    "brainly",
    "nubank",
    "klarna",
    "wise",
    "revolut",
    "stripe",
    "linear",
    "loom",
    "pitch",
    "superhuman",
    "retool",
    "vercel",
    "airtable",
]
