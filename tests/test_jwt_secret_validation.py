"""Tests for JWT_SECRET validation at startup.

This module tests that the application properly validates JWT_SECRET
configuration at startup, refusing to start if the secret is missing
or too short in production environments.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from shared.config import Settings, Environment


class TestJwtSecretValidation:
    """Test JWT_SECRET validation in Settings.validate_critical()."""

    def test_validate_critical_empty_jwt_secret_in_prod_raises(self):
        """Empty JWT_SECRET should raise RuntimeError in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,  # Valid CSRF secret
            jwt_secret="",  # Empty - should fail
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower()

    def test_validate_critical_short_jwt_secret_in_prod_raises(self):
        """JWT_SECRET shorter than 32 chars should raise RuntimeError in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="too-short-secret",  # 16 chars - too short
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)
        assert "32" in str(exc_info.value)

    def test_validate_critical_dev_prefix_jwt_secret_in_prod_raises(self):
        """JWT_SECRET with dev- prefix should raise RuntimeError in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="dev-this-is-a-dev-secret-not-allowed",  # dev- prefix
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)
        assert "dev" in str(exc_info.value).lower()

    def test_validate_critical_valid_jwt_secret_in_prod_passes(self):
        """Valid JWT_SECRET (32+ chars) should pass validation in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="a" * 64,  # Valid 64-char secret
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        # Should not raise
        settings.validate_critical()

    def test_validate_critical_empty_jwt_secret_in_local_allowed(self):
        """Empty JWT_SECRET should be allowed in local environment (with warning)."""
        settings = Settings(
            env=Environment.LOCAL,
            database_url="postgresql://user:pass@localhost:5432/db",
            llm_api_key="test-key",
            jwt_secret="",  # Empty - allowed in local
        )
        
        # Should not raise in local environment
        settings.validate_critical()

    def test_validate_critical_short_jwt_secret_in_local_allowed(self):
        """Short JWT_SECRET should be allowed in local environment (with warning)."""
        settings = Settings(
            env=Environment.LOCAL,
            database_url="postgresql://user:pass@localhost:5432/db",
            llm_api_key="test-key",
            jwt_secret="short",  # Short - allowed in local
        )
        
        # Should not raise in local environment
        settings.validate_critical()

    def test_validate_critical_empty_jwt_secret_in_staging_raises(self):
        """Empty JWT_SECRET should raise RuntimeError in staging."""
        settings = Settings(
            env=Environment.STAGING,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://staging.example.com",
            api_public_url="https://api-staging.example.com",
            csrf_secret="a" * 64,
            jwt_secret="",  # Empty - should fail
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)

    def test_validate_critical_exactly_32_char_jwt_secret_passes(self):
        """JWT_SECRET of exactly 32 characters should pass validation."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="a" * 32,  # Exactly 32 chars - minimum valid
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        # Should not raise
        settings.validate_critical()

    def test_validate_critical_31_char_jwt_secret_fails(self):
        """JWT_SECRET of 31 characters should fail validation."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="a" * 31,  # 31 chars - just under minimum
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)
        assert "31" in str(exc_info.value)  # Current length reported


class TestJwtSecretLengthReporting:
    """Test that JWT_SECRET validation reports the actual length in error messages."""

    def test_error_message_includes_current_length(self):
        """Error message should include the current JWT_SECRET length for debugging."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="short-key",  # 9 chars
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        error_msg = str(exc_info.value)
        # Should report current length (9 chars)
        assert "9" in error_msg
        # Should mention minimum required
        assert "32" in error_msg


class TestChangeInProductionPlaceholder:
    """Test that 'change-in-production' placeholder values are rejected."""

    def test_change_in_production_placeholder_rejected(self):
        """JWT_SECRET containing 'change-in-production' should be rejected."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="change-in-production-please-replace-this",
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()
        
        assert "JWT_SECRET" in str(exc_info.value)
        assert "prod" in str(exc_info.value).lower() or "default" in str(exc_info.value).lower()


class TestAdditionalCriticalValidation:
    """Test broader critical startup validation coverage."""

    def test_validate_critical_short_csrf_secret_in_prod_raises(self):
        """Short CSRF_SECRET should raise RuntimeError in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="short-secret",
            jwt_secret="a" * 64,
            redis_url="redis://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )

        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()

        assert "CSRF_SECRET" in str(exc_info.value)
        assert "32" in str(exc_info.value)

    def test_validate_critical_invalid_cors_origin_in_prod_raises(self):
        """Wildcard CORS entries should fail fast in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="b" * 64,
            redis_url="redis://cache.example.com:6379",
            cors_allowed_origins="https://app.example.com,*",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )

        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()

        assert "CORS_ALLOWED_ORIGINS" in str(exc_info.value)
        assert "wildcard" in str(exc_info.value).lower()

    def test_validate_critical_invalid_redis_url_in_prod_raises(self):
        """Invalid REDIS_URL scheme should raise RuntimeError in production."""
        settings = Settings(
            env=Environment.PROD,
            database_url="postgresql://user:pass@host:5432/db",
            llm_api_key="test-key",
            app_base_url="https://example.com",
            api_public_url="https://api.example.com",
            csrf_secret="a" * 64,
            jwt_secret="b" * 64,
            redis_url="http://cache.example.com:6379",
            webhook_signing_secret="test-webhook-secret-min-32-chars",
        )

        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_critical()

        assert "REDIS_URL" in str(exc_info.value)
        assert "redis://" in str(exc_info.value)
