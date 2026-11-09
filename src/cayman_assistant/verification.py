"""Claim-to-citation support screening; a fallible check, not proof of truth."""

from pathlib import Path
import re
import numpy as np


def claims(answer: str) -> list[dict]:
    """Bind sentence citations locally; allow a single shared paragraph footer.

    Explicit citations on one sentence cannot substantiate another sentence.
    A single footer may cover a whole paragraph, as the prompt permits.
    """
    results = []
    for paragraph in answer.split("\n"):
        paragraph = paragraph.strip(" -•*")
        if not paragraph:
            continue
        paragraph = re.sub(
            r"([.!?])\s+(\[S\d+\](?:\s*\[S\d+\])*)(?=\s+[A-Z]|\s*$)",
            lambda m: " " + m.group(2) + m.group(1),
            paragraph,
        )
        footer = re.search(r"(?:\s*\[S\d+\])+\s*[.!?]?\s*$", paragraph)
        shared = (
            re.findall(r"\[(S\d+)\]", footer.group())
            if footer and not re.search(r"\[S\d+\]", paragraph[: footer.start()])
            else []
        )
        protected = (
            paragraph.replace("U.S.", "US")
            .replace("e.g.", "for example")
            .replace("i.e.", "that is")
        )
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", protected)
        for sentence in sentences:
            labels = list(dict.fromkeys(re.findall(r"\[(S\d+)\]", sentence) or shared))
            plain = re.sub(r"\[S\d+\]", "", sentence).strip(" -•*")
            plain = re.sub(r"\s+([.!?,;])", r"\1", plain)
            plain = re.sub(
                r"^(?:According to (?:the )?(?:evidence|rules|procedure|procedures|provided (?:evidence|procedure)|source)|Based on (?:the )?(?:evidence|procedure|provided information)),?\s*",
                "",
                plain,
                flags=re.I,
            )
            plain = re.sub(
                r"^(?:The procedure (?:explicitly states|also mentions|states|says|specifies) that|Additionally,|Specifically,)\s*",
                "",
                plain,
                flags=re.I,
            )
            if re.fullmatch(
                r"(?:This|That) is (?:explicitly )?(?:stated|mentioned|provided) in the (?:evidence|procedure)\s*\.?",
                plain,
                re.I,
            ):
                continue
            if len(plain.split()) >= 3:
                results.append({"claim": plain, "labels": labels})
    return results


def canonical(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def source_windows(text: str) -> list[str]:
    text = text.replace("U.S.", "US")
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])|\n", text)
    prefix = text.split(" | ")[0] + " | " if " | " in text else ""
    windows = [text] + [" ".join(sentences[j : j + 2]) for j in range(len(sentences))]
    return list(
        dict.fromkeys(
            prefix + w if prefix and not w.startswith(prefix) else w for w in windows if w
        )
    )


class Verifier:
    model_id = "cross-encoder/nli-deberta-v3-small"

    def __init__(self, root: Path):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(
            str(root / "models" / "verifier"),
            device="cpu",
            max_length=512,
            local_files_only=True,
            trust_remote_code=False,
        )

    def check(self, answer: str, evidence: list[dict]) -> dict:
        by_label = {e["label"]: e for e in evidence}
        rows = claims(answer)
        if not rows:
            return {"passed": False, "claims": [], "reason": "no_claims"}
        pairs, bindings = [], []
        for index, row in enumerate(rows):
            claim_text = canonical(row["claim"])
            match = next(
                (
                    label
                    for label in row["labels"]
                    if label in by_label
                    and len(claim_text.split()) >= 5
                    and f" {claim_text} " in f" {canonical(by_label[label]['text'])} "
                ),
                None,
            )
            row["verbatim_support"] = bool(match)
            if match:
                windows = source_windows(by_label[match]["text"])
                quote = next(
                    (
                        w
                        for w in sorted(windows, key=len)
                        if f" {claim_text} " in f" {canonical(w)} "
                    ),
                    by_label[match]["text"],
                )
                row.update(
                    entailment=None,
                    contradiction=None,
                    supported=True,
                    support_method="verbatim_match",
                    supporting_label=match,
                    source_chunk_id=by_label[match].get("chunk_id"),
                    support_quote=quote,
                )
                continue
            for label in row["labels"]:
                if label in by_label:
                    for window in source_windows(by_label[label]["text"]):
                        pairs.append((window, row["claim"]))
                        bindings.append((index, label, window))
        scores = (
            np.asarray(self.model.predict(pairs, show_progress_bar=False, apply_softmax=True))
            if pairs
            else np.empty((0, 3))
        )
        # Published model label order: contradiction, entailment, neutral.
        for index, row in enumerate(rows):
            if row["verbatim_support"]:
                continue
            options = [
                (score, label, quote)
                for score, (row_index, label, quote) in zip(scores, bindings)
                if row_index == index
            ]
            best, label, quote = (
                max(options, key=lambda item: float(item[0][1]))
                if options
                else (np.array([0.0, 0.0, 1.0]), None, "")
            )
            row.update(
                entailment=round(float(best[1]), 4),
                contradiction=round(float(best[0]), 4),
                supported=bool(best[1] >= 0.55 and best[0] < 0.2),
                support_method="nli_screen",
                supporting_label=label,
                source_chunk_id=by_label[label].get("chunk_id") if label else None,
                support_quote=quote,
            )
        return {
            "passed": all(r["supported"] for r in rows),
            "claims": rows,
            "model": self.model_id,
            "entailment_threshold": 0.55,
            "limitation": "NLI and verbatim matches do not prove correctness or applicability to the user's situation.",
        }
