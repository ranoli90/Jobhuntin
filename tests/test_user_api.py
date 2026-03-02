"""Tests for user-facing web API (api.user).

Covers status mapping and response shapes without requiring a live DB.
"""

from __future__ import annotations


def test_status_to_web_mapping() -> None:
    """Map backend application_status to web status for list_applications."""
    from api.user import _status_to_web

    assert _status_to_web("QUEUED") == "APPLYING"
    assert _status_to_web("PROCESSING") == "APPLYING"
    assert _status_to_web("REQUIRES_INPUT") == "HOLD"
    assert _status_to_web("APPLIED") == "APPLIED"
    assert _status_to_web("SUBMITTED") == "APPLIED"
    assert _status_to_web("COMPLETED") == "APPLIED"
    assert _status_to_web("FAILED") == "FAILED"
    assert _status_to_web("REGISTERED") == "APPLIED"
    assert _status_to_web("UNKNOWN") == "FAILED"
