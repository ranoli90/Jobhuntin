"""Tests for ATS-specific handlers.

Validates platform detection, CAPTCHA detection, and handler functionality.
"""

from __future__ import annotations

from backend.domain.ats_handlers import (
    ATSDetectionResult,
    ATSPlatform,
    CAPTCHADetection,
    GreenhouseHandler,
    LeverHandler,
    SmartRecruitersHandler,
    WorkdayHandler,
    detect_ats_platform,
    get_handler,
)


class TestDetectATSPlatform:
    """Tests for ATS platform detection."""

    def test_detect_greenhouse_url(self) -> None:
        """Greenhouse URL should be detected."""
        result = detect_ats_platform("https://boards.greenhouse.io/company/jobs/12345")
        assert result.platform == ATSPlatform.GREENHOUSE
        assert result.confidence >= 0.8

    def test_detect_lever_url(self) -> None:
        """Lever URL should be detected."""
        result = detect_ats_platform("https://jobs.lever.co/company/12345-abc")
        assert result.platform == ATSPlatform.LEVER
        assert result.confidence >= 0.8

    def test_detect_workday_url(self) -> None:
        """Workday URL should be detected."""
        result = detect_ats_platform("https://wd5.myworkdayjobs.com/company/job/12345")
        assert result.platform == ATSPlatform.WORKDAY
        assert result.confidence >= 0.8

    def test_detect_smartrecruiters_url(self) -> None:
        """SmartRecruiters URL should be detected."""
        result = detect_ats_platform("https://jobs.smartrecruiters.com/company/12345")
        assert result.platform == ATSPlatform.SMARTRECRUITERS

    def test_detect_unknown_platform(self) -> None:
        """Unknown URLs should return UNKNOWN platform."""
        result = detect_ats_platform("https://company.com/careers/job/12345")
        assert result.platform == ATSPlatform.UNKNOWN
        assert result.confidence == 0.0

    def test_detect_with_content_greenhouse(self) -> None:
        """Greenhouse content patterns should be detected."""
        result = detect_ats_platform(
            "https://jobs.example.com/apply",
            page_content='<div id="grnhse_app">Application Form</div>',
        )
        assert result.platform == ATSPlatform.GREENHOUSE
        assert result.confidence >= 0.6

    def test_detect_with_content_lever(self) -> None:
        """Lever content patterns should be detected."""
        result = detect_ats_platform(
            "https://careers.example.com/apply",
            page_content='<div class="lever-application">Apply</div>',
        )
        assert result.platform == ATSPlatform.LEVER

    def test_detect_with_content_workday(self) -> None:
        """Workday content patterns should be detected."""
        result = detect_ats_platform(
            "https://careers.example.com/apply",
            page_content='<button data-automation-id="submit">Submit</button>',
        )
        assert result.platform == ATSPlatform.WORKDAY

    def test_content_boosts_confidence(self) -> None:
        """Matching content should boost confidence."""
        url = "https://boards.greenhouse.io/company/jobs/123"
        result_url_only = detect_ats_platform(url)
        result_with_content = detect_ats_platform(
            url, page_content='<div id="grnhse_app">Form</div>'
        )
        assert result_with_content.confidence > result_url_only.confidence


