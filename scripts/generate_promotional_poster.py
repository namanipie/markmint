import os
import re
import math
from PIL import Image, ImageDraw, ImageFont

def bezier_cubic(p0, p1, p2, p3, steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts

def get_lucide_leaf_points(cx, cy, size=80):
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

def build_promotional_poster(output_path="public/promotional-poster.png"):
    WIDTH = 2480
    HEIGHT = 3508

    # Base background: Deep green-black from MarkMint website (#0B1110)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (11, 17, 16, 255))

    # Ambient glow
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Upper glow behind headline
    for r in range(650, 0, -20):
        alpha = int(18 * (1.0 - (r / 650.0) ** 1.3))
        glow_draw.ellipse([WIDTH // 2 - r, 780 - r // 2, WIDTH // 2 + r, 780 + r // 2], fill=(230, 50, 122, alpha))

    # Lower subtle glow behind QR / CTA
    for r in range(550, 0, -20):
        alpha = int(14 * (1.0 - (r / 550.0) ** 1.2))
        glow_draw.ellipse([1900 - r, 2550 - r // 2, 1900 + r, 2550 + r // 2], fill=(230, 50, 122, alpha))

    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_dir = "C:/Windows/Fonts"
    f_brand = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 62)
    f_beta = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 22)
    f_subline = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 30)

    # Headline fonts: Exact editorial contrast (Bold Sans + Italic Serif in Pink)
    # Scaled up for immediate 3-second communication
    f_hl_sans = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 156)
    f_hl_serif = ImageFont.truetype(os.path.join(font_dir, "georgiaz.ttf"), 174)

    f_subhead = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 50)
    f_feat_pill = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 34)

    # UI Fonts inside laptop frame (clean and clearly legible)
    f_ui_logo = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 28)
    f_ui_nav = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 22)
    f_ui_code = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 26)
    f_ui_status = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 17)
    f_ui_head = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 30)
    f_ui_item = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 25)

    f_cta_title = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 56)
    f_url = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 42)
    f_qr_label = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 32)
    f_footer = ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 24)

    # Colors
    C_PINK = (230, 50, 122, 255)         # Hot pink #E6327A
    C_WHITE = (243, 240, 232, 255)       # Warm white #F3F0E8
    C_MUTED = (184, 194, 191, 255)       # Muted gray-blue #B8C2BF
    C_DIM = (100, 114, 110, 255)         # Dim gray
    C_GREEN = (16, 185, 129, 255)        # Emerald green
    C_CARD_BG = (17, 25, 23, 255)        # #111917
    C_BORDER = (45, 58, 54, 255)         # Subtle border
    C_BORDER_LINE = (35, 46, 42, 255)

    MARGIN_X = 160

    # ========================================================
    # 1. BRAND HEADER (TOP LEFT ONLY)
    # ========================================================
    top_y = 250

    # Leaf Icon
    leaf_pts, vein_pts = get_lucide_leaf_points(MARGIN_X + 30, top_y + 32, size=58)
    draw.line(leaf_pts, fill=C_PINK, width=4, joint="curve")
    draw.line(vein_pts, fill=C_PINK, width=4, joint="curve")

    # Wordmark
    draw.text((MARGIN_X + 80, top_y), "MarkMint", font=f_brand, fill=C_WHITE)

    # BETA badge
    brand_w = f_brand.getlength("MarkMint")
    beta_x = MARGIN_X + 80 + int(brand_w) + 16
    draw.rounded_rectangle([beta_x, top_y + 14, beta_x + 76, top_y + 48], radius=4,
                           fill=(44, 22, 32, 255), outline=(160, 40, 90, 255), width=1)
    draw.text((beta_x + 13, top_y + 20), "BETA", font=f_beta, fill=C_PINK)

    # "For SRMIST Students" directly below
    draw.text((MARGIN_X + 82, top_y + 72), "For SRMIST Students", font=f_subline, fill=C_MUTED)

    # ========================================================
    # 2. MAIN HEADLINE (EXACT EDITORIAL CONTRAST)
    # Communicates what MarkMint does in 3 seconds:
    # "Predict your exams with" (Bold white sans-serif)
    # "historical evidence." (Italic serif in MarkMint pink)
    # "Past papers. Real patterns. Smarter preparation."
    # ========================================================
    hl_y = top_y + 220

    draw.text((MARGIN_X, hl_y), "Predict your exams with", font=f_hl_sans, fill=C_WHITE)
    draw.text((MARGIN_X, hl_y + 175), "historical evidence.", font=f_hl_serif, fill=C_PINK)

    # Subhead
    sub_y = hl_y + 390
    draw.text((MARGIN_X, sub_y), "Past papers. Real patterns. Smarter preparation.", font=f_subhead, fill=C_MUTED)

    # ========================================================
    # 3. THREE COMPACT FEATURE ITEMS (ONE CLEAN HORIZONTAL ROW)
    # "Past Paper Intelligence · AI Exam Forecasts · Study Plans"
    # Compact bordered capsules with small line icons
    # ========================================================
    feat_y = sub_y + 115
    features = [
        ("Past Paper Intelligence", "chart"),
        ("AI Exam Forecasts", "forecast"),
        ("Study Plans", "plan")
    ]

    p_curr_x = MARGIN_X
    pill_gap = 24
    pill_h = 74

    for title, icon_type in features:
        tw = int(f_feat_pill.getlength(title))
        pw = tw + 92  # icon + padding

        # Compact pill container
        draw.rounded_rectangle([p_curr_x, feat_y, p_curr_x + pw, feat_y + pill_h], radius=37,
                               fill=(14, 22, 19, 255), outline=(45, 58, 54, 255), width=1)

        # Small line icon
        ic_x = p_curr_x + 32
        ic_y = feat_y + pill_h // 2

        if icon_type == "chart":
            draw.line([ic_x - 8, ic_y + 9, ic_x - 8, ic_y - 3], fill=C_PINK, width=2)
            draw.line([ic_x, ic_y + 9, ic_x, ic_y - 9], fill=C_PINK, width=2)
            draw.line([ic_x + 8, ic_y + 9, ic_x + 8, ic_y - 14], fill=C_PINK, width=2)
            draw.line([ic_x - 12, ic_y + 11, ic_x + 12, ic_y + 11], fill=C_WHITE, width=2)
        elif icon_type == "forecast":
            draw.line([ic_x - 10, ic_y + 7, ic_x - 3, ic_y - 2, ic_x + 3, ic_y + 3, ic_x + 10, ic_y - 9],
                      fill=C_PINK, width=2)
            draw.ellipse([ic_x + 7, ic_y - 12, ic_x + 13, ic_y - 6], fill=C_WHITE)
        elif icon_type == "plan":
            draw.rounded_rectangle([ic_x - 9, ic_y - 12, ic_x + 9, ic_y + 12], radius=3, outline=C_PINK, width=2)
            draw.line([ic_x - 4, ic_y - 5, ic_x + 4, ic_y - 5], fill=C_WHITE, width=2)
            draw.line([ic_x - 4, ic_y, ic_x + 3, ic_y], fill=C_WHITE, width=2)
            draw.line([ic_x - 4, ic_y + 5, ic_x + 1, ic_y + 5], fill=C_PINK, width=2)

        # Title
        draw.text((p_curr_x + 66, feat_y + 18), title, font=f_feat_pill, fill=C_WHITE)
        p_curr_x += pw + pill_gap

    # ========================================================
    # 4. SMALLER, CLEAN MINTAI DASHBOARD PREVIEW
    # Reduced to ~48% of original size (660px vs 1380px)
    # Secondary visual rather than dominant element.
    # No tiny micro-text paragraphs. Visually clear 3 elements:
    # - High-Yield Topics
    # - Question Recurrence
    # - Study Plan
    # ========================================================
    lap_y = feat_y + 155
    lap_w = WIDTH - 2 * MARGIN_X
    lap_h = 560
    lap_x = MARGIN_X

    # Laptop Outer Aluminum Chassis
    draw.rounded_rectangle([lap_x, lap_y, lap_x + lap_w, lap_y + lap_h], radius=20,
                           fill=(18, 24, 21, 255), outline=(48, 60, 54, 255), width=2)

    # Inner Screen Surface
    scr_pad = 14
    scr_x = lap_x + scr_pad
    scr_y = lap_y + scr_pad
    scr_w = lap_w - 2 * scr_pad
    scr_h = lap_h - 38

    draw.rounded_rectangle([scr_x, scr_y, scr_x + scr_w, scr_y + scr_h], radius=12,
                           fill=(11, 17, 16, 255))

    # Screen Nav Bar (Minimal, clean)
    nav_h = 58
    draw.line([scr_x, scr_y + nav_h, scr_x + scr_w, scr_y + nav_h], fill=(255, 255, 255, 14), width=1)

    # Nav: Leaf + MarkMint + BETA
    ui_l, ui_v = get_lucide_leaf_points(scr_x + 32, scr_y + 29, size=24)
    draw.line(ui_l, fill=C_PINK, width=2, joint="curve")
    draw.line(ui_v, fill=C_PINK, width=2, joint="curve")
    draw.text((scr_x + 54, scr_y + 15), "MarkMint", font=f_ui_logo, fill=C_WHITE)
    draw.rounded_rectangle([scr_x + 184, scr_y + 18, scr_x + 232, scr_y + 38], radius=3,
                           fill=(44, 22, 32, 255), outline=(160, 40, 90, 255), width=1)
    draw.text((scr_x + 192, scr_y + 21), "BETA", font=ImageFont.truetype(os.path.join(font_dir, "consolab.ttf"), 13), fill=C_PINK)

    # Nav links
    ui_navs = [("Home", False), ("Courses", False), ("MintAI", True), ("Study Plan", False)]
    nx = scr_x + 290
    for ntext, is_active in ui_navs:
        col = C_WHITE if is_active else C_MUTED
        draw.text((nx, scr_y + 17), ntext, font=f_ui_nav, fill=col)
        if is_active:
            draw.line([nx, scr_y + 44, nx + 62, scr_y + 44], fill=C_PINK, width=2)
        nx += 120

    # Course scope + Status on right side of nav bar
    code_text = "18MAB101T // Calculus & Linear Algebra"
    code_w = f_ui_code.getlength(code_text)
    stat_box_w = 190
    right_align_x = scr_x + scr_w - 30 - stat_box_w - int(code_w) - 24
    draw.text((right_align_x, scr_y + 16), code_text, font=f_ui_code, fill=C_MUTED)

    stat_x = scr_x + scr_w - 30 - stat_box_w
    stat_y = scr_y + 14
    draw.rounded_rectangle([stat_x, stat_y, stat_x + stat_box_w, stat_y + 30], radius=15,
                           fill=(12, 38, 30, 255), outline=(20, 110, 78, 255), width=1)
    draw.ellipse([stat_x + 12, stat_y + 11, stat_x + 20, stat_y + 19], fill=C_GREEN)
    draw.text((stat_x + 28, stat_y + 7), "Calibrated Evidence", font=f_ui_status, fill=C_GREEN)

    # THREE CLEAN VISUAL PILLARS / CARDS ACROSS
    # 1. High-Yield Topics
    # 2. Question Recurrence
    # 3. Study Plan
    content_y = scr_y + nav_h + 20
    card_gap = 20
    card_w = (scr_w - 60 - 2 * card_gap) // 3
    card_h = scr_h - (content_y - scr_y) - 20

    # Card 1: High-Yield Topics
    c1_x = scr_x + 30
    draw.rounded_rectangle([c1_x, content_y, c1_x + card_w, content_y + card_h], radius=10,
                           fill=(15, 22, 19, 255), outline=(32, 44, 38, 255), width=1)
    draw.text((c1_x + 24, content_y + 20), "High-Yield Topics", font=f_ui_head, fill=C_WHITE)
    draw.line([c1_x + 24, content_y + 60, c1_x + card_w - 24, content_y + 60], fill=(28, 38, 33, 255), width=1)

    topics_simple = [
        ("Laplace Transforms", 0.92),
        ("Eigenvalues & Vectors", 0.78),
        ("Multiple Integrals", 0.64)
    ]
    t_start_y = content_y + 90
    t_step = 100
    for idx, (tname, bpct) in enumerate(topics_simple):
        ty = t_start_y + idx * t_step
        draw.text((c1_x + 24, ty), tname, font=f_ui_item, fill=C_WHITE)
        bar_w = card_w - 48
        bar_y = ty + 38
        draw.rounded_rectangle([c1_x + 24, bar_y, c1_x + 24 + bar_w, bar_y + 9], radius=4, fill=(24, 34, 29, 255))
        draw.rounded_rectangle([c1_x + 24, bar_y, c1_x + 24 + int(bar_w * bpct), bar_y + 9], radius=4, fill=C_PINK)

    # Card 2: Question Recurrence
    c2_x = c1_x + card_w + card_gap
    draw.rounded_rectangle([c2_x, content_y, c2_x + card_w, content_y + card_h], radius=10,
                           fill=(15, 22, 19, 255), outline=(32, 44, 38, 255), width=1)
    draw.text((c2_x + 24, content_y + 20), "Question Recurrence", font=f_ui_head, fill=C_WHITE)
    draw.line([c2_x + 24, content_y + 60, c2_x + card_w - 24, content_y + 60], fill=(28, 38, 33, 255), width=1)

    recur_simple = [
        "Cayley-Hamilton Verification",
        "Analytic Functions & CR Eq.",
        "Matrix Diagonalization"
    ]
    r_start_y = content_y + 95
    r_step = 95
    for idx, rname in enumerate(recur_simple):
        ry = r_start_y + idx * r_step
        draw.ellipse([c2_x + 24, ry + 6, c2_x + 36, ry + 18], fill=C_PINK)
        draw.text((c2_x + 48, ry), rname, font=f_ui_item, fill=C_WHITE)

    # Card 3: Study Plan
    c3_x = c2_x + card_w + card_gap
    draw.rounded_rectangle([c3_x, content_y, c3_x + card_w, content_y + card_h], radius=10,
                           fill=(15, 22, 19, 255), outline=(32, 44, 38, 255), width=1)
    draw.text((c3_x + 24, content_y + 20), "Study Plan", font=f_ui_head, fill=C_WHITE)
    draw.line([c3_x + 24, content_y + 60, c3_x + card_w - 24, content_y + 60], fill=(28, 38, 33, 255), width=1)

    plan_simple = [
        ("Phase 1: High-Yield Core", True),
        ("Phase 2: Question Patterns", False),
        ("Phase 3: Targeted Revision", False)
    ]
    p_start_y = content_y + 95
    p_step = 95
    for idx, (pname, is_act) in enumerate(plan_simple):
        py = p_start_y + idx * p_step
        draw.ellipse([c3_x + 24, py + 6, c3_x + 36, py + 18],
                     fill=C_PINK if is_act else (60, 75, 68, 255))
        draw.text((c3_x + 48, py), pname, font=f_ui_item, fill=C_WHITE if is_act else C_MUTED)

    # Laptop Bottom Lip
    lip_y = lap_y + lap_h - 14
    draw.rounded_rectangle([lap_x + 160, lip_y, lap_x + lap_w - 160, lip_y + 12], radius=4,
                           fill=(26, 34, 30, 255), outline=(42, 54, 48, 255), width=1)

    # ========================================================
    # 5. LOWER SECTION: CTA & CLEAN SCANNABLE QR CODE
    # Naturally positioned in lower third
    # Strictly only:
    # "Built specifically for SRMIST students."
    # "markmint.vercel.app"
    # "Scan to start predicting"
    # ========================================================
    cta_y = lap_y + lap_h + 200
    draw.line([MARGIN_X, cta_y, WIDTH - MARGIN_X, cta_y], fill=C_BORDER_LINE, width=1)

    # Left CTA
    left_y = cta_y + 90
    draw.text((MARGIN_X, left_y), "Built specifically for SRMIST students.", font=f_cta_title, fill=C_WHITE)

    # Domain Capsule
    url_box_y = left_y + 105
    url_box_w = 700
    url_box_h = 96
    draw.rounded_rectangle([MARGIN_X, url_box_y, MARGIN_X + url_box_w, url_box_y + url_box_h], radius=14,
                           fill=C_CARD_BG, outline=C_PINK, width=2)

    # Globe icon in pink
    gb_cx, gb_cy = MARGIN_X + 52, url_box_y + url_box_h // 2
    draw.ellipse([gb_cx - 22, gb_cy - 22, gb_cx + 22, gb_cy + 22], outline=C_PINK, width=2)
    draw.line([gb_cx - 22, gb_cy, gb_cx + 22, gb_cy], fill=C_PINK, width=2)
    draw.ellipse([gb_cx - 10, gb_cy - 22, gb_cx + 10, gb_cy + 22], outline=C_PINK, width=2)

    draw.text((MARGIN_X + 102, url_box_y + 25), "markmint.vercel.app", font=f_url, fill=C_WHITE)

    # Right QR Code Area (Crisp, perfectly scannable, well-proportioned)
    qr_card_size = 400
    qr_card_x = WIDTH - MARGIN_X - qr_card_size
    qr_card_y = cta_y + 90

    # Label centered above QR
    qr_lbl = "Scan to start predicting"
    w_qlbl = f_qr_label.getlength(qr_lbl)
    draw.text((qr_card_x + qr_card_size // 2 - int(w_qlbl) // 2, cta_y + 32),
              qr_lbl, font=f_qr_label, fill=C_WHITE)

    # Pink corner brackets
    b_len = 40
    b_w = 4
    draw.line([qr_card_x - 14, qr_card_y - 14, qr_card_x - 14 + b_len, qr_card_y - 14], fill=C_PINK, width=b_w)
    draw.line([qr_card_x - 14, qr_card_y - 14, qr_card_x - 14, qr_card_y - 14 + b_len], fill=C_PINK, width=b_w)
    draw.line([qr_card_x + qr_card_size + 14, qr_card_y - 14, qr_card_x + qr_card_size + 14 - b_len, qr_card_y - 14], fill=C_PINK, width=b_w)
    draw.line([qr_card_x + qr_card_size + 14, qr_card_y - 14, qr_card_x + qr_card_size + 14, qr_card_y - 14 + b_len], fill=C_PINK, width=b_w)
    draw.line([qr_card_x - 14, qr_card_y + qr_card_size + 14, qr_card_x - 14 + b_len, qr_card_y + qr_card_size + 14], fill=C_PINK, width=b_w)
    draw.line([qr_card_x - 14, qr_card_y + qr_card_size + 14, qr_card_x - 14, qr_card_y + qr_card_size + 14 - b_len], fill=C_PINK, width=b_w)
    draw.line([qr_card_x + qr_card_size + 14, qr_card_y + qr_card_size + 14, qr_card_x + qr_card_size + 14 - b_len, qr_card_y + qr_card_size + 14], fill=C_PINK, width=b_w)
    draw.line([qr_card_x + qr_card_size + 14, qr_card_y + qr_card_size + 14, qr_card_x + qr_card_size + 14, qr_card_y + qr_card_size + 14 - b_len], fill=C_PINK, width=b_w)

    # Pure white card base
    draw.rounded_rectangle([qr_card_x, qr_card_y, qr_card_x + qr_card_size, qr_card_y + qr_card_size], radius=18,
                           fill=(255, 255, 255, 255))

    # Vector QR parsing from public/qr-code.svg
    qr_pad = 30
    qr_draw_x = qr_card_x + qr_pad
    qr_draw_y = qr_card_y + qr_pad
    qr_avail = qr_card_size - 2 * qr_pad

    with open("public/qr-code.svg", "r", encoding="utf-8") as f:
        svg_content = f.read()

    matches = re.findall(r"M\s*(\d+),(\d+)\s*l\s*(\d+),0\s*0,(\d+)\s*-(\d+),0\s*z", svg_content)
    scale = qr_avail / 300.0
    for m in matches:
        sx, sy, sw, sh = int(m[0]), int(m[1]), int(m[2]), int(m[3])
        rx1 = int(qr_draw_x + sx * scale)
        ry1 = int(qr_draw_y + sy * scale)
        rx2 = int(qr_draw_x + (sx + sw) * scale)
        ry2 = int(qr_draw_y + (sy + sh) * scale)
        draw.rectangle([rx1, ry1, rx2, ry2], fill=(11, 17, 16, 255))

    # URL below QR code
    qr_url = "markmint.vercel.app"
    w_qurl = f_footer.getlength(qr_url)
    draw.text((qr_card_x + qr_card_size // 2 - int(w_qurl) // 2, qr_card_y + qr_card_size + 30),
              qr_url, font=f_footer, fill=C_MUTED)

    # ========================================================
    # 6. BOTTOM MICRO FOOTER
    # Strictly: LEARN // PLAN // PREPARE // SCORE
    # Positioned with comfortable breathing space, perfectly balanced
    # ========================================================
    bot_y = qr_card_y + qr_card_size + 180
    div_text = "LEARN   //   PLAN   //   PREPARE   //   SCORE"
    w_div = f_footer.getlength(div_text)
    draw.line([MARGIN_X, bot_y, WIDTH // 2 - w_div // 2 - 40, bot_y], fill=C_BORDER_LINE, width=1)
    draw.text((WIDTH // 2 - w_div // 2, bot_y - 12), div_text, font=f_footer, fill=C_DIM)
    draw.line([WIDTH // 2 + w_div // 2 + 40, bot_y, WIDTH - MARGIN_X, bot_y], fill=C_BORDER_LINE, width=1)

    # Save 300 DPI PNG
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.convert("RGB").save(output_path, "PNG", dpi=(300, 300))
    print(f"Successfully generated 300 DPI promotional poster at {output_path}")

if __name__ == "__main__":
    build_promotional_poster("public/promotional-poster.png")
