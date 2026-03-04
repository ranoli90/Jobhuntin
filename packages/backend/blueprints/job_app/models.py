"""Job-seeker profile model — Sorce's specialization of ActorProfile.

Extends the generic ActorProfile with employment-specific fields
(current_title, current_company, years_experience) and maps Sorce's
CanonicalProfile structure onto the generic base.
"""

from __future__ import annotations

from typing import Any

from backend.domain.core_models import (
    ActorHistoryEntry,
    ActorIdentity,
    ActorProfile,
    ActorQualification,
)


class JobSeekerProfile(ActorProfile):
    """Sorce-specific extension of ActorProfile for job seekers.

    Adds employment-centric fields that don't belong in the generic base.
    """

    current_title: str = ""
    current_company: str = ""
    years_experience: int | None = None


def from_canonical_profile(canonical: dict) -> JobSeekerProfile:
    """Convert a raw Sorce CanonicalProfile dict (as stored in profiles.profile_data)
    into a JobSeekerProfile instance.
    """
    contact = canonical.get("contact", {})
    identity = ActorIdentity(
        full_name=contact.get("full_name", ""),
        first_name=contact.get("first_name", ""),
        last_name=contact.get("last_name", ""),
        email=contact.get("email", ""),
        phone=contact.get("phone", ""),
        location=contact.get("location", ""),
    )

    qualifications = [
        ActorQualification(
            institution=e.get("institution", ""),
            title=e.get("degree", ""),
            field=e.get("field_of_study", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date", ""),
            details=e.get("gpa", ""),
        )
        for e in canonical.get("education", [])
    ]

    history = [
        ActorHistoryEntry(
            organization=x.get("company", ""),
            role=x.get("title", ""),
            start_date=x.get("start_date", ""),
            end_date=x.get("end_date", ""),
            location=x.get("location", ""),
            description=x.get("responsibilities", []),
        )
        for x in canonical.get("experience", [])
    ]

    skills_raw = canonical.get("skills", {})
    skills = {
        "technical": skills_raw.get("technical", []),
        "soft": skills_raw.get("soft", []),
    }

    return JobSeekerProfile(
        identity=identity,
        qualifications=qualifications,
        history=history,
        skills=skills,
        certifications=canonical.get("certifications", []),
        languages=canonical.get("languages", []),
        summary=canonical.get("summary", ""),
        current_title=canonical.get("current_title", ""),
        current_company=canonical.get("current_company", ""),
        years_experience=canonical.get("years_experience"),
        metadata={
            "linkedin_url": contact.get("linkedin_url", ""),
            "portfolio_url": contact.get("portfolio_url", ""),
        },
    )


def to_canonical_dict(profile: JobSeekerProfile) -> dict[str, Any]:
    """Convert a JobSeekerProfile back to the Sorce CanonicalProfile dict shape
    for backward compatibility with existing DB storage and LLM prompts.
    """
    return {
        "contact": {
            "full_name": profile.identity.full_name,
            "first_name": profile.identity.first_name,
            "last_name": profile.identity.last_name,
            "email": profile.identity.email,
            "phone": profile.identity.phone,
            "location": profile.identity.location,
            "linkedin_url": profile.metadata.get("linkedin_url", ""),
            "portfolio_url": profile.metadata.get("portfolio_url", ""),
        },
        "education": [
            {
                "institution": q.institution,
                "degree": q.title,
                "field_of_study": q.field,
                "start_date": q.start_date,
                "end_date": q.end_date,
                "gpa": q.details,
            }
            for q in profile.qualifications
        ],
        "experience": [
            {
                "company": h.organization,
                "title": h.role,
                "start_date": h.start_date,
                "end_date": h.end_date,
                "location": h.location,
                "responsibilities": h.description,
            }
            for h in profile.history
        ],
        "skills": profile.skills,
        "certifications": profile.certifications,
        "languages": profile.languages,
        "summary": profile.summary,
        "current_title": profile.current_title,
        "current_company": profile.current_company,
        "years_experience": profile.years_experience,
    }
