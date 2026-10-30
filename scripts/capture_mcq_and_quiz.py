import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_showcase"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        print("Navigating to dashboard with PPS (course 5)...")
        page.goto(f"{BASE_URL}/dashboard?course=5", wait_until="domcontentloaded")
        time.sleep(3)

        # Click CT1 Preset
        ct1_btn = page.locator('button:has-text("CT1 (Units 1 & 2)")').first
        if ct1_btn.count() > 0:
            ct1_btn.click()
            time.sleep(2)

        # Scroll to Cycle Test Drawer
        page.evaluate("window.scrollBy(0, 260)")
        time.sleep(1)

        # Switch to Interactive MCQ Test
        mcq_tab = page.locator('button:has-text("Interactive MCQ Test")').first
        if mcq_tab.count() > 0:
            mcq_tab.click()
            time.sleep(2)

            # Click an option on the first question to show interactive evaluation
            opt = page.locator('button:has-text("C. Program"), button:has-text("B. Bitwise AND")').first
            if opt.count() == 0:
                opt = page.locator('button:has-text("A."), button:has-text("B."), button:has-text("C.")').first
            
            if opt.count() > 0:
                opt.click()
                time.sleep(1)

            # Expand explanation
            sol_btn = page.locator('button:has-text("Faculty Solution & Key")').first
            if sol_btn.count() > 0:
                sol_btn.click()
                time.sleep(0.5)

        p8 = os.path.join(OUTPUT_DIR, "08_mintai_interactive_mcq_suite.png")
        page.screenshot(path=p8)
        print("Captured 08:", p8)
        shutil.copy2(p8, os.path.join(ARTIFACT_DIR, "08_mintai_interactive_mcq_suite.png"))

        # Now switch to Timed Quiz Mode
        timed_tab = page.locator('button:has-text("Timed Quiz Mode")').first
        if timed_tab.count() > 0:
            timed_tab.click()
            time.sleep(2.5)

        p9 = os.path.join(OUTPUT_DIR, "09_mintai_timed_quiz_mode.png")
        page.screenshot(path=p9)
        print("Captured 09:", p9)
        shutil.copy2(p9, os.path.join(ARTIFACT_DIR, "09_mintai_timed_quiz_mode.png"))

        browser.close()
        print("Done!")

if __name__ == "__main__":
    run()
