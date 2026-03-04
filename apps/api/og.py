import io

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response
from PIL import Image, ImageDraw, ImageFont
from shared.middleware import get_client_ip
from shared.logging_config import get_logger

from shared.metrics import get_rate_limiter

logger = get_logger("sorce.api.og")

router = APIRouter()

# --- CONFIG ---
WIDTH, HEIGHT = 1200, 630
BG_COLOR = "#FAF9F6"  # Warm off-white
PRIMARY_COLOR = "#FF6B35"  # Denver sunset orange
SECONDARY_COLOR = "#4A90E2"  # Tech blue
TEXT_COLOR = "#2D2D2D"  # Charcoal gray
ACCENT_COLOR = "#FFFFFF"

# Font URLs (Google Fonts - using raw.githubusercontent.com for stability)
FONT_URL_BOLD = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf"
FONT_URL_REGULAR = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter-Regular.ttf"

# In-memory cache for fonts
_font_cache = {}

def get_font(url: str, size: int):
    key = f"{url}-{size}"
    if key in _font_cache:
        return _font_cache[key]

    try:
        # Try to load from cache first if we saved it to disk (optional optimization)
        # For now, just fetch into memory
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        font_bytes = io.BytesIO(resp.content)
        font = ImageFont.truetype(font_bytes, size)
        _font_cache[key] = font
        return font
    except Exception as e:
        logger.warning("Failed to load font %s: %s", url, e)
        return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width."""
    lines = []
    if not text:
        return lines

    # Simple word wrap
    words = text.split()
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        # getbbox returns (left, top, right, bottom)
        w = bbox[2] - bbox[0]

        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Word itself is too long, just put it (or truncate)
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines

@router.get("/api/og")
async def generate_og_image(
    request: Request,
    job: str = Query(..., description="Job Title", max_length=100),
    company: str = Query("Top Company", description="Company Name", max_length=50),
    score: int = Query(90, description="Match Score (0-100)"),
    location: str = Query("Denver, CO", description="Job Location", max_length=50),
):
    """Generate a dynamic Open Graph image for a job posting."""
    # Rate limit OG image generation per IP
    client_ip = get_client_ip(request)
    limiter = get_rate_limiter(f"og:{client_ip}", max_calls=30, window_seconds=60)
    if not await limiter.acquire():
        raise HTTPException(status_code=429, detail="Too many requests")

    # 1. Create Canvas
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    # 2. Draw "Robot Arm" Swipe Effect (Orange/Blue Gradient-ish)
    # We'll simulate a gradient by drawing multiple lines or circles
    # Background swipe trail
    for i in range(200):
        _alpha = int(255 * (1 - i/200))  # kept for future gradient opacity
        color = (255, 107, 53) # RGB for #FF6B35
        # Interpolate towards blue
        if i > 100:
             # Simple interpolation
             ratio = (i - 100) / 100
             r = int(255 * (1 - ratio) + 74 * ratio)
             g = int(107 * (1 - ratio) + 144 * ratio)
             b = int(53 * (1 - ratio) + 226 * ratio)
             color = (r, g, b)

        x_offset = i * 2
        draw.ellipse([800 + x_offset, -100 + x_offset, 1400 + x_offset, 500 + x_offset], outline=None, fill=color)

    # Main "Card" Area (White Box)
    margin = 60
    card_width = WIDTH - (margin * 2)
    _card_height = HEIGHT - (margin * 2)  # noqa: F841 — kept for future use
    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=40,
        fill="white",
        outline="#E5E7EB",
        width=2
    )

    # 3. Text
    # Load Fonts
    title_font = get_font(FONT_URL_BOLD, 70)
    company_font = get_font(FONT_URL_REGULAR, 40)
    meta_font = get_font(FONT_URL_BOLD, 30)
    footer_font = get_font(FONT_URL_REGULAR, 24)

    # Job Title
    lines = wrap_text(job, title_font, card_width - 100)
    # Take max 2 lines
    lines = lines[:2]

    current_y = 120
    for line in lines:
        draw.text((100, current_y), line, font=title_font, fill=TEXT_COLOR)
        current_y += 90

    # Company
    draw.text((100, current_y + 10), f"at {company}", font=company_font, fill=SECONDARY_COLOR)

    # Badges Row (Score + Location)
    badge_y = current_y + 100

    # Score Badge
    score_text = f"AI Match: {score}%"
    # Estimate width
    bbox = meta_font.getbbox(score_text)
    w = bbox[2] - bbox[0]
    padding = 20
    draw.rounded_rectangle(
        [100, badge_y, 100 + w + (padding*2), badge_y + 60],
        radius=15,
        fill="#ECFDF5", # Green-ish background
        outline="#10B981",
        width=2
    )
    draw.text((100 + padding, badge_y + 10), score_text, font=meta_font, fill="#047857")

    # Location Badge
    loc_x = 100 + w + (padding*2) + 30
    draw.text((loc_x, badge_y + 10), f"📍 {location}", font=meta_font, fill="#6B7280")

    # 4. Footer
    # "JobHuntin.com"
    draw.line([100, HEIGHT - 120, WIDTH - 100, HEIGHT - 120], fill="#F3F4F6", width=2)
    draw.text((100, HEIGHT - 90), "jobhuntin.com", font=footer_font, fill=PRIMARY_COLOR)
    draw.text((WIDTH - 400, HEIGHT - 90), "AI Applies For You • Beat Sorce.jobs", font=footer_font, fill="#9CA3AF")

    # 5. Output
    img_byte_arr = io.BytesIO()
    im.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return Response(content=img_byte_arr.getvalue(), media_type="image/png")
