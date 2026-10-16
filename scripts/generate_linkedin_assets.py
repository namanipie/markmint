import os
import math
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "public/branding"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def bezier_cubic(p0, p1, p2, p3, steps=60):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts

def get_lucide_leaf_points(cx, cy, size=400):
    """
    Lucide Leaf SVG paths:
    Path 1 (outline): M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z
    Path 2 (central vein): M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12
    Scaled to (cx, cy) with specified size.
    """
    scale = size / 24.0
    ox, oy = 11.5, 11.5

    leaf_pts = []
    leaf_pts.extend(bezier_cubic((11, 20), (4.5, 18), (5.5, 8.5), (9.8, 6.1)))
    leaf_pts.extend(bezier_cubic((9.8, 6.1), (14, 5), (16.5, 4), (19, 2)))
    leaf_pts.extend(bezier_cubic((19, 2), (20.2, 4.5), (21, 7), (21, 10)))
    leaf_pts.extend(bezier_cubic((21, 10), (21, 15.5), (16.5, 20), (11, 20)))

    vein_pts = []
    vein_pts.extend(bezier_cubic((2, 21), (2, 18), (4, 16), (7.08, 15)))
    vein_pts.extend(bezier_cubic((7.08, 15), (9.5, 14.5), (12, 13), (13, 12)))

    scaled_leaf = [(cx + (x - ox) * scale, cy + (y - oy) * scale) for x, y in leaf_pts]
    scaled_vein = [(cx + (x - ox) * scale, cy + (y - oy) * scale) for x, y in vein_pts]
    return scaled_leaf, scaled_vein

def draw_thick_path(draw, pts, color, width=16):
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=color, width=width)
    for p in pts:
        r = width // 2
        draw.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=color)

def generate_square_avatar(filename, bg_color, leaf_color, vein_color, glow_color=None, transparent=False):
    # Render at 4x (3200x3200) and downsample to 800x800 for cinema-grade antialiasing
    CANVAS_SIZE = 3200
    TARGET_SIZE = 800
    
    if transparent:
        img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    else:
        img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), bg_color)
    
    # Glow effect
    if glow_color and not transparent:
        glow_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow_layer)
        cx, cy = CANVAS_SIZE // 2, CANVAS_SIZE // 2
        for r in range(1200, 0, -30):
            alpha = int(45 * (1.0 - (r / 1200.0) ** 1.4))
            r_val, g_val, b_val = glow_color[:3]
            g_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(r_val, g_val, b_val, alpha))
        img = Image.alpha_composite(img, glow_layer)
    
    draw = ImageDraw.Draw(img)
    
    # Draw leaf centered
    # In Lucide, leaf center is slightly offset, so we adjust center by +40px on Y
    leaf_pts, vein_pts = get_lucide_leaf_points(CANVAS_SIZE // 2, CANVAS_SIZE // 2, size=1550)
    
    # Stroke width at 4x is ~68px
    draw_thick_path(draw, leaf_pts, leaf_color, width=68)
    draw_thick_path(draw, vein_pts, vein_color, width=68)
    
    # Downsample
    final_img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
    out_path = os.path.join(OUTPUT_DIR, filename)
    final_img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path} ({TARGET_SIZE}x{TARGET_SIZE})")

def generate_linkedin_banner():
    # LinkedIn company banner standard: 1584 x 396 px
    # Supersampled at 2x: 3168 x 792 px
    CANVAS_W, CANVAS_H = 3168, 792
    TARGET_W, TARGET_H = 1584, 396
    
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (11, 17, 16, 255))
    
    # Ambient glows
    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)
    
    # Glow left (behind logo)
    for r in range(600, 0, -20):
        alpha = int(35 * (1.0 - (r / 600.0) ** 1.4))
        g_draw.ellipse([450 - r, 396 - r, 450 + r, 396 + r], fill=(16, 185, 129, alpha))
        
    # Glow right (behind headline)
    for r in range(750, 0, -25):
        alpha = int(22 * (1.0 - (r / 750.0) ** 1.3))
        g_draw.ellipse([2100 - r, 396 - r // 2, 2100 + r, 396 + r // 2], fill=(230, 50, 122, alpha))
        
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)
    
    # Draw Logo Mark on Left
    leaf_pts, vein_pts = get_lucide_leaf_points(380, 396, size=520)
    draw_thick_path(draw, leaf_pts, (16, 185, 129, 255), width=28)
    draw_thick_path(draw, vein_pts, (16, 185, 129, 255), width=28)
    
    # Fonts
    font_dir = "C:/Windows/Fonts"
    f_brand = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 118)
    f_badge = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 44)
    f_hl_sans = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 78)
    f_hl_italic = ImageFont.truetype(os.path.join(font_dir, "georgiaz.ttf"), 84)
    f_subline = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 44)
    
    # "MarkMint" brand text
    brand_x = 640
    brand_y = 220
    draw.text((brand_x, brand_y), "MarkMint", font=f_brand, fill=(243, 240, 232, 255))
    
    # BETA badge
    badge_x = brand_x + 590
    badge_y = brand_y + 36
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 150, badge_y + 54], radius=10, fill=(44, 22, 32, 255), outline=(160, 40, 90, 255), width=3)
    draw.text((badge_x + 22, badge_y + 4), "BETA", font=f_badge, fill=(230, 50, 122, 255))
    
    # Subtitle under brand
    draw.text((brand_x, brand_y + 130), "Exam Intelligence for SRMIST", font=f_subline, fill=(184, 194, 191, 255))
    
    # Divider line
    draw.line([(1500, 180), (1500, 610)], fill=(255, 255, 255, 30), width=4)
    
    # Right side: Flagship Tagline
    tag_x = 1620
    draw.text((tag_x, 240), "Predict your exams with", font=f_hl_sans, fill=(243, 240, 232, 255))
    draw.text((tag_x, 340), "historical evidence.", font=f_hl_italic, fill=(16, 185, 129, 255))
    draw.text((tag_x, 460), "Past papers. Real patterns. Smarter preparation.", font=f_subline, fill=(184, 194, 191, 230))
    
    # Downsample
    final_img = img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    out_path = os.path.join(OUTPUT_DIR, "markmint-linkedin-banner.png")
    final_img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path} ({TARGET_W}x{TARGET_H})")

