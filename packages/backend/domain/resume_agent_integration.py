"""Integration service for connecting tailored resumes with the application agent.

This service bridges the gap between the resume tailoring system and the
Playwright-based application agent, enabling:

1. Automatic resume tailoring before application submission
2. ATS optimization integration
3. Template selection based on job requirements
4. Resume PDF generation and storage
5. Application agent resume file updates
6. Analytics and performance tracking

Key features:
- Seamless integration between tailoring and application systems
- Automatic PDF generation for applications
- ATS score optimization
- Template recommendation engine
- Resume file management
- Application success tracking
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.domain.resume_pdf_generator import get_pdf_generator
from backend.domain.resume_tailoring import get_tailoring_service
from shared.logging_config import get_logger

logger = get_logger("sorce.resume_agent_integration")


class ResumeAgentIntegration:
    """Integration service for connecting tailored resumes with the application agent.

    This service acts as a bridge between the resume tailoring system and
    the Playwright-based application agent, ensuring that applications are
    submitted with optimized, job-specific resumes.
    """

    def __init__(self):
        self._pdf_generator = get_pdf_generator()
        self._tailoring_service = get_tailoring_service()

    async def prepare_resume_for_application(
        self,
        user_id: str,
        job_id: str,
        application_id: str,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        template_style: Optional[str] = None,
        force_tailoring: bool = False,
    ) -> Dict[str, Any]:
        """Prepare a tailored resume for job application.

        This method:
        1. Analyzes job requirements
        2. Determines optimal template style
        3. Generates tailored resume content
        4. Creates ATS-optimized PDF
        5. Stores PDF for application agent
        6. Returns integration metadata

        Args:
            user_id: User identifier
            job_id: Job identifier
            application_id: Application identifier
            profile: User profile data
            job: Job posting data
            template_style: Optional template override
            force_tailoring: Force retailoring even if cached

        Returns:
            Integration metadata with PDF information
        """
        try:
            # Step 1: Determine optimal template if not provided
            if not template_style:
                template_style = await self._recommend_template(job, profile)

            # Step 2: Tailor resume content
            tailoring_result = await self._tailoring_service.tailor_resume(
                profile=profile,
                job=job,
            )

            # Step 3: Generate ATS-optimized PDF
            pdf_bytes = await self._pdf_generator.generate_tailored_resume_pdf(
                profile=profile,
                job=job,
                tailoring_result=tailoring_result,
                template_style=template_style,
            )

            # Step 4: Store PDF for application
            pdf_metadata = await self._store_resume_pdf(
                user_id=user_id,
                job_id=job_id,
                application_id=application_id,
                profile=profile,
                job=job,
                tailoring_result=tailoring_result,
                pdf_bytes=pdf_bytes,
                template_style=template_style,
            )

            # Step 5: Update application with resume info
            await self._update_application_resume(
                application_id=application_id,
                pdf_metadata=pdf_metadata,
                tailoring_result=tailoring_result,
            )

            # Step 6: Record analytics
            await self._record_integration_analytics(
                user_id=user_id,
                job_id=job_id,
                application_id=application_id,
                template_style=template_style,
                tailoring_result=tailoring_result,
                pdf_metadata=pdf_metadata,
            )

            logger.info(
                f"Resume prepared for application {application_id}: "
                f"template={template_style}, ats_score={tailoring_result.ats_optimization_score:.2f}"
            )

            return {
                "success": True,
                "application_id": application_id,
                "template_style": template_style,
                "ats_score": tailoring_result.ats_optimization_score,
                "tailoring_confidence": tailoring_result.tailoring_confidence,
                "pdf_id": pdf_metadata["id"],
                "file_size": pdf_metadata["file_size"],
                "highlighted_skills": tailoring_result.highlighted_skills,
                "emphasized_experiences": tailoring_result.emphasized_experiences,
                "added_keywords": tailoring_result.added_keywords,
            }

        except Exception as e:
            logger.error(
                f"Failed to prepare resume for application {application_id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "application_id": application_id,
            }

    async def _recommend_template(
        self,
        job: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> str:
        """Recommend the optimal template style based on job and profile.

        Args:
            job: Job posting data
            profile: User profile data

        Returns:
            Recommended template style
        """
        job_title = job.get("title", "").lower()
        job_description = job.get("description", "").lower()
        company_industry = job.get("company_industry", "").lower()

        # Template selection logic
        if any(
            keyword in job_title
            for keyword in ["executive", "director", "vp", "manager", "lead"]
        ):
            return "executive"
        elif any(
            keyword in job_title
            for keyword in ["engineer", "developer", "technical", "software"]
        ):
            return "technical"
        elif any(
            keyword in job_title
            for keyword in ["designer", "creative", "artist", "writer"]
        ):
            return "creative"
        elif any(keyword in job_title for keyword in ["senior", "principal", "staff"]):
            return "executive"
        elif any(
            keyword in job_title
            for keyword in ["junior", "entry", "intern", "associate"]
        ):
            return "professional"
        else:
            return "professional"  # Default

    async def _store_resume_pdf(
        self,
        user_id: str,
        job_id: str,
        application_id: str,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        tailoring_result: Any,
        pdf_bytes: bytes,
        template_style: str,
    ) -> Dict[str, Any]:
        """Store the generated PDF for the application.

        Args:
            user_id: User identifier
            job_id: Job identifier
            application_id: Application identifier
            profile: User profile data
            job: Job posting data
            tailoring_result: Resume tailoring results
            pdf_bytes: Generated PDF bytes
            template_style: Template style used

        Returns:
            PDF metadata
        """
        # TODO: Implement actual storage in database
        # For now, return placeholder metadata

        pdf_metadata = {
            "id": f"pdf_{application_id}",
            "application_id": application_id,
            "user_id": user_id,
            "job_id": job_id,
            "template_style": template_style,
            "file_size": len(pdf_bytes),
            "ats_score": tailoring_result.ats_optimization_score,
            "tailoring_confidence": tailoring_result.tailoring_confidence,
            "highlighted_skills": tailoring_result.highlighted_skills,
            "emphasized_experiences": tailoring_result.emphasized_experiences,
            "added_keywords": tailoring_result.added_keywords,
            "original_summary": tailoring_result.original_summary,
            "tailored_summary": tailoring_result.tailored_summary,
            "created_at": "2024-01-01T00:00:00Z",  # Placeholder
            "storage_url": f"/resume-pdf/download/{application_id}",
        }

        return pdf_metadata

    async def _update_application_resume(
        self,
        application_id: str,
        pdf_metadata: Dict[str, Any],
        tailoring_result: Any,
    ) -> None:
        """Update application record with resume information.

        Args:
            application_id: Application identifier
            pdf_metadata: PDF storage metadata
            tailoring_result: Resume tailoring results
        """
        # TODO: Implement actual database update
        # This would update the applications table with resume PDF info
        logger.info(f"Would update application {application_id} with resume info")

    async def _record_integration_analytics(
        self,
        user_id: str,
        job_id: str,
        application_id: str,
        template_style: str,
        tailoring_result: Any,
        pdf_metadata: Dict[str, Any],
    ) -> None:
        """Record analytics for the resume integration.

        Args:
            user_id: User identifier
            job_id: Job identifier
            application_id: Application identifier
            template_style: Template style used
            tailoring_result: Resume tailoring results
            pdf_metadata: PDF storage metadata
        """
        # TODO: Implement actual analytics recording
        # This would store integration metrics for analysis
        logger.info(
            f"Would record analytics for application {application_id}: "
            f"template={template_style}, ats_score={tailoring_result.ats_optimization_score:.2f}"
        )

    async def get_resume_integration_status(
        self,
        application_id: str,
    ) -> Dict[str, Any]:
        """Get the status of resume integration for an application.

        Args:
            application_id: Application identifier

        Returns:
            Integration status information
        """
        # TODO: Implement actual status check
        # This would query the database for integration status

        return {
            "application_id": application_id,
            "resume_prepared": False,
            "template_used": None,
            "ats_score": None,
            "pdf_generated": False,
            "integration_status": "pending",
            "error_message": None,
        }

    async def update_application_agent_resume(
        self,
        application_id: str,
        pdf_path: str,
    ) -> bool:
        """Update the application agent with the new resume file.

        This method ensures that when the Playwright agent processes
        the application, it uses the tailored resume PDF instead of
        the original resume.

        Args:
            application_id: Application identifier
            pdf_path: Path to the tailored PDF

        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO: Implement actual agent resume update
            # This would update the application's resume_url field
            # to point to the tailored PDF

            logger.info(
                f"Would update application agent resume for {application_id}: {pdf_path}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to update application agent resume for {application_id}: {e}"
            )
            return False

    async def batch_prepare_resumes(
        self,
        applications: List[Dict[str, Any]],
        profiles: Dict[str, Dict[str, Any]],
        jobs: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepare resumes for multiple applications in batch.

        Args:
            applications: List of application data
            profiles: Mapping of user_id to profile data
            jobs: Mapping of job_id to job data

        Returns:
            List of preparation results
        """
        results = []

        for app in applications:
            user_id = app.get("user_id")
            job_id = app.get("job_id")
            application_id = app.get("id")

            if not all([user_id, job_id, application_id]):
                results.append(
                    {
                        "application_id": application_id,
                        "success": False,
                        "error": "Missing required fields",
                    }
                )
                continue

            profile = profiles.get(user_id)
            job = jobs.get(job_id)

            if not profile or not job:
                results.append(
                    {
                        "application_id": application_id,
                        "success": False,
                        "error": "Missing profile or job data",
                    }
                )
                continue

            try:
                result = await self.prepare_resume_for_application(
                    user_id=user_id,
                    job_id=job_id,
                    application_id=application_id,
                    profile=profile,
                    job=job,
                )
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to prepare resume for application {application_id}: {e}"
                )
                results.append(
                    {
                        "application_id": application_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    async def get_integration_analytics(
        self,
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        template_style: Optional[str] = None,
        date_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get analytics for resume integration.

        Args:
            user_id: Optional user filter
            job_id: Optional job filter
            template_style: Optional template filter
            date_range: Optional date range filter

        Returns:
            Analytics data
        """
        # TODO: Implement actual analytics query
        # This would aggregate integration metrics

        return {
            "total_integrations": 0,
            "success_rate": 0.0,
            "average_ats_score": 0.0,
            "template_usage": {
                "professional": 0,
                "modern": 0,
                "executive": 0,
                "technical": 0,
                "creative": 0,
            },
            "performance_metrics": {
                "average_generation_time": 0.0,
                "average_file_size": 0,
                "optimization_improvement": 0.0,
            },
        }


# Singleton instance
_integration_service: ResumeAgentIntegration | None = None


def get_resume_agent_integration() -> ResumeAgentIntegration:
    """Get or create the singleton integration service."""
    global _integration_service
    if _integration_service is None:
        _integration_service = ResumeAgentIntegration()
    return _integration_service
