"""
API Compression Middleware

Provides intelligent response compression with support for gzip, deflate, and brotli.
Includes content negotiation, compression thresholds, and performance monitoring.
"""

import gzip
import io
import re
import zlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.logging_config import get_logger

logger = get_logger("sorce.api_compression")


class CompressionType(Enum):
    """Supported compression algorithms."""

    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "br"
    IDENTITY = "identity"


@dataclass
class CompressionConfig:
    """Configuration for compression middleware."""

    min_size: int = 1024  # Minimum response size to compress (bytes)
    compressible_types: List[str] = None
    exclude_paths: List[str] = None
    exclude_content_types: List[str] = None
    quality_levels: Dict[str, int] = None
    enable_brotli: bool = True
    enable_gzip: bool = True
    enable_deflate: bool = True
    vary_header: bool = True

    def __post_init__(self):
        """Initialize default values."""
        if self.compressible_types is None:
            self.compressible_types = [
                "application/json",
                "application/javascript",
                "text/css",
                "text/html",
                "text/plain",
                "text/xml",
                "application/xml",
                "application/vnd.api+json",
                "application/hal+json",
            ]

        if self.exclude_paths is None:
            self.exclude_paths = [
                "/health",
                "/healthz",
                "/metrics",
                "/monitoring/health",
                "/favicon.ico",
                "/robots.txt",
            ]

        if self.exclude_content_types is None:
            self.exclude_content_types = [
                "image/",
                "video/",
                "audio/",
                "application/pdf",
                "application/zip",
                "application/octet-stream",
            ]

        if self.quality_levels is None:
            self.quality_levels = {
                CompressionType.GZIP.value: 6,
                CompressionType.DEFLATE.value: 6,
                CompressionType.BROTLI.value: 4,
            }


class CompressionStats:
    """Statistics for compression performance."""

    def __init__(self):
        self.total_responses = 0
        self.compressed_responses = 0
        self.total_original_bytes = 0
        self.total_compressed_bytes = 0
        self.compression_type_counts = {ctype.value: 0 for ctype in CompressionType}
        self.average_compression_ratio = 0.0

    def record_compression(
        self, original_size: int, compressed_size: int, compression_type: str
    ) -> None:
        """Record compression statistics."""
        self.total_responses += 1
        self.total_original_bytes += original_size
        self.total_compressed_bytes += compressed_size

        if compressed_size < original_size:
            self.compressed_responses += 1
            self.compression_type_counts[compression_type] += 1

        # Update average compression ratio
        if self.total_original_bytes > 0:
            self.average_compression_ratio = (
                self.total_original_bytes - self.total_compressed_bytes
            ) / self.total_original_bytes

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return {
            "total_responses": self.total_responses,
            "compressed_responses": self.compressed_responses,
            "compression_rate": (
                self.compressed_responses / self.total_responses
                if self.total_responses > 0
                else 0.0
            ),
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "average_compression_ratio": self.average_compression_ratio,
            "compression_type_counts": dict(self.compression_type_counts),
            "bytes_saved": self.total_original_bytes - self.total_compressed_bytes,
        }


class CompressionMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for response compression."""

    def __init__(self, app: ASGIApp, config: Optional[CompressionConfig] = None):
        super().__init__(app)
        self.config = config or CompressionConfig()
        self.stats = CompressionStats()

        # Pre-compile regex patterns for performance
        self._exclude_path_pattern = re.compile(
            "|".join(self.config.exclude_paths).replace("*", ".*")
        )
        self._exclude_content_type_pattern = re.compile(
            "|".join(self.config.exclude_content_types)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through compression middleware."""
        # Check if compression should be applied
        if not self._should_compress_request(request):
            response = await call_next(request)
            if response is None:
                return JSONResponse(
                    status_code=500,
                    content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "No response"}},
                )
            return response

        # Get original response - CRITICAL: never return None (causes "NoneType object is not callable" in ASGI)
        response = await call_next(request)
        if response is None:
            return JSONResponse(
                status_code=500,
                content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "No response"}},
            )

        # Check if response should be compressed
        if not self._should_compress_response(request, response):
            return response

        # Get preferred compression type
        compression_type = self._get_preferred_compression(request)

        if compression_type == CompressionType.IDENTITY:
            return response

        # Compress response
        compressed_response = await self._compress_response(response, compression_type)

        return compressed_response

    def _should_compress_request(self, request: Request) -> bool:
        """Check if request should be considered for compression."""
        # Check excluded paths
        if self._exclude_path_pattern.search(request.url.path):
            return False

        # Check Accept-Encoding header
        accept_encoding = request.headers.get("accept-encoding", "")
        if not accept_encoding:
            return False

        # Check if any supported encoding is accepted
        supported_encodings = []
        if self.config.enable_gzip and "gzip" in accept_encoding:
            supported_encodings.append("gzip")
        if self.config.enable_deflate and "deflate" in accept_encoding:
            supported_encodings.append("deflate")
        if self.config.enable_brotli and "br" in accept_encoding:
            supported_encodings.append("br")

        return bool(supported_encodings)

    def _should_compress_response(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed."""
        # Check response status code (don't compress certain status codes)
        if response.status_code in (204, 304):
            return False

        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.config.min_size:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").lower()

        # Check if content type is compressible
        if not any(
            compressible in content_type
            for compressible in self.config.compressible_types
        ):
            return False

        # Check if content type is excluded
        if self._exclude_content_type_pattern.search(content_type):
            return False

        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False

        return True

    def _get_preferred_compression(self, request: Request) -> CompressionType:
        """Get preferred compression type from Accept-Encoding header."""
        accept_encoding = request.headers.get("accept-encoding", "")

        # Parse Accept-Encoding header
        encodings = []
        for encoding in accept_encoding.split(","):
            encoding = encoding.strip()
            if not encoding:
                continue

            # Parse quality parameter
            parts = encoding.split(";")
            encoding_name = parts[0].strip()
            quality = 1.0

            for part in parts[1:]:
                if part.strip().startswith("q="):
                    try:
                        quality = float(part.split("=")[1].strip())
                    except (ValueError, IndexError):
                        continue

            encodings.append((encoding_name, quality))

        # Sort by quality (descending)
        encodings.sort(key=lambda x: x[1], reverse=True)

        # Find first supported encoding
        for encoding_name, quality in encodings:
            if quality <= 0:
                continue

            if encoding_name == "br" and self.config.enable_brotli:
                return CompressionType.BROTLI
            elif encoding_name == "gzip" and self.config.enable_gzip:
                return CompressionType.GZIP
            elif encoding_name == "deflate" and self.config.enable_deflate:
                return CompressionType.DEFLATE
            elif encoding_name == "identity":
                return CompressionType.IDENTITY

        return CompressionType.IDENTITY

    async def _compress_response(
        self, response: Response, compression_type: CompressionType
    ) -> Response:
        """Compress response using specified algorithm."""
        try:
            # Get response body
            if hasattr(response, "body"):
                body = response.body
            elif hasattr(response, "content"):
                body = response.content
            else:
                # For streaming responses, don't compress
                return response

            # Check if body is bytes
            if not isinstance(body, bytes):
                if isinstance(body, str):
                    body = body.encode("utf-8")
                else:
                    # Convert to JSON string then bytes
                    import json

                    body = json.dumps(body).encode("utf-8")

            original_size = len(body)

            # Compress body
            if compression_type == CompressionType.GZIP:
                compressed_body = self._gzip_compress(body)
                encoding_name = "gzip"
            elif compression_type == CompressionType.DEFLATE:
                compressed_body = self._deflate_compress(body)
                encoding_name = "deflate"
            elif compression_type == CompressionType.BROTLI:
                compressed_body = await self._brotli_compress(body)
                encoding_name = "br"
            else:
                return response

            compressed_size = len(compressed_body)

            # Only use compression if it actually reduces size
            if compressed_size >= original_size:
                return response

            # Record statistics
            self.stats.record_compression(
                original_size, compressed_size, compression_type.value
            )

            # Create new response - always use Response for compressed bytes
            # (JSONResponse expects dict/list, not raw bytes)
            compressed_response = Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                background=response.background,
            )

            # Set compression headers
            compressed_response.headers["content-encoding"] = encoding_name
            compressed_response.headers["content-length"] = str(compressed_size)

            # Add Vary header if configured
            if self.config.vary_header:
                existing_vary = compressed_response.headers.get("vary", "")
                if "accept-encoding" not in existing_vary.lower():
                    if existing_vary:
                        compressed_response.headers["vary"] = (
                            f"{existing_vary}, Accept-Encoding"
                        )
                    else:
                        compressed_response.headers["vary"] = "Accept-Encoding"

            # Log compression
            logger.debug(
                f"Compressed response: {original_size} -> {compressed_size} bytes "
                f"({encoding_name}, {((original_size - compressed_size) / original_size * 100):.1f}% reduction)",
                extra={
                    "compression_type": encoding_name,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": (original_size - compressed_size)
                    / original_size,
                },
            )

            return compressed_response

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return response

    def _gzip_compress(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        quality = self.config.quality_levels.get(CompressionType.GZIP.value, 6)

        # Create gzip buffer
        buffer = io.BytesIO()

        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=quality) as gz_file:
            gz_file.write(data)

        return buffer.getvalue()

    def _deflate_compress(self, data: bytes) -> bytes:
        """Compress data using deflate."""
        quality = self.config.quality_levels.get(CompressionType.DEFLATE.value, 6)

        # Convert quality to zlib level (0-9)
        zlib_level = max(0, min(9, int(quality * 9 / 6)))

        # Compress with deflate
        compressed = zlib.compress(data, level=zlib_level)

        # Remove zlib header and checksum for raw deflate
        return compressed[2:-4] if len(compressed) > 6 else compressed

    async def _brotli_compress(self, data: bytes) -> bytes:
        """Compress data using brotli."""
        try:
            import brotli

            quality = self.config.quality_levels.get(CompressionType.BROTLI.value, 4)

            # Convert quality to brotli level (0-11)
            brotli_level = max(0, min(11, int(quality * 11 / 6)))

            return brotli.compress(data, quality=brotli_level)

        except ImportError:
            logger.warning("Brotli compression not available, falling back to gzip")
            return self._gzip_compress(data)

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return self.stats.get_stats()


class SmartCompressionMiddleware(CompressionMiddleware):
    """Enhanced compression middleware with smart features."""

    def __init__(self, app: ASGIApp, config: Optional[CompressionConfig] = None):
        super().__init__(app, config)
        self._compression_history = {}  # Track compression effectiveness per content type
        self._adaptive_quality = True  # Enable adaptive quality adjustment

    def _should_compress_response(self, request: Request, response: Response) -> bool:
        """Enhanced response compression check with adaptive logic."""
        # Basic checks from parent
        if not super()._should_compress_response(request, response):
            return False

        # Adaptive logic: check historical compression effectiveness
        content_type = response.headers.get("content-type", "").lower()

        # Find the most specific content type category
        compressible_category = None
        for compressible in self.config.compressible_types:
            if compressible in content_type:
                compressible_category = compressible
                break

        if compressible_category and compressible_category in self._compression_history:
            history = self._compression_history[compressible_category]

            # Skip compression if historically ineffective
            if history["attempts"] > 10 and history["avg_compression_ratio"] < 0.1:
                logger.debug(
                    f"Skipping compression for {compressible_category} "
                    f"(historically ineffective: {history['avg_compression_ratio']:.2f})"
                )
                return False

        return True

    async def _compress_response(
        self, response: Response, compression_type: CompressionType
    ) -> Response:
        """Enhanced compression with adaptive quality and learning."""
        try:
            # Get content type for tracking
            content_type = response.headers.get("content-type", "").lower()

            # Find compressible category
            compressible_category = None
            for compressible in self.config.compressible_types:
                if compressible in content_type:
                    compressible_category = compressible
                    break

            # Adaptive quality adjustment
            if self._adaptive_quality and compressible_category:
                original_quality = self.config.quality_levels.get(
                    compression_type.value, 6
                )
                adjusted_quality = self._adjust_quality(
                    compressible_category, compression_type
                )
                self.config.quality_levels[compression_type.value] = adjusted_quality

            # Compress response
            compressed_response = await super()._compress_response(
                response, compression_type
            )

            # Update compression history
            if compressible_category and compressed_response.headers.get(
                "content-encoding"
            ):
                original_size = len(response.body) if hasattr(response, "body") else 0
                compressed_size = (
                    len(compressed_response.body)
                    if hasattr(compressed_response, "body")
                    else 0
                )

                if original_size > 0:
                    compression_ratio = (
                        original_size - compressed_size
                    ) / original_size
                    self._update_compression_history(
                        compressible_category, compression_ratio
                    )

            # Restore original quality
            if self._adaptive_quality and compressible_category:
                self.config.quality_levels[compression_type.value] = original_quality

            return compressed_response

        except Exception as e:
            logger.error(f"Smart compression failed: {e}")
            return response

    def _adjust_quality(
        self, content_type: str, compression_type: CompressionType
    ) -> int:
        """Adjust compression quality based on historical performance."""
        if content_type not in self._compression_history:
            return self.config.quality_levels.get(compression_type.value, 6)

        history = self._compression_history[content_type]

        # If compression is very effective, use higher quality
        if history["avg_compression_ratio"] > 0.5:
            return min(9, self.config.quality_levels.get(compression_type.value, 6) + 1)

        # If compression is barely effective, use lower quality
        elif history["avg_compression_ratio"] < 0.2:
            return max(1, self.config.quality_levels.get(compression_type.value, 6) - 1)

        return self.config.quality_levels.get(compression_type.value, 6)

    def _update_compression_history(
        self, content_type: str, compression_ratio: float
    ) -> None:
        """Update compression effectiveness history."""
        if content_type not in self._compression_history:
            self._compression_history[content_type] = {
                "attempts": 0,
                "total_compression_ratio": 0.0,
                "avg_compression_ratio": 0.0,
            }

        history = self._compression_history[content_type]
        history["attempts"] += 1
        history["total_compression_ratio"] += compression_ratio
        history["avg_compression_ratio"] = (
            history["total_compression_ratio"] / history["attempts"]
        )

    def get_compression_history(self) -> Dict[str, Any]:
        """Get compression effectiveness history."""
        return dict(self._compression_history)


# Global instances
default_compression_middleware = CompressionMiddleware
smart_compression_middleware = SmartCompressionMiddleware


# Utility functions
def create_compression_config(
    min_size: int = 1024,
    enable_brotli: bool = True,
    enable_gzip: bool = True,
    enable_deflate: bool = True,
    quality_levels: Optional[Dict[str, int]] = None,
) -> CompressionConfig:
    """Create compression configuration."""
    return CompressionConfig(
        min_size=min_size,
        enable_brotli=enable_brotli,
        enable_gzip=enable_gzip,
        enable_deflate=enable_deflate,
        quality_levels=quality_levels,
    )


def get_compression_stats(middleware: CompressionMiddleware) -> Dict[str, Any]:
    """Get compression statistics from middleware."""
    return middleware.get_stats()


def reset_compression_stats(middleware: CompressionMiddleware) -> None:
    """Reset compression statistics."""
    middleware.stats = CompressionStats()
