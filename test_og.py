
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import httpx

# Mocking the constants from api/og.py
WIDTH, HEIGHT = 1200, 630
BG_COLOR = "#FAF9F6"
PRIMARY_COLOR = "#FF6B35"
SECONDARY_COLOR = "#4A90E2"
TEXT_COLOR = "#2D2D2D"
FONT_URL_BOLD = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
FONT_URL_REGULAR = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"

async def test_generation():
    print("Starting OG Image generation test...")
    
    # 1. Create Canvas
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)
    
    print("Canvas created.")

    # 2. Draw "Robot Arm" Swipe Effect
    for i in range(200):
        alpha = int(255 * (1 - i/200))
        # Simple interpolation logic from the file
        ratio = (i - 100) / 100 if i > 100 else 0
        r = int(255 * (1 - ratio) + 74 * ratio) if i > 100 else 255
        g = int(107 * (1 - ratio) + 144 * ratio) if i > 100 else 107
        b = int(53 * (1 - ratio) + 226 * ratio) if i > 100 else 53
        color = (r, g, b)
        
        x_offset = i * 2
        draw.ellipse([800 + x_offset, -100 + x_offset, 1400 + x_offset, 500 + x_offset], outline=None, fill=color)

    print("Background drawn.")

    # 3. Fonts
    try:
        print(f"Fetching font: {FONT_URL_BOLD}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(FONT_URL_BOLD, follow_redirects=True)
            resp.raise_for_status()
            font_bytes = io.BytesIO(resp.content)
            title_font = ImageFont.truetype(font_bytes, 70)
            print("Font loaded successfully.")
    except Exception as e:
        print(f"Font loading failed: {e}")
        return

    # 4. Text
    job = "Senior Software Engineer"
    company = "TechCorp"
    draw.text((100, 120), job, font=title_font, fill=TEXT_COLOR)
    
    print("Text drawn.")
    
    # 5. Save
    output = io.BytesIO()
    im.save(output, format='PNG')
    size = output.tell()
    print(f"Image generated successfully! Size: {size} bytes")

if __name__ == "__main__":
    asyncio.run(test_generation())
