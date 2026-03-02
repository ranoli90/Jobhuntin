"""Staffing Agency models — candidate profiles for bulk ATS submission."""

from __future__ import annotations

from pydantic import BaseModel


class CandidateProfile(BaseModel):
    """Profile for a single candidate to submit to a client ATS."""

    full_name: str
    email: str
    phone: str = ""
    linkedin_url: str = ""
    resume_url: str = ""
    resume_text: str = ""
    title: str = ""
    years_experience: int = 0
    skills: list[str] = []
    location: str = ""
    salary_expectation: str = ""
    availability: str = "Immediate"
    work_authorization: str = "Authorized"
    notes: str = ""


class StaffingBatchRequest(BaseModel):
    """Request to submit a batch of candidates to a client portal."""

    client_name: str
    client_portal: str  # URL of client ATS/Greenhouse/Lever
    role_title: str
    role_description: str = ""
    candidates: list[CandidateProfile]
    priority: str = "normal"  # normal, urgent
