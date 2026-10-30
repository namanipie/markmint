import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_showcase"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def inject_cleanups(page):
    try:
        page.add_style_tag(content="""
            div:has(> div:has-text("cookies")),
            div:has-text("We use essential cookies"),
            .fixed.bottom-6.right-6,
            button[aria-label*="Scroll to top"],
            ::-webkit-scrollbar { display: none !important; }
        """)
    except Exception as e:
        log(f"  Warning injecting cleanups: {e}")

def run():
    with sync_playwright() as p:
        log("Launching browser...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. MintAI Forecast Hub
        # -------------------------------------------------------------
        log("[1/11] MintAI Forecast Hub (ALL cycles)...")
        page.goto(f"{BASE_URL}/dashboard?course=1", wait_until="domcontentloaded")
        time.sleep(3)
        inject_cleanups(page)
        p1 = os.path.join(OUTPUT_DIR, "01_mintai_forecast_hub.png")
        page.screenshot(path=p1)
        log(f"  -> Saved: {p1}")

        # -------------------------------------------------------------
        # 2. Cycle Test 1 Portion Filter
        # -------------------------------------------------------------
        log("[2/11] MintAI Assessment Cycle (CT1 Preset)...")
        ct1_btn = page.locator('button:has-text("CT1 (Units 1 & 2)")').first
        if ct1_btn.count() > 0:
            ct1_btn.click()
            time.sleep(2)
        p2 = os.path.join(OUTPUT_DIR, "02_mintai_cycle_test_filter_ct1.png")
        page.screenshot(path=p2)
        log(f"  -> Saved: {p2}")

        # -------------------------------------------------------------
        # 3. Exam DNA Overview
        # -------------------------------------------------------------
        log("[3/11] MintAI Exam DNA Overview...")
        page.goto(f"{BASE_URL}/mintai/exam-dna?course=1", wait_until="domcontentloaded")
        time.sleep(3)
        inject_cleanups(page)
        p3 = os.path.join(OUTPUT_DIR, "03_mintai_exam_dna_overview.png")
        page.screenshot(path=p3)
        log(f"  -> Saved: {p3}")

        # -------------------------------------------------------------
        # 4. Exam DNA Blueprints & Cognitive Taxonomy
        # -------------------------------------------------------------
        log("[4/11] MintAI Exam DNA Blueprints & Cognitive Demand...")
        page.evaluate("window.scrollBy(0, 650)")
        time.sleep(1.5)
        p4 = os.path.join(OUTPUT_DIR, "04_mintai_exam_dna_blueprints.png")
        page.screenshot(path=p4)
        log(f"  -> Saved: {p4}")

        # -------------------------------------------------------------
        # 5. Slide-Over Practice Drawer (Verified PYQs)
        # -------------------------------------------------------------
        log("[5/11] MintAI Slide-Over Practice Drawer (Verified PYQs)...")
        page.goto(f"{BASE_URL}/dashboard?course=1", wait_until="domcontentloaded")
        time.sleep(3)
        inject_cleanups(page)
        
        practice_btns = page.locator('button:has-text("Practice")')
        if practice_btns.count() > 1:
            practice_btns.nth(1).click()
        elif practice_btns.count() > 0:
            practice_btns.first.click()
        time.sleep(2.5)
        p5 = os.path.join(OUTPUT_DIR, "05_mintai_practice_drawer_pyq.png")
        page.screenshot(path=p5)
        log(f"  -> Saved: {p5}")

        # -------------------------------------------------------------
        # 6. AI Question Generator Tab
        # -------------------------------------------------------------
        log("[6/11] MintAI AI Question Generator Tab...")
        ai_tab = page.locator('button:has-text("AI Practice Generator")').first
        if ai_tab.count() > 0:
            ai_tab.click()
            time.sleep(1.5)
            gen_btn = page.locator('button:has-text("Generate")').first
            if gen_btn.count() > 0:
                gen_btn.click()
                time.sleep(3)
            rev_btn = page.locator('button:has-text("Reveal Solution")').first
            if rev_btn.count() > 0:
                rev_btn.click()
                time.sleep(0.5)
        p6 = os.path.join(OUTPUT_DIR, "06_mintai_practice_drawer_ai_generator.png")
        page.screenshot(path=p6)
        log(f"  -> Saved: {p6}")

        # Close the drawer
        page.keyboard.press("Escape")
        time.sleep(1)

        # -------------------------------------------------------------
        # 7. Cycle Test Drawer: Descriptive Questions
        # -------------------------------------------------------------
        log("[7/11] MintAI CT1 Descriptive Archive...")
        page.goto(f"{BASE_URL}/dashboard?course=1", wait_until="domcontentloaded")
        time.sleep(3)
        inject_cleanups(page)
        
        # Select CT1
        page.locator('button:has-text("CT1 (Units 1 & 2)")').first.click()
        time.sleep(2)

        # Scroll down to cycle test questions drawer
        page.evaluate("window.scrollBy(0, 320)")
        time.sleep(1)

        # Reveal answer key of first question
        reveal_key = page.locator('button:has-text("Reveal Answer Key")').first
        if reveal_key.count() > 0:
            reveal_key.click()
            time.sleep(0.5)
        p7 = os.path.join(OUTPUT_DIR, "07_mintai_ct1_descriptive_archive.png")
        page.screenshot(path=p7)
        log(f"  -> Saved: {p7}")

        # -------------------------------------------------------------
        # 8. Cycle Test Drawer: Interactive MCQ Testing Suite
        # -------------------------------------------------------------
        log("[8/11] MintAI Interactive MCQ Testing Suite (Practice Mode)...")
        mcq_toggle = page.locator('button:has-text("Interactive MCQ Test")').first
        if mcq_toggle.count() > 0:
            mcq_toggle.click()
            time.sleep(2)
            # Select an option
            opt = page.locator('button:has-text("A."), button:has-text("B.")').first
            if opt.count() > 0:
                opt.click()
                time.sleep(1)
        p8 = os.path.join(OUTPUT_DIR, "08_mintai_interactive_mcq_suite.png")
        page.screenshot(path=p8)
        log(f"  -> Saved: {p8}")

        # -------------------------------------------------------------
        # 9. Interactive MCQ Suite: Timed Quiz Mode
        # -------------------------------------------------------------
        log("[9/11] MintAI Timed Quiz Mode...")
        timed_btn = page.locator('button:has-text("Timed Quiz Mode")').first
        if timed_btn.count() > 0:
            timed_btn.click()
            time.sleep(2)
        p9 = os.path.join(OUTPUT_DIR, "09_mintai_timed_quiz_mode.png")
        page.screenshot(path=p9)
        log(f"  -> Saved: {p9}")

        # -------------------------------------------------------------
        # 10. Course Resource Hub: Video Classes Tab (Dr. E Suresh)
        # -------------------------------------------------------------
        log("[10/11] MintAI Curated Study Resources Hub...")
        page.goto(f"{BASE_URL}/courses/calculus-and-linear-algebra", wait_until="domcontentloaded")
        time.sleep(3)
        inject_cleanups(page)
        
        # Scroll to course resources
        page.evaluate("window.scrollBy(0, 850)")
        time.sleep(1.5)

        # Switch to Video Classes tab
        v_tab = page.locator('button:has-text("Video Classes")').first
        if v_tab.count() > 0:
            v_tab.click()
            time.sleep(2)

        p10 = os.path.join(OUTPUT_DIR, "10_mintai_study_resources_hub.png")
        page.screenshot(path=p10)
        log(f"  -> Saved: {p10}")

        # -------------------------------------------------------------
        # 11. In-App Resource Viewer Modal (Dr. E Suresh Video Player)
        # -------------------------------------------------------------
        log("[11/11] In-App Resource Viewer Modal (Dr. E Suresh Lecture)...")
        watch_btn = page.locator('button:has-text("Watch in MarkMint")').first
        if watch_btn.count() > 0:
            watch_btn.click()
            time.sleep(3)
        p11 = os.path.join(OUTPUT_DIR, "11_mintai_resource_viewer_player.png")
        page.screenshot(path=p11)
        log(f"  -> Saved: {p11}")

        browser.close()

    log("\nCopying screenshots to Brain Artifact directory...")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            src = os.path.join(OUTPUT_DIR, f)
            dst = os.path.join(ARTIFACT_DIR, f)
            shutil.copy2(src, dst)
            log(f"  -> Copied {f} to Brain artifacts")

    log("\nAll 11 MintAI Showcase Screenshots captured and copied successfully!")

if __name__ == "__main__":
    run()
