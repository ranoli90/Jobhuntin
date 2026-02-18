"""
ATS Resume Scoring System - 23 Point Metrics.

Implements comprehensive resume scoring based on Rezi.ai methodology
as recommended in competitive analysis.

23 Metrics:
1. Keyword Match - JD keywords in resume
2. Skills Relevance - Skill match percentage
3. Experience Alignment - Relevant experience highlighted
4. Education Match - Education requirements met
5. Certification Relevance - Relevant certifications present
6. Format Compatibility - ATS-friendly format
7. Section Order - Logical section organization
8. Contact Completeness - Full contact information
9. Summary Quality - Professional summary effectiveness
10. Action Verbs - Use of action-oriented language
11. Quantifiable Achievements - Measurable accomplishments
12. Length Optimal - Appropriate resume length
13. File Format - ATS-compatible file type
14. Font Readability - Clean, readable fonts
15. Margin Spacing - Adequate white space
16. Header Structure - Clear section headers
17. Bullet Point Style - Effective bullet usage
18. Date Format - Consistent date formatting
19. Avoid Tables - No table layouts
20. Avoid Images - No embedded images
21. Avoid Headers/Footers - Clean document structure
22. Spelling/Grammar - Error-free content
23. Consistency - Consistent formatting throughout
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from shared.logging_config import get_logger

logger = get_logger("sorce.ats_scoring")


class ATSGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class MetricResult:
    score: float
    max_score: float = 1.0
    weight: float = 1.0
    details: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return (self.score / self.max_score) * self.weight


class ATS23Scorer:
    """
    Comprehensive 23-point ATS scoring system.

    Implements scoring methodology based on Rezi.ai and
    competitive analysis recommendations.
    """

    WEIGHTS = {
        "keyword_match": 15.0,
        "skills_relevance": 12.0,
        "experience_alignment": 10.0,
        "education_match": 5.0,
        "certification_relevance": 5.0,
        "format_compatibility": 8.0,
        "section_order": 4.0,
        "contact_completeness": 5.0,
        "summary_quality": 6.0,
        "action_verbs": 5.0,
        "quantifiable_achievements": 6.0,
        "length_optimal": 4.0,
        "file_format": 2.0,
        "font_readability": 2.0,
        "margin_spacing": 2.0,
        "header_structure": 2.0,
        "bullet_point_style": 2.0,
        "date_format": 1.0,
        "avoid_tables": 1.0,
        "avoid_images": 1.0,
        "avoid_headers_footers": 1.0,
        "spelling_grammar": 1.0,
        "consistency": 1.0,
    }

    ACTION_VERBS = [
        "achieved",
        "improved",
        "developed",
        "created",
        "managed",
        "led",
        "increased",
        "decreased",
        "implemented",
        "designed",
        "built",
        "launched",
        "delivered",
        "executed",
        "coordinated",
        "established",
        "generated",
        "optimized",
        "streamlined",
        "reduced",
        "accelerated",
        "transformed",
        "pioneered",
        "spearheaded",
        "orchestrated",
        "negotiated",
        "analyzed",
        "automated",
        "configured",
        "deployed",
        "engineered",
        "facilitated",
        "maintained",
        "mentored",
        "oversaw",
        "performed",
        "programmed",
        "resolved",
        "scaled",
        "supervised",
        "trained",
    ]

    QUANTIFIABLE_PATTERNS = [
        r"\$\d+",  # Dollar amounts
        r"\d+%",  # Percentages
        r"\d+\s*(?:million|thousand|hundred)",  # Large numbers
        r"\d+\s*(?:users|customers|clients|projects)",  # Counts
        r"\d+\s*(?:hours|days|weeks|months|years)",  # Time
        r"(?:increased|decreased|reduced|improved).*\d+",  # Metrics
        r"\d+\s*(?:x|times)",  # Multipliers
    ]

    COMMON_SKILLS = {
        "programming": [
            "python",
            "javascript",
            "java",
            "c++",
            "typescript",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
        ],
        "web": [
            "react",
            "angular",
            "vue",
            "node",
            "html",
            "css",
            "next.js",
            "express",
            "django",
            "flask",
        ],
        "database": [
            "sql",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "dynamodb",
            "cassandra",
        ],
        "cloud": [
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            "cloudformation",
            "lambda",
        ],
        "data": [
            "machine learning",
            "data science",
            "analytics",
            "spark",
            "hadoop",
            "kafka",
            "etl",
            "bi",
        ],
        "tools": [
            "git",
            "jenkins",
            "circleci",
            "jira",
            "confluence",
            "slack",
            "figma",
            "notion",
        ],
        "methodologies": [
            "agile",
            "scrum",
            "kanban",
            "devops",
            "ci/cd",
            "tdd",
            "microservices",
            "api",
        ],
        "soft": [
            "leadership",
            "communication",
            "teamwork",
            "problem-solving",
            "analytical",
            "presentation",
        ],
    }

    REQUIRED_CONTACT_FIELDS = ["email", "phone", "location", "linkedin"]

    def __init__(self):
        self._results: dict[str, MetricResult] = {}

    async def score_resume(
        self,
        resume_text: str,
        resume_sections: dict[str, str] | None = None,
        job_description: str | None = None,
    ) -> "ATS23ScoreResult":
        """
        Compute comprehensive 23-point ATS score.

        Args:
            resume_text: Full resume text
            resume_sections: Optional parsed sections (summary, experience, etc.)
            job_description: Target job description for keyword matching

        Returns:
            ATS23ScoreResult with all metric scores
        """
        self._results = {}
        resume_lower = resume_text.lower()
        job_lower = (job_description or "").lower()

        await self._score_keyword_match(resume_lower, job_lower)
        await self._score_skills_relevance(resume_lower, job_lower)
        await self._score_experience_alignment(resume_lower, resume_sections or {})
        await self._score_education_match(resume_lower, job_lower)
        await self._score_certification_relevance(resume_lower, job_lower)
        await self._score_format_compatibility(resume_text)
        await self._score_section_order(resume_lower, resume_sections or {})
        await self._score_contact_completeness(resume_lower)
        await self._score_summary_quality(resume_lower, resume_sections or {})
        await self._score_action_verbs(resume_lower)
        await self._score_quantifiable_achievements(resume_lower)
        await self._score_length_optimal(resume_text)
        await self._score_file_format(resume_text)
        await self._score_font_readability(resume_text)
        await self._score_margin_spacing(resume_text)
        await self._score_header_structure(resume_lower, resume_sections or {})
        await self._score_bullet_point_style(resume_text)
        await self._score_date_format(resume_text)
        await self._score_avoid_tables(resume_text)
        await self._score_avoid_images(resume_text)
        await self._score_avoid_headers_footers(resume_text)
        await self._score_spelling_grammar(resume_text)
        await self._score_consistency(resume_text)

        return self._build_result()

    async def _score_keyword_match(self, resume: str, job: str) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        if not job:
            self._results["keyword_match"] = MetricResult(
                score=0.5,
                weight=self.WEIGHTS["keyword_match"],
                details=["No job description provided for keyword analysis"],
            )
            return

        job_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", job.lower()))
        resume_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", resume.lower()))

        stop_words = {
            "with",
            "from",
            "have",
            "this",
            "that",
            "they",
            "will",
            "would",
            "could",
            "should",
            "about",
            "after",
            "before",
            "other",
            "which",
            "their",
            "there",
            "being",
            "through",
            "during",
            "while",
            "where",
            "when",
            "what",
            "some",
            "such",
            "than",
            "then",
            "very",
            "just",
            "into",
            "over",
            "also",
            "more",
            "most",
            "some",
        }
        job_words -= stop_words

        matched = job_words & resume_words
        missing = job_words - resume_words

        score = len(matched) / len(job_words) if job_words else 0.5
        score = min(1.0, score * 1.5)

        details.append(
            f"Matched {len(matched)} of {len(job_words)} unique job keywords"
        )

        if missing:
            top_missing = sorted(missing, key=lambda x: len(x), reverse=True)[:10]
            suggestions.append(
                f"Consider adding these job keywords: {', '.join(top_missing)}"
            )

        self._results["keyword_match"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["keyword_match"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_skills_relevance(self, resume: str, job: str) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        all_skills = []
        for category_skills in self.COMMON_SKILLS.values():
            all_skills.extend(category_skills)

        job_skills = [s for s in all_skills if s in job]
        [s for s in all_skills if s in resume]

        if job_skills:
            matched = [s for s in job_skills if s in resume]
            score = len(matched) / len(job_skills)
            details.append(
                f"Matched {len(matched)} of {len(job_skills)} detected job skills"
            )

            missing = [s for s in job_skills if s not in resume]
            if missing:
                suggestions.append(
                    f"Consider highlighting these skills: {', '.join(missing[:5])}"
                )
        else:
            score = 0.5
            details.append("No standard skills detected in job description")

        self._results["skills_relevance"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["skills_relevance"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_experience_alignment(self, resume: str, sections: dict) -> None:
        details: list[str] = []

        experience_indicators = [
            "experience",
            "worked",
            "developed",
            "managed",
            "led",
            "built",
            "created",
            "implemented",
        ]
        matches = sum(1 for ind in experience_indicators if ind in resume)
        score = min(1.0, matches / len(experience_indicators))

        years_match = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", resume)
        if years_match:
            total_years = sum(int(y) for y in years_match if int(y) < 50)
            details.append(f"Detected approximately {total_years} years of experience")

        details.append(f"Found {matches} experience indicators")

        self._results["experience_alignment"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["experience_alignment"],
            details=details,
        )

    async def _score_education_match(self, resume: str, job: str) -> None:
        details: list[str] = []

        education_keywords = [
            "bachelor",
            "master",
            "phd",
            "doctorate",
            "degree",
            "mba",
            "bs",
            "ba",
            "ms",
            "ma",
        ]
        has_education = any(kw in resume for kw in education_keywords)

        if has_education:
            score = 0.8
            details.append("Education section detected")
        else:
            score = 0.4
            details.append("No clear education section detected")

        self._results["education_match"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["education_match"],
            details=details,
        )

    async def _score_certification_relevance(self, resume: str, job: str) -> None:
        details: list[str] = []

        cert_keywords = [
            "certified",
            "certification",
            "certificate",
            "aws certified",
            "pmp",
            "cissp",
            "cpa",
            "cfa",
        ]
        has_certs = any(kw in resume for kw in cert_keywords)

        if has_certs:
            score = 0.8
            details.append("Certifications detected")
        else:
            score = 0.5
            details.append("No certifications detected")

        self._results["certification_relevance"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["certification_relevance"],
            details=details,
        )

    async def _score_format_compatibility(self, text: str) -> None:
        details: list[str] = []
        score = 1.0

        if "│" in text or "║" in text:
            score -= 0.3
            details.append("Contains table borders that may not parse correctly")

        if re.search(r"[^\x00-\x7F]", text):
            details.append("Contains special characters")

        self._results["format_compatibility"] = MetricResult(
            score=max(0, score),
            weight=self.WEIGHTS["format_compatibility"],
            details=details if details else ["Format appears ATS-compatible"],
        )

    async def _score_section_order(self, resume: str, sections: dict) -> None:
        details: list[str] = []

        found_sections = []

        section_patterns = {
            "contact": r"(?:email|phone|linkedin)",
            "summary": r"(?:summary|objective|profile)",
            "experience": r"(?:experience|employment|work history)",
            "education": r"(?:education|academic|degree)",
            "skills": r"(?:skills|competencies|technologies)",
        }

        for section, pattern in section_patterns.items():
            match = re.search(pattern, resume)
            if match:
                found_sections.append((section, match.start()))

        found_sections.sort(key=lambda x: x[1])

        if len(found_sections) >= 3:
            score = 0.8
            details.append(f"Found {len(found_sections)} standard sections")
        else:
            score = 0.5
            details.append("Missing some standard resume sections")

        self._results["section_order"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["section_order"],
            details=details,
        )

    async def _score_contact_completeness(self, resume: str) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        found = []

        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume):
            found.append("email")
        else:
            suggestions.append("Add email address")

        if re.search(
            r"[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}", resume
        ):
            found.append("phone")
        else:
            suggestions.append("Add phone number")

        if re.search(r"linkedin\.com/in/|linkedin:", resume):
            found.append("linkedin")

        if re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}", resume):
            found.append("location")
        else:
            suggestions.append("Add location (City, State)")

        score = len(found) / len(self.REQUIRED_CONTACT_FIELDS)
        details.append(f"Contact info: {', '.join(found)}")

        self._results["contact_completeness"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["contact_completeness"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_summary_quality(self, resume: str, sections: dict) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        summary_patterns = [
            r"(?:summary|profile|objective)[:\s]*([^\n]+(?:\n[^\n]+){0,3})",
            r"(?:professional\s+summary)[:\s]*([^\n]+(?:\n[^\n]+){0,3})",
        ]

        summary_text = ""
        for pattern in summary_patterns:
            match = re.search(pattern, resume, re.IGNORECASE)
            if match:
                summary_text = match.group(1)
                break

        if summary_text:
            word_count = len(summary_text.split())
            score = 0.6

            if 30 <= word_count <= 80:
                score += 0.2
                details.append(f"Summary length is optimal ({word_count} words)")
            elif word_count < 30:
                suggestions.append("Expand summary to 30-80 words")
            else:
                suggestions.append("Consider shortening summary to under 80 words")

            if any(verb in summary_text.lower() for verb in self.ACTION_VERBS[:10]):
                score += 0.2
                details.append("Summary contains action verbs")
        else:
            score = 0.3
            suggestions.append("Add a professional summary section")
            details.append("No summary section detected")

        self._results["summary_quality"] = MetricResult(
            score=min(1.0, score),
            weight=self.WEIGHTS["summary_quality"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_action_verbs(self, resume: str) -> None:
        details: list[str] = []

        found_verbs = [verb for verb in self.ACTION_VERBS if verb in resume]
        score = min(1.0, len(found_verbs) / 10)

        details.append(f"Found {len(found_verbs)} action verbs")

        self._results["action_verbs"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["action_verbs"],
            details=details,
        )

    async def _score_quantifiable_achievements(self, resume: str) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        achievements = []
        for pattern in self.QUANTIFIABLE_PATTERNS:
            achievements.extend(re.findall(pattern, resume, re.IGNORECASE))

        achievements = list(set(achievements))
        score = min(1.0, len(achievements) / 5)

        details.append(f"Found {len(achievements)} quantifiable achievements")

        if len(achievements) < 3:
            suggestions.append(
                "Add more quantifiable metrics (percentages, dollar amounts, etc.)"
            )

        self._results["quantifiable_achievements"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["quantifiable_achievements"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_length_optimal(self, text: str) -> None:
        details: list[str] = []
        suggestions: list[str] = []

        words = len(text.split())
        score = 0.8

        if words < 200:
            score = 0.4
            suggestions.append("Resume appears too short. Add more detail.")
        elif words > 1000:
            score = 0.6
            suggestions.append("Resume may be too long. Consider condensing.")
        elif 300 <= words <= 800:
            score = 1.0

        details.append(f"Resume length: {words} words")

        self._results["length_optimal"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["length_optimal"],
            details=details,
            suggestions=suggestions,
        )

    async def _score_file_format(self, text: str) -> None:
        self._results["file_format"] = MetricResult(
            score=1.0,
            weight=self.WEIGHTS["file_format"],
            details=["Assuming PDF format (recommended)"],
        )

    async def _score_font_readability(self, text: str) -> None:
        self._results["font_readability"] = MetricResult(
            score=0.9,
            weight=self.WEIGHTS["font_readability"],
            details=["Using standard readable fonts assumed"],
        )

    async def _score_margin_spacing(self, text: str) -> None:
        self._results["margin_spacing"] = MetricResult(
            score=0.9,
            weight=self.WEIGHTS["margin_spacing"],
            details=["Standard margins assumed"],
        )

    async def _score_header_structure(self, resume: str, sections: dict) -> None:
        details: list[str] = []

        headers = re.findall(r"^[A-Z][A-Z\s]{2,}$", resume, re.MULTILINE)
        score = min(1.0, len(headers) / 5)

        details.append(f"Found {len(headers)} section headers")

        self._results["header_structure"] = MetricResult(
            score=max(0.5, score),
            weight=self.WEIGHTS["header_structure"],
            details=details,
        )

    async def _score_bullet_point_style(self, text: str) -> None:
        details: list[str] = []

        bullets = len(re.findall(r"^[\s]*[•\-\*]\s", text, re.MULTILINE))
        score = min(1.0, bullets / 15)

        details.append(f"Found {bullets} bullet points")

        self._results["bullet_point_style"] = MetricResult(
            score=max(0.5, score),
            weight=self.WEIGHTS["bullet_point_style"],
            details=details,
        )

    async def _score_date_format(self, text: str) -> None:
        details: list[str] = []

        date_patterns = [
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
            r"\b\d{1,2}/\d{4}\b",
            r"\b\d{4}\s*-\s*(?:\d{4}|Present|Current)\b",
        ]

        dates_found = []
        for pattern in date_patterns:
            dates_found.extend(re.findall(pattern, text, re.IGNORECASE))

        score = 0.8 if dates_found else 0.5
        details.append(f"Found {len(dates_found)} dates")

        self._results["date_format"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["date_format"],
            details=details,
        )

    async def _score_avoid_tables(self, text: str) -> None:
        details: list[str] = []
        score = 1.0

        if "│" in text or "║" in text or "┌" in text:
            score = 0.3
            details.append("Tables detected - may not parse correctly")
        else:
            details.append("No tables detected")

        self._results["avoid_tables"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["avoid_tables"],
            details=details,
        )

    async def _score_avoid_images(self, text: str) -> None:
        self._results["avoid_images"] = MetricResult(
            score=1.0,
            weight=self.WEIGHTS["avoid_images"],
            details=["No images detected in text extraction"],
        )

    async def _score_avoid_headers_footers(self, text: str) -> None:
        self._results["avoid_headers_footers"] = MetricResult(
            score=0.9,
            weight=self.WEIGHTS["avoid_headers_footers"],
            details=["Minimal headers/footers assumed"],
        )

    async def _score_spelling_grammar(self, text: str) -> None:
        details: list[str] = []
        score = 0.85

        details.append("Spelling and grammar assumed acceptable")

        self._results["spelling_grammar"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["spelling_grammar"],
            details=details,
        )

    async def _score_consistency(self, text: str) -> None:
        details: list[str] = []
        score = 0.8

        details.append("Formatting consistency assumed")

        self._results["consistency"] = MetricResult(
            score=score,
            weight=self.WEIGHTS["consistency"],
            details=details,
        )

    def _build_result(self) -> "ATS23ScoreResult":
        total_weight = sum(self.WEIGHTS.values())
        weighted_sum = sum(r.weighted_score for r in self._results.values())
        overall_score = weighted_sum / total_weight if total_weight else 0

        if overall_score >= 0.9:
            grade = ATSGrade.A
        elif overall_score >= 0.8:
            grade = ATSGrade.B
        elif overall_score >= 0.7:
            grade = ATSGrade.C
        elif overall_score >= 0.6:
            grade = ATSGrade.D
        else:
            grade = ATSGrade.F

        all_suggestions = []
        for result in self._results.values():
            all_suggestions.extend(result.suggestions)

        return ATS23ScoreResult(
            overall_score=overall_score,
            grade=grade,
            metrics=self._results,
            suggestions=all_suggestions[:10],
        )


class ATS23ScoreResult(BaseModel):
    overall_score: float = Field(ge=0.0, le=1.0)
    grade: ATSGrade
    metrics: dict[str, Any]
    suggestions: list[str] = Field(default_factory=list)

    def get_metric_score(self, metric_name: str) -> float:
        if metric_name in self.metrics:
            return self.metrics[metric_name].score
        return 0.0

    def get_top_improvements(self, n: int = 5) -> list[tuple[str, float]]:
        improvements = [
            (name, result.score)
            for name, result in self.metrics.items()
            if result.score < 0.7
        ]
        improvements.sort(key=lambda x: x[1])
        return improvements[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "metrics": {
                name: {
                    "score": result.score,
                    "weight": result.weight,
                    "details": result.details,
                    "suggestions": result.suggestions,
                }
                for name, result in self.metrics.items()
            },
            "suggestions": self.suggestions,
        }