def generate_social_preview(filename, width, height, title="MarkMint", is_github=False):
    # Supersampled 2x
    CANVAS_W = width * 2
    CANVAS_H = height * 2
    
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (11, 17, 16, 255))
    
    # Ambient glows
    glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)
    
    # Emerald glow behind leaf on left
    for r in range(700, 0, -25):
        alpha = int(40 * (1.0 - (r / 700.0) ** 1.3))
        g_draw.ellipse([380 - r, CANVAS_H // 2 - r, 380 + r, CANVAS_H // 2 + r], fill=(16, 185, 129, alpha))
        
    # Magenta glow on bottom right
    for r in range(750, 0, -30):
        alpha = int(24 * (1.0 - (r / 750.0) ** 1.2))
        g_draw.ellipse([CANVAS_W - 400 - r, CANVAS_H - 200 - r // 2, CANVAS_W - 400 + r, CANVAS_H - 200 + r // 2], fill=(230, 50, 122, alpha))
        
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)
    
    # Outer subtle architectural border
    draw.rounded_rectangle([40, 40, CANVAS_W - 40, CANVAS_H - 40], radius=32, outline=(255, 255, 255, 22), width=3)
    
    # Draw Leaf Logo on Left
    leaf_cx = 380
    leaf_cy = CANVAS_H // 2
    leaf_pts, vein_pts = get_lucide_leaf_points(leaf_cx, leaf_cy, size=620)
    draw_thick_path(draw, leaf_pts, (16, 185, 129, 255), width=32)
    draw_thick_path(draw, vein_pts, (16, 185, 129, 255), width=32)
    
    # Fonts
    font_dir = "C:/Windows/Fonts"
    f_brand = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 140)
    f_badge = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 48)
    f_hl_sans = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 86)
    f_hl_serif = ImageFont.truetype(os.path.join(font_dir, "georgiaz.ttf"), 96)
    f_subline = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 50)
    f_tag = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 38)
    
    # Text Left alignment
    text_x = 760
    
    # 1. Brand Row: MarkMint + BETA badge
    brand_y = 210 if is_github else 200
    draw.text((text_x, brand_y), "MarkMint", font=f_brand, fill=(243, 240, 232, 255))
    
    badge_x = text_x + 690
    badge_y = brand_y + 44
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 160, badge_y + 60], radius=12, fill=(44, 22, 32, 255), outline=(160, 40, 90, 255), width=3)
    draw.text((badge_x + 24, badge_y + 6), "BETA", font=f_badge, fill=(230, 50, 122, 255))
    
    # 2. Main Headline
    hl_y = brand_y + 175
    draw.text((text_x, hl_y), "Predict your exams with", font=f_hl_sans, fill=(243, 240, 232, 255))
    draw.text((text_x, hl_y + 105), "historical evidence.", font=f_hl_serif, fill=(16, 185, 129, 255))
    
    # 3. Subline
    sub_y = hl_y + 235
    if is_github:
        draw.text((text_x, sub_y), "Open-Source Exam Intelligence Platform • SRMIST", font=f_subline, fill=(184, 194, 191, 230))
    else:
        draw.text((text_x, sub_y), "Past papers. Real patterns. Smarter preparation.", font=f_subline, fill=(184, 194, 191, 230))
        
    # 4. Feature Pills at bottom
    pills = [
        "9,205 Verified Questions",
        "320 Exam Papers",
        "AI Blueprint Forecasts"
    ] if not is_github else [
        "9,205 Verified Questions",
        "Next.js 15 + FastAPI",
        "Deterministic Analytics"
    ]
    
    pill_x = text_x
    pill_y = sub_y + 90
    for pill in pills:
        # Calculate text width
        bbox = draw.textbbox((0, 0), pill, font=f_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        pw = tw + 48
        ph = 68
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pw, pill_y + ph], radius=34, fill=(24, 34, 30, 255), outline=(255, 255, 255, 30), width=2)
        draw.text((pill_x + 24, pill_y + 12), pill, font=f_tag, fill=(243, 240, 232, 240))
        pill_x += pw + 24

    # Downsample
    final_img = img.resize((width, height), Image.Resampling.LANCZOS)
    out_path = filename
    final_img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path} ({width}x{height})")

