"""Skills Taxonomy System - Standardized skill mapping and validation.

This module provides a comprehensive skills taxonomy for mapping user skills
to standardized categories, validating skill names, and providing structured
skill data for better job matching and analytics.
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from shared.logging_config import get_logger

logger = get_logger("sorce.skills_taxonomy")


class SkillCategory(Enum):
    """Standardized skill categories."""

    PROGRAMMING = "programming"
    WEB_DEVELOPMENT = "web_development"
    DATA_SCIENCE = "data_science"
    CLOUD_DEVOPS = "cloud_devops"
    MOBILE_DEVELOPMENT = "mobile_development"
    DATABASE = "database"
    DESIGN = "design"
    PROJECT_MANAGEMENT = "project_management"
    MARKETING = "marketing"
    SALES = "sales"
    BUSINESS = "business"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    SECURITY = "security"
    QA_TESTING = "qa_testing"
    SOFT_SKILLS = "soft_skills"
    OTHER = "other"


@dataclass
class StandardizedSkill:
    """Standardized skill with metadata."""

    name: str
    category: SkillCategory
    aliases: Set[str]
    proficiency_levels: List[str]
    description: str
    demand_score: float  # 0.0 to 1.0, based on market demand
    technical_level: str  # "junior", "mid", "senior", "expert"


class SkillsTaxonomy:
    """Comprehensive skills taxonomy system."""

    def __init__(self):
        """Initialize the skills taxonomy with predefined skills."""
        self._skills_db: Dict[str, StandardizedSkill] = {}
        self._aliases_map: Dict[str, str] = {}
        self._category_skills: Dict[SkillCategory, Set[str]] = {}
        self._initialize_skills_database()
        self._build_mappings()

    def _initialize_skills_database(self) -> None:
        """Initialize the standardized skills database."""

        # Programming Languages
        programming_skills = {
            "Python": StandardizedSkill(
                name="Python",
                category=SkillCategory.PROGRAMMING,
                aliases={"python3", "py", "python 3"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="High-level programming language for general-purpose programming",
                demand_score=0.95,
                technical_level="mid",
            ),
            "JavaScript": StandardizedSkill(
                name="JavaScript",
                category=SkillCategory.PROGRAMMING,
                aliases={"js", "javascript", "ecmascript", "es6", "es2020"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Programming language for web development and scripting",
                demand_score=0.98,
                technical_level="mid",
            ),
            "Java": StandardizedSkill(
                name="Java",
                category=SkillCategory.PROGRAMMING,
                aliases={"java", "jvm", "spring"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Object-oriented programming language for enterprise applications",
                demand_score=0.85,
                technical_level="mid",
            ),
            "TypeScript": StandardizedSkill(
                name="TypeScript",
                category=SkillCategory.PROGRAMMING,
                aliases={"ts", "typescript", "tsx", "tsx"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Typed superset of JavaScript for large-scale applications",
                demand_score=0.92,
                technical_level="mid",
            ),
            "C++": StandardizedSkill(
                name="C++",
                category=SkillCategory.PROGRAMMING,
                aliases={"cpp", "c plus plus", "gnu c++"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="High-performance programming language for systems programming",
                demand_score=0.75,
                technical_level="senior",
            ),
            "C#": StandardizedSkill(
                name="C#",
                category=SkillCategory.PROGRAMMING,
                aliases={"csharp", "c sharp", ".net"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Object-oriented language for .NET framework applications",
                demand_score=0.80,
                technical_level="mid",
            ),
            "Go": StandardizedSkill(
                name="Go",
                category=SkillCategory.PROGRAMMING,
                aliases={"golang", "go lang"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Statically typed programming language for concurrent systems",
                demand_score=0.88,
                technical_level="mid",
            ),
            "Rust": StandardizedSkill(
                name="Rust",
                category=SkillCategory.PROGRAMMING,
                aliases={"rust lang", "rustc"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Systems programming language focused on safety and performance",
                demand_score=0.82,
                technical_level="senior",
            ),
            "Ruby": StandardizedSkill(
                name="Ruby",
                category=SkillCategory.PROGRAMMING,
                aliases={"ruby on rails", "rails", "ror"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Dynamic programming language known for Ruby on Rails framework",
                demand_score=0.70,
                technical_level="mid",
            ),
            "PHP": StandardizedSkill(
                name="PHP",
                category=SkillCategory.PROGRAMMING,
                aliases={"php7", "php8", "laravel", "wordpress"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Server-side scripting language for web development",
                demand_score=0.65,
                technical_level="mid",
            ),
            "Swift": StandardizedSkill(
                name="Swift",
                category=SkillCategory.PROGRAMMING,
                aliases={"ios", "swiftui", "xcode"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Programming language for iOS and macOS applications",
                demand_score=0.78,
                technical_level="mid",
            ),
            "Kotlin": StandardizedSkill(
                name="Kotlin",
                category=SkillCategory.PROGRAMMING,
                aliases={"android", "kotlin android"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Cross-platform programming language for Android and JVM",
                demand_score=0.76,
                technical_level="mid",
            ),
            "R": StandardizedSkill(
                name="R",
                category=SkillCategory.PROGRAMMING,
                aliases={"r language", "rstats", "tidyverse"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Programming language for statistical computing and graphics",
                demand_score=0.72,
                technical_level="mid",
            ),
            "MATLAB": StandardizedSkill(
                name="MATLAB",
                category=SkillCategory.PROGRAMMING,
                aliases={"matlab", "simulink"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Programming language for numerical computing and visualization",
                demand_score=0.68,
                technical_level="mid",
            ),
        }

        # Web Development
        web_dev_skills = {
            "React": StandardizedSkill(
                name="React",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"reactjs", "react js", "react native"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="JavaScript library for building user interfaces",
                demand_score=0.96,
                technical_level="mid",
            ),
            "Vue.js": StandardizedSkill(
                name="Vue.js",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"vue", "vuejs", "nuxt", "nuxt.js"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Progressive JavaScript framework for building UIs",
                demand_score=0.85,
                technical_level="mid",
            ),
            "Angular": StandardizedSkill(
                name="Angular",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"angularjs", "angular 2", "angular 10"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="TypeScript-based web application framework",
                demand_score=0.82,
                technical_level="mid",
            ),
            "Node.js": StandardizedSkill(
                name="Node.js",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"node", "nodejs", "express", "express.js"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="JavaScript runtime for server-side development",
                demand_score=0.94,
                technical_level="mid",
            ),
            "HTML": StandardizedSkill(
                name="HTML",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"html5", "html 5", "markup", "semantic html"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Markup language for structuring web content",
                demand_score=0.98,
                technical_level="junior",
            ),
            "CSS": StandardizedSkill(
                name="CSS",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"css3", "css 3", "stylesheets", "sass", "scss", "less"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Styling language for web page presentation",
                demand_score=0.96,
                technical_level="junior",
            ),
            "Next.js": StandardizedSkill(
                name="Next.js",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"next", "nextjs", "react framework"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="React framework for production-ready applications",
                demand_score=0.90,
                technical_level="mid",
            ),
            "Django": StandardizedSkill(
                name="Django",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"django framework", "django rest", "drf"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Python web framework for rapid development",
                demand_score=0.84,
                technical_level="mid",
            ),
            "Flask": StandardizedSkill(
                name="Flask",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"flask framework", "microframework"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Python microframework for web applications",
                demand_score=0.78,
                technical_level="mid",
            ),
            "WordPress": StandardizedSkill(
                name="WordPress",
                category=SkillCategory.WEB_DEVELOPMENT,
                aliases={"wp", "wordpress development", "woocommerce"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Content management system for websites and blogs",
                demand_score=0.72,
                technical_level="junior",
            ),
        }

        # Data Science & Analytics
        data_science_skills = {
            "Machine Learning": StandardizedSkill(
                name="Machine Learning",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"ml", "machine learning", "ai", "artificial intelligence"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Algorithms and statistical models for pattern recognition",
                demand_score=0.92,
                technical_level="senior",
            ),
            "Data Science": StandardizedSkill(
                name="Data Science",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"data analytics", "data analysis", "big data"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Interdisciplinary field for extracting knowledge from data",
                demand_score=0.90,
                technical_level="senior",
            ),
            "Deep Learning": StandardizedSkill(
                name="Deep Learning",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"neural networks", "tensorflow", "pytorch", "keras"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Subset of machine learning using artificial neural networks",
                demand_score=0.88,
                technical_level="expert",
            ),
            "TensorFlow": StandardizedSkill(
                name="TensorFlow",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"tf", "tensorflow 2", "keras"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Open-source machine learning framework",
                demand_score=0.86,
                technical_level="senior",
            ),
            "PyTorch": StandardizedSkill(
                name="PyTorch",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"torch", "pytorch lightning"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Open-source machine learning framework",
                demand_score=0.84,
                technical_level="senior",
            ),
            "Pandas": StandardizedSkill(
                name="Pandas",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"python pandas", "data frames"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Python library for data manipulation and analysis",
                demand_score=0.94,
                technical_level="mid",
            ),
            "NumPy": StandardizedSkill(
                name="NumPy",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"numpy", "python numpy", "arrays"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Python library for numerical computing",
                demand_score=0.90,
                technical_level="mid",
            ),
            "SQL": StandardizedSkill(
                name="SQL",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"structured query language", "mysql", "postgresql", "t-sql"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Domain-specific language for managing relational databases",
                demand_score=0.96,
                technical_level="junior",
            ),
            "Tableau": StandardizedSkill(
                name="Tableau",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"tableau desktop", "tableau server", "data visualization"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Interactive data visualization software",
                demand_score=0.82,
                technical_level="mid",
            ),
            "Power BI": StandardizedSkill(
                name="Power BI",
                category=SkillCategory.DATA_SCIENCE,
                aliases={"power bi desktop", "dax", "microsoft bi"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Business analytics and visualization tool",
                demand_score=0.80,
                technical_level="mid",
            ),
        }

        # Cloud & DevOps
        cloud_devops_skills = {
            "AWS": StandardizedSkill(
                name="AWS",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"amazon web services", "ec2", "s3", "lambda"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Amazon Web Services cloud computing platform",
                demand_score=0.94,
                technical_level="mid",
            ),
            "Docker": StandardizedSkill(
                name="Docker",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"containers", "containerization", "docker compose"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Platform for developing and running applications in containers",
                demand_score=0.92,
                technical_level="mid",
            ),
            "Kubernetes": StandardizedSkill(
                name="Kubernetes",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"k8s", "kubernetes", "container orchestration"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Container orchestration platform for automating deployment",
                demand_score=0.90,
                technical_level="senior",
            ),
            "Azure": StandardizedSkill(
                name="Azure",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"microsoft azure", "azure cloud", "azure devops"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Microsoft cloud computing platform",
                demand_score=0.86,
                technical_level="mid",
            ),
            "Google Cloud": StandardizedSkill(
                name="Google Cloud",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"gcp", "google cloud platform", "gke"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Google cloud computing platform",
                demand_score=0.82,
                technical_level="mid",
            ),
            "CI/CD": StandardizedSkill(
                name="CI/CD",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={
                    "continuous integration",
                    "continuous deployment",
                    "jenkins",
                    "github actions",
                },
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Automated process for software delivery",
                demand_score=0.88,
                technical_level="mid",
            ),
            "Terraform": StandardizedSkill(
                name="Terraform",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"infrastructure as code", "iac", "terraform hcl"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Infrastructure as code tool for building and managing infrastructure",
                demand_score=0.84,
                technical_level="mid",
            ),
            "Ansible": StandardizedSkill(
                name="Ansible",
                category=SkillCategory.CLOUD_DEVOPS,
                aliases={"automation", "configuration management", "playbooks"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Automation tool for software provisioning and configuration management",
                demand_score=0.80,
                technical_level="mid",
            ),
        }

        # Database
        database_skills = {
            "PostgreSQL": StandardizedSkill(
                name="PostgreSQL",
                category=SkillCategory.DATABASE,
                aliases={"postgres", "postgresql", "pgsql"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Open-source relational database system",
                demand_score=0.90,
                technical_level="mid",
            ),
            "MySQL": StandardizedSkill(
                name="MySQL",
                category=SkillCategory.DATABASE,
                aliases={"mysql database", "mariadb"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Open-source relational database management system",
                demand_score=0.88,
                technical_level="mid",
            ),
            "MongoDB": StandardizedSkill(
                name="MongoDB",
                category=SkillCategory.DATABASE,
                aliases={"nosql", "document database", "bson"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="NoSQL document-oriented database",
                demand_score=0.82,
                technical_level="mid",
            ),
            "Redis": StandardizedSkill(
                name="Redis",
                category=SkillCategory.DATABASE,
                aliases={"redis cache", "in-memory database"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="In-memory data structure store used as database, cache, and message broker",
                demand_score=0.86,
                technical_level="mid",
            ),
            "Oracle": StandardizedSkill(
                name="Oracle",
                category=SkillCategory.DATABASE,
                aliases={"oracle database", "plsql"},
                proficiency_levels=["Beginner", "Intermediate", "Advanced", "Expert"],
                description="Multi-model database management system",
                demand_score=0.75,
                technical_level="senior",
            ),
        }

        # Soft Skills
        soft_skills = {
            "Leadership": StandardizedSkill(
                name="Leadership",
                category=SkillCategory.SOFT_SKILLS,
                aliases={"team leadership", "management", "people management"},
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Ability to lead and guide teams toward goals",
                demand_score=0.85,
                technical_level="junior",
            ),
            "Communication": StandardizedSkill(
                name="Communication",
                category=SkillCategory.SOFT_SKILLS,
                aliases={
                    "written communication",
                    "verbal communication",
                    "presentation",
                },
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Ability to effectively convey information and ideas",
                demand_score=0.90,
                technical_level="junior",
            ),
            "Problem Solving": StandardizedSkill(
                name="Problem Solving",
                category=SkillCategory.SOFT_SKILLS,
                aliases={"critical thinking", "analytical thinking", "troubleshooting"},
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Ability to analyze problems and find effective solutions",
                demand_score=0.92,
                technical_level="junior",
            ),
            "Teamwork": StandardizedSkill(
                name="Teamwork",
                category=SkillCategory.SOFT_SKILLS,
                aliases={"collaboration", "team collaboration", "interpersonal skills"},
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Ability to work effectively with others in a team setting",
                demand_score=0.88,
                technical_level="junior",
            ),
            "Project Management": StandardizedSkill(
                name="Project Management",
                category=SkillCategory.PROJECT_MANAGEMENT,
                aliases={"pmp", "agile", "scrum", "waterfall"},
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Process of planning, executing, and managing projects",
                demand_score=0.86,
                technical_level="mid",
            ),
            "Time Management": StandardizedSkill(
                name="Time Management",
                category=SkillCategory.SOFT_SKILLS,
                aliases={"organization", "prioritization", "efficiency"},
                proficiency_levels=["Developing", "Proficient", "Advanced", "Expert"],
                description="Ability to use time effectively and productively",
                demand_score=0.80,
                technical_level="junior",
            ),
        }

        # Combine all skills
        all_skills = {
            **programming_skills,
            **web_dev_skills,
            **data_science_skills,
            **cloud_devops_skills,
            **database_skills,
            **soft_skills,
        }

        self._skills_db = all_skills

    def _build_mappings(self) -> None:
        """Build internal mappings for efficient lookup."""
        # Build aliases map
        for skill_name, skill in self._skills_db.items():
            # Add the canonical name
            self._aliases_map[skill_name.lower()] = skill_name

            # Add all aliases
            for alias in skill.aliases:
                normalized_alias = alias.lower()
                self._aliases_map[normalized_alias] = skill_name

        # Build category mapping
        for skill_name, skill in self._skills_db.items():
            category = skill.category
            if category not in self._category_skills:
                self._category_skills[category] = set()
            self._category_skills[category].add(skill_name)

    def normalize_skill(self, skill_input: str) -> Optional[str]:
        """Normalize a skill input to the canonical skill name.

        Args:
            skill_input: Raw skill input from user or resume parsing

        Returns:
            Canonical skill name if found, None otherwise
        """
        if not skill_input or not skill_input.strip():
            return None

        # Normalize the input
        normalized_input = skill_input.strip().lower()

        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            "experience in",
            "knowledge of",
            "skilled in",
            "proficient in",
        ]
        suffixes_to_remove = ["development", "programming", "language", "framework"]

        for prefix in prefixes_to_remove:
            if normalized_input.startswith(prefix):
                normalized_input = normalized_input[len(prefix) :].strip()

        for suffix in suffixes_to_remove:
            if normalized_input.endswith(suffix):
                normalized_input = normalized_input[: -len(suffix)].strip()

        # Try direct lookup
        if normalized_input in self._aliases_map:
            return self._aliases_map[normalized_input]

        # Try fuzzy matching
        best_match = self._fuzzy_match_skill(normalized_input)
        if best_match:
            return best_match

        return None

    def _fuzzy_match_skill(self, skill_input: str) -> Optional[str]:
        """Fuzzy match skill input to known skills."""
        best_match = None
        best_score = 0.0

        for canonical_name, skill in self._skills_db.items():
            # Check exact match with canonical name
            if canonical_name.lower() == skill_input:
                return canonical_name

            # Check aliases
            for alias in skill.aliases:
                if alias.lower() == skill_input:
                    return canonical_name

            # Check partial matches
            if (
                skill_input in canonical_name.lower()
                or canonical_name.lower() in skill_input
            ):
                score = len(skill_input) / len(canonical_name)
                if score > best_score and score > 0.7:  # Threshold for partial match
                    best_match = canonical_name
                    best_score = score

            # Check alias partial matches
            for alias in skill.aliases:
                if skill_input in alias.lower() or alias.lower() in skill_input:
                    score = len(skill_input) / len(alias)
                    if score > best_score and score > 0.7:
                        best_match = canonical_name
                        best_score = score

        return best_match

    def validate_and_normalize_skills(
        self, skills: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Validate and normalize a list of skills.

        Args:
            skills: List of raw skill strings

        Returns:
            Tuple of (valid_skills, invalid_skills)
        """
        valid_skills = []
        invalid_skills = []

        for skill in skills:
            normalized = self.normalize_skill(skill)
            if normalized:
                if normalized not in valid_skills:  # Avoid duplicates
                    valid_skills.append(normalized)
            else:
                invalid_skills.append(skill)

        return valid_skills, invalid_skills

    def get_skill_info(self, skill_name: str) -> Optional[StandardizedSkill]:
        """Get detailed information about a skill."""
        if skill_name in self._skills_db:
            return self._skills_db[skill_name]
        return None

    def get_skills_by_category(self, category: SkillCategory) -> List[str]:
        """Get all skills in a specific category."""
        return sorted(list(self._category_skills.get(category, set())))

    def get_skill_categories(self) -> List[SkillCategory]:
        """Get all available skill categories."""
        return list(SkillCategory)

    def calculate_skill_score(
        self, skills: List[str], weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate a composite skill score based on demand and variety.

        Args:
            skills: List of normalized skill names
            weights: Optional weights for different categories

        Returns:
            Composite skill score (0.0 to 1.0)
        """
        if not skills:
            return 0.0

        # Default weights for categories
        default_weights = {
            SkillCategory.PROGRAMMING: 0.25,
            SkillCategory.WEB_DEVELOPMENT: 0.20,
            SkillCategory.DATA_SCIENCE: 0.20,
            SkillCategory.CLOUD_DEVOPS: 0.15,
            SkillCategory.DATABASE: 0.10,
            SkillCategory.SOFT_SKILLS: 0.10,
        }

        category_weights = weights or default_weights

        # Calculate weighted score
        total_score = 0.0
        category_scores = {}

        for skill_name in skills:
            skill_info = self.get_skill_info(skill_name)
            if skill_info:
                category = skill_info.category
                demand_score = skill_info.demand_score

                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(demand_score)

        # Calculate weighted average
        for category, scores in category_scores.items():
            if category in category_weights:
                avg_score = sum(scores) / len(scores)
                weight = category_weights[category]
                total_score += avg_score * weight

        # Normalize to 0-1 range
        return min(total_score, 1.0)

    def suggest_missing_skills(
        self, user_skills: List[str], target_role: str
    ) -> List[str]:
        """Suggest missing skills based on target role.

        Args:
            user_skills: List of user's current skills
            target_role: Target job role (e.g., "Software Engineer", "Data Scientist")

        Returns:
            List of suggested skills to learn
        """
        target_skills = self._get_target_role_skills(target_role)
        user_skill_set = set(user_skills)

        missing_skills = []
        for skill in target_skills:
            if skill not in user_skill_set:
                missing_skills.append(skill)

        # Sort by demand score
        missing_skills.sort(key=lambda x: self._skills_db[x].demand_score, reverse=True)

        return missing_skills[:10]  # Return top 10 suggestions

    def _get_target_role_skills(self, target_role: str) -> List[str]:
        """Get recommended skills for a target role."""
        role_mappings = {
            "Software Engineer": [
                "Python",
                "JavaScript",
                "React",
                "Node.js",
                "Git",
                "SQL",
                "Docker",
                "AWS",
                "Testing",
                "System Design",
            ],
            "Data Scientist": [
                "Python",
                "Machine Learning",
                "Deep Learning",
                "TensorFlow",
                "PyTorch",
                "Pandas",
                "NumPy",
                "SQL",
                "Statistics",
                "Data Visualization",
            ],
            "DevOps Engineer": [
                "Docker",
                "Kubernetes",
                "CI/CD",
                "AWS",
                "Linux",
                "Python",
                "Terraform",
                "Monitoring",
                "Security",
                "Networking",
            ],
            "Frontend Developer": [
                "JavaScript",
                "React",
                "Vue.js",
                "HTML",
                "CSS",
                "TypeScript",
                "Node.js",
                "Web Performance",
                "Testing",
                "UI/UX Design",
            ],
            "Backend Developer": [
                "Python",
                "Java",
                "Node.js",
                "SQL",
                "PostgreSQL",
                "MongoDB",
                "API Design",
                "Security",
                "Performance",
                "System Architecture",
            ],
            "Full Stack Developer": [
                "Python",
                "JavaScript",
                "React",
                "Node.js",
                "SQL",
                "Docker",
                "AWS",
                "Git",
                "Testing",
                "System Design",
                "Frontend",
                "Backend",
            ],
        }

        # Normalize role name
        normalized_role = target_role.lower().strip()

        for role, skills in role_mappings.items():
            if role.lower() in normalized_role or normalized_role in role.lower():
                return skills

        # Default to common tech skills if role not found
        return [
            "Python",
            "JavaScript",
            "React",
            "Node.js",
            "SQL",
            "Git",
            "Docker",
            "AWS",
            "Communication",
            "Problem Solving",
        ]


# Global instance
_skills_taxonomy = None


def get_skills_taxonomy() -> SkillsTaxonomy:
    """Get the global skills taxonomy instance."""
    global _skills_taxonomy
    if _skills_taxonomy is None:
        _skills_taxonomy = SkillsTaxonomy()
    return _skills_taxonomy


def validate_user_skills(skills: List[str]) -> Tuple[List[str], List[str], Dict]:
    """Validate user skills and return analysis.

    Args:
        skills: List of raw skill strings

    Returns:
        Tuple of (valid_skills, invalid_skills, analysis_dict)
    """
    taxonomy = get_skills_taxonomy()
    valid_skills, invalid_skills = taxonomy.validate_and_normalize_skills(skills)

    # Calculate analysis
    analysis = {
        "total_skills": len(skills),
        "valid_skills": len(valid_skills),
        "invalid_skills": len(invalid_skills),
        "skill_score": taxonomy.calculate_skill_score(valid_skills),
        "category_distribution": {},
        "top_skills": [],
    }

    # Category distribution
    for skill_name in valid_skills:
        skill_info = taxonomy.get_skill_info(skill_name)
        if skill_info:
            category = skill_info.category.value
            analysis["category_distribution"][category] = (
                analysis["category_distribution"].get(category, 0) + 1
            )

    # Top skills by demand
    valid_skills.sort(
        key=lambda x: taxonomy.get_skill_info(x).demand_score, reverse=True
    )
    analysis["top_skills"] = valid_skills[:5]

    return valid_skills, invalid_skills, analysis
