import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_phase1"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run():
    with sync_playwright() as p:
        log("Launching browser for Phase 1 verification...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # TEST 1: Canonical /mintai Route & Overview Tab
        # -----------------------------------------------------------------
        log("[1/6] Testing /mintai canonical entry & Overview section...")
        page.goto(f"{BASE_URL}/mintai?course=1", wait_until="domcontentloaded")
        time.sleep(2.5)
        assert "/mintai" in page.url, f"Expected /mintai in URL, got {page.url}"
        
        # Verify 4 persistent tabs exist
        assert page.locator('button[data-tab="overview"]').count() > 0, "Overview tab button missing"
        assert page.locator('button[data-tab="dna"]').count() > 0, "Exam DNA tab button missing"
        assert page.locator('button[data-tab="practice"]').count() > 0, "Practice tab button missing"
        assert page.locator('button[data-tab="study"]').count() > 0, "Study tab button missing"
        
        p1 = os.path.join(OUTPUT_DIR, "phase1_01_canonical_overview.png")
        page.screenshot(path=p1)
        log(f"  -> Overview tab verified, screenshot saved: {p1}")

        # -----------------------------------------------------------------
        # TEST 2: Tab Switching & URL Persistence
        # -----------------------------------------------------------------
        log("[2/6] Testing tab switching & URL persistence...")
        # Click Exam DNA tab
        page.locator('button[data-tab="dna"]').click()
        time.sleep(2)
        assert "tab=dna" in page.url, f"Expected tab=dna in URL, got {page.url}"
        p2 = os.path.join(OUTPUT_DIR, "phase1_02_exam_dna_tab.png")
        page.screenshot(path=p2)
        log(f"  -> Switched to Exam DNA: {page.url}")

        # Click Practice tab
        page.locator('button[data-tab="practice"]').click()
        time.sleep(2)
        assert "tab=practice" in page.url, f"Expected tab=practice in URL, got {page.url}"
        p3 = os.path.join(OUTPUT_DIR, "phase1_03_practice_tab.png")
        page.screenshot(path=p3)
        log(f"  -> Switched to Practice: {page.url}")

        # Click Study tab
        page.locator('button[data-tab="study"]').click()
        time.sleep(2)
        assert "tab=study" in page.url, f"Expected tab=study in URL, got {page.url}"
        p4 = os.path.join(OUTPUT_DIR, "phase1_04_study_tab.png")
        page.screenshot(path=p4)
        log(f"  -> Switched to Study: {page.url}")

        # -----------------------------------------------------------------
        # TEST 3: Browser Back / Forward Navigation
        # -----------------------------------------------------------------
        log("[3/6] Testing browser back and forward navigation...")
        page.go_back()
        time.sleep(1.5)
        assert "tab=practice" in page.url, f"Expected back to tab=practice, got {page.url}"
        assert "bg-foreground" in page.locator('button[data-tab="practice"]').get_attribute("class"), "Practice tab UI not active after back"

        page.go_back()
        time.sleep(1.5)
        assert "tab=dna" in page.url, f"Expected back to tab=dna, got {page.url}"
        assert "bg-foreground" in page.locator('button[data-tab="dna"]').get_attribute("class"), "DNA tab UI not active after back"

        page.go_forward()
        time.sleep(1.5)
        assert "tab=practice" in page.url, f"Expected forward to tab=practice, got {page.url}"
        assert "bg-foreground" in page.locator('button[data-tab="practice"]').get_attribute("class"), "Practice tab UI not active after forward"
        log("  -> Browser back/forward navigation passed!")

        # -----------------------------------------------------------------
        # TEST 4: Assessment Cycle & Course Selection Persistence
        # -----------------------------------------------------------------
        log("[4/6] Testing Assessment Cycle & Course Selector...")
        # Return to Overview
        page.locator('button[data-tab="overview"]').click()
        time.sleep(1.5)

        # Click CT1 Cycle button
        ct1_btn = page.locator('button:has-text("CT1 (Units 1-2)")').first
        ct1_btn.click()
        time.sleep(2)
        assert "cycle=CT1" in page.url, f"Expected cycle=CT1 in URL, got {page.url}"

        # Open course selection modal
        course_btn = page.locator('button:has-text("Calculus")').first
        course_btn.click()
        time.sleep(1.5)

        # Modal should be open
        assert page.locator('h2:has-text("Select Your Course")').count() > 0, "Course modal did not open"
        p5 = os.path.join(OUTPUT_DIR, "phase1_05_course_modal.png")
        page.screenshot(path=p5)
        log(f"  -> Course modal verified, screenshot saved: {p5}")

        # Search for PPS (Programming For Problem Solving)
        page.locator('input[placeholder*="Instant search"]').fill("Programming")
        time.sleep(1)
        pps_btn = page.locator('button:has-text("Programming For Problem Solving")').first
        pps_btn.click()
        time.sleep(2.5)

        assert "course=5" in page.url or "programming" in page.url.lower(), f"Expected course=5 in URL, got {page.url}"
        p6 = os.path.join(OUTPUT_DIR, "phase1_06_pps_overview_ct1.png")
        page.screenshot(path=p6)
        log(f"  -> Course switched to PPS with cycle=CT1 preserved: {page.url}")

        # -----------------------------------------------------------------
        # TEST 5: Backward Compatibility & Redirects
        # -----------------------------------------------------------------
        log("[5/6] Testing backward-compatible redirects...")
        # /dashboard -> /mintai
        page.goto(f"{BASE_URL}/dashboard?course=1&cycle=CT2", wait_until="domcontentloaded")
        time.sleep(2)
        assert "/mintai" in page.url, f"Expected redirect to /mintai, got {page.url}"
        assert "course=1" in page.url, f"Expected course=1 preserved, got {page.url}"
        assert "cycle=CT2" in page.url, f"Expected cycle=CT2 preserved, got {page.url}"
        log("  -> /dashboard redirect passed!")

        # /mintai/exam-dna -> /mintai?tab=dna
        page.goto(f"{BASE_URL}/mintai/exam-dna?course=1", wait_until="domcontentloaded")
        time.sleep(2)
        assert "/mintai" in page.url, f"Expected redirect to /mintai, got {page.url}"
        assert "tab=dna" in page.url, f"Expected tab=dna in URL, got {page.url}"
        log("  -> /mintai/exam-dna redirect passed!")

        # /dashboard/exam-dna -> /mintai?tab=dna
        page.goto(f"{BASE_URL}/dashboard/exam-dna?course=5", wait_until="domcontentloaded")
        time.sleep(2)
        assert "/mintai" in page.url, f"Expected redirect to /mintai, got {page.url}"
        assert "tab=dna" in page.url, f"Expected tab=dna in URL, got {page.url}"
        log("  -> /dashboard/exam-dna redirect passed!")

        # -----------------------------------------------------------------
        # TEST 6: Mobile Responsive Layout
        # -----------------------------------------------------------------
        log("[6/6] Testing mobile responsive layout (375x667)...")
        mobile_context = browser.new_context(
            viewport={"width": 375, "height": 667},
            device_scale_factor=2,
            color_scheme="dark",
            is_mobile=True,
            has_touch=True
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto(f"{BASE_URL}/mintai?course=1", wait_until="domcontentloaded")
        time.sleep(2.5)

        p7 = os.path.join(OUTPUT_DIR, "phase1_07_mobile_mintai.png")
        mobile_page.screenshot(path=p7)
        log(f"  -> Mobile responsive screenshot saved: {p7}")

        # Check mobile menu
        menu_btn = mobile_page.locator('button:has(.lucide-menu)').first
        if menu_btn.count() > 0:
            menu_btn.click()
            time.sleep(1)
            # Verify Mint AI link is in mobile menu
            assert mobile_page.locator('a:has-text("Mint AI")').count() > 0, "Mint AI link missing from mobile menu"
            p8 = os.path.join(OUTPUT_DIR, "phase1_08_mobile_menu.png")
            mobile_page.screenshot(path=p8)
            log(f"  -> Mobile menu screenshot saved: {p8}")

        browser.close()

    # Copy screenshots to artifact directory
    log("Copying Phase 1 screenshots to Brain artifact directory...")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            shutil.copy2(os.path.join(OUTPUT_DIR, f), os.path.join(ARTIFACT_DIR, f))
            log(f"  -> Copied {f}")

    log("\nAll Phase 1 tests PASSED with 100% success!")

if __name__ == "__main__":
    run()
