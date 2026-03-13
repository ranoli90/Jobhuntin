"""CAPTCHA Detection and Solving for Job Application Automation.

Handles detection of CAPTCHAs during job application automation and provides
solving capabilities through various services (2Captcha, Anti-Captcha, ML-based).
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict, Optional

import httpx
from playwright.async_api import Page

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.captcha_handler")

# Import ML solver
try:
    from .ml_captcha_solver import MLCaptchaSolver, EnhancedCaptchaDetector
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML CAPTCHA solver not available - using external services only")


class CaptchaType:
    """CAPTCHA type constants."""

    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    IMAGE_CAPTCHA = "image_captcha"
    TEXT_CAPTCHA = "text_captcha"
    MATH_CAPTCHA = "math_captcha"
    FUNCAPTCHA = "funcaptcha"


class CaptchaDetector:
    """Detects various types of CAPTCHAs on web pages."""

    def __init__(self):
        # Use enhanced detector if available
        if ML_AVAILABLE:
            self.enhanced_detector = EnhancedCaptchaDetector()
        else:
            self.enhanced_detector = None
            
        self.captcha_selectors = {
            CaptchaType.RECAPTCHA_V2: [
                ".g-recaptcha",
                "[data-sitekey]",
                "iframe[src*='recaptcha']",
                "div[style*='recaptcha']",
            ],
            CaptchaType.RECAPTCHA_V3: [
                "[data-recaptcha-sitekey]",
                "script[src*='recaptcha/api.js']",
                "grecaptcha.render",
            ],
            CaptchaType.HCAPTCHA: [
                ".h-captcha",
                "[data-sitekey][data-captcha='true']",
                "iframe[src*='hcaptcha']",
            ],
            CaptchaType.IMAGE_CAPTCHA: [
                "img[src*='captcha']",
                ".captcha-image",
                "#captcha_image",
                "[alt*='captcha']",
            ],
            CaptchaType.TEXT_CAPTCHA: [
                "input[name*='captcha']",
                ".captcha-input",
                "#captcha_input",
                "[placeholder*='captcha']",
            ],
            CaptchaType.MATH_CAPTCHA: [
                ".math-captcha",
                "[data-captcha-type='math']",
                ".captcha-math",
            ],
        }

    async def detect_captcha(self, page: Page) -> Dict[str, Any]:
        """Detect if CAPTCHA is present on the page."""
        # Use enhanced detector if available
        if self.enhanced_detector:
            return await self.enhanced_detector.detect_captcha_enhanced(page)
        
        # Fallback to original detection
        detected = {
            "has_captcha": False,
            "captcha_type": None,
            "site_key": None,
            "selectors": [],
            "element_count": 0,
            "ml_suitable": False,
        }

        for captcha_type, selectors in self.captcha_selectors.items():
            elements = []

            for selector in selectors:
                try:
                    elems = await page.query_selector_all(selector)
                    if elems:
                        elements.extend(elems)
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")

            if elements:
                detected["has_captcha"] = True
                detected["captcha_type"] = captcha_type
                detected["selectors"] = selectors
                detected["element_count"] = len(elements)
                detected["ml_suitable"] = captcha_type in [
                    CaptchaType.IMAGE_CAPTCHA, CaptchaType.TEXT_CAPTCHA, CaptchaType.MATH_CAPTCHA
                ]

                # Extract site key for reCAPTCHA/hCaptcha
                if captcha_type in [
                    CaptchaType.RECAPTCHA_V2,
                    CaptchaType.RECAPTCHA_V3,
                    CaptchaType.HCAPTCHA,
                ]:
                    for elem in elements:
                        try:
                            site_key = await elem.get_attribute("data-sitekey")
                            if site_key:
                                detected["site_key"] = site_key
                                break
                        except Exception:
                            pass

                break

        return detected

    async def get_captcha_image(self, page: Page, captcha_type: str) -> Optional[str]:
        """Extract CAPTCHA image as base64."""
        if captcha_type != CaptchaType.IMAGE_CAPTCHA:
            return None

        try:
            # Find the CAPTCHA image
            img = await page.query_selector(
                "img[src*='captcha'], .captcha-image, #captcha_image"
            )
            if not img:
                return None

            # Get image source
            src = await img.get_attribute("src")
            if not src:
                return None

            # If it's a data URL, extract base64
            if src.startswith("data:image"):
                return src.split(",")[1] if "," in src else None

            # If it's a regular URL, fetch and encode
            async with page.context.request.get(src) as response:
                if response.status == 200:
                    image_data = await response.body()
                    return base64.b64encode(image_data).decode()

        except Exception as e:
            logger.error(f"Error extracting CAPTCHA image: {e}")

        return None


class CaptchaSolver:
    """Solves various types of CAPTCHAs using external services and ML."""

    def __init__(self):
        self.settings = get_settings()
        val = getattr(self.settings, "captcha_solvers", None)
        self.enabled_solvers = (
            [s.strip() for s in val.split(",") if s.strip()]
            if isinstance(val, str)
            else []
        )
        
        # Initialize ML solver if available
        if ML_AVAILABLE:
            self.ml_solver = MLCaptchaSolver()
        else:
            self.ml_solver = None

    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve reCAPTCHA v2 using external service."""
        if not self.enabled_solvers:
            logger.warning("No CAPTCHA solvers configured")
            return None

        for solver in self.enabled_solvers:
            try:
                if solver == "2captcha":
                    return await self._solve_with_2captcha(
                        site_key, page_url, "recaptcha_v2"
                    )
                elif solver == "anticaptcha":
                    return await self._solve_with_anticaptcha(
                        site_key, page_url, "recaptcha_v2"
                    )
            except Exception as e:
                logger.error(f"Failed to solve with {solver}: {e}")
                continue

        return None

    async def solve_hcaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha using external service."""
        if not self.enabled_solvers:
            logger.warning("No CAPTCHA solvers configured")
            return None

        for solver in self.enabled_solvers:
            try:
                if solver == "2captcha":
                    return await self._solve_with_2captcha(
                        site_key, page_url, "hcaptcha"
                    )
                elif solver == "anticaptcha":
                    return await self._solve_with_anticaptcha(
                        site_key, page_url, "hcaptcha"
                    )
            except Exception as e:
                logger.error(f"Failed to solve with {solver}: {e}")
                continue

        return None

    async def solve_image_captcha(
        self, image_base64: str, instructions: str = ""
    ) -> Optional[str]:
        """Solve image CAPTCHA using ML first, then external services."""
        
        # Try ML solving first if available
        if self.ml_solver:
            try:
                ml_result, ml_method, ml_confidence = await self.ml_solver.solve_with_fallback(
                    image_base64, "text", self
                )
                if ml_result and ml_confidence >= 0.7:
                    logger.info(f"ML CAPTCHA solved: {ml_method} with confidence {ml_confidence:.2f}")
                    return ml_result
            except Exception as e:
                logger.debug(f"ML CAPTCHA solving failed: {e}")
        
        # Fallback to external services
        if not self.enabled_solvers:
            logger.warning("No CAPTCHA solvers configured")
            return None

        for solver in self.enabled_solvers:
            try:
                if solver == "2captcha":
                    return await self._solve_image_with_2captcha(
                        image_base64, instructions
                    )
                elif solver == "anticaptcha":
                    return await self._solve_image_with_anticaptcha(
                        image_base64, instructions
                    )
            except Exception as e:
                logger.error(f"Failed to solve image with {solver}: {e}")
                continue

        return None

    async def _solve_with_2captcha(
        self, site_key: str, page_url: str, captcha_type: str
    ) -> Optional[str]:
        """Solve CAPTCHA using 2Captcha service."""
        api_key = getattr(self.settings, "twocaptcha_api_key", None)
        if not api_key:
            logger.warning("2Captcha API key not configured")
            return None

        # Create task
        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "RecaptchaV2TaskProxyless"
                if captcha_type == "recaptcha_v2"
                else "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Create task
                resp = await client.post(
                    "https://api.2captcha.com/createTask", json=task_data
                )
                result = resp.json()

                if result.get("errorId", 0) > 0:
                    logger.error(
                        f"2Captcha task creation failed: {result.get('errorDescription')}"
                    )
                    return None

                task_id = result.get("taskId")
                if not task_id:
                    logger.error("No task ID received from 2Captcha")
                    return None

                # Wait for solution
                for _ in range(30):  # 30 attempts, 2 seconds each = 1 minute timeout
                    await asyncio.sleep(2)

                    result_data = {
                        "clientKey": api_key,
                        "taskId": task_id,
                    }

                    resp = await client.post(
                        "https://api.2captcha.com/getTaskResult", json=result_data
                    )
                    result = resp.json()

                    if result.get("status") == "ready":
                        return result.get("solution", {}).get("gRecaptchaResponse")
                    elif result.get("status") == "failed":
                        logger.error(
                            f"2Captcha task failed: {result.get('errorDescription')}"
                        )
                        return None

        except Exception as e:
            logger.error(f"2Captcha solving error: {e}")

        return None

    async def _solve_with_anticaptcha(
        self, site_key: str, page_url: str, captcha_type: str
    ) -> Optional[str]:
        """Solve CAPTCHA using Anti-Captcha service."""
        api_key = getattr(self.settings, "anticaptcha_api_key", None)
        if not api_key:
            logger.warning("Anti-Captcha API key not configured")
            return None

        # Create task
        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "RecaptchaV2TaskProxyless"
                if captcha_type == "recaptcha_v2"
                else "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Create task
                resp = await client.post(
                    "https://api.anti-captcha.com/createTask", json=task_data
                )
                result = resp.json()

                if result.get("errorId", 0) > 0:
                    logger.error(
                        f"Anti-Captcha task creation failed: {result.get('errorDescription')}"
                    )
                    return None

                task_id = result.get("taskId")
                if not task_id:
                    logger.error("No task ID received from Anti-Captcha")
                    return None

                # Wait for solution
                for _ in range(30):  # 30 attempts, 2 seconds each = 1 minute timeout
                    await asyncio.sleep(2)

                    result_data = {
                        "clientKey": api_key,
                        "taskId": task_id,
                    }

                    resp = await client.post(
                        "https://api.anti-captcha.com/getTaskResult", json=result_data
                    )
                    result = resp.json()

                    if result.get("status") == "ready":
                        return result.get("solution", {}).get("gRecaptchaResponse")
                    elif result.get("status") == "failed":
                        logger.error(
                            f"Anti-Captcha task failed: {result.get('errorDescription')}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Anti-Captcha solving error: {e}")

        return None

    async def _solve_image_with_2captcha(
        self, image_base64: str, instructions: str = ""
    ) -> Optional[str]:
        """Solve image CAPTCHA using 2Captcha."""
        api_key = getattr(self.settings, "twocaptcha_api_key", None)
        if not api_key:
            logger.warning("2Captcha API key not configured")
            return None

        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": image_base64,
                "phrase": False,
                "case": False,
                "numeric": 0,
                "math": 0,
                "minLength": 0,
                "maxLength": 0,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Create task
                resp = await client.post(
                    "https://api.2captcha.com/createTask", json=task_data
                )
                result = resp.json()

                if result.get("errorId", 0) > 0:
                    logger.error(
                        f"2Captcha image task creation failed: {result.get('errorDescription')}"
                    )
                    return None

                task_id = result.get("taskId")
                if not task_id:
                    logger.error("No task ID received from 2Captcha")
                    return None

                # Wait for solution
                for _ in range(30):
                    await asyncio.sleep(2)

                    result_data = {
                        "clientKey": api_key,
                        "taskId": task_id,
                    }

                    resp = await client.post(
                        "https://api.2captcha.com/getTaskResult", json=result_data
                    )
                    result = resp.json()

                    if result.get("status") == "ready":
                        return result.get("solution", {}).get("text")
                    elif result.get("status") == "failed":
                        logger.error(
                            f"2Captcha image task failed: {result.get('errorDescription')}"
                        )
                        return None

        except Exception as e:
            logger.error(f"2Captcha image solving error: {e}")

        return None

    async def _solve_image_with_anticaptcha(
        self, image_base64: str, instructions: str = ""
    ) -> Optional[str]:
        """Solve image CAPTCHA using Anti-Captcha."""
        # Implementation similar to 2Captcha but for Anti-Captcha
        # For brevity, returning None to indicate not implemented
        return None


class CaptchaHandler:
    """Main CAPTCHA handling interface for job application automation."""

    def __init__(self):
        self.detector = CaptchaDetector()
        self.solver = CaptchaSolver()

    async def handle_captcha(self, page: Page, page_url: str) -> Dict[str, Any]:
        """Handle CAPTCHA detection and solving with ML enhancement."""
        result = {
            "detected": False,
            "solved": False,
            "solution": None,
            "captcha_type": None,
            "solving_method": None,
            "confidence": 0.0,
            "error": None,
        }

        try:
            # Detect CAPTCHA
            detected = await self.detector.detect_captcha(page)

            if not detected["has_captcha"]:
                return result

            result["detected"] = True
            result["captcha_type"] = detected["captcha_type"]

            captcha_type = detected["captcha_type"]
            site_key = detected.get("site_key")
            ml_suitable = detected.get("ml_suitable", False)

            logger.info(f"CAPTCHA detected: {captcha_type} on {page_url} (ML suitable: {ml_suitable})")

            # Solve based on type
            solution = None
            solving_method = None
            confidence = 0.0

            if captcha_type == CaptchaType.RECAPTCHA_V2 and site_key:
                solution = await self.solver.solve_recaptcha_v2(site_key, page_url)
                solving_method = "external"
                confidence = 0.9
            elif captcha_type == CaptchaType.HCAPTCHA and site_key:
                solution = await self.solver.solve_hcaptcha(site_key, page_url)
                solving_method = "external"
                confidence = 0.9
            elif captcha_type == CaptchaType.IMAGE_CAPTCHA:
                image_data = await self.detector.get_captcha_image(page, captcha_type)
                if image_data:
                    solution = await self.solver.solve_image_captcha(image_data)
                    solving_method = "hybrid" if self.solver.ml_solver else "external"
                    confidence = 0.8 if self.solver.ml_solver else 0.7
            elif captcha_type == CaptchaType.TEXT_CAPTCHA:
                # Try to extract and solve text CAPTCHA
                image_data = await self.detector.get_captcha_image(page, captcha_type)
                if image_data:
                    solution = await self.solver.solve_image_captcha(image_data)
                    solving_method = "hybrid" if self.solver.ml_solver else "external"
                    confidence = 0.8 if self.solver.ml_solver else 0.7
            else:
                result["error"] = (
                    f"CAPTCHA type {captcha_type} not supported for solving"
                )
                return result

            if solution:
                result["solved"] = True
                result["solution"] = solution
                result["solving_method"] = solving_method
                result["confidence"] = confidence
                logger.info(f"CAPTCHA solved successfully: {captcha_type} via {solving_method}")
            else:
                result["error"] = "Failed to solve CAPTCHA"
                logger.warning(f"Failed to solve {captcha_type} on {page_url}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"CAPTCHA handling error: {e}")

        return result

    async def inject_solution(
        self, page: Page, captcha_type: str, solution: str
    ) -> bool:
        """Inject CAPTCHA solution into the page."""
        try:
            if captcha_type in [CaptchaType.RECAPTCHA_V2, CaptchaType.HCAPTCHA]:
                # Inject solution for reCAPTCHA/hCaptcha
                script = f"""
                (function() {{
                    if (typeof grecaptcha !== 'undefined') {{
                        grecaptcha.getResponse = function() {{ return '{solution}'; }};
                    }}
                    if (typeof hcaptcha !== 'undefined') {{
                        hcaptcha.getResponse = function() {{ return '{solution}'; }};
                    }}
                    // Set the response in hidden fields
                    var hiddenInputs = document.querySelectorAll('input[name="g-recaptcha-response"], input[name="h-captcha-response"]');
                    hiddenInputs.forEach(function(input) {{
                        input.value = '{solution}';
                    }});
                }})();
                """
                await page.evaluate(script)
                return True

            elif captcha_type == CaptchaType.IMAGE_CAPTCHA:
                # Find and fill the CAPTCHA input
                captcha_input = await page.query_selector(
                    "input[name*='captcha'], .captcha-input, #captcha_input"
                )
                if captcha_input:
                    await captcha_input.fill(solution)
                    return True

            return False

        except Exception as e:
            logger.error(f"Error injecting CAPTCHA solution: {e}")
            return False
