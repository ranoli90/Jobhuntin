"""Advanced image processing with resizing, compression, and optimization.

Provides:
- Multi-format image resizing (JPEG, PNG, WebP)
- Intelligent compression based on content
- Thumbnail generation
- Format conversion
- EXIF data handling
- Performance optimization

Usage:
    from shared.image_processor import ImageProcessor

    processor = ImageProcessor()
    thumbnail = await processor.create_thumbnail(image_data, 200, 200)
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from shared.logging_config import get_logger

logger = get_logger("sorce.image_processor")

# Try to import Pillow with fallback
try:
    from PIL import Image, ImageOps, ImageEnhance, ExifTags  # noqa: F401

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available - limited image processing")

try:
    import pillow_heif  # noqa: F401

    PIL_AVAILABLE = True
except ImportError:
    pass  # HEIF support is optional


class ImageFormat(Enum):
    """Supported image formats."""

    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    HEIF = "heif"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"


@dataclass
class ImageProcessingConfig:
    """Configuration for image processing."""

    max_width: int = 2048
    max_height: int = 2048
    quality: int = 85  # JPEG quality
    optimize: bool = True
    progressive: bool = True
    strip_metadata: bool = True
    preserve_exif: bool = False
    thumbnail_size: Tuple[int, int] = (200, 200)
    thumbnail_quality: int = 75


@dataclass
class ProcessingResult:
    """Result of image processing."""

    original_format: str
    output_format: str
    original_size_bytes: int
    output_size_bytes: int
    compression_ratio: float
    dimensions: Tuple[int, int]
    processing_time_ms: float
    error: Optional[str] = None


class ImageProcessor:
    """Advanced image processor with optimization."""

    def __init__(self, config: Optional[ImageProcessingConfig] = None):
        self.config = config or ImageProcessingConfig()
        self.supported_formats = {
            ImageFormat.JPEG: [".jpg", ".jpeg"],
            ImageFormat.PNG: [".png"],
            ImageFormat.WEBP: [".webp"],
            ImageFormat.HEIF: [".heif", ".heic"],
            ImageFormat.GIF: [".gif"],
            ImageFormat.BMP: [".bmp"],
            ImageFormat.TIFF: [".tiff", ".tif"],
        }

    async def process_image(
        self,
        image_data: bytes,
        output_format: Optional[ImageFormat] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
    ) -> ProcessingResult:
        """Process image with resizing and compression."""
        if not PIL_AVAILABLE:
            return ProcessingResult(
                original_format="unknown",
                output_format="unknown",
                original_size_bytes=len(image_data),
                output_size_bytes=len(image_data),
                compression_ratio=1.0,
                dimensions=(0, 0),
                processing_time_ms=0,
                error="Pillow not available",
            )

        start_time = time.time()

        try:
            # Load image
            image, original_format = await self._load_image(image_data)
            if image is None:
                raise ValueError("Failed to load image")

            original_size = len(image_data)
            original_dimensions = image.size

            # Determine output format
            if output_format is None:
                output_format = self._choose_optimal_format(original_format, image.mode)

            # Resize if needed
            max_w = max_width or self.config.max_width
            max_h = max_height or self.config.max_height

            if image.size[0] > max_w or image.size[1] > max_h:
                image = await self._resize_image(image, max_w, max_h)

            # Apply optimizations
            if self.config.optimize:
                image = await self._optimize_image(image, original_format)

            # Convert format if needed
            if output_format.value != original_format.lower():
                image = await self._convert_format(image, output_format)

            # Save with compression
            output_data, output_size = await self._save_image(
                image, output_format, quality or self.config.quality
            )

            processing_time = (time.time() - start_time) * 1000

            return ProcessingResult(
                original_format=original_format,
                output_format=output_format.value,
                original_size_bytes=original_size,
                output_size_bytes=output_size,
                compression_ratio=output_size / original_size
                if original_size > 0
                else 1.0,
                dimensions=image.size,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return ProcessingResult(
                original_format="unknown",
                output_format="unknown",
                original_size_bytes=len(image_data),
                output_size_bytes=len(image_data),
                compression_ratio=1.0,
                dimensions=(0, 0),
                processing_time_ms=processing_time,
                error=str(e),
            )

    async def create_thumbnail(
        self,
        image_data: bytes,
        width: int,
        height: int,
        format: ImageFormat = ImageFormat.JPEG,
        quality: Optional[int] = None,
    ) -> Tuple[bytes, ProcessingResult]:
        """Create thumbnail from image."""
        if not PIL_AVAILABLE:
            return image_data, ProcessingResult(
                original_format="unknown",
                output_format="unknown",
                original_size_bytes=len(image_data),
                output_size_bytes=len(image_data),
                compression_ratio=1.0,
                dimensions=(width, height),
                processing_time_ms=0,
                error="Pillow not available",
            )

        start_time = time.time()
        original_size = len(image_data)

        try:
            # Load image
            image, original_format = await self._load_image(image_data)
            if image is None:
                raise ValueError("Failed to load image")

            # Create thumbnail with smart cropping
            thumbnail = await self._create_smart_thumbnail(image, width, height)

            # Save thumbnail
            thumbnail_data, thumbnail_size = await self._save_image(
                thumbnail, format, quality or self.config.thumbnail_quality
            )

            processing_time = (time.time() - start_time) * 1000

            result = ProcessingResult(
                original_format=original_format,
                output_format=format.value,
                original_size_bytes=original_size,
                output_size_bytes=thumbnail_size,
                compression_ratio=thumbnail_size / original_size
                if original_size > 0
                else 1.0,
                dimensions=thumbnail.size,
                processing_time_ms=processing_time,
            )

            return thumbnail_data, result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            result = ProcessingResult(
                original_format="unknown",
                output_format="unknown",
                original_size_bytes=original_size,
                output_size_bytes=original_size,
                compression_ratio=1.0,
                dimensions=(width, height),
                processing_time_ms=processing_time,
                error=str(e),
            )
            return image_data, result

    async def _load_image(self, image_data: bytes) -> Tuple[Any, str]:
        """Load image from bytes and detect format."""
        try:
            # Try to detect format from bytes
            format_hint = self._detect_format_from_bytes(image_data)

            # Load image with format hint
            if format_hint == "heif" or format_hint == "heic":
                # Handle HEIF/HEIC images
                image = Image.open(io.BytesIO(image_data))
                image = image.convert("RGB")
                return image, format_hint
            else:
                # Handle standard formats
                with Image.open(io.BytesIO(image_data)) as image:
                    # Convert to RGB for JPEG compatibility
                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")
                    return image.copy(), format_hint or "jpeg"

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None, "unknown"

    def _detect_format_from_bytes(self, image_data: bytes) -> str:
        """Detect image format from file signature."""
        if len(image_data) < 8:
            return "jpeg"  # Default

        # Check common image signatures
        signatures = {
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG\r\n\x1a\n": "png",
            b"RIFF": "webp",  # WebP starts with RIFF
            b"\x00\x00\x00 ftyp": "heif",  # HEIF/HEIC
            b"GIF87a": "gif",
            b"GIF89a": "gif",
            b"BM": "bmp",
            b"II*\x00": "tiff",
            b"MM\x00\x00": "tiff",
        }

        for sig, format_name in signatures.items():
            if image_data.startswith(sig):
                return format_name

        return "jpeg"  # Default

    def _choose_optimal_format(self, original_format: str, mode: str) -> ImageFormat:
        """Choose optimal output format based on image characteristics."""
        # Keep original format if it's already efficient
        if original_format in ["webp", "jpeg"]:
            return ImageFormat(original_format)

        # Choose based on image characteristics
        if mode == "RGBA" or "transparency" in mode.lower():
            return ImageFormat.PNG  # Preserve transparency

        # For photos, JPEG is usually most efficient
        return ImageFormat.JPEG

    async def _resize_image(self, image: Any, max_width: int, max_height: int) -> Any:
        """Resize image maintaining aspect ratio."""
        original_width, original_height = image.size

        # Calculate new dimensions
        ratio = min(max_width / original_width, max_height / original_height)
        if ratio >= 1:
            return image  # No resize needed

        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Use high-quality resize
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    async def _create_smart_thumbnail(self, image: Any, width: int, height: int) -> Any:
        """Create thumbnail with smart cropping."""
        # Use ImageOps.fit which maintains aspect ratio and crops intelligently
        return ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS)

    async def _optimize_image(self, image: Any, original_format: str) -> Any:
        """Apply image optimizations."""
        # Enhance contrast slightly for better appearance
        if original_format.lower() in ["jpeg", "jpg"]:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.05)

        # Apply sharpening for better clarity
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.02)

        return image

    async def _convert_format(self, image: Any, target_format: ImageFormat) -> Any:
        """Convert image to target format."""
        if target_format == ImageFormat.JPEG and image.mode in ("RGBA", "LA", "P"):
            # Convert to RGB for JPEG
            image = image.convert("RGB")
        elif target_format == ImageFormat.PNG and image.mode not in (
            "RGBA",
            "RGB",
            "L",
        ):
            # Convert to RGBA for PNG
            image = image.convert("RGBA")

        return image

    async def _save_image(
        self, image: Any, format: ImageFormat, quality: int = 85
    ) -> Tuple[bytes, int]:
        """Save image to bytes with compression."""
        output = io.BytesIO()

        save_kwargs = {}

        if format == ImageFormat.JPEG:
            save_kwargs.update(
                {
                    "format": "JPEG",
                    "quality": quality,
                    "optimize": self.config.optimize,
                    "progressive": self.config.progressive,
                }
            )
        elif format == ImageFormat.PNG:
            save_kwargs.update(
                {
                    "format": "PNG",
                    "optimize": self.config.optimize,
                }
            )
        elif format == ImageFormat.WEBP:
            save_kwargs.update(
                {
                    "format": "WEBP",
                    "quality": quality,
                    "optimize": self.config.optimize,
                    "method": 6,  # Better compression
                }
            )
        else:
            save_kwargs["format"] = format.value.upper()

        image.save(output, **save_kwargs)
        output_data = output.getvalue()
        output.close()

        return output_data, len(output_data)

    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """Get comprehensive image information."""
        if not PIL_AVAILABLE:
            return {
                "size_bytes": len(image_data),
                "format": "unknown",
                "dimensions": (0, 0),
                "mode": "unknown",
                "has_transparency": False,
            }

        try:
            image, format_name = self._load_image(image_data)
            if image is None:
                return {"error": "Failed to load image"}

            return {
                "size_bytes": len(image_data),
                "format": format_name,
                "dimensions": image.size,
                "mode": image.mode,
                "has_transparency": image.mode in ("RGBA", "LA", "P"),
                "color_count": len(image.getcolors()) if image.mode == "P" else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported."""
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        for format_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return True

        return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        extensions = []
        for ext_list in self.supported_formats.values():
            extensions.extend(ext_list)
        return sorted(set(extensions))


# Global processor instance
_processor: ImageProcessor | None = None


def get_image_processor() -> ImageProcessor:
    """Get global image processor instance."""
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


def init_image_processor(
    config: Optional[ImageProcessingConfig] = None,
) -> ImageProcessor:
    """Initialize global image processor."""
    global _processor
    _processor = ImageProcessor(config)
    return _processor


# Import time for performance measurement
import time
