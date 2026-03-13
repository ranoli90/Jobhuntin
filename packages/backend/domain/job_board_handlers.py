"""Job Board Application Handlers.

Provides specialized form filling and navigation logic for:
- Indeed application forms
- LinkedIn Easy Apply
- ZipRecruiter applications
- Glassdoor applications

Each handler implements platform-specific:
- URL detection patterns
- Form field selectors
- Multi-step navigation
- Login requirement handling
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from shared.logging_config import get_logger

logger = get_logger("sorce.job_board_handlers")


class JobBoardPlatform(Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    ZIP_RECRUITER = "zip_recruiter"
    GLASSDOOR = "glassdoor"
    UNKNOWN = "unknown"


@dataclass
class JobBoardDetectionResult:
    """Result of job board platform detection."""

    platform: JobBoardPlatform
    confidence: float
    indicators: list[str] = field(default_factory=list)
    detected_url_patterns: list[str] = field(default_factory=list)
    requires_login: bool = False


# URL patterns for each job board
JOB_BOARD_URL_PATTERNS: dict[JobBoardPlatform, list[str]] = {
    JobBoardPlatform.INDEED: [
        r"indeed\.com",
        r"jobs\.indeed\.com",
        r"/rc/clk\?",  # Indeed job click tracking
        r"/viewjob\?",  # Indeed job view
        r"/company/jobs",
    ],
    JobBoardPlatform.LINKEDIN: [
        r"linkedin\.com",
        r"jobs\.linkedin\.com",
        r"/jobs/view/",
        r"/jobs/collections/",
    ],
    JobBoardPlatform.ZIP_RECRUITER: [
        r"ziprecruiter\.com",
        r"www\.ziprecruiter\.com",
        r"/jobs/",
        r"/jl/",
    ],
    JobBoardPlatform.GLASSDOOR: [
        r"glassdoor\.com",
        r"www\.glassdoor\.com",
        r"/job-listing/",
        r"/partner/",
    ],
}


# Page content patterns for job board detection
JOB_BOARD_CONTENT_PATTERNS: dict[JobBoardPlatform, list[str]] = {
    JobBoardPlatform.INDEED: [
        'id="jobsearch"',
        'class="jobsearch"',
        "data-tn-component",
        "indeed-",
        "jobsearch-",
        "IndeedApplyButton",
        "indeed-apply",
    ],
    JobBoardPlatform.LINKEDIN: [
        'class="jobs-search"',
        "data-ember-job",
        "jobs-search",
        "jobs-apply",
        "jobs-easy-apply",
        "jobs-apply-modal",
    ],
    JobBoardPlatform.ZIP_RECRUITER: [
        'class="ziprecruiter"',
        "data-ziprecruiter",
        "zip-apply",
        "ziprecruiter-apply",
        "job-apply",
    ],
    JobBoardPlatform.GLASSDOOR: [
        'class="glassdoor"',
        "gd-apply",
        "glassdoor-apply",
        "partner-apply",
        "job-apply-button",
    ],
}


def detect_job_board_platform(url: str, page_content: Optional[str] = None) -> JobBoardDetectionResult:
    """Detect which job board platform is being used."""
    url_lower = url.lower()
    detected_platform = JobBoardPlatform.UNKNOWN
    confidence = 0.0
    indicators: list[str] = []
    detected_patterns: list[str] = []

    for platform, patterns in JOB_BOARD_URL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower, re.IGNORECASE):
                detected_platform = platform
                confidence = 0.8
                detected_patterns.append(pattern)
                indicators.append(f"URL pattern: {pattern}")
                break
        if detected_platform != JobBoardPlatform.UNKNOWN:
            break

    if page_content and confidence < 1.0:
        content_lower = page_content.lower()
        for platform, patterns in JOB_BOARD_CONTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in content_lower:
                    if detected_platform == platform:
                        confidence = min(1.0, confidence + 0.2)
                    elif detected_platform == JobBoardPlatform.UNKNOWN:
                        detected_platform = platform
                        confidence = 0.6
                    indicators.append(f"Content pattern: {pattern}")

    # Check if login is required
    requires_login = detected_platform in [JobBoardPlatform.LINKEDIN, JobBoardPlatform.ZIP_RECRUITER]

    return JobBoardDetectionResult(
        platform=detected_platform,
        confidence=confidence,
        indicators=indicators,
        detected_url_patterns=detected_patterns,
        requires_login=requires_login,
    )


class JobBoardHandler:
    """Base class for job board application handlers."""

    platform: JobBoardPlatform = JobBoardPlatform.UNKNOWN

    async def pre_apply_hook(self, page: Page, ctx: dict) -> None:
        """Called before application process. Override in subclasses."""
        pass

    async def post_apply_hook(self, page: Page, ctx: dict) -> None:
        """Called after application process. Override in subclasses."""
        pass

    async def check_login_status(self, page: Page) -> bool:
        """Check if user is logged in. Override in subclasses."""
        return True

    async def handle_login(self, page: Page, credentials: dict) -> bool:
        """Handle login if required. Override in subclasses."""
        return False

    def get_application_selectors(self) -> dict[str, list[str]]:
        """Return platform-specific application selectors. Override in subclasses."""
        return {}

    def get_skip_selectors(self) -> list[str]:
        """Return selectors for fields to skip. Override in subclasses."""
        return []


class IndeedHandler(JobBoardHandler):
    """Handler for Indeed application forms."""

    platform = JobBoardPlatform.INDEED

    def get_application_selectors(self) -> dict[str, list[str]]:
        return {
            "apply_button": [
                'button[data-tn-element="Apply"]',
                'a[data-tn-element="Apply"]',
                'button:has-text("Apply")',
                'a:has-text("Apply Now")',
                '.indeed-apply-button',
                '#apply-now-button',
            ],
            "continue_button": [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button[type="submit"]',
            ],
            "resume_upload": [
                'input[type="file"]',
                'input[name*="resume"]',
                'input[accept*=".pdf"]',
                '.resume-upload-input',
            ],
            "cover_letter": [
                'textarea[name*="cover"]',
                'textarea[name*="letter"]',
                '.cover-letter-textarea',
            ],
            "phone": [
                'input[name*="phone"]',
                'input[type="tel"]',
                'input[name*="mobile"]',
            ],
            "email": [
                'input[name*="email"]',
                'input[type="email"]',
            ],
            "questions": [
                '.job-application-question',
                '.application-question',
                '[data-testid*="question"]',
            ],
        }

    async def pre_apply_hook(self, page: Page, ctx: dict) -> None:
        """Handle Indeed-specific pre-application setup."""
        try:
            # Wait for Indeed job page to load
            await page.wait_for_selector('[data-tn-component]', timeout=5000)
            
            # Check if this is an Indeed Apply job
            indeed_apply = await page.query_selector('.indeed-apply, [data-tn-element="IndeedApply"]')
            if indeed_apply:
                ctx['is_indeed_apply'] = True
                logger.info("Detected Indeed Apply job")
            else:
                ctx['is_indeed_apply'] = False
                
        except Exception as e:
            logger.debug(f"Indeed pre-apply hook error: {e}")

    async def post_apply_hook(self, page: Page, ctx: dict) -> None:
        """Handle Indeed-specific post-application actions."""
        try:
            # Check for application confirmation
            success_message = await page.query_selector(
                '.application-success, .apply-success, [data-testid="apply-success"]'
            )
            if success_message:
                ctx['application_successful'] = True
                logger.info("Indeed application successful")
            else:
                ctx['application_successful'] = False
                
        except Exception as e:
            logger.debug(f"Indeed post-apply hook error: {e}")

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[name*="referral"]',
            'input[name*="source"]',
            'input[name*="diversity"]',
            '.optional-field',
        ]


class LinkedInHandler(JobBoardHandler):
    """Handler for LinkedIn Easy Apply."""

    platform = JobBoardPlatform.LINKEDIN

    def get_application_selectors(self) -> dict[str, list[str]]:
        return {
            "easy_apply_button": [
                'button[aria-label*="Easy Apply"]',
                'button:has-text("Easy Apply")',
                '.jobs-apply-button',
                '[data-ember-action]',
                '.jobs-easy-apply',
            ],
            "continue_button": [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                '.continue-button',
                '.next-button',
            ],
            "submit_button": [
                'button:has-text("Submit application")',
                'button:has-text("Submit")',
                '.submit-application',
                '.apply-submit',
            ],
            "resume_upload": [
                'input[type="file"]',
                'input[name*="resume"]',
                '.resume-upload',
                '[data-test-file-upload]',
            ],
            "cover_letter": [
                'textarea[name*="cover"]',
                'textarea[name*="letter"]',
                '.cover-letter-textarea',
            ],
            "phone": [
                'input[name*="phone"]',
                'input[type="tel"]',
                '.phone-input',
            ],
            "email": [
                'input[name*="email"]',
                'input[type="email"]',
                '.email-input',
            ],
            "questions": [
                '.jobs-easy-apply-form-section',
                '.application-form-question',
                '[data-test-form-element]',
            ],
        }

    async def check_login_status(self, page: Page) -> bool:
        """Check if user is logged into LinkedIn."""
        try:
            # Look for login indicators
            login_button = await page.query_selector('a[href*="/login"], button:has-text("Sign in")')
            if login_button:
                return False
            
            # Look for logged in indicators
            profile_nav = await page.query_selector('.global-nav__primary-link, .nav-item')
            return profile_nav is not None
            
        except Exception:
            return True  # Assume logged in if we can't check

    async def handle_login(self, page: Page, credentials: dict) -> bool:
        """Handle LinkedIn login if required."""
        try:
            # Navigate to login page
            await page.goto('https://www.linkedin.com/login')
            await page.wait_for_selector('#username', timeout=10000)
            
            # Fill login form
            await page.fill('#username', credentials.get('email', ''))
            await page.fill('#password', credentials.get('password', ''))
            
            # Submit login
            await page.click('button[type="submit"]')
            
            # Wait for login completion
            await page.wait_for_selector('.global-nav__primary-link', timeout=10000)
            
            logger.info("LinkedIn login successful")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False

    async def pre_apply_hook(self, page: Page, ctx: dict) -> None:
        """Handle LinkedIn-specific pre-application setup."""
        try:
            # Wait for LinkedIn job page to load
            await page.wait_for_selector('.jobs-top-card', timeout=5000)
            
            # Check if Easy Apply is available
            easy_apply_button = await page.query_selector('button[aria-label*="Easy Apply"]')
            if easy_apply_button:
                ctx['easy_apply_available'] = True
                logger.info("LinkedIn Easy Apply available")
            else:
                ctx['easy_apply_available'] = False
                
        except Exception as e:
            logger.debug(f"LinkedIn pre-apply hook error: {e}")

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[name*="referral"]',
            'input[name*="source"]',
            '.optional-field',
            '[data-optional="true"]',
        ]


class ZipRecruiterHandler(JobBoardHandler):
    """Handler for ZipRecruiter application forms."""

    platform = JobBoardPlatform.ZIP_RECRUITER

    def get_application_selectors(self) -> dict[str, list[str]]:
        return {
            "apply_button": [
                'button:has-text("Apply")',
                'a:has-text("Apply Now")',
                '.apply-button',
                '.zip-apply',
                '#apply-button',
            ],
            "continue_button": [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                '.continue-btn',
            ],
            "submit_button": [
                'button:has-text("Submit Application")',
                'button:has-text("Submit")',
                '.submit-application',
            ],
            "resume_upload": [
                'input[type="file"]',
                'input[name*="resume"]',
                '.resume-upload',
            ],
            "cover_letter": [
                'textarea[name*="cover"]',
                'textarea[name*="letter"]',
                '.cover-letter-textarea',
            ],
            "phone": [
                'input[name*="phone"]',
                'input[type="tel"]',
                '.phone-input',
            ],
            "email": [
                'input[name*="email"]',
                'input[type="email"]',
                '.email-input',
            ],
            "questions": [
                '.application-question',
                '.form-question',
                '[data-testid*="question"]',
            ],
        }

    async def check_login_status(self, page: Page) -> bool:
        """Check if user is logged into ZipRecruiter."""
        try:
            # Look for login indicators
            login_button = await page.query_selector('a[href*="/login"], button:has-text("Sign in")')
            if login_button:
                return False
            
            # Look for logged in indicators
            profile_nav = await page.query_selector('.nav-profile, .user-menu')
            return profile_nav is not None
            
        except Exception:
            return True

    async def handle_login(self, page: Page, credentials: dict) -> bool:
        """Handle ZipRecruiter login if required."""
        try:
            # Navigate to login page
            await page.goto('https://www.ziprecruiter.com/login')
            await page.wait_for_selector('#email', timeout=10000)
            
            # Fill login form
            await page.fill('#email', credentials.get('email', ''))
            await page.fill('#password', credentials.get('password', ''))
            
            # Submit login
            await page.click('button[type="submit"]')
            
            # Wait for login completion
            await page.wait_for_selector('.nav-profile', timeout=10000)
            
            logger.info("ZipRecruiter login successful")
            return True
            
        except Exception as e:
            logger.error(f"ZipRecruiter login failed: {e}")
            return False

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[name*="referral"]',
            'input[name*="source"]',
            '.optional-field',
        ]


class GlassdoorHandler(JobBoardHandler):
    """Handler for Glassdoor application forms."""

    platform = JobBoardPlatform.GLASSDOOR

    def get_application_selectors(self) -> dict[str, list[str]]:
        return {
            "apply_button": [
                'button:has-text("Apply")',
                'a:has-text("Apply Now")',
                '.apply-button',
                '.gd-apply',
                '#apply-button',
            ],
            "continue_button": [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                '.continue-btn',
            ],
            "submit_button": [
                'button:has-text("Submit Application")',
                'button:has-text("Submit")',
                '.submit-application',
            ],
            "resume_upload": [
                'input[type="file"]',
                'input[name*="resume"]',
                '.resume-upload',
            ],
            "cover_letter": [
                'textarea[name*="cover"]',
                'textarea[name*="letter"]',
                '.cover-letter-textarea',
            ],
            "phone": [
                'input[name*="phone"]',
                'input[type="tel"]',
                '.phone-input',
            ],
            "email": [
                'input[name*="email"]',
                'input[type="email"]',
                '.email-input',
            ],
            "questions": [
                '.application-question',
                '.form-question',
                '[data-testid*="question"]',
            ],
        }

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[name*="referral"]',
            'input[name*="source"]',
            '.optional-field',
        ]


# Handler registry
JOB_BOARD_HANDLERS: dict[JobBoardPlatform, type[JobBoardHandler]] = {
    JobBoardPlatform.INDEED: IndeedHandler,
    JobBoardPlatform.LINKEDIN: LinkedInHandler,
    JobBoardPlatform.ZIP_RECRUITER: ZipRecruiterHandler,
    JobBoardPlatform.GLASSDOOR: GlassdoorHandler,
}


def get_job_board_handler(platform: JobBoardPlatform) -> JobBoardHandler | None:
    """Get the appropriate handler for a job board platform."""
    handler_class = JOB_BOARD_HANDLERS.get(platform)
    if handler_class:
        return handler_class()
    return None
