import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # iPhone 13 / 14 / 15 dimensions: 390x844
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()

        # 1. Dashboard mobile view
        print("Auditing mobile /dashboard?course=1...")
        await page.goto("http://localhost:3000/dashboard?course=1", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_dashboard_top.png")

        # Click CT2 preset
        ct2_btn = page.locator("button:has-text('CT2')").first
        if await ct2_btn.count() > 0:
            await ct2_btn.scroll_into_view_if_needed()
            await ct2_btn.click(force=True)
            await page.wait_for_timeout(2000)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Scroll to drawer
        drawer = page.locator("text=Authentic CT2 Questions").or_(page.locator("text=Questions & Testing System")).first
        if await drawer.count() > 0:
            await drawer.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_drawer_normal_questions.png")

            # Switch to Interactive MCQ Test
            mcq_tab = page.locator("button:has-text('Interactive MCQ Test')").first
            if await mcq_tab.count() > 0:
                await mcq_tab.scroll_into_view_if_needed()
                await mcq_tab.click(force=True)
                await page.wait_for_timeout(1500)
                await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_drawer_mcq_practice.png")

                # Switch to Timed Quiz Mode
                quiz_mode_btn = page.locator("button:has-text('Timed Quiz Mode')").first
                if await quiz_mode_btn.count() > 0:
                    await quiz_mode_btn.scroll_into_view_if_needed()
                    await quiz_mode_btn.click(force=True)
                    await page.wait_for_timeout(1500)
                    await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_drawer_timed_quiz.png")

        # 2. Question Bank mobile view
        print("Auditing mobile /question-bank...")
        await page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_question_bank_taxonomy.png")

        # Switch to Cycle Test Archive
        ct_tab = page.locator("button:has-text('Cycle Test Archive')").first
        if await ct_tab.count() > 0:
            await ct_tab.click(force=True)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_question_bank_archive.png")

        await browser.close()
        print("Mobile audit screenshots completed.")

if __name__ == "__main__":
    asyncio.run(run())
