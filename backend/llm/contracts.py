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


class RichSkill(BaseModel):
    """A skill with confidence, context, and metadata for deep matching."""

    skill: str = Field(..., description="Skill name (e.g., 'React', 'Python')")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1 based on evidence",
    )
    years_actual: float | None = Field(
        default=None, description="Years of actual usage"
    )
    context: str = Field(
        default="", description="How the skill was used (brief context)"
    )
    last_used: str | None = Field(
        default=None, description="Last usage date (YYYY-MM format)"
    )
    verified: bool = Field(
        default=False, description="Whether skill is verified (GitHub, etc.)"
    )
    related_to: list[str] = Field(default_factory=list, description="Related skills")
    source: str = Field(
        default="resume", description="Source: resume, github, linkedin, manual"
    )
    project_count: int = Field(
        default=0, description="Number of projects using this skill"
    )


class SkillsInfo(BaseModel):
    technical: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


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


RESUME_PARSE_PROMPT_V1 = """You are a resume parser. Extract structured information from the following resume text.

## Resume Text
{resume_text}

## Instructions
Return ONLY a JSON object (no markdown fences) with exactly these top-level keys:
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
        "technical": [""],
        "soft": [""]
    }},
    "certifications": [""],
    "languages": [""],
    "summary": ""
}}

Fill in every field you can find. Use empty strings or empty arrays for missing data.
"""


def build_resume_parse_prompt(resume_text: str) -> str:
    """Fill the resume parse prompt template."""
    return RESUME_PARSE_PROMPT_V1.format(resume_text=resume_text)


# ===================================================================
# Contract 1b: Resume Parsing V2 → Rich Skills with Confidence
# ===================================================================


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
        default=0.0, description="Total years of professional experience"
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

2. **Years Actual**:
   - Calculate from experience dates when skill was used
   - Sum overlapping years (not additive for parallel usage)
   - Use 0.5 increments (e.g., 2.5 years)

3. **Context**:
   - ONE sentence describing HOW the skill was used
   - Include impact when possible ("Built X for Y users")
   - Be specific, not generic

4. **Project Count**:
   - Count distinct projects/roles where skill was applied
   - Look for bullet points, separate roles, distinct deliverables

5. **Related Skills**:
   - Skills commonly used together (React -> TypeScript, Next.js)
   - Skills from same ecosystem or domain
   - Max 5 related skills

6. **Technical vs Soft Skills**:
   - Technical: programming languages, frameworks, tools, platforms, methodologies
   - Soft: communication, leadership, teamwork, problem-solving

Extract 5-15 technical skills and 3-8 soft skills maximum.
Prioritize skills with strongest evidence (highest confidence).
"""


def build_resume_parse_prompt_v2(resume_text: str) -> str:
    """Fill the resume parse prompt V2 template."""
    return RESUME_PARSE_PROMPT_V2.format(resume_text=resume_text)


# ===================================================================
# Contract 2: DOM Mapping → field values + unresolved fields
# ===================================================================


class DomMappingResponse_V1(BaseModel):
    """Expected JSON output from the DOM field mapping LLM call."""

    field_values: dict[str, str] = Field(default_factory=dict)
    unresolved_required_fields: list[UnresolvedField] = Field(default_factory=list)


DOM_MAPPING_PROMPT_V1 = """You are a job-application autofill assistant. Your goal is to fill a web form using the user's profile data.

## Canonical User Profile
{profile_json}

## Previously Answered Questions (authoritative – override profile if conflicting)
{answered_json}

## Form Fields
Each field is JSON with keys: selector, label, type, required, step_index, options.
For selects and radios, "options" is a list of {{value, text}} objects.
{fields_json}

## Rules
1. For every field, if the profile or previously answered questions contain enough data, add
   an entry to "field_values" mapping the field's `selector` to the concrete value.
   - For <select> fields: return the `value` attribute of the best-matching option.
   - For radio buttons: return the `value` attribute of the best-matching option.
   - For checkboxes: return "true" or "false".
   - For text/email/tel/textarea: return the plain string.
2. If a **required** field cannot be answered, add it to "unresolved_required_fields" with:
   - "selector": the CSS selector,
   - "question": a short user-friendly question.
3. Optional fields that cannot be answered: omit from both lists.
4. User-provided answers (Previously Answered Questions) are authoritative and must always
   override any profile data if there is a conflict.

## Respond with ONLY this JSON (no markdown fences, no commentary):
{{
    "field_values": {{"<selector>": "<value>"}},
    "unresolved_required_fields": [{{"selector": "<selector>", "question": "<question>"}}]
}}
"""


def build_dom_mapping_prompt(
    profile_dict: dict,
    form_fields: list[dict],
    answered_inputs: list[dict] | None = None,
) -> str:
    """Fill the DOM mapping prompt template."""
    return DOM_MAPPING_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        answered_json=json.dumps(answered_inputs or [], indent=2),
        fields_json=json.dumps(form_fields, indent=2, default=str),
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


ROLE_SUGGESTION_PROMPT_V1 = """You are a career advisor AI. Based on the candidate's parsed resume, suggest the most suitable job roles.

## Candidate Profile
{profile_json}

## Instructions
Analyze the candidate's:
- Work experience (titles, companies, responsibilities)
- Technical and soft skills
- Education and certifications
- Career progression

Return ONLY a JSON object (no markdown fences):
{{
    "suggested_roles": ["Role 1", "Role 2", "Role 3"],
    "primary_role": "Best Fit Role Title",
    "experience_level": "senior",
    "confidence": 0.85,
    "reasoning": "Brief explanation of role fit"
}}

