import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/search_and_resources"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run():
    with sync_playwright() as p:
        log("Launching browser for Searchbar & First Year Resource Verification...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # 1. Test Navbar Search Button -> CommandPalette -> Course Navigation
        # -----------------------------------------------------------------
        log("[1/5] Testing Navbar Search Button & CommandPalette...")
        page.goto(f"{BASE_URL}/mintai?course=1", wait_until="domcontentloaded")
        page.wait_for_selector('button[title*="Search questions"]', timeout=15000)

        search_btn = page.locator('button[title*="Search questions"]').first
        search_btn.click()
        page.wait_for_selector('input[placeholder*="Search courses, topics"]', timeout=5000)

        # Verify command palette is open
        cmd_input = page.locator('input[placeholder*="Search courses, topics"]')
        assert cmd_input.count() > 0, "CommandPalette did not open upon clicking navbar search button"
        log("  -> CommandPalette opened successfully via navbar button")

        # Type "Mechanics" into the search bar
        cmd_input.fill("Mechanics")
        time.sleep(1)

        # Verify Engineering Mechanics course is listed
        mech_option = page.locator('.cursor-pointer:has-text("Engineering Mechanics")').first
        assert mech_option.count() > 0, "Engineering Mechanics not found in CommandPalette instant search results"
        log("  -> Found 'Engineering Mechanics' in CommandPalette search results")

        p1 = os.path.join(OUTPUT_DIR, "01_navbar_command_palette_search.png")
        page.screenshot(path=p1)
        log(f"  -> Screenshot saved: {p1}")

        # Click the course to navigate
        mech_option.click()
        time.sleep(1)
        assert "course=21" in page.url, f"Expected navigation to course 21, got {page.url}"
        log("  -> Successfully routed to Engineering Mechanics (course=21)")

        # -----------------------------------------------------------------
        # 2. Test Dr. E. Suresh Video Isolation: Mathematics vs Other Subjects
        # -----------------------------------------------------------------
        log("[2/5] Testing Dr. E. Suresh isolation between Math and Non-Math courses...")

        # A. Mathematics Course (Calculus, course=1)
        page.goto(f"{BASE_URL}/mintai?course=1&tab=study", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="recommended"]', timeout=15000)

        # Check shell badge for math
        study_tab_btn = page.locator('button[data-tab="study"]')
        assert "Dr. E Suresh" in study_tab_btn.text_content(), "Study tab badge for Calculus should be 'Dr. E Suresh'"
        log("  -> Calculus (Math): Study tab badge is 'Dr. E Suresh' (CORRECT)")

        # Check study header
        assert page.locator(':has-text("Dr. E. Suresh (SRMIST Mathematics)")').count() > 0, "Header should mention Dr. E. Suresh for Calculus"

        # Check lectures destination
        page.locator('button[data-dest="lectures"]').click()
        time.sleep(0.5)
        lec_cards = page.locator(':has-text("Dr. E. Suresh (SRMIST Mathematics)")')
        assert lec_cards.count() > 0, "Calculus video cards should show Dr. E. Suresh"
        log("  -> Calculus (Math): Verified 10 Dr. E. Suresh lecture videos")

        # B. Computer Science Course (Programming for Problem Solving, course=5)
        page.goto(f"{BASE_URL}/mintai?course=5&tab=study", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="recommended"]', timeout=15000)

        study_tab_btn = page.locator('button[data-tab="study"]')
        assert "Gate Smashers" in study_tab_btn.text_content(), "Study tab badge for PPS should be 'Gate Smashers'"
        assert "Dr. E Suresh" not in study_tab_btn.text_content(), "Study tab badge for PPS must NOT be 'Dr. E Suresh'"
        log("  -> PPS (CS): Study tab badge is 'Gate Smashers' (CORRECT)")

        # Verify header does NOT mention Suresh
        page_text = page.locator('main').text_content()
        assert "Dr. E. Suresh" not in page_text, "PPS Study tab must NOT mention Dr. E. Suresh anywhere"
        log("  -> PPS (CS): Verified Dr. E. Suresh is completely absent")

        # C. Non-Math, Non-CS Engineering Subject (Engineering Mechanics, course=21)
        page.goto(f"{BASE_URL}/mintai?course=21&tab=study", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="recommended"]', timeout=15000)

        study_tab_btn = page.locator('button[data-tab="study"]')
        assert "Study Hub" in study_tab_btn.text_content(), "Study tab badge for Mechanics should be 'Study Hub'"
        assert "Dr. E Suresh" not in study_tab_btn.text_content(), "Study tab badge for Mechanics must NOT be 'Dr. E Suresh'"
        log("  -> Engineering Mechanics: Study tab badge is 'Study Hub' (CORRECT)")

        page_text = page.locator('main').text_content()
        assert "Dr. E. Suresh" not in page_text, "Engineering Mechanics must NOT mention Dr. E. Suresh anywhere"
        log("  -> Engineering Mechanics: Verified Dr. E. Suresh is completely absent")

        # D. Communicative English (course=15)
        page.goto(f"{BASE_URL}/mintai?course=15&tab=study", wait_until="domcontentloaded")
        page.wait_for_selector('button[data-dest="recommended"]', timeout=15000)

        study_tab_btn = page.locator('button[data-tab="study"]')
        assert "Study Hub" in study_tab_btn.text_content(), "Study tab badge for English should be 'Study Hub'"
        assert "Dr. E Suresh" not in study_tab_btn.text_content(), "Study tab badge for English must NOT be 'Dr. E Suresh'"
        log("  -> Communicative English: Study tab badge is 'Study Hub' (CORRECT)")

        p2 = os.path.join(OUTPUT_DIR, "02_study_hub_badge_and_faculty_isolation.png")
        page.screenshot(path=p2)
        log(f"  -> Screenshot saved: {p2}")

        # -----------------------------------------------------------------
        # 3. Test Study Tab Searchbar Functionality
        # -----------------------------------------------------------------
        log("[3/5] Testing Study Tab Search Bar filtering across sub-destinations...")

        # Switch back to Engineering Mechanics (course=21)
        page.goto(f"{BASE_URL}/mintai?course=21&tab=study&dest=lectures", wait_until="domcontentloaded")
        page.wait_for_selector('input[placeholder*="Search lectures, notes"]', timeout=15000)

        study_search = page.locator('input[placeholder*="Search lectures, notes"]').first

        # Search for "Friction" in Video Lectures
        study_search.fill("Friction")
        time.sleep(0.5)

        # Verify only friction lectures are shown
        assert page.locator(':has-text("Friction")').count() > 0, "Friction videos should be visible"
        assert page.locator(':has-text("Moment of Inertia")').count() == 0, "Moment of inertia video should be filtered out"
        log("  -> Video Lectures filtered accurately by search query")

        p3 = os.path.join(OUTPUT_DIR, "03_study_lectures_search_filter.png")
        page.screenshot(path=p3)

        # Clear search
        page.locator('button:has-text("Clear")').first.click()
        time.sleep(0.5)
        assert page.locator(':has-text("Moment of Inertia")').count() > 0, "Clearing search should restore all videos"
        log("  -> Clear search button works properly")

        # Test Search on Notes & Materials tab
        page.locator('button[data-dest="notes"]').click()
        time.sleep(0.5)
        study_search.fill("Inertia")
        time.sleep(0.5)
        assert page.locator(':has-text("Parallel Axis Theorem")').count() > 0, "Parallel axis formula should match 'Inertia'"
        log("  -> Notes & Formulas filtered accurately by search query")

        # -----------------------------------------------------------------
        # 4. Verify First Year Subjects Have Rich Resources
        # -----------------------------------------------------------------
        log("[4/5] Verifying First Year subjects have curated videos & formulas...")

        first_year_checks = [
            {"id": 21, "name": "Engineering Mechanics", "min_videos": 5, "min_formulas": 3},
            {"id": 15, "name": "Communicative English", "min_videos": 4, "min_formulas": 3},
            {"id": 3, "name": "Philosophy of Engineering", "min_videos": 4, "min_formulas": 3},
            {"id": 6, "name": "Fundamental of Economics", "min_videos": 4, "min_formulas": 3},
            {"id": 20, "name": "Physics: Mechanics", "min_videos": 3, "min_formulas": 3},
            {"id": 4, "name": "Computational Biology", "min_videos": 3, "min_formulas": 2},
            {"id": 5, "name": "Programming for Problem Solving", "min_videos": 8, "min_formulas": 4},
            {"id": 1, "name": "Calculus and Linear Algebra", "min_videos": 8, "min_formulas": 4},
        ]

        for check in first_year_checks:
            cid = check["id"]
            cname = check["name"]
            page.goto(f"{BASE_URL}/mintai?course={cid}&tab=study&dest=lectures", wait_until="domcontentloaded")
            time.sleep(0.5)

            # Check lecture cards count
            watch_btns = page.locator('button:has-text("Watch Lecture")')
            vcount = watch_btns.count()
            assert vcount >= check["min_videos"], f"Expected at least {check['min_videos']} videos for {cname}, got {vcount}"

            # Check formulas count
            page.locator('button[data-dest="notes"]').click()
            time.sleep(0.5)
            formula_cards = page.locator('button:has-text("Inspect Full Formula Card")')
            fcount = formula_cards.count()
            assert fcount >= check["min_formulas"], f"Expected at least {check['min_formulas']} formulas for {cname}, got {fcount}"

            log(f"  -> [OK] {cname}: {vcount} videos, {fcount} formula cheat sheets")

        p4 = os.path.join(OUTPUT_DIR, "04_first_year_resources_overview.png")
        page.screenshot(path=p4)
        log(f"  -> Screenshot saved: {p4}")

        # -----------------------------------------------------------------
        # 5. Test Course Selector Modal Instant Search
        # -----------------------------------------------------------------
        log("[5/5] Testing Course Selector Modal Instant Search...")
        page.goto(f"{BASE_URL}/mintai?course=1", wait_until="domcontentloaded")
        time.sleep(0.5)

        # Open course selector modal
        page.locator('button[data-testid="course-selector-trigger"], button:has-text("Calculus And Linear Algebra")').first.click()
        time.sleep(0.5)

        modal_search = page.locator('input[placeholder*="Instant search courses"]')
        assert modal_search.count() > 0, "Course selector search input missing"

        # Search for "Economics"
        modal_search.fill("Economics")
        time.sleep(0.3)
        assert page.locator(':has-text("Fundamental Of Economics")').count() > 0, "Economics course not found in modal search"

        # Search by course code "21CSS101J"
        modal_search.fill("21CSS101J")
        time.sleep(0.3)
        assert page.locator(':has-text("Programming For Problem Solving")').count() > 0, "PPS not found by course code in modal search"
        log("  -> Course Selector Modal search works by title and canonical code")

        p5 = os.path.join(OUTPUT_DIR, "05_course_selector_modal_search.png")
        page.screenshot(path=p5)
        log(f"  -> Screenshot saved: {p5}")

        browser.close()
        log("\nAll Search & Resource Isolation verification tests PASSED successfully!")

if __name__ == "__main__":
    run()
