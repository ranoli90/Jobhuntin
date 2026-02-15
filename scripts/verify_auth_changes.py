import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from fastapi import HTTPException

from apps.api.auth import _generate_magic_link


async def test_auth_security():
    print("Testing auth security...")

    # Mock settings with no secret
    mock_settings = MagicMock()
    mock_settings.jwt_secret = None

    # Mock DB
    mock_db = MagicMock()

    try:
        await _generate_magic_link(mock_settings, "test@example.com", "http://localhost", mock_db)
        print("❌ FAILED: _generate_magic_link should have raised HTTPException")
        sys.exit(1)
    except HTTPException as e:
        if e.status_code == 500 and "JWT_SECRET missing" in e.detail:
            print("✅ PASSED: _generate_magic_link raised 500 when JWT_SECRET is missing")
        else:
            print(f"❌ FAILED: Raised unexpected HTTPException: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ FAILED: Raised unexpected exception: {type(e).__name__}: {e}")
        sys.exit(1)

    from unittest.mock import AsyncMock, MagicMock

    # Test with secret
    mock_settings.jwt_secret = "secret"

    # Mock connection with AsyncMock for async methods
    mock_conn = MagicMock()
    mock_conn.fetchval = AsyncMock(return_value="user-uuid")
    mock_conn.execute = AsyncMock(return_value=None)

    # Mock db.acquire() to return an async context manager
    mock_ctx = MagicMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_ctx.__aexit__.return_value = None

    mock_db.acquire.return_value = mock_ctx

    try:
        link = await _generate_magic_link(mock_settings, "test@example.com", "http://localhost", mock_db)
        if "token=" in link:
             print("✅ PASSED: _generate_magic_link generated link with token when secret is present")
        else:
             print("❌ FAILED: Link missing token")
             sys.exit(1)
    except Exception as e:
        print(f"❌ FAILED: Raised unexpected exception with valid secret: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_auth_security())
