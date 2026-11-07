"""Conversational orchestration. Session memory supplies context, never facts."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import re
import time
import uuid

from .retrieval import Retriever, Hit
from .validation import validate_answer, failure_reasons
from .observability import ActivityTrace, grounding_summary, PIPELINE_VERSION

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

    activity: list[dict] = field(default_factory=list)
    grounding: dict = field(default_factory=dict)
    followups: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def resolve_question(question: str, history: list[Turn]) -> tuple[str, str | None, str]:
    scenario_followup = bool(re.match(r"^(?:and\s+)?what if\b", question, re.I))

    def with_situation():
        return f"Current question: {question}\nPrior situation: {history[-1].retrieval_query[-700:]}"

    explicit = re.search(r"\bPR\s*(\d+)\b", question, re.I)
    if explicit:
        doc_id = "PR" + explicit.group(1)
        query = with_situation() if history and history[-1].doc_id == doc_id and scenario_followup else question
        return query, doc_id, "explicit_procedure"
    named = [doc for doc, pattern in TOPICS.items() if re.search(pattern, question, re.I)]
    if len(named) == 1:
        # A hypothetical changes a condition within the prior situation, even
        # when it repeats the procedure name. A newly named task stands alone.
        if history and history[-1].doc_id == named[0] and FOLLOWUP.search(question):
            return with_situation() if scenario_followup else question, named[0], "followup"
        return question, None, "named_topic"
    if history and history[-1].doc_id and (FOLLOWUP.search(question) or re.search(r"\b(it|that|those|these|they|them|there|same)\b", question, re.I)):
        return with_situation(), history[-1].doc_id, "followup"
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

    def answer(self, question: str, history: list[Turn] | None = None, *, scope_doc_id: str | None = None,
               on_event=None, max_repairs: int = 1) -> Response:
        if max_repairs not in {0, 1}:
            raise ValueError("At most one grounded correction is permitted")
        started = time.perf_counter()
        trace = ActivityTrace(on_event)
        verified = False
        resolution = "not_resolved"
        history = history or []
        question = question.strip()
        trace.start("resolve", "Understand the request", "Checking scope, question context and input requirements.")

        def finish(response):
            response.trace_id = trace.request_id
            response.metrics.update(total_seconds=round(time.perf_counter() - started, 3),
                                    pipeline_version=PIPELINE_VERSION, context_resolution=resolution)
            response.grounding = grounding_summary(response.status, response.checks, response.sources, verified, resolution)
            trace.start("decision", "Choose the response", "Applying the observed evidence and validation results.")
            trace.finish("decision", response.grounding["decision"], "complete" if response.status == "answered" else "review")
            response.activity = trace.steps
            response.followups = suggested_followups(response)
            return response

        def stop(answer, status, query=None):
            trace.finish("resolve", answer, "blocked")
            return finish(Response(answer, status, question, query or question))

        if not question or len(question) > 1200:
            return stop("Please enter a procedure question of 1–1,200 characters.", "clarify")
        if INJECTION.search(question):
            return stop("I can help with questions grounded in the 11 supplied procedures. Please ask about a branch procedure.", "refused")
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{12,19}\b", question):
            return stop("Please remove customer identifiers and ask about the procedure using a hypothetical example.", "clarify")
        query, doc_id, resolution = resolve_question(question, history)
        if doc_id and doc_id not in TOPICS or scope_doc_id and scope_doc_id not in TOPICS:
            return stop("That procedure is not among the 11 supplied documents. Please select a supplied procedure or ask your supervisor for the current source.", "unsupported", query)
        named = [doc for doc, pattern in TOPICS.items() if re.search(pattern, question, re.I)]
        named_doc = doc_id if resolution == "explicit_procedure" else named[0] if len(named) == 1 else None
        if scope_doc_id and named_doc and named_doc != scope_doc_id:
            return stop(f"This question refers to {named_doc}, while the selected search scope is {scope_doc_id}. Choose All procedures or select {named_doc} to continue.", "clarify", query)
        if not history and not named and (len(question.split()) < 5 or re.search(r"\b(it|that|those|they|them)\b", question, re.I)):
            return stop("Which procedure or situation are you asking about? For example, notary services, identification, or coin-counting machines.", "clarify", query)
        doc_id = scope_doc_id or doc_id
        trace.finish("resolve", f"Resolved as {resolution.replace('_', ' ')}; searching {doc_id or 'all 11 procedures'}.",
                     query=query, scope=doc_id or "all")
        trace.start("integrity", "Verify the source snapshot", "Checking source files and the cached index for changes.")
        try:
            count = self.retriever.validate_snapshot()
        except (OSError, ValueError):
            trace.finish("integrity", "The source or indexed snapshot changed.", "blocked")
            return finish(Response("The source or index has changed. Reload the application and rebuild the index if needed before asking again.", "unsupported", question, query))
        verified = True
        trace.finish("integrity", f"{count} supplied procedure files match the indexed snapshot.", documents=count)
        trace.start("retrieve", "Find relevant procedure passages", "Running keyword search, semantic search and cross-encoder reranking.")
        search_start = time.perf_counter()
        hits = self.retriever.search(query, k=8, doc_id=doc_id)
        metrics = {"retrieval_seconds": round(time.perf_counter() - search_start, 3), "context_resolution": resolution}
        trace.finish("retrieve", f"Retrieved and ranked {len(hits)} candidate passages.", passages=len(hits))
        if not hits or hits[0].rerank < -2.0 or hits[0].cosine < .24:
            return finish(Response("I could not find sufficient support in the 11 supplied procedures. Please clarify the situation or consult the current procedure and your supervisor.",
                                   "unsupported", question, query, metrics=metrics))
        trace.start("evidence", "Assemble the evidence", "Keeping relevant source conditions and adjacent qualifications together.")
        evidence = evidence_from_hits(self.retriever.expand_qualifications(hits))
        doc_count = len({e['doc_id'] for e in evidence})
        trace.finish("evidence", f"Selected {len(evidence)} passages from {doc_count} procedure{'s' if doc_count != 1 else ''}.",
                     "complete" if evidence else "blocked",
                     source_labels=[e["label"] for e in evidence], expanded=sum(bool(e.get("expanded_from")) for e in evidence))
        if not evidence:
            return finish(Response("I could not find a complete supporting passage for this question. Please clarify the situation or consult the original procedure.",
                                   "unsupported", question, query, metrics=metrics))
        if not self.generator:
            return finish(Response("Relevant source passages are available below. Generative answering is not loaded.", "evidence_only", question, query, evidence, metrics=metrics))
        metrics.update(generation_seconds=0., verification_seconds=0., input_tokens=0, output_tokens=0,
                       generation_attempts=0, repair_attempted=False)
        rejected = []
        for attempt in range(max_repairs + 1):
            draft_key, check_key = ("draft", "validate") if not attempt else ("repair", "revalidate")
            trace.start(draft_key, "Draft the answer" if not attempt else "Revise the draft once",
                        "Generating from the selected source passages." if not attempt else "Applying failed-check feedback to the same evidence; the revision must pass the same checks.")
            draft_query = query
            if attempt:
                metrics["repair_attempted"] = True
                draft_query += "\n\nValidation guidance for one correction:\n" + "\n".join(failure_reasons(checks))
                draft_query += "\nCite each factual sentence. If the evidence is insufficient, output INSUFFICIENT_EVIDENCE."
            answer, generated = self.generator.generate(draft_query, evidence)
            metrics["generation_attempts"] += 1
            for key in ["generation_seconds", "input_tokens", "output_tokens"]:
                metrics[key] += generated.get(key, 0)
            trace.finish(draft_key, "The local model completed its output from the supplied evidence context.", output_tokens=generated.get("output_tokens"))
            if answer.strip().upper().startswith("INSUFFICIENT_EVIDENCE"):
                return finish(Response("I could not produce a sufficiently supported answer from the retrieved passages. Review the available sources or consult the current approved procedure.",
                                       "unsupported", question, query, evidence, self.generator.model_id, True, metrics,
                                       {"model_abstained": True, "passed": False, "rejected_attempts": rejected}))
            trace.start(check_key, "Check the answer" if not attempt else "Check the revised answer",
                        "Checking citation attribution, numeric values, thresholds and claim support.")
            check_start = time.perf_counter()
            checks = validate_answer(answer, evidence)
            if checks["passed"]:
                checks["claim_support"] = self.verifier.check(answer, evidence)
                checks["passed"] = checks["claim_support"]["passed"]
            metrics["verification_seconds"] += round(time.perf_counter() - check_start, 3)
            trace.finish(check_key, "All required output checks passed." if checks["passed"] else "The draft failed one or more required checks.",
                         "complete" if checks["passed"] else "review", passed=checks["passed"])
            if checks["passed"]:
                break
            rejected.append({"attempt": attempt + 1, "draft_answer": answer, "failure_reasons": failure_reasons(checks)})
        checks["rejected_attempts"] = rejected
        status = "answered"
        if not checks["passed"]:
            checks["withheld_draft"] = answer
            answer = "I could not validate the generated answer. Review these retrieved excerpts for the applicable conditions:\n\n" + "\n\n".join(
                f"> {e['text']} [{e['label']}]" for e in evidence[:2])
            status = "evidence_only"
        elif re.search(r"(?:(?:information|detail|answer|rate)(?: is| was|s are)? not (?:provided|specified|mentioned|available|included)|(?:cannot|could not) (?:answer|determine|find)|(?:evidence|procedure|document)[^.]{0,40}does not (?:provide|specify|mention)|no (?:information|specific (?:information|rate|details)))", answer, re.I):
            status = "partial"
        return finish(Response(answer, status, question, query, evidence, self.generator.model_id, True, metrics, checks))


def suggested_followups(response: Response) -> list[str]:
    """Curated questions are navigation suggestions, never canned answers."""
    if not response.sources or response.status not in {"answered", "partial", "evidence_only"}:
        return []
    doc = response.sources[0]["doc_id"]
    if doc == "PR63":
        return ["And is monthly testing done in single or dual control?", "What are the coin totals for monthly testing?"] if "overnight" in response.question.lower() else ["How often must the coin machine be balanced?", "What is the overnight coin storage limit?"]
    if doc == "PR1000":
        return ["What if the requester is physically present?", "What are the notary journal requirements?"] if "email" in response.retrieval_query.lower() else ["Can a notary charge a fee?", "What are the notary journal requirements?"]
    if doc == "PR1949":
        return ["What if they are eligible for The Private Bank Experience?", "Can the bank charge a savings bond redemption fee?"]
    return [f"What exceptions are described in {doc}?", f"What identification requirements are described in {doc}?"]
