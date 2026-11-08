# Final assignment and delivery review

Review date: November 7, 2026. Both pages of the original assignment were reread. The review covered the eleven source documents, ingestion/index artifacts, retrieval and generation, conversation handling, evidence checks, UI, evaluation records, six-slide presentation, supporting PDFs, source-free submission ZIP and approved silent recording.

The requested implementation and presentation deliverables are present. The review found and fixed a conversational edge case and several integrity/reproducibility gaps. Answer-quality limitations remain explicit; independent subject-matter validation and enterprise approval have not been completed or implied.

The revised leadership presentation has six connected sections: solution overview, document engineering, architecture and technology choices, user experience and follow-ups, evaluation, and demonstration. The opening slides explain the complete solution and its methodology; procedure examples appear only on slides 4 and 6. Light backgrounds, restrained brand accents and consistent navigation connect the story. Contextual interview, mock-assignment and prototype labels are absent from the deck, speaker notes and shared PDFs. The accepted metrics and substantive limitations remain unchanged. See [the presentation story and requirement coverage](PRESENTATION_STORY.md) and the editable-PPT/PDF content and layout checks under `artifacts/presentation/`. Microsoft PowerPoint rendered the completed Final deck, with zero measured text overflows; local LibreOffice Impress is available as an independent fallback. Existing user-open presentations were left untouched. The approved final tool video remains unchanged.

The later speaker-notes revision changes preparation material only. The [presenter learning guide](PRESENTER_LEARNING_NOTES.md) explains each slide's claims, implementation, rationale, measured evidence and limitations, with a short speaking version and likely questions. It is embedded in the existing Final PPT and rendered as the bookmarked `submission/Presenter_Notes.pdf`. Exactly six notes XML parts changed; all 58 other PPTX parts, the slide PDF, images and preview remain byte-identical. Native PowerPoint opened the revised notes successfully from a read-only compatibility copy. Source documents, application behaviour, accepted evaluation and the approved video are unchanged. Evidence is recorded under `artifacts/presentation/notes_*` and `learning_notes_review.json`.

## Approved video: preserved without overwrite

The user-approved final is [Branch_Assist_Final_Approved.mp4](../demo/final/Branch_Assist_Final_Approved.mp4). Open [the final player](../demo/final/Watch_Final_Demo.html), or run the local video server and visit `http://127.0.0.1:8502/final/Watch_Final_Demo.html`.

The copy is 9 minutes 25 seconds, 2560×1440, entirely silent, with the approved plain-language descriptions and reading pauses. The approved video bytes are unchanged:

`48bc8f2c63d31c7efd5080606f4c2b2165c873c0c31e79b9cb6b318afe0d2c0b`

`demo/final/APPROVED_FINAL.json` records the source commit and hashes for the video and twelve supporting files. Build scripts target the editable `demo/tool-only/` directory, never the final directory. Deliverable checks verify the preserved hashes. The final player was tested separately for playback, chapter seeking and HTTP byte ranges. Any subsequent recording must use a new directory and filename.

## Assignment coverage

The original detailed traceability map is [ASSIGNMENT_REVIEW.md](ASSIGNMENT_REVIEW.md). This review checked its requirements against the actual files and execution evidence.

