import os
from playwright.sync_api import sync_playwright

OUT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1300}, device_scale_factor=2, color_scheme="dark")
        
        # 1. Capture Dashboard Operating Systems - Normal Questions Section
        print("1. Loading Dashboard for Operating Systems (Normal Questions)...")
        page.goto("http://localhost:3000/dashboard?course=operating-systems&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")
        
        drawer = page.query_selector("button:has-text('Authentic')")
        if drawer:
            drawer.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

        out1 = os.path.join(OUT_DIR, "dashboard_normal_questions_section.png")
        page.screenshot(path=out1)
        print("Saved:", out1)

        # 2. Click MCQ Section button in drawer
        mcq_btn = page.query_selector("button:has-text('Multiple Choice Section')")
        if mcq_btn:
            print("Found Multiple Choice Section button! Clicking...")
            mcq_btn.click()
            page.wait_for_timeout(1500)
            
            # Reveal answer key
            reveal = page.query_selector("button:has-text('Reveal Faculty Answer Key')")
            if reveal:
                reveal.click()
                page.wait_for_timeout(1000)

            out2 = os.path.join(OUT_DIR, "dashboard_mcq_section_revealed.png")
            page.screenshot(path=out2)
            print("Saved:", out2)

        # 3. Question Bank - Universal Archive MCQ Section
        print("\n3. Loading Question Bank Archive (MCQ Section)...")
        page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        ct_tab = page.query_selector("button:has-text('Cycle Test Archive')")
        if ct_tab:
            print("Found Cycle Test Archive tab! Clicking...")
            ct_tab.click()
            page.wait_for_timeout(2000)

            qb_mcq = page.query_selector("button:has-text('MCQ Section')")
            if qb_mcq:
                print("Found Question Bank MCQ Section button! Clicking...")
                qb_mcq.click()
                page.wait_for_timeout(1500)

                out3 = os.path.join(OUT_DIR, "question_bank_mcq_dedicated_archive.png")
                page.screenshot(path=out3)
                print("Saved:", out3)

        browser.close()
        print("Visual verification completed.")

if __name__ == '__main__':
    capture()
