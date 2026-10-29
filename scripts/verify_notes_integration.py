import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1366, "height": 950})

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
        # 1. VERIFY DASHBOARD PORTION NOTES DRAWER
        # -----------------------------------------------------------------
        print("1. Opening /dashboard?course=database-management-systems&cycle=CT1...")
        await page.goto("http://localhost:3000/dashboard?course=database-management-systems&cycle=CT1", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Look for the Portion Notes Drawer toggle
        toggle_btn = page.locator("button:has-text('View Slides & Notes')")
        if await toggle_btn.count() > 0:
            print("Found 'View Slides & Notes' toggle. Clicking to expand drawer...")
            await toggle_btn.first.click()
            await page.wait_for_timeout(1000)
        else:
            print("Toggle button not found or already open.")

        # Check if notes drawer is visible
        notes_header = page.locator("h4:has-text('Professor Slides & Notes')")
        print(f"Notes header visible: {await notes_header.is_visible() if await notes_header.count() > 0 else False}")

        dashboard_notes_shot = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_portion_notes_drawer.png"
        await page.screenshot(path=dashboard_notes_shot, full_page=False)
        print(f"  --> Saved {dashboard_notes_shot}")

        # -----------------------------------------------------------------
        # 2. VERIFY COURSE DETAIL RESOURCES (SLIDES & NOTES TAB & CT1 FILTER)
        # -----------------------------------------------------------------
        print("2. Opening /courses/database-management-systems#verified-papers...")
        await page.goto("http://localhost:3000/courses/database-management-systems#verified-papers", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Click the "Slides & Notes" tab
        notes_tab = page.locator("button:has-text('Slides & Notes')")
        if await notes_tab.count() > 0:
            print("Clicking 'Slides & Notes' tab...")
            await notes_tab.first.click()
            await page.wait_for_timeout(1000)

        # Click the "CT1 (Units 1 & 2)" filter button
        ct1_filter = page.locator("button:has-text('CT1 (Units 1 & 2)')")
        if await ct1_filter.count() > 0:
            print("Clicking 'CT1 (Units 1 & 2)' filter pill...")
            await ct1_filter.first.click()
            await page.wait_for_timeout(1000)

        course_notes_shot = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/course_notes_portion_filtered.png"
        await page.screenshot(path=course_notes_shot, full_page=False)
        print(f"  --> Saved {course_notes_shot}")

        await browser.close()
        print("Verification complete!")

if __name__ == "__main__":
    asyncio.run(main())
