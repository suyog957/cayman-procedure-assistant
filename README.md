# Branch Assist

A local conversational assistant for eleven Cayman Bank procedure documents. It combines keyword and semantic retrieval, generates answers with Qwen3, and checks each draft against its cited passages. The workspace supports follow-up questions, source inspection, procedure scope, review feedback and conversation export.

![Branch Assist workspace](artifacts/screenshots/welcome.png)

## Run locally

Tested on Windows x64 with Python 3.10, 16 GB RAM and CPU inference. Model downloads require internet access during setup; inference uses local model files and does not need an API key.

```powershell
git clone https://github.com/suyog957/cayman-procedure-assistant.git
cd cayman-procedure-assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/build_index.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open **http://127.0.0.1:8501**. The first question loads the models; subsequent questions reuse them. On the prepared workstation, start with `python -m streamlit run app.py`.

If `llama-cpp-python` needs a prebuilt CPU wheel, the tested wheel index is `https://abetlen.github.io/llama-cpp-python/whl/cpu`. A source installation requires a C++ toolchain. See [development instructions](docs/DEVELOPMENT.md) for checks, evaluation and presentation builds.

Try a question and a follow-up:

1. What is the overnight storage limit for a coin-counting machine?
2. And is monthly testing done in single or dual control?
3. What about savings bond redemption fees?

## How it works

1. **Prepare the sources.** Parse HTML headings, lists and tables. Preserve row conditions, sections and source fingerprints in 1,388 passage records.
2. **Resolve the question.** Apply the selected procedure scope and bounded context from earlier user questions. Each turn retrieves fresh evidence.
3. **Retrieve and select evidence.** Combine BM25 and MiniLM vector search with reciprocal rank fusion, rerank candidates jointly with the question, and select up to three passages.
4. **Generate and check.** Qwen3-4B Q4 runs through llama.cpp on CPU. Citation, numeric-boundary and claim-support checks screen the draft. One correction is permitted; persistent failures produce labelled source excerpts.
5. **Expose the result.** Show the answer, original passages, check results and recorded execution activity. Activity describes system actions rather than private model reasoning.

The index uses JSONL records and a normalized 384-dimensional NumPy matrix. This collection fits in memory without a separate vector database. The [architecture document](docs/ARCHITECTURE.md) explains component choices, budgets and tradeoffs.

## Measured results

These are saved local regression results, using AI-authored, source-checked cases rather than independently adjudicated labels.

| Measure | Result | Interpretation |
|---|---|---|
| Relevant passage in the top five | Keyword 27/30; semantic 28/30; hybrid + rerank 30/30 | Retrieval ordering, not answer accuracy |
| Ordinary-answer expected-fact proxy | 23/30 | Phrase matching can miss valid wording or pass an incorrect statement |
| Source-only fallback | 6/35 generated evaluation records | A draft was withheld after checking |
| Original follow-up fact proxy | 2/4 | Remaining misses are retained in the report |
| Serial CPU response time | p50 13.81 s; p95 23.92 s | Cold model loading excluded |

Read the [evaluation report](docs/EVALUATION_REPORT.md) and [independent-review rubric](evaluation/REVIEW_RUBRIC.md) for definitions and limitations. Passing a citation or NLI screen does not establish correctness. Independent review, authoritative policy versions, enterprise access controls and deployment monitoring remain future work.

## Tests and code checks

```powershell
python -m pytest -q
python -m ruff check app.py src tests scripts
python -m ruff format --check app.py src tests scripts
```

Tests cover table extraction, source/index integrity, conversation handling, citation attribution, numerical boundaries and bounded correction. Model-backed evaluation and browser checks are separate from these unit tests.

## Presentation and demo

- [Presenter learning notes](docs/PRESENTER_LEARNING_NOTES.md) and [walkthrough](docs/SOLUTION_WALKTHROUGH.md)
- [Selected PowerPoint](submission/Copy%20of%20Branch_Assist_Solution_Presentation_Final.pptx) and [selected slide PDF](submission/Copy%20of%20Branch_Assist_Solution_Presentation_Final.pdf). Other presentation exports stay local and are excluded from Git; see [presentation materials](submission/README.md).
- [Approved silent demo](demo/final/Branch_Assist_Final_Approved.mp4): 9:25, 1440p, with on-screen descriptions

For chapter navigation, run `python scripts/serve_demo_video.py` and open **http://127.0.0.1:8502/final/Watch_Final_Demo.html**. The server serves the demo directory on localhost and supports video seeking. The approved recording and sidecars are hash-locked; subsequent recordings must use a separate path.

## Repository layout

| Path | Purpose |
|---|---|
| `src/cayman_assistant/` | Ingestion, retrieval, generation, context, verification and interface |
| `tests/` | Unit and regression tests |
| `scripts/` | Setup, indexing, evaluation, artifact checks and media utilities |
| `evaluation/` | Cases, scoring rubric and human-review template |
| `artifacts/index/` | Prepared passages, vectors and source manifests |
| `artifacts/evaluation/` | Accepted results and response traces |
| `artifacts/experiments/` | Earlier development runs, separate from accepted results |
| `docs/` | Architecture, operating instructions and design explanations |
| `submission/` | The selected PPT/PDF pair and output instructions; other exports stay local |
| `demo/final/` | Preserved approved recording and its verification manifest |

Original inputs are retained without modification. Model weights, environments, credentials and local rendering caches are excluded from Git. Pinned model revisions and local hashes are recorded in the runtime manifest.

Generative AI assisted development, evaluation-case drafting and presentation preparation, and powers runtime answers. [AI use and validation](docs/AI_USE_AND_VALIDATION.md) records that contribution and the checks applied. This repository retains the underlying evidence and development history.
