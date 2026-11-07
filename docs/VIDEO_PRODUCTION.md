# Demo recordings: production and provenance

The primary format is the **readable silent, tool-only cut** at `demo/tool-only/Branch_Assist_Tool_Demo.mp4`: 9:25, 1440p, 25 scenes of the actual application. A large, high-contrast bottom description panel sits outside the UI; each description uses at most two lines of 40-pixel text. Focus zooms, subtle highlights, a restrained frame and deliberate reading holds make the evidence easier to inspect. It contains no audio stream, narration, music, architecture slide or presentation graphic. Open `demo/tool-only/Watch_Tool_Demo.html` for chapter/step navigation. The earlier narrated recording is preserved separately.

The readable edition freshly captures the complete workflow as lossless 3072×1728 PNGs from a 1536×864 browser viewport at double pixel density. It does not enlarge the old compressed recording. H.264 CRF 15 encoding, Lanczos resampling and clean focus crops preserve detail in the 2560×1440 output. Mouse and typing actions retain normal timing; only idle processing intervals and unchanged endings may be cut. A 1.2-second eased camera move leads into a deliberate final-state reading hold. Descriptions are burned into a separate bottom panel, with SRT/VTT sidecars provided. The local player's controls sit below the picture, including in fullscreen, and offer 0.75×, 1× and 1.25× speeds.

A display-only fix escapes dollar signs in Streamlit Markdown so currency cannot accidentally become inline math; exported model text and evidence are unchanged. Fresh browser assertions verify the displayed amount and absence of a math element. Review feedback is recorded as **Needs review** for the withheld response.

The silent build uses `capture_tool_demo_hd.py`, `render_tool_demo.py` (the entry point for `tool_demo_compositor.py`) and `verify_tool_demo.py`. Its README provides exact commands. Verification checks lossless source dimensions, reading holds, description size and location, full decoding, absence of audio, continuous timing, real Chrome playback, external controls, speed selection and chapter/step seeking. Representative decoded frames are compared with the lossless composition reference using SSIM; this measures media fidelity, not correctness of the guidance. Capture outcomes, provenance, the media hash, a contact sheet and the QA report accompany the cut. No TTS dependency is needed to build it.

## Earlier narrated recording

The finished recording is `demo/Branch_Assist_Full_Demo.mp4`. Open `demo/Watch_Demo.html` for a local chapter navigation page, or play the MP4 directly. The video includes voice-over, burned-in captions, an embedded English subtitle track, chapter metadata, a right-hand annotation rail, and explanatory graphics. Separate SRT/VTT captions, a transcript, a cover image, scene timing, feature coverage and media verification accompany it.

## What the audience sees

The story proceeds from purpose and architecture to asking a question, inspecting evidence/checks/activity, conversational follow-ups and scope, correction/withholding, feedback/export, safe outcomes, evaluation and delivery. The recording is designed to fit the assignment's 15-minute technical walkthrough slot, leaving room for a brief introduction or questions. It does not replace the six-slide, 20-minute presentation or the candidate's responsibility to answer questions.

The earlier local ontology LinkedIn demo supplied a visual reference: visible labels, focused interactions, and a concise narrative. This assignment uses a longer 16:9 format with synthetic narration and captions to carry the explanation.

## Authenticity and editorial boundaries

- `capture_demo_video.py` drives installed Chrome against the real local application with Playwright. Supported questions execute the actual local models. Assertions inspect actual responses, sources, downloads, statuses, exports and browser errors.
- The recording introduces a presentation cursor and adjusts real scroll positions for readable framing. It does not substitute generated text, fabricate checks, patch session state, mock network responses or replay saved answers inside the application.
- The edit shortens some processing pauses and holds final frames while narration explains them. Answer runtimes remain visible. It is labelled as a recorded walkthrough, not a claim of live real-time playback.
- Two explanatory cards use actual saved regression results, explicitly labelled **B02** and **N03**. B02 demonstrates recovered threshold wording. N03 demonstrates withholding and the possibility of unnecessary refusal. These cards are distinct from newly captured browser interactions.
- The captured Private Bank Experience follow-up also yields a real source-only outcome after correction. Narration explicitly describes that outcome; it is not presented as a generated-answer success.
- Explanatory architecture and proposed production-validation graphics are labelled separately. Proposed enterprise capabilities are not shown as implemented features.
- No implementation source code, terminal, editor, credentials, unrelated browser tabs, or customer identifiers appear in the video. The wordmark and visual language remain labelled as an interview prototype over the supplied Cayman Bank snapshot.

## Narration and accessibility

Narration is generated locally with [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), using the synthetic `af_heart` voice. The engine repository documents its MIT license and the model's Apache 2.0 license. The voice is not a clone or recording of the candidate. Narrator artifacts are separately downloaded, size/hash checked, and excluded from Git along with the application's model weights. The exact URLs and SHA256 values are retained in the production manifest.

The script is `demo/storyboard.json`. Narration is synthesized sentence by sentence; captions use those measured sentence intervals, with proportional phrase splits within sentences. A uniform pitch-preserving pacing adjustment brings the deliberately unhurried take to presentation speed. All caption and chapter times use the same adjustment and frame-aligned scene durations. Audio is normalized to a target of -16 LUFS and a -1.5 dB true-peak limit. There is no background music competing with the explanation.

The main MP4 has burned-in captions for portable playback and an optional embedded English text track. SRT and VTT files are provided separately. Avoid enabling an extra subtitle track when burned-in captions are already visible. Scene and chapter buttons in the local player support seeking. A complete text transcript is available for review without audio.

## Rebuild on the prepared Windows workspace

FFmpeg/ffprobe, installed Chrome, and Windows Segoe UI/Georgia fonts are used. The application server must be running on `http://127.0.0.1:8501`. Raw captures, generated WAV files, intermediate frames and encoding logs stay in ignored `artifacts/video_build/`.

```powershell
python -m pip install -e ".[dev,demo]"
python -m playwright install ffmpeg
python scripts/prepare_video_narrator.py
python scripts/capture_demo_video.py
python scripts/capture_demo_video.py --signals-only
python scripts/narrate_demo_video.py
python scripts/render_demo_video.py
python scripts/verify_demo_video.py
python scripts/serve_demo_video.py
```

The last command starts the local chapter player at `http://127.0.0.1:8502/Watch_Demo.html`. In another terminal, `python scripts/check_demo_player.py` checks real Chrome playback, advancing playback time, chapter/scene seeking, and HTTP byte-range behavior. The server binds only to localhost and serves the demo directory. The MP4 also plays as a standalone file.

The narration generator caches each scene by its text, voice, speed and segmentation version. Encoding caches also bind the scene, narration identity and source recording. Model output may differ across environments; review the capture outcomes and adapt the narration before publishing a new recording. The saved recording is the evidence for this particular take, not a guarantee of future outputs.

## Validation and packaging

The verifier checks resolution/codecs, the 12–14 minute duration, continuous scene timing, caption bounds, chapter count, audio/video duration agreement, captured outcomes and media hash. It decodes the entire video, measures narration loudness and true peak, and extracts a contact sheet for visual review. The QA report distinguishes media/integration checks from independent validation of operational guidance.

The existing presentation ZIP is intentionally kept small and source-free. The narrated video is delivered alongside it in `demo/`, with its transcript and accessibility assets. It is not sent to the Administrator or published to LinkedIn automatically.
