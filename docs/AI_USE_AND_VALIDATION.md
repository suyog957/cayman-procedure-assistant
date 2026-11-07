# Use of generative AI and validation

The PDF explicitly expects use of generative AI and asks the candidate to explain that use, the decisions made, and evaluation of the resulting outputs. It also requires independent work and prohibits plagiarism. The candidate should accurately disclose this assistance, review every result and be able to explain the solution personally.

## Where AI was used

| Activity | AI contribution | Validation and ownership |
|---|---|---|
| Requirements and architecture | AI assisted with PDF analysis, requirement mapping and design alternatives | Requirements mapped back to both PDF pages; candidate reviews recruiter-specific logistics |
| Implementation | AI assisted with parser, retrieval, orchestration, UI, tests and artifact generation | Local execution, structural tests, source-hash checks, retrieval ablations and actual model-response evaluation |
| Runtime answers | A locally executed Qwen3-4B quantized model generates responses from retrieved evidence; a Qwen2.5 1.5B baseline was compared | Citation/number/length checks, verbatim support and NLI screening, visible source passages and explicit fallback |
| Evaluation cases | AI authored questions and expected facts using source excerpts | Evidence locators must resolve to actual source passages; labels are explicitly not independent SME ground truth |
| Presentation and explanation | AI assisted with slides, notes, walkthrough and design rationale | Claims tied to measured artifacts; six-slide count, source-free packaging and visual checks |

Embeddings, passage reranking and NLI screening are machine-learning components, but they do not generate the final answer. The actual generative model call is separately recorded in each response using `generator_used`, model identity and input/output token counts. Retrieval-only and withheld-output responses are not presented as successful generation.

## Evidence of validation

- The original PDF text is saved for requirement checking.
- All eleven input filenames and byte-level hashes are recorded in the corpus manifest.
- Normalized document extracts can be inspected beside the originals.
- Unit tests cover nontrivial table layout, Unicode, stable passage identity, source changes, conversation isolation/topic switching and output guardrails.
- Retrieval is measured against source-specific evidence locators, not just the expected document title.
- Keyword, dense and hybrid approaches are compared on the same cases.
- The answer evaluation retains responses, selected evidence, source hashes, timing and diagnostic checks.
- Follow-up and topic-switch conversations are evaluated separately.
- Tests for unsupported questions, missing context, instruction injection and obvious identifiers are included.
- Review documents distinguish mechanically valid citations, NLI screening, factual term coverage and human-assessed correctness.

## Failures that informed the design

Initial experiments exposed a notary answer that reached the right permission decision but invented an exemption from other notarization rules. A metal-card answer incorrectly added instructions from a found-card scenario to a customer disposal scenario. Both examples illustrate why a citation and a keyword match are insufficient to validate a complete answer. Partial diagnostic traces are retained under `artifacts/experiments/`; they are not the final benchmark.

Changes included shorter passages, a stronger reranker, a narrower evidence pack, prompts to preserve row conditions and omit invented explanations, and a claim-support screening step. An NLI diagnostic also showed false rejections caused by phrases such as “according to the evidence.” Attribution language is removed from the claim before screening while the substantive claim is left intact.

The final pipeline remains imperfect. Passing the screening step does not establish semantic correctness, and a rejected draft may actually be correct. The evaluation report records abstention/fallback as a loss of generated-answer coverage rather than hiding it inside a high accuracy percentage.

## What has not been established

No bank SME has independently adjudicated the generated labels or outputs. The challenge split was authored before results were inspected, but it is not a blinded holdout after inspection during development. No production user study, enterprise security assessment, model-risk approval, live policy-version check or real-bank-system integration has occurred. No productivity savings or enterprise-scale service levels are claimed.

The candidate should review the response traces, rehearse the demo, personalize the leadership narrative, and accurately describe this as an AI-assisted implementation. Submission and any representations to the hiring team remain the candidate's responsibility.

## Version 2 validation records

The current workspace adds claim-local citation binding, current source/index integrity checks, statement-to-source evidence windows and one bounded correction. Runtime activity shows observed actions and deterministic check results, not fabricated agent thinking or private model reasoning. The same regression suite is rerun, with earlier results retained under `artifacts/experiments/v1_complete_before_workspace_v2`. The current evaluation records correction attempts and how many revised drafts passed the release checks. More inspectability does not itself establish factual correctness.

## Narrated demonstration

The end-to-end video uses genuine browser interactions and a separately generated local synthetic narration voice. It does not clone or represent the candidate's own voice. AI assisted the narration script, scene planning and production automation. B02 and N03 are explicitly labelled saved regression examples, and a freshly captured source-only follow-up is described as withheld. Processing pauses may be shortened and final frames held for explanation; model runtimes remain visible. Source code is not displayed. Media, caption and playback checks support the recording's quality but do not add independent SME validation. The editable script, capture outcomes, production/model hashes and verification report accompany the video under `demo/`; the recording boundaries and reproduction steps are in `docs/VIDEO_PRODUCTION.md`.
