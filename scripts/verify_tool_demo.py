"""Verify the silent cut, genuine capture mapping, and real browser playback."""

from hashlib import sha256
from pathlib import Path
import json
import re
import struct
import subprocess
import urllib.request

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo/tool-only"
BUILD = ROOT / "artifacts/video_build/tool-only/hd"
URL = "http://127.0.0.1:8502/tool-only/"


def main():
    manifest = json.loads((OUT / "production_manifest.json").read_text(encoding="utf-8"))
    timeline = json.loads((OUT / "timeline.json").read_text(encoding="utf-8"))
    story = json.loads((OUT / "storyboard.json").read_text(encoding="utf-8"))
    capture = json.loads((BUILD / "capture_manifest.json").read_text(encoding="utf-8"))
    video = OUT / "Branch_Assist_Tool_Demo.mp4"
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-show_chapters",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    assert not any(s["codec_type"] == "audio" for s in probe["streams"]), (
        "The silent cut must have no audio stream."
    )
    assert not any(s["codec_type"] == "subtitle" for s in probe["streams"]), (
        "Narration captions must not enter this cut."
    )
    visual = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert visual["codec_name"] == "h264" and (visual["width"], visual["height"]) == (2560, 1440)
    duration = float(probe["format"]["duration"])
    assert abs(duration - sum(s["duration"] for s in timeline)) < 0.1
    assert len(timeline) == 25 and len(probe["chapters"]) == 7
    assert all(s["kind"] == "actual_app_capture" for s in timeline)
    assert (
        manifest["browser_only"]
        and not manifest["presentation_slides"]
        and not manifest["narration"]
    )
    assert manifest["sha256"] == sha256(video.read_bytes()).hexdigest()
    assert capture["status"] == "passed" and capture["currency_display_verified"]
    assert capture["complete_export_verified"] and capture["silent_feedback"] == "Needs review"
    assert not capture["client_errors"]
    assert capture["responses"]["bond_exception"]["status"] == "evidence_only"
    assert capture["responses"]["bond_exception"]["metrics"]["repair_attempted"]
    for left, right in zip(timeline, timeline[1:]):
        assert abs(left["end"] - right["start"]) < 0.0001
    assert timeline[-1]["end"] == manifest["duration_seconds"]
    assert manifest["interaction_speed"] == 1 and manifest["capture_format"] == "lossless PNG"
    assert manifest["description_position"] == "dedicated bottom panel outside the UI"
    assert manifest["description_font_pixels"] == 40 and manifest["description_max_lines"] == 2
    assert (
        manifest["capture_pixel_dimensions"] == [3072, 1728] and capture["device_scale_factor"] == 2
    )
    ax, ay, aw, ah = manifest["app_frame_pixels"]
    cx, cy, cw, ch = manifest["description_panel_pixels"]
    assert cy >= ay + ah + 10 and cy + ch <= 1440 - 80, (
        "Descriptions must not cover UI or occupy the control-safe area."
    )
    for row in timeline:
        assert row["reading_seconds"] + 0.01 >= row["minimum_reading_seconds"]
        assert row["description_lines"] <= 2 and row["description_font_pixels"] == 40
        assert row["description_characters_per_second"] <= 12
    png_count = 0
    for segment in capture["segments"]:
        for path in [segment["screenshot"]] + [f["file"] for f in segment["frames"]]:
            with (ROOT / path).open("rb") as stream:
                head = stream.read(24)
            assert head[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", head[16:24]) == (
                3072,
                1728,
            )
            png_count += 1
    assert png_count >= capture["total_png_frames"]
    descriptions = (OUT / "Descriptions.srt").read_text(encoding="utf-8")
    assert len(re.findall(r" --> ", descriptions)) == 25
    print(
        "1440p, lossless double-density source, readable bottom descriptions and reading holds verified; decoding...",
        flush=True,
    )
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and not result.stderr, result.stderr
    with urllib.request.urlopen(
        urllib.request.Request(URL + video.name, headers={"Range": "bytes=0-1023"})
    ) as response:
        assert response.status == 206 and len(response.read()) == 1024
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True
        )
        page = browser.new_page(viewport={"width": 1536, "height": 1100})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL + "Watch_Tool_Demo.html", wait_until="networkidle", timeout=60000)
        player = page.locator("video")
        page.wait_for_function('document.querySelector("video").readyState>=2', timeout=30000)
        assert not player.evaluate("(v)=>v.muted"), (
            "Playback should be silent without relying on mute."
        )
        assert abs(player.evaluate("(v)=>v.duration") - duration) < 0.1
        assert not player.evaluate("(v)=>v.controls"), "Controls must be outside the picture."
        page.get_by_role("button", name="Play video", exact=True).click()
        page.wait_for_function('document.querySelector("video").currentTime>.25', timeout=30000)
        page.get_by_role("button", name="Pause video", exact=True).click()
        speed = page.get_by_role("combobox", name="Playback speed", exact=True)
        await_value = speed.input_value()
        assert await_value == "1"
        speed.select_option("0.75")
        assert player.evaluate("(v)=>v.playbackRate") == 0.75
        speed.select_option("1")
        assert player.evaluate("(v)=>v.playbackRate") == 1
        bounds = page.evaluate(
            """()=>({v:document.querySelector('video').getBoundingClientRect().bottom,c:document.querySelector('.controls').getBoundingClientRect().top})"""
        )
        assert bounds["c"] >= bounds["v"] - 1
        page.get_by_role("button", name="Full screen", exact=True).click()
        page.wait_for_function('document.fullscreenElement?.id === "film"', timeout=15000)
        fullscreen_bounds = page.evaluate(
            """()=>({v:document.querySelector('video').getBoundingClientRect().bottom,c:document.querySelector('.controls').getBoundingClientRect().top})"""
        )
        assert fullscreen_bounds["c"] >= fullscreen_bounds["v"] - 1
        page.evaluate("document.exitFullscreen()")
        expect(page.locator("#chapters button")).to_have_count(7)
        page.locator("#chapters button").nth(2).click()
        start = manifest["chapters"][2]["start"]
        page.wait_for_function(
            '(start)=>document.querySelector("video").currentTime>start+.25',
            arg=start,
            timeout=30000,
        )
        page.get_by_text("Jump to an individual step", exact=True).click()
        expect(page.locator("#scenes button")).to_have_count(25)
        index = next(i for i, row in enumerate(timeline) if row["id"] == "bond_limit")
        page.locator("#scenes button").nth(index).click()
        start = timeline[index]["start"]
        page.wait_for_function(
            '(start)=>document.querySelector("video").currentTime>start+.25',
            arg=start,
            timeout=30000,
        )
        seek = (
            timeline[index]["start"]
            + timeline[index]["motion_seconds"]
            + timeline[index]["camera_transition_seconds"]
            + 3
        )
        player.evaluate("(v,t)=>{v.pause();v.currentTime=t}", seek)
        page.wait_for_function('document.querySelector("video").seeking === false', timeout=15000)
        page.wait_for_timeout(500)
        page.get_by_text("Jump to an individual step", exact=True).click()
        player.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "Player_Preview.png"), full_page=True)
        assert player.evaluate("(v)=>v.error") is None and not errors
        browser.close()
    print(
        "Playback, external controls, speed selection and seeking passed; extracting visual review frames...",
        flush=True,
    )
    qc = BUILD / "qc"
    qc.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (2400, 5 * 292), "#f9f7f6")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 15)
    for index, scene in enumerate(timeline):
        image_path = qc / (scene["id"] + ".png")
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(scene["end"] - 1.2),
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(image_path),
            ],
            capture_output=True,
            check=True,
        )
        image = Image.open(image_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        x = (index % 5) * 480
        y = (index // 5) * 292
        sheet.paste(image, (x, y))
        draw.text((x + 5, y + 272), f"{index + 1:02d} {scene['id']}", fill="#3b3331", font=font)
    sheet.save(OUT / "Contact_Sheet.jpg", quality=92)
    quality = []
    for name in ["coin_evidence", "claim_checks", "bond_limit"]:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(qc / (name + ".png")),
                "-i",
                str(BUILD / "composition" / name / "reference.png"),
                "-filter_complex_threads",
                "2",
                "-lavfi",
                "ssim",
                "-frames:v",
                "1",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        values = re.findall(r"All:([\d.]+)", result.stderr)
        assert values, result.stderr
        value = float(values[-1])
        assert value >= 0.98, (name, value)
        quality.append({"scene": name, "reference_ssim": value})
    evidence = {k: v for k, v in capture.items() if k not in {"segments", "raw_video", "downloads"}}
    evidence["scenes"] = [{"id": s["capture"], "actual_capture": True} for s in story["scenes"]]
    (OUT / "capture_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report = {
        "status": "passed",
        "duration_seconds": duration,
        "resolution": [2560, 1440],
        "scene_count": 25,
        "chapter_count": 7,
        "audio_stream_count": 0,
        "narration_caption_stream_count": 0,
        "relies_on_player_mute": False,
        "all_scenes_actual_ui": True,
        "presentation_slides": False,
        "full_decode_passed": True,
        "continuous_timeline": True,
        "currency_display_verified": True,
        "feedback_and_export_verified": True,
        "capture_pixels": [3072, 1728],
        "lossless_png_files_verified": png_count,
        "normal_speed_interactions": True,
        "minimum_reading_hold_seconds": manifest["min_reading_hold_seconds"],
        "large_bottom_descriptions": True,
        "description_font_pixels": 40,
        "max_description_lines": 2,
        "descriptions_clear_of_ui": True,
        "external_controls_clear_of_picture": True,
        "fullscreen_controls_clear_of_picture": True,
        "speed_control_passed": True,
        "visual_reference_checks": quality,
        "browser_playback_passed": True,
        "chapter_and_step_seeking_passed": True,
        "http_byte_ranges_passed": True,
        "client_errors": errors,
        "sha256": manifest["sha256"],
        "url": URL + "Watch_Tool_Demo.html",
    }
    (OUT / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