Experience levels: entry, mid, senior, staff, principal, executive
Confidence: 0.0-1.0 based on how clear the career path is
"""


def build_role_suggestion_prompt(resume_text: str, skills: list[str], experience_years: int, education_level: str) -> str:
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


SALARY_SUGGESTION_PROMPT_V1 = """You are a compensation advisor AI. Estimate a competitive salary range for this candidate.

## Candidate Profile
{profile_json}

## Target Role
{target_role}

## Preferred Location
{location}

## Instructions
Consider:
- Years of relevant experience
- Technical skill rarity and demand
- Location cost of living and market rates
- Industry standards for the role
- Education and certifications

Return ONLY a JSON object (no markdown fences):
{{
    "min_salary": 120000,
    "max_salary": 180000,
    "market_median": 150000,
    "currency": "USD",
    "confidence": 0.75,
    "factors": ["5+ years experience", "In-demand skills", "High COL location"],
    "reasoning": "Brief explanation of estimate"
}}

Use USD as default currency. Be conservative with confidence for unusual combinations.
"""


def build_salary_suggestion_prompt(skills: list[str], experience_years: int, education_level: str, target_role: str, location: str) -> str:
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


LOCATION_SUGGESTION_PROMPT_V1 = """You are a job market advisor AI. Suggest the best locations for this candidate to find work.

## Candidate Profile
{profile_json}

## Current/Preferred Location (if any)
{current_location}

## Instructions
Consider:
- Where their skills are most in-demand
- Remote work viability for their role type
- Major tech/industry hubs relevant to their experience
- Cost of living vs salary potential

Return ONLY a JSON object (no markdown fences):
{{
    "suggested_locations": ["Remote", "San Francisco, CA", "Austin, TX", "New York, NY"],
    "remote_friendly_score": 0.9,
    "top_markets": ["San Francisco, CA", "Seattle, WA", "Austin, TX"],
    "reasoning": "Brief explanation of location recommendations"
}}

remote_friendly_score: 0.0 = requires on-site, 1.0 = fully remote viable
"""


def build_location_suggestion_prompt(skills: list[str], role: str, experience_years: int, remote_preference: bool) -> str:
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


JOB_MATCH_PROMPT_V1 = """You are a job matching AI. Score how well this candidate matches the job.

## Candidate Profile
{profile_json}

## Job Posting
{job_json}

## Instructions
Score the match considering:
- Skills overlap (required vs candidate skills)
- Experience level alignment
- Location/remote compatibility
- Salary range fit (if available)
- Any red flags (overqualified, underqualified, career change)

Return ONLY a JSON object (no markdown fences):
{{
    "score": 85,
    "skill_match": 0.9,
    "experience_match": 0.8,
    "location_match": 1.0,
    "culture_signals": ["startup environment", "fast-paced"],
    "red_flags": [],
    "summary": "Strong match - 4/5 required skills, remote-friendly"
}}

score: 0-100 overall match quality
"""


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


COVER_LETTER_PROMPT_V1 = """You are an expert career coach. Write a compelling cover letter for this candidate applying to this job.

## Candidate Profile
{profile_json}

## Job Posting
{job_json}

## Tone
{tone}

## Instructions
- Highlight relevant experience that matches the job requirements.
- Show enthusiasm for the company and role.
- Keep it concise (under 400 words).
- Use professional formatting.
- Do not make up facts not in the profile.

Return ONLY a JSON object:
{{
    "subject_line": "Application for [Role] - [Name]",
    "content": "Dear Hiring Manager,\\n\\n..."
}}
"""


def build_cover_letter_prompt(
    profile_dict: dict, job_dict: dict, tone: str = "professional"
) -> str:
    """Build prompt for AI cover letter generation."""
    return COVER_LETTER_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        job_json=json.dumps(job_dict, indent=2),
        tone=tone,
    )


# ===================================================================
# Contract 8: Onboarding Calibration Questions
# ===================================================================


class OnboardingQuestion(BaseModel):
    id: str = Field(
        ..., description="Unique identifier for the question (e.g., 'relocation')"
    )
    text: str = Field(..., description="The user-facing question text")
    type: str = Field(..., description="Question type: 'yes_no', 'text', 'select'")
    options: list[str] = Field(
        default_factory=list, description="Options for select/radio types"
    )


class OnboardingQuestionsResponse_V1(BaseModel):
    """AI-generated onboarding calibration questions."""

    questions: list[OnboardingQuestion] = Field(
        ..., description="List of 3-5 strategic questions"
    )


ONBOARDING_QUESTIONS_PROMPT_V1 = """You are a career strategist AI. The user has just uploaded their resume, but some key information for job matching might be missing.

## Candidate Profile
{profile_json}

## Instructions
Generate 3-5 high-value "calibration" questions to ask the candidate. These should focus on logistics, preferences, or deal-breakers that are rarely on resumes but critical for job matching (e.g., visa sponsorship, clearance, relocation, remote preference if not obvious).

Do NOT ask for information already present in the profile (e.g., if they listed their email or phone, don't ask for it).
Focus on:
1. Visa sponsorship needed?
2. Security clearance (if relevant to their field)?
3. Relocation willingness?
4. Commute preference?
5. Start date availability?

Return ONLY a JSON object:
{{
    "questions": [
        {{
            "id": "visa_sponsorship",
            "text": "Do you require visa sponsorship now or in the future?",
            "type": "yes_no",
            "options": []
        }},
        {{
            "id": "clearance",
            "text": "Do you hold an active security clearance?",
            "type": "select",
            "options": ["None", "Secret", "Top Secret", "TS/SCI"]
        }}
    ]
}}
"""


def build_onboarding_questions_prompt(resume_text: str, current_step: str) -> str:
    """Build prompt for AI onboarding calibration questions."""
    profile_dict = {
        "resume_text": resume_text,
        "current_step": current_step,
    }
    return ONBOARDING_QUESTIONS_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2)
    )
