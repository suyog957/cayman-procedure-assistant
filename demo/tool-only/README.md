# Branch Assist — silent tool demo

This is the primary tool-only cut: **4 minutes 41 seconds**, 1080p, 25 actual application scenes, seven navigation chapters, short on-screen tags and focused corner highlights. The MP4 contains **no audio track**. There is no narration, music, narrated subtitle track, architecture slide, explanatory graphic or slide-deck segment.

Open [Watch_Tool_Demo.html](Watch_Tool_Demo.html) or play [Branch_Assist_Tool_Demo.mp4](Branch_Assist_Tool_Demo.mp4) directly. For browser chapter seeking, run `python scripts/serve_demo_video.py` from the project root and visit **http://127.0.0.1:8502/tool-only/Watch_Tool_Demo.html**.

The workflow covers asking a question; citations and original sources; provenance and ranking signals; statement checks and real activity; trace download; follow-ups and topic switching; procedure search and scope; notary and savings-bond scenarios; a genuinely withheld draft; review feedback and conversation export; reset and unsupported requests; evaluation and report downloads.

The cut uses the original raw browser recordings, with fresh recordings for currency display, feedback and report downloads. It is not a muted copy of the earlier narrated presentation. Processing pauses can be shortened, while genuine final UI frames are held for reading. Highlights annotate real controls and outputs without changing them. The Wells Fargo wordmark remains part of the clearly labelled interview-prototype interface over the supplied Cayman Bank snapshot.

`SCENE_GUIDE.md` lists each action and its tag. `production_manifest.json` records provenance and the media hash. `qa_report.json` verifies absence of audio, full decoding, actual UI coverage, continuous scene timing, browser playback and seeking. `Contact_Sheet.jpg` and `Player_Preview.png` support visual review. Automatic checks and regression diagnostics remain fallible; the recording adds no independent validation of the procedural guidance.

Rebuild using the prepared local workspace:

```powershell
python scripts/capture_demo_video.py
python scripts/capture_demo_video.py --signals-only
python scripts/capture_tool_demo_details.py
python scripts/capture_tool_demo_details.py --reports-only
python scripts/render_tool_demo.py
python scripts/serve_demo_video.py
```

Then, in another terminal, run `python scripts/verify_tool_demo.py`. Raw captures and intermediate encodes remain in ignored `artifacts/video_build/`. Rebuilding requires the app running on localhost, the prepared local models, installed Chrome, Playwright's recording helper, FFmpeg/ffprobe and Windows fonts. Synthetic narration packages are not required for this cut. Future model outputs may differ; review fresh outcomes and update tags if needed.
