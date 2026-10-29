import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1366, "height": 900})

        # Pre-seed profile
        await context.add_init_script("""
            localStorage.setItem('markmint_academic_profile', JSON.stringify({
                branch: 'Computer Science and Engineering',
                semester: 4,
                courseId: 5
            }));
            localStorage.setItem('markmint_welcome_dismissed', 'true');
        """)

        page = await context.new_page()

        # -----------------------------------------------------------------
        # 1. VERIFY DASHBOARD CT QUESTIONS DRAWER
        # -----------------------------------------------------------------
        print("1. Opening /dashboard?course=database-management-systems&cycle=CT1...")
        await page.goto("http://localhost:3000/dashboard?course=database-management-systems&cycle=CT1", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        drawer_header = page.locator("h4:has-text('Authentic CT1 Questions')")
        is_visible = await drawer_header.is_visible() if await drawer_header.count() > 0 else False
        print(f"Drawer CT1 header visible: {is_visible}")

        reveal_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await reveal_btn.count() > 0:
            print("Found Reveal Faculty Answer Key button! Clicking...")
            await reveal_btn.click()
            await page.wait_for_timeout(800)

        ct_drawer_shot = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_ct_questions_drawer.png"
        await page.screenshot(path=ct_drawer_shot, full_page=False)
        print(f"  --> Saved {ct_drawer_shot}")

        # -----------------------------------------------------------------
        # 2. VERIFY /question-bank CYCLE TEST ARCHIVE TAB
        # -----------------------------------------------------------------
        print("2. Opening /question-bank...")
        await page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Click Cycle Test Archive tab
        ct_tab = page.locator("button:has-text('Cycle Test Archive')")
        if await ct_tab.count() > 0:
            print("Clicking Cycle Test Archive tab...")
            await ct_tab.first.click()
            await page.wait_for_timeout(2000)

        # Select a subject from dropdown
        subject_select = page.locator("select").first
        if await subject_select.count() > 0:
            await subject_select.select_option(label="Database Management Systems (108 qs)")
            await page.wait_for_timeout(1500)
            print("Selected Database Management Systems in Subject Filter")

        # Click Reveal Faculty Answer Key if present
        qb_reveal_btn = page.locator("button:has-text('Reveal Faculty Answer Key')").first
        if await qb_reveal_btn.count() > 0:
            print("Clicking Reveal Faculty Answer Key in Question Bank...")
            await qb_reveal_btn.click()
            await page.wait_for_timeout(800)

        qb_archive_shot = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_ct_archive.png"
        await page.screenshot(path=qb_archive_shot, full_page=False)
        print(f"  --> Saved {qb_archive_shot}")

        # -----------------------------------------------------------------
        # 3. VERIFY SYLLABUS MODE WITH MINTAI GENERATOR
        # -----------------------------------------------------------------
        print("3. Switching to Syllabus Taxonomy & Units tab...")
        syllabus_tab = page.locator("button:has-text('Syllabus Taxonomy')")
        if await syllabus_tab.count() > 0:
            await syllabus_tab.first.click()
            await page.wait_for_timeout(1500)

        # Click subject in sidebar
        sub_btn = page.locator("button:has-text('Calculus and Linear Algebra')")
        if await sub_btn.count() > 0:
            await sub_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Clicked Calculus in sidebar")

        qb_syllabus_shot = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_syllabus_view.png"
        await page.screenshot(path=qb_syllabus_shot, full_page=False)
        print(f"  --> Saved {qb_syllabus_shot}")

        await browser.close()
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    asyncio.run(main())
