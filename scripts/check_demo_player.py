"""Verify actual MP4 playback and chapter/scene navigation in installed Chrome."""

from pathlib import Path
import json
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo"


def main():
    timeline = json.loads((OUT / "timeline.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "production_manifest.json").read_text(encoding="utf-8"))
    errors = []
    media_url = "http://127.0.0.1:8502/Branch_Assist_Full_Demo.mp4"
    with urllib.request.urlopen(
        urllib.request.Request(media_url, headers={"Range": "bytes=0-1023"})
    ) as response:
        assert response.status == 206 and len(response.read()) == 1024
    with urllib.request.urlopen(
        urllib.request.Request(media_url, headers={"Range": "bytes=-16"})
    ) as response:
        assert response.status == 206 and len(response.read()) == 16
    try:
        urllib.request.urlopen(
            urllib.request.Request(media_url, headers={"Range": "bytes=999999999-"})
        )
        raise AssertionError("Unsatisfiable range was not rejected")
    except urllib.error.HTTPError as error:
        assert error.code == 416
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True
        )
        page = browser.new_page(viewport={"width": 1536, "height": 1100})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://127.0.0.1:8502/Watch_Demo.html", wait_until="networkidle", timeout=60000)
        video = page.locator("video")
        video.evaluate("(v)=>{v.muted=true}")
        page.wait_for_function('document.querySelector("video").readyState >= 2', timeout=60000)
        duration = video.evaluate("(v)=>v.duration")
        assert abs(duration - manifest["duration_seconds"]) < 0.1
        expect(page.locator("#chapters button")).to_have_count(5)
        page.locator("#chapters button").nth(2).click()
        start = manifest["chapters"][2]["start"]
        page.wait_for_function(
            '(start)=>document.querySelector("video").currentTime > start+.25',
            arg=start,
            timeout=30000,
        )
        video.evaluate("(v)=>v.pause()")
        page.get_by_text("Jump to an individual scene", exact=True).click()
        expect(page.locator("#scenes button")).to_have_count(len(timeline))
        entry = next(i for i, s in enumerate(timeline) if s["id"] == "ranking_signals")
        page.locator("#scenes button").nth(entry).click()
        start = timeline[entry]["start"]
        page.wait_for_function(
            '(start)=>document.querySelector("video").currentTime > start+.25',
            arg=start,
            timeout=30000,
        )
        video.evaluate("(v)=>{v.pause();v.currentTime+=6}")
        page.wait_for_timeout(800)
        page.get_by_text("Jump to an individual scene", exact=True).click()
        video.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "Player_Preview.png"), full_page=True)
        assert video.evaluate("(v)=>v.error") is None
        assert not errors
        browser.close()
    result = {
        "status": "passed",
        "video_loads_and_decodes": True,
        "duration_seconds": duration,
        "chapter_buttons": 5,
        "scene_buttons": len(timeline),
        "chapter_seeking_passed": True,
        "scene_seeking_passed": True,
        "playback_time_advances": True,
        "client_errors": errors,
        "http_range_requests_passed": True,
        "url": "http://127.0.0.1:8502/Watch_Demo.html",
    }
    (OUT / "player_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
