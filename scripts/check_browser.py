"""Browser integration check against the locally running Streamlit app.

Uses installed Chrome; does not download a browser or send data externally.
"""
from pathlib import Path
import argparse
import json
import re
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--chat", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
screens = root / "artifacts/screenshots"
screens.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=60000)
    page.get_by_text("A clearer path through procedures.", exact=True).wait_for(timeout=60000)
    page.screenshot(path=str(screens / "welcome.png"), full_page=True)
    results = {"welcome_loaded": True, "client_errors": errors}
    if args.chat:
        page.get_by_role("button", name="Coin machine limits", exact=True).click()
        page.get_by_text("Generated answer · inspect citations", exact=True).wait_for(timeout=180000)
        page.locator('[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p').filter(has_text="5,250").last.wait_for(state="visible",timeout=180000)
        page.wait_for_timeout(500)
        answer1 = page.locator('[data-testid="stChatMessage"]').last.inner_text()
        assert "5,250" in answer1
        page.locator('[data-testid="stChatInputTextArea"]').fill("And is monthly testing done in single or dual control?")
        page.locator('[data-testid="stChatInputTextArea"]').press("Enter")
        page.get_by_text("Generated answer · inspect citations", exact=True).nth(1).wait_for(timeout=180000)
        page.locator('[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p').filter(has_text=re.compile(r"single control",re.I)).last.wait_for(state="visible",timeout=180000)
        page.wait_for_timeout(500)
        answer2 = page.locator('[data-testid="stChatMessage"]').last.inner_text()
        assert "single control" in answer2.lower()
        page.get_by_text(re.compile(r"^View \d+ source passages$")).last.click()
        page.get_by_text(re.compile(r"^Source SHA256:")).last.wait_for(state="visible",timeout=15000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(screens / "conversation.png"), full_page=True)
        results.update({"first_answer": answer1, "followup_answer": answer2, "followup_pass": True})
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export this conversation", exact=True).click()
        download_info.value.save_as(str(root / "artifacts/browser_conversation.json"))
        exported = json.loads((root / "artifacts/browser_conversation.json").read_text(encoding="utf-8"))
        assert len(exported) == 4
        results["export_includes_latest_turn"] = True
        other = browser.new_page()
        other.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=60000)
        other.locator('[data-testid="stChatInputTextArea"]').fill("Can they do that?")
        other.locator('[data-testid="stChatInputTextArea"]').press("Enter")
        other.get_by_text("More context needed", exact=True).wait_for(timeout=30000)
        results["second_session_isolated"] = True
        other.close()
        page.get_by_role("button", name="Start a new conversation", exact=True).click()
        page.get_by_role("button", name="Coin machine limits", exact=True).wait_for(timeout=15000)
        assert page.locator('[data-testid="stChatMessage"]').count() == 0
        results["reset_pass"] = True
    browser.close()
(root / "artifacts/browser_check.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2), flush=True)
