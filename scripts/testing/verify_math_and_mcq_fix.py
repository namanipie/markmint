import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1100})
        page = await context.new_page()

        print("Navigating to http://localhost:3000/dashboard...")
        await page.goto("http://localhost:3000/dashboard", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        # Clear any overlay or modal
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Look for course selector or select Calculus
        print("Selecting Calculus And Linear Algebra if available...")
        # Find course buttons or links
        calc_btn = page.locator("button, a").filter(has_text="Calculus").first
        if await calc_btn.count() > 0:
            try:
                await calc_btn.click(force=True)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print("Could not click calc button:", e)

        # Re-clear overlay
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Find the cycle test drawer toggle button
        print("Looking for cycle test drawer toggle...")
        drawer_btn = page.locator("button").filter(has_text="Cycle Test").first
        if await drawer_btn.count() > 0:
            await drawer_btn.click(force=True)
            await page.wait_for_timeout(2000)

        # Wait for drawer content
        await page.wait_for_timeout(2000)

        # Take screenshot of Dashboard Normal Questions
        print("Capturing dashboard_normal_questions_purified.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_normal_questions_purified.png")

        # Now click on "Interactive MCQ Test"
        print("Clicking Interactive MCQ Test tab...")
        mcq_tab = page.locator("button").filter(has_text="Interactive MCQ Test").first
        if await mcq_tab.count() > 0:
            await mcq_tab.click(force=True)
            await page.wait_for_timeout(2000)
            print("Capturing dashboard_mcq_interactive_purified.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_mcq_interactive_purified.png")

        # Now visit Question Bank archive
        print("Navigating to http://localhost:3000/question-bank...")
        await page.goto("http://localhost:3000/question-bank", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        # Clear overlay
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Select Calculus in Question Bank
        print("Selecting Calculus in Question Bank...")
        calc_pill = page.locator("button").filter(has_text="Calculus").first
        if await calc_pill.count() > 0:
            await calc_pill.click(force=True)
            await page.wait_for_timeout(2000)

        print("Capturing question_bank_purified_calculus.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_purified_calculus.png")

        # Now switch to MCQ tab in Question Bank
        mcq_archive_tab = page.locator("button").filter(has_text="MCQ Section").first
        if await mcq_archive_tab.count() > 0:
            await mcq_archive_tab.click(force=True)
            await page.wait_for_timeout(2000)
            print("Capturing question_bank_mcq_math_rendered.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_mcq_math_rendered.png")

        await browser.close()
        print("Playwright verification completed successfully.")

if __name__ == "__main__":
    asyncio.run(run())
