# Branch Assist — silent tool demo

This is the primary readable tool-only cut: **9 minutes 25 seconds**, 1440p, 25 actual application scenes and seven navigation chapters. Large, high-contrast bottom descriptions use at most two lines; eased focus zooms and roughly 10–20 second reading holds make the sources easier to inspect. The MP4 contains **no audio track**. There is no narration, music, architecture slide, explanatory graphic or slide-deck segment.

Open [Watch_Tool_Demo.html](Watch_Tool_Demo.html) or play [Branch_Assist_Tool_Demo.mp4](Branch_Assist_Tool_Demo.mp4) directly. For browser chapter seeking, run `python scripts/serve_demo_video.py` from the project root and visit **http://127.0.0.1:8502/tool-only/Watch_Tool_Demo.html**.

The workflow covers asking a question; citations and original sources; provenance and ranking signals; statement checks and real activity; trace download; follow-ups and topic switching; procedure search and scope; notary and savings-bond scenarios; a genuinely withheld draft; review feedback and conversation export; reset and unsupported requests; evaluation and report downloads.

The complete workflow was freshly captured as lossless **3072×1728 PNGs at double browser pixel density**, then composed into a 2560×1440 video with high-quality H.264 CRF 15 encoding and Lanczos resampling. The edit does not enlarge the old compressed recording. Mouse and typing actions retain normal speed; idle processing waits and unchanged endings may be cut. A 1.2-second eased camera move leads into a reading hold. Highlights annotate real controls and outputs without changing them. The Wells Fargo wordmark remains part of the clearly labelled interview-prototype interface over the supplied Cayman Bank snapshot.

Descriptions occupy a dedicated panel below the UI. All 25 descriptions, step titles and tags use plain language to explain the action, its result and why it matters. Source matching is distinguished from answer checking without specialist scoring terminology; the limits of the checks remain clear. The local player's controls sit outside the picture even in fullscreen, so pausing does not cover the text. Playback speed can be set to 0.75×, 1× or 1.25×. `Descriptions.srt` and `Descriptions.vtt` provide the text separately; no duplicate subtitle stream is embedded in the MP4.

`SCENE_GUIDE.md` lists each action, description and reading hold. `production_manifest.json` records provenance and the media hash. `qa_report.json` checks absence of audio, lossless source dimensions, description size/placement, reading time, full decoding, browser playback, external controls and seeking. Representative frames are compared with their lossless reference using SSIM to check media fidelity. `Contact_Sheet.jpg` and `Player_Preview.png` support visual review. These are media checks, not independent validation of the procedural guidance.

Rebuild using the prepared local workspace:

```powershell
python scripts/capture_tool_demo_hd.py
python scripts/render_tool_demo.py
python scripts/serve_demo_video.py
```

Then, in another terminal, run `python scripts/verify_tool_demo.py`. Raw captures and intermediate encodes remain in ignored `artifacts/video_build/`. Rebuilding requires the app running on localhost, prepared local models, installed Chrome, Playwright, FFmpeg/ffprobe, Pillow and Windows fonts. Synthetic narration packages are not required. Future model outputs may differ; review fresh outcomes and update descriptions/highlights if needed.
