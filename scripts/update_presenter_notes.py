"""Update speaker notes while preserving every other PPTX part and slide PDF.

Use this for a notes-only revision. The full deliverable builder is deliberately
not imported or run: the approved visible slide objects are copied verbatim.
"""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from copy import copy
import json
import re
import uuid
import zipfile

from pptx import Presentation

from learning_notes import load_learning_notes, plain_notes, apply_learning_note, write_learning_pdf
from presentation_deck import DECK_BASENAME

ROOT = Path(__file__).resolve().parents[1]
NOTE_PART = re.compile(r"ppt/notesSlides/notesSlide[1-6]\.xml$")


def fingerprint(data):
    return sha256(data).hexdigest()


def main():
    submission = ROOT / "submission"
    target = submission / (DECK_BASENAME + ".pptx")
    original = target.read_bytes()
    working = ROOT / "artifacts/video_build" / ("notes_update_" + uuid.uuid4().hex[:8])
    working.mkdir(parents=True)
    (working / "original.pptx").write_bytes(original)
    with zipfile.ZipFile(BytesIO(original)) as archive:
        baseline_parts = {
            name: fingerprint(archive.read(name))
            for name in archive.namelist()
            if not NOTE_PART.fullmatch(name)
        }
        note_parts = [name for name in archive.namelist() if NOTE_PART.fullmatch(name)]
    assert len(note_parts) == 6
    preserved = [
        submission / (DECK_BASENAME + ".pdf"),
        submission / "Cayman_Procedure_Assistant.pdf",
    ]
    preserved += list((ROOT / "artifacts/slides").glob("slide_*.png"))
    preserved += [ROOT / "artifacts/presentation/Leadership_Deck_Preview.jpg"]
    protected_hashes = {
        path.relative_to(ROOT).as_posix(): fingerprint(path.read_bytes()) for path in preserved
    }
    qa = ROOT / "artifacts/presentation"
    baseline_file = qa / "notes_revision_baseline.json"
    if baseline_file.exists():
        baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
        assert baseline["non_note_parts"] == baseline_parts, (
            "A visible presentation part changed since the notes baseline."
        )
        assert baseline["protected_files"] == protected_hashes, (
            "A slide PDF or preview changed since the notes baseline."
        )
    else:
        with zipfile.ZipFile(BytesIO(original)) as archive:
            original_notes = {name: fingerprint(archive.read(name)) for name in note_parts}
        baseline = {
            "original_pptx_sha256": fingerprint(original),
            "non_note_parts": baseline_parts,
            "note_parts": original_notes,
            "protected_files": protected_hashes,
        }
        baseline_file.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

    notes = load_learning_notes(ROOT)
    deck = Presentation(BytesIO(original))
    assert len(deck.slides) == len(notes) == 6
    for slide, note in zip(deck.slides, notes):
        apply_learning_note(slide, note)
        assert slide.notes_slide.notes_text_frame.text == plain_notes(note)
    edited = BytesIO()
    deck.save(edited)
    output = working / target.name
    with zipfile.ZipFile(BytesIO(original)) as source, zipfile.ZipFile(edited) as revised:
        with zipfile.ZipFile(output, "w") as destination:
            destination.comment = source.comment
            for item in source.infolist():
                data = (
                    revised.read(item.filename)
                    if NOTE_PART.fullmatch(item.filename)
                    else source.read(item.filename)
                )
                destination.writestr(copy(item), data)
        with zipfile.ZipFile(output) as final:
            changed = [name for name in source.namelist() if source.read(name) != final.read(name)]
            assert set(final.namelist()) == set(source.namelist())
            assert all(NOTE_PART.fullmatch(name) for name in changed), changed
            assert all(
                fingerprint(final.read(name)) == digest for name, digest in baseline_parts.items()
            )

    pdf = working / "Presenter_Notes.pdf"
    write_learning_pdf(ROOT, pdf)
    # Atomic replacement cannot truncate an existing user-open presentation.
    # If Office locks it, the verified output remains in this working directory.
    output.replace(target)
    pdf.replace(submission / "Presenter_Notes.pdf")
    for name, digest in protected_hashes.items():
        assert fingerprint((ROOT / name).read_bytes()) == digest, name
    members = [
        DECK_BASENAME + ".pptx",
        DECK_BASENAME + ".pdf",
        "Demo_Runbook.pdf",
        "Recorded_Demo.pdf",
        "Presenter_Notes.pdf",
        "README.txt",
    ]
    bundle = working / "Presentation_Materials.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in members:
            archive.write(submission / name, name)
    bundle.replace(submission / "Presentation_Materials.zip")
    with zipfile.ZipFile(target) as archive:
        modified_from_baseline = [
            name
            for name, digest in baseline["note_parts"].items()
            if fingerprint(archive.read(name)) != digest
        ]
    report = {
        "status": "passed",
        "notes_format": "learning explanations, short speaking version and Q&A",
        "slide_count": 6,
        "speaker_note_words_per_slide": [len(plain_notes(note).split()) for note in notes],
        "all_non_note_pptx_parts_byte_identical": True,
        "preserved_non_note_parts": len(baseline_parts),
        "modified_parts": modified_from_baseline,
        "modified_parts_this_run": changed,
        "visible_slide_pdf_and_previews_byte_identical": True,
        "source_free_bundle_refreshed": True,
        "original_pptx_sha256": baseline["original_pptx_sha256"],
        "updated_pptx_sha256": fingerprint(target.read_bytes()),
        "learning_notes_pdf_sha256": fingerprint((submission / "Presenter_Notes.pdf").read_bytes()),
    }
    (qa / "notes_revision_review.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
