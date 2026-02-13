"""
Skill normalization service.

Provides:
- Skill synonym mapping
- Skill categorization
- Skill level inference
- Cross-platform skill mapping
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Categories of skills."""
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    MOBILE = "mobile"
    DESIGN = "design"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    LEADERSHIP = "leadership"
    OTHER = "other"


class SkillLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class NormalizedSkill:
    """A normalized skill with metadata."""
    canonical_name: str
    display_name: str
    category: SkillCategory
    level: Optional[SkillLevel] = None
    aliases: list[str] = field(default_factory=list)
    related_skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


# Skill synonym mappings
SKILL_SYNONYMS: dict[str, str] = {
    # Programming languages
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "c#": "csharp",
    "c sharp": "csharp",
    "c++": "cpp",
    "c plus plus": "cpp",
    "objective-c": "objectivec",
    "obj-c": "objectivec",
    "k8s": "kubernetes",
    "gcp": "google cloud platform",
    "aws": "amazon web services",
    "azure": "microsoft azure",
    
    # Frameworks
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "django rest framework": "django rest framework",
    "drf": "django rest framework",
    
    # Databases
    "postgres": "postgresql",
    "pg": "postgresql",
    "mongo": "mongodb",
    "redis cache": "redis",
    
    # DevOps
    "ci/cd": "cicd",
    "ci cd": "cicd",
    "infrastructure as code": "iac",
    "terraform": "terraform",
    "ansible": "ansible",
    
    # Data Science
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "data viz": "data visualization",
    
    # Soft skills
    "comm skills": "communication",
    "team lead": "team leadership",
    "project mgmt": "project management",
    "pmp": "project management professional",
}

