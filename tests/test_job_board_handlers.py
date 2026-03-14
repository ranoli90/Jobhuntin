"""Tests for job board application handlers.

Validates job board platform detection, login handling, and form automation.
"""

from __future__ import annotations

from packages.backend.domain.job_board_handlers import (
    GlassdoorHandler,
    IndeedHandler,
    JobBoardDetectionResult,
    JobBoardPlatform,
    LinkedInHandler,
    ZipRecruiterHandler,
    detect_job_board_platform,
    get_job_board_handler,
)


class TestDetectJobBoardPlatform:
    """Tests for job board platform detection."""

    def test_detect_indeed_url(self) -> None:
        """Indeed URL should be detected."""
        result = detect_job_board_platform("https://www.indeed.com/rc/clk?jk=12345")
        assert result.platform == JobBoardPlatform.INDEED
        assert result.confidence >= 0.8
        assert result.requires_login == False

    def test_detect_linkedin_url(self) -> None:
        """LinkedIn URL should be detected."""
        result = detect_job_board_platform("https://www.linkedin.com/jobs/view/12345")
        assert result.platform == JobBoardPlatform.LINKEDIN
        assert result.confidence >= 0.8
        assert result.requires_login == True

    def test_detect_ziprecruiter_url(self) -> None:
        """ZipRecruiter URL should be detected."""
        result = detect_job_board_platform("https://www.ziprecruiter.com/jobs/12345")
        assert result.platform == JobBoardPlatform.ZIP_RECRUITER
        assert result.confidence >= 0.8
        assert result.requires_login == True

    def test_detect_glassdoor_url(self) -> None:
        """Glassdoor URL should be detected."""
        result = detect_job_board_platform("https://www.glassdoor.com/job-listing/12345")
        assert result.platform == JobBoardPlatform.GLASSDOOR
        assert result.confidence >= 0.8
        assert result.requires_login == False

    def test_detect_unknown_platform(self) -> None:
        """Unknown URLs should return UNKNOWN platform."""
        result = detect_job_board_platform("https://company.com/careers/job/12345")
        assert result.platform == JobBoardPlatform.UNKNOWN
        assert result.confidence == 0.0
        assert result.requires_login == False

    def test_detect_with_content_indeed(self) -> None:
        """Indeed content patterns should be detected."""
        result = detect_job_board_platform(
            "https://jobs.example.com/apply",
            page_content='<div id="jobsearch">Job Search</div>',
        )
        assert result.platform == JobBoardPlatform.INDEED
        assert result.confidence >= 0.6

    def test_detect_with_content_linkedin(self) -> None:
        """LinkedIn content patterns should be detected."""
        result = detect_job_board_platform(
            "https://careers.example.com/apply",
            page_content='<div class="jobs-search">LinkedIn Jobs</div>',
        )
        assert result.platform == JobBoardPlatform.LINKEDIN
        assert result.confidence >= 0.6

    def test_content_boosts_confidence(self) -> None:
        """Matching content should boost confidence."""
        url = "https://www.indeed.com/jobs/123"
        result_url_only = detect_job_board_platform(url)
        result_with_content = detect_job_board_platform(
            url, page_content='<div id="jobsearch">Indeed Job Search</div>'
        )
        assert result_with_content.confidence > result_url_only.confidence


