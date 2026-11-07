# Silent tool walkthrough — readable edition

Actual UI only, with double-density lossless PNG capture. Descriptions remain in a large bottom panel; focus zooms and normal-speed interactions are followed by deliberate reading holds. Only idle processing waits may be cut. No audio, narration or slides.

| Time | Step | Bottom description | Reading hold |
|---|---|---|---|
| 00:00 | Start with a procedure question | Start with a question or one of the guided scenarios. The sidebar controls which of the 11 supplied procedures the assistant can search. | 9.9s |
| 00:12 | Ask about the coin-machine overnight limit | Ask about the overnight coin limit. The assistant answers $5,250 and cites PR63; use the citation to check the original rule. | 10.0s |
| 00:41 | Open the citation and read the exact passage | Open the citation beneath the answer. The Evidence desk selects the exact source passage, including the conditions around the overnight limit. | 14.4s |
| 01:01 | Inspect the source identity | Expand Source provenance to inspect the document, passage ID and source fingerprint. A matching hash identifies the supplied snapshot, rather than certifying current policy. | 13.9s |
| 01:19 | Inspect how the passage matched | Inspect the retrieval signals for this passage. BM25, semantic similarity and reranker scores describe matching; they are not probabilities that the answer is correct. | 12.0s |
| 01:38 | Download the original procedure | Download the original procedure when you need more context. The full supplied HTML document remains available alongside the short answer. | 10.0s |
| 01:56 | Check each statement against its cited source | Open Checks to see how each statement maps to its cited evidence. Citation, numeric and support screens are inspectable, but can still miss errors. | 19.7s |
| 02:20 | Follow the actual execution steps | Activity shows the actions that actually ran, with their timings. Follow retrieval, evidence assembly, drafting and validation through the release decision. | 18.2s |
| 02:42 | Export the evidence record for one answer | Open the technical record and download the selected answer's evidence. Trace identity, model, question resolution, token counts and checks travel with the record. | 12.8s |
| 03:00 | Ask a follow-up about monthly testing | Ask a follow-up about monthly testing. The assistant keeps the procedure context, retrieves fresh evidence and answers that this task uses single control. | 12.3s |
| 03:25 | Verify the follow-up against its own passage | Select the follow-up's citation to inspect the testing passage. This task has its own evidence; the overnight-storage passage is not reused as proof. | 14.5s |
| 03:45 | Switch from coin machines to savings-bond fees | Name a new topic: savings-bond redemption fees. The source changes from coin-machine procedure PR63 to savings-bond procedure PR1949. | 10.4s |
| 04:09 | Find a procedure in the library | Search the Procedure library for notary services. Inspect the matching document, then use it in the workspace to restrict retrieval to that procedure. | 10.0s |
| 04:27 | See document scope enforced | A coin-machine question conflicts with the selected notary scope. The assistant asks for a scope change and does not reuse an earlier source. | 10.0s |
| 04:50 | Ask whether an emailed document can be notarized | Ask whether an emailed document can be notarized. The supplied procedure prohibits it, even when the requester is physically present; inspect the citation. | 10.0s |
| 05:20 | Refine the situation: the requester is present | Refine the scenario by saying the requester is present. The follow-up must retain the original emailed-document condition and preserve the source's prohibition. | 12.0s |
| 05:46 | Ask about an account open less than 12 months | Ask about an account open less than 12 months. Read the $1,000 daily aggregate redemption limit together with the procedure's eligibility conditions. | 14.0s |
| 06:27 | Ask about The Private Bank Experience exception | Ask about The Private Bank Experience exception. In this recorded run, one correction still failed validation, so the draft is withheld and original passages remain available. | 14.0s |
| 06:57 | Review the outcome, give feedback and export | Inspect the failed check, mark the response Needs review and export the investigation. The download includes the conversation, evidence, checks, activity and feedback. | 14.9s |
| 07:19 | Reset the conversation and test missing context | Start a new investigation and ask an ambiguous question. Without the earlier situation, the assistant requests context and shows no borrowed evidence. | 10.0s |
| 07:40 | Ask a question outside the supplied documents | Ask about tomorrow's weather. The supplied procedures cannot support that request, so the assistant reports insufficient evidence and does not invent a sourced answer. | 10.0s |
| 08:00 | Ask about an unavailable procedure | Ask about a procedure that is not in the collection. The assistant identifies the missing source instead of inventing its requirements. | 10.0s |
| 08:20 | See an obvious instruction attack rejected | Try an obvious direct instruction attack. The request is rejected by a narrow pattern guard; this example does not establish comprehensive security protection. | 10.0s |
| 08:40 | Inspect the recorded evaluation | Open Evaluation to inspect the recorded results. Evidence retrieval, generated-answer fact coverage and withheld drafts are separate measures, each with stated limitations. | 20.4s |
| 09:04 | Download the reports and presentation | Download the evaluation report, detailed solution overview and presentation. These materials preserve the design, measured results and limitations for deeper review. | 12.9s |
