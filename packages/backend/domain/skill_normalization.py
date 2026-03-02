"""Skill Normalization — normalize skills across job postings for better matching.

Provides:
- Skill synonym resolution (JS → JavaScript)
- Skill categorization (programming, framework, tool)
- Skill level inference (beginner, intermediate, expert)
- Canonical skill naming
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from shared.logging_config import get_logger

logger = get_logger("sorce.skill_normalization")


class SkillCategory(StrEnum):
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    METHODOLOGY = "methodology"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class NormalizedSkill(BaseModel):
    canonical_name: str
    original: str
    category: SkillCategory
    aliases: list[str] = []
    level: SkillLevel | None = None
    confidence: float = 1.0


SKILL_SYNONYMS: dict[str, str] = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "python": "Python",
    "py": "Python",
    "java": "Java",
    "c#": "C#",
    "csharp": "C#",
    "c++": "C++",
    "cpp": "C++",
    "ruby": "Ruby",
    "rb": "Ruby",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "php": "PHP",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular.js",
    "angular.js": "Angular.js",
    "svelte": "Svelte",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next": "Next.js",
    "nuxt": "Nuxt.js",
    "nuxtjs": "Nuxt.js",
    "nuxt.js": "Nuxt.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "ror": "Ruby on Rails",
    "spring": "Spring",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "aspnet": "ASP.NET",
    "asp.net": "ASP.NET",
    ".net": ".NET",
    "dotnet": ".NET",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "elastic": "Elasticsearch",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "rest": "REST API",
    "rest api": "REST API",
    "restful": "REST API",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "sql": "SQL",
    "nosql": "NoSQL",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "data science": "Data Science",
    "ds": "Data Science",
    "etl": "ETL",
    "spark": "Apache Spark",
    "hadoop": "Hadoop",
    "kafka": "Apache Kafka",
    "airflow": "Apache Airflow",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "excel": "Excel",
    "figma": "Figma",
    "sketch": "Sketch",
    "adobe xd": "Adobe XD",
    "xd": "Adobe XD",
}

SKILL_CATEGORIES: dict[str, SkillCategory] = {
    "JavaScript": SkillCategory.PROGRAMMING_LANGUAGE,
    "TypeScript": SkillCategory.PROGRAMMING_LANGUAGE,
    "Python": SkillCategory.PROGRAMMING_LANGUAGE,
    "Java": SkillCategory.PROGRAMMING_LANGUAGE,
    "C#": SkillCategory.PROGRAMMING_LANGUAGE,
    "C++": SkillCategory.PROGRAMMING_LANGUAGE,
    "Go": SkillCategory.PROGRAMMING_LANGUAGE,
    "Rust": SkillCategory.PROGRAMMING_LANGUAGE,
    "Ruby": SkillCategory.PROGRAMMING_LANGUAGE,
    "PHP": SkillCategory.PROGRAMMING_LANGUAGE,
    "Swift": SkillCategory.PROGRAMMING_LANGUAGE,
    "Kotlin": SkillCategory.PROGRAMMING_LANGUAGE,
    "Scala": SkillCategory.PROGRAMMING_LANGUAGE,
    "React": SkillCategory.FRAMEWORK,
    "Vue.js": SkillCategory.FRAMEWORK,
    "Angular": SkillCategory.FRAMEWORK,
    "Angular.js": SkillCategory.FRAMEWORK,
    "Svelte": SkillCategory.FRAMEWORK,
    "Next.js": SkillCategory.FRAMEWORK,
    "Nuxt.js": SkillCategory.FRAMEWORK,
    "Node.js": SkillCategory.FRAMEWORK,
    "Express.js": SkillCategory.FRAMEWORK,
    "Django": SkillCategory.FRAMEWORK,
    "Flask": SkillCategory.FRAMEWORK,
    "FastAPI": SkillCategory.FRAMEWORK,
    "Ruby on Rails": SkillCategory.FRAMEWORK,
    "Spring": SkillCategory.FRAMEWORK,
    "Spring Boot": SkillCategory.FRAMEWORK,
    "ASP.NET": SkillCategory.FRAMEWORK,
    ".NET": SkillCategory.FRAMEWORK,
    "PostgreSQL": SkillCategory.DATABASE,
    "MySQL": SkillCategory.DATABASE,
    "MongoDB": SkillCategory.DATABASE,
    "Redis": SkillCategory.DATABASE,
    "Elasticsearch": SkillCategory.DATABASE,
    "AWS": SkillCategory.CLOUD,
    "Azure": SkillCategory.CLOUD,
    "Google Cloud": SkillCategory.CLOUD,
    "Docker": SkillCategory.TOOL,
    "Kubernetes": SkillCategory.TOOL,
    "Terraform": SkillCategory.TOOL,
    "Jenkins": SkillCategory.TOOL,
    "Git": SkillCategory.TOOL,
    "GitHub": SkillCategory.TOOL,
    "GitLab": SkillCategory.TOOL,
    "CI/CD": SkillCategory.METHODOLOGY,
    "Agile": SkillCategory.METHODOLOGY,
    "Scrum": SkillCategory.METHODOLOGY,
    "Kanban": SkillCategory.METHODOLOGY,
    "Machine Learning": SkillCategory.DOMAIN,
    "Artificial Intelligence": SkillCategory.DOMAIN,
    "Deep Learning": SkillCategory.DOMAIN,
    "Data Science": SkillCategory.DOMAIN,
    "NLP": SkillCategory.DOMAIN,
    "Figma": SkillCategory.TOOL,
    "Excel": SkillCategory.TOOL,
    "Tableau": SkillCategory.TOOL,
    "Power BI": SkillCategory.TOOL,
}

LEVEL_INDICATORS = {
    SkillLevel.BEGINNER: [
        "familiar",
        "basic",
        "beginner",
        "entry-level",
        "junior",
        "understanding of",
        "exposure to",
        "learning",
    ],
    SkillLevel.INTERMEDIATE: [
        "intermediate",
        "experienced",
        "proficient",
        "working knowledge",
        "hands-on",
        "practical",
        "1-2 years",
        "2-3 years",
    ],
    SkillLevel.EXPERT: [
        "expert",
        "advanced",
        "senior",
        "lead",
        "architect",
        "5+ years",
        "7+ years",
        "10+ years",
        "deep expertise",
        "mastery",
        "specialist",
    ],
}


def normalize_skill(skill_text: str) -> NormalizedSkill:
    original = skill_text.strip()
    lower = original.lower()

    clean_skill = re.sub(r"[^\w\s\.\+\#\-]", "", lower).strip()

    level = None
    for skill_level, indicators in LEVEL_INDICATORS.items():
        for indicator in indicators:
            if indicator in lower:
                level = skill_level
                break
        if level:
            break

    canonical = SKILL_SYNONYMS.get(clean_skill, original.title())

    category = SKILL_CATEGORIES.get(canonical, SkillCategory.TOOL)

    aliases = [
        syn
        for syn, canon in SKILL_SYNONYMS.items()
        if canon == canonical and syn != clean_skill
    ][:5]

    confidence = 1.0 if canonical != original.title() else 0.7

    return NormalizedSkill(
        canonical_name=canonical,
        original=original,
        category=category,
        aliases=aliases,
        level=level,
        confidence=confidence,
    )


def normalize_skills_list(skills: list[str]) -> list[NormalizedSkill]:
    normalized = []
    seen_canonical: set[str] = set()

    for skill in skills:
        n = normalize_skill(skill)
        if n.canonical_name not in seen_canonical:
            seen_canonical.add(n.canonical_name)
            normalized.append(n)

    return normalized


def extract_skills_from_text(text: str) -> list[str]:
    patterns = [
        r"(?:skills?|technologies?|tools?|frameworks?|languages?)[:\s]+([^.\n]+)",
        r"(?:proficient|experienced|skilled)\s+(?:in|with)\s+([^.\n]+)",
        r"(?:knowledge|familiarity)\s+(?:of|with)\s+([^.\n]+)",
    ]

    extracted = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            skills = [s.strip() for s in re.split(r"[,;/&]|\band\b", match)]
            extracted.extend(skills)

    return [s for s in extracted if len(s) > 1]


def categorize_skills(skills: list[NormalizedSkill]) -> dict[SkillCategory, list[str]]:
    categorized: dict[SkillCategory, list[str]] = {cat: [] for cat in SkillCategory}

    for skill in skills:
        categorized[skill.category].append(skill.canonical_name)

    return {k: v for k, v in categorized.items() if v}


def compare_skill_sets(
    profile_skills: list[str],
    job_skills: list[str],
) -> dict[str, Any]:
    normalized_profile = normalize_skills_list(profile_skills)
    normalized_job = normalize_skills_list(job_skills)

    profile_set = {s.canonical_name.lower() for s in normalized_profile}
    job_set = {s.canonical_name.lower() for s in normalized_job}

    matching = profile_set & job_set
    missing = job_set - profile_set
    extra = profile_set - job_set

    match_score = len(matching) / max(len(job_set), 1) if job_set else 0.0

    return {
        "match_score": round(match_score, 2),
        "matching_skills": list(matching),
        "missing_skills": list(missing),
        "extra_skills": list(extra),
        "profile_count": len(profile_set),
        "job_count": len(job_set),
    }
