from playwright.sync_api import sync_playwright
import time

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        # 1600x900 at 2x gives a crisp 3200x1800 capture
        context = browser.new_context(
            viewport={"width": 1600, "height": 920},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()
        
        # Go to mintai page with Calculus and Linear Algebra preselected
        page.goto("https://markmint.vercel.app/mintai?course_id=1", wait_until="networkidle")
        time.sleep(1.5)


        # Inject CSS to remove unwanted overlays
        page.add_style_tag(content="""
            /* Hide cookie banner */
            div:has(> div:has-text("cookies")),
            div:has-text("We use essential cookies"),
            /* Hide floating action buttons */
            .fixed.bottom-6.right-6,
            button[aria-label*="contact"],
            button[aria-label*="Scroll to top"],
            /* Clean up scrollbars */
            ::-webkit-scrollbar { display: none !important; }
        """)

        # Also JS removal to be 100% sure
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) {
                    el.style.display = 'none';
                }
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        # Click Generate Forecast button
        forecast_btn = page.query_selector('button:has-text("Generate Forecast")')
        if forecast_btn and not forecast_btn.is_disabled():
            forecast_btn.click()
            time.sleep(3)
            page.screenshot(path="scratch/screenshots/mintai_forecast_clicked.png")
            print("Captured scratch/screenshots/mintai_forecast_clicked.png")

        # Also let's test clicking Repetition Analytics tab
        rep_tab = page.query_selector('button:has-text("Repetition Analytics")')
        if rep_tab:
            rep_tab.click()
            time.sleep(2)
            page.screenshot(path="scratch/screenshots/mintai_analytics_tab.png")
            print("Captured scratch/screenshots/mintai_analytics_tab.png")

        browser.close()

if __name__ == "__main__":
    capture()
