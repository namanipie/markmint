import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1300})
        page = await context.new_page()

        print("Navigating to http://localhost:3000/dashboard?course=1...")
        await page.goto("http://localhost:3000/dashboard?course=1", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        # Clear overlay if any
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Click CT1 preset button
        print("Clicking CT1 preset button...")
        ct1_preset = page.locator("button:has-text('CT1 (Units 1 & 2)')").first
        if await ct1_preset.count() > 0:
            await ct1_preset.click(force=True)
            await page.wait_for_timeout(2500)

        # Clear overlay
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Look for cycle test drawer header
        drawer_header = page.locator("text=Authentic CT1 Questions").or_(page.locator("text=Questions & Testing System")).first
        if await drawer_header.count() > 0:
            print("Found drawer header! Scrolling into view...")
            await drawer_header.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)

        # Reveal faculty key on first question
        rev_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await rev_btn.count() > 0:
            await rev_btn.scroll_into_view_if_needed()
            await rev_btn.click(force=True)
            await page.wait_for_timeout(1000)

        print("Capturing calculus_ct1_normal_questions_drawer.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_ct1_normal_questions_drawer.png")

        # Now click Interactive MCQ Test button
        mcq_btn = page.locator("button:has-text('Interactive MCQ Test')").first
        if await mcq_btn.count() > 0:
            print("Switching to Interactive MCQ Test tab...")
            await mcq_btn.scroll_into_view_if_needed()
            await mcq_btn.click(force=True)
            await page.wait_for_timeout(2000)

            # Click option B or A on the first MCQ
            opt_btn = page.locator("button:has-text('A')").or_(page.locator("button:has-text('(A)')")).first
            if await opt_btn.count() > 0:
                await opt_btn.click(force=True)
                await page.wait_for_timeout(1000)

            print("Capturing calculus_ct1_mcq_interactive_drawer.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_ct1_mcq_interactive_drawer.png")

        await browser.close()
        print("Success! Screenshots captured.")

if __name__ == "__main__":
    asyncio.run(run())
