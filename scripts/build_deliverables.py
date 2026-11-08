"""Build six editable slides, a matching PDF, reports and source-free package.

Deck content and measured figures come from the final corpus/evaluation files.
No source code, model files or evaluation internals enter the submission ZIP.
"""
from __future__ import annotations

from pathlib import Path
from html import escape
import json
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

import pymupdf as fitz
from presentation_deck import build_leadership_deck, DECK_BASENAME
from learning_notes import write_learning_pdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"
OUT.mkdir(exist_ok=True)
CORPUS = json.loads((ROOT / "artifacts/index/corpus_manifest.json").read_text())
METRICS = json.loads((ROOT / "artifacts/evaluation/metrics.json").read_text())
ANSWERS = json.loads((ROOT / "artifacts/evaluation/answer_details.json").read_text())
if "answers" not in METRICS:
    raise SystemExit("Complete the generative evaluation before building final deliverables")
A = METRICS["answers"]
generated_rows = [row for row in ANSWERS if row['result']['generator_used']]
# Aggregate from raw diagnostics so later-added guards are represented in the
# summary even when an earlier evaluator binary produced the same raw run.
mechanical_passes = [row for row in generated_rows if (
    row['result']['checks'].get('valid_citations') and row['result']['checks'].get('all_paragraphs_cited')
    and row['result']['checks'].get('all_claims_attributed',True) and not row['result']['checks'].get('numeric_citation_conflicts')
    and not row['result']['checks'].get('novel_numbers') and not row['result']['checks'].get('comparison_conflicts')
    and 0 < row['result']['checks'].get('word_count',999) <= 190)]
draft_lengths = [row['result']['checks']['word_count'] for row in generated_rows if 'word_count' in row['result']['checks']]
derived = {'mechanical_validation_pass_rate':round(len(mechanical_passes) / len(generated_rows),4),
           'mean_word_count':round(sum(draft_lengths)/len(draft_lengths),1),
           'draft_word_count_n':len(draft_lengths)}
for name,value in derived.items():
    if name in A and A[name] != value:
        raise ValueError('Saved evaluation summary disagrees with raw answers: '+name)
A.update(derived)
# Presentation builds consume accepted evidence; they never rewrite it.
BY_ID = {r["id"]: r for r in ANSWERS}
R = {r["mode"]: r for r in METRICS["retrieval"] if r["split"] == "all"}
browser_file=ROOT / "artifacts/browser_check.json"
browser_result=json.loads(browser_file.read_text()) if browser_file.exists() else {}
browser_ok=browser_result.get('pipeline_version')=='2.0' and all(browser_result.get(k) for k in ['welcome_loaded','followup_pass','export_includes_latest_turn','second_session_isolated','reset_pass','claim_map_pass','activity_record_pass','library_search_and_scope_pass'])
browser_summary=("The live browser integration check passed actual generation, an explicit single-versus-dual-control follow-up, source inspection, complete transcript export, independent browser sessions and reset. The browser reported no client errors. Results and screenshots are retained under `artifacts/`." if browser_ok else "Browser integration results are retained under `artifacts/` when the optional live browser check has completed.")
test_file=ROOT / 'artifacts/test_results.xml'
test_suites=list(ET.parse(test_file).getroot().iter('testsuite')) if test_file.exists() else []
test_total=sum(int(s.attrib.get('tests',0)) for s in test_suites)
test_failures=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in test_suites)
test_summary=f"The recorded automated test run contains {test_total} tests with {test_failures} failures/errors." if test_suites else "Run the automated tests using the README instructions."

NAVY = "3B3331"
TEAL = "D71E28"
LIGHT = "F9F7F6"
INK = "3B3331"
MUTED = "787070"
WHITE = "FFFFFF"
LINE = "E2DEDE"
GOLD = "FFCD41"


def pct(v):
    return f"{100*v:.1f}%"


def rgb(value):
    return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))


deck = build_leadership_deck(ROOT, CORPUS, METRICS)
# Keep the existing application download path current without changing its UI.
shutil.copy2(OUT / (DECK_BASENAME+".pdf"), OUT / "Cayman_Procedure_Assistant.pdf")