def generate_svg_assets():
    svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <defs>
    <radialGradient id="mintGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#10B981" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#10B981" stop-opacity="0" />
    </radialGradient>
  </defs>
  <rect width="100" height="100" rx="22" fill="#0B1110" />
  <circle cx="50" cy="50" r="40" fill="url(#mintGlow)" />
  <g transform="translate(18, 18) scale(2.66)" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </g>
</svg>'''
    
    svg_lockup = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 120" width="100%" height="100%">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&amp;family=Inter:wght@500;600&amp;display=swap');
      .brand-title { font-family: 'Space Grotesk', -apple-system, sans-serif; font-weight: 700; font-size: 42px; fill: #F3F0E8; }
      .brand-sub { font-family: 'Inter', -apple-system, sans-serif; font-weight: 500; font-size: 14px; fill: #B8C2BF; }
      .badge-text { font-family: 'Consolas', monospace; font-weight: 700; font-size: 11px; fill: #10B981; }
    </style>
  </defs>
  <rect width="460" height="120" rx="16" fill="#0B1110" />
  <!-- Leaf Icon -->
  <g transform="translate(24, 28) scale(2.6)" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </g>
  <!-- Brand Text -->
  <text x="100" y="62" class="brand-title">MarkMint</text>
  <rect x="312" y="38" width="50" height="20" rx="4" fill="#082A1E" stroke="#10B981" stroke-width="1" />
  <text x="337" y="52" class="badge-text" text-anchor="middle" dominant-baseline="middle">BETA</text>
  <text x="102" y="88" class="brand-sub">Exam Intelligence for SRMIST</text>
</svg>'''

    with open(os.path.join(OUTPUT_DIR, "markmint-icon.svg"), "w", encoding="utf-8") as f:
        f.write(svg_icon)
    with open(os.path.join(OUTPUT_DIR, "markmint-logo.svg"), "w", encoding="utf-8") as f:
        f.write(svg_lockup)
    print("Generated SVG assets in", OUTPUT_DIR)

if __name__ == "__main__":
    # 1. Dark Emerald Avatar (Default LinkedIn Profile Logo)
    generate_square_avatar(
        "markmint-logo-emerald-dark.png",
        bg_color=(11, 17, 16, 255),
        leaf_color=(16, 185, 129, 255),
        vein_color=(16, 185, 129, 255),
        glow_color=(16, 185, 129)
    )
    
    # 2. Electric Pink Accent Avatar (Poster signature edition)
    generate_square_avatar(
        "markmint-logo-pink-dark.png",
        bg_color=(11, 17, 16, 255),
        leaf_color=(230, 50, 122, 255),
        vein_color=(230, 50, 122, 255),
        glow_color=(230, 50, 122)
    )

    # 3. Transparent PNG
    generate_square_avatar(
        "markmint-logo-transparent.png",
        bg_color=None,
        leaf_color=(16, 185, 129, 255),
        vein_color=(16, 185, 129, 255),
        glow_color=None,
        transparent=True
    )
    
    # 4. Light Mode / Ivory Clean Edition
    generate_square_avatar(
        "markmint-logo-light.png",
        bg_color=(247, 246, 242, 255),
        leaf_color=(0, 104, 56, 255),
        vein_color=(0, 104, 56, 255),
        glow_color=None
    )

    # 5. LinkedIn Cover Banner
    generate_linkedin_banner()

    # 6. GitHub Social Preview (1280x640)
    generate_social_preview(
        os.path.join(OUTPUT_DIR, "github-social-preview.png"),
        width=1280,
        height=640,
        title="MarkMint",
        is_github=True
    )

    # 7. Website OpenGraph Image (1200x630)
    generate_social_preview(
        os.path.join(OUTPUT_DIR, "site-og-image.png"),
        width=1200,
        height=630,
        title="MarkMint",
        is_github=False
    )
    # Also save to public/og-image.png for standard direct URL serving
    generate_social_preview(
        "public/og-image.png",
        width=1200,
        height=630,
        title="MarkMint",
        is_github=False
    )

    # 8. SVG Assets
    generate_svg_assets()

