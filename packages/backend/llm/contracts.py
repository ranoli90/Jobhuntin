"""Versioned prompt contracts for LLM interactions.

Each contract defines:
  - A Pydantic response model (the expected output schema)
  - A prompt template (multiline string with placeholders)
  - A builder function that fills the template

Versioned by naming convention: *_V1, *_V2, etc.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class UnresolvedField(BaseModel):
    selector: str
    question: str


# ===================================================================
# Contract 1: Resume Parsing → CanonicalProfile
# ===================================================================


class ContactInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""


class ExperienceEntry(BaseModel):
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    responsibilities: list[str] = Field(default_factory=list)


class SkillsInfo(BaseModel):
    technical: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class RichSkill(BaseModel):
    """A skill with confidence, context, and metadata for deep matching."""

    skill: str = Field(..., description="Skill name (e.g., 'React', 'Python')")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence score 0-1"
    )
    years_actual: float | None = Field(
        default=None, description="Years of actual usage"
    )
    context: str = Field(default="", description="How the skill was used")
    last_used: str | None = Field(default=None, description="Last usage date (YYYY-MM)")
    verified: bool = Field(default=False, description="Whether skill is verified")
    related_to: list[str] = Field(default_factory=list, description="Related skills")
    source: str = Field(
        default="resume", description="Source: resume, github, linkedin, manual"
    )
    project_count: int = Field(
        default=0, description="Number of projects using this skill"
    )


class RichSkillsInfo(BaseModel):
    """Rich skills with confidence and metadata for deep matching."""

    technical: list[RichSkill] = Field(
        default_factory=list, description="Technical skills with metadata"
    )
    soft: list[RichSkill] = Field(
        default_factory=list, description="Soft skills with metadata"
    )


class ResumeParseResponse_V1(BaseModel):
    """Expected JSON output from the resume parsing LLM call."""

    contact: ContactInfo = Field(default_factory=ContactInfo)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: SkillsInfo = Field(default_factory=SkillsInfo)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""


RESUME_PARSE_PROMPT_V1 = """Extract from resume. Return JSON only:
{resume_text}

Keys: contact(
    full_name,email,phone,location,linkedin_url,portfolio_url), education[](institution,degree,field_of_study,
    start_date,end_date,gpa), experience[](company,title,start_date,end_date,location,responsibilities[]),
    skills(technical[],soft[]), certifications[], languages[], summary.
Empty string/array if missing."""


def build_resume_parse_prompt(resume_text: str) -> str:
    text = resume_text.strip()
    text = " ".join(text.split())
    if len(text) > 8000:
        text = text[:8000] + "... [truncated]"
    return RESUME_PARSE_PROMPT_V1.format(resume_text=text)


class ResumeParseResponse_V2(BaseModel):
    """Enhanced resume parsing with rich skill extraction."""

    contact: ContactInfo = Field(default_factory=ContactInfo)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: RichSkillsInfo = Field(default_factory=RichSkillsInfo)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""
    years_experience: float = Field(
        default=0.0, description="Total years of experience"
    )


RESUME_PARSE_PROMPT_V2 = """You are an expert resume parser. Extract structured information with DEEP skill analysis.

## Resume Text
{resume_text}

## Instructions
Return ONLY a JSON object (no markdown fences) with these top-level keys:

{{
    "contact": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin_url": "",
        "portfolio_url": ""
    }},
    "education": [
        {{
            "institution": "",
            "degree": "",
            "field_of_study": "",
            "start_date": "",
            "end_date": "",
            "gpa": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "title": "",
            "start_date": "",
            "end_date": "",
            "location": "",
            "responsibilities": [""]
        }}
    ],
    "skills": {{
        "technical": [
            {{
                "skill": "React",
                "confidence": 0.85,
                "years_actual": 3.5,
                "context": "Built user dashboards and data visualization components",
                "last_used": "2024-01",
                "project_count": 4,
                "related_to": ["TypeScript", "Next.js", "Redux"]
            }}
        ],
        "soft": [
            {{
                "skill": "Leadership",
                "confidence": 0.7,
                "years_actual": 2.0,
                "context": "Led team of 5 engineers on product initiatives",
                "last_used": "2024-01",
                "project_count": 2,
                "related_to": ["Mentorship", "Project Management"]
            }}
        ]
    }},
    "certifications": [""],
    "languages": [""],
    "summary": "",
    "years_experience": 5.5
}}

## SKILL EXTRACTION RULES (CRITICAL):

