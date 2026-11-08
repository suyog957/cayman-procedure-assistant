# Branch Assist: solution presentation and demonstration

The solution presentation is designed for 20 minutes, followed by a 15-minute walkthrough of the working chat. Present the methodology, architecture and measured evidence first; use procedure examples to demonstrate behavior afterward.

## Presentation flow

| Time | Slide | Core question |
|---|---|---|
| 0:00–2:30 | 1 — Solution overview | What business objective does the system address, what was implemented, and what methodology does it use? |
| 2:30–6:00 | 2 — Document engineering | How were the eleven documents profiled, parsed, chunked, indexed and made traceable? |
| 6:00–9:30 | 3 — Architecture and design choices | How do context resolution, hybrid retrieval, generation and checks work, and why were these technologies chosen? |
| 9:30–13:00 | 4 — User experience and follow-ups | How does an employee control scope, inspect sources, refine a situation, change topics and review a response? |
| 13:00–17:00 | 5 — Evaluation | How are accuracy, relevance, completeness and conciseness assessed, and what do the measured results establish? |
| 17:00–20:00 | 6 — Demonstration | What behavior should be observed across routine questions, changed conditions, exceptions and insufficient support? |

## Walkthrough setup

Open the local application at `http://127.0.0.1:8501`, warm the model with one question, then select New investigation. Keep All 11 procedures selected for topic changes. The approved silent recording is available separately at `demo/final/Branch_Assist_Final_Approved.mp4`; its 9:25 duration leaves time for live source inspection and technical questions. Identify recorded playback as a recording.

## Demonstration sequence

1. Ask “What is the overnight storage limit for a coin-counting machine?” Open the citation and verify the $5,250 maximum in a single machine against PR63.
2. Ask “And is monthly testing done in single or dual control?” Inspect the new testing passage and the single-control answer. Explain that context retains the procedure while evidence is retrieved for the new task.
3. Start a new investigation. Ask “Can a notary notarize an emailed document?” Then ask “What if the requester is physically present?” PR1000 still prohibits the emailed document; the prior situation must remain in the resolved question.
4. Ask a named new topic such as “What about savings bond redemption fees?” The source should change to PR1949, which prohibits the bank from charging a redemption fee.
5. Start a new investigation. Ask the savings-bond limit for an account open less than twelve months, then ask about The Private Bank Experience. PR1949 gives a $1,000 daily aggregate limit with an exception for eligible customers regardless of account age. In the approved recording, the exception draft fails a check after one correction and the tool exposes original passages for review.
6. Inspect Checks and Activity. Show a response's citation attribution, numeric and support screens, selected evidence, actual execution steps and durations. Explain that these are fallible screening results, not a correctness probability.
7. Mark a response for review and export the investigation. The export includes conversation, sources, checks, activity, selected scope and feedback.
8. Reset and ask “Can they do that?” to show clarification. Ask about tomorrow's weather or an unavailable procedure to show unsupported outcomes. Earlier sources must not silently become evidence for a new request.
9. Open Evaluation and distinguish evidence retrieval from answer quality, fallback coverage and response latency. Download the current presentation and reports if needed.

## Interpretation and technical discussion

Use the original source text to assess applicability, conditions and exceptions. A passed screen does not establish independent correctness; a withheld draft may still contain correct information. Source-only outcomes are reported separately from generated-answer coverage. Model outputs can vary across hardware or backend versions despite greedy decoding.

Discuss RAG versus fine-tuning or full-corpus prompting; section/table-aware chunking; BM25 and dense search; rank fusion and cross-encoder reranking; local quantized generation; claim-local citations; bounded correction; source/index integrity; session-scoped context; and the limits of NLI screening. The working UI, evidence records and architecture diagrams provide the walkthrough evidence; implementation source remains outside the shared presentation.

The next engineering work includes independent review on unseen scenarios, broader exception coverage, stronger-model and concurrency comparisons, authoritative source versions, access controls, monitoring and rollback. Those capabilities are future work rather than measured achievements.
