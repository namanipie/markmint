import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # 1. Desktop Test: Question Bank Archive & Printable Worksheet
        # -------------------------------------------------------------
        d_context = await browser.new_context(viewport={"width": 1440, "height": 1100})
        page = await d_context.new_page()

        print("Navigating to http://localhost:3000/question-bank?view=cycle-tests...")
        await page.goto("http://localhost:3000/question-bank?view=cycle-tests", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3500)

        # Remove any cookie banners or overlays
        await page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => {
                if (!el.textContent.includes('Printable Practice Worksheet Preview')) {
                    el.remove();
                }
            });
        }""")

        # Select subject: Calculus And Linear Algebra
        print("Selecting subject Calculus...")
        sub_select = page.locator("select").first
        if await sub_select.count() > 0:
            await sub_select.select_option(value="Calculus And Linear Algebra")
            await page.wait_for_timeout(2000)

        # Test Expand All Faculty Solutions
        print("Testing Expand All Faculty Solutions...")
        expand_btn = page.locator("button:has-text('Expand All Faculty Solutions')").first
        if await expand_btn.count() > 0:
            await expand_btn.click(force=True)
            await page.wait_for_timeout(1000)

        print("Capturing question_bank_desktop_expanded_solutions.png...")
        await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_desktop_expanded_solutions.png")

        # Click Printable Worksheet button
        print("Opening Printable Practice Worksheet Modal...")
        print_btn = page.locator("button:has-text('Printable Worksheet')").first
        if await print_btn.count() > 0:
            await print_btn.click(force=True)
            await page.wait_for_timeout(1500)

            # Check Include Solutions
            inc_cb = page.locator("input[type='checkbox']").first
            if await inc_cb.count() > 0:
                await inc_cb.check()
                await page.wait_for_timeout(1000)

            print("Capturing question_bank_printable_worksheet_preview.png...")
            await page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/question_bank_printable_worksheet_preview.png")

            # Close preview
            close_btn = page.locator("button:has-text('Close')").first
            if await close_btn.count() > 0:
                await close_btn.click(force=True)
                await page.wait_for_timeout(500)

        await d_context.close()

        # -------------------------------------------------------------
        # 2. Mobile Viewport Test (375x812 - iPhone)
        # -------------------------------------------------------------
        m_context = await browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True)
        m_page = await m_context.new_page()

        print("\nNavigating on mobile viewport to http://localhost:3000/question-bank...")
        await m_page.goto("http://localhost:3000/question-bank", wait_until="domcontentloaded", timeout=30000)
        await m_page.wait_for_timeout(3500)

        # Clear cookie overlays
        await m_page.evaluate("""() => {
            document.querySelectorAll('.fixed.inset-0').forEach(el => el.remove());
        }""")

        print("Capturing mobile_qb_taxonomy_view.png...")
        await m_page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_qb_taxonomy_view.png")

        # Click "Change Subject" accordion
        chg_btn = m_page.locator("button:has-text('Change Subject')").first
        if await chg_btn.count() > 0:
            print("Expanding mobile curriculum selector...")
            await chg_btn.click(force=True)
            await m_page.wait_for_timeout(1000)
            print("Capturing mobile_qb_selector_expanded.png...")
            await m_page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_qb_selector_expanded.png")

        # Now switch to Cycle Test Archive tab
        ct_tab = m_page.locator("button:has-text('Cycle Test Archive')").first
        if await ct_tab.count() > 0:
            print("Switching to Cycle Test Archive tab on mobile...")
            await ct_tab.scroll_into_view_if_needed()
            await ct_tab.click(force=True)
            await m_page.wait_for_timeout(2500)

            print("Capturing mobile_qb_archive_view.png...")
            await m_page.screenshot(path="C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/mobile_qb_archive_view.png")

        await m_context.close()
        await browser.close()
        print("\nAll verification screenshots completed successfully!")

if __name__ == "__main__":
    asyncio.run(run())
