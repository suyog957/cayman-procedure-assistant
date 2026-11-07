# Detailed solution overview

The complete assignment PDF was reviewed and an end-to-end, locally runnable generative chat solution was built over all eleven supplied procedures. The deliverables include six editable PowerPoint slides with speaker notes, a matching PDF, a timed demonstration guide, measured evaluation, raw evidence traces and a source-free presentation archive. This is a tested exercise prototype, not a bank-approved operational deployment.

## What was built and why

The system helps employees ask a procedure question, inspect the supporting passages and refine the situation conversationally. Retrieval-augmented generation was chosen to keep the evidence explicit and replaceable. Fine-tuning would not itself provide reliable citations or source version control. A local model removes the API-key dependency and makes the demonstration reproducible on this computer.

The final generator is Qwen/Qwen3-4B-GGUF:Q4_K_M. The Qwen3 model uses four-bit GGUF inference through llama.cpp on CPU. An earlier Qwen2.5 1.5B float32 baseline produced too many distracting details and withheld drafts; its complete results are retained separately. Model choice was evaluated empirically rather than inferred from published benchmarks.

The solution uses structure-aware HTML parsing, a JSONL passage store, BM25 lexical search, 384-dimensional MiniLM embeddings, reciprocal rank fusion, MiniLM cross-encoder reranking, bounded evidence, actual local generation, citation-local numeric checks and a DeBERTa NLI screening signal. The Wells Fargo–inspired version 2 workspace exposes a searchable procedure library and an Evidence desk with Evidence, Checks and Activity views. The brand asset is the unmodified official website wordmark, and the interface is explicitly labelled as an interview prototype using the supplied Cayman Bank documents.

Version 2 checks original sources and cached-index fingerprints on every supported request. It binds explicit citations to individual claims and records the source passage and evidence window behind each support check. A failed draft may receive one correction using the same evidence; the revised draft must pass the same checks or be withheld. Actual stage events and deterministic decision criteria are visible; the interface does not fabricate private model reasoning or a confidence percentage. Details are in [the version 2 design](docs/EXPERIENCE_V2.md).

## Assignment alignment

The PDF asks for a functional generative conversational solution grounded in eleven documents, approximately five to six PPT slides, methodology and architecture, technology and design decisions, document processing/chunking/retrieval, quality measurement, follow-ups and a demonstration. It allows generative AI, requires explanation of its use and validation, and excludes source code from the presentation and demonstration. Each expectation is mapped in [the assignment review](docs/ASSIGNMENT_REVIEW.md).

The deck has exactly six slides. Presenter notes support a 20-minute delivery; the runbook allocates the separate 15-minute walkthrough. Presentation files are isolated from implementation source. The recruiter-specific deadline, recipient and meeting details were not supplied and are not inferred from the PDF date. No materials have been sent externally.

## Input review and content preservation

The supplied corpus contains 79,424 extracted words and 139 HTML tables including nested tables. It is indexed into 1,388 passages. PR1779 is much larger than the other procedures and contains several account-type workflows.

| Procedure | Subject | Extracted words | Passages | Publication in supplied source |
|---|---|---:|---:|---|
| PR1000 | Notary: Services, Supplies and Manager Responsibilities | 2,909 | 53 | January 29, 2026 |
| PR1263 | Secure Destruction, Store Materials and Records, and Record Holds | 4,781 | 103 | October 10, 2025 |
| PR1277 | Primary and Secondary Identification Requirements | 1,404 | 25 | January 7, 2026 |
| PR1779 | Business Deposit Account: Estate, Receivership, Government Entities, Business Trusts, Girl Scouts | 38,884 | 630 | December 10, 2025 |
| PR1949 | Savings Bonds: Rate and Redeem | 4,654 | 82 | December 17, 2025 |
| PR2306 | Copy Requests: Statements, Debit or Credit Items, and Account Documentation | 7,980 | 175 | January 30, 2026 |
| PR2321 | Approvals and Overrides – Teller | 3,229 | 52 | January 20, 2026 |
| PR472 | Payment Maintenance: Consumer and Small Business Lending | 3,962 | 84 | December 4, 2025 |
| PR607 | Taxpayer Identification Number (TIN) and Foreign Status Maintenance, Certification, and Backup Withholding | 4,483 | 84 | December 29, 2025 |
| PR63 | Coin-Counting Machines: Sell Full Coin Bags, Balance, Test | 1,116 | 21 | October 9, 2025 |
| PR7554 | Incoming Currency and Coin Shipments | 6,022 | 79 | January 30, 2026 |

