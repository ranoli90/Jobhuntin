"""
Open Graph Image Generator — dynamic OG images for social sharing.

Generates shareable images for:
- Match results
- Application milestones
- Profile achievements
- Job listings
"""

from __future__ import annotations

import io
from typing import Any

from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.og_images")

try:
    from PIL import Image, ImageDraw, ImageFont

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("PIL not installed - OG image generation disabled")

OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
BACKGROUND_COLOR = "#1E293B"
ACCENT_COLOR = "#3B82F6"
TEXT_COLOR = "#FFFFFF"
SECONDARY_COLOR = "#94A3B8"


class OGImageGenerator:
    def __init__(
        self,
        width: int = OG_IMAGE_WIDTH,
        height: int = OG_IMAGE_HEIGHT,
        background: str = BACKGROUND_COLOR,
        accent: str = ACCENT_COLOR,
    ):
        self.width = width
        self.height = height
        self.background = background
        self.accent = accent

        if not HAS_PIL:
            raise RuntimeError("PIL not installed")

    def _get_font(self, size: int, bold: bool = False) -> Any:
        font_names = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "Arial-Bold.ttf" if bold else "Arial.ttf",
            "Helvetica-Bold.ttf" if bold else "Helvetica.ttf",
            "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf",
        ]

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue

        return ImageFont.load_default()

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def generate_match_result_image(
        self,
        job_title: str,
        company: str,
        match_score: float,
        match_reasons: list[str] | None = None,
    ) -> bytes:
        img = Image.new(
            "RGB", (self.width, self.height), self._hex_to_rgb(self.background)
        )
        draw = ImageDraw.Draw(img)

        accent_rgb = self._hex_to_rgb(self.accent)
        draw.rectangle([(0, 0), (self.width, 8)], fill=accent_rgb)

        title_font = self._get_font(48, bold=True)
        company_font = self._get_font(32)
        score_font = self._get_font(72, bold=True)
        label_font = self._get_font(24)
        reason_font = self._get_font(20)

        title = self._truncate_text(job_title, 40)
        draw.text((60, 60), title, font=title_font, fill=self._hex_to_rgb(TEXT_COLOR))

        draw.text(
            (60, 120),
            company,
            font=company_font,
            fill=self._hex_to_rgb(SECONDARY_COLOR),
        )

        score_x = self.width - 200
        score_y = 50

        draw.ellipse(
            [(score_x - 60, score_y), (score_x + 140, score_y + 160)],
            fill=accent_rgb,
            outline=accent_rgb,
            width=3,
        )

        score_text = f"{int(match_score)}"
        draw.text(
            (score_x, score_y + 30),
            score_text,
            font=score_font,
            fill=self._hex_to_rgb(TEXT_COLOR),
        )
        draw.text(
            (score_x, score_y + 120),
            "%",
            font=label_font,
            fill=self._hex_to_rgb(TEXT_COLOR),
        )

        draw.text(
            (60, 220),
            "Match Score",
            font=label_font,
            fill=self._hex_to_rgb(SECONDARY_COLOR),
        )

        if match_reasons:
            y_pos = 280
            draw.text(
                (60, y_pos),
                "Why you're a great fit:",
                font=label_font,
                fill=self._hex_to_rgb(TEXT_COLOR),
            )
            y_pos += 40

            for reason in match_reasons[:3]:
                reason_text = f"• {self._truncate_text(reason, 50)}"
                draw.text(
                    (80, y_pos),
                    reason_text,
                    font=reason_font,
                    fill=self._hex_to_rgb(SECONDARY_COLOR),
                )
                y_pos += 35

        draw.text(
            (60, self.height - 60),
            "JobHuntin",
            font=self._get_font(28, bold=True),
            fill=accent_rgb,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", quality=95)
        incr("og_images.generated", {"type": "match_result"})

        return buffer.getvalue()

    def generate_milestone_image(
        self,
        milestone_type: str,
        count: int,
        period: str = "this month",
    ) -> bytes:
        img = Image.new(
            "RGB", (self.width, self.height), self._hex_to_rgb(self.background)
        )
        draw = ImageDraw.Draw(img)

        accent_rgb = self._hex_to_rgb(self.accent)

        milestone_labels = {
            "applications": "Applications Submitted",
            "interviews": "Interviews Scheduled",
            "offers": "Job Offers Received",
        }

        label = milestone_labels.get(milestone_type, milestone_type.title())

        count_font = self._get_font(120, bold=True)
        label_font = self._get_font(36)
        period_font = self._get_font(28)

        count_str = str(count)
        bbox = draw.textbbox((0, 0), count_str, font=count_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2

        draw.text(
            (x, 150), count_str, font=count_font, fill=self._hex_to_rgb(TEXT_COLOR)
        )

        bbox = draw.textbbox((0, 0), label, font=label_font)
        label_width = bbox[2] - bbox[0]
        label_x = (self.width - label_width) // 2
        draw.text((label_x, 290), label, font=label_font, fill=accent_rgb)

        period_text = period
        bbox = draw.textbbox((0, 0), period_text, font=period_font)
        period_width = bbox[2] - bbox[0]
        period_x = (self.width - period_width) // 2
        draw.text(
            (period_x, 350),
            period_text,
            font=period_font,
            fill=self._hex_to_rgb(SECONDARY_COLOR),
        )

        draw.text(
            (60, self.height - 60),
            "JobHuntin",
            font=self._get_font(28, bold=True),
            fill=accent_rgb,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", quality=95)
        incr("og_images.generated", {"type": "milestone"})

        return buffer.getvalue()

    def generate_job_listing_image(
        self,
        title: str,
        company: str,
        location: str,
        salary_range: str | None = None,
    ) -> bytes:
        img = Image.new(
            "RGB", (self.width, self.height), self._hex_to_rgb(self.background)
        )
        draw = ImageDraw.Draw(img)

        accent_rgb = self._hex_to_rgb(self.accent)
        draw.rectangle([(0, 0), (self.width, 8)], fill=accent_rgb)

        title_font = self._get_font(44, bold=True)
        company_font = self._get_font(32)
        detail_font = self._get_font(26)

        title = self._truncate_text(title, 45)
        draw.text((60, 80), title, font=title_font, fill=self._hex_to_rgb(TEXT_COLOR))

        draw.text((60, 150), company, font=company_font, fill=accent_rgb)

        y = 220
        if location:
            draw.text(
                (60, y),
                f"📍 {location}",
                font=detail_font,
                fill=self._hex_to_rgb(SECONDARY_COLOR),
            )
            y += 50

        if salary_range:
            draw.text(
                (60, y),
                f"💰 {salary_range}",
                font=detail_font,
                fill=self._hex_to_rgb(SECONDARY_COLOR),
            )

        draw.text(
            (60, self.height - 60),
            "JobHuntin",
            font=self._get_font(28, bold=True),
            fill=accent_rgb,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", quality=95)
        incr("og_images.generated", {"type": "job_listing"})

        return buffer.getvalue()

    def _truncate_text(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."


async def generate_og_image(
    image_type: str,
    data: dict[str, Any],
) -> bytes | None:
    if not HAS_PIL:
        logger.warning("Cannot generate OG image: PIL not installed")
        return None

    generator = OGImageGenerator()

    if image_type == "match_result":
        return generator.generate_match_result_image(
            job_title=data.get("job_title", "Unknown Position"),
            company=data.get("company", "Unknown Company"),
            match_score=data.get("match_score", 0),
            match_reasons=data.get("match_reasons"),
        )
    elif image_type == "milestone":
        return generator.generate_milestone_image(
            milestone_type=data.get("milestone_type", "applications"),
            count=data.get("count", 0),
            period=data.get("period", "this month"),
        )
    elif image_type == "job_listing":
        return generator.generate_job_listing_image(
            title=data.get("title", "Position"),
            company=data.get("company", "Company"),
            location=data.get("location", ""),
            salary_range=data.get("salary_range"),
        )
    else:
        logger.warning("Unknown OG image type: %s", image_type)
        return None
