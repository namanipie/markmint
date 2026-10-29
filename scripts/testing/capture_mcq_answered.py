import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1300})
        page = await context.new_page()

        await page.goto("http://localhost:3000/dashboard?course=1", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3500)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Click CT2
        ct2 = page.locator("button:has-text('CT2 (Units 3 & 4)')").first
        if await ct2.count() > 0:
            await ct2.click(force=True)
            await page.wait_for_timeout(2500)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Switch to Interactive MCQ Test
        mcq_tab = page.locator("button:has-text('Interactive MCQ Test')").first
        if await mcq_tab.count() > 0:
            await mcq_tab.scroll_into_view_if_needed()
            await mcq_tab.click(force=True)
            await page.wait_for_timeout(2000)

            # Click option A on Q9
            opt_a = page.locator("button:has-text('±2')").or_(page.locator("button:has-text('A')")).first
            if await opt_a.count() > 0:
                await opt_a.click(force=True)
                await page.wait_for_timeout(1000)

            # Reveal explanation
            exp_btn = page.locator("button:has-text('Explanation & Faculty Solution')").first
            if await exp_btn.count() > 0:
                await exp_btn.click(force=True)
                await page.wait_for_timeout(1000)

            print("Capturing calculus_ct2_mcq_answered_with_math_explanation.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_ct2_mcq_answered_with_math_explanation.png")

        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
