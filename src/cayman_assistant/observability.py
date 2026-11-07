"""Observable execution events and factual decision summaries, never model thoughts."""
from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Callable
from uuid import uuid4

PIPELINE_VERSION = "2.0"


class ActivityTrace:
    def __init__(self, callback: Callable[[dict], None] | None = None):
        self.request_id = uuid4().hex[:12]
        self.started = perf_counter()
        self.steps: list[dict] = []
        self.callback = callback
        self._starts = {}

    def start(self, key: str, label: str, detail: str):
        self._starts[key] = perf_counter()
        self.steps.append({"key": key, "label": label, "state": "running", "detail": detail,
                           "elapsed_seconds": 0.0})
        self._publish(self.steps[-1])

    def finish(self, key: str, detail: str, state: str = "complete", **data):
        step = next(s for s in reversed(self.steps) if s["key"] == key)
        step.update(state=state, detail=detail, elapsed_seconds=round(perf_counter() - self._starts[key], 3), **data)
        self._publish(step)

    def _publish(self, step: dict):
        if self.callback:
            self.callback({"request_id": self.request_id, **deepcopy(step)})


def grounding_summary(status: str, checks: dict, sources: list[dict], verified: bool, resolution: str) -> dict:
    """Explain the release decision from actual evidence/checks, not generated rationale."""
    claims = checks.get("claim_support", {}).get("claims", [])
    rules = [
        ("citations", "Citation labels", checks.get("valid_citations"), "References point to supplied evidence."),
        ("attribution", "Claim attribution", checks.get("all_claims_attributed"), "Factual statements have an associated citation."),
        ("numbers", "Numeric values", None if "novel_numbers" not in checks else not checks["novel_numbers"] and not checks.get("numeric_citation_conflicts"), "Amounts and numeric literals match their cited passages."),
        ("boundaries", "Threshold wording", None if "comparison_conflicts" not in checks else not checks["comparison_conflicts"], "Recognized strict and inclusive boundaries are preserved."),
        ("support", "Claim support", checks.get("claim_support", {}).get("passed"), "Verbatim matching or NLI screening checks cited support."),
    ]
    rule_rows = [{"key": key, "label": label, "state": "not_run" if passed is None else "passed" if passed else "failed", "detail": detail}
                 for key, label, passed, detail in rules]
    if status in {"answered", "partial"}:
        decision = "The answer was released after citation, numeric, threshold and claim-support screening."
    elif status == "evidence_only" and not checks:
        decision = "Source passages are available; generative answering was not used for this request."
    elif status == "evidence_only":
        decision = "The generated answer was withheld; the original source passages remain available for review."
    elif status == "clarify":
        decision = "More context is needed before retrieving or answering safely."
    elif checks.get("model_abstained"):
        decision = "No answer was released because the model could not establish sufficient support."
    else:
        decision = "The request did not meet the source or input requirements for an answer."
    return {"decision": decision, "rules": rule_rows, "claims_checked": len(claims),
            "claims_supported": sum(bool(c.get("supported")) for c in claims),
            "source_files_verified_at_request": verified, "evidence_passages": len(sources),
            "procedure_ids": list(dict.fromkeys(s["doc_id"] for s in sources)),
            "context_resolution": resolution,
            "limitation": "Automatic support checks are fallible; they are not calibrated confidence or independent correctness validation."}