def markdown_html(markdown: str) -> str:
    """Small report formatter; no fenced source or active content is emitted."""
    lines, output, paragraph, table, list_open = markdown.splitlines(), [], [], [], False
    def inline(s):
        s = escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r"<span>\1</span>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
        return s
    def flush():
        nonlocal paragraph
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph = []
    def flush_table():
        nonlocal table
        if table:
            output.append("<table>")
            for i, row in enumerate(table):
                if re.match(r"^\s*\|?[\s:|\-]+\|?\s*$", row):
                    continue
                cells = row.strip().strip("|").split("|")
                tag = "th" if i == 0 else "td"
                output.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in cells) + "</tr>")
            output.append("</table>")
            table=[]
    in_fence = False
    for line in lines + [""]:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("|"):
            flush()
            table.append(line)
            continue
        flush_table()
        if line.startswith("#"):
            flush()
            if list_open:
                output.append("</ul>"); list_open=False
            level = min(4, len(line) - len(line.lstrip("#")))
            output.append(f"<h{level}>" + inline(line[level:].strip()) + f"</h{level}>")
        elif re.match(r"^(?:- |\d+\. )", line):
            flush()
            if not list_open:
                output.append("<ul>"); list_open=True
            output.append("<li>" + inline(re.sub(r"^(?:- |\d+\. )", "", line)) + "</li>")
        elif not line.strip():
            flush()
            if list_open:
                output.append("</ul>"); list_open=False
        else:
            paragraph.append(line)
    return "<html><body>" + "\n".join(output) + "</body></html>"


def report_pdf(markdown: str, output: Path):
    css = """body {font-family: sans-serif; font-size:10pt; color:#3b3331; line-height:1.35}
    h1{font-size:23pt;color:#3b3331} h2{font-size:15pt;color:#b01c24;margin-top:18pt}
    h3{font-size:12pt;color:#3b3331} p{margin-bottom:8pt} table{border-collapse:collapse;font-size:8.5pt;width:100%;margin:9pt 0}
    th{background:#e8eff4;color:#3b3331}td,th{border:0.4pt solid #ccd8e1;padding:5pt;vertical-align:top}
    li{margin-bottom:5pt} """
    story = fitz.Story(html=markdown_html(markdown), user_css=css)
    writer = fitz.DocumentWriter(str(output))
    media = fitz.paper_rect("a4")
    where = fitz.Rect(40,40,media.width-40,media.height-45)
    more=1
    while more:
        device=writer.begin_page(media)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()
    del writer
    doc=fitz.open(output)
    for i,page in enumerate(doc):
        page.insert_text((40,media.height-22), f"Branch Assist | Solution materials | {i+1}/{len(doc)}", fontsize=8, color=rgb(MUTED))
    doc.save(str(output)+".tmp", deflate=True)
    doc.close()
    Path(str(output)+".tmp").replace(output)


