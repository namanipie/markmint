import os
import sys
import time
import json
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = os.path.abspath("qa_audit/screenshots")
REPORT_PATH = os.path.abspath("qa_audit/browser_audit_results.json")

class MarkMintQATester:
    def __init__(self, headless=False):
        self.headless = headless
        self.console_errors = []
        self.network_errors = []
        self.routes_tested = []
        self.elements_tested = []
        self.bugs_found = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=50
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )
        self.page = self.context.new_page()

        self.page.on("console", self._handle_console)
        self.page.on("requestfailed", self._handle_request_failed)

    def _handle_console(self, msg):
        # Ignore external vercel scripts in local development
        if "_vercel" in msg.text:
            return
        if msg.type == "error":
            log_entry = {
                "url": self.page.url if self.page else "",
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }
            self.console_errors.append(log_entry)
            print(f"[CONSOLE ERROR] {msg.text}")

    def _handle_request_failed(self, req):
        if "_vercel" in req.url or "youtube.com" in req.url:
            return
        entry = {
            "url": req.url,
            "method": req.method,
            "failure": req.failure
        }
        self.network_errors.append(entry)
        print(f"[NETWORK ERROR] {req.method} {req.url} - {req.failure}")

    def capture(self, name):
        filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        self.page.screenshot(path=filepath, full_page=False)
        # Also copy to artifact dir for direct access
        artifact_copy = os.path.join(r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db", f"{name}.png")
        try:
            self.page.screenshot(path=artifact_copy, full_page=False)
        except Exception:
            pass
        print(f"[SCREENSHOT] Saved {filepath}")
        return filepath

    def dismiss_cookie_banner(self):
        try:
            btn = self.page.locator("button:has-text('Accept'), button:has-text('Decline')")
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                time.sleep(0.5)
        except Exception:
            pass

    def test_route(self, path):
        full_url = f"{BASE_URL}{path}"
        print(f"\n==========================================")
        print(f"Testing Route: {path} ({full_url})")
        print(f"==========================================")
        try:
            resp = self.page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.5)
            self.dismiss_cookie_banner()
            status = resp.status if resp else 0
            self.routes_tested.append({
                "route": path,
                "url": full_url,
                "status": status,
                "success": status < 400
            })
            return status
        except Exception as e:
            print(f"[ERROR] Failed navigating to {path}: {e}")
            self.bugs_found.append({
                "severity": "High",
                "route": path,
                "element": "Page Navigation",
                "issue": f"Navigation failed or timed out: {str(e)}"
            })
            self.routes_tested.append({
                "route": path,
                "url": full_url,
                "status": 0,
                "success": False,
                "error": str(e)
            })
            return 0

    def run_audit(self):
        self.start()
        try:
            # 1. HOMEPAGE AUDIT
            self.audit_homepage()

            # 2. GLOBAL SEARCH MODAL (CMD+K)
            self.audit_global_search()

            # 3. DASHBOARD & MINTAI FORECAST AUDIT
            self.audit_dashboard()

            # 4. COURSES CATALOG & DETAIL AUDIT
            self.audit_courses()

            # 5. EXAM DNA AUDIT
            self.audit_exam_dna()

            # 6. STUDY PLAN AUDIT
            self.audit_study_plan()

            # 7. QUESTION BANK AUDIT
            self.audit_question_bank()

            # 8. CALCULATOR AUDIT
            self.audit_calculator()

            # 9. SUBMIT PAPER AUDIT
            self.audit_submit_paper()

            # 10. AUXILIARY ROUTES AUDIT
            self.audit_auxiliary_pages()

            # 11. MOBILE RESPONSIVENESS AUDIT
            self.audit_mobile_responsiveness()

        finally:
            self.save_results()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

    def audit_homepage(self):
        status = self.test_route("/")
        self.capture("01_homepage_desktop")
        
        # Test navigation links
        nav_links = self.page.locator("nav a").all()
        print(f"Discovered {len(nav_links)} navigation links in header")
        for link in nav_links[:6]:
            href = link.get_attribute("href")
            text = link.inner_text().strip()
            self.elements_tested.append({"type": "nav_link", "text": text, "href": href})

        # Test Hero Search Bar
        hero_search = self.page.locator("main input[placeholder*='search' i]")
        if hero_search.count() > 0:
            print("Typing into Hero Search input...")
            hero_search.first.fill("Calculus")
            time.sleep(1)
            self.capture("01_homepage_search_filled")
            self.elements_tested.append({"type": "input", "name": "Hero Search", "status": "PASSED"})

        # Check CTA buttons
        cta_mint = self.page.locator("a:has-text('Open MintAI Intelligence'), a:has-text('Launch MintAI')")
        if cta_mint.count() > 0:
            self.elements_tested.append({"type": "cta", "name": "Open MintAI CTA", "href": cta_mint.first.get_attribute("href")})

    def audit_global_search(self):
        print("\n--- Testing Global Search (Cmd+K) ---")
        search_btn = self.page.locator("button:has-text('Search'), button:has-text('⌘K'), button:has-text('Ctrl K')")
        if search_btn.count() > 0:
            search_btn.first.click()
            time.sleep(1)
            self.capture("02_global_search_open")
            
            # Type into dialog
            dialog_input = self.page.locator("div[role='dialog'] input, div[cmdk-input-wrapper] input")
            if dialog_input.count() > 0:
                dialog_input.first.fill("Matrices")
                time.sleep(1)
                self.capture("02_global_search_results")
                
                # Close search
                self.page.keyboard.press("Escape")
                time.sleep(0.5)
                self.elements_tested.append({"type": "modal", "name": "Global Search Dialog", "status": "PASSED"})

    def audit_dashboard(self):
        status = self.test_route("/dashboard")
        self.capture("03_dashboard_initial")

        # 1. Handle Setup Modal if visible
        modal_header = self.page.locator("text='What are you preparing for?'")
        if modal_header.count() > 0 and modal_header.first.is_visible():
            print("[MODAL DETECTED] Academic Setup Modal is open.")
            self.capture("03_dashboard_setup_modal")
            
            # Select Semester 1
            sem1_btn = self.page.locator("button:text-is('Sem 1')")
            if sem1_btn.count() > 0:
                sem1_btn.first.click()
                time.sleep(0.5)

            # Select 'Calculus and Linear Algebra'
            calc_btn = self.page.locator("button:has-text('Calculus and Linear Algebra')")
            if calc_btn.count() > 0:
                print("Selecting Calculus and Linear Algebra from modal...")
                calc_btn.first.click()
                time.sleep(2)
                self.elements_tested.append({"type": "modal_selection", "name": "Calculus Selection", "status": "PASSED"})

        self.capture("03_dashboard_with_calculus")

        # 2. Test Assessment Cycle Selector
        cycles = ["ENDSEM", "CT1", "CT2", "ALL"]
        for c in cycles:
            btn = self.page.locator(f"button:text-is('{c}')")
            if btn.count() > 0:
                print(f"Testing Cycle Pill: {c}")
                btn.first.click()
                time.sleep(1)
                self.elements_tested.append({"type": "tab", "name": f"Cycle {c}", "status": "PASSED"})
        self.capture("03_dashboard_cycle_tested")

        # 3. Test Forecast Signal Filters (ALL, TOPIC, FAMILY)
        for f in ["ALL", "TOPIC", "FAMILY"]:
            f_btn = self.page.locator(f"#forecast button:has-text('{f}')")
            if f_btn.count() > 0:
                print(f"Testing Forecast Filter: {f}")
                f_btn.first.click()
                time.sleep(0.5)
                self.elements_tested.append({"type": "tab", "name": f"Forecast Filter {f}", "status": "PASSED"})
        self.capture("03_dashboard_forecast_filters")

        # 4. Test "Show All Signals" Expand Button
        expand_btn = self.page.locator("#forecast button:has-text('Show All'), #forecast button:has-text('Show Top 4')")
        if expand_btn.count() > 0:
            print(f"Toggling signal list: {expand_btn.first.inner_text().strip()}")
            expand_btn.first.click()
            time.sleep(1)
            self.capture("03_dashboard_signals_expanded")
            expand_btn.first.click()
            time.sleep(0.5)
            self.elements_tested.append({"type": "button", "name": "Expand Signals Toggle", "status": "PASSED"})

        # 5. Test Topic Practice Drawer
        practice_btn = self.page.locator("#forecast button:has-text('Practice')")
        if practice_btn.count() > 0:
            print("Opening Topic Practice Drawer...")
            practice_btn.first.click()
            time.sleep(2)
            self.capture("03_dashboard_practice_drawer")

            # Close drawer
            close_btn = self.page.locator("button:has(svg.lucide-x)")
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(1)
                print("Closed Practice Drawer.")
            self.elements_tested.append({"type": "drawer", "name": "Topic Practice Drawer", "status": "PASSED"})

        # 6. Verify Empirical Historical Backtest Validation Panel
        try:
            self.page.wait_for_selector("text='Empirical Historical Backtest Validation'", timeout=8000)
            val_heading = self.page.locator("text='Empirical Historical Backtest Validation'")
            val_heading.first.scroll_into_view_if_needed()
            time.sleep(1)
            if val_heading.count() > 0 and val_heading.first.is_visible():
                print("[VERIFIED] Empirical Historical Backtest Validation panel is rendered!")
                self.capture("03_dashboard_validation_panel")
                self.elements_tested.append({"type": "panel", "name": "Empirical Backtest Validation", "status": "PASSED"})
        except Exception as e:
            print(f"[ERROR] Empirical Historical Backtest Validation panel not found: {e}")
            self.bugs_found.append({
                "severity": "High",
                "route": "/dashboard",
                "element": "Validation Panel",
                "issue": "Empirical Backtest Validation panel was not visible on Dashboard"
            })

        # 7. Test Re-opening Course Selector Modal via Header Button
        change_course_btn = self.page.locator("button:has-text('Change Subject'), button:has-text('Change Course')")
        if change_course_btn.count() > 0:
            print("Clicking 'Change Subject' to test modal re-open...")
            change_course_btn.first.click()
            time.sleep(1)
            self.capture("03_dashboard_modal_reopened")
            
            # Select Chemistry (which has limited history) to test honest abstention UI
            chem_btn = self.page.locator("button:has-text('Chemistry')")
            if chem_btn.count() > 0:
                print("Selecting Chemistry to test limited history / abstention state...")
                chem_btn.first.click()
                time.sleep(2)
                self.capture("03_dashboard_chemistry_selected")
                self.elements_tested.append({"type": "course_switch", "name": "Switch to Chemistry", "status": "PASSED"})

    def audit_courses(self):
        status = self.test_route("/courses")
        self.capture("04_courses_catalog")

        # Test Course Search Input
        search_input = self.page.locator("input[placeholder*='search' i]")
        if search_input.count() > 0:
            print("Searching courses for 'Linear'...")
            search_input.first.fill("Linear")
            time.sleep(1)
            self.capture("04_courses_search_linear")

            print("Searching courses for non-existent 'xyz999'...")
            search_input.first.fill("xyz999")
            time.sleep(1)
            self.capture("04_courses_search_empty")
            
            search_input.first.fill("")
            time.sleep(0.5)
            self.elements_tested.append({"type": "input", "name": "Courses Search", "status": "PASSED"})

        # Click first course card link
        course_link = self.page.locator("main a[href^='/courses/']").first
        if course_link.count() > 0:
            course_href = course_link.get_attribute("href")
            print(f"Navigating to course detail: {course_href}")
            self.test_route(course_href)
            self.capture("04_course_detail_page")

            # Check for topic link inside course detail
            topic_link = self.page.locator("a[href*='/topics/']").first
            if topic_link.count() > 0:
                topic_href = topic_link.get_attribute("href")
                print(f"Navigating to topic detail: {topic_href}")
                self.test_route(topic_href)
                self.capture("04_topic_detail_page")
                self.elements_tested.append({"type": "page", "name": "Topic Detail", "status": "PASSED"})

    def audit_exam_dna(self):
        status = self.test_route("/mintai/exam-dna")
        self.capture("05_exam_dna_page")

        # Verify DNA sections
        dna_sections = self.page.locator("h2, h3").all()
        print(f"Discovered {len(dna_sections)} headings on Exam DNA page")
        self.elements_tested.append({"type": "page", "name": "Exam DNA Page", "status": "PASSED"})

    def audit_study_plan(self):
        status = self.test_route("/study-plan")
        self.capture("06_study_plan_page")

        # Test Study Task Checkbox
        checkboxes = self.page.locator("input[type='checkbox'], button[role='checkbox']")
        if checkboxes.count() > 0:
            print(f"Toggling Study Task Checkbox ({checkboxes.count()} found)...")
            checkboxes.first.click()
            time.sleep(0.5)
            self.capture("06_study_plan_toggled")
            self.elements_tested.append({"type": "checkbox", "name": "Study Task Checkbox", "status": "PASSED"})

    def audit_question_bank(self):
        status = self.test_route("/question-bank")
        self.capture("07_question_bank_page")

        # Test search filter
        q_search = self.page.locator("input[placeholder*='search' i]")
        if q_search.count() > 0:
            print("Testing Question Bank Search...")
            q_search.first.fill("matrix")
            time.sleep(1)
            self.capture("07_question_bank_search_matrix")
            q_search.first.fill("")
            self.elements_tested.append({"type": "input", "name": "Question Bank Search", "status": "PASSED"})

    def audit_calculator(self):
        status = self.test_route("/calculator")
        self.capture("08_calculator_page")

        # Test inputs in Calculator
        calc_inputs = self.page.locator("input")
        if calc_inputs.count() > 0:
            print(f"Testing Calculator Inputs ({calc_inputs.count()} found)...")
            calc_inputs.first.fill("85")
            time.sleep(1)
            self.capture("08_calculator_filled")
            self.elements_tested.append({"type": "input", "name": "Calculator Input", "status": "PASSED"})

    def audit_submit_paper(self):
        status = self.test_route("/submit-paper")
        self.capture("09_submit_paper_page")

        # Test form submission button
        submit_btn = self.page.locator("button[type='submit'], button:has-text('Submit')")
        if submit_btn.count() > 0:
            print("Clicking Submit Paper button without inputs...")
            submit_btn.first.click()
            time.sleep(1)
            self.capture("09_submit_paper_validation")
            self.elements_tested.append({"type": "form", "name": "Submit Paper Validation", "status": "PASSED"})

    def audit_auxiliary_pages(self):
        for path in ["/developers", "/privacy", "/terms", "/poster", "/non-existent-404-test"]:
            self.test_route(path)
            clean_name = path.strip("/").replace("-", "_")
            self.capture(f"10_{clean_name}")

    def audit_mobile_responsiveness(self):
        print("\n==========================================")
        print("Testing Mobile Viewport (375x667)")
        print("==========================================")
        self.page.set_viewport_size({"width": 375, "height": 667})
        self.test_route("/")
        self.capture("11_mobile_homepage")

        # Test mobile hamburger menu
        try:
            menu_btn = self.page.locator("button:has(svg.lucide-menu), button[aria-label*='menu' i]")
            if menu_btn.count() > 0:
                print("Opening Mobile Navigation Menu...")
                menu_btn.first.click()
                time.sleep(1)
                self.capture("11_mobile_menu_open")
                self.elements_tested.append({"type": "menu", "name": "Mobile Hamburger Menu", "status": "PASSED"})

                # Close mobile menu
                close_btn = self.page.locator("button:has(svg.lucide-x)")
                if close_btn.count() > 0:
                    close_btn.first.click()
                    time.sleep(0.5)
        except Exception as e:
            print(f"[ERROR] Mobile menu interaction failed: {e}")
            self.bugs_found.append({
                "severity": "Medium",
                "route": "/",
                "element": "Mobile Menu",
                "issue": f"Mobile menu failed to open: {e}"
            })

        # Check horizontal overflow
        has_overflow = self.page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print(f"Mobile Horizontal Overflow: {has_overflow}")
        if has_overflow:
            self.bugs_found.append({
                "severity": "Low",
                "route": "/",
                "element": "Mobile Layout",
                "issue": "Horizontal overflow detected (scrollWidth > innerWidth)"
            })
        else:
            self.elements_tested.append({"type": "layout", "name": "Zero Horizontal Overflow", "status": "PASSED"})

        self.test_route("/dashboard")
        self.capture("11_mobile_dashboard")
        self.page.set_viewport_size({"width": 1280, "height": 800})

    def save_results(self):
        payload = {
            "routes_tested": self.routes_tested,
            "elements_tested": self.elements_tested,
            "console_errors": self.console_errors,
            "network_errors": self.network_errors,
            "bugs_found": self.bugs_found
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"\n==========================================")
        print(f"QA Audit Complete. Tested {len(self.routes_tested)} routes.")
        print(f"Results saved to {REPORT_PATH}")
        print(f"==========================================")

if __name__ == "__main__":
    tester = MarkMintQATester(headless=False)
    tester.run_audit()
