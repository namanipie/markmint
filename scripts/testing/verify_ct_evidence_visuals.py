import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1500, "height": 950},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # ------------------------------------------------------------------
        # 1. Operating Systems CT1 on Dashboard
        # ------------------------------------------------------------------
        print("Navigating to Dashboard: Operating Systems (CT1)...", flush=True)
        page.goto("http://localhost:3000/dashboard?course=operating-systems&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Inject styling cleanup
        page.add_style_tag(content="""
            div:has-text("We use essential cookies"),
            .fixed.bottom-6.right-6 { display: none !important; }
            ::-webkit-scrollbar { display: none !important; }
        """)

        # Look for the Authentic CT1 Questions drawer button
        drawer_btn = page.query_selector('button:has-text("Authentic CT1 Questions")')
        if drawer_btn:
            print("Found Authentic CT1 Questions drawer button. Clicking to expand...", flush=True)
            drawer_btn.click()
            page.wait_for_timeout(1000)
            
            # Click "Reveal Faculty Answer Key" if available
            reveal_btn = page.query_selector('button:has-text("Reveal Faculty Answer Key")')
            if reveal_btn:
                print("Revealing faculty answer key...", flush=True)
                reveal_btn.click()
                page.wait_for_timeout(800)

        shot1_path = os.path.join(ARTIFACT_DIR, "dashboard_os_ct1_questions.png")
        page.screenshot(path=shot1_path)
        print(f"Captured: {shot1_path}", flush=True)

        # ------------------------------------------------------------------
        # 2. Compiler Design CT1 on Dashboard
        # ------------------------------------------------------------------
        print("Navigating to Dashboard: Compiler Design (CT1)...", flush=True)
        page.goto("http://localhost:3000/dashboard?course=compiler-design&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        drawer_btn = page.query_selector('button:has-text("Authentic CT1 Questions")')
        if drawer_btn:
            print("Found Compiler Design CT1 drawer. Clicking to expand...", flush=True)
            drawer_btn.click()
            page.wait_for_timeout(1000)
            reveal_btn = page.query_selector('button:has-text("Reveal Faculty Answer Key")')
            if reveal_btn:
                reveal_btn.click()
                page.wait_for_timeout(800)

        shot2_path = os.path.join(ARTIFACT_DIR, "dashboard_cd_ct1_questions.png")
        page.screenshot(path=shot2_path)
        print(f"Captured: {shot2_path}", flush=True)

        # ------------------------------------------------------------------
        # 3. Question Bank Cycle Test Archive Tab
        # ------------------------------------------------------------------
        print("Navigating to Question Bank...", flush=True)
        page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Click SRMIST Cycle Test Papers tab
        ct_tab = page.query_selector('button:has-text("Cycle Test")')
        if ct_tab:
            print("Clicking Cycle Test tab in Question Bank...", flush=True)
            ct_tab.click()
            page.wait_for_timeout(2000)

        shot3_path = os.path.join(ARTIFACT_DIR, "question_bank_ct_archive_expanded.png")
        page.screenshot(path=shot3_path)
        print(f"Captured: {shot3_path}", flush=True)

        browser.close()
        print("All visual verification screenshots captured successfully!")

if __name__ == '__main__':
    run()
