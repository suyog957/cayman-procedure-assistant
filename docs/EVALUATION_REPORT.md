# Evaluation report

Final model: Qwen/Qwen3-4B-GGUF:Q4_K_M. All figures below are calculated from the saved final local run. The test suite uses AI-authored, source-checked labels and is not an independently adjudicated benchmark. Review the original sources and [the scoring rubric](../evaluation/REVIEW_RUBRIC.md) before interpreting these figures.

## Retrieval versus response quality

BM25 evidence hit@5: 90.0%; dense: 93.3%; hybrid plus reranking: 100.0%. Hybrid MRR@5 is 0.928. These use specific evidence locators and allow repeated equivalent relevant passages. They do not establish complete evidence retrieval or correct responses.

All required fact groups occur in 76.7% of the 30 ordinary generated-answer evaluations. Mean fact-group coverage is 76.7%. A source-only fallback fails the generated-answer proxy even when its excerpts contain the answer. Keyword proxies can miss valid paraphrases and pass incorrect statements containing expected words.

The output-screen pass rate is 74.3%. This is a combination of mechanical and support screening, not a correctness estimate. There are 6 source-only outcomes among 35 evaluated generated calls. Guardrail expected-status agreement is 100.0% on six deliberately selected cases; six cases do not establish general security effectiveness.

The version 2 engine attempted 9 bounded corrections and released 2 revised answers after the same checks. Each correction keeps the same evidence pack. The record retains rejected draft details, and the activity view reports a correction only when it occurred. Additional attempts can increase CPU response time; safety and coverage must be assessed together with that latency cost.

Serial local generated-call latency is p50 13.81s and p95 23.92s. First model load is excluded. Mean draft length is 28.0 words. Neither length nor speed establishes usefulness or completeness. Concurrent users, network deployments and cold starts were not benchmarked.

## Every ordinary case

| Case | Procedure | Response outcome | All-fact proxy | Diagnostic |
|---|---|---|---|---|
| N01 | PR1000 | answered | pass | fact proxy passed |
| N02 | PR1000 | answered | pass | fact proxy passed |
| N03 | PR1000 | evidence_only | miss | claim support screen |
| R01 | PR1263 | answered | pass | fact proxy passed |
| R02 | PR1263 | answered | pass | fact proxy passed |
| R03 | PR1263 | answered | pass | fact proxy passed |
| I01 | PR1277 | answered | pass | fact proxy passed |
| I02 | PR1277 | answered | pass | fact proxy passed |
| I03 | PR1277 | answered | pass | fact proxy passed |
| B01 | PR1779 | unsupported | miss | model abstention |
| B02 | PR1779 | answered | pass | fact proxy passed |
| B03 | PR1779 | answered | pass | fact proxy passed |
| S01 | PR1949 | answered | pass | fact proxy passed |
| S02 | PR1949 | answered | pass | fact proxy passed |
| S03 | PR1949 | evidence_only | miss | claim support screen |
| C01 | PR2306 | evidence_only | miss | missing fact group |
| C02 | PR2306 | answered | pass | fact proxy passed |
| A01 | PR2321 | answered | pass | fact proxy passed |
| A02 | PR2321 | answered | pass | fact proxy passed |
| A03 | PR2321 | evidence_only | miss | claim support screen |
| P01 | PR472 | answered | pass | fact proxy passed |
| P02 | PR472 | answered | pass | fact proxy passed |
| T01 | PR607 | evidence_only | miss | claim support screen |
| T02 | PR607 | answered | pass | fact proxy passed |
| M01 | PR63 | answered | pass | fact proxy passed |
| M02 | PR63 | answered | pass | fact proxy passed |
| M03 | PR63 | answered | pass | fact proxy passed |
| H01 | PR7554 | answered | pass | fact proxy passed |
| H02 | PR7554 | unsupported | miss | model abstention |
| H03 | PR7554 | answered | pass | fact proxy passed |

## Per-procedure view

