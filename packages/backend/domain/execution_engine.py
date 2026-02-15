"""
Headless Browser Execution Engine with Bot Detection Evasion.

Implements the "Execution Engine" layer from competitive analysis:
- Randomized cursor movements and keystroke latency
- Human-like interaction patterns
- Anti-fingerprinting measures
- CAPTCHA detection and handoff
- Resilient form filling with retry logic

This module provides the low-level browser automation primitives
that the Agent uses to interact with ATS portals.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from playwright.async_api import (
    BrowserContext,
    Page,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.execution_engine")


class InteractionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    SCROLL = "scroll"
    HOVER = "hover"
    UPLOAD = "upload"


@dataclass
class InteractionResult:
    success: bool
    interaction_type: InteractionType
    selector: str
    duration_ms: float
    error: str | None = None
    retry_count: int = 0


@dataclass
class HumanBehaviorConfig:
    min_typing_delay_ms: int = 30
    maxTyping_delay_ms: int = 120
    min_click_delay_ms: int = 50
    max_click_delay_ms: int = 200
    scroll_pause_ms: int = 300
    mouse_move_steps: int = 20
    page_load_wait_ms: int = 500
    think_time_min_ms: int = 200
    think_time_max_ms: int = 800


class HumanBehaviorSimulator:
    """
    Simulates human-like browser interactions.

    Based on competitive analysis recommendations:
    - Randomized cursor movements
    - Variable keystroke latency
    - Scroll pausing
    - Natural timing patterns
    """

    def __init__(self, config: HumanBehaviorConfig | None = None):
        self.config = config or HumanBehaviorConfig()
        self._last_interaction_time = time.monotonic()

    async def think(self) -> None:
        await asyncio.sleep(
            random.uniform(self.config.think_time_min_ms, self.config.think_time_max_ms)
            / 1000
        )

    async def human_delay(self, action: str = "general") -> None:
        if action == "typing":
            delay = random.uniform(
                self.config.minTyping_delay_ms, self.config.maxTyping_delay_ms
            )
        elif action == "click":
            delay = random.uniform(
                self.config.min_click_delay_ms, self.config.max_click_delay_ms
            )
        else:
            delay = random.uniform(50, 150)

        await asyncio.sleep(delay / 1000)

    async def move_mouse_humanlike(
        self,
        page: Page,
        target_x: int,
        target_y: int,
    ) -> None:
        try:
            viewport = page.viewport_size
            if not viewport:
                return

            current = await page.evaluate(
                "() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })"
            )
            current_x = current.get("x", viewport["width"] // 2)
            current_y = current.get("y", viewport["height"] // 2)

            steps = self.config.mouse_move_steps
            for i in range(steps):
                progress = (i + 1) / steps
                curve = 4 * progress * (1 - progress)

                x = current_x + (target_x - current_x) * progress
                y = current_y + (target_y - current_y) * progress

                x += random.uniform(-5, 5) * curve
                y += random.uniform(-5, 5) * curve

                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(5, 15) / 1000)

            await page.mouse.move(target_x, target_y)
        except Exception as e:
            logger.debug("Mouse movement failed: %s", e)

    async def type_humanlike(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True,
    ) -> InteractionResult:
        start_time = time.monotonic()

        try:
            element = await page.wait_for_selector(selector, timeout=10000)
            if not element:
                return InteractionResult(
                    success=False,
                    interaction_type=InteractionType.TYPE,
                    selector=selector,
                    duration_ms=0,
                    error="Element not found",
                )

            await element.scroll_into_view_if_needed()
            await self.think()

            if clear_first:
                await element.click(click_count=3)
                await page.keyboard.press("Backspace")
                await self.human_delay("click")

            for char in text:
                await element.type(char, delay=0)
                await self.human_delay("typing")

            duration_ms = (time.monotonic() - start_time) * 1000
            incr(
                "execution_engine.type_success",
                {"selector_type": self._classify_selector(selector)},
            )

            return InteractionResult(
                success=True,
                interaction_type=InteractionType.TYPE,
                selector=selector,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            incr("execution_engine.type_error", {"error_type": type(e).__name__})
            logger.warning("Type failed for %s: %s", selector, e)

            return InteractionResult(
                success=False,
                interaction_type=InteractionType.TYPE,
                selector=selector,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def click_humanlike(
        self,
        page: Page,
        selector: str,
        double_click: bool = False,
    ) -> InteractionResult:
        start_time = time.monotonic()

        try:
            element = await page.wait_for_selector(selector, timeout=10000)
            if not element:
                return InteractionResult(
                    success=False,
                    interaction_type=InteractionType.CLICK,
                    selector=selector,
                    duration_ms=0,
                    error="Element not found",
                )

            await element.scroll_into_view_if_needed()
            await self.think()

            box = await element.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2 + random.uniform(-2, 2)
                target_y = box["y"] + box["height"] / 2 + random.uniform(-2, 2)
                await self.move_mouse_humanlike(page, target_x, target_y)

            await self.human_delay("click")

            if double_click:
                await element.dblclick()
            else:
                await element.click()

            duration_ms = (time.monotonic() - start_time) * 1000
            incr(
                "execution_engine.click_success",
                {"selector_type": self._classify_selector(selector)},
            )

            return InteractionResult(
                success=True,
                interaction_type=InteractionType.CLICK,
                selector=selector,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            incr("execution_engine.click_error", {"error_type": type(e).__name__})
            logger.warning("Click failed for %s: %s", selector, e)

            return InteractionResult(
                success=False,
                interaction_type=InteractionType.CLICK,
                selector=selector,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def select_humanlike(
        self,
        page: Page,
        selector: str,
        value: str,
    ) -> InteractionResult:
        start_time = time.monotonic()

        try:
            element = await page.wait_for_selector(selector, timeout=10000)
            if not element:
                return InteractionResult(
                    success=False,
                    interaction_type=InteractionType.SELECT,
                    selector=selector,
                    duration_ms=0,
                    error="Element not found",
                )

            await element.scroll_into_view_if_needed()
            await self.think()
            await self.human_delay("click")

            await element.click()
            await self.human_delay("click")

            await element.select_option(value=value)

            duration_ms = (time.monotonic() - start_time) * 1000
            incr(
                "execution_engine.select_success",
                {"selector_type": self._classify_selector(selector)},
            )

            return InteractionResult(
                success=True,
                interaction_type=InteractionType.SELECT,
                selector=selector,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            incr("execution_engine.select_error", {"error_type": type(e).__name__})
            logger.warning("Select failed for %s: %s", selector, e)

            return InteractionResult(
                success=False,
                interaction_type=InteractionType.SELECT,
                selector=selector,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _classify_selector(self, selector: str) -> str:
        if selector.startswith("#"):
            return "id"
        elif selector.startswith("."):
            return "class"
        elif selector.startswith("["):
            return "attribute"
        elif selector.startswith("//"):
            return "xpath"
        else:
            return "other"


class AntiDetection:
    """
    Anti-detection and anti-fingerprinting measures.

    Implements countermeasures against common bot detection:
    - WebDriver flag masking
    - Navigator property spoofing
    - Canvas fingerprint randomization
    - WebGL fingerprint randomization
    """

    STEALTH_SCRIPT = """
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // Override navigator.plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
            ];
            plugins.item = (i) => plugins[i] || null;
            plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
            plugins.refresh = () => {};
            return plugins;
        }
    });
    
    // Override navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    // Override permissions API
    const originalQuery = window.navigator.permissions?.query;
    if (originalQuery) {
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery.call(window.navigator.permissions, parameters);
        };
    }
    
    // Randomize canvas fingerprint
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (this.width === 0 || this.height === 0) {
            return originalToDataURL.apply(this, arguments);
        }
        // Add subtle noise to canvas data
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] ^= (Math.random() * 2) | 0;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, arguments);
    };
    
    // Override WebGL fingerprint
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };
    
    // Mask automation indicators
    window.chrome = {
        runtime: {}
    };
    
    // Override notification permission
    if (window.Notification) {
        Object.defineProperty(Notification, 'permission', {
            get: () => 'default'
        });
    }
    """

    @classmethod
    async def inject_stealth(cls, page: Page) -> None:
        try:
            await page.add_init_script(cls.STEALTH_SCRIPT)
            logger.debug("Stealth script injected")
        except Exception as e:
            logger.warning("Failed to inject stealth script: %s", e)

    @classmethod
    async def setup_context(
        cls,
        context: BrowserContext,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
        locale: str = "en-US",
        timezone: str = "America/New_York",
    ) -> None:
        try:
            await context.add_init_script(cls.STEALTH_SCRIPT)

            if user_agent:
                await context.set_extra_http_headers({"User-Agent": user_agent})

            logger.debug("Anti-detection context configured")
        except Exception as e:
            logger.warning("Failed to setup anti-detection context: %s", e)


class ExecutionEngine:
    """
    Main execution engine that coordinates browser interactions.

    Provides:
    - Form filling with retry logic
    - CAPTCHA detection and handoff
    - Multi-step form navigation
    - Error recovery
    """

    def __init__(
        self,
        page: Page,
        behavior_config: HumanBehaviorConfig | None = None,
    ):
        self.page = page
        self.behavior = HumanBehaviorSimulator(behavior_config)
        self._interaction_history: list[InteractionResult] = []

    async def initialize(self) -> None:
        await AntiDetection.inject_stealth(self.page)
        incr("execution_engine.initialized")

    async def fill_form(
        self,
        fields: list[dict[str, Any]],
        max_retries: int = 3,
    ) -> list[InteractionResult]:
        results: list[InteractionResult] = []

        for field in fields:
            selector = field.get("selector")
            field_type = field.get("type", "text")
            value = field.get("value", "")

            if not selector:
                continue

            result = await self._fill_single_field(
                selector=selector,
                field_type=field_type,
                value=value,
                max_retries=max_retries,
            )
            results.append(result)
            self._interaction_history.append(result)

            if result.success:
                await self.behavior.think()

        return results

    async def _fill_single_field(
        self,
        selector: str,
        field_type: str,
        value: str,
        max_retries: int,
    ) -> InteractionResult:
        last_result: InteractionResult | None = None

        for attempt in range(max_retries):
            if field_type in ("text", "email", "tel", "password", "textarea"):
                result = await self.behavior.type_humanlike(self.page, selector, value)
            elif field_type == "select":
                result = await self.behavior.select_humanlike(
                    self.page, selector, value
                )
            elif field_type == "checkbox":
                result = await self.behavior.click_humanlike(self.page, selector)
            elif field_type == "radio":
                result = await self.behavior.click_humanlike(self.page, selector)
            elif field_type == "file":
                result = await self._upload_file(selector, value)
            else:
                result = await self.behavior.type_humanlike(self.page, selector, value)

            result.retry_count = attempt

            if result.success:
                return result

            last_result = result
            await asyncio.sleep(0.5 * (attempt + 1))

        return last_result or InteractionResult(
            success=False,
            interaction_type=InteractionType.TYPE,
            selector=selector,
            duration_ms=0,
            error="Max retries exceeded",
            retry_count=max_retries,
        )

    async def _upload_file(
        self,
        selector: str,
        file_path: str,
    ) -> InteractionResult:
        start_time = time.monotonic()

        try:
            async with self.page.expect_file_chooser() as fc_info:
                await self.page.click(selector)
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)

            duration_ms = (time.monotonic() - start_time) * 1000
            incr("execution_engine.upload_success")

            return InteractionResult(
                success=True,
                interaction_type=InteractionType.UPLOAD,
                selector=selector,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            incr("execution_engine.upload_error")

            return InteractionResult(
                success=False,
                interaction_type=InteractionType.UPLOAD,
                selector=selector,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def navigate_to_next_step(
        self,
        next_selectors: list[str],
        timeout_ms: int = 5000,
    ) -> bool:
        for selector in next_selectors:
            result = await self.behavior.click_humanlike(self.page, selector)
            if result.success:
                try:
                    await self.page.wait_for_load_state(
                        "networkidle", timeout=timeout_ms
                    )
                    incr("execution_engine.navigation_success")
                    return True
                except PlaywrightTimeoutError:
                    pass

        incr("execution_engine.navigation_failed")
        return False

    async def scroll_page(self, direction: str = "down", amount: int = 300) -> None:
        delta = amount if direction == "down" else -amount
        await self.page.evaluate(f"window.scrollBy(0, {delta})")
        await asyncio.sleep(self.behavior.config.scroll_pause_ms / 1000)

    def get_metrics(self) -> dict[str, Any]:
        if not self._interaction_history:
            return {}

        total = len(self._interaction_history)
        successful = sum(1 for r in self._interaction_history if r.success)
        avg_duration = sum(r.duration_ms for r in self._interaction_history) / total

        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "success_rate": successful / total if total > 0 else 0,
            "average_duration_ms": avg_duration,
        }
