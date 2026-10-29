from playwright.sync_api import sync_playwright
import time
import json

def capture_calculus_real():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 920},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # Set localStorage before navigation
        study_context = {
            "course_id": 1,
            "course_name": "Calculus and Linear Algebra",
            "course_code": "21MAB101T",
            "branch": "Computer Science and Engineering",
            "semester": 1,
            "assessment_cycle": "ALL"
        }
        page.add_init_script(f"""
            localStorage.setItem('markmint_study_context', JSON.stringify({json.dumps(study_context)}));
        """)

        # Navigate to mintai
        page.goto("https://markmint.vercel.app/mintai", wait_until="networkidle")
        time.sleep(1.5)

        # Inject CSS to remove unwanted overlays
        page.add_style_tag(content="""
            div:has-text("We use essential cookies"),
            .fixed.bottom-6.right-6,
            button[aria-label*="contact"],
            button[aria-label*="Scroll to top"],
            ::-webkit-scrollbar { display: none !important; }
        """)

        # Also JS removal
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) {
                    el.style.display = 'none';
                }
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        time.sleep(1)

        # Click Generate Forecast
        gen_btn = page.query_selector('button:has-text("Generate Forecast")')
        if gen_btn and not gen_btn.is_disabled():
            gen_btn.click()
            print("Clicked Generate Forecast for Calculus!")
            time.sleep(4)

        # Remove only the exact bottom banners / buttons
        page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            btns.forEach(b => {
                if (b.innerText && (b.innerText.includes('Decline') || b.innerText.includes('Accept'))) {
                    const card = b.closest('.fixed, [role=\"region\"], .bg-card');
                    if (card) card.remove();
                }
                if (b.innerText && b.innerText.includes('Was this forecast useful?')) {
                    const bar = b.closest('.fixed, .bg-card');
                    if (bar) bar.remove();
                }
            });
            document.querySelectorAll('.fixed.bottom-6.right-6, section[aria-label*=\"Notifications\"]').forEach(el => el.remove());
        }""")

        # Take full screenshot
        page.screenshot(path="scratch/screenshots/mintai_real_calculus.png")
        print("Captured scratch/screenshots/mintai_real_calculus.png!")

        browser.close()

if __name__ == "__main__":
    capture_calculus_real()