# Detailed solution overview: engineering evidence and limitations.
inventory = "\n".join(f"| {d['doc_id']} | {d['title'].split(' - PR')[0]} | {d['words']:,} | {d['chunks']} | {d['published'].replace('Published ','')} |" for d in CORPUS["documents"])
failed = [r["id"] for r in ANSWERS if r.get("all_required_facts_proxy") is False]
ordinary = [r for r in ANSWERS if r["id"] in {c["id"] for c in json.loads((ROOT/'evaluation/cases.json').read_text())["cases"]}]
status_counts = {status: sum(r['result']['status']==status for r in ordinary) for status in sorted({r['result']['status'] for r in ordinary})}
follow = ", ".join(k + ": " + ("pass" if v else "miss") for k,v in A["followup_fact_passes"].items())
overview = f"""# Detailed solution overview

Branch Assist is a locally runnable generative conversational solution over eleven operational procedures. It combines structured document processing, hybrid retrieval, evidence-based generation and inspectable output checks. The supporting materials include a six-slide solution presentation, measured evaluation, response traces and a timed demonstration guide.

## What was built and why

The system helps employees ask a procedure question, inspect the supporting passages and refine the situation conversationally. Retrieval-augmented generation was chosen to keep the evidence explicit and replaceable. Fine-tuning would not itself provide reliable citations or source version control. A local model removes the API-key dependency and makes the demonstration reproducible on this computer.

The final generator is {A['model']}. The Qwen3 model uses four-bit GGUF inference through llama.cpp on CPU. An earlier Qwen2.5 1.5B float32 baseline produced too many distracting details and withheld drafts; its complete results are retained separately. Model choice was evaluated empirically rather than inferred from published benchmarks.

The solution uses structure-aware HTML parsing, a JSONL passage store, BM25 lexical search, 384-dimensional MiniLM embeddings, reciprocal rank fusion, MiniLM cross-encoder reranking, bounded evidence, actual local generation, citation-local numeric checks and a DeBERTa NLI screening signal. The Wells Fargo–inspired version 2 workspace exposes a searchable procedure library and an Evidence desk with Evidence, Checks and Activity views. The workspace uses the supplied Cayman Bank documents as its knowledge collection.

Version 2 checks original sources and cached-index fingerprints on every supported request. It binds explicit citations to individual claims and records the source passage and evidence window behind each support check. A failed draft may receive one correction using the same evidence; the revised draft must pass the same checks or be withheld. Actual stage events and deterministic decision criteria are visible; the interface does not fabricate private model reasoning or a confidence percentage. Details are in [the version 2 design](docs/EXPERIENCE_V2.md).

## Solution presentation

The six-slide presentation covers the business objective and solution scope, document engineering, architecture and technology choices, user experience and follow-ups, quality evaluation, and the demonstration. Speaker notes support a 20-minute explanation followed by a 15-minute walkthrough. The presentation package contains solution materials and excludes implementation source.

## Input review and content preservation

The supplied corpus contains {sum(d['words'] for d in CORPUS['documents']):,} extracted words and 139 HTML tables including nested tables. It is indexed into {CORPUS['chunk_count']:,} passages. PR1779 is much larger than the other procedures and contains several account-type workflows.

| Procedure | Subject | Extracted words | Passages | Publication in supplied source |
|---|---|---:|---:|---|
{inventory}

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
| BM25 | {pct(R['bm25']['hit_at_5'])} | {R['bm25']['mrr_at_5']:.3f} | {R['bm25']['p50_seconds']:.3f} |
| Dense | {pct(R['dense']['hit_at_5'])} | {R['dense']['mrr_at_5']:.3f} | {R['dense']['p50_seconds']:.3f} |
| Hybrid + reranker | {pct(R['hybrid']['hit_at_5'])} | {R['hybrid']['mrr_at_5']:.3f} | {R['hybrid']['p50_seconds']:.3f} |

Retrieval hit@5 measures whether at least one labelled relevant passage was in the first five, not whether all applicable evidence was retrieved or an answer was correct. Repeated equivalent passages are allowed by the label locators.

| Answer diagnostic | Observed result |
|---|---|
| Ordinary questions with all required fact groups, automatic proxy | {pct(A['all_required_facts_proxy'])} of {A['ordinary_n']} |
| Mean required-fact group coverage, automatic proxy | {pct(A['fact_coverage_proxy'])} |
| Withheld drafts shown as source excerpts | {A['evidence_only_fallbacks']} of {A['generated_n']} generated evaluations |
| Expected guardrail response status | {pct(A['guardrail_expected_status_rate'])} of {A['guardrails_n']} |
| Serial local end-to-end p50 / p95, generated evaluations | {A['p50_seconds']:.2f}s / {A['p95_seconds']:.2f}s |
| Mean generated-draft word count | {A['mean_word_count']:.1f} |
| Bounded correction attempts / revised answers released | {A.get('repair_attempts',0)} / {A.get('repairs_released',0)} |
| Ordinary-question response outcome counts | {status_counts} |
| Follow-up final-turn fact proxies | {follow} |

The latency measurements exclude initial model loading and are from serial requests on the local CPU; they are not a throughput benchmark. Word count is a conciseness diagnostic, not proof of sufficient context. Term matching can pass wrong statements or miss correct paraphrases. NLI is fallible. These results must not be described as independently established accuracy.

Version 2 permits one correction after a failed draft, using the same evidence and check feedback. This increases the worst-case generation work. {A.get('repairs_released',0)} of {A.get('repair_attempts',0)} revised evaluated drafts passed release checks in this run. This is a screened-release count, not independent confirmation of the revisions' correctness.

Regression cases missing at least one required fact group, including source-only outcomes: {', '.join(failed) or 'none'}. Review their raw responses and evidence in `artifacts/evaluation/answer_details.json`. The report does not hide fallback as generated-answer success.

## Testing and observed engineering lessons

Focused automated tests cover table row/column condition preservation, nested table duplication, UTF-8, stable IDs, source revisions, real-corpus facts, follow-up scope, topic changes, session isolation, invalid citations, invented amounts, equivalent currency formatting, missing paragraph citations, stale sources, direct instruction attacks and obvious identifiers. Separate browser checks exercise the actual local app and save screenshots.

{test_summary} {browser_summary}

Initial failures combined rules from different situations and invented an exception rationale despite valid citations. Shorter passages, stronger reranking and a larger quantized generator reduced some weaknesses. Claim screening adds a conservative boundary but can withhold valid answers. A narrow evidence pack also trades lower distraction against missing exceptions elsewhere. These are documented tradeoffs, not solved problems.

## What a production version still needs

Independent SME-authored and adjudicated cases are the first priority. Evaluate accuracy, relevance, completeness and conciseness separately, and treat critical errors independently of averages. Include unseen scenarios, long conversations, cross-references, conditional tables, outdated/conflicting sources, malicious retrieved content and realistic employee tasks.

Production also needs authoritative effective policy versions, approved ingestion and rollback, employee SSO, document-level entitlements, approved model selection, redacted audit/retention, monitoring, rate limits, concurrency, timeouts, escalation and required enterprise review. Local processing and simple identifier patterns do not replace these controls.

The recommended next step is a scoped validation phase with procedure owners and model/platform teams. A pilot should depend on agreed critical-error, coverage, correctness, completeness and latency gates and measured employee benefit over existing search. No productivity, cost saving or enterprise-compliance achievement is claimed here.

## Where to find the deliverables

- `submission/{DECK_BASENAME}.pptx`: six editable slides and presenter notes.
- `submission/{DECK_BASENAME}.pdf`: matching slide PDF.
- `submission/Demo_Runbook.pdf`: timed presentation and demonstration guide.
- `submission/Recorded_Demo.pdf`: clearly labelled saved responses for rehearsal and backup.
- `submission/Presentation_Materials.zip`: allowlisted source-free presentation package.
- `docs/ARCHITECTURE.md`: component design, decisions, parameters and production path.
- `docs/ASSIGNMENT_REVIEW.md`: every requirement, acceptance evidence and three-day plan.
- `docs/AI_USE_AND_VALIDATION.md`: development/runtime AI use and validation boundaries.
- `docs/TECHNICAL_WALKTHROUGH.md`: technical design decisions and review questions.
- `evaluation/REVIEW_RUBRIC.md`: independent-review scoring and proposed release gates.
- `artifacts/index/`, `artifacts/evaluation/` and `artifacts/runtime_manifest.json`: reproducible source, measurement and model provenance.

Run the application using `README.md`. Inspect the recorded evidence, measured results and documented limitations when reviewing the solution.
"""
(ROOT / "SOLUTION_OVERVIEW.md").write_text(overview, encoding="utf-8")
report_pdf(overview, ROOT / "SOLUTION_OVERVIEW.pdf")

