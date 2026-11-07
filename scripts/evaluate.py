"""Reproducible retrieval ablations and answer diagnostics, not an LLM judge.

Answer term matching is explicitly a proxy. Raw answers/evidence are retained
for human review; a matching answer can still be semantically wrong.
"""
from pathlib import Path
import argparse
import json
import sys
import time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cayman_assistant.assistant import Assistant, Turn, resolve_question
from cayman_assistant.retrieval import Retriever

parser = argparse.ArgumentParser()
parser.add_argument("--generate", action="store_true")
parser.add_argument("--limit", type=int)
parser.add_argument("--backend", choices=["qwen3", "qwen2.5"], default="qwen3")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
suite = json.loads((root / "evaluation" / "cases.json").read_text(encoding="utf-8"))
out_dir = root / "artifacts" / "evaluation"
out_dir.mkdir(parents=True, exist_ok=True)


def term_checks(answer, required):
    normalized = answer.lower()
    return [any(term.lower() in normalized for term in alternatives) for alternatives in required]


retriever = Retriever(root)
rows = []
for case in suite["cases"]:
    relevant = [c for c in retriever.chunks if c.doc_id == case["doc_id"] and case["evidence_contains"].lower() in c.text.lower()]
    if not relevant:
        raise ValueError("Unresolved evidence label: " + case["id"])
    relevant_ids = {c.chunk_id for c in relevant}
    for mode in ["bm25", "dense", "hybrid"]:
        start = time.perf_counter()
        hits = retriever.search(case["question"], k=5, mode=mode)
        ranks = [i + 1 for i, h in enumerate(hits) if h.chunk.chunk_id in relevant_ids]
        rows.append({"id": case["id"], "split": case["split"], "mode": mode,
                     "hit_at_5": bool(ranks), "reciprocal_rank_at_5": 1 / min(ranks) if ranks else 0,
                     "document_hit_at_5": any(h.chunk.doc_id == case["doc_id"] for h in hits),
                     "seconds": round(time.perf_counter() - start, 4),
                     "expected_chunk_ids": sorted(relevant_ids),
                     "retrieved_chunk_ids": [h.chunk.chunk_id for h in hits]})
summary = {"label_status": suite["label_status"], "retrieval": []}
for split in ["all", "development", "challenge"]:
    for mode in ["bm25", "dense", "hybrid"]:
        selected = [r for r in rows if r["mode"] == mode and (split == "all" or r["split"] == split)]
        summary["retrieval"].append({"split": split, "mode": mode, "n": len(selected),
                                     "hit_at_5": round(float(np.mean([r["hit_at_5"] for r in selected])), 4),
                                     "mrr_at_5": round(float(np.mean([r["reciprocal_rank_at_5"] for r in selected])), 4),
                                     "p50_seconds": round(float(np.median([r["seconds"] for r in selected])), 3),
                                     "p95_seconds": round(float(np.percentile([r["seconds"] for r in selected], 95)), 3)})
(out_dir / "retrieval_details.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
(out_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2), flush=True)
del retriever

if args.generate:
    assistant = Assistant(root, generator_backend=args.backend)
    answers = []
    def run_case(case, history=None, question=None):
        response = assistant.answer(question or case["question"], history)
        row = {"id": case["id"], "result": response.to_dict()}
        if "required" in case:
            # Excerpts shown after failed validation do not count as generated answers.
            checks = term_checks(response.answer, case["required"]) if response.status in {"answered", "partial"} else [False] * len(case["required"])
            row.update({"required_fact_checks": checks, "all_required_facts_proxy": all(checks),
                        "fact_coverage_proxy": sum(checks) / len(checks)})
        if "allowed_status" in case:
            row["expected_status_pass"] = response.status in case["allowed_status"]
        answers.append(row)
        # Checkpoint every answer to retain raw evidence if interrupted.
        (out_dir / "answer_details.json").write_text(json.dumps(answers, indent=2), encoding="utf-8")
        print(case["id"], response.status, response.metrics.get("total_seconds"), response.answer[:220], flush=True)
        return response
    for case in suite["cases"][:args.limit]:
        run_case(case)
    for case in suite["conversations"]:
        history = []
        for i, q in enumerate(case["questions"]):
            response = run_case(dict(case, id=f"{case['id']}.{i+1}", required=case["required"] if i else []), history, q) if i else assistant.answer(q, history)
            if response.sources:
                history.append(Turn(q, response.retrieval_query, response.sources[0]["doc_id"]))
    for case in suite["guardrails"]:
        run_case(case)
    factual = [r for r in answers if "all_required_facts_proxy" in r]
    ordinary = [r for r in factual if not r["id"].startswith("F")]
    generated = [r for r in answers if r["result"]["generator_used"]]
    valid = [r for r in generated if r["result"]["checks"].get("passed")]
    guardrails = [r for r in answers if "expected_status_pass" in r]
    latencies = [r["result"]["metrics"]["total_seconds"] for r in generated]
    summary["answers"] = {
        "model": assistant.generator.model_id, "ordinary_n": len(ordinary),
        "all_required_facts_proxy": round(float(np.mean([r["all_required_facts_proxy"] for r in ordinary])), 4),
        "fact_coverage_proxy": round(float(np.mean([r["fact_coverage_proxy"] for r in ordinary])), 4),
        "generated_n": len(generated), "output_screen_pass_rate": round(len(valid) / len(generated), 4),
        "mechanical_validation_pass_rate": round(float(np.mean([bool(r['result']['checks'].get('valid_citations') and r['result']['checks'].get('all_paragraphs_cited') and not r['result']['checks'].get('novel_numbers') and not r['result']['checks'].get('comparison_conflicts') and r['result']['checks'].get('word_count',999)>0 and r['result']['checks'].get('word_count',999)<=190) for r in generated])),4),
        "evidence_only_fallbacks": sum(r["result"]["status"] == "evidence_only" for r in generated),
        "guardrails_n": len(guardrails), "guardrail_expected_status_rate": round(float(np.mean([r["expected_status_pass"] for r in guardrails])), 4),
        "p50_seconds": round(float(np.median(latencies)), 2), "p95_seconds": round(float(np.percentile(latencies, 95)), 2),
        "mean_word_count": round(float(np.mean([r["result"]["checks"]["word_count"] for r in generated if 'word_count' in r['result']['checks']])), 1),
        "followup_fact_passes": {r["id"]: r["all_required_facts_proxy"] for r in factual if r["id"].startswith("F")},
        "limitations": "AI-authored labels; challenge set is not a blind holdout after inspection. Term matching and citation checks do not establish semantic correctness, relevance, or completeness. Human SME review remains required."
    }
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary["answers"], indent=2), flush=True)
    if hasattr(assistant.generator, "close"):
        assistant.generator.close()