1. **Confidence Score (0.0-1.0)**:
   - 0.9-1.0: Multiple projects with specific achievements, quantified impact
   - 0.7-0.89: Clear usage in 2+ projects with context
   - 0.5-0.69: Listed in skills section, mentioned in responsibilities
   - 0.3-0.49: Mentioned once or indirectly
   - 0.0-0.29: Just keyword match, unclear usage

2. **Years Actual**: Calculate from experience dates when skill was used

3. **Context**: ONE sentence describing HOW the skill was used

4. **Project Count**: Count distinct projects/roles where skill was applied

5. **Related Skills**: Skills commonly used together (max 5)

Extract 5-15 technical skills and 3-8 soft skills maximum.
"""


def build_resume_parse_prompt_v2(resume_text: str) -> str:
    """Fill the resume parse prompt V2 template."""
    text = resume_text.strip()
    text = " ".join(text.split())
    if len(text) > 12000:
        text = text[:12000] + "... [truncated]"
    return RESUME_PARSE_PROMPT_V2.format(resume_text=text)


# ===================================================================
# Contract 2: DOM Mapping → field values + unresolved fields
# ===================================================================


class DomMappingResponse_V1(BaseModel):
    """Expected JSON output from the DOM field mapping LLM call."""

    field_values: dict[str, str] = Field(default_factory=dict)
    unresolved_required_fields: list[UnresolvedField] = Field(default_factory=list)


DOM_MAPPING_PROMPT_V1 = """Fill form fields. Return JSON only.

Profile: {profile_json}
Answered: {answered_json}
Fields: {fields_json}

Rules:
1. Map selectors to values in field_values
2. Select/radio: return option value
3. Checkbox: "true" or "false"
4. Unresolved required fields: {{"selector":"...", "question":"..."}}
5. Answered questions override profile

Output: {{"field_values":{{}}, "unresolved_required_fields":[]}}"""


def build_dom_mapping_prompt(
    profile_dict: dict,
    form_fields: list[dict],
    answered_inputs: list[dict] | None = None,
) -> str:
    p = {k: v for k, v in profile_dict.items() if v}
    return DOM_MAPPING_PROMPT_V1.format(
        profile_json=json.dumps(p),
        answered_json=json.dumps(answered_inputs or []),
        fields_json=json.dumps(form_fields, default=str),
    )


# ===================================================================
# Contract 3: Role Suggestion from Resume
# ===================================================================


class RoleSuggestionResponse_V1(BaseModel):
    """AI-suggested job roles based on resume analysis."""

    suggested_roles: list[str] = Field(
        default_factory=list,
        description="Top 3-5 job titles that match the candidate's experience",
    )
    primary_role: str = Field(default="", description="The single best-fit role title")
    experience_level: str = Field(
        default="",
        description="Experience level: entry, mid, senior, staff, principal, executive",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1"
    )
    reasoning: str = Field(
        default="", description="Brief explanation of why these roles fit"
    )


ROLE_SUGGESTION_PROMPT_V1 = """Suggest roles for candidate. Return JSON only:
{profile_json}

Keys: suggested_roles[](
    3-5), primary_role, experience_level(entry|mid|senior|staff|principal|executive), confidence(0-1), reasoning."""


def build_role_suggestion_prompt(
    resume_text: str, skills: list[str], experience_years: int, education_level: str
) -> str:
    """Build prompt for AI role suggestions."""
    profile_dict = {
        "resume_text": resume_text,
        "skills": skills,
        "experience_years": experience_years,
        "education_level": education_level,
    }
    return ROLE_SUGGESTION_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2)
    )


# ===================================================================
# Contract 4: Salary Suggestion based on Role + Location + Skills
# ===================================================================


class SalarySuggestionResponse_V1(BaseModel):
    """AI-suggested salary range based on role, location, and skills."""

    min_salary: int = Field(default=0, description="Minimum suggested salary USD")
    max_salary: int = Field(default=0, description="Maximum suggested salary USD")
    market_median: int = Field(default=0, description="Estimated market median USD")
    currency: str = Field(default="USD", description="Currency code")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    factors: list[str] = Field(
        default_factory=list, description="Key factors influencing the estimate"
    )
    reasoning: str = Field(default="", description="Explanation of salary estimate")


SALARY_SUGGESTION_PROMPT_V1 = """Estimate salary. Return JSON only.

Profile: {profile_json}
Role: {target_role}
Location: {location}

