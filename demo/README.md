# Branch Assist — demo videos

The primary recording is the **[silent, tool-only demo](tool-only/Watch_Tool_Demo.html)**: 9 minutes 25 seconds, 1440p, 25 genuine application scenes with large plain-language descriptions at the bottom, focused zooms and longer reading holds. Fresh double-density lossless capture improves the source detail. The MP4 has no audio stream, narration, music or slide segments. Open [the silent MP4](tool-only/Branch_Assist_Tool_Demo.mp4) directly or use **http://127.0.0.1:8502/tool-only/Watch_Tool_Demo.html** with the local player server. Its [README](tool-only/README.md), [scene guide](tool-only/SCENE_GUIDE.md) and QA report describe the workflow and checks.

## Earlier narrated demonstration

Open **`Watch_Demo.html`** for chapter/scene navigation, or play **`Branch_Assist_Full_Demo.mp4`** directly in a browser or media player. The MP4 contains synthetic narration and burned-in captions, so it works as a standalone file. It also contains chapter metadata and an optional English subtitle track. Captions are already visible; enabling a second subtitle track may duplicate them.

For browser playback with reliable chapter seeking, run `python scripts/serve_demo_video.py` from the project root and visit **http://127.0.0.1:8502/Watch_Demo.html**. The local player server supports HTTP byte ranges. The MP4 plays independently of this server.

The recording is designed for the assignment's 15-minute technical walkthrough slot. It explains the workflow without requiring live voice-over, while keeping the candidate responsible for the separate slide presentation, discussion and design defense. It is a recorded interview prototype, not a Wells Fargo product or independently validated operational guidance.

| File | Purpose |
|---|---|
| `Branch_Assist_Full_Demo.mp4` | Complete 1080p narrated, labelled, captioned walkthrough |
| `Watch_Demo.html` | Local playback with chapter and individual-scene navigation |
| `Branch_Assist_Cover.png` | Thumbnail / cover |
| `Branch_Assist_Demo.srt`, `.vtt` | Separate caption files |
| `Branch_Assist_Transcript.md`, `.txt` | Full narration script with scene timestamps |
| `chapters.txt` | Copyable chapter timestamps |
| `FEATURE_COVERAGE.md` | Scene-by-scene feature and evidence index |
| `timeline.json` | Machine-readable scene boundaries |
| `capture_evidence.json` | Genuine captured response outcomes and feature assertions |
| `production_manifest.json` | Editing/narration provenance, model hashes and final video hash |
| `qa_report.json`, `player_check.json`, `Contact_Sheet.jpg` | Media/playback verification and a visual review index |
| `storyboard.json` | Editable narration, labels and scene plan |

The story covers purpose, RAG architecture, ingestion, hybrid retrieval, actual local generation, citation navigation, provenance, ranking signals, original documents, claim checks, activity and trace export, follow-ups, topic switching, the procedure library and scope, notary and savings-bond scenarios, bounded correction, withholding, feedback/export, reset, unsupported/unknown requests, a narrow instruction guard, mobile/session behavior, evaluation, human review and the next validation gates.

Processing pauses may be shortened and final frames held for explanation. Actual model runtimes remain visible. Saved evaluation examples B02 and N03 are labelled separately from fresh interactions. The captured savings-bond exception follow-up genuinely produced a source-only outcome, which the narration explains. The video contains no implementation source code.

Use the original procedures to check conditions. The recorded regression metrics and automatic screens are not independent accuracy estimates. No video, presentation or source material is automatically submitted or posted externally.

Build details and primary narration-tool attribution: [VIDEO_PRODUCTION.md](../docs/VIDEO_PRODUCTION.md).