The original files were preserved. Each passage records its procedure ID, title, publication text, source filename, source SHA256, section hierarchy, anchor, ordinal, text, content type and table/row metadata when applicable. A source revision changes passage identity and requires rebuilding the index.

The parser recognizes the HTML export's policy classes and handles UTF-8 explicitly. It excludes scripts and display-only styling, does not follow links, and retains table column labels, row conditions, rowspans and colspans. Nested table text is included once. Long table rows repeat their leftmost condition in continuation passages.

Narrative grouping targets roughly 110 words within sections, with 20-word overlap when splitting long content. Unsplit table rows can reach 130 words; continuation condition prefixes can make them longer. These are word targets, not exact token counts. All checked source paragraph five-word sequences were found by the extraction audit across the eleven documents; that establishes a limited text-preservation diagnostic, not semantic validation of the table parser.

## How a question is answered

1. Bound and check the question. Recognize an explicit procedure, a named topic or a contextual follow-up.
2. Search BM25 and normalized dense vectors. Combine the rankings with RRF and rerank the candidates jointly with the question.
3. Abstain if evidence signals are weak. Otherwise construct a pack of up to three nonduplicate passages, targeting at most 520 words.
4. Give the selected evidence and resolved question to the local generative model. The prompt requires a direct, concise answer with conditions, exceptions and source labels.
5. Check citation labels, claim-local attribution, numeric values and recognized boundaries against the cited passages; screen claim support with verbatim matching or NLI.
6. If a draft fails, allow one bounded correction with the same evidence and deterministic feedback, then apply the same checks. Display a passing answer with evidence; otherwise withhold it and show sources. Unsupported questions receive abstention or clarification. Record the actual stages and decision for inspection.

Source hashes detect changed originals; the embedding manifest binds the exact vector-matrix bytes and the passage-file hash. Startup validates dimensions, finite values and normalization, and requests detect changes to the cached matrix file as well as metadata. Plain JSON and NumPy files avoid loading pickled index objects. Runtime model loading uses local files; external linked documents are not retrieved. Some supplied links are placeholders and are not treated as evidence.

## Follow-ups and user experience

Browser sessions own their question history; cached models/indexes do not own user conversation memory. Prior user questions can resolve an elliptical follow-up. A hypothetical repeating the same topic or procedure ID retains the earlier situation, including conditions such as an emailed document. A follow-up naming a new task in the same procedure retains scope without repeating unrelated prior-task keywords. Named topic changes replace previous scope. Every follow-up performs fresh retrieval; previous generated claims are never authoritative evidence.

The interface provides starter scenarios, a searchable procedure library, optional document-scoped retrieval, citation selection, original-procedure downloads, publication information, reset, opt-in investigation export and feedback. The Evidence desk separates exact passages, claim-support checks and observed activity. Conflicting document scope prompts clarification, and a new unsupported response does not silently show an earlier response's sources. The resolver remains bounded and can misinterpret ambiguous or long conversations.

## Measured results

The suite includes 30 ordinary procedure questions, four two-turn conversations and six guardrail questions. Labels are AI-authored and source-checked. The 19/11 development/challenge split is not an independent blind holdout after development inspection.

| Retrieval method | Evidence hit@5 | MRR@5 | Local median retrieval seconds |
|---|---:|---:|---:|
| BM25 | 90.0% | 0.798 | 0.036 |
| Dense | 93.3% | 0.818 | 0.035 |
| Hybrid + reranker | 100.0% | 0.928 | 1.484 |

Retrieval hit@5 measures whether at least one labelled relevant passage was in the first five, not whether all applicable evidence was retrieved or an answer was correct. Repeated equivalent passages are allowed by the label locators.