Keys: min_salary, max_salary, market_median, currency(USD), confidence(0-1), factors[], reasoning."""


def build_salary_suggestion_prompt(
    skills: list[str],
    experience_years: int,
    education_level: str,
    target_role: str,
    location: str,
) -> str:
    """Build prompt for AI salary suggestions."""
    profile_dict = {
        "skills": skills,
        "experience_years": experience_years,
        "education_level": education_level,
    }
    return SALARY_SUGGESTION_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        target_role=target_role,
        location=location,
    )


# ===================================================================
# Contract 5: Location Suggestion based on Skills + Preferences
# ===================================================================


class LocationSuggestionResponse_V1(BaseModel):
    """AI-suggested locations based on skills and job market."""

    suggested_locations: list[str] = Field(
        default_factory=list, description="Top 3-5 recommended job markets"
    )
    remote_friendly_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How remote-friendly the candidate's skills are (0-1)",
    )
    top_markets: list[str] = Field(
        default_factory=list, description="Best physical job markets for their skills"
    )
    reasoning: str = Field(default="", description="Explanation of recommendations")


LOCATION_SUGGESTION_PROMPT_V1 = """Suggest locations. Return JSON only.

Profile: {profile_json}
Current: {current_location}

Keys: suggested_locations[](3-5), remote_friendly_score(0-1), top_markets[], reasoning."""


def build_location_suggestion_prompt(
    skills: list[str], role: str, experience_years: int, remote_preference: bool
) -> str:
    """Build prompt for AI location suggestions."""
    profile_dict = {
        "skills": skills,
        "role": role,
        "experience_years": experience_years,
        "remote_preference": remote_preference,
    }
    return LOCATION_SUGGESTION_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        current_location="Not specified",
    )


# ===================================================================
# Contract 6: Job Match Scoring
# ===================================================================


class JobMatchScore_V1(BaseModel):
    """AI-generated match score between candidate and job."""

    score: int = Field(default=0, ge=0, le=100, description="Overall match 0-100")
    skill_match: float = Field(default=0.0, ge=0.0, le=1.0)
    experience_match: float = Field(default=0.0, ge=0.0, le=1.0)
    location_match: float = Field(default=0.0, ge=0.0, le=1.0)
    culture_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    summary: str = Field(default="", description="One-line match summary")


JOB_MATCH_PROMPT_V1 = """Score candidate-job match. Return JSON only.

Profile: {profile_json}
Job: {job_json}

Keys: score(
    0-100), skill_match(0-1), experience_match(0-1), location_match(0-1), culture_signals[], red_flags[], summary."""


def build_job_match_prompt(profile_dict: dict, job_dict: dict) -> str:
    """Build prompt for AI job matching."""
    return JOB_MATCH_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        job_json=json.dumps(job_dict, indent=2),
    )


# ===================================================================
# Contract 7: Cover Letter Generation
# ===================================================================


class CoverLetterResponse_V1(BaseModel):
    """AI-generated cover letter."""

    content: str = Field(..., description="Markdown formatted cover letter text")
    subject_line: str = Field(..., description="Suggested email subject line")


COVER_LETTER_PROMPT_V1 = """Write cover letter. Return JSON only.

Profile: {profile_json}
Job: {job_json}
Tone: {tone}

Rules: Under 300 words. Professional. No invented facts.

Keys: subject_line, content(markdown)."""


def build_cover_letter_prompt(
    profile_dict: dict, job_dict: dict, tone: str = "professional"
) -> str:
    p = {
        k: v
        for k, v in profile_dict.items()
        if k in ("experience", "skills", "contact", "summary") and v
    }
    j = {
        k: v
        for k, v in job_dict.items()
        if k in ("title", "company", "description") and v
    }
    return COVER_LETTER_PROMPT_V1.format(
        profile_json=json.dumps(p),
        job_json=json.dumps(j),
        tone=tone,
    )


# ===================================================================
# Contract 8: Onboarding Questions
# ===================================================================


class OnboardingQuestionsResponse_V1(BaseModel):
    """AI-generated onboarding calibration questions."""

    questions: list[str] = Field(
        default_factory=list,
        description="Strategic questions to calibrate job matching",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Key areas to focus on based on profile analysis",
    )
    suggested_preferences: dict = Field(
        default_factory=dict, description="Suggested job preferences based on profile"
    )


ONBOARDING_QUESTIONS_PROMPT_V1 = """Generate calibration questions. Return JSON only.

Profile: {profile_json}

Keys: questions[](3-5), focus_areas[], suggested_preferences{{remote_preference, company_stage, min_salary}}."""


def build_onboarding_questions_prompt(profile_dict: dict) -> str:
    p = {k: v for k, v in profile_dict.items() if v}
    return ONBOARDING_QUESTIONS_PROMPT_V1.format(profile_json=json.dumps(p))
