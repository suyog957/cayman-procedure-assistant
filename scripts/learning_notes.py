"""Load the presenter study guide and render its readable companion PDF."""

from html import escape
from pathlib import Path
import re

import pymupdf

NOTES_FILE = "docs/PRESENTER_LEARNING_NOTES.md"


def load_learning_notes(root: Path) -> list[str]:
    text = (root / NOTES_FILE).read_text(encoding="utf-8")
    parts = re.split(r"^## Slide ([1-6]) - (.+)$", text, flags=re.MULTILINE)
    if len(parts) != 19:
        raise ValueError("Expected exactly six numbered slide sections in the learning notes.")
    notes = []
    for offset in range(1, len(parts), 3):
        number, title, body = parts[offset : offset + 3]
        if int(number) != len(notes) + 1:
            raise ValueError("Learning notes must follow the six-slide order.")
        notes.append(f"## Slide {number} - {title}\n\n{body.strip()}")
    return notes


def plain_notes(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            line = line.lstrip("#").strip().upper()
        lines.append(line.replace("**", ""))
    return "\n".join(lines).strip()


def apply_learning_note(slide, markdown: str):
    """Format only the speaker-note body; the slide itself is never edited."""
    from pptx.dml.color import RGBColor
    from pptx.util import Pt

    frame = slide.notes_slide.notes_text_frame
    frame.clear()
    for index, line in enumerate(markdown.splitlines()):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        heading = line.startswith("#")
        text = line.lstrip("#").strip().upper() if heading else line
        paragraph.space_after = Pt(5 if heading else 3)
        for token in re.split(r"(\*\*.+?\*\*)", text):
            if not token:
                continue
            run = paragraph.add_run()
            run.text = token.replace("**", "")
            run.font.name = "Segoe UI"
            run.font.size = Pt(13 if heading else 11.5)
            run.font.bold = heading or token.startswith("**")
            run.font.color.rgb = RGBColor.from_string("A61C27" if heading else "302B28")


def _html(markdown: str) -> str:
    paragraphs = []
    pending = []

    def inline(value):
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(value))

    def flush():
        if pending:
            paragraphs.append("<p>" + inline(" ".join(pending)) + "</p>")
            pending.clear()

    for line in markdown.splitlines() + [""]:
        if line.startswith("#"):
            flush()
            level = min(3, len(line) - len(line.lstrip("#")))
            paragraphs.append(f"<h{level}>" + inline(line.lstrip("#").strip()) + f"</h{level}>")
        elif not line.strip():
            flush()
        else:
            pending.append(line)
    return "<html><body>" + "\n".join(paragraphs) + "</body></html>"


def write_learning_pdf(root: Path, output: Path):
    """Start each slide's study notes on a new page, at a comfortable type size."""
    source = (root / NOTES_FILE).read_text(encoding="utf-8")
    introduction = source.split("## Slide 1 -", 1)[0]
    sections = [introduction] + load_learning_notes(root)
    css = """body {font-family: sans-serif; font-size:10.5pt; line-height:1.32; color:#302b28;}
    h1 {font-size:24pt; color:#302b28; margin-bottom:16pt;}
    h2 {font-size:20pt; color:#a61c27; margin-bottom:14pt;}
    h3 {font-size:12.2pt; color:#a61c27; margin-top:15pt; margin-bottom:6pt;}
    p {margin-top:0; margin-bottom:9pt;} b {color:#302b28;}"""
    media = pymupdf.paper_rect("a4")
    body = pymupdf.Rect(46, 44, media.width - 46, media.height - 49)
    raw = output.with_suffix(".raw.pdf")
    writer = pymupdf.DocumentWriter(str(raw))
    ranges = []
    page_number = 0
    try:
        for index, section in enumerate(sections):
            story = pymupdf.Story(html=_html(section), user_css=css)
            first = page_number + 1
            more = True
            while more:
                device = writer.begin_page(media)
                more, _ = story.place(body)
                story.draw(device)
                writer.end_page()
                page_number += 1
            ranges.append((index, first, page_number))
    finally:
        writer.close()
    del writer
    with pymupdf.open(raw) as pdf:
        toc = []
        for index, first, last in ranges:
            label = "How to use these notes" if index == 0 else f"Slide {index} - learning notes"
            toc.append([1, label, first])
            for page_index in range(first - 1, last):
                page = pdf[page_index]
                page.draw_line(
                    (46, media.height - 36),
                    (media.width - 46, media.height - 36),
                    color=(0.84, 0.81, 0.78),
                    width=0.5,
                )
                page.insert_text(
                    (46, media.height - 24),
                    f"Branch Assist | {label}",
                    fontsize=8,
                    color=(0.4, 0.37, 0.35),
                )
                page.insert_text(
                    (media.width - 85, media.height - 24),
                    f"{page_index + 1}/{len(pdf)}",
                    fontsize=8,
                    color=(0.4, 0.37, 0.35),
                )
        pdf.set_toc(toc)
        pdf.set_metadata(
            {
                "title": "Branch Assist | Presenter learning notes",
                "author": "Branch Assist",
                "subject": "Plain-language explanations, implementation choices and presentation preparation",
            }
        )
        pdf.save(output, deflate=True)
    raw.unlink()