# Skill categorization
SKILL_CATEGORIES: dict[str, SkillCategory] = {
    # Programming languages
    "javascript": SkillCategory.PROGRAMMING_LANGUAGE,
    "typescript": SkillCategory.PROGRAMMING_LANGUAGE,
    "python": SkillCategory.PROGRAMMING_LANGUAGE,
    "java": SkillCategory.PROGRAMMING_LANGUAGE,
    "c": SkillCategory.PROGRAMMING_LANGUAGE,
    "cpp": SkillCategory.PROGRAMMING_LANGUAGE,
    "csharp": SkillCategory.PROGRAMMING_LANGUAGE,
    "go": SkillCategory.PROGRAMMING_LANGUAGE,
    "rust": SkillCategory.PROGRAMMING_LANGUAGE,
    "ruby": SkillCategory.PROGRAMMING_LANGUAGE,
    "php": SkillCategory.PROGRAMMING_LANGUAGE,
    "swift": SkillCategory.PROGRAMMING_LANGUAGE,
    "kotlin": SkillCategory.PROGRAMMING_LANGUAGE,
    "scala": SkillCategory.PROGRAMMING_LANGUAGE,
    "r": SkillCategory.PROGRAMMING_LANGUAGE,
    "sql": SkillCategory.PROGRAMMING_LANGUAGE,
    
    # Frontend
    "react": SkillCategory.FRONTEND,
    "vue": SkillCategory.FRONTEND,
    "angular": SkillCategory.FRONTEND,
    "svelte": SkillCategory.FRONTEND,
    "next.js": SkillCategory.FRONTEND,
    "html": SkillCategory.FRONTEND,
    "css": SkillCategory.FRONTEND,
    "tailwind": SkillCategory.FRONTEND,
    "bootstrap": SkillCategory.FRONTEND,
    
    # Backend
    "node.js": SkillCategory.BACKEND,
    "express": SkillCategory.BACKEND,
    "django": SkillCategory.BACKEND,
    "flask": SkillCategory.BACKEND,
    "fastapi": SkillCategory.BACKEND,
    "spring": SkillCategory.BACKEND,
    "rails": SkillCategory.BACKEND,
    "laravel": SkillCategory.BACKEND,
    
    # Database
    "postgresql": SkillCategory.DATABASE,
    "mysql": SkillCategory.DATABASE,
    "mongodb": SkillCategory.DATABASE,
    "redis": SkillCategory.DATABASE,
    "elasticsearch": SkillCategory.DATABASE,
    "sqlite": SkillCategory.DATABASE,
    "dynamodb": SkillCategory.DATABASE,
    "cassandra": SkillCategory.DATABASE,
    
    # Cloud
    "amazon web services": SkillCategory.CLOUD,
    "google cloud platform": SkillCategory.CLOUD,
    "microsoft azure": SkillCategory.CLOUD,
    "digitalocean": SkillCategory.CLOUD,
    "heroku": SkillCategory.CLOUD,
    "vercel": SkillCategory.CLOUD,
    "netlify": SkillCategory.CLOUD,
    
    # DevOps
    "docker": SkillCategory.DEVOPS,
    "kubernetes": SkillCategory.DEVOPS,
    "terraform": SkillCategory.DEVOPS,
    "ansible": SkillCategory.DEVOPS,
    "jenkins": SkillCategory.DEVOPS,
    "github actions": SkillCategory.DEVOPS,
    "gitlab ci": SkillCategory.DEVOPS,
    "cicd": SkillCategory.DEVOPS,
    
    # Data Science
    "pandas": SkillCategory.DATA_SCIENCE,
    "numpy": SkillCategory.DATA_SCIENCE,
    "scipy": SkillCategory.DATA_SCIENCE,
    "matplotlib": SkillCategory.DATA_SCIENCE,
    "tableau": SkillCategory.DATA_SCIENCE,
    "power bi": SkillCategory.DATA_SCIENCE,
    "spark": SkillCategory.DATA_SCIENCE,
    "hadoop": SkillCategory.DATA_SCIENCE,
    
    # Machine Learning
    "tensorflow": SkillCategory.MACHINE_LEARNING,
    "pytorch": SkillCategory.MACHINE_LEARNING,
    "keras": SkillCategory.MACHINE_LEARNING,
    "scikit-learn": SkillCategory.MACHINE_LEARNING,
    "machine learning": SkillCategory.MACHINE_LEARNING,
    "deep learning": SkillCategory.MACHINE_LEARNING,
    "artificial intelligence": SkillCategory.MACHINE_LEARNING,
    "natural language processing": SkillCategory.MACHINE_LEARNING,
    "computer vision": SkillCategory.MACHINE_LEARNING,
    
    # Mobile
    "react native": SkillCategory.MOBILE,
    "flutter": SkillCategory.MOBILE,
    "ios": SkillCategory.MOBILE,
    "android": SkillCategory.MOBILE,
    "objectivec": SkillCategory.MOBILE,
    
    # Design
    "figma": SkillCategory.DESIGN,
    "sketch": SkillCategory.DESIGN,
    "adobe xd": SkillCategory.DESIGN,
    "photoshop": SkillCategory.DESIGN,
    "illustrator": SkillCategory.DESIGN,
    "ui design": SkillCategory.DESIGN,
    "ux design": SkillCategory.DESIGN,
    
    # Project Management
    "agile": SkillCategory.PROJECT_MANAGEMENT,
    "scrum": SkillCategory.PROJECT_MANAGEMENT,
    "kanban": SkillCategory.PROJECT_MANAGEMENT,
    "jira": SkillCategory.PROJECT_MANAGEMENT,
    "project management": SkillCategory.PROJECT_MANAGEMENT,
    
    # Communication
    "communication": SkillCategory.COMMUNICATION,
    "presentation": SkillCategory.COMMUNICATION,
    "writing": SkillCategory.COMMUNICATION,
    "public speaking": SkillCategory.COMMUNICATION,
    
    # Leadership
    "leadership": SkillCategory.LEADERSHIP,
    "team leadership": SkillCategory.LEADERSHIP,
    "mentoring": SkillCategory.LEADERSHIP,
    "people management": SkillCategory.LEADERSHIP,
}