suite = json.loads((ROOT / "evaluation/cases.json").read_text())
case_map = {c["id"]: c for c in suite["cases"]}
case_table = []
for row in ordinary:
    result=row["result"]
    reason=("model abstention" if result["status"]=="unsupported" else
            "numeric/comparator check" if result["checks"].get("novel_numbers") or result["checks"].get("comparison_conflicts") else
            "claim support screen" if not result["checks"].get("claim_support",{}).get("passed",True) else
            "missing fact group" if not row.get("all_required_facts_proxy") else "fact proxy passed")
    case_table.append(f"| {row['id']} | {case_map[row['id']]['doc_id']} | {result['status']} | {'pass' if row.get('all_required_facts_proxy') else 'miss'} | {reason} |")
per_doc=[]
for doc in CORPUS["documents"]:
    relevant=[row for row in ordinary if case_map[row['id']]['doc_id']==doc['doc_id']]
    per_doc.append(f"| {doc['doc_id']} | {len(relevant)} | {sum(bool(row.get('all_required_facts_proxy')) for row in relevant)} | {sum(row['result']['status']=='evidence_only' for row in relevant)} |")
baseline_path=ROOT / "artifacts/experiments/qwen2_5_complete/metrics.json"
baseline=json.loads(baseline_path.read_text())["answers"] if baseline_path.exists() else None
comparison=(f"The retained initial 1.5B pipeline had {pct(baseline['all_required_facts_proxy'])} all-fact proxy coverage and p50 {baseline['p50_seconds']:.2f}s; the final pipeline has {pct(A['all_required_facts_proxy'])} and p50 {A['p50_seconds']:.2f}s. Model, prompts, evidence packing and screening changed between these runs, so this is an end-to-end iteration comparison, not an isolated causal model ablation." if baseline else "No initial comparison artifact is present.")
v1_path=ROOT / "artifacts/experiments/v1_complete_before_workspace_v2/metrics.json"
v1=json.loads(v1_path.read_text())["answers"] if v1_path.exists() else None
v2_comparison=(f"On the same 30-question regression set, the previous version had {pct(v1['all_required_facts_proxy'])} all-fact proxy coverage and {v1['evidence_only_fallbacks']} source-only outcomes; the current version has {pct(A['all_required_facts_proxy'])} and {A['evidence_only_fallbacks']}. The strict sales-boundary and savings-bond exception cases were recovered through bounded correction, while some other cases remain withheld or unnecessarily refused. Local timing and pipeline changes prevent treating this as an isolated model-performance experiment." if v1 else "")
evaluation_report=f"""# Evaluation report

Final model: {A['model']}. All figures below are calculated from the saved final local run. The test suite uses AI-authored, source-checked labels and is not an independently adjudicated benchmark. Review the original sources and [the scoring rubric](../evaluation/REVIEW_RUBRIC.md) before interpreting these figures.

## Retrieval versus response quality

BM25 evidence hit@5: {pct(R['bm25']['hit_at_5'])}; dense: {pct(R['dense']['hit_at_5'])}; hybrid plus reranking: {pct(R['hybrid']['hit_at_5'])}. Hybrid MRR@5 is {R['hybrid']['mrr_at_5']:.3f}. These use specific evidence locators and allow repeated equivalent relevant passages. They do not establish complete evidence retrieval or correct responses.

All required fact groups occur in {pct(A['all_required_facts_proxy'])} of the 30 ordinary generated-answer evaluations. Mean fact-group coverage is {pct(A['fact_coverage_proxy'])}. A source-only fallback fails the generated-answer proxy even when its excerpts contain the answer. Keyword proxies can miss valid paraphrases and pass incorrect statements containing expected words.

The output-screen pass rate is {pct(A.get('output_screen_pass_rate',A['mechanical_validation_pass_rate']))}. This is a combination of mechanical and support screening, not a correctness estimate. There are {A['evidence_only_fallbacks']} source-only outcomes among {A['generated_n']} evaluated generated calls. Guardrail expected-status agreement is {pct(A['guardrail_expected_status_rate'])} on six deliberately selected cases; six cases do not establish general security effectiveness.

The version 2 engine attempted {A.get('repair_attempts',0)} bounded corrections and released {A.get('repairs_released',0)} revised answers after the same checks. Each correction keeps the same evidence pack. The record retains rejected draft details, and the activity view reports a correction only when it occurred. Additional attempts can increase CPU response time; safety and coverage must be assessed together with that latency cost.

Serial local generated-call latency is p50 {A['p50_seconds']:.2f}s and p95 {A['p95_seconds']:.2f}s. First model load is excluded. Mean draft length is {A['mean_word_count']:.1f} words. Neither length nor speed establishes usefulness or completeness. Concurrent users, network deployments and cold starts were not benchmarked.

## Every ordinary case

| Case | Procedure | Response outcome | All-fact proxy | Diagnostic |
|---|---|---|---|---|
{chr(10).join(case_table)}

## Per-procedure view

| Procedure | Questions | All-fact proxy passes | Source-only fallbacks |
|---|---:|---:|---:|
{chr(10).join(per_doc)}

These small per-procedure counts are useful for finding weak areas, not statistical estimates of production accuracy. The corpus's largest document does not dominate the question count.

## Follow-ups and unsupported questions

Final-turn fact checks: {follow}. Inspect the full resolved query, selected evidence and status in the raw details file. The coin-machine follow-up asking simply for a “control” can produce the task name while omitting the control level. The live runbook uses the clearer single-versus-dual-control question, while the original ambiguous regression question remains in the suite and its miss remains visible.

Guardrail cases cover unrelated content, a direct instruction attack, an unknown procedure, missing context, an obvious customer identifier, and unavailable current interest rates. Pattern checks are narrow. The suite does not establish defenses against indirect prompt injection, comprehensive privacy protection, source poisoning or enterprise authorization failures.

## Observed failure patterns and corrective choices

- A notary draft in an early run invented an exemption from other rules despite a correct main permission decision. Citation/term checks alone did not catch it. This motivated claim screening and explicit condition preservation.
- A metal-card draft borrowed instructions from a found-card scenario. Shorter passages and narrower evidence reduced distraction, but situation applicability still needs human review.
- Some correct paraphrases are withheld by the NLI screen. Literal substantive source matches use a direct support check; NLI is used for paraphrases. Neither proves applicability to the user's situation.
- A model changed “less than $2 million” into an inclusive threshold. A comparator guard and regression test now withhold such a draft. The number comparison check covers recognizable patterns, not general mathematical reasoning.
- An evidence pack can miss an exception even when top-five retrieval contains the general rule. Leading hits now recover the next same-section qualification or table-row continuation. Remote cross-references remain outside scope.
- Fact completeness and relevance remain imperfect. The application may omit a requested condition, refuse a valid question or add related but unnecessary detail. These are exposed in raw traces and the table above.

{comparison}

{v2_comparison}

## Interpretation and next validation

Do not report these proxies as independently established accuracy. Have two operational SMEs independently score accuracy, relevance, completeness and conciseness, adjudicate disagreements, and mark critical errors separately. Use unseen scenarios, realistic branch tasks, source-version conflicts and long conversations. Measure answer coverage, correct abstention, unnecessary refusal, employee task success and time to correct guidance against existing search.

Proposed pilot gates are in the rubric and are not achieved enterprise service levels. Independent assessment and deployment controls are required before operational use.

Raw metrics: `artifacts/evaluation/metrics.json`. Retrieval rankings: `artifacts/evaluation/retrieval_details.json`. Answers, withheld drafts, sources, checks and timings: `artifacts/evaluation/answer_details.json`. Earlier experiments are retained separately under `artifacts/experiments/`.
"""
(ROOT / "docs/EVALUATION_REPORT.md").write_text(evaluation_report,encoding="utf-8")
report_pdf(evaluation_report,ROOT / "docs/EVALUATION_REPORT.pdf")
report_pdf((ROOT / "docs/SOLUTION_WALKTHROUGH.md").read_text(encoding="utf-8"), OUT / "Demo_Runbook.pdf")