| Requirement | Review conclusion and evidence |
|---|---|
| R01: use all eleven supplied procedures | All eleven original byte hashes remain unchanged. The index contains 1,388 passages and 384-dimensional vectors. Extraction diagnostics found no missing checked paragraph five-word sequences; this is text preservation, not proof of table semantics. |
| R02: functional generative conversational solution | Actual Qwen3 local generation is exercised through the browser. Retrieval, generation, output checks, citations and fallback are implemented and inspectable. No canned answers replace inference. |
| R03: approximately five to six PPT slides | Exactly six editable PowerPoint slides, matching six-page PDF and speaker notes. The complete slide contact sheet was visually reviewed. |
| R04–R05: methodology, architecture, technologies and choices | Slides 2–4 and architecture/walkthrough documents explain RAG, structural parsing, local models, lexical/semantic search, fusion, reranking, evidence limits and tradeoffs. The architecture diagram was corrected to give the correction loop its own node. |
| R06–R07: processing, organization, chunking and retrieval | Original-file identity, section hierarchy, tables, row conditions, continuation context, roughly 110-word narrative chunks and 20-word overlap are documented. A fresh comparison reproduced the recorded retrieval quality for all three methods and all splits. |
| R08: accuracy, relevance, completeness and conciseness | Slide 5, the evaluation report and scoring rubric distinguish retrieval measures, expected-fact proxies, output length, coverage and independent review. All four requested response-quality dimensions have explicit human scoring criteria. |
| R09–R10: user experience and follow-ups | The workspace, procedure library, Evidence/Checks/Activity views, feedback, downloads, reset and document scope were tested. Session isolation passed. Hypotheticals repeating a procedure name or ID now retain the original scenario. |
| R11: demonstration using provided procedures and follow-ups | The approved video and fresh live checks cover factual questions, source inspection, follow-ups, topic changes, notary restrictions, savings-bond amounts/exceptions, missing context, missing sources and unsupported requests. |
| R12: explain and defend technical decisions | Six-slide notes, detailed solution overview and technical walkthrough cover alternatives, observed failures, design tradeoffs and production work. The candidate must rehearse and be able to defend these personally. |
| R13 and R18: use AI, explain validation, independent ownership and no plagiarism | AI-assisted development and runtime generation are disclosed. Model/component references and evidence records are supplied. AI-authored labels are not described as independent ground truth. Candidate review and ownership remain necessary. |
| R14: exclude implementation source from presentation/demo | The submission ZIP uses a fixed six-file presentation allowlist. Every archived member is checked byte-for-byte against the latest deliverable. No implementation source, model files or evaluation internals enter that archive. The approved recording shows the application UI. |
| R15 and R19: 20-minute presentation, 15-minute walkthrough, video delivery and questions | The runbook allocates both segments and includes rehearsal, screen-sharing and Q&A guidance. The 9:25 recording fits within the walkthrough, with time for live inspection and discussion. Meeting details and personal rehearsal are candidate actions. |
| R16: submit to the Administrator by the email deadline | Presentation files and ZIP are prepared. The recipient, deadline and delivery instructions were not supplied; no submission has been sent or invented. |
| R17: three-day preparation and time management | A proposed three-day allocation and timed delivery guide are provided. No fabricated preparation timesheet is claimed. |
| R20: company-specific policy compliance is not the scoring criterion | Scope remains the supplied Cayman Bank snapshot. Branding is clearly an interview prototype. Current real-bank policy authority and enterprise approval are not claimed. |
| R21: accommodation if needed | This is a conditional candidate instruction. No accommodation was requested; contact with the recruiter remains the candidate's action if applicable. |

## Gaps fixed and rationale

| Finding | Change | Why it matters |
|---|---|---|
| A same-topic hypothetical could discard the earlier situation when it repeated the topic or procedure ID | Preserve prior user-question context for “what if” questions naming the same procedure. Continue to discard old context for a different named procedure and avoid irrelevant earlier terms for a new task. | “What if the notary requester is physically present?” must retain that the document was emailed. Physical presence must not silently become permission. Four new conversation regressions and real browser scenarios cover this distinction. |
| Index validation did not bind the embedding file bytes to the manifest | Add the matrix SHA256, validate shape/finite values/unit norms, and include the matrix in cached-snapshot fingerprints. Existing matrix and passage bytes are unchanged. | A corrupt or replaced matrix should fail clearly rather than silently change retrieval or crash later. Five new integrity regressions cover changed files, wrong dimensions, invalid norms and non-finite values. |
| Retrieval-only or interrupted evaluations could overwrite accepted generative results | Write each run to an isolated new directory. Permit explicit publication only after a complete full Qwen3 run. Publish a hash manifest last so an interrupted multi-file promotion can be detected. | Presentation figures and raw accepted evidence must stay consistent while experiments run. Partial and retrieval-only results cannot erase the accepted answer benchmark. Three new tests cover isolation, incomplete publication and complete bundle binding. |
| Building reports rewrote accepted metrics | Report generation now checks derived values against the saved answers and consumes the accepted metrics without rewriting them. | A presentation build should not modify the evaluation evidence it cites or invalidate the published run's hashes. |
| The submission verifier checked filenames but could accept stale archived files | Compare every allowlisted ZIP member byte-for-byte with the current submission files. | The package being shared must contain the latest deck, notes and runbook. |
| The approved recording had no separately preserved final path | Copy the exact approved bytes and supporting files into `demo/final/`, record hashes and make the primary links point there. | Further implementation or demo work cannot silently replace the user's approved copy. |
| Git line-ending conversion could change frozen sidecar or packaged README bytes after checkout | Preserve exact final-artifact and archived README bytes with Git attributes; normalize newly published evaluation JSON to LF before hashing it. | A separate checkout must pass the same video-hash and exact ZIP-content checks as the prepared workspace. The clean-checkout test exposed and verified this fix. |
| Documentation had a reused diagram node and incomplete correction-loop wording | Give the correction node a distinct identity; align architecture and walkthrough explanations with the implemented bounded retry and source checks. | Reviewers can follow the real request path accurately. |

