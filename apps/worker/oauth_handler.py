"""OAuth/SSO handling for the FormAgent.

This module provides support for modern login flows including:
- OAuth2 authentication (Google, LinkedIn, Microsoft)
- SSO integration (SAML, OIDC)
- Social media login buttons
- Multi-factor authentication
- Session management
- Cookie preservation

The handler detects OAuth flows and manages authentication
during job application processes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from playwright.async_api import BrowserContext, Page

from shared.logging_config import get_logger

logger = get_logger("sorce.oauth_handler")


class OAuthHandler:
    """Handles OAuth/SSO authentication flows during job applications."""

    def __init__(self, context: BrowserContext):
        self.context = context
        self.auth_cookies: List[Dict[str, Any]] = []
        self.auth_tokens: Dict[str, str] = {}
        self.session_state: Dict[str, Any] = {}

    async def detect_oauth_flow(self, page: Page) -> bool:
        """Detect if the current page requires OAuth/SSO authentication."""
        oauth_indicators = [
            # Common OAuth provider buttons
            'button[aria-label*="Sign in with Google"]',
            'button[aria-label*="Sign in with LinkedIn"]',
            'button[aria-label*="Sign in with Microsoft"]',
            'button[aria-label*="Sign in with Facebook"]',
            'button[aria-label*="Sign in with Apple"]',
            # Text-based OAuth buttons
            'button:has-text("Sign in with Google")',
            'button:has-text("Sign in with LinkedIn")',
            'button:has-text("Sign in with Microsoft")',
            'button:has-text("Sign in with Facebook")',
            'button:has-text("Sign in with Apple")',
            'button:has-text("Continue with Google")',
            'button:has-text("Continue with LinkedIn")',
            'button:has-text("Continue with Microsoft")',
            'button:has-text("Continue with Facebook")',
            'button:has-text("Continue with Apple")',
            # Class-based OAuth buttons
            ".oauth-button",
            ".sso-button",
            ".social-login",
            ".google-signin",
            ".linkedin-signin",
            ".microsoft-signin",
            ".facebook-signin",
            ".apple-signin",
            # Form-based OAuth
            'form[action*="oauth"]',
            'form[action*="sso"]',
            'form[action*="saml"]',
            'form[action*="openid"]',
            # URL indicators
            'a[href*="oauth"]',
            'a[href*="sso"]',
            'a[href*="saml"]',
            'a[href*="openid"]',
            # Common OAuth text patterns
            ':has-text("Sign in with")',
            ':has-text("Continue with")',
            ':has-text("Log in with")',
            ':has-text("Connect with")',
            # SSO-specific indicators
            ':has-text("Single Sign-On")',
            ':has-text("SSO")',
            ':has-text("Company Login")',
            ':has-text("Enterprise Login")',
        ]

        for selector in oauth_indicators:
            try:
                element = page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    logger.info("OAuth/SSO flow detected with selector: %s", selector)
                    return True
            except Exception as e:
                logger.debug("OAuth detection failed for selector %s: %s", selector, e)
                continue

        # Check URL patterns for OAuth redirects
        current_url = page.url
        oauth_url_patterns = [
            "oauth",
            "sso",
            "saml",
            "openid",
            "auth",
            "login",
            "accounts.google.com",
            "linkedin.com/oauth",
            "login.microsoftonline.com",
            "facebook.com/v2.0/dialog",
            "appleid.apple.com/auth",
        ]

        if any(pattern in current_url.lower() for pattern in oauth_url_patterns):
            logger.info("OAuth/SSO flow detected via URL: %s", current_url)
            return True

        return False

    async def handle_oauth_flow(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle OAuth/SSO authentication flow.

        Args:
            page: Current page instance
            user_credentials: Optional user credentials for manual authentication

        Returns:
            True if authentication was successful, False otherwise
        """
        try:
            # Detect OAuth provider
            provider = await self._detect_oauth_provider(page)
            if not provider:
                logger.warning("Could not detect OAuth provider")
                return False

            logger.info("Handling OAuth flow for provider: %s", provider)

            # Store current state for potential redirect
            initial_url = page.url
            self.session_state["initial_url"] = initial_url
            self.session_state["provider"] = provider

            # Click OAuth button
            success = await self._click_oauth_button(page, provider)
            if not success:
                logger.warning(
                    "Could not click OAuth button for provider: %s", provider
                )
                return False

            # Wait for redirect and handle provider-specific flow
            success = await self._handle_provider_redirect(
                page, provider, user_credentials
            )
            if not success:
                logger.warning(
                    "Failed to handle OAuth redirect for provider: %s", provider
                )
                return False

            # Store authentication cookies/tokens
            await self._store_auth_session(page)

            logger.info("OAuth flow completed successfully for provider: %s", provider)
            return True

        except Exception as e:
            logger.error("OAuth flow failed: %s", e)
            return False

    async def _detect_oauth_provider(self, page: Page) -> Optional[str]:
        """Detect which OAuth provider is being used."""
        provider_selectors = {
            "google": [
                'button[aria-label*="Google"]',
                'button:has-text("Google")',
                ".google-signin",
                'a[href*="accounts.google.com"]',
            ],
            "linkedin": [
                'button[aria-label*="LinkedIn"]',
                'button:has-text("LinkedIn")',
                ".linkedin-signin",
                'a[href*="linkedin.com/oauth"]',
            ],
            "microsoft": [
                'button[aria-label*="Microsoft"]',
                'button:has-text("Microsoft")',
                ".microsoft-signin",
                'a[href*="login.microsoftonline.com"]',
            ],
            "facebook": [
                'button[aria-label*="Facebook"]',
                'button:has-text("Facebook")',
                ".facebook-signin",
                'a[href*="facebook.com/v2.0/dialog"]',
            ],
            "apple": [
                'button[aria-label*="Apple"]',
                'button:has-text("Apple")',
                ".apple-signin",
                'a[href*="appleid.apple.com/auth"]',
            ],
        }

        for provider, selectors in provider_selectors.items():
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0 and await element.is_visible():
                        return provider
                except Exception:
                    continue

        # Check URL for provider indicators
        current_url = page.url.lower()
        if "accounts.google.com" in current_url:
            return "google"
        elif "linkedin.com/oauth" in current_url:
            return "linkedin"
        elif "login.microsoftonline.com" in current_url:
            return "microsoft"
        elif "facebook.com" in current_url:
            return "facebook"
        elif "appleid.apple.com" in current_url:
            return "apple"

        return None

    async def _click_oauth_button(self, page: Page, provider: str) -> bool:
        """Click the OAuth button for the detected provider."""
        button_selectors = {
            "google": [
                'button:has-text("Sign in with Google")',
                'button:has-text("Continue with Google")',
                'button[aria-label*="Google"]',
                ".google-signin",
            ],
            "linkedin": [
                'button:has-text("Sign in with LinkedIn")',
                'button:has-text("Continue with LinkedIn")',
                'button[aria-label*="LinkedIn"]',
                ".linkedin-signin",
            ],
            "microsoft": [
                'button:has-text("Sign in with Microsoft")',
                'button:has-text("Continue with Microsoft")',
                'button[aria-label*="Microsoft"]',
                ".microsoft-signin",
            ],
            "facebook": [
                'button:has-text("Sign in with Facebook")',
                'button:has-text("Continue with Facebook")',
                'button[aria-label*="Facebook"]',
                ".facebook-signin",
            ],
            "apple": [
                'button:has-text("Sign in with Apple")',
                'button:has-text("Continue with Apple")',
                'button[aria-label*="Apple"]',
                ".apple-signin",
            ],
        }

        selectors = button_selectors.get(provider, [])
        for selector in selectors:
            try:
                button = page.locator(selector).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    await page.wait_for_timeout(2000)
                    return True
            except Exception as e:
                logger.debug(
                    "Failed to click OAuth button %s for %s: %s", selector, provider, e
                )
                continue

        return False

    async def _handle_provider_redirect(
        self,
        page: Page,
        provider: str,
        user_credentials: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Handle the provider-specific redirect and authentication."""
        try:
            # Wait for redirect to provider
            await page.wait_for_load_state("networkidle", timeout=10000)

            current_url = page.url
            logger.info("Redirected to: %s", current_url)

            # Provider-specific handling
            if provider == "google":
                return await self._handle_google_auth(page, user_credentials)
            elif provider == "linkedin":
                return await self._handle_linkedin_auth(page, user_credentials)
            elif provider == "microsoft":
                return await self._handle_microsoft_auth(page, user_credentials)
            elif provider == "facebook":
                return await self._handle_facebook_auth(page, user_credentials)
            elif provider == "apple":
                return await self._handle_apple_auth(page, user_credentials)
            else:
                # Generic OAuth handling
                return await self._handle_generic_oauth(page, user_credentials)

        except Exception as e:
            logger.error("Provider redirect handling failed for %s: %s", provider, e)
            return False

    async def _handle_google_auth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle Google OAuth authentication."""
        try:
            # Check if we're on Google's auth page
            if "accounts.google.com" not in page.url:
                return False

            # Look for email input
            email_input = page.locator(
                'input[type="email"], input[name="email"], input[id="identifierId"]'
            ).first
            if await email_input.count() > 0 and await email_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await email_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

                    # Click next button
                    next_button = page.locator(
                        'button:has-text("Next"), button:has-text("Next")'
                    ).first
                    if await next_button.count() > 0:
                        await next_button.click()
                        await page.wait_for_timeout(2000)
                else:
                    logger.warning("No email credentials provided for Google OAuth")
                    return False

            # Look for password input
            password_input = page.locator(
                'input[type="password"], input[name="password"]'
            ).first
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

                    # Click password next button
                    password_next = page.locator(
                        'button:has-text("Next"), button:has-text("Next")'
                    ).first
                    if await password_next.count() > 0:
                        await password_next.click()
                        await page.wait_for_timeout(2000)
                else:
                    logger.warning("No password credentials provided for Google OAuth")
                    return False

            # Handle 2FA if present
            if await self._detect_2fa(page):
                return await self._handle_2fa(page, user_credentials)

            # Wait for redirect back to original site
            await page.wait_for_url("**/oauth**", timeout=15000)
            return True

        except Exception as e:
            logger.error("Google OAuth handling failed: %s", e)
            return False

    async def _handle_linkedin_auth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle LinkedIn OAuth authentication."""
        try:
            # Check if we're on LinkedIn's auth page
            if "linkedin.com/oauth" not in page.url:
                return False

            # Look for email input
            email_input = page.locator(
                'input[type="email"], input[name="session_key"]'
            ).first
            if await email_input.count() > 0 and await email_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await email_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

            # Look for password input
            password_input = page.locator(
                'input[type="password"], input[name="session_password"]'
            ).first
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

            # Click sign in button
            signin_button = page.locator(
                'button:has-text("Sign in"), button:has-text("Allow")'
            ).first
            if await signin_button.count() > 0:
                await signin_button.click()
                await page.wait_for_timeout(2000)

            # Wait for redirect back to original site
            await page.wait_for_url("**/oauth**", timeout=15000)
            return True

        except Exception as e:
            logger.error("LinkedIn OAuth handling failed: %s", e)
            return False

    async def _handle_microsoft_auth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle Microsoft OAuth authentication."""
        try:
            # Check if we're on Microsoft's auth page
            if "login.microsoftonline.com" not in page.url:
                return False

            # Look for email input
            email_input = page.locator(
                'input[type="email"], input[name="loginfmt"]'
            ).first
            if await email_input.count() > 0 and await email_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await email_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

                    # Click next button
                    next_button = page.locator(
                        'button:has-text("Next"), input[type="submit"][value="Next"]'
                    ).first
                    if await next_button.count() > 0:
                        await next_button.click()
                        await page.wait_for_timeout(2000)

            # Look for password input
            password_input = page.locator(
                'input[type="password"], input[name="passwd"]'
            ).first
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

            # Click sign in button
            signin_button = page.locator(
                'button:has-text("Sign in"), input[type="submit"][value="Sign in"]'
            ).first
            if await signin_button.count() > 0:
                await signin_button.click()
                await page.wait_for_timeout(2000)

            # Handle 2FA if present
            if await self._detect_2fa(page):
                return await self._handle_2fa(page, user_credentials)

            # Wait for redirect back to original site
            await page.wait_for_url("**/oauth**", timeout=15000)
            return True

        except Exception as e:
            logger.error("Microsoft OAuth handling failed: %s", e)
            return False

    async def _handle_facebook_auth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle Facebook OAuth authentication."""
        try:
            # Check if we're on Facebook's auth page
            if "facebook.com" not in page.url:
                return False

            # Look for email input
            email_input = page.locator('input[type="email"], input[name="email"]').first
            if await email_input.count() > 0 and await email_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await email_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

            # Look for password input
            password_input = page.locator(
                'input[type="password"], input[name="pass"]'
            ).first
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

            # Click login button
            login_button = page.locator(
                'button:has-text("Log In"), input[type="submit"][value="Log In"]'
            ).first
            if await login_button.count() > 0:
                await login_button.click()
                await page.wait_for_timeout(2000)

            # Handle permission dialog if present
            continue_button = page.locator(
                'button:has-text("Continue"), button:has-text("Allow")'
            ).first
            if await continue_button.count() > 0:
                await continue_button.click()
                await page.wait_for_timeout(2000)

            # Wait for redirect back to original site
            await page.wait_for_url("**/oauth**", timeout=15000)
            return True

        except Exception as e:
            logger.error("Facebook OAuth handling failed: %s", e)
            return False

    async def _handle_apple_auth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle Apple OAuth authentication."""
        try:
            # Check if we're on Apple's auth page
            if "appleid.apple.com" not in page.url:
                return False

            # Look for Apple ID input
            apple_id_input = page.locator(
                'input[type="email"], input[name="accountName"]'
            ).first
            if await apple_id_input.count() > 0 and await apple_id_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await apple_id_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

            # Click continue button
            continue_button = page.locator(
                'button:has-text("Continue"), button:has-text("Sign In")'
            ).first
            if await continue_button.count() > 0:
                await continue_button.click()
                await page.wait_for_timeout(2000)

            # Handle password if required
            password_input = page.locator('input[type="password"]').first
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

                    # Click sign in button
                    signin_button = page.locator('button:has-text("Sign In")').first
                    if await signin_button.count() > 0:
                        await signin_button.click()
                        await page.wait_for_timeout(2000)

            # Handle 2FA if present
            if await self._detect_2fa(page):
                return await self._handle_2fa(page, user_credentials)

            # Wait for redirect back to original site
            await page.wait_for_url("**/oauth**", timeout=15000)
            return True

        except Exception as e:
            logger.error("Apple OAuth handling failed: %s", e)
            return False

    async def _handle_generic_oauth(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle generic OAuth authentication."""
        try:
            # Look for common OAuth form fields
            email_input = page.locator(
                'input[type="email"], input[name*="email"], input[name*="username"]'
            ).first
            password_input = page.locator(
                'input[type="password"], input[name*="password"]'
            ).first

            # Fill email if found
            if await email_input.count() > 0 and await email_input.is_visible():
                if user_credentials and user_credentials.get("email"):
                    await email_input.fill(user_credentials["email"])
                    await page.wait_for_timeout(1000)

            # Fill password if found
            if await password_input.count() > 0 and await password_input.is_visible():
                if user_credentials and user_credentials.get("password"):
                    await password_input.fill(user_credentials["password"])
                    await page.wait_for_timeout(1000)

            # Look for submit button
            submit_button = page.locator(
                'button[type="submit"], input[type="submit"], button:has-text("Sign"), button:has-text("Login")'
            ).first
            if await submit_button.count() > 0:
                await submit_button.click()
                await page.wait_for_timeout(2000)

            # Wait for redirect
            await page.wait_for_load_state("networkidle", timeout=10000)
            return True

        except Exception as e:
            logger.error("Generic OAuth handling failed: %s", e)
            return False

    async def _detect_2fa(self, page: Page) -> bool:
        """Detect if 2FA is required."""
        two_fa_indicators = [
            'input[type="text"][name*="code"]',
            'input[type="text"][placeholder*="code"]',
            'input[type="text"][aria-label*="code"]',
            ':has-text("verification code")',
            ':has-text("two-factor")',
            ':has-text("2FA")',
            ':has-text("authentication code")',
        ]

        for selector in two_fa_indicators:
            try:
                element = page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    return True
            except Exception:
                continue

        return False

    async def _handle_2fa(
        self, page: Page, user_credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """Handle 2FA authentication."""
        try:
            logger.info("2FA detected, attempting to handle")

            # Look for 2FA code input
            code_input = page.locator(
                'input[type="text"][name*="code"], input[type="text"][placeholder*="code"]'
            ).first
            if await code_input.count() > 0 and await code_input.is_visible():
                if user_credentials and user_credentials.get("two_factor_code"):
                    await code_input.fill(user_credentials["two_factor_code"])
                    await page.wait_for_timeout(1000)

                    # Click verify button
                    verify_button = page.locator(
                        'button:has-text("Verify"), button:has-text("Continue")'
                    ).first
                    if await verify_button.count() > 0:
                        await verify_button.click()
                        await page.wait_for_timeout(2000)
                        return True
                else:
                    logger.warning("No 2FA code provided, authentication may fail")
                    return False

            return False

        except Exception as e:
            logger.error("2FA handling failed: %s", e)
            return False

    async def _store_auth_session(self, page: Page) -> None:
        """Store authentication cookies and tokens."""
        try:
            # Get cookies
            cookies = await page.context.cookies()
            self.auth_cookies.extend(cookies)

            # Extract tokens from local storage
            try:
                local_storage = await page.evaluate("() => localStorage")
                for key, value in local_storage.items():
                    if "token" in key.lower() or "auth" in key.lower():
                        self.auth_tokens[key] = value
            except Exception as e:
                logger.debug("Could not access localStorage: %s", e)

            # Extract tokens from session storage
            try:
                session_storage = await page.evaluate("() => sessionStorage")
                for key, value in session_storage.items():
                    if "token" in key.lower() or "auth" in key.lower():
                        self.auth_tokens[key] = value
            except Exception as e:
                logger.debug("Could not access sessionStorage: %s", e)

            logger.info(
                "Stored %d cookies and %d auth tokens",
                len(self.auth_cookies),
                len(self.auth_tokens),
            )

        except Exception as e:
            logger.error("Failed to store auth session: %s", e)

    async def restore_auth_session(self, page: Page) -> bool:
        """Restore previously stored authentication session."""
        try:
            # Restore cookies
            if self.auth_cookies:
                await page.context.add_cookies(self.auth_cookies)
                logger.info("Restored %d cookies", len(self.auth_cookies))

            # Restore tokens to localStorage
            if self.auth_tokens:
                for key, value in self.auth_tokens.items():
                    try:
                        await page.evaluate(
                            f"() => localStorage.setItem('{key}', '{value}')"
                        )
                    except Exception as e:
                        logger.debug(
                            "Could not restore localStorage item %s: %s", key, e
                        )

                logger.info("Restored %d auth tokens", len(self.auth_tokens))

            return True

        except Exception as e:
            logger.error("Failed to restore auth session: %s", e)
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return {
            "authenticated": len(self.auth_cookies) > 0 or len(self.auth_tokens) > 0,
            "cookies_count": len(self.auth_cookies),
            "tokens_count": len(self.auth_tokens),
            "session_state": self.session_state,
            "auth_providers": list(
                set(cookie.get("domain", "") for cookie in self.auth_cookies)
            ),
        }

    async def clear_auth_session(self) -> None:
        """Clear stored authentication session."""
        self.auth_cookies.clear()
        self.auth_tokens.clear()
        self.session_state.clear()
        logger.info("Cleared authentication session")


def get_oauth_handler(context: BrowserContext) -> OAuthHandler:
    """Get or create OAuth handler instance."""
    return OAuthHandler(context)
