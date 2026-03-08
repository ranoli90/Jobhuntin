"""Professional PDF generation service for tailored resumes.

Implements ATS-optimized PDF generation with:
- Professional formatting and layout
- Keyword optimization integration
- Multiple template styles
- Section reordering based on job relevance
- Contact information and header formatting
- Skills prioritization and emphasis
- Experience bullet point optimization
- Education and certification sections
- ATS-friendly formatting rules

Key features:
1. Professional resume templates
2. Dynamic content based on tailoring results
3. ATS-optimized formatting
4. Multiple style options
5. Contact information headers
6. Skills prioritization
7. Experience emphasis
8. Education and certifications
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, List

from reportlab.lib.colors import darkblue, darkgray, gray
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from backend.domain.resume_tailoring import TailoredResumeResult
from shared.logging_config import get_logger

logger = get_logger("sorce.resume_pdf_generator")


class ResumePDFGenerator:
    """Professional PDF generator for tailored resumes.

    Creates ATS-optimized PDF resumes with professional formatting
    and dynamic content based on tailoring results.
    """

    def __init__(self):
        self._setup_fonts()
        self._setup_styles()

    def _setup_fonts(self) -> None:
        """Setup professional fonts for resume generation."""
        try:
            # Try to use system fonts, fallback to built-in
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",
                "/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont("Arial", font_path))
                    break
            else:
                # Use built-in fonts as fallback
                logger.warning("No Arial font found, using built-in fonts")
        except Exception as e:
            logger.warning(f"Font setup failed: {e}")

    def _setup_styles(self) -> None:
        """Setup professional styles for resume sections."""
        self.styles = getSampleStyleSheet()

        # Custom styles for professional resume
        self.styles.add(
            ParagraphStyle(
                name="ResumeHeader",
                parent=self.styles["Heading1"],
                fontSize=16,
                spaceAfter=12,
                textColor=darkblue,
                alignment=1,  # Center
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ContactInfo",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                alignment=1,  # Center
                textColor=darkgray,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=16,
                textColor=darkblue,
                borderWidth=0,
                borderBottomWidth=1,
                borderColor=gray,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="BulletPoint",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=2,
                leftIndent=20,
                bulletIndent=10,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="NormalText",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=4,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SkillTag",
                parent=self.styles["Normal"],
                fontSize=9,
                spaceAfter=2,
            )
        )

    def generate_tailored_resume_pdf(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        tailoring_result: TailoredResumeResult,
        template_style: str = "professional",
    ) -> bytes:
        """Generate a tailored resume PDF.

        Args:
            profile: User profile data
            job: Job posting data
            tailoring_result: Resume tailoring analysis results
            template_style: Template style (professional, modern, executive)

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build resume content
        story = []

        # Header with contact information
        story.extend(self._build_header(profile))

        # Professional summary (tailored)
        story.extend(self._build_summary(tailoring_result.tailored_summary))

        # Skills section (prioritized)
        story.extend(
            self._build_skills_section(
                profile.get("skills", {}), tailoring_result.highlighted_skills
            )
        )

        # Experience section (emphasized)
        story.extend(
            self._build_experience_section(
                profile.get("experience", []), tailoring_result.emphasized_experiences
            )
        )

        # Education section
        story.extend(self._build_education_section(profile.get("education", [])))

        # Certifications section
        story.extend(
            self._build_certifications_section(profile.get("certifications", []))
        )

        # Keywords section (for ATS optimization)
        if tailoring_result.added_keywords:
            story.extend(self._build_keywords_section(tailoring_result.added_keywords))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_header(self, profile: Dict[str, Any]) -> List[Any]:
        """Build resume header with contact information."""
        elements = []

        # Name
        name = profile.get("name", "YOUR NAME")
        elements.append(Paragraph(name, self.styles["ResumeHeader"]))

        # Contact information
        contact_parts = []

        if profile.get("email"):
            contact_parts.append(f"📧 {profile['email']}")
        if profile.get("phone"):
            contact_parts.append(f"📱 {profile['phone']}")
        if profile.get("location"):
            contact_parts.append(f"📍 {profile['location']}")
        if profile.get("linkedin"):
            contact_parts.append(f"💼 {profile['linkedin']}")
        if profile.get("github"):
            contact_parts.append(f"💻 {profile['github']}")

        if contact_parts:
            contact_text = " | ".join(contact_parts)
            elements.append(Paragraph(contact_text, self.styles["ContactInfo"]))

        elements.append(Spacer(1, 12))
        return elements

    def _build_summary(self, tailored_summary: str) -> List[Any]:
        """Build professional summary section."""
        elements = []

        elements.append(Paragraph("PROFESSIONAL SUMMARY", self.styles["SectionHeader"]))
        elements.append(Paragraph(tailored_summary, self.styles["NormalText"]))
        elements.append(Spacer(1, 12))

        return elements

    def _build_skills_section(
        self,
        skills: Dict[str, List[str]],
        highlighted_skills: List[str],
    ) -> List[Any]:
        """Build skills section with prioritized skills."""
        elements = []

        elements.append(Paragraph("SKILLS", self.styles["SectionHeader"]))

        # Highlighted skills first
        if highlighted_skills:
            highlighted_text = ", ".join(highlighted_skills[:10])
            elements.append(
                Paragraph(
                    f"<b>Key Skills:</b> {highlighted_text}", self.styles["NormalText"]
                )
            )

        # Technical skills
        technical = skills.get("technical", [])
        if technical:
            # Filter and prioritize based on highlighted skills
            prioritized_technical = [
                skill for skill in technical if skill in highlighted_skills
            ] + [skill for skill in technical if skill not in highlighted_skills]

            if prioritized_technical:
                tech_text = ", ".join(prioritized_technical[:15])
                elements.append(
                    Paragraph(
                        f"<b>Technical:</b> {tech_text}", self.styles["NormalText"]
                    )
                )

        # Soft skills
        soft = skills.get("soft", [])
        if soft:
            soft_text = ", ".join(soft[:8])
            elements.append(
                Paragraph(f"<b>Soft Skills:</b> {soft_text}", self.styles["NormalText"])
            )

        elements.append(Spacer(1, 12))
        return elements

    def _build_experience_section(
        self,
        experiences: List[Dict[str, Any]],
        emphasized_experiences: List[Dict[str, Any]],
    ) -> List[Any]:
        """Build experience section with emphasized positions."""
        elements = []

        elements.append(
            Paragraph("PROFESSIONAL EXPERIENCE", self.styles["SectionHeader"])
        )

        # Combine emphasized experiences with regular ones
        all_experiences = emphasized_experiences + [
            exp for exp in experiences if exp not in emphasized_experiences
        ]

        for exp in all_experiences[:5]:  # Limit to 5 most relevant
            # Job title and company
            title = exp.get("title", "Position")
            company = exp.get("company", "Company")
            dates = exp.get("dates", "")

            header_text = f"<b>{title}</b> - {company}"
            if dates:
                header_text += f" | {dates}"

            elements.append(Paragraph(header_text, self.styles["NormalText"]))

            # Responsibilities and achievements
            responsibilities = exp.get("responsibilities", [])
            achievements = exp.get("achievements", [])

            all_points = responsibilities + achievements

            for point in all_points[:5]:  # Limit bullets per position
                elements.append(Paragraph(f"• {point}", self.styles["BulletPoint"]))

            elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 12))
        return elements

    def _build_education_section(self, education: List[Dict[str, Any]]) -> List[Any]:
        """Build education section."""
        elements = []

        if not education:
            return elements

        elements.append(Paragraph("EDUCATION", self.styles["SectionHeader"]))

        for edu in education[:3]:  # Limit to 3 most recent
            degree = edu.get("degree", "Degree")
            school = edu.get("school", "School")
            dates = edu.get("dates", "")
            gpa = edu.get("gpa", "")

            education_text = f"<b>{degree}</b> - {school}"
            if dates:
                education_text += f" | {dates}"
            if gpa:
                education_text += f" (GPA: {gpa})"

            elements.append(Paragraph(education_text, self.styles["NormalText"]))

            # Relevant coursework if available
            coursework = edu.get("coursework", [])
            if coursework:
                coursework_text = ", ".join(coursework[:5])
                elements.append(
                    Paragraph(
                        f"Relevant Coursework: {coursework_text}",
                        self.styles["NormalText"],
                    )
                )

            elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 12))
        return elements

    def _build_certifications_section(
        self, certifications: List[Dict[str, Any]]
    ) -> List[Any]:
        """Build certifications section."""
        elements = []

        if not certifications:
            return elements

        elements.append(Paragraph("CERTIFICATIONS", self.styles["SectionHeader"]))

        for cert in certifications[:5]:  # Limit to 5 most relevant
            name = cert.get("name", "Certification")
            issuer = cert.get("issuer", "Issuer")
            date = cert.get("date", "")

            cert_text = f"<b>{name}</b> - {issuer}"
            if date:
                cert_text += f" | {date}"

            elements.append(Paragraph(cert_text, self.styles["NormalText"]))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 12))
        return elements

    def _build_keywords_section(self, keywords: List[str]) -> List[Any]:
        """Build keywords section for ATS optimization."""
        elements = []

        elements.append(Paragraph("KEY COMPETENCIES", self.styles["SectionHeader"]))

        # Create keyword table for ATS optimization
        keyword_data = []
        for i in range(0, len(keywords), 3):
            row = keywords[i : i + 3]
            # Pad row to have 3 columns
            while len(row) < 3:
                row.append("")
            keyword_data.append(row)

        if keyword_data:
            keyword_table = Table(
                keyword_data, colWidths=[2 * inch, 2 * inch, 2 * inch]
            )
            keyword_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )

            elements.append(keyword_table)

        elements.append(Spacer(1, 12))
        return elements

    def generate_ats_compliance_report(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        tailoring_result: TailoredResumeResult,
    ) -> Dict[str, Any]:
        """Generate ATS compliance report for the tailored resume."""

        compliance_score = tailoring_result.ats_optimization_score

        recommendations = []

        if compliance_score < 0.7:
            recommendations.append("Add more keywords from job description")

        if len(tailoring_result.highlighted_skills) < 5:
            recommendations.append(
                "Expand skills section with relevant technical skills"
            )

        if not tailoring_result.tailored_summary:
            recommendations.append("Add a professional summary tailored to the job")

        # Check contact information completeness
        contact_fields = ["email", "phone", "location"]
        missing_contact = [field for field in contact_fields if not profile.get(field)]
        if missing_contact:
            recommendations.append(
                f"Add missing contact information: {', '.join(missing_contact)}"
            )

        return {
            "ats_score": compliance_score,
            "compliance_level": "High"
            if compliance_score > 0.8
            else "Medium"
            if compliance_score > 0.6
            else "Low",
            "keyword_match": len(tailoring_result.added_keywords),
            "skills_highlighted": len(tailoring_result.highlighted_skills),
            "experiences_emphasized": len(tailoring_result.emphasized_experiences),
            "recommendations": recommendations,
            "tailoring_confidence": tailoring_result.tailoring_confidence,
        }


_pdf_generator: ResumePDFGenerator | None = None


def get_pdf_generator() -> ResumePDFGenerator:
    """Get or create the singleton PDF generator."""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = ResumePDFGenerator()
    return _pdf_generator