## Verification evidence

| Check | Result | Evidence |
|---|---|---|
| Automated regressions | 49 passed, zero failures/errors | `artifacts/test_results.xml` |
| Original documents and extraction | Eleven sources preserved; no missing checked five-word sequences | `artifacts/extraction_audit.json`, corpus manifest and deliverable verification |
| Saved-answer review | 40 response records inspected; all 67 source references match the current indexed passages; 26 released answers pass current mechanical checks | `artifacts/final_review/saved_answer_audit.json` |
| Existing benchmark compatibility | All 38 applicable recorded resolved queries unchanged; vector-matrix bytes unchanged | `artifacts/final_review/regression_compatibility.json` |
| Browser integration | Actual generation, explicit control-level follow-up, citations, checks, activity, feedback/export, library/scope, session isolation, reset and mobile layout passed | `artifacts/browser_check.json` |
| Additional live review | Ten requests passed: notary plus repeated-topic and explicit-ID hypotheticals; topic switch; savings-bond amount and exception; reset ambiguity; weather; missing procedure; direct instruction attack | `artifacts/final_review/live_workflow.json` |
| Fresh retrieval comparison | 90 query/method runs; recorded hit@5 and MRR reproduced across every method/split; accepted result files preserved | `artifacts/final_review/retrieval_rerun/`, `evaluation_isolation_check.json` |
| Slides and PDFs | Six slides and matching PDF, notes and supporting documents structurally checked; slide layouts visually reviewed | `artifacts/final_review/presentation_contact_sheet.jpg`, `pdf_structure_review.json`, verification summary |
| Submission package | Exactly six allowed presentation files, valid ZIP, current file bytes, no implementation source | `artifacts/verification_summary.json` |
| Separate repository checkout | The complete staged tree passes source/index, six-slide, exact ZIP-content and approved-video checks in a separate directory | `artifacts/final_review/fresh_checkout_check.json` |
| Approved video | All thirteen preserved file hashes passed, including the approved MP4; silent 1440p playback and chapter seek passed | `artifacts/final_review/approved_video_check.json` |

These checks verify engineering behavior, artifact integrity and measured regression compatibility. They do not establish independent factual accuracy or bank approval. No new full generative benchmark is substituted for the previously recorded one: the existing evaluated queries, sources, model and matrix are unchanged, and fresh browser tests exercise the repaired edge case separately.

## Measured quality and remaining limits

The accepted regression run still reports evidence hit@5 of 90.0% for keyword search, 93.3% for semantic search and 100.0% for hybrid retrieval plus reranking. Hybrid MRR@5 is 0.9278. These are passage-ranking measures.

The expected-fact proxy passes 23 of 30 ordinary cases. Six of 35 evaluated generated calls show source excerpts after withholding a draft. The four original follow-up fact proxies include two misses; those failures remain visible. Six selected guardrail cases agree with their expected statuses. None of these figures is an independently established accuracy or security guarantee.

Known limitations remain explicit: imperfect condition/exception retrieval and NLI screening, unnecessary refusal or withholding, ambiguous long conversations, a narrow input-pattern guard, no authoritative live-policy lookup, and no production identity, entitlements, monitoring or model-risk approval. The supplied rubric explains how independent reviewers should assess accuracy, relevance, completeness and conciseness before a pilot. These are disclosed prototype boundaries, not missing deliverables concealed by the review.

## Recording decision

No replacement video is needed for this review. The interface, approved captions, workflow, recorded results, supplied sources, model and index contents remain the same. The demonstrated requests retain the same resolved queries, and fresh live checks reproduce the central notary, bond and fallback behaviors. The fixes strengthen unshown follow-up edge cases, artifact integrity and development/release workflows; they do not invalidate the approved demonstration.

The approved final remains untouched. If a future change alters a demonstrated workflow, displayed metric, model behavior or explanation materially, produce a separately named new recording and retain this approved copy.

## Delivery and candidate actions

Use `submission/Presentation_Materials.zip` for the source-free presentation bundle, with the approved MP4 separately if the recruiter accepts a video attachment. Keep the private implementation repository available for preparation; do not show its source during the interview demonstration.

Before delivery, confirm the Administrator/deadline and meeting instructions from the recruiter email, rehearse the 20-minute presentation and 15-minute walkthrough, warm the local model, and personalize the AI-use disclosure. These steps require the candidate and recruiter-specific information; nothing has been submitted to the hiring team automatically.
