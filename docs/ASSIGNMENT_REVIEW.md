# Assignment review and delivery plan

Source: `Sr Ld Quantitative Analytics Specialist_R-573883_PresSE Candidate_SRF #1839_30Oct26.pdf`, both pages reviewed. The source text is retained at `artifacts/assignment_extracted.txt`. Review date: November 7, 2026, America/New_York.

The exercise asks the candidate to act as a Senior Lead Quantitative Analytics Specialist supporting AI development. The business problem is helping branch employees find and use information in eleven operational procedures. Success requires a working generative conversational assistant and a leadership presentation that explains and demonstrates the engineering choices.

The completed post-approval review is recorded in [FINAL_REVIEW.md](FINAL_REVIEW.md), including requirement coverage, the fixes made, fresh verification evidence and preservation of the approved final video.

## Requirement traceability

| ID | PDF expectation | Implementation or evidence | Acceptance check |
|---|---|---|---|
| R01 | Use all eleven supplied procedural documents | `artifacts/index/corpus_manifest.json`; hashes, dates, sections, and counts for each source | Exactly eleven documents; source verification at startup; corpus tests |
| R02 | Build a functional generative chat solution grounded in those procedures | `app.py`; local retrieval, Qwen generation, citation/number checks and claim-support screening | Run the interactive assistant; inspect saved answer traces |
| R03 | Approximately five to six PPT slides | `submission/Cayman_Procedure_Assistant.pptx` | Exactly six slides; presenter notes; PDF companion |
| R04 | Explain methodology and architecture | Slides 2–4; `docs/ARCHITECTURE.md` | Trace a question through retrieval, context, generation and checks |
| R05 | Explain technology choices and key decisions | Slides 2–4; architecture decision table | Defend RAG, local models, hybrid search, reranking and in-memory indexing |
| R06 | Explain document processing and organization | Slide 3; manifests; normalized source extracts | Show section and table condition preservation; source provenance |
| R07 | Explain chunking and retrieval | Slide 3; retrieval ablation results | Explain bounded sections, overlap, row labels, BM25, vectors, RRF and reranking |
| R08 | Describe testing: accuracy, relevance, completeness and conciseness | Slide 5; evaluation report and review rubric | Separate retrieval metrics, answer diagnostics and human evaluation |
| R09 | Address user experience | Slide 4; interactive app | Guided starters, citations, source inspection, reset, feedback and export |
| R10 | Handle follow-up questions | Session-scoped question context and explicit topic switching | Four saved two-turn conversations; unit tests for isolation and switching |
| R11 | Demonstrate questions from supplied procedures and follow-ups | `submission/Demo_Runbook.pdf`; runnable app; saved demo transcript | Rehearse factual answer, follow-up, exception, topic switch and refusal |
| R12 | Explain technical choices in discussion | `docs/TECHNICAL_WALKTHROUGH.md` | Prepare tradeoffs, failure examples and production next steps |
| R13 | Use generative AI and explain its role and validation | Qwen inference in the product; `docs/AI_USE_AND_VALIDATION.md` | Distinguish AI-assisted development, runtime generation, and validation |
| R14 | Exclude source code from presentation materials and demonstration | `submission/` contains presentation, PDF, runbook and recorded responses only | Packaging script allowlist; no implementation files in the submission archive |
| R15 | Deliver a 20-minute presentation, then a 15-minute technical walkthrough/demo | Six-slide speaking allocation and timed demo guide | Rehearse with a timer; do not navigate into the source-code directory |
| R16 | Submit presentation materials to the Administrator before the stated deadline | Submission-ready files and archive prepared locally | Candidate must use the deadline, recipient, and delivery method in the recruiter email |
| R17 | Prepare within a three-day window and track time | Suggested three-day work breakdown below; reproducible execution records | Planning constraint recorded; no fabricated time sheet |
| R18 | Complete independently, avoid plagiarism | AI use is expressly allowed later in the PDF; AI assistance disclosed; model and technical sources attributed | Candidate reviews, understands, personalizes and can defend every claim |
| R19 | Follow video meeting delivery details and respond to questions | Runbook, presenter notes, technical questions | Candidate checks the meeting invitation, screen sharing and audio |
| R20 | Company-specific policy compliance is not the scoring criterion | Scope limited to the supplied, fictionalized snapshot | Do not claim enterprise approval or current real-bank policy correctness |
| R21 | If an accommodation is needed, contact the recruiter immediately | Conditional candidate logistics instruction | No accommodation was requested in this conversation; candidate contacts the recruiter if applicable |

## Architecture and action sequence

1. Read the complete PDF; extract the delivery constraints and create this traceability map.
2. Inventory all inputs without changing them. Profile document sizes, publication dates, sections, tables, links, and encoding.
3. Parse the HTML structurally. Preserve headings, paragraph/list boundaries, table column labels, row conditions, source anchors and original-file hashes. Do not fetch linked material.
4. Create stable passage records and normalized source extracts. Build and validate the vector index.
5. Compare keyword-only, vector-only and hybrid retrieval against source-checked questions covering every procedure.
6. Implement actual local language-model generation, bounded evidence, explicit citations and input/output checks. Retain failure traces rather than silently presenting them as successes.
7. Implement conversation context and topic switching. Keep sessions isolated and use previous user questions for context, not previous generated claims as factual evidence.
8. Build the employee-facing chat experience and verify it interactively.
9. Run automated structural/safety tests and empirical retrieval/answer evaluations. Review actual answers against cited passages. Record limitations and unresolved risks.
10. Produce six leadership slides, speaker notes, PDF companion, a timed demo guide, a detailed engineering report and source-free submission archive.
11. Rehearse the full 35-minute delivery. The candidate handles the recruiter-specific deadline, submission and meeting logistics.

## Suggested three-day allocation

| Day | Focus | Exit condition |
|---|---|---|
| 1 | Requirements, corpus audit, architecture, baseline retrieval | All sources indexed and representative evidence locators authored |
| 2 | Chat, local generation, conversational context, evidence checks, evaluation | Runnable demonstration with documented failures and measured results |
| 3 | Slides, technical narrative, demo rehearsal, submission checks | Six slides, tested demo, source-free package, rehearsed Q&A |

This is a proposed preparation schedule, not a claim about hours already spent. The filename and PDF date do not establish the submission deadline. That deadline and additional meeting instructions are in the email/invitation, which was not supplied.

## Scope boundaries

The local implementation is a demonstrable prototype. It does not execute transactions, authenticate employees, connect to production bank systems, or certify current policy compliance. It uses the supplied snapshot and does not resolve external procedure links. Enterprise identity, entitlements, policy version authority, operational monitoring, and independent model-risk review are described as future production work, not completed features.

The source files are left in their original location and retain their original bytes. Implementation source remains available locally for the candidate's preparation. Presentation materials and the demonstration do not expose it. No materials have been sent to the Administrator or any other person.
