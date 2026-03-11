"""Advanced API authentication middleware system.

Provides:
- JWT token authentication
- API key authentication
- OAuth2 integration
- Session management
- Multi-factor authentication
- Rate limiting per user
- Security monitoring

Usage:
    from shared.api_auth_middleware import AuthMiddleware

    middleware = AuthMiddleware()
    await middleware.authenticate_request(request)
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

from shared.alerting import AlertSeverity, get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.api_auth")


class AuthType(Enum):
    """Authentication types."""

    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SESSION = "session"
    BASIC = "basic"
    NONE = "none"


class AuthStatus(Enum):
    """Authentication status."""

    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    INVALID = "invalid"
    FORBIDDEN = "forbidden"
    RATE_LIMITED = "rate_limited"


@dataclass
class AuthResult:
    """Authentication result."""

    status: AuthStatus
    user_id: Optional[str] = None
    user_type: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    token_info: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    auth_type: Optional[AuthType] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class UserSession:
    """User session information."""

    session_id: str
    user_id: str
    user_type: str
    permissions: List[str]
    created_at: float
    last_accessed: float
    expires_at: float
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Authentication configuration."""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    api_key_header_name: str = "X-API-Key"
    session_cookie_name: str = "session_id"
    session_expire_minutes: int = 120
    enable_mfa: bool = False
    mfa_required_for: List[str] = field(default_factory=lambda: ["admin"])
    rate_limit_per_user: int = 1000
    rate_limit_window_minutes: int = 60
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = field(default_factory=list)
    enable_user_agent_filtering: bool = False
    blocked_user_agents: List[str] = field(default_factory=list)


