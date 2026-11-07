"""Conversational orchestration. Session memory supplies context, never facts."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from decimal import Decimal
import re
import time
import uuid

from .retrieval import Retriever, Hit

TOPICS = {
    "PR1000": r"notar|notary|notaries",
    "PR1263": r"record hold|destruct|shred|stored records|metal card|plastic card",
    "PR1277": r"primary (?:id|identification)|secondary (?:id|identification)|driver.?s licen|face covering|digital id",
    "PR1779": r"estate|receivership|girl scout|government entit|business trust|pension|profit.sharing",
    "PR1949": r"savings bond|series (?:e|ee|i) bond|redeem.*bond",
    "PR2306": r"statement cop|copy request|copies of|copy of.*statement|verification of deposit",
    "PR2321": r"approv|override|bsa.*exception|exception.*bsa",
    "PR472": r"payoff|paydown|payment maintenance|due date|deferral|re.age",
    "PR607": r"taxpayer|\btin\b|backup withholding|w.?8ben|w.?9\b",
    "PR63": r"coin.counting|coin machine|weekly balanc|monthly test",
    "PR7554": r"shipment|courier|armored transport|cash in transit",
}
FOLLOWUP = re.compile(r"^(and\b|what (?:about|if|else)\b|how (?:about|long|often)\b|where\b|do (?:i|we|they) need\b|is (?:it|that|this)\b|can (?:it|they|i|we)\b|does (?:it|that|this)\b)", re.I)
INJECTION = re.compile(r"ignore (?:all |the |your |previous )*(?:instructions|rules|prompt)|(?:reveal|show|print).{0,25}(?:system prompt|api key|secret)|act as (?:a |an )?(?:system|developer)|<\|im_start\|>", re.I)


@dataclass
class Turn:
    question: str
    retrieval_query: str
    doc_id: str | None


@dataclass
class Response:
    answer: str
    status: str
    question: str
    retrieval_query: str
    sources: list[dict] = field(default_factory=list)
    model: str | None = None
    generator_used: bool = False
    metrics: dict = field(default_factory=dict)
    checks: dict = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self):
        return asdict(self)


def resolve_question(question: str, history: list[Turn]) -> tuple[str, str | None, str]:
    explicit = re.search(r"\bPR\s*(\d+)\b", question, re.I)
    if explicit:
        return question, "PR" + explicit.group(1), "explicit_procedure"
    named = [doc for doc, pattern in TOPICS.items() if re.search(pattern, question, re.I)]
    if len(named) == 1:
        # Carry a previous scenario when the follow-up names the same topic.
        if history and history[-1].doc_id == named[0] and FOLLOWUP.search(question):
            # A newly named task needs its own evidence; retain procedure scope
            # without diluting the new task with the previous task's keywords.
            return question, named[0], "followup"
        return question, None, "named_topic"
    if history and history[-1].doc_id and (FOLLOWUP.search(question) or re.search(r"\b(it|that|those|these|they|them|there|same)\b", question, re.I)):
        return f"Current question: {question}\nPrior situation: {history[-1].retrieval_query[-700:]}", history[-1].doc_id, "followup"
    return question, None, "standalone"


def evidence_from_hits(hits: list[Hit], max_chunks: int = 3, max_words: int = 520) -> list[dict]:
    evidence, words = [], 0
    for hit in hits:
        c = hit.chunk
        if evidence and hit.rerank < max(-2.0, hits[0].rerank - 1.5):
            continue
        if c.kind == "table_header":
            continue
        # Avoid spending the small local model's context on near-duplicates.
        if any(c.text in e["text"] or e["text"] in c.text for e in evidence):
            continue
        count = len(c.text.split())
        if words + count > max_words and evidence:
            continue
        evidence.append({"label": f"S{len(evidence) + 1}", "chunk_id": c.chunk_id,
                         "doc_id": c.doc_id, "title": c.title, "published": c.published,
                         "section": c.section, "source_file": c.source_file,
                         "source_sha256": c.source_sha256, "anchor": c.anchor,
                         "text": c.text, "table_id": c.table_id, "row_id": c.row_id,
                         "expanded_from": hit.expanded_from,
                         "retrieval": {"bm25": round(hit.bm25, 4), "cosine": round(hit.cosine, 4),
                                       "rerank": round(hit.rerank, 4)}})
        words += count
        if len(evidence) >= max_chunks:
            break
    return evidence


def validate_answer(answer: str, evidence: list[dict]) -> dict:
    valid = {e["label"] for e in evidence}
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    paragraphs = [p for p in answer.split("\n") if p.strip() and len(p.split()) > 3]
    missing = [p for p in paragraphs if not re.search(r"\[S\d+\]", p)]
    # This is a narrow mechanical check, not semantic entailment verification.
    references = " ".join(e["text"] for e in evidence)
    def nums(t):
        t = re.sub(r"\[S\d+\]|\bPR\d+\b|^\s*\d+[.)]\s*", "", t, flags=re.M)
        return {format(Decimal(n.replace(",", "")).normalize(), "f")
                for n in re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", t)}
    novel_numbers = nums(answer) - nums(references)
    def comparisons(text):
        number = r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)?"
        prefix = {"less than":"lt", "below":"lt", "under":"lt", "more than":"gt", "greater than":"gt", "over":"gt",
                  "at most":"le", "up to":"le", "no more than":"le", "not more than":"le",
                  "not less than":"ge", "at least":"ge"}
        found = {}
        def record(raw, scale, operator):
            multiplier = {"million": 1000000, "billion": 1000000000, "thousand": 1000}.get((scale or "").lower(), 1)
            key = format((Decimal(raw.replace(",", "")) * multiplier).normalize(), "f")
            found.setdefault(key, set()).add(operator)
        phrases = "|".join(re.escape(p) for p in sorted(prefix, key=len, reverse=True))
        for match in re.finditer(r"\b(" + phrases + r")\s+" + number, text, re.I):
            record(match.group(2), match.group(3), prefix[match.group(1).lower()])
        for match in re.finditer(number + r"\s+(?:calendar |business )?(?:days? |months? |years? )?or (less|more)\b", text, re.I):
            record(match.group(1), match.group(2), "le" if match.group(3).lower() == "less" else "ge")
        return found
    source_comparisons, answer_comparisons = comparisons(references), comparisons(answer)
    comparison_conflicts = [{"value": number, "answer_operators": sorted(operators),
                             "source_operators": sorted(source_comparisons[number])}
                            for number, operators in answer_comparisons.items()
                            if number in source_comparisons and not operators <= source_comparisons[number]]
    return {"valid_citations": bool(cited) and cited <= valid,
            "all_paragraphs_cited": not missing and bool(paragraphs),
            "novel_numbers": sorted(novel_numbers), "comparison_conflicts": comparison_conflicts, "word_count": len(answer.split()),
            "passed": bool(cited) and cited <= valid and not missing and not novel_numbers and not comparison_conflicts and len(answer.split()) <= 190}


class Assistant:
    def __init__(self, root: Path, load_generator: bool = True, generator_backend: str = "qwen3"):
        self.root = root
        self.retriever = Retriever(root)
        self.generator = None
        self.verifier = None
        if load_generator:
            from .generation import QuantizedGenerator, TransformerGenerator
            from .verification import Verifier
            if generator_backend not in {"qwen3", "qwen2.5"}:
                raise ValueError("Unknown generator backend")
            self.generator = (QuantizedGenerator if generator_backend == "qwen3" else TransformerGenerator)(root)
            self.verifier = Verifier(root)

    def answer(self, question: str, history: list[Turn] | None = None) -> Response:
        started = time.perf_counter()
        history = history or []
        question = question.strip()
        if not question or len(question) > 1200:
            return Response("Please enter a procedure question of 1–1,200 characters.", "clarify", question, question)
        if INJECTION.search(question):
            return Response("I can help with questions grounded in the 11 supplied procedures. Please ask about a branch procedure.", "refused", question, question)
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{12,19}\b", question):
            return Response("Please remove customer identifiers and ask about the procedure using a hypothetical example.", "clarify", question, question)
        query, doc_id, resolution = resolve_question(question, history)
        if doc_id and doc_id not in TOPICS:
            return Response("That procedure is not among the 11 supplied documents. Please select a supplied procedure or ask your supervisor for the current source.", "unsupported", question, query)
        if not history and not any(re.search(p, question, re.I) for p in TOPICS.values()) and (len(question.split()) < 5 or re.search(r"\b(it|that|those|they|them)\b", question, re.I)):
            return Response("Which procedure or situation are you asking about? For example, notary services, identification, or coin-counting machines.", "clarify", question, query)
        search_start = time.perf_counter()
        hits = self.retriever.search(query, k=8, doc_id=doc_id)
        retrieval_seconds = time.perf_counter() - search_start
        metrics = {"retrieval_seconds": round(retrieval_seconds, 3), "context_resolution": resolution}
        # Reranker logits and cosine are signals, not calibrated probabilities.
        # Initial development thresholds; report coverage and abstention separately.
        if not hits or hits[0].rerank < -2.0 or hits[0].cosine < .24:
            metrics["total_seconds"] = round(time.perf_counter() - started, 3)
            return Response("I could not find sufficient support in the 11 supplied procedures. Please clarify the situation or consult the current procedure and your supervisor.",
                            "unsupported", question, query, metrics=metrics)
        evidence = evidence_from_hits(self.retriever.expand_qualifications(hits))
        if not self.generator:
            return Response("Relevant source passages are available below. Generative answering is not loaded.", "evidence_only", question, query, evidence, metrics=metrics)
        answer, generation_metrics = self.generator.generate(query, evidence)
        metrics.update(generation_metrics)
        if answer.strip().upper().startswith("INSUFFICIENT_EVIDENCE"):
            metrics["total_seconds"] = round(time.perf_counter() - started, 3)
            return Response("The retrieved passages do not provide the information needed to answer this question. Please consult the current approved source or your supervisor.",
                            "unsupported", question, query, evidence, self.generator.model_id, True, metrics,
                            {"model_abstained": True, "passed": False})
        checks = validate_answer(answer, evidence)
        if checks["passed"]:
            check_start = time.perf_counter()
            checks["claim_support"] = self.verifier.check(answer, evidence)
            metrics["verification_seconds"] = round(time.perf_counter() - check_start, 3)
            checks["passed"] = checks["passed"] and checks["claim_support"]["passed"]
        status = "answered"
        if not checks["passed"]:
            checks["withheld_draft"] = answer
            # Never disguise a quote as a successfully generated answer.
            answer = "I could not validate the generated answer. Review these retrieved excerpts for the applicable conditions:\n\n" + "\n\n".join(
                f"> {e['text']} [{e['label']}]" for e in evidence[:2])
            status = "evidence_only"
        elif re.search(r"(?:(?:information|detail|answer|rate)(?: is| was|s are)? not (?:provided|specified|mentioned|available|included)|(?:cannot|could not) (?:answer|determine|find)|(?:evidence|procedure|document)[^.]{0,40}does not (?:provide|specify|mention)|no (?:information|specific (?:information|rate|details)))", answer, re.I):
            status = "partial"
        metrics["total_seconds"] = round(time.perf_counter() - started, 3)
        return Response(answer, status, question, query, evidence, self.generator.model_id, True, metrics, checks)