| Procedure | Questions | All-fact proxy passes | Source-only fallbacks |
|---|---:|---:|---:|
| PR1000 | 3 | 2 | 1 |
| PR1263 | 3 | 3 | 0 |
| PR1277 | 3 | 3 | 0 |
| PR1779 | 3 | 2 | 0 |
| PR1949 | 3 | 2 | 1 |
| PR2306 | 2 | 1 | 1 |
| PR2321 | 3 | 2 | 1 |
| PR472 | 2 | 2 | 0 |
| PR607 | 2 | 1 | 1 |
| PR63 | 3 | 3 | 0 |
| PR7554 | 3 | 2 | 0 |

These small per-procedure counts are useful for finding weak areas, not statistical estimates of production accuracy. The corpus's largest document does not dominate the question count.

## Follow-ups and unsupported questions

Final-turn fact checks: F01.2: miss, F02.2: pass, F03.2: miss, F04.2: pass. Inspect the full resolved query, selected evidence and status in the raw details file. The coin-machine follow-up asking simply for a “control” can produce the task name while omitting the control level. The live runbook uses the clearer single-versus-dual-control question, while the original ambiguous regression question remains in the suite and its miss remains visible.

Guardrail cases cover unrelated content, a direct instruction attack, an unknown procedure, missing context, an obvious customer identifier, and unavailable current interest rates. Pattern checks are narrow. The suite does not establish defenses against indirect prompt injection, comprehensive privacy protection, source poisoning or enterprise authorization failures.

## Observed failure patterns and corrective choices

- A notary draft in an early run invented an exemption from other rules despite a correct main permission decision. Citation/term checks alone did not catch it. This motivated claim screening and explicit condition preservation.
- A metal-card draft borrowed instructions from a found-card scenario. Shorter passages and narrower evidence reduced distraction, but situation applicability still needs human review.
- Some correct paraphrases are withheld by the NLI screen. Literal substantive source matches use a direct support check; NLI is used for paraphrases. Neither proves applicability to the user's situation.
- A model changed “less than $2 million” into an inclusive threshold. A comparator guard and regression test now withhold such a draft. The number comparison check covers recognizable patterns, not general mathematical reasoning.
- An evidence pack can miss an exception even when top-five retrieval contains the general rule. Leading hits now recover the next same-section qualification or table-row continuation. Remote cross-references remain outside scope.
- Fact completeness and relevance remain imperfect. The application may omit a requested condition, refuse a valid question or add related but unnecessary detail. These are exposed in raw traces and the table above.

The retained initial 1.5B pipeline had 53.3% all-fact proxy coverage and p50 11.66s; the final pipeline has 76.7% and p50 13.81s. Model, prompts, evidence packing and screening changed between these runs, so this is an end-to-end iteration comparison, not an isolated causal model ablation.

On the same 30-question regression set, the previous version had 73.3% all-fact proxy coverage and 8 source-only outcomes; the current version has 76.7% and 6. The strict sales-boundary and savings-bond exception cases were recovered through bounded correction, while some other cases remain withheld or unnecessarily refused. Local timing and pipeline changes prevent treating this as an isolated model-performance experiment.

## Interpretation and next validation

Do not report these proxies as independently established accuracy. Have two operational SMEs independently score accuracy, relevance, completeness and conciseness, adjudicate disagreements, and mark critical errors separately. Use unseen scenarios, realistic branch tasks, source-version conflicts and long conversations. Measure answer coverage, correct abstention, unnecessary refusal, employee task success and time to correct guidance against existing search.

Proposed pilot gates are in the rubric and are not achieved enterprise service levels. This exercise demonstrates a measurable prototype with explicit limits; it does not justify unsupervised operational deployment.

Raw metrics: `artifacts/evaluation/metrics.json`. Retrieval rankings: `artifacts/evaluation/retrieval_details.json`. Answers, withheld drafts, sources, checks and timings: `artifacts/evaluation/answer_details.json`. Earlier experiments are retained separately under `artifacts/experiments/`.
