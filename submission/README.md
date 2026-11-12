# Presentation outputs

PowerPoint files, PDFs and presentation ZIPs in this directory are local build outputs. They are not versioned in the repository.

The prepared workstation retains:

- `Branch_Assist_Solution_Presentation_Final.pptx`: final six-slide deck with learning notes.
- `Branch_Assist_Solution_Presentation_Final.pdf`: slide PDF.
- `Presenter_Notes.pdf`: presenter learning guide.
- `Demo_Runbook.pdf`: presentation and demonstration sequence.
- `Recorded_Demo.pdf`: saved-response backup.
- `Presentation_Materials.zip`: source-free presentation package.

To create the outputs from the accepted results, run `python scripts/build_deliverables.py` from the repository root. Rendering requires PowerPoint or local LibreOffice Impress. See [development instructions](../docs/DEVELOPMENT.md) for setup and checks.

For a notes-only revision to an existing local deck, edit [the presenter guide](../docs/PRESENTER_LEARNING_NOTES.md), then run `python scripts/update_presenter_notes.py`.

The original local files are preserved when removing these exports from Git. Do not commit generated copies or upload the implementation source as presentation material.
