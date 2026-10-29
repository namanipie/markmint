import os
import re
from PIL import Image, ImageDraw, ImageFont

def build_poster(embed_qr=False, output_path="public/poster.png"):
    # A4 at 300 DPI: 2480 x 3508 pixels
    WIDTH = 2480
    HEIGHT = 3508

    # Create base dark obsidian image
    img = Image.new("RGBA", (WIDTH, HEIGHT), (9, 10, 15, 255))
    
    # Layer for alpha-blended glows
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    center_x, center_y = 1650, 1450
    for r in range(950, 0, -20):
        alpha = int(36 * (1.0 - (r / 950.0) ** 1.5))
        glow_draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=(124, 58, 237, alpha))
    img = Image.alpha_composite(img, glow_layer)

    draw = ImageDraw.Draw(img)

    # Fonts
    font_dir = "C:/Windows/Fonts"
    f_brand = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 46)
    f_meta = ImageFont.truetype(os.path.join(font_dir, "consola.ttf"), 22)
    f_headline = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 165)
    f_flow = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 66)
    f_flow_hero = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 70)
    f_support = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 34)
    f_scan = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 115)
    f_url = ImageFont.truetype(os.path.join(font_dir, "consola.ttf"), 42)
    f_qr_place = ImageFont.truetype(os.path.join(font_dir, "bahnschrift.ttf"), 30)
    f_qr_sub = ImageFont.truetype(os.path.join(font_dir, "consola.ttf"), 20)
    f_tag = ImageFont.truetype(os.path.join(font_dir, "consola.ttf"), 22)

    # Subtle Background Matrix Grid
    for x in range(120, WIDTH - 120, 80):
        for y in range(120, HEIGHT - 120, 80):
            draw.rectangle([x, y, x + 2, y + 2], fill=(255, 255, 255, 18))

    # Outer Architectural Frame (120px = 10mm margin)
    draw.rectangle([120, 120, WIDTH - 120, HEIGHT - 120], outline=(255, 255, 255, 28), width=2)

    # Corner Registration Crosshairs
    def draw_crosshair(cx, cy):
        draw.line([cx - 28, cy, cx + 28, cy], fill=(139, 92, 246, 200), width=3)
        draw.line([cx, cy - 28, cx, cy + 28], fill=(139, 92, 246, 200), width=3)

    draw_crosshair(120, 120)
    draw_crosshair(WIDTH - 120, 120)
    draw_crosshair(120, HEIGHT - 120)
    draw_crosshair(WIDTH - 120, HEIGHT - 120)

    # Top Margin Coordinates
    draw.text((160, 80), "SRMIST // ACADEMIC INTELLIGENCE", font=f_meta, fill=(130, 140, 155, 255))
    draw.text((WIDTH - 430, 80), "A4 PORTRAIT // 300 DPI", font=f_meta, fill=(130, 140, 155, 255))

    # ========================================================
    # 1. BRAND HEADER
    # ========================================================
    draw.rounded_rectangle([200, 240, 252, 292], radius=10, fill=(139, 92, 246, 255))
    draw.polygon([(214, 252), (238, 252), (238, 276), (226, 276), (214, 264)], fill=(9, 10, 15, 255))
    draw.text((272, 242), "MARKMINT", font=f_brand, fill=(255, 255, 255, 255))

    # Header Divider
    draw.line([200, 330, WIDTH - 200, 330], fill=(255, 255, 255, 24), width=2)

    # ========================================================
    # 2. DOMINANT HEADLINE
    # ========================================================
    draw.text((200, 470), "STOP GUESSING", font=f_headline, fill=(255, 255, 255, 255))
    draw.text((200, 650), "WHAT TO STUDY", font=f_headline, fill=(255, 255, 255, 255))
    w_text = f_headline.getlength("WHAT TO STUDY")
    # Clean purple square period exactly aligned with baseline
    draw.rectangle([200 + w_text + 4, 765, 200 + w_text + 34, 795], fill=(168, 85, 247, 255))

    # ========================================================
    # 3. CENTRAL WORKSPACE: FLOW (LEFT) + MOTIF (RIGHT)
    # ========================================================
    start_y = 1040
    step_gap = 145

    flow_steps = [
        ("Historical PYQs", False),
        ("Exam Patterns", False),
        ("What Matters", True),
        ("Study", False),
        ("Practice", False)
    ]

    curr_y = start_y
    for i, (text, is_hero) in enumerate(flow_steps):
        node_x = 225
        node_y = curr_y + 36

        if is_hero:
            text_w = f_flow_hero.getlength(text)
            # Solid dark pill with vibrant purple border
            draw.rounded_rectangle([270, curr_y - 12, 270 + text_w + 60, curr_y + 82], radius=14,
                                   fill=(35, 24, 60, 255), outline=(167, 139, 250, 255), width=3)
            # Glowing node
            draw.ellipse([node_x - 22, node_y - 22, node_x + 22, node_y + 22], outline=(167, 139, 250, 255), width=3)
            draw.ellipse([node_x - 12, node_y - 12, node_x + 12, node_y + 12], fill=(255, 255, 255, 255))
            draw.text((295, curr_y - 2), text, font=f_flow_hero, fill=(255, 255, 255, 255))
        else:
            draw.ellipse([node_x - 18, node_y - 18, node_x + 18, node_y + 18], outline=(139, 92, 246, 160), width=2)
            draw.ellipse([node_x - 8, node_y - 8, node_x + 8, node_y + 8], fill=(139, 92, 246, 255))
            draw.text((280, curr_y), text, font=f_flow, fill=(240, 242, 245, 255))

        # Down arrow connector line
        if i < len(flow_steps) - 1:
            line_top = node_y + 24
            line_bot = line_top + 64
            draw.line([node_x, line_top, node_x, line_bot], fill=(139, 92, 246, 220), width=3)
            # Crisp downward arrowhead
            draw.polygon([(node_x - 7, line_bot - 4), (node_x + 7, line_bot - 4), (node_x, line_bot + 8)], fill=(167, 139, 250, 255))

        curr_y += step_gap

    # Small Supporting Text under Flow
    draw.rectangle([200, curr_y + 52, 235, curr_y + 56], fill=(139, 92, 246, 255))
    draw.text((255, curr_y + 36), "Built from past SRM exam papers.", font=f_support, fill=(156, 163, 175, 255))

    # ========================================================
    # RIGHT COLUMN: ABSTRACT MINIMALIST DATA MOTIF
    # ========================================================
    motif_x = 1380
    motif_y = 1000
    motif_w = 900
    motif_h = 980

    # Motif Frame Box
    draw.rounded_rectangle([motif_x, motif_y, motif_x + motif_w, motif_y + motif_h], radius=20,
                           fill=(15, 16, 24, 255), outline=(255, 255, 255, 28), width=2)

    draw.text((motif_x + 40, motif_y + 35), "// DATA TRANSFORMATION ARCHITECTURE", font=f_meta, fill=(120, 130, 145, 255))
    draw.line([motif_x + 40, motif_y + 72, motif_x + motif_w - 40, motif_y + 72], fill=(255, 255, 255, 20), width=1)

    # 1. Stacked Exam Paper Wireframes (Top)
    # Sheet 3 (Back)
    s3_x, s3_y = motif_x + 200, motif_y + 115
    draw.rounded_rectangle([s3_x + 40, s3_y - 15, s3_x + 460, s3_y + 240], radius=10,
                           fill=(20, 21, 32, 255), outline=(255, 255, 255, 30), width=2)

    # Sheet 2 (Mid)
    s2_x, s2_y = motif_x + 220, motif_y + 130
    draw.rounded_rectangle([s2_x + 20, s2_y - 5, s2_x + 440, s2_y + 250], radius=10,
                           fill=(24, 22, 40, 255), outline=(139, 92, 246, 70), width=2)

    # Sheet 1 (Front Exam Paper Wireframe)
    s1_x, s1_y = motif_x + 240, motif_y + 148
    draw.rounded_rectangle([s1_x, s1_y, s1_x + 420, s1_y + 268], radius=10,
                           fill=(22, 18, 38, 255), outline=(167, 139, 250, 160), width=3)
    # Paper title / subject header rule
    draw.line([s1_x + 35, s1_y + 44, s1_x + 190, s1_y + 44], fill=(167, 139, 250, 255), width=4)
    draw.rounded_rectangle([s1_x + 330, s1_y + 30, s1_x + 385, s1_y + 56], radius=4, fill=(139, 92, 246, 90))
    
    # Exam question simulated lines
    for q_idx, q_offset in enumerate([85, 118, 151, 184, 217]):
        w_line = 350 if q_idx != 4 else 260
        draw.line([s1_x + 35, s1_y + q_offset, s1_x + 35 + w_line, s1_y + q_offset],
                  fill=(255, 255, 255, 75 if q_idx != 0 else 130), width=2)

    # 2. Analytical Convergence Lines
    mid_cx = motif_x + motif_w // 2
    prism_y = motif_y + 590

    for rx in [-220, -110, 0, 110, 220]:
        draw.line([mid_cx + rx, motif_y + 430, mid_cx, prism_y], fill=(167, 139, 250, 100 if rx != 0 else 240), width=2 if rx != 0 else 3)

    # Analytical Frequency Spectrogram Box
    bar_box_y = motif_y + 480
    draw.rounded_rectangle([mid_cx - 180, bar_box_y, mid_cx + 180, bar_box_y + 42], radius=8,
                           fill=(28, 24, 46, 255), outline=(139, 92, 246, 120), width=2)
    bar_heights = [18, 28, 14, 32, 22, 12, 30, 18, 26, 16, 24]
    for bi, bh in enumerate(bar_heights):
        bx = mid_cx - 155 + bi * 28
        draw.rectangle([bx, bar_box_y + 32 - bh, bx + 12, bar_box_y + 32], fill=(192, 132, 252, 240))

    # Central Focal Crystal (What Matters)
    draw.ellipse([mid_cx - 60, prism_y - 60, mid_cx + 60, prism_y + 60], fill=(42, 28, 75, 255))
    draw.ellipse([mid_cx - 40, prism_y - 40, mid_cx + 40, prism_y + 40], fill=(76, 35, 140, 255), outline=(167, 139, 250, 255), width=3)
    draw.polygon([(mid_cx, prism_y - 24), (mid_cx + 24, prism_y), (mid_cx, prism_y + 24), (mid_cx - 24, prism_y)], fill=(255, 255, 255, 255))

    # 3. Output Study & Practice High-Yield Cards
    out_y = prism_y + 105
    draw.line([mid_cx, prism_y + 40, mid_cx, out_y], fill=(139, 92, 246, 255), width=4)

    # Card 1: High-Yield Insights
    c1_x = mid_cx - 320
    draw.rounded_rectangle([c1_x, out_y + 10, c1_x + 300, out_y + 170], radius=14,
                           fill=(20, 22, 34, 255), outline=(167, 139, 250, 140), width=2)
    draw.ellipse([c1_x + 35, out_y + 45, c1_x + 55, out_y + 65], fill=(139, 92, 246, 255))
    draw.line([c1_x + 70, out_y + 55, c1_x + 260, out_y + 55], fill=(255, 255, 255, 240), width=4)
    draw.line([c1_x + 35, out_y + 95, c1_x + 265, out_y + 95], fill=(255, 255, 255, 70), width=2)
    draw.line([c1_x + 35, out_y + 125, c1_x + 205, out_y + 125], fill=(255, 255, 255, 70), width=2)

    # Card 2: Precision Practice
    c2_x = mid_cx + 20
    draw.rounded_rectangle([c2_x, out_y + 10, c2_x + 300, out_y + 170], radius=14,
                           fill=(20, 22, 34, 255), outline=(167, 139, 250, 140), width=2)
    draw.ellipse([c2_x + 35, out_y + 45, c2_x + 55, out_y + 65], fill=(192, 132, 252, 255))
    draw.line([c2_x + 70, out_y + 55, c2_x + 260, out_y + 55], fill=(255, 255, 255, 240), width=4)
    # Reticle
    draw.ellipse([c2_x + 150 - 32, out_y + 115 - 32, c2_x + 150 + 32, out_y + 115 + 32], outline=(139, 92, 246, 200), width=2)
    draw.ellipse([c2_x + 150 - 15, out_y + 115 - 15, c2_x + 150 + 15, out_y + 115 + 15], fill=(139, 92, 246, 120), outline=(167, 139, 250, 255), width=2)
    draw.ellipse([c2_x + 150 - 4, out_y + 115 - 4, c2_x + 150 + 4, out_y + 115 + 4], fill=(255, 255, 255, 255))

    draw.text((mid_cx - 285, out_y + 210), "RAW EXAMS  ->  REPETITION PATTERNS  ->  HIGH-YIELD MASTERY", font=f_meta, fill=(140, 150, 165, 255))

    # ========================================================
    # 4. BOTTOM SECTION: CALL TO ACTION & QR PLACEHOLDER
    # ========================================================
    footer_y = 2640
    draw.line([200, footer_y, WIDTH - 200, footer_y], fill=(255, 255, 255, 25), width=2)

    # Action Copy & Domain (Left)
    cta_y = footer_y + 90
    draw.rounded_rectangle([200, cta_y, 440, cta_y + 50], radius=8, fill=(35, 24, 60, 255), outline=(139, 92, 246, 200), width=2)
    draw.text((235, cta_y + 12), "INSTANT ACCESS", font=f_tag, fill=(192, 132, 252, 255))

    draw.text((200, cta_y + 95), "SCAN TO TRY", font=f_scan, fill=(255, 255, 255, 255))

    # Domain Pill Box (Dark high-contrast with purple border)
    url_y = cta_y + 260
    draw.rounded_rectangle([200, url_y, 840, url_y + 96], radius=16,
                           fill=(18, 20, 30, 255), outline=(139, 92, 246, 180), width=2)
    
    # Globe icon
    draw.ellipse([235, url_y + 24, 283, url_y + 72], outline=(167, 139, 250, 255), width=3)
    draw.line([235, url_y + 48, 283, url_y + 48], fill=(167, 139, 250, 255), width=2)
    draw.ellipse([247, url_y + 24, 271, url_y + 72], outline=(167, 139, 250, 255), width=2)
    draw.text((315, url_y + 27), "markmint.vercel.app", font=f_url, fill=(255, 255, 255, 255))

    # Direct arrow pointing towards QR
    arrow_x = 900
    arrow_y = url_y + 48
    draw.line([arrow_x, arrow_y, arrow_x + 85, arrow_y], fill=(139, 92, 246, 255), width=5)
    draw.polygon([(arrow_x + 70, arrow_y - 16), (arrow_x + 95, arrow_y), (arrow_x + 70, arrow_y + 16)], fill=(139, 92, 246, 255))

    # ========================================================
    # QR CODE AREA (Right)
    # ========================================================
    qr_box_x = 1620
    qr_box_y = footer_y + 70
    qr_size = 540

    # Purple Scanner Corner Brackets
    bracket_len = 50
    bracket_w = 6
    b_color = (139, 92, 246, 255)
    draw.line([qr_box_x - 30, qr_box_y - 30, qr_box_x - 30 + bracket_len, qr_box_y - 30], fill=b_color, width=bracket_w)
    draw.line([qr_box_x - 30, qr_box_y - 30, qr_box_x - 30, qr_box_y - 30 + bracket_len], fill=b_color, width=bracket_w)
    draw.line([qr_box_x + qr_size + 30, qr_box_y - 30, qr_box_x + qr_size + 30 - bracket_len, qr_box_y - 30], fill=b_color, width=bracket_w)
    draw.line([qr_box_x + qr_size + 30, qr_box_y - 30, qr_box_x + qr_size + 30, qr_box_y - 30 + bracket_len], fill=b_color, width=bracket_w)
    draw.line([qr_box_x - 30, qr_box_y + qr_size + 30, qr_box_x - 30 + bracket_len, qr_box_y + qr_size + 30], fill=b_color, width=bracket_w)
    draw.line([qr_box_x - 30, qr_box_y + qr_size + 30, qr_box_x - 30, qr_box_y + qr_size + 30 - bracket_len], fill=b_color, width=bracket_w)
    draw.line([qr_box_x + qr_size + 30, qr_box_y + qr_size + 30, qr_box_x + qr_size + 30 - bracket_len, qr_box_y + qr_size + 30], fill=b_color, width=bracket_w)
    draw.line([qr_box_x + qr_size + 30, qr_box_y + qr_size + 30, qr_box_x + qr_size + 30, qr_box_y + qr_size + 30 - bracket_len], fill=b_color, width=bracket_w)

    # Pure White Card Base
    draw.rounded_rectangle([qr_box_x, qr_box_y, qr_box_x + qr_size, qr_box_y + qr_size], radius=20, fill=(255, 255, 255, 255))

    in_pad = 32
    inner_box = [qr_box_x + in_pad, qr_box_y + in_pad, qr_box_x + qr_size - in_pad, qr_box_y + qr_size - in_pad]

    if embed_qr:
        # Render live scannable QR Code
        with open("public/qr-code.svg", "r", encoding="utf-8") as f:
            svg_content = f.read()
        
        matches = re.findall(r"M\s*(\d+),(\d+)\s*l\s*(\d+),0\s*0,(\d+)\s*-(\d+),0\s*z", svg_content)
        scale = (qr_size - 2 * in_pad) / 300.0
        for m in matches:
            sx, sy, sw, sh = int(m[0]), int(m[1]), int(m[2]), int(m[3])
            rx1 = int(inner_box[0] + sx * scale)
            ry1 = int(inner_box[1] + sy * scale)
            rx2 = int(inner_box[0] + (sx + sw) * scale)
            ry2 = int(inner_box[1] + (sy + sh) * scale)
            draw.rectangle([rx1, ry1, rx2, ry2], fill=(15, 23, 42, 255))
    else:
        # Clean Rectangular Placeholder Area as specified in prompt
        draw.rounded_rectangle(inner_box, radius=12, fill=(246, 248, 252, 255), outline=(203, 213, 225, 255), width=3)

        def draw_finder_pattern(fx, fy):
            draw.rectangle([fx, fy, fx + 74, fy + 74], outline=(15, 23, 42, 255), width=8)
            draw.rectangle([fx + 20, fy + 20, fx + 54, fy + 54], fill=(15, 23, 42, 255))

        draw_finder_pattern(qr_box_x + in_pad + 24, qr_box_y + in_pad + 24)
        draw_finder_pattern(qr_box_x + qr_size - in_pad - 98, qr_box_y + in_pad + 24)
        draw_finder_pattern(qr_box_x + in_pad + 24, qr_box_y + qr_size - in_pad - 98)

        p_text1 = "[ PLACE A LARGE, CLEAR"
        p_text2 = "QR CODE HERE ]"
        tw1 = f_qr_place.getlength(p_text1)
        tw2 = f_qr_place.getlength(p_text2)
        mid_qr_x = qr_box_x + qr_size // 2
        mid_qr_y = qr_box_y + qr_size // 2

        draw.text((mid_qr_x - tw1 // 2, mid_qr_y - 45), p_text1, font=f_qr_place, fill=(15, 23, 42, 255))
        draw.text((mid_qr_x - tw2 // 2, mid_qr_y), p_text2, font=f_qr_place, fill=(15, 23, 42, 255))

        sub_text = "50 × 50 MM INSERTION ZONE"
        sub_tw = f_qr_sub.getlength(sub_text)
        draw.text((mid_qr_x - sub_tw // 2, mid_qr_y + 80), sub_text, font=f_qr_sub, fill=(100, 116, 139, 255))

    # Technical Ticker Footer
    draw.line([200, HEIGHT - 180, WIDTH - 200, HEIGHT - 180], fill=(255, 255, 255, 18), width=2)
    draw.text((200, HEIGHT - 145), "CAMPUS CIRCULATION // SRM INSTITUTE OF SCIENCE & TECHNOLOGY", font=f_meta, fill=(85, 95, 110, 255))
    draw.text((WIDTH - 590, HEIGHT - 145), "NO GUESSWORK. ALL SIGNAL.", font=f_meta, fill=(85, 95, 110, 255))

    # Save output
    img.convert("RGB").save(output_path, "PNG", dpi=(300, 300))
    print(f"Generated {output_path} (embed_qr={embed_qr})")

if __name__ == "__main__":
    build_poster(embed_qr=False, output_path="public/poster.png")
    build_poster(embed_qr=True, output_path="public/poster-with-qr.png")
