# Solution presentation: content and requirement coverage

The presentation explains the solution to senior leadership in six slides. The opening establishes the objective, implemented scope and methodology. Examples support the user-experience and demonstration sections. Speaker notes now provide a learning guide: a short speaking version, plain-language explanations of the claims and implementation choices, limitations, likely questions and transitions. The full notes are preparation material, rather than a script to read verbatim. The planned presentation remains 20 minutes, followed by a separate 15-minute walkthrough.

## Slide structure

| Slide | Core purpose | Content |
|---|---|---|
| 1 → Solution overview | Define the business objective, scope and methodology | Employee access to applicable guidance; generative chat over all eleven procedures; retrieval-augmented generation; follow-ups, evidence workspace and evaluation capabilities. No example question or answer card. |
| 2 → Document engineering | Explain preparation and organization of the complete collection | Inventory/profile; structural HTML parsing; ~110-word narrative chunks and 20-word overlap; table labels and conditions; 1,388 indexed passages; BM25 and 384D vectors; source identity and integrity. No procedure-specific example. |
| 3 → Architecture and design choices | Explain the request path and defend technology choices | Context/scope → hybrid retrieval and reranking → selected evidence → local Qwen generation → citation/numeric/support checks → answer or source review. Explain why RAG, hybrid retrieval and the local runtime were selected. |
| 4 → Experience and follow-ups | Explain interaction and conversation design | Library and search scope; context retention and topic changes; citations, checks/activity, feedback and export. A bounded panel reproduces an actual recorded question, answer and follow-up to illustrate those rules. |
| 5 → Evaluation | Explain how response quality is tested and what was measured | Accuracy, relevance, completeness and conciseness have explicit diagnostics and independent-review questions. Compare retrieval methods; show fact-proxy coverage, source-only outcomes, follow-up misses and latency with clear limitations. |
| 6 → Demonstration | Show observable solution behavior and summarize the engineering work | Routine question/follow-up, changed notary condition and savings-bond exception. Inspect source grounding, conversation continuity and failure handling. Conclude with independent quality review, exception coverage and deployment work. |

The story is objective → evidence preparation → answer architecture → employee interaction → evaluation → demonstration. A single example does not define the business problem or the content-engineering method.

## Requirement coverage

| Requested expectation | Presentation evidence |
|---|---|
| Functional generative conversational solution based on eleven procedures | Slide 1 defines the scope and implemented capabilities; slide 3 shows runtime generation; slides 4 and 6 show actual outputs and the demonstration workflow. |
| Approximately five to six slides for senior leadership | Exactly six, with a business objective, technical methodology, measured results and a clear demonstration handoff. |
| Methodology, architecture, technologies and key decisions | Slides 1–3 explain RAG, structural parsing, bounded evidence, lexical/dense retrieval, rank fusion/reranking, local quantized Qwen inference and checks. Notes defend the choices and tradeoffs. |
| Document processing, organization, chunking and retrieval | Slide 2 covers the full collection and extraction/chunking/indexing rules. Slide 3 explains question-time retrieval and evidence selection. |
| Accuracy, relevance, completeness and conciseness | All four dimensions are visible on slide 5; notes explain independent reviewers, unseen scenarios, adjudication, critical errors, coverage and false refusal. |
| User experience and follow-up handling | Slide 4 explains scope, context retention, fresh retrieval, topic changes, evidence inspection, feedback/export and session behavior, with a short recorded dialogue. |
| Questions, responses and follow-ups in the demonstration | Slide 6 and the solution walkthrough cover routine, conditional and exception scenarios, plus clarification and unsupported requests. |
| Explanation of technical approach and decisions | Detailed speaker notes and the architecture document explain model/retrieval tradeoffs, table semantics, token budgets, bounded correction, integrity checks and known failures. |
| Generative-AI use and validation | Slide 6 and notes distinguish development assistance from runtime generation, and explain source checking, engineering tests, retained traces and non-independent labels. |
| No implementation source in shared presentation materials | The package has a fixed six-file allowlist. Slides contain editable text/diagrams/charts and the wordmark; implementation files are excluded. |

## Design and language

Warm white backgrounds, restrained red/gold accents, serif takeaway headings and consistent navigation connect the deck. Native PowerPoint objects keep the content editable. Slides and speaker notes use professional solution language without interview, mock-assignment or prototype labels. Measured outcomes, quality limits and future capabilities remain explicit.

The completed file is `submission/Branch_Assist_Solution_Presentation_Final.pptx`, with a matching PDF. Earlier PowerPoints were open during revision and are left untouched at their previous filenames. The application download path also receives the current PDF; the shared ZIP includes the newly named presentation.

## Validation and rendering

The notes-only revision uses `update_presenter_notes.py` and the canonical [presenter learning notes](PRESENTER_LEARNING_NOTES.md). Only six speaker-note XML parts are replaced in the existing PPTX. All 58 other package parts, including slide text, geometry, imagery, themes and metadata, remain byte-identical. The matching slide PDF and previews are also unchanged. The companion `Presenter_Notes.pdf` has slide bookmarks and the same explanations. `verify_learning_notes.py` checks that the embedded notes and PDF match the guide and that the protected slide artifacts remain intact.

`presentation_deck.py` builds the editable file. PowerPoint is used when background opening is available; local LibreOffice Impress provides an independent rendering path when it is not. A separate local tool/profile keeps existing open presentations intact. Rendered text is checked against intended boxes and the PPT text; all six slides are inspected visually.

`verify_presentation.py` checks that the first two slides contain solution/method content without procedure examples, that contextual labels are absent, that all four quality dimensions are visible, and that recorded dialogue and measured values match their evidence. It also verifies the PDF, source-free package and all preserved final-video hashes.

The accepted evaluation remains unchanged: 27/30, 28/30 and 30/30 top-five evidence hits for keyword, semantic and hybrid retrieval; 23/30 expected-fact proxy passes; six source-only outcomes among 35 generated evaluations; two of four original follow-up fact proxies passing; CPU p50/p95 of 13.8/23.9 seconds, excluding cold load. The mean of 28 words is draft length across 32 records, including withheld drafts. These are diagnostics with stated limits, not independently established accuracy.

The approved silent tool recording remains unchanged. This revision changes presentation content and the accompanying shared materials; it does not change the chat workflow or its accepted results.