class TestATSHandlers:
    """Tests for ATS-specific handlers."""

    def test_get_greenhouse_handler(self) -> None:
        """Should get GreenhouseHandler for Greenhouse platform."""
        handler = get_handler(ATSPlatform.GREENHOUSE)
        assert isinstance(handler, GreenhouseHandler)
        assert handler.platform == ATSPlatform.GREENHOUSE

    def test_get_lever_handler(self) -> None:
        """Should get LeverHandler for Lever platform."""
        handler = get_handler(ATSPlatform.LEVER)
        assert isinstance(handler, LeverHandler)
        assert handler.platform == ATSPlatform.LEVER

    def test_get_workday_handler(self) -> None:
        """Should get WorkdayHandler for Workday platform."""
        handler = get_handler(ATSPlatform.WORKDAY)
        assert isinstance(handler, WorkdayHandler)
        assert handler.platform == ATSPlatform.WORKDAY

    def test_get_smartrecruiters_handler(self) -> None:
        """Should get SmartRecruitersHandler for SmartRecruiters platform."""
        handler = get_handler(ATSPlatform.SMARTRECRUITERS)
        assert isinstance(handler, SmartRecruitersHandler)
        assert handler.platform == ATSPlatform.SMARTRECRUITERS

    def test_get_unknown_handler(self) -> None:
        """Should return None for unknown platform."""
        handler = get_handler(ATSPlatform.UNKNOWN)
        assert handler is None

    def test_greenhouse_selectors(self) -> None:
        """GreenhouseHandler should have custom selectors."""
        handler = GreenhouseHandler()
        selectors = handler.get_custom_selectors()
        assert "submit" in selectors
        assert len(selectors["submit"]) > 0
        assert "next" in selectors

    def test_lever_selectors(self) -> None:
        """LeverHandler should have custom selectors."""
        handler = LeverHandler()
        selectors = handler.get_custom_selectors()
        assert "submit" in selectors
        assert "resume" in selectors

    def test_workday_selectors(self) -> None:
        """WorkdayHandler should have custom selectors."""
        handler = WorkdayHandler()
        selectors = handler.get_custom_selectors()
        assert "submit" in selectors
        assert "country_select" in selectors

    def test_greenhouse_skip_selectors(self) -> None:
        """GreenhouseHandler should have skip selectors."""
        handler = GreenhouseHandler()
        skip = handler.get_skip_selectors()
        assert len(skip) > 0

    def test_workday_skip_selectors(self) -> None:
        """WorkdayHandler should have skip selectors."""
        handler = WorkdayHandler()
        skip = handler.get_skip_selectors()
        assert len(skip) > 0


class TestCAPTCHADetection:
    """Tests for CAPTCHA detection data structures."""

    def test_captcha_detection_defaults(self) -> None:
        """CAPTCHADetection should have sensible defaults."""
        detection = CAPTCHADetection(detected=False)
        assert detection.detected is False
        assert detection.captcha_type is None
        assert detection.selectors == []
        assert detection.indicators == []

    def test_captcha_detection_with_data(self) -> None:
        """CAPTCHADetection should store detection data."""
        detection = CAPTCHADetection(
            detected=True,
            captcha_type="recaptcha",
            selectors=[".g-recaptcha"],
            indicators=["Selector found: .g-recaptcha"],
        )
        assert detection.detected is True
        assert detection.captcha_type == "recaptcha"
        assert len(detection.selectors) == 1


class TestATSDetectionResult:
    """Tests for ATS detection result data structures."""

    def test_detection_result_defaults(self) -> None:
        """ATSDetectionResult should have sensible defaults."""
        result = ATSDetectionResult(
            platform=ATSPlatform.UNKNOWN,
            confidence=0.0,
        )
        assert result.platform == ATSPlatform.UNKNOWN
        assert result.confidence == 0.0
        assert result.indicators == []
        assert result.detected_url_patterns == []

    def test_detection_result_with_data(self) -> None:
        """ATSDetectionResult should store detection data."""
        result = ATSDetectionResult(
            platform=ATSPlatform.GREENHOUSE,
            confidence=0.9,
            indicators=["URL pattern: greenhouse.io"],
            detected_url_patterns=[r"greenhouse\.io"],
        )
        assert result.platform == ATSPlatform.GREENHOUSE
        assert result.confidence == 0.9
        assert len(result.indicators) == 1


class TestATSPlatformEnum:
    """Tests for ATSPlatform enum."""

    def test_platform_values(self) -> None:
        """All expected platforms should be defined."""
        platforms = [
            ATSPlatform.GREENHOUSE,
            ATSPlatform.LEVER,
            ATSPlatform.WORKDAY,
            ATSPlatform.SMARTRECRUITERS,
            ATSPlatform.ICIMS,
            ATSPlatform.TALENTSOFT,
            ATSPlatform.BRASSRING,
            ATSPlatform.UNKNOWN,
        ]
        for platform in platforms:
            assert platform.value is not None

    def test_platform_equality(self) -> None:
        """Platforms should compare correctly."""
        assert ATSPlatform.GREENHOUSE == ATSPlatform.GREENHOUSE
        assert ATSPlatform.GREENHOUSE != ATSPlatform.LEVER
