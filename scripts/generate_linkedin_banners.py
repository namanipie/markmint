"""
Generate official LinkedIn banners for MarkMint v2.0:
1. Personal Profile Banner (1584 x 396 px)
2. Company / Organization Page Banner (1128 x 191 px standard + 1584 x 396 px high-res)
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "C:/Windows/Fonts"

def get_font(name: str, size: int):
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    # Fallback to arial
    return ImageFont.truetype(os.path.join(FONT_DIR, "arial.ttf"), size)


def draw_glow(base_img: Image.Image, cx: int, cy: int, radius: int, color_rgb: tuple, max_alpha: int = 40):
    glow = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for r in range(radius, 0, -15):
        alpha = int(max_alpha * (1.0 - (r / float(radius)) ** 1.6))
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(color_rgb[0], color_rgb[1], color_rgb[2], alpha))
    return Image.alpha_composite(base_img, glow)


def draw_rounded_card(draw: ImageDraw.ImageDraw, bbox: tuple, radius: int, fill: tuple, outline: tuple, width: int = 1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


# ==============================================================================
# 1. PERSONAL PROFILE BANNER (1584 x 396 px)
# ==============================================================================
def generate_personal_banner(output_path="public/banners/linkedin_personal_banner.png"):
    W, H = 1584, 396
    img = Image.new("RGBA", (W, H), (9, 10, 15, 255))

    # Ambient glows (Emerald mint glow top right, violet glow bottom center)
    img = draw_glow(img, W - 250, 100, 480, (16, 185, 129), max_alpha=45) # Emerald
    img = draw_glow(img, 700, 320, 420, (124, 58, 237), max_alpha=35)   # Violet
    img = draw_glow(img, 200, 50, 300, (6, 95, 70), max_alpha=25)      # Deep teal

    draw = ImageDraw.Draw(img)

    # Architectural dot grid (Spacing: 40px)
    for x in range(30, W - 30, 40):
        for y in range(30, H - 30, 40):
            draw.point((x, y), fill=(255, 255, 255, 22))

    # Outer border
    draw.rectangle([20, 20, W - 20, H - 20], outline=(255, 255, 255, 20), width=1)

    # Crosshairs
    def crosshair(cx, cy):
        draw.line([cx - 10, cy, cx + 10, cy], fill=(16, 185, 129, 180), width=1)
        draw.line([cx, cy - 10, cx, cy + 10], fill=(16, 185, 129, 180), width=1)

    crosshair(20, 20)
    crosshair(W - 20, 20)
    crosshair(20, H - 20)
    crosshair(W - 20, H - 20)

    # Fonts
    f_badge = get_font("bahnschrift.ttf", 15)
    f_title = get_font("bahnschrift.ttf", 46)
    f_sub = get_font("segoeui.ttf", 20)
    f_stat_num = get_font("bahnschrift.ttf", 26)
    f_stat_label = get_font("segoeui.ttf", 14)
    f_tech = get_font("consola.ttf", 15)
    f_url = get_font("bahnschrift.ttf", 19)

    # Left Profile Photo Indicator Guide (Subtle, so user knows safe space)
    # Avatar occupies ~ (60, 180) to (240, 396). Content sits at x >= 360.
    start_x = 360

    # Badges Row (y=38)
    # Badge 1: MARKMINT v2.0
    draw_rounded_card(draw, (start_x, 38, start_x + 155, 66), radius=14, fill=(16, 185, 129, 35), outline=(16, 185, 129, 140))
    draw.text((start_x + 16, 44), "MARKMINT v2.0", font=f_badge, fill=(52, 211, 153, 255))

    # Badge 2: SRMIST ACADEMIC INTELLIGENCE
    b2_x = start_x + 168
    draw_rounded_card(draw, (b2_x, 38, b2_x + 245, 66), radius=14, fill=(255, 255, 255, 12), outline=(255, 255, 255, 30))
    draw.text((b2_x + 16, 44), "SRMIST ACADEMIC INTELLIGENCE", font=f_badge, fill=(203, 213, 225, 255))

    # Badge 3: FOUNDER / BUILDER
    b3_x = b2_x + 258
    draw_rounded_card(draw, (b3_x, 38, b3_x + 175, 66), radius=14, fill=(124, 58, 237, 30), outline=(139, 92, 246, 120))
    draw.text((b3_x + 16, 44), "BUILDER // LEAD", font=f_badge, fill=(196, 181, 253, 255))

    # Headline (y=90)
    draw.text((start_x, 86), "Building MarkMint • Academic Intelligence", font=f_title, fill=(255, 255, 255, 255))

    # Subtitle (y=150)
    draw.text(
        (start_x, 150),
        "Turning 7 years of authentic SRM engineering exam data into calibrated predictive intelligence.",
        font=f_sub,
        fill=(148, 163, 184, 255),
    )

    # 4 Metric Cards Row (y=198)
    metrics = [
        ("43", "Courses (Sem 1–8)"),
        ("389", "Authentic Papers"),
        ("11,498", "Verified Questions"),
        ("9,798", "Question Families"),
    ]

    card_w = 265
    card_h = 74
    gap = 18
    for i, (num, label) in enumerate(metrics):
        cx = start_x + i * (card_w + gap)
        cy = 198
        # Glassmorphic Card
        draw_rounded_card(draw, (cx, cy, cx + card_w, cy + card_h), radius=12, fill=(17, 24, 39, 180), outline=(255, 255, 255, 28))
        # Top Accent Line
        draw.line([cx + 12, cy, cx + card_w - 12, cy], fill=(16, 185, 129, 200) if i == 0 else (139, 92, 246, 160), width=2)
        # Number
        draw.text((cx + 18, cy + 12), num, font=f_stat_num, fill=(255, 255, 255, 255))
        # Label
        draw.text((cx + 18, cy + 44), label, font=f_stat_label, fill=(148, 163, 184, 255))

    # Bottom Footer Divider (y=305)
    draw.line([start_x, 305, W - 60, 305], fill=(255, 255, 255, 22), width=1)

    # Tech Stack on Left of Footer
    tech_str = "Next.js 16 • Turbopack • Neon PostgreSQL 18.6 • Gemini 3.5 Flash Vision • Sub-15ms Latency"
    draw.text((start_x, 325), tech_str, font=f_tech, fill=(100, 116, 139, 255))

    # Platform URL on Right of Footer
    url_box_w = 215
    url_box_x = W - 60 - url_box_w
    draw_rounded_card(draw, (url_box_x, 318, url_box_x + url_box_w, 354), radius=10, fill=(16, 185, 129, 30), outline=(16, 185, 129, 180))
    draw.text((url_box_x + 18, 325), "markmint.vercel.app ↗", font=f_url, fill=(52, 211, 153, 255))

    img.save(output_path, "PNG")
    print(f"[OK] Generated Personal Banner: {output_path} ({W}x{H})")


# ==============================================================================
# 2. COMPANY / BRAND PAGE BANNER (1128 x 191 px Standard)
# ==============================================================================
def generate_company_banner_standard(output_path="public/banners/linkedin_company_banner_1128x191.png"):
    W, H = 1128, 191
    img = Image.new("RGBA", (W, H), (9, 10, 15, 255))

    # Ambient glows
    img = draw_glow(img, W - 180, 80, 320, (16, 185, 129), max_alpha=50) # Emerald right
    img = draw_glow(img, 550, 150, 260, (124, 58, 237), max_alpha=35)   # Violet center
    img = draw_glow(img, 120, 50, 200, (6, 95, 70), max_alpha=25)

    draw = ImageDraw.Draw(img)

    # Dot Grid (Spacing: 30px)
    for x in range(20, W - 20, 30):
        for y in range(15, H - 15, 30):
            draw.point((x, y), fill=(255, 255, 255, 18))

    # Outer border
    draw.rectangle([12, 12, W - 12, H - 12], outline=(255, 255, 255, 20), width=1)

    # Fonts
    f_brand = get_font("bahnschrift.ttf", 36)
    f_badge = get_font("bahnschrift.ttf", 13)
    f_tagline = get_font("segoeui.ttf", 15)
    f_pillar = get_font("bahnschrift.ttf", 13)
    f_stat = get_font("consola.ttf", 13)
    f_url = get_font("bahnschrift.ttf", 14)

    # Note: On LinkedIn Company pages, the square profile photo sits on the bottom-left
    # usually covering (25, 90) to (140, 191). So we place main brand content starting at x=220 or center.
    start_x = 230

    # Top Row: Brand + Version Badge
    draw.text((start_x, 22), "MARKMINT", font=f_brand, fill=(255, 255, 255, 255))
    # Emerald Dot
    brand_w = f_brand.getlength("MARKMINT")
    draw.ellipse([start_x + brand_w + 6, 42, start_x + brand_w + 16, 52], fill=(16, 185, 129, 255))

    # Version Pill
    pill_x = start_x + brand_w + 30
    draw_rounded_card(draw, (pill_x, 28, pill_x + 95, 52), radius=10, fill=(16, 185, 129, 30), outline=(16, 185, 129, 160))
    draw.text((pill_x + 12, 32), "v2.0 LIVE", font=f_badge, fill=(52, 211, 153, 255))

    # Tagline
    draw.text((start_x, 68), "The Academic Intelligence & Exam Prediction Platform for SRMIST Engineering", font=f_tagline, fill=(203, 213, 225, 255))

    # 4 Core Pillars Pills (y=98)
    pillars = [
        "3-Tier Prediction Engine (CT1 • CT2 • EndSem)",
        "11,498 Authentic Questions (2018–2025)",
        "Search Radar (LaTeX Math)",
        "Mint+ GPA Calculator",
    ]
    px = start_x
    py = 98
    for p in pillars:
        pw = int(f_pillar.getlength(p)) + 20
        draw_rounded_card(draw, (px, py, px + pw, py + 26), radius=8, fill=(17, 24, 39, 190), outline=(255, 255, 255, 30))
        draw.text((px + 10, py + 4), p, font=f_pillar, fill=(148, 163, 184, 255))
        px += pw + 10

    # Bottom Stat Line (y=138)
    draw.line([start_x, 134, W - 40, 134], fill=(255, 255, 255, 20), width=1)
    stat_text = "43 COURSES  //  389 PAPERS  //  9,798 QUESTION FAMILIES  //  1,226 TOPICS  //  <15MS LATENCY"
    draw.text((start_x, 146), stat_text, font=f_stat, fill=(100, 116, 139, 255))

    # URL Pill on Top-Right (y=26)
    url_w = 195
    url_x = W - 35 - url_w
    draw_rounded_card(draw, (url_x, 26, url_x + url_w, 54), radius=10, fill=(16, 185, 129, 35), outline=(16, 185, 129, 180))
    draw.text((url_x + 14, 32), "markmint.vercel.app ↗", font=f_url, fill=(52, 211, 153, 255))

    img.save(output_path, "PNG")
    print(f"[OK] Generated Standard Company Banner: {output_path} ({W}x{H})")


# ==============================================================================
# 3. COMPANY / BRAND PAGE BANNER (1584 x 396 px High-Res 4:1)
# ==============================================================================
def generate_company_banner_highres(output_path="public/banners/linkedin_company_banner_1584x396.png"):
    W, H = 1584, 396
    img = Image.new("RGBA", (W, H), (9, 10, 15, 255))

    # Ambient glows
    img = draw_glow(img, W - 250, 120, 500, (16, 185, 129), max_alpha=50) # Emerald
    img = draw_glow(img, 750, 320, 440, (124, 58, 237), max_alpha=35)   # Violet
    img = draw_glow(img, 200, 80, 340, (6, 95, 70), max_alpha=30)

    draw = ImageDraw.Draw(img)

    for x in range(30, W - 30, 40):
        for y in range(30, H - 30, 40):
            draw.point((x, y), fill=(255, 255, 255, 20))

    draw.rectangle([20, 20, W - 20, H - 20], outline=(255, 255, 255, 20), width=1)

    f_brand = get_font("bahnschrift.ttf", 52)
    f_badge = get_font("bahnschrift.ttf", 15)
    f_sub = get_font("segoeui.ttf", 22)
    f_stat_num = get_font("bahnschrift.ttf", 26)
    f_stat_label = get_font("segoeui.ttf", 14)
    f_tech = get_font("consola.ttf", 15)
    f_url = get_font("bahnschrift.ttf", 19)

    start_x = 360

    # Badges Row (y=38)
    draw_rounded_card(draw, (start_x, 38, start_x + 140, 66), radius=14, fill=(16, 185, 129, 35), outline=(16, 185, 129, 160))
    draw.text((start_x + 16, 44), "MARKMINT", font=f_badge, fill=(52, 211, 153, 255))

    b2_x = start_x + 152
    draw_rounded_card(draw, (b2_x, 38, b2_x + 245, 66), radius=14, fill=(255, 255, 255, 12), outline=(255, 255, 255, 30))
    draw.text((b2_x + 16, 44), "SRMIST ACADEMIC INTELLIGENCE", font=f_badge, fill=(203, 213, 225, 255))

    b3_x = b2_x + 258
    draw_rounded_card(draw, (b3_x, 38, b3_x + 165, 66), radius=14, fill=(124, 58, 237, 30), outline=(139, 92, 246, 120))
    draw.text((b3_x + 16, 44), "SEMESTERS 1–8", font=f_badge, fill=(196, 181, 253, 255))

    # Headline
    draw.text((start_x, 86), "The Definitive Exam Intelligence Platform", font=f_brand, fill=(255, 255, 255, 255))

    # Subtitle
    draw.text(
        (start_x, 150),
        "Calibrated topic forecasts, 11,498 authentic verified questions, and isolated CT1 / CT2 / EndSem scopes.",
        font=f_sub,
        fill=(148, 163, 184, 255),
    )

    # 4 Metric Cards Row (y=198)
    metrics = [
        ("43 Courses", "Semesters 1 through 8"),
        ("389 Papers", "Complete 7-Year Archive"),
        ("11,498 Questions", "100% Topic-Verified"),
        ("9,798 Families", "Exact & Structural Repeats"),
    ]

    card_w = 265
    card_h = 74
    gap = 18
    for i, (num, label) in enumerate(metrics):
        cx = start_x + i * (card_w + gap)
        cy = 198
        draw_rounded_card(draw, (cx, cy, cx + card_w, cy + card_h), radius=12, fill=(17, 24, 39, 180), outline=(255, 255, 255, 28))
        draw.line([cx + 12, cy, cx + card_w - 12, cy], fill=(16, 185, 129, 200) if i == 0 else (139, 92, 246, 160), width=2)
        draw.text((cx + 18, cy + 12), num, font=f_stat_num, fill=(255, 255, 255, 255))
        draw.text((cx + 18, cy + 44), label, font=f_stat_label, fill=(148, 163, 184, 255))

    # Bottom Footer Divider
    draw.line([start_x, 305, W - 60, 305], fill=(255, 255, 255, 22), width=1)
    tech_str = "MintAI 2.0 Engine • Search Radar (LaTeX) • Mint+ GPA Calculator • Sub-15ms In-Memory Caching"
    draw.text((start_x, 325), tech_str, font=f_tech, fill=(100, 116, 139, 255))

    url_box_w = 215
    url_box_x = W - 60 - url_box_w
    draw_rounded_card(draw, (url_box_x, 318, url_box_x + url_box_w, 354), radius=10, fill=(16, 185, 129, 30), outline=(16, 185, 129, 180))
    draw.text((url_box_x + 18, 325), "markmint.vercel.app ↗", font=f_url, fill=(52, 211, 153, 255))

    img.save(output_path, "PNG")
    print(f"[OK] Generated High-Res Company Banner: {output_path} ({W}x{H})")


# ==============================================================================
# 4. HTML INTERACTIVE PREVIEW GENERATOR
# ==============================================================================
def generate_html_preview():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MarkMint v2.0 • LinkedIn Banners Preview</title>
  <style>
    body {
      background: #090a0f;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 40px 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #10b981, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p.subtitle {
      color: #94a3b8;
      font-size: 16px;
      margin-bottom: 40px;
    }
    .banner-card {
      background: #111827;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 40px;
      max-width: 1200px;
      width: 100%;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    .banner-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .banner-title {
      font-size: 18px;
      font-weight: 600;
      color: #e2e8f0;
    }
    .banner-tag {
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 9999px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .banner-img-container {
      position: relative;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    img.banner-img {
      width: 100%;
      height: auto;
      display: block;
    }
    .btn-download {
      display: inline-block;
      margin-top: 14px;
      padding: 10px 18px;
      background: #10b981;
      color: #042f2e;
      font-weight: 700;
      font-size: 14px;
      border-radius: 8px;
      text-decoration: none;
      transition: background 0.2s;
    }
    .btn-download:hover {
      background: #34d399;
    }
  </style>
</head>
<body>
  <h1>MarkMint v2.0 • LinkedIn Official Banners</h1>
  <p class="subtitle">Pixel-perfect banners tailored for personal profile and company page specifications.</p>

  <!-- 1. PERSONAL PROFILE BANNER -->
  <div class="banner-card">
    <div class="banner-header">
      <div class="banner-title">1. Personal LinkedIn Profile Banner (Creator / Founder)</div>
      <span class="banner-tag">1584 x 396 px (4:1 Aspect Ratio)</span>
    </div>
    <div class="banner-img-container">
      <img class="banner-img" src="/banners/linkedin_personal_banner.png" alt="Personal LinkedIn Banner">
    </div>
    <a class="btn-download" href="/banners/linkedin_personal_banner.png" download="linkedin_personal_banner_markmint.png">Download Personal Profile Banner (1584x396 PNG)</a>
  </div>

  <!-- 2. COMPANY PAGE BANNER (Standard) -->
  <div class="banner-card">
    <div class="banner-header">
      <div class="banner-title">2. MarkMint Company Page Banner (Standard LinkedIn Specs)</div>
      <span class="banner-tag">1128 x 191 px (5.91:1 Aspect Ratio)</span>
    </div>
    <div class="banner-img-container">
      <img class="banner-img" src="/banners/linkedin_company_banner_1128x191.png" alt="Company LinkedIn Banner Standard">
    </div>
    <a class="btn-download" href="/banners/linkedin_company_banner_1128x191.png" download="linkedin_company_banner_1128x191.png">Download Standard Company Banner (1128x191 PNG)</a>
  </div>

  <!-- 3. COMPANY PAGE BANNER (High-Res 4:1) -->
  <div class="banner-card">
    <div class="banner-header">
      <div class="banner-title">3. MarkMint Company Page Banner (High-Res 4:1 Ratio)</div>
      <span class="banner-tag">1584 x 396 px</span>
    </div>
    <div class="banner-img-container">
      <img class="banner-img" src="/banners/linkedin_company_banner_1584x396.png" alt="Company LinkedIn Banner High-Res">
    </div>
    <a class="btn-download" href="/banners/linkedin_company_banner_1584x396.png" download="linkedin_company_banner_1584x396.png">Download High-Res Company Banner (1584x396 PNG)</a>
  </div>
</body>
</html>
"""
    with open("public/banners/preview.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[OK] Generated HTML Preview: public/banners/preview.html")


if __name__ == "__main__":
    generate_personal_banner()
    generate_company_banner_standard()
    generate_company_banner_highres()
    generate_html_preview()
