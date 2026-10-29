import os
from playwright.sync_api import sync_playwright

def capture_course(course_slug, out_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1300}, device_scale_factor=2, color_scheme="dark")
        page.goto(f"http://localhost:3000/dashboard?course={course_slug}&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)
        
        # Dismiss overlays
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")
        
        btn = page.query_selector("button:has-text('Reveal Faculty Answer Key')")
        if btn:
            print(f"Found Reveal Faculty Answer Key for {course_slug}! Clicking...")
            btn.scroll_into_view_if_needed()
            btn.click()
            page.wait_for_timeout(1000)

        out_path = os.path.join(r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db", out_name)
        page.screenshot(path=out_path)
        print("Saved:", out_path)
        browser.close()

def main():
    capture_course("compiler-design", "dashboard_cd_ct1_questions_revealed.png")
    capture_course("fundamental-of-economics-foe", "dashboard_foe_ct1_questions_revealed.png")

if __name__ == '__main__':
    main()