transcript = ["# Recorded demonstration responses", "These are saved outputs from the final local evaluation, not a live session. Sources, status and elapsed time are preserved. Automatic screening does not guarantee correctness; inspect the applicable procedure."]
for case_id in ["M01", "F01.2", "N01", "F02.2", "S01", "F03.2", "F04.2", "N03", "G01", "G04", "G06"]:
    row=BY_ID[case_id]; result=row["result"]
    transcript += [f"## {case_id}: {result['question']}", f"Status: {result['status']} | Model: {result.get('model') or 'generation not used'} | Elapsed: {result['metrics'].get('total_seconds','not applicable')} seconds", result["answer"]]
    for source in result["sources"]:
        transcript += [f"### [{source['label']}] {source['doc_id']} — {source['section']}", source["published"], source["text"]]
transcript_text="\n\n".join(transcript)
(ROOT / "artifacts/recorded_demo.md").write_text(transcript_text, encoding="utf-8")
report_pdf(transcript_text, OUT / "Recorded_Demo.pdf")
write_learning_pdf(ROOT, OUT / "Presenter_Notes.pdf")

(OUT / "README.txt").write_text(
    "CAYMAN PROCEDURE ASSISTANT — PRESENTATION MATERIALS\n\n"
    "Six-slide deck with speaker notes; matching PDF; timed runbook; recorded demonstration backup.\n"
    "No implementation source or model files are included.\n"
    "Recorded responses are saved outputs, not a live demonstration.\n"
    "AI assisted development and runtime answering. Regression labels are AI-authored/source-checked, not independently adjudicated.\n"
    "See the solution walkthrough for the presentation flow and demonstration sequence.\n", encoding="utf-8")
allowlist=[DECK_BASENAME+".pptx",DECK_BASENAME+".pdf","Demo_Runbook.pdf","Recorded_Demo.pdf","Presenter_Notes.pdf","README.txt"]
with zipfile.ZipFile(OUT / "Presentation_Materials.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in allowlist:
        archive.write(OUT / name, name)
with zipfile.ZipFile(OUT / "Presentation_Materials.zip") as archive:
    if sorted(archive.namelist()) != sorted(allowlist):
        raise ValueError("Unexpected submission archive contents")
print(json.dumps({"slides":len(deck.prs.slides),"files":[str(OUT/name) for name in allowlist],
                  "overview":str(ROOT / "SOLUTION_OVERVIEW.md"),"archive":"Presentation_Materials.zip"},indent=2))