class TestJobBoardHandlers:
    """Tests for job board application handlers."""

    def test_get_indeed_handler(self) -> None:
        """Should get IndeedHandler for Indeed platform."""
        handler = get_job_board_handler(JobBoardPlatform.INDEED)
        assert isinstance(handler, IndeedHandler)
        assert handler.platform == JobBoardPlatform.INDEED

    def test_get_linkedin_handler(self) -> None:
        """Should get LinkedInHandler for LinkedIn platform."""
        handler = get_job_board_handler(JobBoardPlatform.LINKEDIN)
        assert isinstance(handler, LinkedInHandler)
        assert handler.platform == JobBoardPlatform.LINKEDIN

    def test_get_ziprecruiter_handler(self) -> None:
        """Should get ZipRecruiterHandler for ZipRecruiter platform."""
        handler = get_job_board_handler(JobBoardPlatform.ZIP_RECRUITER)
        assert isinstance(handler, ZipRecruiterHandler)
        assert handler.platform == JobBoardPlatform.ZIP_RECRUITER

    def test_get_glassdoor_handler(self) -> None:
        """Should get GlassdoorHandler for Glassdoor platform."""
        handler = get_job_board_handler(JobBoardPlatform.GLASSDOOR)
        assert isinstance(handler, GlassdoorHandler)
        assert handler.platform == JobBoardPlatform.GLASSDOOR

    def test_get_unknown_handler(self) -> None:
        """Should return None for unknown platform."""
        handler = get_job_board_handler(JobBoardPlatform.UNKNOWN)
        assert handler is None

    def test_indeed_selectors(self) -> None:
        """IndeedHandler should have application selectors."""
        handler = IndeedHandler()
        selectors = handler.get_application_selectors()
        assert "apply_button" in selectors
        assert "continue_button" in selectors
        assert "resume_upload" in selectors

    def test_linkedin_selectors(self) -> None:
        """LinkedInHandler should have application selectors."""
        handler = LinkedInHandler()
        selectors = handler.get_application_selectors()
        assert "easy_apply_button" in selectors
        assert "continue_button" in selectors
        assert "submit_button" in selectors

    def test_ziprecruiter_selectors(self) -> None:
        """ZipRecruiterHandler should have application selectors."""
        handler = ZipRecruiterHandler()
        selectors = handler.get_application_selectors()
        assert "apply_button" in selectors
        assert "continue_button" in selectors
        assert "submit_button" in selectors

    def test_indeed_skip_selectors(self) -> None:
        """IndeedHandler should have skip selectors."""
        handler = IndeedHandler()
        skip = handler.get_skip_selectors()
        assert len(skip) > 0

    def test_linkedin_skip_selectors(self) -> None:
        """LinkedInHandler should have skip selectors."""
        handler = LinkedInHandler()
        skip = handler.get_skip_selectors()
        assert len(skip) > 0


class TestJobBoardDetectionResult:
    """Tests for job board detection result data structures."""

    def test_detection_result_defaults(self) -> None:
        """JobBoardDetectionResult should have sensible defaults."""
        result = JobBoardDetectionResult(
            platform=JobBoardPlatform.UNKNOWN,
            confidence=0.0,
        )
        assert result.platform == JobBoardPlatform.UNKNOWN
        assert result.confidence == 0.0
        assert result.indicators == []
        assert result.detected_url_patterns == []
        assert result.requires_login == False

    def test_detection_result_with_data(self) -> None:
        """JobBoardDetectionResult should store detection data."""
        result = JobBoardDetectionResult(
            platform=JobBoardPlatform.INDEED,
            confidence=0.9,
            indicators=["URL pattern: indeed.com"],
            detected_url_patterns=[r"indeed\.com"],
            requires_login=False,
        )
        assert result.platform == JobBoardPlatform.INDEED
        assert result.confidence == 0.9
        assert len(result.indicators) == 1
        assert result.requires_login == False


class TestJobBoardPlatformEnum:
    """Tests for JobBoardPlatform enum."""

    def test_platform_values(self) -> None:
        """All expected platforms should be defined."""
        platforms = [
            JobBoardPlatform.INDEED,
            JobBoardPlatform.LINKEDIN,
            JobBoardPlatform.ZIP_RECRUITER,
            JobBoardPlatform.GLASSDOOR,
            JobBoardPlatform.UNKNOWN,
        ]
        for platform in platforms:
            assert platform.value is not None

    def test_platform_equality(self) -> None:
        """Platforms should compare correctly."""
        assert JobBoardPlatform.INDEED == JobBoardPlatform.INDEED
        assert JobBoardPlatform.INDEED != JobBoardPlatform.LINKEDIN

    def test_login_requirements(self) -> None:
        """Login requirements should be correctly set."""
        # Test login requirements based on platform detection results
        linkedin_result = detect_job_board_platform("https://www.linkedin.com/jobs/12345")
        assert linkedin_result.requires_login == True

        ziprecruiter_result = detect_job_board_platform("https://www.ziprecruiter.com/jobs/12345")
        assert ziprecruiter_result.requires_login == True

        indeed_result = detect_job_board_platform("https://www.indeed.com/rc/clk?jk=12345")
        assert indeed_result.requires_login == False

        glassdoor_result = detect_job_board_platform("https://www.glassdoor.com/job-listing/12345")
        assert glassdoor_result.requires_login == False
