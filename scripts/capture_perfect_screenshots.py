import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 950})

        # Pre-seed profile and cookies
        await context.add_init_script("""
            localStorage.setItem('cookie_consent', 'true');
            localStorage.setItem('markmint_academic_profile', JSON.stringify({
                branch: 'Computer Science and Engineering',
                semester: 4,
                courseId: 5
            }));
            localStorage.setItem('markmint_welcome_dismissed', 'true');
        """)

        page = await context.new_page()

        # -------------------------------------------------------------
        # 1. DASHBOARD WITH CT1 PORTION AND REVEALED ANSWER KEY
        # -------------------------------------------------------------
        print("1. Loading Dashboard CT1 view...")
        await page.goto("http://localhost:3000/dashboard?course=database-management-systems&cycle=CT1", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        reveal_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await reveal_btn.count() > 0:
            await reveal_btn.click()
            await page.wait_for_timeout(800)

        # Scroll so selector and drawer are in view
        await page.evaluate("window.scrollTo(0, 180)")
        await page.wait_for_timeout(500)

        shot1 = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_ct_questions_drawer.png"
        await page.screenshot(path=shot1)
        print(f"Captured: {shot1}")

        # -------------------------------------------------------------
        # 2. QUESTION BANK CYCLE TEST ARCHIVE VIEW
        # -------------------------------------------------------------
        print("2. Loading Question Bank CT Archive view...")
        await page.goto("http://localhost:3000/question-bank?tab=cycle-tests", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        # Pick DBMS from dropdown
        select_el = page.locator("select").first
        if await select_el.count() > 0:
            await select_el.select_option(label="Database Management Systems (108 qs)")
            await page.wait_for_timeout(1500)

        # Reveal faculty key
        qb_reveal = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await qb_reveal.count() > 0:
            await qb_reveal.click()
            await page.wait_for_timeout(800)

        await page.evaluate("window.scrollTo(0, 80)")
        await page.wait_for_timeout(500)

        shot2 = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_ct_archive.png"
        await page.screenshot(path=shot2)
        print(f"Captured: {shot2}")

        # -------------------------------------------------------------
        # 3. QUESTION BANK SYLLABUS VIEW
        # -------------------------------------------------------------
        print("3. Loading Question Bank Syllabus view...")
        await page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        sub_btn = page.locator("button:has-text('Calculus and Linear Algebra')")
        if await sub_btn.count() > 0:
            await sub_btn.first.click()
            await page.wait_for_timeout(1500)

        shot3 = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_syllabus_view.png"
        await page.screenshot(path=shot3)
        print(f"Captured: {shot3}")

        await browser.close()
        print("ALL SCREENSHOTS CAPTURED CLEANLY!")

if __name__ == '__main__':
    asyncio.run(main())
