"""Real-browser checks for the branded workspace and its evidence records."""

from pathlib import Path
import argparse
import json
import re
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("--chat", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
screens = root / "artifacts/screenshots"
screens.mkdir(exist_ok=True)
(root / "artifacts/browser_check.json").write_text(
    json.dumps({"pipeline_version": "2.0", "run_status": "running"}), encoding="utf-8"
)


def answer_message(page, count, phrase=None):
    answers = page.locator('[data-testid="stChatMessage"]').filter(
        has=page.locator(".assistant-emblem")
    )
    answers.nth(count - 1).wait_for(state="visible", timeout=240000)
    if phrase:
        answers.nth(count - 1).get_by_text(re.compile(phrase, re.I)).first.wait_for(
            state="visible", timeout=30000
        )
    page.wait_for_timeout(700)
    assert not page.locator('[data-testid="stException"]').count()
    return answers.nth(count - 1)


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True
    )
    page = browser.new_page(viewport={"width": 1536, "height": 1060}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=60000)
    page.get_by_role("heading", name="Clear answers. Visible evidence.").wait_for(timeout=30000)
    assert page.get_by_alt_text("Wells Fargo", exact=True).is_visible()
    page.screenshot(path=str(screens / "welcome.png"), full_page=True)
    result = {"pipeline_version": "2.0", "welcome_loaded": True, "client_errors": errors}
    if args.chat:
        page.get_by_role("button", name="Explore coin limits →", exact=True).click()
        first = answer_message(page, 1, r"5,250")
        result["first_answer"] = first.inner_text()
        first_citation = first.get_by_role("button", name=re.compile(r"\[S\d+\] PR63")).first
        first_label = first_citation.inner_text()
        first_citation.click()
        expect(page.locator(".doc-badge")).to_have_text(first_label, timeout=15000)
        page.locator(".source-text").get_by_text(re.compile("5,250")).wait_for(timeout=15000)
        assert not page.locator(".integrity-line.failed").count()
        result["citation_selection_pass"] = True
        page.locator('[data-testid="stChatInputTextArea"]').fill(
            "And is monthly testing done in single or dual control?"
        )
        page.locator('[data-testid="stChatInputTextArea"]').press("Enter")
        second = answer_message(page, 2, r"single control")
        result.update(followup_answer=second.inner_text(), followup_pass=True)
        second_citation = second.get_by_role("button", name=re.compile(r"\[S\d+\] PR63")).first
        second_label = second_citation.inner_text()
        second_citation.click()
        expect(page.locator(".doc-badge")).to_have_text(second_label, timeout=15000)
        page.locator(".source-text").get_by_text(re.compile("single control", re.I)).wait_for(
            timeout=15000
        )
        page.wait_for_timeout(500)
        page.screenshot(path=str(screens / "conversation.png"), full_page=True)
        second.get_by_role("button", name="Inspect answer checks", exact=True).click()
        page.locator(".check-summary").wait_for(timeout=15000)
        page.locator(".claim-card").first.wait_for(state="attached", timeout=15000)
        page.locator(".claim-quote").first.wait_for(state="attached", timeout=15000)
        page.screenshot(path=str(screens / "checks.png"), full_page=True)
        result["claim_map_pass"] = True
        page.get_by_role("button", name="Helpful", exact=True).click()
        page.get_by_role("button", name="✓ Helpful", exact=True).wait_for(timeout=15000)
        page.get_by_text("Activity", exact=True).click()
        page.locator(".activity-step").first.wait_for(timeout=15000)
        page.locator(".activity-step").nth(6).wait_for(state="attached", timeout=15000)
        assert page.locator(".activity-step").count() >= 7
        page.screenshot(path=str(screens / "activity.png"), full_page=True)
        result["activity_record_pass"] = True
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export investigation", exact=True).click()
        download_info.value.save_as(str(root / "artifacts/browser_conversation.json"))
        exported = json.loads(
            (root / "artifacts/browser_conversation.json").read_text(encoding="utf-8")
        )
        assert len(exported["messages"]) == 4 and "Helpful" in exported["feedback"].values()
        assert all(
            m["result"]["activity"] and m["result"]["grounding"]["source_files_verified_at_request"]
            for m in exported["messages"]
            if m["role"] == "assistant"
        )
        result["export_includes_latest_turn"] = True
        page.get_by_role("button", name="Procedure library", exact=True).click()
        page.get_by_label("Find a procedure", exact=True).fill("notary")
        page.get_by_label("Find a procedure", exact=True).press("Enter")
        expect(page.locator(".catalog-title")).to_have_count(1, timeout=15000)
        page.screenshot(path=str(screens / "library.png"), full_page=True)
        page.get_by_role("button", name="Use in workspace", exact=True).click()
        page.locator(".scope-pill").get_by_text("PR1000", exact=False).wait_for(timeout=15000)
        result["library_search_and_scope_pass"] = True
        page.locator('[data-testid="stChatInputTextArea"]').fill(
            "What is the overnight storage limit for a coin-counting machine?"
        )
        page.locator('[data-testid="stChatInputTextArea"]').press("Enter")
        answer_message(page, 3, r"More context needed")
        assert page.locator(".source-text").count() == 0
        result["conflicting_scope_clarifies"] = True
        other = browser.new_page()
        other.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=60000)
        other.get_by_role("textbox", name="Ask a procedure question", exact=True).fill(
            "Can they do that?"
        )
        other.get_by_role("button", name="Investigate →", exact=True).click()
        answer_message(other, 1, r"More context needed")
        assert other.locator(".source-text").count() == 0
        result["second_session_isolated"] = True
        other.close()
        page.get_by_role("button", name=re.compile("New investigation")).click()
        page.get_by_role("heading", name="Clear answers. Visible evidence.").wait_for(timeout=15000)
        expect(page.locator('[data-testid="stChatMessage"]')).to_have_count(0, timeout=15000)
        result["reset_pass"] = True
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    mobile.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=60000)
    hero = mobile.get_by_role("heading", name="Clear answers. Visible evidence.")
    hero.wait_for(timeout=30000)
    assert mobile.locator(".wf-mobile-prototype").is_visible()
    assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    mobile.screenshot(path=str(screens / "mobile.png"), full_page=True)
    result["mobile_no_horizontal_overflow"] = True
    assert not page.locator('[data-testid="stException"]').count()
    assert not errors
    result["run_status"] = "passed"
    browser.close()
(root / "artifacts/browser_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2), flush=True)
