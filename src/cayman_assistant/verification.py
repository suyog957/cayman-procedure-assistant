"""Claim-level NLI signal. This classifier is fallible, not proof of truth."""
from pathlib import Path
import re
import numpy as np


def claims(answer: str) -> list[dict]:
    results = []
    for paragraph in answer.split("\n"):
        labels = re.findall(r"\[(S\d+)\]", paragraph)
        plain = re.sub(r"\[S\d+\]", "", paragraph).strip(" -•*")
        if not plain:
            continue
        # Do not split U.S., decimals, abbreviations, or phone numbers.
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", plain.replace("U.S.", "US"))
        for sentence in sentences:
            # Attribution is display language, not part of the procedural claim.
            # Leaving it in makes an NLI model label otherwise identical facts
            # neutral because the premise does not discuss 'the evidence'.
            sentence = re.sub(r"^(?:According to (?:the )?(?:evidence|rules|procedure|procedures|provided (?:evidence|procedure)|source)|Based on (?:the )?(?:evidence|procedure|provided information)),?\s*", "", sentence, flags=re.I)
            sentence = re.sub(r"^(?:The procedure (?:explicitly states|also mentions|states|says) that|Additionally,|Specifically,)\s*", "", sentence, flags=re.I)
            if re.fullmatch(r"(?:This|That) is (?:explicitly )?(?:stated|mentioned|provided) in the (?:evidence|procedure)\s*\.?", sentence, re.I):
                continue
            if len(sentence.split()) >= 3:
                results.append({"claim": sentence, "labels": labels})
    return results


class Verifier:
    model_id = "cross-encoder/nli-deberta-v3-small"

    def __init__(self, root: Path):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(str(root / "models" / "verifier"), device="cpu", max_length=512,
                                  local_files_only=True, trust_remote_code=False)

    def check(self, answer: str, evidence: list[dict]) -> dict:
        by_label = {e["label"]: e["text"] for e in evidence}
        rows = claims(answer)
        if not rows:
            return {"passed": False, "claims": [], "reason": "no_claims"}
        def canonical(text):
            return " ".join(re.findall(r"[a-z0-9]+", text.lower()))
        # Verbatim substantive text has a direct trace to the cited passage.
        # NLI is reserved for paraphrases, rather than overruling literal matches.
        # This still cannot prove that a quoted action fits the user's situation.
        for row in rows:
            claim_text = canonical(row["claim"])
            row["verbatim_support"] = bool(len(claim_text.split()) >= 5 and any(
                f" {claim_text} " in f" {canonical(by_label[label])} " for label in row["labels"] if label in by_label))
        pairs, pair_rows = [], []
        for i, row in enumerate(rows):
            if row["verbatim_support"]:
                continue
            for label in row["labels"]:
                if label in by_label:
                    text = by_label[label].replace("U.S.", "US")
                    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])|\n", text)
                    # Adjacent windows reduce long-premise dilution while keeping
                    # nearby exceptions. Include the original as an alternative.
                    windows = [text] + [" ".join(sentences[j:j+2]) for j in range(len(sentences))]
                    prefix = text.split(" | ")[0] + " | " if " | " in text else ""
                    for window in dict.fromkeys(windows):
                        premise = prefix + window if prefix and not window.startswith(prefix) else window
                        pairs.append((premise, row["claim"]))
                        pair_rows.append(i)
        scores = np.asarray(self.model.predict(pairs, show_progress_bar=False, apply_softmax=True)) if pairs else np.empty((0,3))
        # Model card: contradiction=0, entailment=1, neutral=2.
        for i, row in enumerate(rows):
            if row["verbatim_support"]:
                row.update({"entailment": None, "contradiction": None, "supported": True,
                            "support_method": "verbatim_match"})
                continue
            relevant = [s for s, row_idx in zip(scores, pair_rows) if row_idx == i]
            best = max(relevant, key=lambda s: float(s[1])) if relevant else np.array([0., 0., 1.])
            row["entailment"] = round(float(best[1]), 4)
            row["contradiction"] = round(float(best[0]), 4)
            row["supported"] = bool(best[1] >= .55 and best[0] < .2)
            row["support_method"] = "nli_screen"
        return {"passed": all(r["supported"] for r in rows), "claims": rows,
                "model": self.model_id, "entailment_threshold": .55,
                "limitation": "NLI is an imperfect screening signal, not independent factual validation."}
