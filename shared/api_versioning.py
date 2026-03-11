"""
API Versioning System

Comprehensive API versioning with support for multiple versions, version negotiation,
backward compatibility, and deprecation management.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import Request
from fastapi.responses import JSONResponse

from shared.logging_config import get_logger

logger = get_logger("sorce.api_versioning")


class VersionType(Enum):
    """Supported version types."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PREVIEW = "preview"


@dataclass
class APIVersion:
    """API version information."""

    major: int
    minor: int
    patch: int = 0
    prerelease: Optional[str] = None
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    supported_until: Optional[datetime] = None

    def __str__(self) -> str:
        """String representation of version."""
        version = f"v{self.major}.{self.minor}"
        if self.patch > 0:
            version += f".{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    def __eq__(self, other) -> bool:
        """Check version equality."""
        if not isinstance(other, APIVersion):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other) -> bool:
        """Check if this version is less than another."""
        if not isinstance(other, APIVersion):
            return False

        if self.major < other.major:
            return True
        elif self.major > other.major:
            return False

        if self.minor < other.minor:
            return True
        elif self.minor > other.minor:
            return False

        if self.patch < other.patch:
            return True
        elif self.patch > other.patch:
            return False

        # Handle prerelease comparison
        if self.prerelease and not other.prerelease:
            return False
        elif not self.prerelease and other.prerelease:
            return True
        elif self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease

        return False

    def __gt__(self, other) -> bool:
        """Check if this version is greater than another."""
        return not self.__eq__(other) and not self.__lt__(other)

    def __le__(self, other) -> bool:
        """Check if this version is less than or equal to another."""
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other) -> bool:
        """Check if this version is greater than or equal to another."""
        return self.__gt__(other) or self.__eq__(other)

    @classmethod
    def parse(cls, version_str: str) -> "APIVersion":
        """Parse version string."""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip("v")

        # Parse main version parts
        parts = version_str.split("-")
        main_version = parts[0]
        prerelease = parts[1] if len(parts) > 1 else None

        version_numbers = main_version.split(".")
        if len(version_numbers) < 2:
            raise ValueError(f"Invalid version format: {version_str}")

        major = int(version_numbers[0])
        minor = int(version_numbers[1])
        patch = int(version_numbers[2]) if len(version_numbers) > 2 else 0

        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease)


@dataclass
class VersionConfig:
    """Configuration for API versioning."""

    default_version: APIVersion = field(default_factory=lambda: APIVersion(1, 0, 0))
    supported_versions: List[APIVersion] = field(
        default_factory=lambda: [
            APIVersion(1, 0, 0),
            APIVersion(1, 1, 0),
            APIVersion(2, 0, 0),
        ]
    )
    deprecated_versions: List[APIVersion] = field(default_factory=list)
    version_header: str = "API-Version"
    version_param: str = "version"
    enable_version_negotiation: bool = True
    enable_backward_compatibility: bool = True
    enable_deprecation_warnings: bool = True
    default_deprecation_period_days: int = 90


@dataclass
class VersionedRoute:
    """Route with version information."""

    path: str
    endpoint: Callable
    version: APIVersion
    methods: List[str]
    deprecated: bool = False
    alternatives: Dict[str, str] = field(default_factory=dict)  # version -> path


