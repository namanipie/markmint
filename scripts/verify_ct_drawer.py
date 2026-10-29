import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 950})

        # Pre-seed profile with Data Structures and Algorithms (Semester 3)
        await context.add_init_script("""
            localStorage.setItem('markmint_academic_profile', JSON.stringify({
                branch: 'Computer Science and Engineering',
                semester: 3,
                courseId: 2
            }));
            localStorage.setItem('markmint_welcome_dismissed', 'true');
        """)

        page = await context.new_page()

        print("1. Opening /dashboard with Data Structures and Algorithms...")
        await page.goto("http://localhost:3000/dashboard", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Click DSA if on course picker
        dsa_card = page.locator("button:has-text('Data Structures')")
        if await dsa_card.count() > 0:
            await dsa_card.first.click()
            await page.wait_for_timeout(1000)
            print("  --> Clicked Data Structures course card")

        # Click CT2 preset
        ct2_btn = page.locator("button:has-text('CT2 (Units 3 & 4)')")
        if await ct2_btn.count() > 0:
            await ct2_btn.first.click()
            await page.wait_for_timeout(1500)
            print("  --> Clicked CT2 (Units 3 & 4)")

        # Verify drawer
        drawer_header = page.locator("button:has-text('Authentic')")
        print("Drawer header visible:", await drawer_header.is_visible() if await drawer_header.count() > 0 else False)

        # Click "Reveal Faculty Answer Key" if available
        reveal_btn = page.locator("button:has-text('Reveal Faculty Answer Key')")
        if await reveal_btn.count() > 0:
            await reveal_btn.first.click()
            await page.wait_for_timeout(600)
            print("  --> Clicked Reveal Faculty Answer Key")

        # Take screenshot
        screenshot_path = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/dashboard_ct_questions_drawer.png"
        await page.screenshot(path=screenshot_path)
        print(f"Captured screenshot to {screenshot_path}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
