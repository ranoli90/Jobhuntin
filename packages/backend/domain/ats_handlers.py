"""
ATS-specific handlers for common application platforms.

Provides specialized form filling and navigation logic for:
- Greenhouse (greenhouse.io)
- Lever (lever.co)
- Workday (myworkdayjobs.com)
- SmartRecruiters
- iCIMS

Each handler implements platform-specific:
- URL detection patterns
- Form field selectors
- Multi-step navigation
- CAPTCHA detection indicators
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from playwright.async_api import Page


class ATSPlatform(Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    SMARTRECRUITERS = "smartrecruiters"
    ICIMS = "icims"
    TALENTSOFT = "talentsoft"
    BRASSRING = "brassring"
    UNKNOWN = "unknown"


@dataclass
class ATSDetectionResult:
    """Result of ATS platform detection."""

    platform: ATSPlatform
    confidence: float
    indicators: list[str] = field(default_factory=list)
    detected_url_patterns: list[str] = field(default_factory=list)


@dataclass
class CAPTCHADetection:
    """Result of CAPTCHA detection."""

    detected: bool
    captcha_type: str | None = None
    selectors: list[str] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)


# URL patterns for each ATS platform
ATS_URL_PATTERNS: dict[ATSPlatform, list[str]] = {
    ATSPlatform.GREENHOUSE: [
        r"greenhouse\.io",
        r"job-boards\.greenhouse\.io",
        r"boards\.greenhouse\.io",
        r"/jobs/.*greenhouse",
    ],
    ATSPlatform.LEVER: [
        r"lever\.co",
        r"jobs\.lever\.co",
        r"/apply/.*lever",
    ],
    ATSPlatform.WORKDAY: [
        r"myworkdayjobs\.com",
        r"workday\.com",
        r"wd\d+\.myworkdayjobs\.com",
        r"/job/.*wd\d+",
    ],
    ATSPlatform.SMARTRECRUITERS: [
        r"smartrecruiters\.com",
        r"jobs\.smartrecruiters\.com",
    ],
    ATSPlatform.ICIMS: [
        r"icims\.com",
        r"\.icims\.com",
        r"jobs\?i=icims",
    ],
    ATSPlatform.TALENTSOFT: [
        r"talentsoft\.com",
        r"\.talentsoft\.com",
    ],
    ATSPlatform.BRASSRING: [
        r"brassring\.com",
        r"\.brassring\.com",
        r"tm\.brassring\.com",
    ],
}

# Page content patterns for ATS detection
ATS_CONTENT_PATTERNS: dict[ATSPlatform, list[str]] = {
    ATSPlatform.GREENHOUSE: [
        'id="grnhse_app"',
        'class="greenhouse"',
        "data-greenhouse",
        "application/x-greenhouse",
        "/assets/greenhouse-",
    ],
    ATSPlatform.LEVER: [
        'class="lever',
        "data-lever",
        "window.lever",
        "/assets/lever-",
        "lever-apply",
    ],
    ATSPlatform.WORKDAY: [
        "data-automation-id",
        "wd-Button",
        "workday-",
        "gnewton",
        "css-workday",
    ],
    ATSPlatform.SMARTRECRUITERS: [
        "smartrecruiters",
        "sr-apply",
        "data-sr",
    ],
    ATSPlatform.ICIMS: [
        "icims-",
        "iCIMS",
        "data-icims",
    ],
}

# CAPTCHA detection selectors
CAPTCHA_SELECTORS = {
    "recaptcha": [
        'iframe[src*="recaptcha"]',
        ".g-recaptcha",
        "#g-recaptcha",
        "div.g-recaptcha",
        "[data-sitekey]",
    ],
    "hcaptcha": [
        'iframe[src*="hcaptcha"]',
        ".h-captcha",
        "#h-captcha",
        "div.h-captcha",
    ],
    "cloudflare": [
        "#cf-wrapper",
        ".cf-browser-verification",
        "challenge-platform",
        "cf-turnstile",
    ],
    "turnstile": [
        'iframe[src*="challenges.cloudflare.com"]',
        ".cf-turnstile",
        "[data-turnstile]",
    ],
    "arkose": [
        'iframe[src*="arkose"]',
        "#arkose",
        ".arkose-labs",
    ],
    "friendly_captcha": [
        'iframe[src*="friendlycaptcha"]',
        ".frc-captcha",
        "#frc-captcha",
    ],
}

# CAPTCHA content indicators
CAPTCHA_CONTENT_INDICATORS = [
    "verify you're a human",
    "verify that you are not a robot",
    "i'm not a robot",
    "prove you're human",
    "captcha",
    "security check",
    "complete the puzzle",
    "select all images",
]


def detect_ats_platform(
    url: str, page_content: str | None = None
) -> ATSDetectionResult:
    """
    Detect the ATS platform from URL and optional page content.

    Args:
        url: The application URL
        page_content: Optional HTML content for deeper detection

    Returns:
        ATSDetectionResult with platform and confidence
    """
    url_lower = url.lower()
    detected_platform = ATSPlatform.UNKNOWN
    confidence = 0.0
    indicators: list[str] = []
    detected_patterns: list[str] = []

    for platform, patterns in ATS_URL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower, re.IGNORECASE):
                detected_platform = platform
                confidence = 0.8
                detected_patterns.append(pattern)
                indicators.append(f"URL pattern: {pattern}")
                break
        if detected_platform != ATSPlatform.UNKNOWN:
            break

    if page_content and confidence < 1.0:
        content_lower = page_content.lower()
        for platform, patterns in ATS_CONTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in content_lower:
                    if detected_platform == platform:
                        confidence = min(1.0, confidence + 0.2)
                    elif detected_platform == ATSPlatform.UNKNOWN:
                        detected_platform = platform
                        confidence = 0.6
                    indicators.append(f"Content pattern: {pattern}")

    return ATSDetectionResult(
        platform=detected_platform,
        confidence=confidence,
        indicators=indicators,
        detected_url_patterns=detected_patterns,
    )


async def detect_captcha(page: Page) -> CAPTCHADetection:
    """
    Detect CAPTCHA on a page using multiple methods.

    Args:
        page: Playwright page object

    Returns:
        CAPTCHADetection with details
    """
    indicators: list[str] = []
    detected_selectors: list[str] = []
    detected_type: str | None = None

    for captcha_type, selectors in CAPTCHA_SELECTORS.items():
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    detected_type = captcha_type
                    detected_selectors.append(selector)
                    indicators.append(f"Selector found: {selector}")
            except Exception:
                pass

    if not detected_type:
        try:
            page_content = await page.content()
            content_lower = page_content.lower()
            for indicator in CAPTCHA_CONTENT_INDICATORS:
                if indicator.lower() in content_lower:
                    indicators.append(f"Content indicator: {indicator}")
                    if not detected_type:
                        detected_type = "unknown"
        except Exception:
            pass

    return CAPTCHADetection(
        detected=len(detected_selectors) > 0 or len(indicators) > 0,
        captcha_type=detected_type,
        selectors=detected_selectors,
        indicators=indicators,
    )


class ATSSpecificHandler:
    """Base class for ATS-specific handlers."""

    platform: ATSPlatform = ATSPlatform.UNKNOWN

    async def pre_fill_hook(self, page: Page, ctx: dict) -> None:
        """Called before form filling. Override in subclasses."""
        pass

    async def post_fill_hook(self, page: Page, ctx: dict) -> None:
        """Called after form filling. Override in subclasses."""
        pass

    async def pre_submit_hook(self, page: Page, ctx: dict) -> None:
        """Called before submission. Override in subclasses."""
        pass

    def get_custom_selectors(self) -> dict[str, list[str]]:
        """Return platform-specific selectors. Override in subclasses."""
        return {}

    def get_skip_selectors(self) -> list[str]:
        """Return selectors for fields to skip. Override in subclasses."""
        return []


class GreenhouseHandler(ATSSpecificHandler):
    """Handler for Greenhouse application forms."""

    platform = ATSPlatform.GREENHOUSE

    def get_custom_selectors(self) -> dict[str, list[str]]:
        return {
            "submit": [
                'button[id*="submit_app"]',
                'input[type="submit"][value*="Submit"]',
                'button:has-text("Submit Application")',
                "#submit_app",
            ],
            "next": [
                'button:has-text("Next")',
                'a:has-text("Next")',
                ".button.next",
            ],
            "cover_letter": [
                'input[name*="cover_letter"]',
                'textarea[name*="cover_letter"]',
            ],
        }

    async def pre_fill_hook(self, page: Page, ctx: dict) -> None:
        try:
            await page.wait_for_selector("#grnhse_app", timeout=5000)
        except Exception:
            pass

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[name*="referral"]',
            'input[name*="source"]',
        ]


class LeverHandler(ATSSpecificHandler):
    """Handler for Lever application forms."""

    platform = ATSPlatform.LEVER

    def get_custom_selectors(self) -> dict[str, list[str]]:
        return {
            "submit": [
                'button[data-testid="submit-button"]',
                'button:has-text("Submit application")',
                ".lever-submit",
            ],
            "next": [
                'button:has-text("Continue")',
                'a:has-text("Next")',
            ],
            "resume": [
                'input[type="file"][name*="resume"]',
                'input[accept*=".pdf"]',
            ],
        }

    async def pre_fill_hook(self, page: Page, ctx: dict) -> None:
        try:
            await page.click('button:has-text("Apply")', timeout=3000)
        except Exception:
            pass


class WorkdayHandler(ATSSpecificHandler):
    """Handler for Workday application forms."""

    platform = ATSPlatform.WORKDAY

    def get_custom_selectors(self) -> dict[str, list[str]]:
        return {
            "submit": [
                'button[data-automation-id="bottom-apply"]',
                'button[data-automation-id="submit"]',
                'button:has-text("Submit")',
            ],
            "next": [
                'button[data-automation-id="bottom-next"]',
                'button:has-text("Next")',
            ],
            "country_select": [
                'select[data-automation-id*="country"]',
            ],
        }

    def get_skip_selectors(self) -> list[str]:
        return [
            'input[data-automation-id*="agency"]',
            'input[data-automation-id*="source"]',
        ]

    async def pre_fill_hook(self, page: Page, ctx: dict) -> None:
        try:
            apply_button = await page.query_selector(
                'button[data-automation-id="bottom-apply"]'
            )
            if apply_button:
                await apply_button.click()
                await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass


class SmartRecruitersHandler(ATSSpecificHandler):
    """Handler for SmartRecruiters application forms."""

    platform = ATSPlatform.SMARTRECRUITERS

    def get_custom_selectors(self) -> dict[str, list[str]]:
        return {
            "submit": [
                'button[type="submit"]',
                'button:has-text("Send")',
                ".sr-submit",
            ],
            "next": [
                'button:has-text("Next")',
                'button:has-text("Continue")',
            ],
        }


# Handler registry
ATS_HANDLERS: dict[ATSPlatform, type[ATSSpecificHandler]] = {
    ATSPlatform.GREENHOUSE: GreenhouseHandler,
    ATSPlatform.LEVER: LeverHandler,
    ATSPlatform.WORKDAY: WorkdayHandler,
    ATSPlatform.SMARTRECRUITERS: SmartRecruitersHandler,
}


def get_handler(platform: ATSPlatform) -> ATSSpecificHandler | None:
    """Get the appropriate handler for an ATS platform."""
    handler_class = ATS_HANDLERS.get(platform)
    if handler_class:
        return handler_class()
    return None