class VersionManager:
    """Manages API versions and routing."""

    def __init__(self, config: Optional[VersionConfig] = None):
        self.config = config or VersionConfig()
        self.routes: Dict[APIVersion, List[VersionedRoute]] = {}
        self.middleware_handlers: Dict[str, Callable] = {}

        # Initialize route registry
        for version in self.config.supported_versions:
            self.routes[version] = []

    def register_route(
        self,
        path: str,
        endpoint: Callable,
        version: Optional[Union[str, APIVersion]] = None,
        methods: Optional[List[str]] = None,
        deprecated: bool = False,
        alternatives: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a versioned route."""
        if version is None:
            version = self.config.default_version
        elif isinstance(version, str):
            version = APIVersion.parse(version)

        # Validate version
        if version not in self.config.supported_versions:
            raise ValueError(f"Unsupported version: {version}")

        route = VersionedRoute(
            path=path,
            endpoint=endpoint,
            version=version,
            methods=methods or ["GET"],
            deprecated=deprecated,
            alternatives=alternatives or {},
        )

        self.routes[version].append(route)

    def get_route(
        self, path: str, method: str, version: Optional[APIVersion] = None
    ) -> Optional[VersionedRoute]:
        """Get route for specific version and path."""
        if version is None:
            version = self.config.default_version

        # Try exact match first
        for route in self.routes.get(version, []):
            if route.path == path and method in route.methods:
                return route

        # Try pattern matching
        for route in self.routes.get(version, []):
            if self._path_matches(route.path, path) and method in route.methods:
                return route

        return None

    def _path_matches(self, route_path: str, request_path: str) -> bool:
        """Check if request path matches route path pattern."""
        # Convert to regex pattern
        pattern = route_path.replace("{id}", "[^/]+")
        pattern = pattern.replace("{.*}", "[^/]+")
        pattern = f"^{pattern}$"

        return re.match(pattern, request_path) is not None

    def get_latest_version(self) -> APIVersion:
        """Get the latest supported version."""
        return max(self.config.supported_versions)

    def get_supported_versions(self) -> List[APIVersion]:
        """Get all supported versions."""
        return self.config.supported_versions.copy()

    def is_version_supported(self, version: APIVersion) -> bool:
        """Check if version is supported."""
        return version in self.config.supported_versions

    def is_version_deprecated(self, version: APIVersion) -> bool:
        """Check if version is deprecated."""
        return version.deprecated or version in self.config.deprecated_versions


class VersionNegotiation:
    """Handles API version negotiation."""

    def __init__(self, config: Optional[VersionConfig] = None):
        self.config = config or VersionConfig()

    def negotiate_version(
        self,
        accept_header: Optional[str],
        version_param: Optional[str],
        default_version: Optional[APIVersion] = None,
    ) -> APIVersion:
        """Negotiate version from request."""
        if default_version is None:
            default_version = self.config.default_version

        # Try version parameter first
        if version_param:
            try:
                param_version = APIVersion.parse(version_param)
                if self._is_version_acceptable(param_version):
                    return param_version
            except ValueError:
                logger.warning(f"Invalid version parameter: {version_param}")

        # Try Accept header
        if accept_header and self.config.enable_version_negotiation:
            return self._parse_accept_header(accept_header, default_version)

        return default_version

    def _is_version_acceptable(self, version: APIVersion) -> bool:
        """Check if version is acceptable."""
        version_manager = VersionManager(self.config)
        return version_manager.is_version_supported(version)

    def _parse_accept_header(
        self, accept_header: str, default_version: APIVersion
    ) -> APIVersion:
        """Parse Accept-Version header."""
        # Parse accept header
        versions = []
        for part in accept_header.split(","):
            part = part.strip()
            if not part:
                continue

            # Parse quality
            if ";" in part:
                version_part, quality_part = part.split(";")
                quality = float(quality_part.split("=")[1])
            else:
                version_part = part
                quality = 1.0

            try:
                version = APIVersion.parse(version_part.strip())
                versions.append((version, quality))
            except ValueError:
                continue

        # Sort by quality (descending)
        versions.sort(key=lambda x: x[1], reverse=True)

        # Find first acceptable version
        for version, quality in versions:
            if self._is_version_acceptable(version):
                return version

        return default_version


class VersionMiddleware:
    """Middleware for API versioning."""

    def __init__(self, config: Optional[VersionConfig] = None):
        self.config = config or VersionConfig()
        self.version_manager = VersionManager(config)
        self.negotiation = VersionNegotiation(config)

    async def __call__(self, request: Request, call_next):
        """Process request through versioning middleware."""
        # Extract version information
        version = self._extract_version(request)

        # Add version to request state
        request.state.version = version

        # Add version headers
        response = await call_next(request)

        # Add version headers to response
        response.headers[self.config.version_header] = str(version)

        # Add deprecation warning if needed (Sunset must be HTTP-date per RFC 8594)
        if self.config.enable_deprecation_warnings:
            version_manager = VersionManager(self.config)
            if version_manager.is_version_deprecated(version):
                response.headers["Deprecation"] = "true"
                sunset_date = (
                    version.sunset_date
                    or version.deprecation_date
                    or (
                        version_manager.get_latest_version().sunset_date
                        if version_manager.get_latest_version().sunset_date
                        else None
                    )
                )
                if sunset_date:
                    response.headers["Sunset"] = (
                        sunset_date.isoformat()
                        if hasattr(sunset_date, "isoformat")
                        else str(sunset_date)
                    )

        return response

    def _extract_version(self, request: Request) -> APIVersion:
        """Extract version from request."""
        # Try version parameter
        version_param = request.query_params.get(self.config.version_param)

        # Try Accept-Version header
        accept_header = request.headers.get("accept-version")

        return self.negotiation.negotiate_version(accept_header, version_param)


class VersionedAPIRouter:
    """Router with version support."""

    def __init__(self, config: Optional[VersionConfig] = None):
        self.config = config or VersionConfig()
        self.version_manager = VersionManager(config)
        self.routes: List[VersionedRoute] = []

    def add_route(
        self,
        path: str,
        endpoint: Callable,
        version: Optional[Union[str, APIVersion]] = None,
        methods: Optional[List[str]] = None,
        deprecated: bool = False,
        alternatives: Optional[Dict[str, str]] = None,
    ):
        """Add a versioned route."""
        self.version_manager.register_route(
            path=path,
            endpoint=endpoint,
            version=version,
            methods=methods,
            deprecated=deprecated,
            alternatives=alternatives,
        )
        self.routes.append(
            VersionedRoute(
                path=path,
                endpoint=endpoint,
                version=version or self.config.default_version,
                methods=methods or ["GET"],
                deprecated=deprecated,
                alternatives=alternatives or {},
            )
        )

    def get_route(
        self, path: str, method: str, version: Optional[APIVersion] = None
    ) -> Optional[VersionedRoute]:
        """Get route for specific version and path."""
        return self.version_manager.get_route(path, method, version)


# Decorators for versioning
def versioned(
    version: Optional[Union[str, APIVersion]] = None,
    methods: Optional[List[str]] = None,
    deprecated: bool = False,
    alternatives: Optional[Dict[str, str]] = None,
):
    """Decorator to mark endpoint with version."""

    def decorator(func):
        func._version = version
        func._version_methods = methods
        func._version_deprecated = deprecated
        func._version_alternatives = alternatives
        return func

    return decorator


def deprecated(
    since_version: Optional[Union[str, APIVersion]] = None,
    sunset_version: Optional[Union[str, APIVersion]] = None,
    alternatives: Optional[Dict[str, str]] = None,
):
    """Decorator to mark endpoint as deprecated."""

    def decorator(func):
        func._deprecated = True
        func._deprecated_since = since_version
        func._deprecated_sunset = sunset_version
        func._deprecated_alternatives = alternatives
        return func

    return decorator


class VersionCompatibilityHelper:
    """Helper for maintaining backward compatibility."""

    @staticmethod
    def adapt_response(
        response_data: Dict[str, Any],
        requested_version: APIVersion,
        current_version: APIVersion,
    ) -> Dict[str, Any]:
        """Adapt response data for version compatibility."""
        if requested_version == current_version:
            return response_data

        # Remove fields not available in older versions
        adapted_data = response_data.copy()

        # Example adaptation logic
        if requested_version.major < current_version.major:
            # Remove newer fields
            adapted_data = VersionCompatibilityHelper._remove_newer_fields(
                adapted_data, requested_version, current_version
            )
        elif requested_version.major > current_version.major:
            # Add default values for newer fields
            adapted_data = VersionCompatibilityHelper._add_default_fields(
                adapted_data, requested_version, current_version
            )

        return adapted_data

    @staticmethod
    def _remove_newer_fields(
        data: Dict[str, Any], requested_version: APIVersion, current_version: APIVersion
    ) -> Dict[str, Any]:
        """Remove fields not available in requested version."""
        # Example: Remove fields added in v2.0 for v1.x requests
        if requested_version.major < 2 and current_version.major >= 2:
            data.pop("new_field_v2", None)
            data.pop("another_field_v2", None)

        return data

    @staticmethod
    def _add_default_values(
        data: Dict[str, Any], requested_version: APIVersion, current_version: APIVersion
    ) -> Dict[str, Any]:
        """Add default values for fields not in older version."""
        # Example: Add default values for fields added in v2.0 for v1.x requests
        if requested_version.major < 2 and current_version.major >= 2:
            if "new_field_v2" not in data:
                data["new_field_v2"] = "default_value"
            if "another_field_v2" not in data:
                data["another_field_v2"] = None

        return data


class VersionDocumentation:
    """Generates version-specific API documentation."""

    def __init__(self, config: Optional[VersionConfig] = None):
        self.config = config or VersionConfig()
        self.version_manager = VersionManager(config)

    def generate_openapi(
        self,
        version: Optional[APIVersion] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate OpenAPI spec for specific version."""
        if version is None:
            version = self.config.default_version

        # Base OpenAPI spec
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": title or f"API v{version}",
                "description": description or f"API version {version}",
                "version": str(version),
                "deprecated": version.deprecated,
            },
            "servers": [
                {"url": f"/v{version.major}", "description": f"Version {version} API"}
            ],
        }

        # Add deprecation notice if applicable
        version_manager = VersionManager(self.config)
        if version_manager.is_version_deprecated(version):
            spec["info"]["x-deprecated"] = True
            sunset_date = (
                version.sunset_date
                or version.deprecation_date
                or (
                    version_manager.get_latest_version().sunset_date
                    if version_manager.get_latest_version().sunset_date
                    else None
                )
            )
            spec["info"]["x-sunset"] = (
                sunset_date.isoformat()
                if sunset_date and hasattr(sunset_date, "isoformat")
                else (str(sunset_date) if sunset_date else "")
            )

        return spec


