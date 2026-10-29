import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1400})
        page = await context.new_page()

        # 1. Direct course page: Calculus and Linear Algebra
        print("Visiting /courses/calculus-and-linear-algebra...")
        await page.goto("http://localhost:3000/courses/calculus-and-linear-algebra", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        # Clear overlay / cookie banners
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
            document.querySelectorAll('button').forEach(b => {
                if (b.textContent && b.textContent.includes('Accept')) b.click();
            });
        }""")

        # Look for cycle test drawer toggle
        drawer = page.locator("text=Authentic CT1 Questions").or_(page.locator("text=Cycle Test")).or_(page.locator("text=Questions & Testing System")).first
        if await drawer.count() > 0:
            await drawer.scroll_into_view_if_needed()
            await drawer.click(force=True)
            await page.wait_for_timeout(2000)

        # Reveal faculty answer key
        sol_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await sol_btn.count() > 0:
            await sol_btn.scroll_into_view_if_needed()
            await sol_btn.click(force=True)
            await page.wait_for_timeout(1000)

        print("Capturing calculus_course_page_normal_questions.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_course_page_normal_questions.png")

        # Now click Interactive MCQ Test
        mcq_tab = page.locator("button:has-text('Interactive MCQ Test')").first
        if await mcq_tab.count() > 0:
            await mcq_tab.scroll_into_view_if_needed()
            await mcq_tab.click(force=True)
            await page.wait_for_timeout(2000)

            # Click option B or A on the first MCQ
            opt_btn = page.locator("button:has-text('B')").first
            if await opt_btn.count() > 0:
                await opt_btn.click(force=True)
                await page.wait_for_timeout(1000)

            print("Capturing calculus_course_page_interactive_mcq.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/calculus_course_page_interactive_mcq.png")

        # 2. Question Bank Cycle Test Archive
        print("Visiting /question-bank...")
        await page.goto("http://localhost:3000/question-bank", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        # Click on Cycle Test Archive tab
        ct_tab = page.locator("button:has-text('Cycle Test Archive')").first
        if await ct_tab.count() > 0:
            await ct_tab.click(force=True)
            await page.wait_for_timeout(2500)

        # Select Calculus in subject dropdown or filter
        subj_btn = page.locator("button:has-text('Calculus')").first
        if await subj_btn.count() > 0:
            await subj_btn.click(force=True)
            await page.wait_for_timeout(2000)

        # Reveal solution on first question
        sol_btn2 = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await sol_btn2.count() > 0:
            await sol_btn2.scroll_into_view_if_needed()
            await sol_btn2.click(force=True)
            await page.wait_for_timeout(1000)

        print("Capturing question_bank_calculus_descriptive_math.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_calculus_descriptive_math.png")

        # Switch to MCQ section in Question Bank
        mcq_sec = page.locator("button:has-text('MCQ Section')").first
        if await mcq_sec.count() > 0:
            await mcq_sec.click(force=True)
            await page.wait_for_timeout(2000)
            print("Capturing question_bank_calculus_mcq_interactive.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_calculus_mcq_interactive.png")

        await browser.close()
        print("All visual evidence screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(run())
