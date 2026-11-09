"""Verify source-aligned learning notes and the strictly preserved slides."""

from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata
import zipfile

import pymupdf
from pptx import Presentation

from learning_notes import load_learning_notes, plain_notes
from presentation_deck import DECK_BASENAME

ROOT = Path(__file__).resolve().parents[1]


def compact(text):
    return "".join(re.findall(r"\w+", unicodedata.normalize("NFKC", text).lower()))


def main():
    target = ROOT / "submission" / (DECK_BASENAME + ".pptx")
    baseline = json.loads(
        (ROOT / "artifacts/presentation/notes_revision_baseline.json").read_text(encoding="utf-8")
    )
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for name, digest in baseline["non_note_parts"].items():
            assert sha256(archive.read(name)).hexdigest() == digest, name
    for name, digest in baseline["protected_files"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    notes = load_learning_notes(ROOT)
    deck = Presentation(target)
    assert len(deck.slides) == len(notes) == 6
    with pymupdf.open(ROOT / "submission/Presenter_Notes.pdf") as pdf:
        toc = pdf.get_toc()
        assert len(toc) == 7
        assert all(page.get_text().strip() for page in pdf)
        pdf_pages = len(pdf)
        for index, (slide, markdown) in enumerate(zip(deck.slides, notes), 1):
            first = toc[index][2] - 1
            last = toc[index + 1][2] - 1 if index < 6 else len(pdf)
            content = compact(
                " ".join(
                    pdf[p].get_text(
                        sort=True,
                        clip=pymupdf.Rect(0, 0, pdf[p].rect.width, pdf[p].rect.height - 40),
                    )
                    for p in range(first, last)
                )
            )
            expected = plain_notes(markdown)
            actual = slide.notes_slide.notes_text_frame.text
            assert actual == expected, ("PPT notes do not match canonical guide", index)
            assert "SHORT SPEAKING VERSION" in actual
            assert "QUESTIONS I SHOULD BE ABLE TO ANSWER" in actual
            assert not re.search(r"\w\?\w| ?\uFFFD", actual)
            for line in expected.splitlines():
                if line.strip():
                    assert compact(line) in content, ("Notes PDF omitted text", index, line[:70])
    # Pin the measurements explained in the guide to the unchanged accepted run.
    metrics = json.loads((ROOT / "artifacts/evaluation/metrics.json").read_text(encoding="utf-8"))
    assert [
        (r["mode"], round(r["hit_at_5"] * r["n"]))
        for r in metrics["retrieval"]
        if r["split"] == "all"
    ] == [("bm25", 27), ("dense", 28), ("hybrid", 30)]
    answer = metrics["answers"]
    assert round(answer["all_required_facts_proxy"] * answer["ordinary_n"]) == 23
    assert answer["generated_n"] == 35 and answer["evidence_only_fallbacks"] == 6
    assert (
        sum(answer["followup_fact_passes"].values()) == 2
        and len(answer["followup_fact_passes"]) == 4
    )
    assert answer["draft_word_count_n"] == 32 and answer["mean_word_count"] == 28
    assert answer["p50_seconds"] == 13.81 and answer["p95_seconds"] == 23.92
    report = {
        "status": "passed",
        "embedded_notes_equal_canonical_guide": True,
        "all_guide_lines_present_in_readable_pdf": True,
        "learning_notes_pdf_pages": pdf_pages,
        "pdf_slide_bookmarks": 6,
        "short_speaking_version_and_questions_per_slide": True,
        "all_non_note_pptx_parts_byte_identical": True,
        "preserved_non_note_parts": len(baseline["non_note_parts"]),
        "visible_slide_pdf_and_previews_byte_identical": True,
        "explained_measurements_match_accepted_results": True,
        "pptx_sha256": sha256(target.read_bytes()).hexdigest(),
        "learning_notes_pdf_sha256": sha256(
            (ROOT / "submission/Presenter_Notes.pdf").read_bytes()
        ).hexdigest(),
    }
    (ROOT / "artifacts/presentation/learning_notes_review.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
