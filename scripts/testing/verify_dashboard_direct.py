import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1300})
        page = await context.new_page()

        print("Navigating to http://localhost:3000/dashboard?course=calculus&cycle=CT1...")
        await page.goto("http://localhost:3000/dashboard?course=calculus&cycle=CT1", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        # Clear overlay
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Look for the Cycle Test Questions Drawer
        print("Looking for cycle test drawer...")
        drawer = page.locator("text=Authentic CT1 Questions").or_(page.locator("text=Cycle Test")).or_(page.locator("text=Questions & Testing System")).first
        if await drawer.count() > 0:
            print("Found drawer! Scrolling and opening...")
            await drawer.scroll_into_view_if_needed()
            await drawer.click(force=True)
            await page.wait_for_timeout(2000)

        # Reveal faculty answer key on first question
        sol_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await sol_btn.count() > 0:
            await sol_btn.scroll_into_view_if_needed()
            await sol_btn.click(force=True)
            await page.wait_for_timeout(1000)

        # Take screenshot of Normal Questions
        print("Capturing calculus_dashboard_normal_questions.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_dashboard_normal_questions.png")

        # Now click Interactive MCQ Test
        mcq_btn = page.locator("button:has-text('Interactive MCQ Test')").first
        if await mcq_btn.count() > 0:
            print("Switching to Interactive MCQ Test tab...")
            await mcq_btn.scroll_into_view_if_needed()
            await mcq_btn.click(force=True)
            await page.wait_for_timeout(2000)

            # Click option B or A on the first MCQ
            opt_btn = page.locator("button:has-text('B')").first
            if await opt_btn.count() > 0:
                await opt_btn.click(force=True)
                await page.wait_for_timeout(1000)

            print("Capturing calculus_dashboard_mcq_interactive.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_dashboard_mcq_interactive.png")

        await browser.close()
        print("Finished capturing dashboard screenshots.")

if __name__ == "__main__":
    asyncio.run(run())
