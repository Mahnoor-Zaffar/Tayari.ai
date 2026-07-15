"""Seed the database with initial companies, roles, and interview templates."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session

# Import all models to ensure they are registered with SQLAlchemy
from features.auth.models import User  # noqa: F401,E402
from features.interview.models import Interview, InterviewConfiguration, InterviewTemplate, JobDescription, Resume, UserTemplate  # noqa: F401,E402
from features.reports.models import Evaluation  # noqa: F401,E402
from features.billing.models import BillingEvent, Subscription  # noqa: F401,E402

COMPANIES = [
    "Google", "Meta", "Amazon", "Apple", "Microsoft", "Netflix", "Tesla",
    "Stripe", "Airbnb", "Uber", "Lyft", "Spotify", "Adobe", "Salesforce",
    "Oracle", "IBM", "Intel", "Nvidia", "LinkedIn", "Slack", "Square",
    "Palantir", "Snowflake", "Datadog", "Databricks", "ByteDance", "Snap",
    "Pinterest", "Reddit",
]

ROLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Software Engineer",
    "Frontend Engineer", "Backend Engineer", "Full-Stack Engineer",
    "DevOps Engineer", "Site Reliability Engineer", "Machine Learning Engineer",
    "Data Engineer", "Security Engineer", "Engineering Manager",
    "Technical Lead", "Principal Engineer",
]

TEMPLATES = [
    {
        "name": "FAANG Frontend Coding",
        "description": "Standard frontend engineering interview at a large tech company",
        "interview_type": "coding",
        "default_company": "Google",
        "default_role": "Frontend Engineer",
        "default_experience_level": "mid-senior",
        "default_language": "javascript",
        "default_framework": "react",
        "default_difficulty": "hard",
        "default_duration_minutes": 45,
    },
    {
        "name": "Backend System Design",
        "description": "System design interview focused on distributed systems",
        "interview_type": "system-design",
        "default_company": "Amazon",
        "default_role": "Backend Engineer",
        "default_experience_level": "staff-lead",
        "default_difficulty": "hard",
        "default_duration_minutes": 45,
    },
    {
        "name": "Behavioral + Leadership",
        "description": "Behavioral interview with leadership-focused questions",
        "interview_type": "behavioral",
        "default_company": "Meta",
        "default_role": "Engineering Manager",
        "default_experience_level": "staff-lead",
        "default_difficulty": "medium",
        "default_duration_minutes": 30,
    },
    {
        "name": "Junior Coding Warm-up",
        "description": "Entry-level coding interview with fundamentals",
        "interview_type": "coding",
        "default_company": "Startup",
        "default_role": "Junior Software Engineer",
        "default_experience_level": "junior",
        "default_language": "python",
        "default_difficulty": "easy",
        "default_duration_minutes": 30,
    },
]


async def seed() -> None:
    async with async_session() as session:
        result = await session.execute(select(InterviewTemplate).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("Templates already exist — skipping seed.")
            return

        for tmpl in TEMPLATES:
            session.add(InterviewTemplate(
                id=uuid.uuid4(),
                name=tmpl["name"],
                description=tmpl["description"],
                interview_type=tmpl["interview_type"],
                default_company=tmpl.get("default_company"),
                default_role=tmpl.get("default_role"),
                default_experience_level=tmpl.get("default_experience_level"),
                default_language=tmpl.get("default_language"),
                default_framework=tmpl.get("default_framework"),
                default_difficulty=tmpl["default_difficulty"],
                default_duration_minutes=tmpl["default_duration_minutes"],
                is_active=True,
            ))

        await session.commit()
        print(f"Seeded {len(TEMPLATES)} templates and {len(COMPANIES)} companies.")


if __name__ == "__main__":
    asyncio.run(seed())
