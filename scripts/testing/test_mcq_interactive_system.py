import os
from playwright.sync_api import sync_playwright

OUT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"

def run_interactive_mcq_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1300}, device_scale_factor=2, color_scheme="dark")

        print("1. Loading Dashboard for Operating Systems CT1...")
        page.goto("http://localhost:3000/dashboard?course=operating-systems&cycle=CT1", wait_until="domcontentloaded")
        page.wait_for_timeout(3500)

        # Dismiss cookies / overlays
        page.evaluate("""() => {
            document.querySelectorAll('div').forEach(el => {
                if (el.textContent && el.textContent.includes('We use essential cookies')) el.style.display = 'none';
            });
            document.querySelectorAll('.fixed.bottom-6.right-6').forEach(el => el.remove());
        }""")

        # Scroll to drawer
        drawer = page.query_selector("button:has-text('Authentic')")
        if drawer:
            drawer.scroll_into_view_if_needed()
            page.wait_for_timeout(500)

        # Click "Interactive MCQ Test" tab
        mcq_tab = page.query_selector("button:has-text('Interactive MCQ Test')")
        if mcq_tab:
            print("Clicking Interactive MCQ Test tab...")
            mcq_tab.click()
            page.wait_for_timeout(1500)

            # Test Practice Mode: Click an option on the first question!
            first_opt = page.query_selector("button:has-text('A')")
            # Let's find an option button inside the first question card
            opt_buttons = page.query_selector_all("div.grid.grid-cols-1 button")
            if opt_buttons:
                print(f"Found {len(opt_buttons)} option buttons! Clicking first option...")
                opt_buttons[0].click()
                page.wait_for_timeout(1000)

            out_practice = os.path.join(OUT_DIR, "mcq_interactive_practice_option_selected.png")
            page.screenshot(path=out_practice)
            print("Saved:", out_practice)

            # Test Timed Quiz Mode
            quiz_btn = page.query_selector("button:has-text('Timed Quiz Mode')")
            if quiz_btn:
                print("Switching to Timed Quiz Mode...")
                quiz_btn.click()
                page.wait_for_timeout(1500)

                # Select an option for Q1
                quiz_opts = page.query_selector_all("div.space-y-4 button")
                for btn in quiz_opts:
                    txt = btn.inner_text()
                    if txt.startswith("A") or txt.startswith("B") or "Option" in txt:
                        btn.click()
                        page.wait_for_timeout(500)
                        break

                # Click "Next Question"
                next_btn = page.query_selector("button:has-text('Next Question')")
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(500)

                # Select an option for Q2
                quiz_opts2 = page.query_selector_all("div.space-y-4 button")
                for btn in quiz_opts2:
                    txt = btn.inner_text()
                    if txt.startswith("B") or txt.startswith("C"):
                        btn.click()
                        page.wait_for_timeout(500)
                        break

                out_quiz_active = os.path.join(OUT_DIR, "mcq_interactive_quiz_in_progress.png")
                page.screenshot(path=out_quiz_active)
                print("Saved:", out_quiz_active)

                # Submit Quiz to see Scorecard
                submit_btn = page.query_selector("button:has-text('Submit Test')")
                if submit_btn:
                    print("Submitting quiz test...")
                    submit_btn.click()
                    page.wait_for_timeout(1500)

                    out_scorecard = os.path.join(OUT_DIR, "mcq_interactive_quiz_scorecard.png")
                    page.screenshot(path=out_scorecard)
                    print("Saved:", out_scorecard)

        # 2. Test Question Bank Universal Archive MCQ Mode
        print("\n2. Loading Question Bank...")
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
            ct_tab.click()
            page.wait_for_timeout(2000)

            qb_mcq_btn = page.query_selector("button:has-text('MCQ Testing System')")
            if qb_mcq_btn:
                print("Opening MCQ Testing System in Question Bank...")
                qb_mcq_btn.click()
                page.wait_for_timeout(1500)

                # Click an option
                qb_opts = page.query_selector_all("div.grid.grid-cols-1 button")
                if qb_opts:
                    qb_opts[1].click()
                    page.wait_for_timeout(1000)

                out_qb = os.path.join(OUT_DIR, "question_bank_mcq_interactive_test.png")
                page.screenshot(path=out_qb)
                print("Saved:", out_qb)

        browser.close()
        print("Interactive MCQ testing suite verification complete.")

if __name__ == '__main__':
    run_interactive_mcq_test()
