# Development

The application, artifact utilities and recorded evaluation share the same prepared source snapshot. Preserve the original inputs and accepted evidence when making changes.

## Setup

Follow the Windows setup in [README](../README.md). The default downloader pins the embedding, reranking, verification and quantized generation models. Add `--include-baseline` only when reproducing the earlier Qwen2.5 comparison. Downloaded model weights stay outside Git.

The `dev` extras include pytest, Ruff, PDF/PPT tooling and Playwright. Presentation rendering on Windows additionally uses `python -m pip install -e ".[dev,presentation]"`. The optional `demo` extras support the earlier narrated recording; the application does not require them.

## Code style and unit tests

```powershell
python -m ruff format app.py src tests scripts
python -m ruff check app.py src tests scripts
python -m pytest -q
```

Ruff is pinned in the development dependencies. Formatting uses a 100-character line target and Python 3.10 syntax. Direct entry points add the local `src` directory before package imports; their import-order exception is scoped in `pyproject.toml`.

Keep comments focused on a constraint or a reason for a decision. Core examples include retaining table conditions, binding numbers to the cited passage, preserving source fingerprints, and limiting correction to one attempt. Avoid changing prompts, thresholds or evidence budgets as part of a formatting change.

## Evaluation

```powershell
python scripts/evaluate.py
python scripts/evaluate.py --generate
```

The first command compares retrieval methods; the second also runs local generation. Each writes to a new directory under `artifacts/experiments/`. `--output-dir` accepts a new or empty alternative directory. Interrupted and retrieval-only runs cannot replace accepted answer results.

To publish a completed full Qwen3 evaluation intentionally:

```powershell
python scripts/evaluate.py --generate --publish
```

Accepted results live in `artifacts/evaluation/`. Publication binds the metrics, retrieval details and response details with hashes. Review the changed outputs and update dependent presentation claims before committing a new accepted run. Do not describe phrase-match or NLI results as independent factual accuracy.

For an interactive terminal conversation:

```powershell
python scripts/ask.py "What is the coin-counting machine overnight limit?" "And what control is required for monthly testing?"
```

## Browser checks

Start Streamlit on port 8501, then run `python scripts/check_browser.py --chat`. This optional integration check uses Playwright and installed Chrome. It exercises actual generation, citations, Checks/Activity, library scope, feedback, exports, session isolation and reset. It is not part of the unit-test suite.

## Presentations

PowerPoint, PDF, ZIP and generated README exports in `submission/` are local outputs and are excluded from Git. A fresh clone contains the output instructions, not those files. Build or restore the local presentation before running presentation-specific checks. The app omits downloads for generated reports that are not present.

`python scripts/build_deliverables.py` rebuilds the deck, reports and source-free package from the accepted results. Rendering prefers desktop PowerPoint; local LibreOffice Impress is an alternative. Set `BRANCH_ASSIST_SOFFICE` to the executable path if it is not on PATH or in the local rendering cache. Runtime inference does not require either application.

For a notes-only edit, change [the presenter guide](PRESENTER_LEARNING_NOTES.md), then run:

```powershell
python scripts/update_presenter_notes.py
python scripts/verify_learning_notes.py
```

The updater replaces only the six speaker-note XML parts, preserves the visible slide parts and slide PDF, rebuilds the notes PDF and refreshes the package. If PowerPoint locks the target, the verified temporary result remains in the ignored build directory; leave the open presentation intact and retry after closing it.

Check the completed artifacts with:

```powershell
python scripts/verify_deliverables.py
python scripts/verify_presentation.py
python scripts/verify_learning_notes.py
```

The first two consume saved test and browser evidence as well as current files. They do not rerun model inference or establish independent answer correctness. A test report can be refreshed with `python -m pytest --junitxml=artifacts/test_results.xml`.

## Files to preserve

- Original HTML inputs and the assignment PDF.
- Accepted evaluation files unless deliberately publishing a complete replacement run.
- `demo/final/` in its entirety. `APPROVED_FINAL.json` binds the approved video and twelve sidecars. Render future demos elsewhere.
- Personal Office review copies. They stay local and are excluded from Git; do not silently replace the canonical final deck with one.

Do not commit model weights, environments, secrets, renderer downloads or local caches. Keep source code outside the presentation package, as required by the assignment.
