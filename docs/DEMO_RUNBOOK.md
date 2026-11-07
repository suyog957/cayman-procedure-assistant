# Presentation and demonstration runbook

The assignment allows 20 minutes for the presentation and 15 minutes for the technical walkthrough and demonstration. Use the six-slide deck and the local application. Do not show or submit implementation source code. This guide is preparation material; use the source-free PDF copy in `submission/` if sharing it.

The separately delivered narrated recording, `demo/Branch_Assist_Full_Demo.mp4`, covers the end-to-end technical workflow within the walkthrough slot. Open `demo/Watch_Demo.html` to jump to chapters or individual scenes. It includes synthetic narration, captions, actual UI interactions and explicitly labelled saved regression cases. Present it as a recorded walkthrough. Keep the live application ready for questions and leave room for discussion; the separate 20-minute slide presentation and candidate Q&A still apply. See `demo/FEATURE_COVERAGE.md` and `docs/VIDEO_PRODUCTION.md` for timing and provenance. The video is delivered alongside the presentation ZIP, rather than inside it.

## Version 2 workspace controls

Use **New investigation** to reset. Citation buttons such as **[S1] PR63** select the exact passage in the **Evidence desk**. Its **Evidence**, **Checks** and **Activity** views expose sources, statement support and actual execution events. A failed draft may receive one bounded correction; show that step only when it appears in the actual activity record. The **Procedure library** searches source documents and sets retrieval scope. Keep **All 11 procedures** selected for the topic-switch demonstration. The **Evaluation** view shows measured results and limitations. Do not describe activity events as the model’s private reasoning.

## Before the meeting

1. Check the recruiter email for the exact submission deadline, recipient, video meeting link and any additional delivery instructions. None were supplied with this workspace.
2. Review the six slides, presenter notes, final evaluation report and AI-use disclosure. Personalize the introduction and accurately disclose assistance.
3. Start the application using the README instructions. Open `http://127.0.0.1:8501` and ask one question before the call to load the models. Then reset the conversation.
4. Keep the PPT, its PDF backup, this runbook and `Recorded_Demo.pdf` ready. Use the PDF/transcript only as a clearly labelled recorded backup if live inference fails.
5. Share only the presentation/application window. Close editors, terminals showing source, notifications and unrelated browser tabs. Set display scaling so source passages are legible.
6. Rehearse once with a timer. Verify the model files are present and the laptop is connected to power. No API key or internet model service is required after setup.

## Twenty-minute presentation

| Time | Slide | Message |
|---|---|---|
| 0:00–3:00 | 1 — Business problem and delivered prototype | Employees need an answer they can inspect; this is decision support over the supplied snapshot |
| 3:00–6:30 | 2 — Architecture | Follow evidence through ingestion, retrieval, generation and checks; explain why RAG |
| 6:30–10:00 | 3 — Content and retrieval | Explain tables, conditions, chunking, provenance, hybrid search and measured alternatives |
| 10:00–13:00 | 4 — Conversation and experience | Demonstrate the mental model for follow-ups, topic changes, citations and fallback |
| 13:00–17:00 | 5 — Evaluation | Separate retrieval success, generated fact coverage, screening, conciseness and human correctness |
| 17:00–20:00 | 6 — Limits and next decision | Explain observed weaknesses and the work required before a real pilot |

Numbers on slide 5 are generated from the final local metrics. Do not replace proxy labels with a claim of independently established accuracy. Leave a few seconds per slide for transitions and questions; adjust speaking pace during rehearsal.

## Fifteen-minute technical walkthrough and demonstration

| Time | Action | What to explain |
|---|---|---|
| 0:00–1:30 | Open the application and identify the eleven-document collection | Local model, fixed snapshot, source inspection, no transaction execution |
| 1:30–4:00 | Ask the coin-machine question, then its follow-up | Actual generation, fresh retrieval, procedure-scoped context and source citations |
| 4:00–6:00 | Reset; ask the emailed-document notary scenario, then “What if the requester is physically present?” | Follow-up context must preserve the original prohibition |
| 6:00–8:00 | Reset; ask the savings-bond limit, then the Private Bank exception | Completeness includes exceptions; inspect the source instead of relying on a fluent answer |
| 8:00–9:30 | Ask “What about savings bond redemption fees?” after a different topic | A named new topic should replace old context |
| 9:30–11:00 | Ask an unsupported question and a short ambiguous question after reset | Show abstention and clarification; avoid inventing missing information |
| 11:00–12:00 | Expand a source panel and a procedure download | Show section, date, passage identity and original source; explain the source hash |
| 12:00–13:30 | Discuss a withheld response from the recorded evaluation | Failed checks show excerpts; explain false positives and coverage loss honestly |
| 13:30–15:00 | Return to evaluation/architecture slide and discuss tradeoffs | Defend model choice, retrieval, limitations and next validation work; respond to questions |

## Exact scenario prompts and source facts to verify

**Coin-counting machines**

- “What is the overnight storage limit for a coin-counting machine?”
- “And is monthly testing done in single or dual control?”

PR63 states a maximum overnight amount of $5,250 in a single machine. Monthly testing is single control; weekly balancing and random monthly cash counts are dual control. The second question names a new task within the same procedure and must retrieve the testing requirement rather than restate the overnight rule.

**Notary services**

- “Can a notary notarize an emailed document?”
- “What if the requester is physically present?”

PR1000 prohibits notarizing documents sent by email, fax, mail or text even if the requester is present. A fluent answer must not turn physical presence into permission. If the generated draft is withheld, show the source excerpt and explain the outcome instead of presenting it as a successful generated answer.

**Savings-bond limit and exception**

- “What is the savings bond redemption limit for an account open less than 12 months?”
- “What if they are eligible for The Private Bank Experience?”

PR1949 limits those accounts to $1,000 per day in aggregate redemption value, with an exception for customers eligible for The Private Bank Experience regardless of account age. The presence and account-eligibility conditions in the full procedure still apply; the assistant must not invent a general exemption from all rules.

**Topic change**

- Ask a coin-machine question, then “What about savings bond redemption fees?”

PR1949 says a bank is prohibited from charging a fee to redeem a U.S. savings bond. The source should change from PR63 to PR1949.

**Missing evidence and missing context**

- “What is the weather in London tomorrow?”
- After reset: “Can they do that?”
- “What does PR999999 require for mortgage applications?”

Expected outcomes: insufficient support, clarification, and unavailable procedure. These are deliberate outcomes, not system errors.

## When something goes wrong

If inference is slow, describe the local CPU tradeoff and inspect an existing source panel while waiting. If an answer is partial or withheld, identify the status and use it to explain evidence checks and coverage. If the app cannot load, use the clearly labelled recorded transcript; do not imply a recorded response is live. Do not improvise a bank rule from memory to fill missing evidence.

The recorded transcript and evaluation traces represent outputs from the tested snapshot and configuration. Future runs may differ across model/backend versions or hardware, despite greedy decoding. The source procedure remains the reference for the exercise.
