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

        print("Navigating to dashboard...")
        page.goto(f"{BASE_URL}/dashboard?course=1", wait_until="domcontentloaded")
        time.sleep(3)

        # Click CT1
        page.locator('button:has-text("CT1 (Units 1 & 2)")').first.click()
        time.sleep(2)

        # Click Interactive MCQ Test
        mcq_tab = page.locator('button:has-text("Interactive MCQ Test")').first
        mcq_tab.scroll_into_view_if_needed()
        time.sleep(1)
        mcq_tab.click()
        time.sleep(2)

        # Click Timed Quiz Mode
        quiz_btn = page.locator('button:has-text("Timed Quiz Mode")').first
        quiz_btn.scroll_into_view_if_needed()
        time.sleep(1)
        quiz_btn.click()
        time.sleep(2.5)

        # Scroll so the quiz interface and timer are prominent
        page.evaluate("window.scrollBy(0, 200)")
        time.sleep(1)

        p9 = os.path.join(OUTPUT_DIR, "09_mintai_timed_quiz_mode.png")
        page.screenshot(path=p9)
        print("Captured 09:", p9)

        # Copy to artifact
        shutil.copy2(p9, os.path.join(ARTIFACT_DIR, "09_mintai_timed_quiz_mode.png"))
        print("Copied to artifact dir.")

        browser.close()

if __name__ == "__main__":
    run()
