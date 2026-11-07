# Technical walkthrough and design defense

Use this document to prepare for discussion. During the 15-minute walkthrough, show the application, source evidence, architecture slide and measured results rather than implementation source. The assignment explicitly excludes source code from the demonstration.

## Explain a complete request in two minutes

An employee asks a question. Input checks bound its length and reject a small set of obvious instruction attacks or customer identifiers. The conversation resolver identifies an explicit procedure, a new named topic, or a follow-up using the previous user question. It creates a new retrieval query and searches the supplied snapshot.

BM25 finds exact language and identifiers; dense vectors find paraphrases. RRF combines their rankings. A cross-encoder reorders the candidates. Weak evidence produces a clarification or abstention. Strong candidates are packed into a small evidence block with labels, sections and source identity. A local language model writes an answer from that block.

Checks validate citation labels, cited paragraphs, numeric literals, length and claim-support signals. A failed draft can receive one correction using the same evidence and failed-check feedback. If it still fails, the draft is withheld and the UI shows labelled excerpts instead. The employee can inspect the sources, continue the scenario, switch topics, reset or export the conversation.

## Questions to be ready to answer

**Why use RAG rather than fine-tuning?**

The task is evidence access over eleven procedures, with provenance and likely revisions. RAG makes source updates explicit and citations inspectable. Fine-tuning might help style or domain behavior later but does not replace retrieval, versioning or output evaluation.

**Why not use a vector database, orchestration framework and agent tools?**

The small corpus fits exact local vector search and a transparent pipeline. A database or framework would add operations without demonstrating more value here. A production platform can replace the index interface when scale, entitlements and update concurrency justify it. No transaction agent is needed to answer procedure questions.

**What makes this an actual generative solution?**

The model executes on the local machine for supported questions. Saved traces include model identity, token counts and generation time. Answers are not canned lookups or a remote chat transcript. The system reports separately when it abstains or shows excerpts after withholding a generated draft.

**How did you use generative AI in the development work?**

AI assisted requirements analysis, code, tests, evaluation case drafting and presentation preparation. It also generates runtime answers. These are distinct uses. The case labels are not independent ground truth. The candidate should disclose the assistance, understand all components, and explain the source and execution checks used to validate outputs.

**How do you prevent a correct action from being applied to the wrong situation?**

Table extraction preserves column labels and leftmost conditions, and the prompt tells the model to retain them. Shorter chunks reduce unrelated content. Claim screening and human review remain necessary. A recorded early error combined found-card instructions with a disposal request; that motivated changes. The prototype does not claim to have solved conditional reasoning.

**What does a citation prove?**

It proves which passage was supplied and referenced. Source hashes identify the original file snapshot. Citation checks do not prove the passage entails the generated statement. NLI is a screening model and can fail. Reviewers must inspect actual claims and conditions against the source.

**Why these chunk sizes?**

The first larger grouping diluted specific requirements. The final target is about 110 narrative words, with 20-word overlap for oversized blocks, and table-row treatment with repeated conditions. This is empirical development tuning for a small local model, not a universal optimum. Exact token length, logical section boundaries and exception recall are the relevant tradeoffs.

**How do you handle follow-ups?**

Previous user questions resolve context; previous generated claims are not factual input. Follow-ups retrieve fresh evidence within the prior procedure when appropriate. A hypothetical repeating the same topic or procedure ID retains the prior situation; a different topic or ID starts a new one. A newly named task such as monthly testing keeps procedure scope without irrelevant overnight-storage terms. Session state isolates browser conversations. Ambiguous or long histories remain a limitation.

**How do you evaluate accuracy, relevance, completeness and conciseness?**

Separate retrieval from generation. Use passage-specific hit@5 and MRR for retrieval; fact groups and citations for diagnostics; word count for output length; and independent human scoring for substantive accuracy, relevance, completeness and conciseness. Count fallback/abstention separately and review critical errors independently of averages.

**Are the evaluation labels independent?**

No. They were AI-authored and source-checked. The challenge questions are a regression split, not a blind external benchmark after development inspection. A production decision needs independently authored and adjudicated labels and unseen scenarios.

**What happens when documents change or conflict?**

Changed file hashes stop startup and require rebuilding the local index. The demo does not automatically choose an authoritative policy when versions conflict. Production ingestion needs effective dates, owner approval, supersession rules, signed releases, regression checks and rollback.

**How do you handle missing external references?**

Only the supplied eleven files are evidence. Their links are not followed, and some are placeholders. The assistant should state insufficient support and direct the employee to the current approved procedure or supervisor. It must not synthesize the missing referenced policy from general banking knowledge.

**What is the privacy boundary?**

Runtime generation uses local model files; procedure content is not sent to a hosted inference API. The demo uses session memory and opt-in export without automatic persistent chat logging. Public model downloads occur during setup. These properties do not provide enterprise access control, comprehensive PII protection or an approved audit/retention policy.

**What does it cost and how does it scale?**

Local inference has no per-call hosted API fee, but uses laptop CPU, memory, power and setup storage. Those costs were not converted into dollar savings. Retrieval is inexpensive at this corpus size; generation dominates latency. A production comparison must measure an approved model on the same scenario set, including infrastructure cost, throughput, concurrency, cold starts and employee task completion.

**What would you improve first?**

First, independently review scenario labels and all high-impact instructions. Then compare stronger approved models, improve table-condition and exception retrieval, calibrate answer/abstention thresholds, and measure employee tasks against existing search. Before rollout, add identity, entitlements, authoritative versioning, redacted audit logging and operational controls.

**What should leadership approve now?**

The prototype demonstrates the architecture and provides measured engineering evidence. The next decision is a scoped validation effort with procedure owners, not an unqualified branch deployment. Use the final evaluation report to state what was observed and what remains unproven.

## Presentation discipline

Know the difference between the original document snapshot, extracted content, retrieved passages, evidence actually sent to the model, generated drafts, accepted outputs and independently validated facts. Do not call automatic proxy metrics “accuracy” without explaining their limitations. Do not hide source-only fallback as a generated success. State that no productivity or real-bank compliance claim was validated.
