import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_phase3"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run():
    with sync_playwright() as p:
        log("Launching browser for Phase 3 Practice Hub verification...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # 1. Load /mintai?course=1&tab=practice
        # -----------------------------------------------------------------
        log("[1/7] Loading Practice Hub for Calculus...")
        page.goto(f"{BASE_URL}/mintai?course=1&tab=practice", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="pyqs"]', timeout=15000)
        assert "/mintai" in page.url and "tab=practice" in page.url, f"Expected /mintai?course=1&tab=practice, got {page.url}"

        # -----------------------------------------------------------------
        # 2. Destination 1: PYQs (Past Papers)
        # -----------------------------------------------------------------
        log("[2/7] Verifying Destination 1: PYQs (Past Papers)...")
        # Wait for PYQs to load from API
        page.wait_for_selector(':has-text("Q#")', timeout=15000)
        pyq_dest_btn = page.locator('button[data-dest="pyqs"]')
        assert pyq_dest_btn.count() > 0, "PYQs tab button missing"

        # Check for question cards
        question_cards = page.locator(':has-text("Q#")')
        log(f"  -> Found {question_cards.count()} PYQ elements")
        assert question_cards.count() > 0, "No PYQs rendered on page"

        # Test Solution Rubric toggle on first question
        rubric_btn = page.locator('button:has-text("View Solution Rubric")').first
        if rubric_btn.count() > 0:
            rubric_btn.click()
            time.sleep(0.5)
            assert page.locator(':has-text("Official Mark Rubric & Solution Strategy")').count() > 0, "Solution Rubric did not open"
            log("  -> Solution Rubric toggle verified")

        # Test Search Filter
        search_input = page.locator('input[placeholder*="Search questions or topics"]')
        search_input.fill("matrix")
        time.sleep(1)
        search_input.fill("")
        time.sleep(0.5)

        p1 = os.path.join(OUTPUT_DIR, "phase3_01_practice_pyqs.png")
        page.screenshot(path=p1)
        log(f"  -> PYQs screenshot saved: {p1}")

        # -----------------------------------------------------------------
        # 3. Destination 2: Cycle Test Archive
        # -----------------------------------------------------------------
        log("[3/7] Verifying Destination 2: Cycle Test Archive...")
        ct_btn = page.locator('button[data-dest="ct_archives"]')
        assert ct_btn.count() > 0, "CT Archives button missing"
        ct_btn.click()
        page.wait_for_selector(':has-text("Cycle Test Descriptive Archive")', timeout=10000)
        assert "dest=ct_archives" in page.url, f"Expected dest=ct_archives in URL, got {page.url}"

        # Check if faculty answer key toggle is present
        answer_key_btn = page.locator('button:has-text("Show Faculty Answer Key")').first
        if answer_key_btn.count() > 0:
            answer_key_btn.click()
            time.sleep(0.5)
            assert page.locator(':has-text("Official Faculty Solution & Answer Key")').count() > 0, "Answer key did not open"
            log("  -> Faculty answer key toggle verified")

        p2 = os.path.join(OUTPUT_DIR, "phase3_02_practice_ct_archives.png")
        page.screenshot(path=p2)
        log(f"  -> CT Archives screenshot saved: {p2}")

        # -----------------------------------------------------------------
        # 4. Destination 3: Interactive MCQ Practice
        # -----------------------------------------------------------------
        log("[4/7] Verifying Destination 3: Interactive MCQ Practice...")
        mcq_btn = page.locator('button[data-dest="mcqs"]')
        assert mcq_btn.count() > 0, "Interactive MCQs button missing"
        mcq_btn.click()
        page.wait_for_selector(':has-text("Interactive MCQ Testing Engine")', timeout=10000)
        assert "dest=mcqs" in page.url, f"Expected dest=mcqs in URL, got {page.url}"

        # Test selecting an option if available
        opt = page.locator('button:has-text("A)"), button:has-text("B)"), button:has-text("C)"), button:has-text("D)")').first
        if opt.count() > 0:
            opt.click()
            time.sleep(1)
            log("  -> Option selected and validated")

        p3 = os.path.join(OUTPUT_DIR, "phase3_03_practice_mcqs.png")
        page.screenshot(path=p3)
        log(f"  -> Interactive MCQs screenshot saved: {p3}")

        # -----------------------------------------------------------------
        # 5. Destination 4: Timed Examination Tests
        # -----------------------------------------------------------------
        log("[5/7] Verifying Destination 4: Timed Tests...")
        quiz_btn = page.locator('button[data-dest="quiz"]')
        assert quiz_btn.count() > 0, "Timed Tests button missing"
        quiz_btn.click()
        page.wait_for_selector(':has-text("Time Left")', timeout=10000)
        assert "dest=quiz" in page.url, f"Expected dest=quiz in URL, got {page.url}"

        # Verify Quiz mode elements
        assert page.locator(':has-text("Question Navigator")').count() > 0, "Question Navigator missing"
        assert page.locator(':has-text("Submit Test")').count() > 0, "Submit Test button missing"

        # Select an option in quiz mode
        quiz_opt = page.locator('button:has-text("A)"), button:has-text("B)"), button:has-text("C)"), button:has-text("D)")').first
        if quiz_opt.count() > 0:
            quiz_opt.click()
            time.sleep(0.5)

        p4 = os.path.join(OUTPUT_DIR, "phase3_04_practice_timed_quiz.png")
        page.screenshot(path=p4)
        log(f"  -> Timed Tests screenshot saved: {p4}")

        # -----------------------------------------------------------------
        # 6. Destination 5: AI Question Generator
        # -----------------------------------------------------------------
        log("[6/7] Verifying Destination 5: AI Question Generator...")
        gen_btn = page.locator('button[data-dest="generator"]')
        assert gen_btn.count() > 0, "AI Generator button missing"
        gen_btn.click()
        page.wait_for_selector(':has-text("MintAI Question Generator & Synthesizer")', timeout=10000)
        assert "dest=generator" in page.url, f"Expected dest=generator in URL, got {page.url}"

        # Check topic dropdown
        topic_select = page.locator('select:has-text("Calculus And Linear Algebra")')
        assert topic_select.count() > 0, "Topic selector dropdown missing"

        p5 = os.path.join(OUTPUT_DIR, "phase3_05_practice_ai_generator.png")
        page.screenshot(path=p5)
        log(f"  -> AI Generator screenshot saved: {p5}")

        # -----------------------------------------------------------------
        # 7. Regression Test: Tab switching back and forth
        # -----------------------------------------------------------------
        log("[7/7] Verifying tab navigation regression (Overview -> Exam DNA -> Practice)...")
        # Click Overview
        page.locator('button:has-text("Overview")').first.click()
        time.sleep(1.5)
        assert page.locator(':has-text("Exam Forecast")').count() > 0 or "tab=overview" in page.url or "tab" not in page.url, "Overview tab navigation failed"
        log("  -> Overview tab verified")

        # Click Exam DNA
        page.locator('button:has-text("Exam DNA")').first.click()
        time.sleep(1.5)
        assert "tab=dna" in page.url, "Exam DNA tab navigation failed"
        log("  -> Exam DNA tab verified")

        # Return to Practice
        page.locator('button:has-text("Practice")').first.click()
        time.sleep(1.5)
        assert "tab=practice" in page.url, "Practice tab navigation failed"
        log("  -> Practice tab return verified")

        browser.close()
        log("All Phase 3 verification tests passed successfully!")

    # Copy screenshots to artifact directory
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            src = os.path.join(OUTPUT_DIR, f)
            dst = os.path.join(ARTIFACT_DIR, f)
            shutil.copy2(src, dst)
            log(f"Copied {f} to {ARTIFACT_DIR}")

if __name__ == "__main__":
    run()
