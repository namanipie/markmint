import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"

def capture(slug, out_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1300}, device_scale_factor=2, color_scheme="dark")
        page.goto(f"http://localhost:3000/dashboard?course={slug}&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)

        # Dismiss cookie banner
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        # Reveal faculty key if button present
        btn = page.query_selector("button:has-text('Reveal Faculty Answer Key')")
        if btn:
            btn.scroll_into_view_if_needed()
            btn.click()
            page.wait_for_timeout(800)

        out_path = os.path.join(ARTIFACT_DIR, out_name)
        page.screenshot(path=out_path)
        print(f"Captured: {out_path}", flush=True)
        browser.close()

def capture_qb(out_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1100}, device_scale_factor=2, color_scheme="dark")
        page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        btn = page.query_selector("button:has-text('Cycle Test')")
        if btn:
            btn.click()
            page.wait_for_timeout(2000)

        out_path = os.path.join(ARTIFACT_DIR, out_name)
        page.screenshot(path=out_path)
        print(f"Captured: {out_path}", flush=True)
        browser.close()

def main():
    capture("artificial-intelligence", "dashboard_ai_ct1_questions.png")
    capture("computer-networks", "dashboard_cn_ct1_questions.png")
    capture("internet-of-things", "dashboard_iot_ct1_questions.png")
    capture_qb("question_bank_all_43_subjects_ct.png")

if __name__ == '__main__':
    main()