# Utility functions
def parse_version(version_str: str) -> APIVersion:
    """Parse version string."""
    return APIVersion.parse(version_str)


def get_version_from_request(
    request: Request, config: Optional[VersionConfig] = None
) -> APIVersion:
    """Get version from request."""
    config = config or VersionConfig()
    negotiation = VersionNegotiation(config)

    version_param = request.query_params.get(config.version_param)
    accept_header = request.headers.get("accept-version")

    return negotiation.negotiate_version(accept_header, version_param)


def create_versioned_response(
    data: Dict[str, Any],
    version: APIVersion,
    request: Optional[Request] = None,
    config: Optional[VersionConfig] = None,
) -> JSONResponse:
    """Create a versioned response."""
    config = config or VersionConfig()

    response = JSONResponse(content=data)
    response.headers[config.version_header] = str(version)

    # Add deprecation warnings
    version_manager = VersionManager(config)
    if version_manager.is_version_deprecated(version):
        response.headers["Deprecation"] = "true"
        sunset_date = (
            version.sunset_date
            or version.deprecation_date
            or (
                version_manager.get_latest_version().sunset_date
                if version_manager.get_latest_version().sunset_date
                else None
            )
        )
        if sunset_date:
            response.headers["Sunset"] = (
                sunset_date.isoformat()
                if hasattr(sunset_date, "isoformat")
                else str(sunset_date)
            )

    # Add compatibility headers
    if request and config.enable_backward_compatibility:
        requested_version = getattr(request.state, "version", version)
        if requested_version != version:
            adapted_data = VersionCompatibilityHelper.adapt_response(
                data, requested_version, version
            )
            response = JSONResponse(content=adapted_data)
            response.headers[config.version_header] = str(version)

    return response


# Global instances
default_version_config = VersionConfig()
default_version_manager = VersionManager(default_version_config)
default_version_negotiation = VersionNegotiation(default_version_config)

# Version presets
V1_CONFIG = VersionConfig(
    default_version=APIVersion(1, 0, 0),
    supported_versions=[APIVersion(1, 0, 0)],
    enable_backward_compatibility=False,
    enable_deprecation_warnings=False,
)

V2_CONFIG = VersionConfig(
    default_version=APIVersion(2, 0, 0),
    supported_versions=[
        APIVersion(1, 0, 0),
        APIVersion(1, 1, 0),
        APIVersion(2, 0, 0),
    ],
    deprecated_versions=[APIVersion(1, 0, 0)],
    enable_backward_compatibility=True,
    enable_deprecation_warnings=True,
)

MULTI_VERSION_CONFIG = VersionConfig(
    default_version=APIVersion(1, 1, 0),
    supported_versions=[
        APIVersion(1, 0, 0),
        APIVersion(1, 1, 0),
        APIVersion(2, 0, 0),
        APIVersion(2, 1, 0, prerelease="alpha"),
    ],
    enable_backward_compatibility=True,
    enable_deprecation_warnings=True,
)
