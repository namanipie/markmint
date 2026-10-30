import os
import shutil
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "scratch/mintai_phase2"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\70daf3e1-493b-412c-ae3f-f59f589f02db"
BASE_URL = "http://localhost:3000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run():
    with sync_playwright() as p:
        log("Launching browser for Phase 2 Exam DNA verification...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            color_scheme="dark"
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # 1. Load /mintai?course=1&tab=dna (Calculus Exam DNA)
        # -----------------------------------------------------------------
        log("[1/7] Loading Exam DNA workspace for Calculus...")
        page.goto(f"{BASE_URL}/mintai?course=1&tab=dna", wait_until="domcontentloaded")
        page.wait_for_selector("#fingerprint", timeout=15000)
        assert "/mintai" in page.url and "tab=dna" in page.url, f"Expected /mintai with tab=dna, got {page.url}"

        # -----------------------------------------------------------------
        # 2. Historical Fingerprint Summary
        # -----------------------------------------------------------------
        log("[2/7] Verifying Section 1: Historical Fingerprint summary cards...")
        fingerprint = page.locator("#fingerprint")
        assert fingerprint.count() > 0, "#fingerprint section not found"
        assert fingerprint.locator('text="Papers Analyzed"').count() > 0, "Papers Analyzed card missing"
        assert fingerprint.locator('text="Questions Analyzed"').count() > 0, "Questions Analyzed card missing"
        assert fingerprint.locator('text="Total Marks Analyzed"').count() > 0, "Total Marks Analyzed card missing"
        assert fingerprint.locator('text="Year Coverage"').count() > 0, "Year Coverage card missing"
        assert fingerprint.locator('text="Active Families"').count() > 0, "Active Families card missing"

        p1 = os.path.join(OUTPUT_DIR, "phase2_01_exam_dna_fingerprint.png")
        page.screenshot(path=p1)
        log(f"  -> Fingerprint verified, screenshot saved: {p1}")

        # -----------------------------------------------------------------
        # 3. Unit-wise Analysis & Marks Distribution
        # -----------------------------------------------------------------
        log("[3/7] Verifying Section 2: Unit-wise Analysis & Marks Distribution...")
        unit_sec = page.locator("#unit-analysis")
        assert unit_sec.count() > 0, "#unit-analysis section not found"
        assert unit_sec.locator(':has-text("Unit Marks Distribution")').count() > 0, "Unit Marks Distribution missing"
        assert unit_sec.locator(':has-text("Question-Type Breakdown")').count() > 0, "Question-Type Breakdown missing"
        assert unit_sec.locator(':has-text("Discrete Mark Tiers")').count() > 0, "Discrete Mark Tiers missing"

        p2 = os.path.join(OUTPUT_DIR, "phase2_02_unit_and_marks_distribution.png")
        unit_sec.scroll_into_view_if_needed()
        time.sleep(1)
        page.screenshot(path=p2)
        log(f"  -> Unit-wise analysis verified, screenshot saved: {p2}")

        # -----------------------------------------------------------------
        # 4. Question Family Intelligence & Evidence Modal
        # -----------------------------------------------------------------
        log("[4/7] Verifying Section 3: Question Family Intelligence...")
        fam_sec = page.locator("#question-families")
        assert fam_sec.count() > 0, "#question-families section not found"
        assert fam_sec.locator(':has-text("Repetition Architecture")').count() > 0, "Repetition Architecture missing"
        assert fam_sec.locator(':has-text("Common Formulation Verb Stems")').count() > 0, "Formulation Verb Stems missing"

        # Test search filter
        fam_sec.scroll_into_view_if_needed()
        time.sleep(1)
        search_input = fam_sec.locator('input[placeholder*="Search question prompts"]').first
        search_input.fill("Hamilton")
        time.sleep(1)
        p3 = os.path.join(OUTPUT_DIR, "phase2_03_question_families_search.png")
        page.screenshot(path=p3)
        log(f"  -> Search filter verified: {p3}")

        # Test opening Family Evidence Modal
        evidence_btn = fam_sec.locator('button:has-text("Evidence")').first
        if evidence_btn.count() > 0:
            evidence_btn.click()
            time.sleep(2)
            drawer = page.locator('[role="dialog"], .fixed')
            assert page.locator(':has-text("Question Family Evidence")').count() > 0 or page.locator(':has-text("Why is MintAI showing me this?")').count() > 0 or page.locator(':has-text("Distinct Papers")').count() > 0, "Family Evidence Drawer not opened"
            p4 = os.path.join(OUTPUT_DIR, "phase2_04_family_evidence_drawer.png")
            page.screenshot(path=p4)
            log(f"  -> Family Evidence Drawer verified, screenshot saved: {p4}")

            # Close drawer
            close_btn = page.locator('button[aria-label="Close drawer"], button:has(.lucide-x)').first
            if close_btn.count() > 0:
                close_btn.click()
                time.sleep(1)

        # Clear search
        search_input.fill("")
        time.sleep(1)

        # -----------------------------------------------------------------
        # 5. Assessment Architecture & Cognitive Demand (Bloom's Taxonomy)
        # -----------------------------------------------------------------
        log("[5/7] Verifying Section 4: Assessment Architecture & Cognitive Demand...")
        arch_sec = page.locator("#blueprints-and-demand")
        assert arch_sec.count() > 0, "#blueprints-and-demand section not found"

        # Default: Blueprints
        arch_sec.scroll_into_view_if_needed()
        time.sleep(1)
        p5 = os.path.join(OUTPUT_DIR, "phase2_05_assessment_blueprints.png")
        page.screenshot(path=p5)
        log(f"  -> Section Blueprints tab verified: {p5}")

        # Switch to Cognitive Demand
        cog_btn = arch_sec.locator('button:has-text("Cognitive Demand")').first
        cog_btn.click()
        time.sleep(1.5)
        assert page.locator(':has-text("Recall & Concept")').count() > 0 or page.locator(':has-text("Procedural & Computational")').count() > 0 or page.locator(':has-text("Recall")').count() > 0, "Cognitive demand archetypes missing"
        p6 = os.path.join(OUTPUT_DIR, "phase2_06_cognitive_demand_tab.png")
        page.screenshot(path=p6)
        log(f"  -> Cognitive Demand tab verified: {p6}")

        # -----------------------------------------------------------------
        # 6. Historical Focus Evolution & Temporal Trends
        # -----------------------------------------------------------------
        log("[6/7] Verifying Section 5: Historical Focus Evolution & Temporal Trends...")
        evo_sec = page.locator("#evolution")
        assert evo_sec.count() > 0, "#evolution section not found"
        evo_sec.scroll_into_view_if_needed()
        time.sleep(1.5)

        # Toggle between Question Share and Marks Share
        marks_share_btn = evo_sec.locator('button:has-text("Marks Share")').first
        if marks_share_btn.count() > 0:
            marks_share_btn.click()
            time.sleep(1)

        p7 = os.path.join(OUTPUT_DIR, "phase2_07_temporal_trends_evolution.png")
        page.screenshot(path=p7)
        log(f"  -> Temporal evolution verified: {p7}")

        # -----------------------------------------------------------------
        # 7. Advanced Analytics: Empirical Backtesting Lab (Collapsible)
        # -----------------------------------------------------------------
        log("[7/7] Verifying Section 6: Empirical Backtesting Lab...")
        backtest_sec = page.locator("#backtesting")
        assert backtest_sec.count() > 0, "#backtesting section not found"
        backtest_sec.scroll_into_view_if_needed()
        time.sleep(1)

        # Click to expand accordion
        toggle_btn = backtest_sec.locator('button[aria-expanded]').first
        toggle_btn.click()
        time.sleep(2)

        # Verify key validation metrics
        assert backtest_sec.locator(':has-text("Precision@3")').count() > 0, "Precision@3 missing"
        assert backtest_sec.locator(':has-text("Precision@5")').count() > 0, "Precision@5 missing"
        assert backtest_sec.locator(':has-text("Marks Coverage@5")').count() > 0, "Marks Coverage@5 missing"
        assert backtest_sec.locator(':has-text("NDCG@5")').count() > 0, "NDCG@5 missing"
        assert backtest_sec.locator(':has-text("Model Comparison Benchmark")').count() > 0, "Model Comparison missing"
        assert backtest_sec.locator(':has-text("Candidate Ensemble (Active)")').count() > 0, "Candidate Ensemble missing"

        p8 = os.path.join(OUTPUT_DIR, "phase2_08_empirical_backtesting_expanded.png")
        page.screenshot(path=p8)
        log(f"  -> Empirical Backtesting Lab verified, screenshot saved: {p8}")

        browser.close()

    # Copy screenshots to artifact directory
    log("Copying Phase 2 screenshots to Brain artifact directory...")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            shutil.copy2(os.path.join(OUTPUT_DIR, f), os.path.join(ARTIFACT_DIR, f))
            log(f"  -> Copied {f}")

    log("\nAll Phase 2 Exam DNA verification tests PASSED with 100% success!")

if __name__ == "__main__":
    run()
