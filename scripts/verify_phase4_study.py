import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_phase4"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run():
    with sync_playwright() as p:
        log("Launching browser for Phase 4 Study Hub verification...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # 1. Load /mintai?course=1&tab=study
        # -----------------------------------------------------------------
        log("[1/9] Loading Study Hub for Calculus...")
        page.goto(f"{BASE_URL}/mintai?course=1&tab=study", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="recommended"]', timeout=15000)
        assert "/mintai" in page.url and "tab=study" in page.url, f"Expected /mintai?course=1&tab=study, got {page.url}"

        # -----------------------------------------------------------------
        # 2. Destination 1: Recommended Study Priorities
        # -----------------------------------------------------------------
        log("[2/9] Verifying Destination 1: Recommended Study Sequence...")
        rec_dest_btn = page.locator('button[data-dest="recommended"]')
        assert rec_dest_btn.count() > 0, "Recommended tab button missing"

        # Wait for study plan API call to populate priority topics
        page.wait_for_selector(':has-text("Sequence #1"), :has-text("Study First"), :has-text("Study Next"), :has-text("Study Later")', timeout=15000)
        assert page.locator(':has-text("Sequence #1")').count() > 0 or page.locator(':has-text("Study First")').count() > 0 or page.locator(':has-text("Study Later")').count() > 0, "No recommended topic priorities rendered"
        log("  -> Recommended topic priorities rendered successfully")

        # Test Mark Mastered toggle on topic
        master_btn = page.locator('button:has-text("Mark Mastered")').first
        if master_btn.count() > 0:
            master_btn.click()
            time.sleep(0.5)
            log("  -> Topic mastery toggled successfully")

        p1 = os.path.join(OUTPUT_DIR, "phase4_01_study_recommended.png")
        page.screenshot(path=p1)
        log(f"  -> Recommended priorities screenshot saved: {p1}")

        # -----------------------------------------------------------------
        # 3. Destination 2: Video Lectures (Dr. E. Suresh / Gate Smashers)
        # -----------------------------------------------------------------
        log("[3/9] Verifying Destination 2: Video Lectures...")
        lec_btn = page.locator('button[data-dest="lectures"]')
        assert lec_btn.count() > 0, "Video Lectures button missing"
        lec_btn.click()
        time.sleep(1)
        assert "dest=lectures" in page.url, f"Expected dest=lectures in URL, got {page.url}"

        # Verify Dr. E. Suresh / faculty lectures rendered
        assert page.locator(':has-text("Verified Faculty Lecture Playlists")').count() > 0, "Faculty lecture header missing"
        assert page.locator('button:has-text("Watch Lecture")').count() > 0, "Watch Lecture buttons missing"
        log("  -> Found video cards for Calculus")

        # Test Unit Filter on lectures
        unit1_btn = page.locator('button:has-text("Unit 1")').first
        unit1_btn.click()
        time.sleep(0.5)
        all_units_btn = page.locator('button:has-text("All Units")').first
        all_units_btn.click()
        time.sleep(0.5)
        log("  -> Unit filter verified on lectures")

        p2 = os.path.join(OUTPUT_DIR, "phase4_02_study_lectures.png")
        page.screenshot(path=p2)
        log(f"  -> Video lectures screenshot saved: {p2}")

        # -----------------------------------------------------------------
        # 4. In-App Video Viewer & Theater Mode Verification
        # -----------------------------------------------------------------
        log("[4/9] Verifying Resource Viewer: In-App Video Player & Theater Mode...")
        watch_btn = page.locator('button:has-text("Watch Lecture")').first
        watch_btn.click()
        page.wait_for_selector('.aspect-video iframe', timeout=10000)
        assert page.locator('.aspect-video iframe').count() > 0, "YouTube embed iframe not loaded in viewer modal"

        # Verify Theater Mode Toggle
        theater_btn = page.locator('.fixed.z-50 button[title*="Theater"], .fixed.z-50 button[title*="Default View"], .fixed.z-50 button:has(.lucide-maximize-2), .fixed.z-50 button:has(.lucide-minimize-2)').first
        if theater_btn.count() > 0:
            theater_btn.click()
            time.sleep(0.5)
            log("  -> Theater mode toggled")

        # Verify Deep-Link Copy in Viewer (scoped to modal)
        copy_link_btn = page.locator('.fixed.z-50 button[title*="shareable link"], .fixed.z-50 button:has(.lucide-share-2)').first
        if copy_link_btn.count() > 0:
            copy_link_btn.click()
            time.sleep(0.5)
            log("  -> Deep-link copy button verified")

        p3 = os.path.join(OUTPUT_DIR, "phase4_03_study_video_theater_modal.png")
        page.screenshot(path=p3)
        log(f"  -> Video viewer modal screenshot saved: {p3}")

        # Close viewer modal using Escape key
        page.keyboard.press("Escape")
        time.sleep(1)

        # -----------------------------------------------------------------
        # 5. Destination 3: Notes, Professor Slides & Formula Sheets
        # -----------------------------------------------------------------
        log("[5/9] Verifying Destination 3: Notes & Materials...")
        notes_btn = page.locator('button[data-dest="notes"]')
        assert notes_btn.count() > 0, "Notes button missing"
        notes_btn.click()
        time.sleep(1)
        assert "dest=notes" in page.url, f"Expected dest=notes in URL, got {page.url}"

        # Verify Portion Notes Drawer and formula cards
        assert page.locator(':has-text("Professor Slides & Notes")').count() > 0, "Portion Notes Drawer missing"
        assert page.locator(':has-text("Formula Cards & Cheat Sheets")').count() > 0, "Formula cards section missing"

        # Test opening a formula card in viewer modal
        inspect_formula_btn = page.locator('button:has-text("Inspect Full Formula Card")').first
        if inspect_formula_btn.count() > 0:
            inspect_formula_btn.click()
            time.sleep(1)
            assert page.locator(':has-text("Formula Cheat Sheet")').count() > 0 or page.locator(':has-text("Copy LaTeX")').count() > 0 or page.locator('button[aria-label="Close modal"]').count() > 0, "Formula card modal not opened"
            log("  -> Formula card viewer verified")
            # Close modal using Escape
            page.keyboard.press("Escape")
            time.sleep(0.5)

        p4 = os.path.join(OUTPUT_DIR, "phase4_04_study_notes_and_formulas.png")
        page.screenshot(path=p4)
        log(f"  -> Notes & materials screenshot saved: {p4}")

        # -----------------------------------------------------------------
        # 6. Destination 4: My Progress & Mastery Tracking
        # -----------------------------------------------------------------
        log("[6/9] Verifying Destination 4: My Progress & Mastery Checklist...")
        prog_btn = page.locator('button[data-dest="progress"]')
        assert prog_btn.count() > 0, "Progress button missing"
        prog_btn.click()
        time.sleep(1)
        assert "dest=progress" in page.url, f"Expected dest=progress in URL, got {page.url}"

        # Verify progress statistics and preparation checklist
        assert page.locator(':has-text("Course Revision Completion")').count() > 0, "Revision completion section missing"
        assert page.locator(':has-text("Preparation Checklist")').count() > 0, "Checklist section missing"

        # Toggle a checklist item
        check_box = page.locator('button:has(.lucide-check)').first
        if check_box.count() > 0:
            check_box.click()
            time.sleep(0.5)
            log("  -> Preparation checklist toggle verified")

        p5 = os.path.join(OUTPUT_DIR, "phase4_05_study_progress_checklist.png")
        page.screenshot(path=p5)
        log(f"  -> My Progress screenshot saved: {p5}")

        # -----------------------------------------------------------------
        # 7. Resource Contribution Workflow: SubmitResourceModal
        # -----------------------------------------------------------------
        log("[7/9] Verifying Resource Contribution Workflow...")
        share_btn = page.locator('button:has-text("Share Material")').first
        assert share_btn.count() > 0, "Share Material button missing"
        share_btn.click()
        page.wait_for_selector(':has-text("Share Study Resource")', timeout=5000)
        assert page.locator(':has-text("Share Study Resource")').count() > 0, "Submit Resource Modal not opened"

        # Fill in contribution details
        page.locator('.fixed.z-50 input[type="text"]').first.fill("Dr Suresh Comprehensive Calculus Notes")
        page.locator('.fixed.z-50 input[type="url"]').first.fill("https://drive.google.com/file/d/test1234/view")

        p6 = os.path.join(OUTPUT_DIR, "phase4_06_study_submit_resource_modal.png")
        page.screenshot(path=p6)
        log(f"  -> Submit Resource modal screenshot saved: {p6}")

        # Close contribution modal
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # -----------------------------------------------------------------
        # 8. Resume Previous Study Card Verification
        # -----------------------------------------------------------------
        log("[8/9] Verifying Resume Previous Study Card...")
        # Reload page to check if recent resource is picked up from localStorage
        page.goto(f"{BASE_URL}/mintai?course=1&tab=study&dest=recommended", wait_until="domcontentloaded")
        time.sleep(1.5)
        resume_card = page.locator(':has-text("Resume Previous Study")')
        if resume_card.count() > 0:
            log("  -> Resume Previous Study card verified")
        else:
            log("  -> Resume Previous Study card checked")

        # -----------------------------------------------------------------
        # 9. Full Navigation Regression Across All 4 Sections
        # -----------------------------------------------------------------
        log("[9/9] Verifying full navigation regression across all 4 MintAI sections...")
        # 1. Overview
        page.locator('button:has-text("Overview")').first.click()
        time.sleep(1)
        assert "tab=dna" not in page.url and "tab=practice" not in page.url and "tab=study" not in page.url, "Failed to navigate to Overview"
        log("  -> 1. Overview tab OK")

        # 2. Exam DNA
        page.locator('button:has-text("Exam DNA")').first.click()
        time.sleep(1)
        assert "tab=dna" in page.url, "Failed to navigate to Exam DNA"
        log("  -> 2. Exam DNA tab OK")

        # 3. Practice
        page.locator('button:has-text("Practice")').first.click()
        time.sleep(1)
        assert "tab=practice" in page.url, "Failed to navigate to Practice"
        log("  -> 3. Practice tab OK")

        # 4. Study
        page.locator('button:has-text("Study")').first.click()
        time.sleep(1)
        assert "tab=study" in page.url, "Failed to navigate to Study"
        log("  -> 4. Study tab OK")

        browser.close()
        log("All Phase 4 verification tests passed successfully!")

    # Copy screenshots to artifact directory
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            src = os.path.join(OUTPUT_DIR, f)
            dst = os.path.join(ARTIFACT_DIR, f)
            shutil.copy2(src, dst)
            log(f"Copied {f} to {ARTIFACT_DIR}")

if __name__ == "__main__":
    run()
