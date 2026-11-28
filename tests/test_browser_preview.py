import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.mark.browser
def test_preview_dialog_fits_desktop_and_mobile_and_zoom_stays_in_dialog(streamlit_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto(streamlit_url, wait_until="domcontentloaded")

        preview_button = page.get_by_role("button", name="Preview PDF")
        expect(preview_button).to_be_visible(timeout=30000)
        preview_button.click()
        dialog = page.get_by_test_id("stDialog")
        expect(dialog).to_be_visible(timeout=30000)
        preview_image = dialog.locator('img[alt="PDF page preview"]')
        expect(preview_image).to_be_visible()
        zoom_in_button = dialog.get_by_role("button").nth(3)
        expect(zoom_in_button).to_be_visible()

        dialog_box = dialog.bounding_box()
        viewport = page.evaluate("({width: innerWidth, height: innerHeight})")
        assert dialog_box["x"] >= 0
        assert dialog_box["y"] >= 0
        assert dialog_box["x"] + dialog_box["width"] <= viewport["width"] + 1
        assert dialog_box["y"] + dialog_box["height"] <= viewport["height"] + 1

        zoom_in_button.click()
        expect(dialog.get_by_text("125%", exact=True)).to_be_visible()

        page.set_viewport_size({"width": 360, "height": 640})
        expect(dialog).to_be_visible()
        expect(preview_image).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        dialog_box = dialog.bounding_box()
        viewport = page.evaluate("({width: innerWidth, height: innerHeight})")
        assert dialog_box["x"] >= 0
        assert dialog_box["x"] + dialog_box["width"] <= viewport["width"] + 1
        assert dialog_box["y"] + dialog_box["height"] <= viewport["height"] + 1
        browser.close()