| Answer diagnostic | Observed result |
|---|---|
| Ordinary questions with all required fact groups, automatic proxy | 76.7% of 30 |
| Mean required-fact group coverage, automatic proxy | 76.7% |
| Withheld drafts shown as source excerpts | 6 of 35 generated evaluations |
| Expected guardrail response status | 100.0% of 6 |
| Serial local end-to-end p50 / p95, generated evaluations | 13.81s / 23.92s |
| Mean generated-draft word count | 28.0 |
| Bounded correction attempts / revised answers released | 9 / 2 |
| Ordinary-question response outcome counts | {'answered': 23, 'evidence_only': 5, 'unsupported': 2} |
| Follow-up final-turn fact proxies | F01.2: miss, F02.2: pass, F03.2: miss, F04.2: pass |

The latency measurements exclude initial model loading and are from serial requests on the local CPU; they are not a throughput benchmark. Word count is a conciseness diagnostic, not proof of sufficient context. Term matching can pass wrong statements or miss correct paraphrases. NLI is fallible. These results must not be described as independently established accuracy.

Version 2 permits one correction after a failed draft, using the same evidence and check feedback. This increases the worst-case generation work. 2 of 9 revised evaluated drafts passed release checks in this run. This is a screened-release count, not independent confirmation of the revisions' correctness.

Regression cases missing at least one required fact group, including source-only outcomes: N03, B01, S03, C01, A03, T01, H02, F01.2, F03.2. Review their raw responses and evidence in `artifacts/evaluation/answer_details.json`. The report does not hide fallback as generated-answer success.

## Testing and observed engineering lessons

Focused automated tests cover table row/column condition preservation, nested table duplication, UTF-8, stable IDs, source revisions, real-corpus facts, follow-up scope, topic changes, session isolation, invalid citations, invented amounts, equivalent currency formatting, missing paragraph citations, stale sources, direct instruction attacks and obvious identifiers. Separate browser checks exercise the actual local app and save screenshots.

The recorded automated test run contains 49 tests with 0 failures/errors. The live browser integration check passed actual generation, an explicit single-versus-dual-control follow-up, source inspection, complete transcript export, independent browser sessions and reset. The browser reported no client errors. Results and screenshots are retained under `artifacts/`.

Initial failures combined rules from different situations and invented an exception rationale despite valid citations. Shorter passages, stronger reranking and a larger quantized generator reduced some weaknesses. Claim screening adds a conservative boundary but can withhold valid answers. A narrow evidence pack also trades lower distraction against missing exceptions elsewhere. These are documented tradeoffs, not solved problems.

## What a production version still needs

Independent SME-authored and adjudicated cases are the first priority. Evaluate accuracy, relevance, completeness and conciseness separately, and treat critical errors independently of averages. Include unseen scenarios, long conversations, cross-references, conditional tables, outdated/conflicting sources, malicious retrieved content and realistic employee tasks.

Production also needs authoritative effective policy versions, approved ingestion and rollback, employee SSO, document-level entitlements, approved model selection, redacted audit/retention, monitoring, rate limits, concurrency, timeouts, escalation and required enterprise review. The prototype's local processing and simple identifier patterns do not replace these controls.

The recommended next step is a scoped validation phase with procedure owners and model/platform teams. A pilot should depend on agreed critical-error, coverage, correctness, completeness and latency gates and measured employee benefit over existing search. No productivity, cost saving or enterprise-compliance achievement is claimed here.

## Where to find the deliverables

- `submission/Cayman_Procedure_Assistant.pptx`: six editable slides and presenter notes.
- `submission/Cayman_Procedure_Assistant.pdf`: matching slide PDF.
- `submission/Demo_Runbook.pdf`: timed presentation and demonstration guide.
- `submission/Recorded_Demo.pdf`: clearly labelled saved responses for rehearsal and backup.
- `submission/Presentation_Materials.zip`: allowlisted source-free presentation package.
- `docs/ARCHITECTURE.md`: component design, decisions, parameters and production path.
- `docs/ASSIGNMENT_REVIEW.md`: every requirement, acceptance evidence and three-day plan.
- `docs/AI_USE_AND_VALIDATION.md`: development/runtime AI use and validation boundaries.
- `docs/TECHNICAL_WALKTHROUGH.md`: design defense and interview questions.
- `evaluation/REVIEW_RUBRIC.md`: independent-review scoring and proposed release gates.
- `artifacts/index/`, `artifacts/evaluation/` and `artifacts/runtime_manifest.json`: reproducible source, measurement and model provenance.

Run the application with the instructions in `README.md`. Review the source traces and personalize the narrative before presenting. The candidate must verify deadline/submission logistics and be able to explain and defend the work personally.
