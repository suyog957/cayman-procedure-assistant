# Leadership presentation: story, design and requirement coverage

The six-slide deck is designed for the assignment's 20-minute senior-leadership presentation, followed by the separate 15-minute technical walkthrough. It explains the employee outcome first, then the engineering choices and measured evidence behind it. Detailed speaker notes provide the technical depth and explicit transitions; the visible slides carry the main argument.

## The connected story

| Slide / timing | Leadership question | Main message | Connection to the next slide |
|---|---|---|---|
| 1 / 0:00–2:30 | What employee problem did we solve? | A working assistant turns a procedure question into guidance with an inspectable source. Faster access to correct guidance is a goal to test, not a claimed saving. | An inspectable answer starts with how the original rules are organized. |
| 2 / 2:30–6:00 | How did the supplied documents become usable evidence? | Preserve the task, conditions, exceptions and source identity before retrieving passages. | The prepared collection feeds a bounded request pipeline. |
| 3 / 6:00–9:30 | How is an answer produced, and why these choices? | Resolve context, retrieve/rerank, select evidence, generate locally and screen the output. Explain weak evidence, one correction and source review. | These controls must be usable in an employee conversation. |
| 4 / 9:30–13:00 | How does it work for the employee and their follow-up? | Actual recorded coin-machine responses show fresh evidence for a new task. The original source is visible beside the dialogue. | A convincing interaction needs separate tests for evidence retrieval and response quality. |
| 5 / 13:00–17:00 | What does the evidence establish, and what remains to validate? | Compare retrieval methods; distinguish the expected-fact proxy from accuracy; explicitly measure accuracy, relevance, completeness and conciseness. | The observed limits define the demonstration and next leadership decision. |
| 6 / 17:00–20:00 | What should we inspect now and validate next? | Demonstrate routine, conditional and exception scenarios; recommend a scoped validation phase with owners and gates. | Hand off to the live application or approved 9:25 silent recording, with time for source inspection and questions. |

The coin-machine question is the running example across the opening, table-preparation example and recorded conversation. This continuity connects the employee need to the data design and visible tool behavior. Notary and savings-bond examples then demonstrate condition preservation and honest fallback. The closing recommendation follows from the measured results.

## Assignment coverage

| Assignment expectation | Where the deck answers it |
|---|---|
| Functional generative chat grounded in all eleven procedures | Slide 1 defines the delivered scope; slide 3 shows actual local Qwen generation; slide 4 reproduces real recorded outputs. The tool and separate demonstration are the execution evidence. |
| Approximately five to six slides for senior leadership | Exactly six slides, with takeaway headlines, a business-first opening, measurable evidence and a closing decision. |
| Methodology, architecture, technology choices and key design decisions | Slides 2–3 show structural parsing, bounded passages, hybrid search, rank fusion, reranking, Qwen3 quantization, local CPU inference, claim checks and fallback. Notes explain RAG versus fine-tuning/full-corpus prompting, exact in-memory search and the limits of local models. |
| Document processing, organization, chunking and retrieval | Slide 2 explicitly shows task/control preservation, source identity, ~110-word narrative targets, 20-word overlap, table conditions, BM25, 384-dimensional MiniLM vectors, fusion/reranking and the evidence pack. |
| Accuracy, relevance, completeness and conciseness | All four dimensions are visible on slide 5 with included diagnostics and the question an independent reviewer must judge. Notes cover unseen scenarios, two reviewers, adjudication, critical errors, coverage and false refusal. |
| User experience and follow-ups | Slide 4 shows an actual question, answer, follow-up and fresh citation. Notes explain scenario retention, new tasks, named topic/ID changes, document scope, reset, isolation, feedback, export and Evidence/Checks/Activity views. |
| Demonstrate procedure questions, responses and follow-ups | Slide 4 contains real recorded dialogue and source evidence. Slide 6 gives the live/recorded demonstration sequence across coin machines, emailed notary documents and savings-bond exceptions. The runbook allocates the separate 15-minute walkthrough. |
| Be prepared to defend technical choices | Notes explain tradeoffs, development failures, local runtime constraints, checks that can fail and proposed validation/production work. |
| Explain generative-AI use and validation | Visible disclosure on slides 1 and 6; detailed notes distinguish AI-assisted development, runtime generation, source checking and non-independent regression labels. |
| No implementation source in presentation or demo | All diagrams, charts and text are native presentation objects. The only product image is a real source-pane screenshot. The source-free archive retains its six-file allowlist. |

## Visual choices

- Warm white replaces the full red cover. Red identifies structure and emphasis; gold marks the evidence flow. Deep green distinguishes source-supported examples and the validation recommendation.
- A shared six-stage navigation rail makes the progression explicit: Need → Content → Architecture → Experience → Evidence → Decision.
- Large Georgia takeaway headlines and Segoe UI body text use locally available fonts. Core content is editable PowerPoint text, shapes and bar charts, not flattened slide images.
- Each composition fits its message: a tangible answer example, a source-table transformation, a pipeline, an actual dialogue/source view, an evaluation matrix and a demo/decision handoff.
- The original wordmark remains unmodified in a small red badge. The deck is clearly labelled as an interview prototype over supplied Cayman Bank documents.
- The product image is an unaltered browser capture from the approved demo, displayed using a native crop. Its source hash and provenance are recorded in `assets/presentation/PROVENANCE.json`.

## Evidence and interpretation

Slide 5 uses the accepted evaluation files, not invented benchmarks: 27/30 keyword evidence hits, 28/30 semantic hits and 30/30 hybrid hits in the first five; 23/30 cases passing the expected-fact proxy; six source-only outcomes among 35 generated evaluations; two of four original follow-up fact proxies passing; local serial CPU p50/p95 of 13.8/23.9 seconds excluding cold load. The 28-word mean is explicitly draft length, with 32 recorded drafts, and includes withheld drafts.

The deck does not label the proxy as independently established accuracy, hide fallback losses, imply comprehensive security from six selected cases, or claim measured productivity gains. Pilot controls are future work. The recommendation is validation before operational deployment.

## Production and checks

`scripts/presentation_deck.py` builds native editable PowerPoint objects. Desktop Microsoft PowerPoint opens only the generated deck without a presentation window, checks rendered text bounds, exports the actual PDF and produces 1920×1080 slide previews. Existing user presentations are left alone. `scripts/build_deliverables.py` then generates the notes/runbook PDFs and source-free package.

Rebuilding requires the prepared Windows environment, desktop PowerPoint and `python -m pip install -e ".[dev,presentation]"`. The runtime assistant does not require PowerPoint. Use `python scripts/verify_presentation.py` and `python scripts/verify_deliverables.py` for content, layout, metric, PDF and package consistency. Visual previews are in `artifacts/slides/` and `artifacts/presentation/Leadership_Deck_Preview.jpg`.

This redesign changes presentation materials and the packaged PDFs. It does not change the assistant, its accepted evaluation results or the approved final recording. The silent tool-only video does not display the slide deck; a replacement video is unnecessary. All preserved final-video hashes remain subject to verification.
