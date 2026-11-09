"""Mechanical answer checks scoped to the evidence actually cited by a claim."""

from decimal import Decimal
import re

from .verification import claims


def numeric_values(text: str) -> set[str]:
    text = re.sub(r"\[S\d+\]|\bPR\d+\b|^\s*\d+[.)]\s*", "", text, flags=re.M)
    return {
        format(Decimal(n.replace(",", "")).normalize(), "f")
        for n in re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", text)
    }


def comparisons(text: str) -> dict[str, set[str]]:
    number = r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)?"
    prefix = {
        "less than": "lt",
        "below": "lt",
        "under": "lt",
        "more than": "gt",
        "greater than": "gt",
        "over": "gt",
        "at most": "le",
        "up to": "le",
        "no more than": "le",
        "not more than": "le",
        "not less than": "ge",
        "at least": "ge",
    }
    found = {}

    def record(raw, scale, operator):
        multiplier = {"million": 1000000, "billion": 1000000000, "thousand": 1000}.get(
            (scale or "").lower(), 1
        )
        key = format((Decimal(raw.replace(",", "")) * multiplier).normalize(), "f")
        found.setdefault(key, set()).add(operator)

    phrases = "|".join(re.escape(p) for p in sorted(prefix, key=len, reverse=True))
    for match in re.finditer(r"\b(" + phrases + r")\s+" + number, text, re.I):
        record(match.group(2), match.group(3), prefix[match.group(1).lower()])
    for match in re.finditer(
        number + r"\s+(?:calendar |business )?(?:days? |months? |years? )?or (less|more)\b",
        text,
        re.I,
    ):
        record(match.group(1), match.group(2), "le" if match.group(3).lower() == "less" else "ge")
    return found


def validate_answer(answer: str, evidence: list[dict]) -> dict:
    by_label = {e["label"]: e["text"] for e in evidence}
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    paragraphs = [p for p in answer.split("\n") if p.strip() and len(p.split()) > 3]
    missing = [p for p in paragraphs if not re.search(r"\[S\d+\]", p)]
    rows = claims(answer)
    unattributed = [r["claim"] for r in rows if not r["labels"]]
    references = " ".join(by_label.values())
    novel_numbers = numeric_values(answer) - numeric_values(references)
    numeric_conflicts, boundary_conflicts = [], []
    for row in rows:
        # A number elsewhere in the evidence pack cannot substantiate the wrong citation.
        support = " ".join(by_label[label] for label in row["labels"] if label in by_label)
        new = numeric_values(row["claim"]) - numeric_values(support)
        if new:
            numeric_conflicts.append(
                {"claim": row["claim"], "labels": row["labels"], "numbers": sorted(new)}
            )
        source_ops, answer_ops = comparisons(support), comparisons(row["claim"])
        for value, operators in answer_ops.items():
            if value in source_ops and not operators <= source_ops[value]:
                boundary_conflicts.append(
                    {
                        "value": value,
                        "answer_operators": sorted(operators),
                        "source_operators": sorted(source_ops[value]),
                        "labels": row["labels"],
                    }
                )
    valid_citations = bool(cited) and cited <= by_label.keys()
    word_count = len(answer.split())
    passed = (
        valid_citations
        and not missing
        and bool(paragraphs)
        and bool(rows)
        and not unattributed
        and not novel_numbers
        and not numeric_conflicts
        and not boundary_conflicts
        and word_count <= 190
    )
    return {
        "valid_citations": bool(valid_citations),
        "all_paragraphs_cited": not missing and bool(paragraphs),
        "all_claims_attributed": bool(rows) and not unattributed,
        "unattributed_claims": unattributed,
        "novel_numbers": sorted(novel_numbers),
        "numeric_citation_conflicts": numeric_conflicts,
        "comparison_conflicts": boundary_conflicts,
        "word_count": word_count,
        "passed": bool(passed),
    }


def failure_reasons(checks: dict) -> list[str]:
    reasons = []
    if not checks.get("valid_citations") or not checks.get("all_claims_attributed"):
        reasons.append(
            "Attach the correct supplied source label to each factual sentence; do not borrow another sentence's citation."
        )
    if checks.get("novel_numbers") or checks.get("numeric_citation_conflicts"):
        reasons.append("Use only numeric values present in the passage you actually cite.")
    if checks.get("comparison_conflicts"):
        reasons.append("Preserve threshold wording exactly, including less than versus or less.")
    if not checks.get("claim_support", {}).get("passed", True):
        reasons.append(
            "Remove unsupported explanations; state only facts supported by the cited passage, preserving its conditions."
        )
    if checks.get("word_count", 0) > 190:
        reasons.append("Keep the answer concise, with at most three complete sentences.")
    return reasons or ["Use only supported source facts and include their source labels."]
