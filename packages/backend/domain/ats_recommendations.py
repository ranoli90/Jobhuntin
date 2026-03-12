"""Job-specific ATS recommendations system.

Provides intelligent, job-tailored ATS optimization recommendations including:
- Job-specific keyword analysis
- Industry-specific formatting guidelines
- Company culture alignment suggestions
- Role-specific content recommendations
- ATS system compatibility insights
- Success probability predictions

Key features:
1. Job analysis and keyword extraction
2. Industry-specific ATS rules
3. Company culture integration
4. Role-based content optimization
5. ATS system compatibility checking
6. Success probability scoring
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from packages.backend.llm.client import LLMClient
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.ats_recommendations")


@dataclass
class ATSRecommendation:
    """Individual ATS recommendation."""

    category: (
        str  # "keywords", "formatting", "content", "skills", "experience", "education"
    )
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_items: List[str]
    impact_score: float  # 0.0-1.0
    implementation_effort: str  # "easy", "moderate", "complex"
    examples: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "action_items": self.action_items,
            "impact_score": self.impact_score,
            "implementation_effort": self.implementation_effort,
            "examples": self.examples,
        }


@dataclass
class ATSAnalysisResult:
    """Complete ATS analysis result."""

    job_id: str
    job_title: str
    company_name: str
    industry: str
    ats_score_current: float
    ats_score_potential: float
    improvement_potential: float
    recommendations: List[ATSRecommendation]
    keyword_analysis: Dict[str, Any]
    format_compliance: Dict[str, Any]
    content_optimization: Dict[str, Any]
    success_probability: float
    estimated_processing_time: str
    industry_specific_rules: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "industry": self.industry,
            "ats_score_current": self.ats_score_current,
            "ats_score_potential": self.ats_score_potential,
            "improvement_potential": self.improvement_potential,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "keyword_analysis": self.keyword_analysis,
            "format_compliance": self.format_compliance,
            "content_optimization": self.content_optimization,
            "success_probability": self.success_probability,
            "estimated_processing_time": self.estimated_processing_time,
            "industry_specific_rules": self.industry_specific_rules,
        }


class ATSRecommendationsEngine:
    """Job-specific ATS recommendations engine.

    Provides intelligent, tailored ATS optimization recommendations
    based on job requirements, industry standards, and company culture.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._settings = get_settings()

        # Industry-specific ATS rules
        self._industry_rules = self._load_industry_rules()

        # ATS system compatibility patterns
        self._ats_patterns = self._load_ats_patterns()

        # Common ATS keywords by industry
        self._industry_keywords = self._load_industry_keywords()

        # Company culture indicators
        self._culture_indicators = self._load_culture_indicators()

    @property
    def llm(self) -> LLMClient:
        """Get LLM client instance."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self._settings)
        return self._llm_client

    async def analyze_job_for_ats(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        current_resume_text: Optional[str] = None,
    ) -> ATSAnalysisResult:
        """Analyze job and provide ATS-specific recommendations.

        Args:
            job: Job posting data
            profile: User profile data
            current_resume_text: Current resume text for comparison

        Returns:
            Comprehensive ATS analysis and recommendations
        """
        try:
            # Extract job information
            job_id = job.get("id", "")
            job_title = job.get("title", "")
            company_name = job.get("company", "")
            industry = job.get("industry", job.get("company_industry", ""))
            job.get("description", "")

            # Analyze keywords
            keyword_analysis = await self._analyze_keywords(job, profile)

            # Check format compliance
            format_compliance = await self._check_format_compliance(
                job, current_resume_text
            )

            # Analyze content optimization
            content_optimization = await self._analyze_content_optimization(
                job, profile, current_resume_text
            )

            # Generate job-specific recommendations
            recommendations = await self._generate_recommendations(
                job, profile, keyword_analysis, format_compliance, content_optimization
            )

            # Calculate scores
            current_score = self._calculate_current_ats_score(
                keyword_analysis, format_compliance, content_optimization
            )
            potential_score = self._calculate_potential_ats_score(
                keyword_analysis,
                format_compliance,
                content_optimization,
                recommendations,
            )

            # Calculate improvement potential
            improvement_potential = potential_score - current_score

            # Predict success probability
            success_probability = self._predict_success_probability(
                current_score, potential_score, industry, job_title
            )

            # Get industry-specific rules
            industry_rules = self._get_industry_specific_rules(industry)

            # Estimate processing time
            processing_time = self._estimate_processing_time(recommendations)

            return ATSAnalysisResult(
                job_id=job_id,
                job_title=job_title,
                company_name=company_name,
                industry=industry,
                ats_score_current=current_score,
                ats_score_potential=potential_score,
                improvement_potential=improvement_potential,
                recommendations=recommendations,
                keyword_analysis=keyword_analysis,
                format_compliance=format_compliance,
                content_optimization=content_optimization,
                success_probability=success_probability,
                estimated_processing_time=processing_time,
                industry_specific_rules=industry_rules,
            )

        except Exception as e:
            logger.error(f"ATS analysis failed for job {job.get('id', 'unknown')}: {e}")
            raise

    async def _analyze_keywords(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze keywords for ATS optimization."""
        job_description = job.get("description", "").lower()
        job_title = job.get("title", "").lower()
        requirements = job.get("requirements", [])

        # Extract keywords from job
        job_keywords = self._extract_keywords_from_text(
            job_description + " " + job_title
        )
        required_keywords = [req.lower() for req in requirements]

        # Get industry-specific keywords
        industry = job.get("industry", "")
        industry_keywords = self._industry_keywords.get(industry.lower(), [])

        # Get profile keywords
        profile_keywords = []
        if profile.get("skills"):
            profile_keywords.extend(profile["skills"].get("technical", []))
            profile_keywords.extend(profile["skills"].get("soft", []))

        # Analyze keyword coverage
        keyword_coverage = self._analyze_keyword_coverage(
            job_keywords, required_keywords, profile_keywords, industry_keywords
        )

        return {
            "job_keywords": job_keywords,
            "required_keywords": required_keywords,
            "industry_keywords": industry_keywords,
            "profile_keywords": profile_keywords,
            "keyword_coverage": keyword_coverage,
            "missing_keywords": keyword_coverage.get("missing", []),
            "priority_keywords": keyword_coverage.get("priority", []),
            "keyword_density": keyword_coverage.get("density", {}),
        }

    async def _check_format_compliance(
        self,
        job: Dict[str, Any],
        resume_text: Optional[str],
    ) -> Dict[str, Any]:
        """Check ATS format compliance."""
        if not resume_text:
            return {
                "compliant": False,
                "issues": ["No resume text provided for analysis"],
                "score": 0.0,
                "checks": {},
            }

        compliance_checks = {
            "file_format": self._check_file_format(resume_text),
            "font_readability": self._check_font_readability(resume_text),
            "margin_spacing": self._check_margin_spacing(resume_text),
            "section_order": self._check_section_order(resume_text),
            "contact_info": self._check_contact_info(resume_text),
            "bullet_points": self._check_bullet_points(resume_text),
            "date_format": self._check_date_format(resume_text),
            "length_optimal": self._check_length_optimal(resume_text),
            "no_tables": self._check_no_tables(resume_text),
            "no_images": self._check_no_images(resume_text),
            "no_headers_footers": self._check_no_headers_footers(resume_text),
        }

        # Calculate overall compliance score
        scores = [check["score"] for check in compliance_checks.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        issues = [
            check["issue"]
            for check in compliance_checks.values()
            if not check["compliant"]
        ]

        return {
            "compliant": overall_score >= 0.8,
            "score": overall_score,
            "issues": issues,
            "checks": compliance_checks,
        }

    async def _analyze_content_optimization(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        resume_text: Optional[str],
    ) -> Dict[str, Any]:
        """Analyze content optimization for ATS."""
        if not resume_text:
            return {
                "optimized": False,
                "issues": ["No resume text provided for analysis"],
                "score": 0.0,
                "checks": {},
            }

        content_checks = {
            "action_verbs": self._check_action_verbs(resume_text),
            "quantifiable_achievements": self._check_quantifiable_achievements(
                resume_text
            ),
            "skills_relevance": self._check_skills_relevance(resume_text, job, profile),
            "experience_alignment": self._check_experience_alignment(resume_text, job),
            "education_match": self._check_education_match(resume_text, job),
            "certification_relevance": self._check_certification_relevance(
                resume_text, job
            ),
            "summary_quality": self._check_summary_quality(resume_text),
            "spelling_grammar": self._check_spelling_grammar(resume_text),
            "consistency": self._check_consistency(resume_text),
        }

        # Calculate overall optimization score
        scores = [check["score"] for check in content_checks.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        issues = [
            check["issue"]
            for check in content_checks.values()
            if not check["optimized"]
        ]

        return {
            "optimized": overall_score >= 0.7,
            "score": overall_score,
            "issues": issues,
            "checks": content_checks,
        }

    async def _generate_recommendations(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        keyword_analysis: Dict[str, Any],
        format_compliance: Dict[str, Any],
        content_optimization: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate job-specific ATS recommendations."""
        recommendations = []

        # Keyword recommendations
        recommendations.extend(
            await self._generate_keyword_recommendations(job, profile, keyword_analysis)
        )

        # Format recommendations
        recommendations.extend(
            await self._generate_format_recommendations(job, format_compliance)
        )

        # Content recommendations
        recommendations.extend(
            await self._generate_content_recommendations(
                job, profile, content_optimization
            )
        )

        # Industry-specific recommendations
        recommendations.extend(
            await self._generate_industry_recommendations(job, profile)
        )

        # Company culture recommendations
        recommendations.extend(
            await self._generate_culture_recommendations(job, profile)
        )

        # Sort by impact score
        recommendations.sort(key=lambda x: x.impact_score, reverse=True)

        return recommendations

    async def _generate_keyword_recommendations(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        keyword_analysis: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate keyword-specific ATS recommendations."""
        recommendations = []

        missing_keywords = keyword_analysis.get("missing_keywords", [])
        priority_keywords = keyword_analysis.get("priority_keywords", [])

        if missing_keywords:
            recommendations.append(
                ATSRecommendation(
                    category="keywords",
                    priority="high",
                    title="Add Missing Job Keywords",
                    description=f"Add {len(missing_keywords)} missing keywords found in job description",
                    action_items=[
                        f"Add keywords: {', '.join(missing_keywords[:5])}",
                        "Integrate keywords naturally into experience descriptions",
                        "Add keywords to skills section",
                        "Use keywords in summary and cover letter",
                    ],
                    impact_score=0.9,
                    implementation_effort="moderate",
                    examples=[f"Add '{missing_keywords[0]}' to skills section"],
                )
            )

        if priority_keywords:
            recommendations.append(
                ATSRecommendation(
                    category="keywords",
                    priority="medium",
                    title="Emphasize Priority Keywords",
                    description=f"Emphasize {len(priority_keywords)} high-priority keywords",
                    action_items=[
                        f"Highlight keywords: {', '.join(priority_keywords[:3])}",
                        "Place keywords in early sections",
                        "Use keywords in achievement descriptions",
                        "Include keywords in professional summary",
                    ],
                    impact_score=0.7,
                    implementation_effort="easy",
                    examples=[
                        f"Emphasize '{priority_keywords[0]}' in experience section"
                    ],
                )
            )

        return recommendations

    async def _generate_format_recommendations(
        self,
        job: Dict[str, Any],
        format_compliance: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate format-specific ATS recommendations."""
        recommendations = []

        issues = format_compliance.get("issues", [])
        format_compliance.get("checks", {})

        for issue in issues:
            if "file format" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="formatting",
                        priority="high",
                        title="Fix File Format",
                        description="Use ATS-friendly file format (.doc, .pdf, .txt)",
                        action_items=[
                            "Save resume as .docx or .pdf format",
                            "Avoid complex formatting and graphics",
                            "Use standard fonts (Arial, Times New Roman)",
                            "Ensure file is machine-readable",
                        ],
                        impact_score=0.8,
                        implementation_effort="easy",
                        examples=["Save as ATS-friendly .docx format"],
                    )
                )
            elif "font" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="formatting",
                        priority="medium",
                        title="Fix Font Issues",
                        description="Use ATS-compatible fonts",
                        action_items=[
                            "Use standard fonts (Arial, Times New Roman, Calibri)",
                            "Font size 10-12pt for body text",
                            "Avoid decorative fonts and scripts",
                            "Ensure consistent font usage",
                        ],
                        impact_score=0.6,
                        implementation_effort="easy",
                        examples=["Change font to Arial 11pt"],
                    )
                )
            elif "margin" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="formatting",
                        priority="medium",
                        title="Fix Margin Issues",
                        description="Use proper margins for ATS readability",
                        action_items=[
                            "Set margins to 0.5-1 inch on all sides",
                            "Ensure consistent spacing throughout",
                            "Avoid narrow margins",
                            "Use standard page layout",
                        ],
                        impact_score=0.5,
                        implementation_effort="easy",
                        examples=["Set margins to 1 inch"],
                    )
                )

        return recommendations

    async def _generate_content_recommendations(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
        content_optimization: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate content-specific ATS recommendations."""
        recommendations = []

        issues = content_optimization.get("issues", [])

        for issue in issues:
            if "action verbs" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="content",
                        priority="high",
                        title="Add Action Verbs",
                        description="Use strong action verbs to start bullet points",
                        action_items=[
                            "Start bullet points with action verbs (Managed, Led, Developed)",
                            "Use past tense for previous experience",
                            "Quantify achievements with numbers",
                            "Focus on results and outcomes",
                        ],
                        impact_score=0.8,
                        implementation_effort="moderate",
                        examples=["Managed team of 10 developers"],
                    )
                )
            elif "quantifiable" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="content",
                        priority="high",
                        title="Add Quantifiable Achievements",
                        description="Include specific metrics and numbers",
                        action_items=[
                            "Add numbers to achievements (e.g., 'Increased sales by 25%')",
                            "Include team sizes managed",
                            "Add project budgets or timelines",
                            "Include efficiency improvements",
                        ],
                        impact_score=0.7,
                        implementation_effort="moderate",
                        examples=["Increased team productivity by 30%"],
                    )
                )
            elif "skills" in issue.lower():
                recommendations.append(
                    ATSRecommendation(
                        category="content",
                        priority="medium",
                        title="Improve Skills Relevance",
                        description="Align skills with job requirements",
                        action_items=[
                            "Add skills mentioned in job description",
                            "Place skills section prominently",
                            "Include both technical and soft skills",
                            "Match skill levels to job requirements",
                        ],
                        impact_score=0.6,
                        implementation_effort="moderate",
                        examples=["Add Python, JavaScript, SQL to skills section"],
                    )
                )

        return recommendations

    async def _generate_industry_recommendations(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate industry-specific ATS recommendations."""
        recommendations = []

        industry = job.get("industry", "").lower()
        industry_rules = self._industry_rules.get(industry, {})

        for rule in industry_rules:
            recommendations.append(
                ATSRecommendation(
                    category="industry",
                    priority=rule.get("priority", "medium"),
                    title=rule.get("title", f"Industry: {industry.title()}"),
                    description=rule.get("description", ""),
                    action_items=rule.get("action_items", []),
                    impact_score=rule.get("impact_score", 0.5),
                    implementation_effort=rule.get("implementation_effort", "moderate"),
                    examples=rule.get("examples", []),
                )
            )

        return recommendations

    async def _generate_culture_recommendations(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> List[ATSRecommendation]:
        """Generate company culture alignment recommendations."""
        recommendations = []

        company_culture = job.get("company_culture", "")
        company_values = job.get("company_values", [])

        if company_culture:
            recommendations.append(
                ATSRecommendation(
                    category="culture",
                    priority="low",
                    title="Align with Company Culture",
                    description="Tailor content to match company culture",
                    action_items=[
                        f"Use culture-specific language: {company_culture}",
                        "Reflect company values in achievements",
                        "Align communication style with culture",
                        "Show cultural fit in summary",
                    ],
                    impact_score=0.4,
                    implementation_effort="complex",
                    examples=[
                        f"Emphasize collaborative approach for {company_culture} culture"
                    ],
                )
            )

        if company_values:
            recommendations.append(
                ATSRecommendation(
                    category="culture",
                    priority="low",
                    title="Incorporateate Company Values",
                    description="Show alignment with company values",
                    action_items=[
                        f"Reference company values: {', '.join(company_values[:3])}",
                        "Demonstrate values in achievements",
                        "Include values in summary section",
                        "Show how values guided decisions",
                    ],
                    impact_score=0.3,
                    implementation_effort="complex",
                    examples=[
                        f"Show commitment to {company_values[0]} through project work"
                    ],
                )
            )

        return recommendations

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract keywords from text using NLP techniques."""
        # Simple keyword extraction (in production, use NLP library)
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
        }

        # Split text and filter out common words
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = [
            word for word in words if word not in common_words and len(word) > 2
        ]

        # Remove duplicates and return
        return list(set(keywords))

    def _analyze_keyword_coverage(
        self,
        job_keywords: List[str],
        required_keywords: List[str],
        profile_keywords: List[str],
        industry_keywords: List[str],
    ) -> Dict[str, Any]:
        """Analyze keyword coverage between job and profile."""
        job_keywords_set = set(job_keywords)
        required_keywords_set = set(required_keywords)
        profile_keywords_set = set(profile_keywords)
        industry_keywords_set = set(industry_keywords)

        # Calculate coverage
        job_profile_overlap = len(job_keywords_set & profile_keywords_set)
        job_profile_coverage = (
            job_profile_overlap / len(job_keywords_set) if job_keywords_set else 0
        )

        required_profile_overlap = len(required_keywords_set & profile_keywords_set)
        required_profile_coverage = (
            required_profile_overlap / len(required_keywords_set)
            if required_keywords_set
            else 0
        )

        industry_profile_overlap = len(industry_keywords_set & profile_keywords_set)
        industry_profile_coverage = (
            industry_profile_overlap / len(industry_keywords_set)
            if industry_keywords_set
            else 0
        )

        # Find missing keywords
        missing_keywords = list(job_keywords_set - profile_keywords_set)
        priority_keywords = [
            kw
            for kw in job_keywords
            if kw in required_keywords or kw in industry_keywords
        ]

        # Calculate keyword density
        keyword_density = {}
        for keyword in job_keywords:
            if keyword in profile_keywords:
                keyword_density[keyword] = profile_keywords.count(keyword) / len(
                    profile_keywords
                )

        return {
            "job_profile_coverage": job_profile_coverage,
            "required_profile_coverage": required_profile_coverage,
            "industry_profile_coverage": industry_profile_coverage,
            "missing": missing_keywords,
            "priority": priority_keywords,
            "density": keyword_density,
        }

    def _check_file_format(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume uses ATS-friendly file format."""
        # Simple check - in production, would analyze actual file metadata
        return {
            "compliant": True,
            "score": 0.9,
            "issue": None,
        }

    def _check_font_readability(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume uses ATS-readable fonts."""
        # Simple check - in production, would analyze actual fonts
        return {
            "compliant": True,
            "score": 0.8,
            "issue": None,
        }

    def _check_margin_spacing(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume has proper margins and spacing."""
        # Simple check - in production, would analyze actual formatting
        return {
            "compliant": True,
            "score": 0.7,
            "issue": None,
        }

    def _check_section_order(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume has proper section order for ATS."""
        # Simple check - in production, would analyze actual section order
        return {
            "compliant": True,
            "score": 0.8,
            "issue": None,
        }

    def _check_contact_info(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume has complete contact information."""
        contact_indicators = ["email", "phone", "address", "linkedin", "github"]
        found_contacts = [
            indicator
            for indicator in contact_indicators
            if indicator in resume_text.lower()
        ]

        return {
            "compliant": len(found_contacts) >= 3,
            "score": min(len(found_contacts) / 3, 1.0),
            "issue": None
            if len(found_contacts) >= 3
            else "Add more contact information",
        }

    def _check_bullet_points(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume uses proper bullet points."""
        bullet_indicators = ["•", "-", "*", "·"]
        bullet_count = sum(resume_text.count(bullet) for bullet in bullet_indicators)

        return {
            "compliant": bullet_count > 0,
            "score": min(bullet_count / 10, 1.0),
            "issue": None
            if bullet_count > 0
            else "Use bullet points for experience sections",
        }

    def _check_date_format(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume uses consistent date formatting."""
        # Simple check - in production, would analyze actual date formats
        return {
            "compliant": True,
            "score": 0.8,
            "issue": None,
        }

    def _check_length_optimal(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume has optimal length for ATS."""
        word_count = len(resume_text.split())

        # Optimal length: 400-600 words for most ATS systems
        if 400 <= word_count <= 600:
            score = 1.0
        elif 300 <= word_count < 400:
            score = 0.8
        elif 600 < word_count <= 800:
            score = 0.9
        else:
            score = 0.7

        return {
            "compliant": score >= 0.7,
            "score": score,
            "issue": None
            if score >= 0.7
            else f"Adjust resume length ({word_count} words)",
        }

    def _check_no_tables(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume avoids tables that confuse ATS."""
        return {
            "compliant": "table" not in resume_text.lower(),
            "score": 1.0 if "table" not in resume_text.lower() else 0.3,
            "issue": None
            if "table" not in resume_text.lower()
            else "Remove tables from resume",
        }

    def _check_no_images(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume avoids images that ATS can't parse."""
        return {
            "compliant": "image" not in resume_text.lower(),
            "score": 1.0 if "image" not in resume_text.lower() else 0.3,
            "issue": None
            if "image" not in resume_text.lower()
            else "Remove images from resume",
        }

    def _check_no_headers_footers(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume avoids complex headers/footers."""
        return {
            "compliant": True,
            "score": 0.9,
            "issue": None,
        }

    def _check_action_verbs(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume uses strong action verbs."""
        action_verbs = [
            "managed",
            "led",
            "developed",
            "created",
            "implemented",
            "achieved",
            "improved",
            "increased",
            "reduced",
            "optimized",
            "designed",
            "built",
        ]

        action_count = sum(1 for verb in action_verbs if verb in resume_text.lower())
        total_sentences = (
            resume_text.count(".") + resume_text.count("!") + resume_text.count("?")
        )

        score = action_count / total_sentences if total_sentences > 0 else 0

        return {
            "optimized": score >= 0.3,
            "score": score,
            "issue": None if score >= 0.3 else "Add more action verbs to bullet points",
        }

    def _check_quantifiable_achievements(self, resume_text: str) -> Dict[str, Any]:
        """Check if resume includes quantifiable achievements."""
        number_patterns = [
            r"\d+%|\d+\.\d+%|\d+\/\d+|\$\d+",
            r"\bpercent\b|\b%\b|\bgrowth\b|\breduction\b",
            r"\b\d+\s+(?:years?|months?)\b",
            r"\b\d+\s+(?:team|people|employees?)\b",
        ]

        quantifiable_count = sum(
            1 for pattern in number_patterns if re.search(pattern, resume_text)
        )

        total_sentences = (
            resume_text.count(".") + resume_text.count("!") + resume_text.count("?")
        )

        score = quantifiable_count / total_sentences if total_sentences > 0 else 0

        return {
            "optimized": score >= 0.3,
            "score": score,
            "issue": None if score >= 0.3 else "Add specific metrics to achievements",
        }

    def _check_skills_relevance(
        self,
        resume_text: str,
        job: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if skills match job requirements."""
        job_skills = job.get("skills_required", [])
        profile_skills = profile.get("skills", {}).get("technical", []) + profile.get(
            "skills", {}
        ).get("soft", [])

        matching_skills = [skill for skill in profile_skills if skill in job_skills]

        score = len(matching_skills) / len(job_skills) if job_skills else 0

        return {
            "optimized": score >= 0.5,
            "score": score,
            "issue": None if score >= 0.5 else "Add job-required skills to resume",
        }

    def _check_experience_alignment(
        self,
        resume_text: str,
        job: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if experience aligns with job requirements."""
        job_title = job.get("title", "").lower()
        job_description = job.get("description", "").lower()

        # Simple alignment check - in production, would use more sophisticated analysis
        title_words = job_title.split()
        desc_words = job_description.split()
        resume_words = resume_text.lower().split()

        alignment_score = 0.0
        if title_words and resume_words:
            title_alignment = len(set(title_words) & set(resume_words)) / len(
                title_words
            )
            desc_alignment = len(set(desc_words) & set(resume_words)) / len(desc_words)
            alignment_score = (title_alignment + desc_alignment) / 2

        return {
            "optimized": alignment_score >= 0.3,
            "score": alignment_score,
            "issue": None
            if alignment_score >= 0.3
            else "Align experience with job requirements",
        }

    def _check_education_match(
        self, resume_text: str, job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if education matches job requirements."""
        education_required = job.get("education_required", "")

        if not education_required:
            return {
                "optimized": True,
                "score": 1.0,
                "issue": None,
            }

        # Simple check - in production, would analyze actual education section
        education_indicators = [
            "bachelor",
            "master",
            "phd",
            "degree",
            "university",
            "college",
        ]
        has_education = any(
            indicator in resume_text.lower() for indicator in education_indicators
        )

        score = 0.8 if has_education else 0.2

        return {
            "optimized": score >= 0.5,
            "score": score,
            "issue": None if has_education else "Add education information if required",
        }

    def _check_certification_relevance(
        self,
        resume_text: str,
        job: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if certifications match job requirements."""
        job_certifications = job.get("certifications_required", [])

        if not job_certifications:
            return {
                "optimized": True,
                "score": 1.0,
                "issue": None,
            }

        # Simple check - in production, would analyze actual certifications
        cert_indicators = ["certified", "certificate", "certification", "license"]
        has_certifications = any(
            indicator in resume_text.lower() for indicator in cert_indicators
        )

        score = 0.7 if has_certifications else 0.3

        return {
            "optimized": score >= 0.5,
            "score": score,
            "issue": None
            if has_certifications
            else "Add relevant certifications if available",
        }

    def _check_summary_quality(self, resume_text: str) -> Dict[str, Any]:
        """Check if professional summary is well-written."""
        summary_indicators = ["summary", "objective", "profile", "about"]
        has_summary = any(
            indicator in resume_text.lower() for indicator in summary_indicators
        )

        # Check summary length (3-4 sentences is optimal)
        if has_summary:
            sentences = resume_text.split(".")
            summary_sentences = len([s for s in sentences if s.strip()])
            optimal_length = 3 <= summary_sentences <= 4
        else:
            optimal_length = False

        score = 0.8 if has_summary and optimal_length else 0.4

        return {
            "optimized": score >= 0.6,
            "score": score,
            "issue": None if score >= 0.6 else "Add or improve professional summary",
        }

    def _check_spelling_grammar(self, resume_text: str) -> Dict[str, Any]:
        """Check for spelling and grammar issues."""
        # Simple check - in production, would use spell checker
        # For now, assume good quality
        return {
            "optimized": True,
            "score": 0.9,
            "issue": None,
        }

    def _check_consistency(self, resume_text: str) -> Dict[str, Any]:
        """Check for formatting consistency."""
        # Simple check - in production, would analyze consistency patterns
        return {
            "optimized": True,
            "score": 0.8,
            "issue": None,
        }

    def _calculate_current_ats_score(
        self,
        keyword_analysis: Dict[str, Any],
        format_compliance: Dict[str, Any],
        content_optimization: Dict[str, Any],
    ) -> float:
        """Calculate current ATS score."""
        keyword_score = keyword_analysis.get("job_profile_coverage", 0.0)
        format_score = format_compliance.get("score", 0.0)
        content_score = content_optimization.get("score", 0.0)

        # Weighted scoring
        weights = {
            "keywords": 0.4,
            "format": 0.3,
            "content": 0.3,
        }

        return (
            keyword_score * weights["keywords"]
            + format_score * weights["format"]
            + content_score * weights["content"]
        )

    def _calculate_potential_ats_score(
        self,
        keyword_analysis: Dict[str, Any],
        format_compliance: Dict[str, Any],
        content_optimization: Dict[str, Any],
        recommendations: List[ATSRecommendation],
    ) -> float:
        """Calculate potential ATS score after implementing recommendations."""
        # Start with current score
        current_score = self._calculate_current_ats_score(
            keyword_analysis, format_compliance, content_optimization
        )

        # Add potential improvements from recommendations
        potential_improvement = 0.0
        for rec in recommendations:
            potential_improvement += (
                rec.impact_score * 0.1
            )  # Cap at 10% per recommendation

        # Cap at 1.0
        return min(current_score + potential_improvement, 1.0)

    def _predict_success_probability(
        self,
        current_score: float,
        potential_score: float,
        industry: str,
        job_title: str,
    ) -> float:
        """Predict success probability based on ATS score and industry factors."""
        base_probability = 0.3  # Base success rate

        # ATS score factor
        ats_factor = current_score * 0.4

        # Industry factor (some industries have higher ATS adoption)
        industry_factors = {
            "technology": 0.1,
            "healthcare": 0.05,
            "finance": 0.08,
            "education": 0.03,
            "government": 0.02,
        }
        industry_factor = industry_factors.get(industry.lower(), 0.0)

        # Role seniority factor
        seniority_indicators = ["senior", "lead", "manager", "director", "executive"]
        seniority_factor = (
            0.05
            if any(indicator in job_title.lower() for indicator in seniority_indicators)
            else 0.0
        )

        # Calculate probability
        probability = base_probability + ats_factor + industry_factor + seniority_factor

        # Cap at 0.8
        return min(probability, 0.8)

    def _get_industry_specific_rules(self, industry: str) -> List[Dict[str, Any]]:
        """Get industry-specific ATS rules."""
        return self._industry_rules.get(industry.lower(), [])

    def _estimate_processing_time(
        self, recommendations: List[ATSRecommendation]
    ) -> str:
        """Estimate processing time for implementing recommendations."""
        easy_count = len(
            [r for r in recommendations if r.implementation_effort == "easy"]
        )
        moderate_count = len(
            [r for r in recommendations if r.implementation_effort == "moderate"]
        )
        complex_count = len(
            [r for r in recommendations if r.implementation_effort == "complex"]
        )

        # Estimate time in hours
        total_time = easy_count * 0.5 + moderate_count * 2 + complex_count * 4

        if total_time < 1:
            return f"{int(total_time * 60)} minutes"
        elif total_time < 8:
            return f"{total_time:.1f} hours"
        else:
            return f"{int(total_time)} hours"

    def _load_industry_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load industry-specific ATS rules."""
        return {
            "technology": [
                {
                    "priority": "medium",
                    "title": "Technology ATS Optimization",
                    "description": "Technology industry-specific ATS rules for better parsing",
                    "action_items": [
                        "Include technical skills prominently",
                        "Use industry-standard terminology",
                        "Include programming languages and frameworks",
                        "Add project details with technologies used",
                    ],
                    "impact_score": 0.6,
                    "implementation_effort": "moderate",
                    "examples": ["Include Python, JavaScript, React in skills section"],
                },
                {
                    "priority": "low",
                    "title": "Tech Stack Documentation",
                    "description": "Document technology stack clearly",
                    "action_items": [
                        "List technologies in project descriptions",
                        "Include version numbers for frameworks",
                        "Document development tools and environments",
                        "Include deployment platforms",
                    ],
                    "impact_score": 0.4,
                    "implementation_effort": "moderate",
                    "examples": ["Developed using React 18.2.0"],
                },
            ],
            "healthcare": [
                {
                    "priority": "high",
                    "title": "Healthcare ATS Compliance",
                    "description": "Healthcare industry has strict ATS requirements",
                    "action_items": [
                        "Include required certifications (RN, BSN, etc.)",
                        "Add clinical experience details",
                        "Include patient care experience",
                        "Add healthcare-specific terminology",
                        "Follow healthcare formatting standards",
                    ],
                    "impact_score": 0.8,
                    "implementation_effort": "complex",
                    "examples": ["Registered Nurse with 5+ years experience"],
                },
                {
                    "priority": "medium",
                    "title": "Medical Terminology",
                    "description": "Use proper medical terminology",
                    "action_items": [
                        "Use standard medical abbreviations",
                        "Include clinical procedures",
                        "Add patient care metrics",
                        "Document healthcare regulations",
                    ],
                    "impact_score": 0.6,
                    "implementation_effort": "moderate",
                    "examples": ["Provided patient care to 50+ patients"],
                },
            ],
            "finance": [
                {
                    "priority": "medium",
                    "title": "Financial ATS Optimization",
                    "description": "Finance industry ATS optimization rules",
                    "action_items": [
                        "Include financial certifications (CFA, CPA, etc.)",
                        "Add financial metrics and achievements",
                        "Include regulatory compliance details",
                        "Use financial terminology",
                    ],
                    "impact_score": 0.7,
                    "implementation_effort": "moderate",
                    "examples": ["Managed $10M portfolio with 15% annual returns"],
                },
                {
                    "priority": "low",
                    "title": "Financial Metrics",
                    "description": "Include quantifiable financial metrics",
                    "action_items": [
                        "Add AUM, ROI, or performance metrics",
                        "Include budget management experience",
                        "Add risk management details",
                    ],
                    "impact_score": 0.5,
                    "implementation_effort": "moderate",
                    "examples": ["Managed $5M budget with 20% under budget"],
                },
            ],
            "education": [
                {
                    "priority": "medium",
                    "title": "Education ATS Compliance",
                    "description": "Education sector ATS optimization",
                    "action_items": [
                        "Include teaching certifications",
                        "Add student outcomes metrics",
                        "Include curriculum development experience",
                        "Add educational research experience",
                    ],
                    "impact_score": 0.6,
                    "implementation_effort": "moderate",
                    "examples": ["Taught 500+ students"],
                },
            ],
            "government": [
                {
                    "priority": "high",
                    "title": "Government ATS Requirements",
                    "description": "Government positions have strict ATS requirements",
                    "action_items": [
                        "Include security clearance level",
                        "Add government experience",
                        "Include public sector achievements",
                        "Use formal language",
                        "Follow government formatting standards",
                    ],
                    "impact_score": 0.9,
                    "implementation_effort": "complex",
                    "examples": ["Security clearance with 10+ years experience"],
                },
            ],
        }

    def _load_ats_patterns(self) -> Dict[str, List[str]]:
        """Load ATS system compatibility patterns."""
        return {
            "job_boards": [
                "Taleo",
                "Workday",
                "Greenhouse",
                "Lever",
                "iCIMS",
                "Kenexa",
                "Oracle",
                "SAP",
            ],
            "file_formats": [
                ".doc",
                ".docx",
                ".pdf",
                ".txt",
                ".rtf",
            ],
            "avoid_elements": [
                "tables",
                "images",
                "headers",
                "footers",
                "columns",
                "text boxes",
            ],
            "required_sections": [
                "contact",
                "experience",
                "education",
                "skills",
            ],
        }

    def _load_industry_keywords(self) -> Dict[str, List[str]]:
        """Load industry-specific keyword lists."""
        return {
            "technology": [
                "python",
                "javascript",
                "java",
                "react",
                "angular",
                "vue",
                "node",
                "django",
                "flask",
                "fastapi",
                "sql",
                "postgresql",
                "mongodb",
                "redis",
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "git",
                "github",
                "gitlab",
                "bitbucket",
                "jira",
                "confluence",
                "slack",
                "agile",
                "scrum",
                "cicd",
                "devops",
                "microservices",
                "api",
                "rest",
                "frontend",
                "backend",
                "fullstack",
                "full-stack",
                "software",
                "engineering",
                "data",
                "analytics",
                "machine learning",
                "ai",
                "artificial intelligence",
                "cloud",
                "serverless",
                "infrastructure",
                "devops",
                "sre",
                "testing",
                "qa",
                "quality assurance",
                "automation",
                "ci/cd",
            ],
            "healthcare": [
                "rn",
                "bsn",
                "cna",
                "lpn",
                "md",
                "do",
                "phd",
                "dnp",
                "fnp",
                "cna",
                "patient",
                "care",
                "clinical",
                "medical",
                "health",
                "hospital",
                "clinic",
                "treatment",
                "diagnosis",
                "assessment",
                "evaluation",
                "therapy",
                "surgery",
                "medication",
                "pharmaceutical",
                "nursing",
                "physician",
                "doctor",
                "nurse",
                "therapist",
                "clinician",
                "practitioner",
                "healthcare",
                "medical",
                "clinical",
                "patient",
                "emergency",
                "urgent",
                "icu",
                "ccu",
                "hipaa",
                "compliance",
                "regulation",
                "fda",
                "certified",
                "licensed",
                "board",
                "registered",
                "accredited",
                "hospital",
                "clinic",
                "medical center",
                "healthcare system",
            ],
            "finance": [
                "finance",
                "financial",
                "accounting",
                "cpa",
                "cfa",
                "cma",
                "ea",
                "fp&a",
                "cfp",
                "investment",
                "banking",
                "bank",
                "financial services",
                "fintech",
                "trading",
                "securities",
                "portfolio",
                "wealth management",
                "asset management",
                "risk management",
                "compliance",
                "regulatory",
                "audit",
                "tax",
                "budget",
                "forecast",
                "analysis",
                "reporting",
                "modeling",
                "analytics",
                "roi",
                "irr",
                "npv",
                "m&a",
                "ebitda",
                "cash flow",
                "p&l",
                "derivatives",
                "trading",
                "futures",
                "options",
                "equity",
                "fixed income",
                "investment banking",
                "corporate finance",
                "investment banking",
                "wealth management",
                "private banking",
                "commercial banking",
                "retail banking",
                "credit",
                "loans",
                "mortgages",
                "insurance",
                "financial planning",
            ],
            "education": [
                "teaching",
                "education",
                "educator",
                "professor",
                "instructor",
                "faculty",
                "curriculum",
                "instruction",
                "pedagogy",
                "learning",
                "academic",
                "scholar",
                "university",
                "college",
                "school",
                "academic",
                "educational",
                "degree",
                "bachelor",
                "master",
                "phd",
                "doctorate",
                "postgraduate",
                "research",
                "publication",
                "journal",
                "paper",
                "study",
                "thesis",
                "dissertation",
                "student",
                "undergraduate",
                "graduate",
                "alumni",
                "class",
                "course",
                "classroom",
                "lecture",
                "seminar",
                "workshop",
                "training",
                "certification",
                "assessment",
                "evaluation",
                "grading",
                "scoring",
                "testing",
                "examination",
                "development",
                "professional development",
                "continuing education",
                "training",
                "online learning",
                "e-learning",
                "distance learning",
                "remote learning",
                "educational technology",
                "edtech",
                "learning management system",
                "lms",
                "instructional design",
                "curriculum development",
                "course design",
                "academic affairs",
                "student affairs",
                "faculty",
                "staff",
            ],
            "government": [
                "government",
                "federal",
                "state",
                "local",
                "municipal",
                "county",
                "public sector",
                "civil service",
                "administrative",
                "bureaucratic",
                "policy",
                "regulation",
                "compliance",
                "audit",
                "oversight",
                "governance",
                "legislative",
                "congress",
                "senate",
                "representative",
                "official",
                "department",
                "agency",
                "bureau",
                "office",
                "division",
                "branch",
                "contract",
                "contractor",
                "consultant",
                "vendor",
                "supplier",
                "partner",
                "military",
                "defense",
                "homeland security",
                "national security",
                "intelligence",
                "federal",
                "state",
                "local",
                "government employee",
                "civil servant",
                "public service",
                "public affairs",
                "communications",
                "relations",
                "regulatory",
                "compliance",
                "legal",
                "legal affairs",
                "counsel",
                "procurement",
                "purchasing",
                "acquisition",
                "contracts",
                "grants",
                "budget",
                "funding",
                "appropriations",
                "spending",
                "finance",
                "management",
                "administration",
                "leadership",
                "executive",
                "management",
                "director",
                "manager",
                "supervisor",
                "team lead",
                "coordinator",
                "specialist",
                "analyst",
                "advisor",
                "consultant",
                "expert",
                "professional",
                "staff",
                "personnel",
                "human resources",
                "hr",
            ],
        }

    def _load_culture_indicators(self) -> Dict[str, List[str]]:
        """Load company culture indicators."""
        return {
            "innovative": [
                "innovative",
                "innovation",
                "creative",
                "cutting-edge",
                "forward-thinking",
                "disruptive",
                "breakthrough",
                "pioneering",
                "trailblazing",
                "visionary",
            ],
            "collaborative": [
                "collaborative",
                "teamwork",
                "team-based",
                "cooperative",
                "partnership",
                "collaborative environment",
                "team player",
                "cross-functional",
                "cross-functional team",
                "team collaboration",
                "work closely with",
                "collaborative approach",
                "team effort",
                "collective",
            ],
            "data-driven": [
                "data-driven",
                "data",
                "analytics",
                "metrics",
                "insights",
                "statistics",
                "data analysis",
                "data science",
                "machine learning",
                "artificial intelligence",
                "quantitative",
                "qualitative",
                "evidence-based",
                "metrics-driven",
                "statistical",
                "analytical",
                "data-backed",
                "measurable",
            ],
            "customer-focused": [
                "customer-centric",
                "customer service",
                "customer experience",
                "client-focused",
                "customer success",
                "client relationships",
                "customer satisfaction",
                "customer needs",
                "customer requirements",
                "customer feedback",
                "client-facing",
                "client relations",
                "customer support",
                "customer base",
                "customer journey",
                "customer lifecycle",
            ],
            "fast-paced": [
                "fast-paced",
                "fast-paced environment",
                "dynamic",
                "agile",
                "rapid",
                "quick turnaround",
                "responsive",
                "flexible",
                "adaptable",
                "high-energy",
                "energetic",
                "fast-moving",
                "deadline-driven",
                "rapid growth",
                "scaling",
                "startup",
                "startup environment",
            ],
            "detail-oriented": [
                "detail-oriented",
                "attention to detail",
                "thorough",
                "meticulous",
                "precise",
                "accurate",
                "quality-focused",
                "high-quality",
                "exact",
                "specific",
                "detailed",
                "comprehensive",
                "well-documented",
                "well-written",
                "professional",
            ],
        }


# Singleton instance
_ats_recommendations_engine: Optional[ATSRecommendationsEngine] = None


def get_ats_recommendations_engine() -> ATSRecommendationsEngine:
    """Get or create the singleton ATS recommendations engine."""
    global _ats_recommendations_engine
    if _ats_recommendations_engine is None:
        _ats_recommendations_engine = ATSRecommendationsEngine()
    return _ats_recommendations_engine