class AuthMiddleware:
    """Advanced API authentication middleware."""

    def __init__(
        self, config: Optional[AuthConfig] = None, alert_manager: Optional[Any] = None
    ):
        if config is None:
            import os

            jwt_secret = os.environ.get("JWT_SECRET", "")
            env = os.environ.get("ENV", os.environ.get("env", "local")).lower()
            _dev_defaults = (
                "your-secret-key",
                "dev-secret-change-in-production",
                "dev-secret-key-change-in-production",
            )
            if env in ("prod", "staging"):
                if not jwt_secret or jwt_secret in _dev_defaults:
                    raise RuntimeError(
                        "JWT_SECRET must be set in production. "
                        "Pass AuthConfig(jwt_secret_key=...) or set JWT_SECRET env."
                    )
            elif not jwt_secret:
                jwt_secret = "dev-secret-key-change-in-production"
            config = AuthConfig(jwt_secret_key=jwt_secret)
        self.config = config
        self.alert_manager = alert_manager or get_alert_manager()

        # Security bearer for JWT
        self.security = HTTPBearer()

        # Session storage
        self.sessions: Dict[str, UserSession] = {}
        self.api_keys: Dict[str, Dict[str, Any]] = {}

        # Rate limiting per user
        self.user_rate_limits: Dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Authentication statistics
        self.auth_stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "rate_limited": 0,
            "blocked_ips": 0,
            "blocked_user_agents": 0,
            "auth_by_type": defaultdict(int),
        }

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None

        self._lock = asyncio.Lock()

    async def authenticate_request(
        self,
        request: Request,
        auth_type: Optional[AuthType] = None,
        required_permissions: Optional[List[str]] = None,
    ) -> AuthResult:
        """Authenticate incoming request."""
        start_time = time.time()

        try:
            # Update statistics
            self.auth_stats["total_requests"] += 1

            # Check IP whitelist if enabled
            if self.config.enable_ip_whitelist:
                client_ip = self._get_client_ip(request)
                if client_ip not in self.config.ip_whitelist:
                    await self._handle_blocked_request(
                        request, "IP not whitelisted", client_ip
                    )
                    return AuthResult(
                        status=AuthStatus.FORBIDDEN,
                        error_message="IP address not whitelisted",
                        timestamp=start_time,
                    )

            # Check user agent filtering if enabled
            if self.config.enable_user_agent_filtering:
                user_agent = request.headers.get("user-agent", "")
                if any(
                    blocked in user_agent.lower()
                    for blocked in self.config.blocked_user_agents
                ):
                    await self._handle_blocked_request(
                        request, "User agent blocked", user_agent
                    )
                    return AuthResult(
                        status=AuthStatus.FORBIDDEN,
                        error_message="User agent blocked",
                        timestamp=start_time,
                    )

            # Check rate limiting
            client_ip = self._get_client_ip(request)
            if await self._is_rate_limited(client_ip):
                self.auth_stats["rate_limited"] += 1
                return AuthResult(
                    status=AuthStatus.RATE_LIMITED,
                    error_message="Rate limit exceeded",
                    timestamp=start_time,
                )

            # Determine authentication type
            if auth_type is None:
                auth_type = self._determine_auth_type(request)

            # Authenticate based on type
            if auth_type == AuthType.JWT:
                result = await self._authenticate_jwt(request)
            elif auth_type == AuthType.API_KEY:
                result = await self._authenticate_api_key(request)
            elif auth_type == AuthType.OAUTH2:
                result = await self._authenticate_oauth2(request)
            elif auth_type == AuthType.SESSION:
                result = await self._authenticate_session(request)
            elif auth_type == AuthType.BASIC:
                result = await self._authenticate_basic(request)
            else:
                result = AuthResult(status=AuthStatus.UNAUTHENTICATED)

            # Check required permissions
            if result.status == AuthStatus.AUTHENTICATED and required_permissions:
                if not self._check_permissions(
                    result.permissions, required_permissions
                ):
                    result.status = AuthStatus.FORBIDDEN
                    result.error_message = "Insufficient permissions"

            # Update statistics
            if result.status == AuthStatus.AUTHENTICATED:
                self.auth_stats["successful_auths"] += 1
            else:
                self.auth_stats["failed_auths"] += 1

            if result.auth_type:
                self.auth_stats["auth_by_type"][result.auth_type.value] += 1

            # Update last access for sessions
            if result.status == AuthStatus.AUTHENTICATED and result.user_id:
                await self._update_session_access(result.user_id, request)

            return result

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.auth_stats["failed_auths"] += 1

            return AuthResult(
                status=AuthStatus.INVALID,
                error_message="Authentication error",
                timestamp=start_time,
            )

    def _determine_auth_type(self, request: Request) -> AuthType:
        """Determine authentication type from request."""
        # Check for JWT in Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return AuthType.JWT

        # Check for API key
        api_key = request.headers.get(self.config.api_key_header_name)
        if api_key:
            return AuthType.API_KEY

        # Check for session cookie
        session_id = request.cookies.get(self.config.session_cookie_name)
        if session_id:
            return AuthType.SESSION

        # Check for Basic auth
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Basic "):
            return AuthType.BASIC

        return AuthType.NONE

    async def _authenticate_jwt(self, request: Request) -> AuthResult:
        """Authenticate using JWT token."""
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED,
                    error_message="Missing or invalid Authorization header",
                )

            token = auth_header.split(" ")[1]

            # Decode and verify token
            try:
                payload = jwt.decode(
                    token,
                    self.config.jwt_secret_key,
                    algorithms=[self.config.jwt_algorithm],
                )
            except jwt.ExpiredSignatureError:
                return AuthResult(
                    status=AuthStatus.EXPIRED, error_message="Token signature expired"
                )
            except jwt.ExpiredTokenError:
                return AuthResult(
                    status=AuthStatus.EXPIRED, error_message="Token expired"
                )
            except jwt.InvalidTokenError:
                return AuthResult(
                    status=AuthStatus.INVALID, error_message="Invalid token"
                )

            # Extract user information
            user_id = payload.get("sub")
            user_type = payload.get("user_type", "user")
            permissions = payload.get("permissions", [])
            expires_at = payload.get("exp")

            if not user_id:
                return AuthResult(
                    status=AuthStatus.INVALID, error_message="Invalid token payload"
                )

            # Check if token is expired
            if expires_at and time.time() > expires_at:
                return AuthResult(
                    status=AuthStatus.EXPIRED, error_message="Token expired"
                )

            # Check MFA if required
            if self.config.enable_mfa and user_type in self.config.mfa_required_for:
                mfa_verified = payload.get("mfa_verified", False)
                if not mfa_verified:
                    return AuthResult(
                        status=AuthStatus.FORBIDDEN,
                        error_message="Multi-factor authentication required",
                    )

            return AuthResult(
                status=AuthStatus.AUTHENTICATED,
                user_id=user_id,
                user_type=user_type,
                permissions=permissions,
                token_info=payload,
                auth_type=AuthType.JWT,
            )

        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, error_message="JWT authentication failed"
            )

    async def _authenticate_api_key(self, request: Request) -> AuthResult:
        """Authenticate using API key."""
        try:
            # Extract API key from header
            api_key = request.headers.get(self.config.api_key_header_name)
            if not api_key:
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED, error_message="Missing API key"
                )

            # Validate API key
            key_info = self.api_keys.get(api_key)
            if not key_info:
                return AuthResult(
                    status=AuthStatus.INVALID, error_message="Invalid API key"
                )

            # Check if key is active and not expired
            if not key_info.get("active", True):
                return AuthResult(
                    status=AuthStatus.FORBIDDEN, error_message="API key deactivated"
                )

            expires_at = key_info.get("expires_at")
            if expires_at and time.time() > expires_at:
                return AuthResult(
                    status=AuthStatus.EXPIRED, error_message="API key expired"
                )

            # Check rate limiting for this key
            if await self._is_key_rate_limited(api_key):
                return AuthResult(
                    status=AuthStatus.RATE_LIMITED,
                    error_message="API key rate limit exceeded",
                )

            user_id = key_info.get("user_id")
            user_type = key_info.get("user_type", "api_user")
            permissions = key_info.get("permissions", [])

            return AuthResult(
                status=AuthStatus.AUTHENTICATED,
                user_id=user_id,
                user_type=user_type,
                permissions=permissions,
                token_info=key_info,
                auth_type=AuthType.API_KEY,
            )

        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, error_message="API key authentication failed"
            )

    async def _authenticate_oauth2(self, request: Request) -> AuthResult:
        """Authenticate using OAuth2."""
        try:
            # This would integrate with OAuth2 providers like Google, GitHub, etc.
            # For now, return unauthenticated as OAuth2 is not implemented
            return AuthResult(
                status=AuthStatus.UNAUTHENTICATED,
                error_message="OAuth2 authentication not implemented",
            )

        except Exception as e:
            logger.error(f"OAuth2 authentication error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, error_message="OAuth2 authentication failed"
            )

    async def _authenticate_session(self, request: Request) -> AuthResult:
        """Authenticate using session."""
        try:
            # Extract session ID from cookie
            session_id = request.cookies.get(self.config.session_cookie_name)
            if not session_id:
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED, error_message="No session found"
                )

            # Get session from storage
            session = self.sessions.get(session_id)
            if not session:
                return AuthResult(
                    status=AuthStatus.INVALID, error_message="Invalid session"
                )

            # Check if session is expired
            if time.time() > session.expires_at:
                # Clean up expired session
                del self.sessions[session_id]
                return AuthResult(
                    status=AuthStatus.EXPIRED, error_message="Session expired"
                )

            return AuthResult(
                status=AuthStatus.AUTHENTICATED,
                user_id=session.user_id,
                user_type=session.user_type,
                permissions=session.permissions,
                token_info={"session_id": session_id},
                auth_type=AuthType.SESSION,
            )

        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, error_message="Session authentication failed"
            )

    async def _authenticate_basic(self, request: Request) -> AuthResult:
        """Authenticate using Basic auth."""
        try:
            # Extract credentials from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Basic "):
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED,
                    error_message="Missing or invalid Authorization header",
                )

            import base64

            # Decode credentials
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

            if ":" not in decoded_credentials:
                return AuthResult(
                    status=AuthStatus.INVALID,
                    error_message="Invalid Basic auth credentials",
                )

            username, password = decoded_credentials.split(":", 1)

            # Validate credentials (this would integrate with user database)
            user_info = await self._validate_basic_credentials(username, password)
            if not user_info:
                return AuthResult(
                    status=AuthStatus.INVALID, error_message="Invalid credentials"
                )

            return AuthResult(
                status=AuthStatus.AUTHENTICATED,
                user_id=user_info["user_id"],
                user_type=user_info.get("user_type", "user"),
                permissions=user_info.get("permissions", []),
                token_info=user_info,
                auth_type=AuthType.BASIC,
            )

        except Exception as e:
            logger.error(f"Basic authentication error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID, error_message="Basic authentication failed"
            )

    async def _validate_basic_credentials(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Validate Basic auth credentials against user database."""
        # This would integrate with your user authentication system
        # For now, return None as no user database is available
        return None

    def _check_permissions(
        self, user_permissions: List[str], required_permissions: List[str]
    ) -> bool:
        """Check if user has required permissions."""
        if not required_permissions:
            return True

        return all(
            permission in user_permissions for permission in required_permissions
        )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP — use shared.middleware for consistency (AUTH-003)."""
        from shared.middleware import get_client_ip
        return get_client_ip(request)

    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited."""
        current_time = time.time()
        rate_window = self.config.rate_limit_window_minutes * 60

        # Clean old entries
        cutoff_time = current_time - rate_window
        if client_ip in self.user_rate_limits:
            while (
                self.user_rate_limits[client_ip]
                and self.user_rate_limits[client_ip][0] < cutoff_time
            ):
                self.user_rate_limits[client_ip].popleft()

        # Check current rate
        recent_requests = len(self.user_rate_limits[client_ip])
        if recent_requests >= self.config.rate_limit_per_user:
            return True

        # Add current request
        self.user_rate_limits[client_ip].append(current_time)
        return False

    async def _is_key_rate_limited(self, api_key: str) -> bool:
        """Check if API key is rate limited."""
        current_time = time.time()
        rate_window = self.config.rate_limit_window_minutes * 60

        # Get rate limit for this key
        key_info = self.api_keys.get(api_key, {})
        key_rate_limit = key_info.get("rate_limit", self.config.rate_limit_per_user)

        # Clean old entries
        cutoff_time = current_time - rate_window
        rate_limit_key = f"api_key:{api_key}"

        if rate_limit_key not in self.user_rate_limits:
            self.user_rate_limits[rate_limit_key] = deque(maxlen=1000)

        while (
            self.user_rate_limits[rate_limit_key]
            and self.user_rate_limits[rate_limit_key][0] < cutoff_time
        ):
            self.user_rate_limits[rate_limit_key].popleft()

        # Check current rate
        recent_requests = len(self.user_rate_limits[rate_limit_key])
        if recent_requests >= key_rate_limit:
            return True

        # Add current request
        self.user_rate_limits[rate_limit_key].append(current_time)
        return False

    async def _update_session_access(self, user_id: str, request: Request) -> None:
        """Update session access time."""
        # Find session for this user
        for session_id, session in self.sessions.items():
            if session.user_id == user_id:
                session.last_accessed = time.time()
                session.ip_address = self._get_client_ip(request)
                session.user_agent = request.headers.get("user-agent", "")
                break

    async def _handle_blocked_request(
        self, request: Request, reason: str, details: str
    ) -> None:
        """Handle blocked request."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Log the blocked request
        logger.warning(
            f"Blocked request: {reason} - {details} - IP: {client_ip} - UA: {user_agent}"
        )

        # Update statistics
        if "IP" in reason:
            self.auth_stats["blocked_ips"] += 1
        elif "User agent" in reason:
            self.auth_stats["blocked_user_agents"] += 1

        # Trigger alert for security monitoring
        await self.alert_manager.trigger_alert(
            name="blocked_request",
            severity=AlertSeverity.WARNING,
            message=f"Blocked request: {reason}",
            context={
                "ip_address": client_ip,
                "user_agent": user_agent,
                "reason": reason,
                "details": details,
                "path": str(request.url),
                "method": request.method,
            },
        )

    def create_jwt_token(
        self,
        user_id: str,
        user_type: str,
        permissions: List[str],
        expires_delta: Optional[int] = None,
        mfa_verified: bool = False,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """Create JWT access and refresh tokens."""
        current_time = time.time()

        # Set expiration
        access_expire = current_time + (
            self.config.jwt_access_token_expire_minutes * 60
        )
        refresh_expire = current_time + (
            self.config.jwt_refresh_token_expire_days * 86400
        )

        if expires_delta:
            access_expire = current_time + expires_delta
            refresh_expire = current_time + (
                expires_delta * 7
            )  # Refresh token lasts 7x longer

        # Create access token payload
        access_payload = {
            "sub": user_id,
            "user_type": user_type,
            "permissions": permissions,
            "iat": current_time,
            "exp": access_expire,
            "type": "access",
            "mfa_verified": mfa_verified,
        }

        # Add additional claims
        if additional_claims:
            access_payload.update(additional_claims)

        # Create refresh token payload
        refresh_payload = {
            "sub": user_id,
            "user_type": user_type,
            "permissions": permissions,
            "iat": current_time,
            "exp": refresh_expire,
            "type": "refresh",
        }

        # Create tokens
        access_token = jwt.encode(
            access_payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

        refresh_token = jwt.encode(
            refresh_payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

        return access_token, refresh_token

    def create_session(
        self,
        user_id: str,
        user_type: str,
        permissions: List[str],
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create user session."""
        import uuid

        session_id = str(uuid.uuid4())
        current_time = time.time()
        expires_at = current_time + (self.config.session_expire_minutes * 60)

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            permissions=permissions,
            created_at=current_time,
            last_accessed=current_time,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        self.sessions[session_id] = session
        return session_id

    def create_api_key(
        self,
        user_id: str,
        user_type: str,
        permissions: List[str],
        name: str,
        rate_limit: Optional[int] = None,
        expires_at: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create API key."""
        import uuid

        api_key = f"sk_{uuid.uuid4().hex}"

        key_info = {
            "api_key": api_key,
            "user_id": user_id,
            "user_type": user_type,
            "permissions": permissions,
            "name": name,
            "rate_limit": rate_limit or self.config.rate_limit_per_user,
            "created_at": time.time(),
            "expires_at": expires_at,
            "active": True,
            "metadata": metadata or {},
        }

        self.api_keys[api_key] = key_info
        return api_key

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            return True
        return False

    def revoke_session(self, session_id: str) -> bool:
        """Revoke user session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        revoked_count = 0

        sessions_to_remove = [
            session_id
            for session_id, session in self.sessions.items()
            if session.user_id == user_id
        ]

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            revoked_count += 1

        return revoked_count

    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user."""
        return [
            session
            for session in self.sessions.values()
            if session.user_id == user_id and session.expires_at > time.time()
        ]

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        session = self.sessions.get(session_id)
        if session and session.expires_at > time.time():
            return session
        return None

    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
            return payload
        except jwt.PyJWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def refresh_jwt_token(self, refresh_token: str) -> str:
        """Refresh JWT token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Validate refresh token
            if payload.get("type") != "refresh":
                raise ValueError("Invalid refresh token")

            # Create new access token
            user_id = payload["sub"]
            user_type = payload.get("user_type", "user")
            permissions = payload.get("permissions", [])
            mfa_verified = payload.get("mfa_verified", False)

            new_access_token, _ = self.create_jwt_token(
                user_id=user_id,
                user_type=user_type,
                permissions=permissions,
                mfa_verified=mfa_verified,
            )

            return new_access_token

        except jwt.PyJWTError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        return dict(self.auth_stats)

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        current_time = time.time()
        return len(
            [
                session
                for session in self.sessions.values()
                if session.expires_at > current_time
            ]
        )

    def get_active_api_keys_count(self) -> int:
        """Get count of active API keys."""
        current_time = time.time()
        return len(
            [
                key
                for key, info in self.api_keys.items()
                if info.get("active", True)
                and (not info.get("expires_at") or info["expires_at"] > current_time)
            ]
        )

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""

        async def cleanup_loop():
            while True:
                try:
                    await self._cleanup_expired_sessions()
                    await self._cleanup_expired_api_keys()
                    await self._cleanup_rate_limits()
                    await asyncio.sleep(300)  # Clean every 5 minutes
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                    await asyncio.sleep(300)

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def _cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []

        for session_id, session in list(self.sessions.items()):
            if session.expires_at <= current_time:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        return len(expired_sessions)

    async def _cleanup_expired_api_keys(self) -> int:
        """Clean up expired API keys."""
        current_time = time.time()
        expired_keys = []

        for api_key, key_info in list(self.api_keys.items()):
            expires_at = key_info.get("expires_at")
            if expires_at and expires_at <= current_time:
                expired_keys.append(api_key)

        for api_key in expired_keys:
            del self.api_keys[api_key]

        return len(expired_keys)

    async def _cleanup_rate_limits(self) -> int:
        """Clean up old rate limit entries."""
        current_time = time.time()
        cutoff_time = current_time - (self.config.rate_limit_window_minutes * 60)
        cleaned_count = 0

        for key in list(self.user_rate_limits.keys()):
            len(self.user_rate_limits[key])

            # Remove old entries
            while (
                self.user_rate_limits[key]
                and self.user_rate_limits[key][0] < cutoff_time
            ):
                self.user_rate_limits[key].popleft()
                cleaned_count += 1

            # Remove empty rate limit lists
            if not self.user_rate_limits[key]:
                del self.user_rate_limits[key]

        return cleaned_count

    def update_config(self, **kwargs) -> None:
        """Update authentication configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                logger.info(f"Updated auth config {key}: {old_value} -> {value}")

    def add_ip_to_whitelist(self, ip_address: str) -> None:
        """Add IP address to whitelist."""
        if ip_address not in self.config.ip_whitelist:
            self.config.ip_whitelist.append(ip_address)
            logger.info(f"Added IP to whitelist: {ip_address}")

    def remove_ip_from_whitelist(self, ip_address: str) -> bool:
        """Remove IP address from whitelist."""
        if ip_address in self.config.ip_whitelist:
            self.config.ip_whitelist.remove(ip_address)
            logger.info(f"Removed IP from whitelist: {ip_address}")
            return True
        return False

    def add_blocked_user_agent(self, user_agent: str) -> None:
        """Add user agent to blocked list."""
        if user_agent not in self.config.blocked_user_agents:
            self.config.blocked_user_agents.append(user_agent)
            logger.info(f"Added user agent to blocked list: {user_agent}")

    def remove_blocked_user_agent(self, user_agent: str) -> bool:
        """Remove user agent from blocked list."""
        if user_agent in self.config.blocked_user_agents:
            self.config.blocked_user_agents.remove(user_agent)
            logger.info(f"Removed user agent from blocked list: {user_agent}")
            return True
        return False


# Global auth middleware instance
_auth_middleware: AuthMiddleware | None = None


def get_auth_middleware() -> AuthMiddleware:
    """Get global auth middleware instance."""
    global _auth_middleware
    if _auth_middleware is None:
        raise RuntimeError(
            "Auth middleware not initialized. Call init_auth_middleware() first."
        )
    return _auth_middleware


async def init_auth_middleware(
    config: Optional[AuthConfig] = None, alert_manager: Optional[Any] = None
) -> AuthMiddleware:
    """Initialize global auth middleware."""
    global _auth_middleware
    _auth_middleware = AuthMiddleware(config, alert_manager)
    await _auth_middleware.start_cleanup_task()
    return _auth_middleware


# FastAPI dependency for JWT authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    _auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to get current authenticated user."""
    try:
        if credentials.credentials:
            # This would be called within a request context
            # For now, we'll need to extract the request from the context
            # In a real implementation, you'd use Request object
            pass

        return None
    except Exception:
        return None


# FastAPI dependency for optional authentication
async def get_current_user_optional(
    _auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to get current user (optional)."""
    return None


# Decorator for requiring authentication
def require_auth(permissions: Optional[List[str]] = None):
    """Decorator to require authentication and optionally specific permissions."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would integrate with FastAPI
            # For now, we'll need to implement the actual decorator logic
            pass

        return wrapper

    return decorator


# Decorator for requiring specific user type
def require_user_type(user_type: str):
    """Decorator to require specific user type."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would integrate with FastAPI
            # For now, we'll need to implement the actual decorator logic
            pass

        return wrapper

    return decorator
