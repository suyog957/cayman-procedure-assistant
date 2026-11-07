# Independent evaluation rubric and pilot proposal

The included suite contains 30 single-turn procedure questions, four two-turn conversations, and six guardrail questions. The single-turn set has 19 development cases and 11 challenge cases. Labels were AI-authored from the supplied documents and source-checked through evidence locators. They are regression material, not an independently validated benchmark.

## Metrics and their interpretation

| Dimension | Automatic measure included | Required human evaluation |
|---|---|---|
| Retrieval | Evidence hit@5 and reciprocal rank@5 for an expected passage or equivalent labelled passages | Did the retrieved evidence contain all applicable conditions and exceptions? |
| Accuracy | Required-fact term-group coverage, citation labels, novel-number check, NLI screen | Is every substantive instruction correct for the stated situation? |
| Relevance | Retrieval ranking; displayed answer and evidence for inspection | Does the answer directly address the user's question without unrelated procedure steps? |
| Completeness | Required-fact coverage proxy | Are material qualifications, exceptions, warnings and escalations included? |
| Conciseness | Word count and a bounded output-token limit | Is the answer as short as possible while preserving necessary conditions? |
| Conversation | Four final-turn fact checks, context-resolution method, source procedure | Is the intended prior situation retained? Are topic switches and ambiguous follow-ups handled? |
| Reliability | Expected guardrail response statuses; evidence-only fallback count | Were unsupported instructions prevented? Were valid questions unnecessarily refused? |
| Experience | Measured latency for serial local requests; session controls | Can employees locate the right evidence and complete the information task efficiently? |

Hit@5 is the proportion of cases with at least one labelled relevant passage in the first five results. MRR@5 averages the reciprocal of the first relevant rank and assigns zero when no relevant passage is in the first five. These measure retrieval ordering, not response accuracy. The label locator can accept repeated equivalent passages in different sections of a procedure, which is disclosed in the details file.

The required-facts proxy checks whether at least one phrase from each required fact group occurs in a displayed generated answer. It can miss correct paraphrases and can pass a wrong answer containing expected words. A withheld draft or source-only fallback fails generated-answer fact coverage even if the displayed excerpts include the answer. This prevents inflating generated quality with fallback quotes.

Mechanical citation checks confirm labels refer to evidence supplied to the generator. They do not establish that the cited passage supports the answer. NLI is another model's screening signal, not ground truth. Raw evidence and drafts must be reviewed.

## Human scoring guide

Two reviewers should independently score responses without seeing the retrieval method/model label. They should consult the original supplied source and document disagreements. A third reviewer adjudicates disagreements about permissions, monetary amounts, deadlines, identities and exceptions.

| Score | Accuracy | Relevance | Completeness | Conciseness |
|---|---|---|---|---|
| 0 | Incorrect or unsupported instruction | Does not address the question | Missing the central requirement | Unusable, repetitive or misleadingly short |
| 1 | Material error or unverified claim | Significant irrelevant content | Missing a material condition/exception | Excessive detail or insufficient actionable context |
| 2 | Correct core answer; minor imprecision | Mostly focused | Most applicable requirements included | Readable with some avoidable detail |
| 3 | Fully supported for the stated situation | Direct and focused | All material conditions included | Minimal wording without losing meaning |

Mark any critical error separately from the average score: invented permission, reversed prohibition, wrong amount/deadline, missing identity requirement, incorrect exception, or unsupported transaction instruction. A good average cannot offset a critical safety error.

Record response outcome as one of: generated complete answer, generated partial answer, correct abstention, unnecessary abstention, source-only fallback, or incorrect generated answer. Report both quality among answered cases and coverage across all cases.

## Proposed release checks, not measured achievements

Before a limited pilot, build a substantially larger independent scenario set covering all procedures, table branches and high-impact exceptions. Hold back unseen scenarios and paraphrases. Include long conversations, new topics, conflicting/outdated versions, external references, malformed documents, prompt injection in retrieved content, permissions and source access controls.

Proposed gates for discussion with the business and validation teams:

- No critical unsupported instruction on the reviewed release suite; investigate every critical failure.
- At least 95% evidence hit@5 and 95% SME-confirmed factual correctness on answered in-scope cases, with explicit uncertainty intervals and per-procedure breakdowns.
- At least 90% materially complete answers, with refusal/fallback coverage reported separately.
- At least 95% appropriate handling of unsupported/ambiguous/adversarial cases.
- A p95 answer-time target agreed from employee tasks; a possible pilot target is 10 seconds on the selected deployment platform. The local CPU prototype does not claim to meet this target.
- Measurable improvement in time to find correct guidance and task success versus the existing search process, without worse critical-error rates.

These thresholds are proposed acceptance targets requiring business approval. The current small development suite does not establish these results or statistical confidence. Measure end-to-end behavior under realistic concurrency and record cold-start time separately.

## Human review record

Use `evaluation/human_review_template.csv` for independent review. No completed SME review is implied by including this template. Inspect every final raw response before the interview, particularly questions involving state-specific exceptions, multiple signatures, backup withholding and follow-up scope.
