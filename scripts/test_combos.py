from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 900})
    page.goto("https://markmint.vercel.app/mintai", wait_until="networkidle")
    time.sleep(1.5)
    
    # Let's inspect buttons
    buttons = page.query_selector_all("button")
    combos = [b for b in buttons if b.get_attribute("role") == "combobox"]
    print("Found combos:", len(combos))
    for i, c in enumerate(combos):
        print(f"Combo {i}: {c.inner_text().strip()}")

    # Click the Course/Subject combobox (index 2)
    if len(combos) >= 3:
        combos[2].click()
        time.sleep(0.8)
        # Check all visible items in the dropdown
        items = page.query_selector_all("div, button, li")
        matching = [it for it in items if "Calculus" in (it.inner_text() or "")]
        print("Found matching Calculus items:", len(matching))
        for m in matching:
            txt = (m.inner_text() or "").strip()
            if "Calculus" in txt and ("21MAB101T" in txt or "Linear Algebra" in txt):
                try:
                    m.click()
                    print("Successfully clicked Calculus option:", txt[:50])
                    break
                except Exception as e:
                    pass

        time.sleep(1)
        # Now click Generate Forecast
        gen_btn = page.query_selector('button:has-text("Generate Forecast")')
        if gen_btn and not gen_btn.is_disabled():
            gen_btn.click()
            print("Clicked Generate Forecast!")
            time.sleep(4)
            page.screenshot(path="scratch/screenshots/mintai_calculus_forecast.png")
            print("Captured scratch/screenshots/mintai_calculus_forecast.png")


    browser.close()