# Related skills mapping
RELATED_SKILLS: dict[str, list[str]] = {
    "javascript": ["typescript", "node.js", "react", "vue", "angular"],
    "typescript": ["javascript", "node.js", "react"],
    "python": ["django", "flask", "fastapi", "pandas", "numpy"],
    "react": ["javascript", "typescript", "next.js", "react native"],
    "node.js": ["javascript", "typescript", "express"],
    "django": ["python", "postgresql", "django rest framework"],
    "aws": ["lambda", "ec2", "s3", "dynamodb", "kubernetes"],
    "docker": ["kubernetes", "cicd", "devops"],
    "kubernetes": ["docker", "helm", "devops", "cloud"],
    "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn"],
}


class SkillNormalizer:
    """
    Normalizes skills across job postings.
    
    Features:
    - Synonym resolution
    - Category classification
    - Level inference
    - Related skill suggestions
    """
    
    def __init__(
        self,
        custom_synonyms: Optional[dict[str, str]] = None,
        custom_categories: Optional[dict[str, SkillCategory]] = None,
    ):
        self._synonyms = {**SKILL_SYNONYMS, **(custom_synonyms or {})}
        self._categories = {**SKILL_CATEGORIES, **(custom_categories or {})}
    
    def normalize(self, skill: str) -> NormalizedSkill:
        """
        Normalize a skill string.
        
        Args:
            skill: Raw skill string from job posting
            
        Returns:
            NormalizedSkill with canonical name and metadata
        """
        # Clean the skill string
        cleaned = self._clean_skill(skill)
        
        # Resolve synonyms
        canonical = self._resolve_synonym(cleaned)
        
        # Get category
        category = self._get_category(canonical)
        
        # Infer level if present
        level = self._infer_level(skill)
        
        # Get related skills
        related = RELATED_SKILLS.get(canonical, [])
        
        # Get aliases
        aliases = [
            k for k, v in self._synonyms.items()
            if v == canonical
        ]
        
        return NormalizedSkill(
            canonical_name=canonical,
            display_name=self._format_display_name(canonical),
            category=category,
            level=level,
            aliases=aliases,
            related_skills=related,
            tags=self._generate_tags(canonical, category),
        )
    
    def normalize_batch(
        self,
        skills: list[str],
    ) -> list[NormalizedSkill]:
        """Normalize a batch of skills."""
        return [self.normalize(skill) for skill in skills]
    
    def _clean_skill(self, skill: str) -> str:
        """Clean and normalize skill string."""
        # Convert to lowercase
        cleaned = skill.lower().strip()
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(proficient in|experience with|knowledge of|expert in)\s*', '', cleaned)
        cleaned = re.sub(r'\s*(required|preferred|nice to have)$', '', cleaned)
        
        # Remove years of experience
        cleaned = re.sub(r'\s*\d+\+?\s*years?\s*$', '', cleaned)
        
        # Remove level indicators
        cleaned = re.sub(r'\s*(junior|senior|lead|principal|staff)\s*$', '', cleaned)
        
        return cleaned.strip()
    
    def _resolve_synonym(self, skill: str) -> str:
        """Resolve skill to canonical name."""
        # Direct lookup
        if skill in self._synonyms:
            return self._synonyms[skill]
        
        # Try case-insensitive lookup
        skill_lower = skill.lower()
        for key, value in self._synonyms.items():
            if key.lower() == skill_lower:
                return value
        
        # No synonym found, return cleaned skill
        return skill_lower
    
    def _get_category(self, skill: str) -> SkillCategory:
        """Get category for a skill."""
        return self._categories.get(skill, SkillCategory.OTHER)
    
    def _infer_level(self, skill: str) -> Optional[SkillLevel]:
        """Infer skill level from original string."""
        skill_lower = skill.lower()
        
        if any(w in skill_lower for w in ["expert", "guru", "master", "architect"]):
            return SkillLevel.EXPERT
        elif any(w in skill_lower for w in ["senior", "lead", "advanced", "strong"]):
            return SkillLevel.ADVANCED
        elif any(w in skill_lower for w in ["junior", "entry", "beginner", "basic"]):
            return SkillLevel.BEGINNER
        elif any(w in skill_lower for w in ["intermediate", "mid", "mid-level"]):
            return SkillLevel.INTERMEDIATE
        
        return None
    
    def _format_display_name(self, skill: str) -> str:
        """Format skill for display."""
        # Handle special cases
        special_cases = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "node.js": "Node.js",
            "next.js": "Next.js",
            "vue": "Vue.js",
            "react": "React",
            "angular": "Angular",
            "postgresql": "PostgreSQL",
            "mongodb": "MongoDB",
            "aws": "AWS",
            "gcp": "GCP",
            "ui design": "UI Design",
            "ux design": "UX Design",
            "cicd": "CI/CD",
        }
        
        if skill in special_cases:
            return special_cases[skill]
        
        # Title case for most skills
        return skill.title()
    
    def _generate_tags(
        self,
        skill: str,
        category: SkillCategory,
    ) -> list[str]:
        """Generate tags for a skill."""
        tags = [category.value]
        
        # Add technology type tags
        if category in [SkillCategory.PROGRAMMING_LANGUAGE, SkillCategory.FRONTEND, SkillCategory.BACKEND]:
            tags.append("technical")
        elif category in [SkillCategory.COMMUNICATION, SkillCategory.LEADERSHIP]:
            tags.append("soft_skill")
        elif category in [SkillCategory.CLOUD, SkillCategory.DEVOPS]:
            tags.append("infrastructure")
        elif category in [SkillCategory.DATA_SCIENCE, SkillCategory.MACHINE_LEARNING]:
            tags.append("data")
        
        return tags
    
    def extract_skills_from_text(
        self,
        text: str,
    ) -> list[NormalizedSkill]:
        """
        Extract and normalize skills from job description text.
        
        Args:
            text: Job description or requirements text
            
        Returns:
            List of normalized skills found
        """
        found_skills: list[NormalizedSkill] = []
        seen: set[str] = set()
        
        # Check for known skills
        for skill_key in self._categories.keys():
            if skill_key in text.lower() and skill_key not in seen:
                normalized = self.normalize(skill_key)
                found_skills.append(normalized)
                seen.add(skill_key)
        
        # Check for synonyms
        for synonym in self._synonyms.keys():
            if synonym in text.lower():
                canonical = self._synonyms[synonym]
                if canonical not in seen:
                    normalized = self.normalize(canonical)
                    found_skills.append(normalized)
                    seen.add(canonical)
        
        return found_skills
    
    def group_by_category(
        self,
        skills: list[NormalizedSkill],
    ) -> dict[SkillCategory, list[NormalizedSkill]]:
        """Group skills by category."""
        grouped: dict[SkillCategory, list[NormalizedSkill]] = {}
        
        for skill in skills:
            if skill.category not in grouped:
                grouped[skill.category] = []
            grouped[skill.category].append(skill)
        
        return grouped


# Global normalizer instance
_normalizer: Optional[SkillNormalizer] = None


def get_skill_normalizer() -> SkillNormalizer:
    """Get the global skill normalizer."""
    global _normalizer
    if _normalizer is None:
        _normalizer = SkillNormalizer()
    return _normalizer


def normalize_skill(skill: str) -> NormalizedSkill:
    """Convenience function to normalize a single skill."""
    return get_skill_normalizer().normalize(skill)


def normalize_skills(skills: list[str]) -> list[NormalizedSkill]:
    """Convenience function to normalize multiple skills."""
    return get_skill_normalizer().normalize_batch(skills)
