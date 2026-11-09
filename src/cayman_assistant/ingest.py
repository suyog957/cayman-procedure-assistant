"""Structure-aware extraction for the supplied Aspose HTML exports.

Never follow links, run scripts, or discard table conditions. Source hashes and
stable chunk IDs make every result traceable to the exact local input snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata

from bs4 import BeautifulSoup, Tag

PARSER_VERSION = "1.1"
HEADING_LEVELS = {
    "PolicyMajorSectionHead": 1,
    "Policy1stLevelSubhead": 2,
    "Policy2ndLevelSubheader": 3,
    "Policy3rdLevelSubheader": 4,
    "h1": 1,
    "h2": 2,
    "h3": 3,
    "h4": 4,
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def element_text(tag: Tag) -> str:
    # Join inline runs without inserting spaces inside split words; paragraph,
    # line break, and list boundaries are represented explicitly.
    copy = BeautifulSoup(str(tag), "html.parser")
    for br in copy.find_all("br"):
        br.replace_with(" ")
    for block in copy.find_all(["p", "li"]):
        block.append(" ")
    return clean(copy.get_text())


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    published: str
    source_file: str
    source_sha256: str
    section: str
    anchor: str
    ordinal: int
    text: str
    kind: str
    table_id: str | None = None
    row_id: int | None = None

    @property
    def search_text(self) -> str:
        return f"{self.doc_id} | {self.title} | {self.section}\n{self.text}"


def split_text(text: str, limit: int = 110, overlap: int = 20) -> list[str]:
    """Bound long cells/paragraphs; prefer complete sentences and preserve overlap."""
    words = text.split()
    if len(words) <= limit:
        return [text] if text else []
    parts, start = [], 0
    while start < len(words):
        end = min(start + limit, len(words))
        if end < len(words):
            for j in range(end, max(start + limit // 2, start + 1), -1):
                if re.search(r"[.!?;:]$", words[j - 1]):
                    end = j
                    break
        parts.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(start + 1, end - overlap)
    return parts


def table_rows(table: Tag, table_id: str):
    """Serialize rows with column labels, including nested table content once.

    Rowspans carry the originating cell into subsequent rows. Colspans occupy
    their actual grid width, so a condition cannot silently shift columns.
    """
    rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
    active: dict[int, tuple[str, int]] = {}
    headers: list[str] = []
    for row_number, row in enumerate(rows):
        cells = row.find_all(["td", "th"], recursive=False)
        values: dict[int, str] = {}
        next_active = {}
        for col, (value, remaining) in active.items():
            values[col] = value
            if remaining > 1:
                next_active[col] = (value, remaining - 1)
        col = 0
        for cell in cells:
            while col in values:
                col += 1
            text = element_text(cell)
            colspan = max(1, int(cell.get("colspan", 1)))
            rowspan = max(1, int(cell.get("rowspan", 1)))
            for offset in range(colspan):
                values[col + offset] = text
                if rowspan > 1:
                    next_active[col + offset] = (text, rowspan - 1)
            col += colspan
        active = next_active
        ordered = [values.get(i, "") for i in range(max(values, default=-1) + 1)]
        if not any(ordered):
            continue
        if row_number == 0:
            # These exports typically use styled td elements, not th.
            header_like = all(len(v.split()) <= 12 for v in ordered) and len(ordered) > 1
            if row.find("th") or header_like:
                headers = ordered
                yield {
                    "text": "Table columns: " + " | ".join(ordered),
                    "kind": "table_header",
                    "table_id": table_id,
                    "row_id": row_number,
                }
                continue
        labelled = []
        for i, value in enumerate(ordered):
            if value and (i == 0 or value != ordered[i - 1]):
                label = headers[i] if i < len(headers) else f"Column {i + 1}"
                labelled.append(f"{label}: {value}")
        yield {
            "text": " | ".join(labelled),
            "kind": "table_row",
            "table_id": table_id,
            "row_id": row_number,
        }


def parse_document(path: Path, root: Path) -> tuple[dict, list[Chunk]]:
    raw = path.read_bytes()
    # Input declares UTF-8; decode explicitly instead of letting a detector guess.
    soup = BeautifulSoup(raw.decode("utf-8-sig"), "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    title_element = soup.select_one(".PolicyTitle") or soup.title
    title = element_text(title_element) if title_element else path.stem
    doc_id = re.search(r"PR\d+", path.name).group()
    pub = soup.select_one(".PublishDate")
    published = element_text(pub) if pub else "Not specified"
    digest = sha256(raw).hexdigest()
    headings: dict[int, str] = {}
    anchor = ""
    pending_anchor = ""
    blocks = []
    table_number = 0
    for tag in soup.body.descendants:
        if not isinstance(tag, Tag):
            continue
        if tag.name == "a" and tag.get("name") and not tag.find_parent("table"):
            pending_anchor = str(tag["name"])
        if tag.name == "table" and not tag.find_parent("table"):
            table_number += 1
            for row in table_rows(tag, f"{doc_id}-T{table_number:03}"):
                blocks.append(
                    dict(row, section=" > ".join(headings.values()) or "Overview", anchor=anchor)
                )
            continue
        if tag.find_parent("table") or tag.name not in {"p", "li", "h1", "h2", "h3", "h4"}:
            continue
        # li text includes its nested paragraphs/list content exactly once.
        if tag.find_parent("li"):
            continue
        classes = tag.get("class", [])
        if any(
            c in classes for c in ("PolicyTitle", "PublishDate", "PolicyFooter", "Footer", "Header")
        ):
            continue
        text = element_text(tag)
        if not text:
            continue
        level = next(
            (HEADING_LEVELS[c] for c in classes if c in HEADING_LEVELS),
            HEADING_LEVELS.get(tag.name),
        )
        if level:
            headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = text
            anchor = pending_anchor
        else:
            blocks.append(
                {
                    "text": text,
                    "kind": "list" if tag.name == "li" else "paragraph",
                    "section": " > ".join(headings.values()) or "Overview",
                    "anchor": anchor,
                }
            )
    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_info = None

    def emit(text: str, info: dict):
        ordinal = len(chunks)
        cid = f"{doc_id}-{sha256((digest + str(ordinal) + text).encode()).hexdigest()[:12]}"
        chunks.append(
            Chunk(
                cid,
                doc_id,
                title,
                published,
                path.relative_to(root).as_posix(),
                digest,
                info["section"],
                info["anchor"],
                ordinal,
                text,
                info["kind"],
                info.get("table_id"),
                info.get("row_id"),
            )
        )

    def flush():
        nonlocal buffer, buffer_info
        if buffer:
            emit("\n".join(buffer), buffer_info)
        buffer, buffer_info = [], None

    for block in blocks:
        if block["kind"].startswith("table"):
            flush()
            # Repeat the row's left-hand condition on oversized continuations.
            condition = block["text"].split(" | ")[0]
            prefix = (
                (condition[:300] + " | Row continuation: ")
                if len(block["text"].split()) > 130
                else ""
            )
            for i, part in enumerate(split_text(block["text"], limit=110 if prefix else 130)):
                emit((prefix if i else "") + part, block)
        else:
            for part in split_text(block["text"]):
                if buffer and (
                    buffer_info["section"] != block["section"]
                    or len((" ".join(buffer) + " " + part).split()) > 110
                ):
                    flush()
                buffer_info = block
                buffer.append(part)
    flush()
    meta = {
        "doc_id": doc_id,
        "title": title,
        "published": published,
        "source_file": path.relative_to(root).as_posix(),
        "sha256": digest,
        "bytes": len(raw),
        "words": sum(len(b["text"].split()) for b in blocks),
        "top_level_tables": table_number,
        "all_tables": len(soup.find_all("table")),
        "chunks": len(chunks),
        "sections": list(dict.fromkeys(b["section"] for b in blocks)),
        "external_links": len(soup.find_all("a", href=True)),
    }
    return meta, chunks


def ingest(root: Path, data_dir: Path, output_dir: Path) -> dict:
    paths = sorted(data_dir.glob("*.html"))
    if len(paths) != 11:
        raise ValueError(f"Expected 11 supplied HTML documents; found {len(paths)} in {data_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    documents, chunks = [], []
    for path in paths:
        meta, parsed = parse_document(path, root)
        documents.append(meta)
        chunks.extend(parsed)
    if len({c.chunk_id for c in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    manifest = {
        "parser_version": PARSER_VERSION,
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "documents": documents,
    }
    (output_dir / "corpus_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (output_dir / "chunks.jsonl").write_text(
        "\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in chunks) + "\n",
        encoding="utf-8",
    )
    clean_dir = output_dir / "documents"
    clean_dir.mkdir(exist_ok=True)
    for doc in documents:
        content = [f"# {doc['title']}", doc["published"], f"Source SHA256: {doc['sha256']}"]
        last = None
        for c in chunks:
            if c.doc_id == doc["doc_id"]:
                if c.section != last:
                    content.append(f"\n## {c.section}")
                    last = c.section
                content.append(f"\n[{c.chunk_id}]\n{c.text}")
        (clean_dir / f"{doc['doc_id']}.md").write_text("\n".join(content), encoding="utf-8")
    return manifest


def load_chunks(index_dir: Path) -> list[Chunk]:
    return [
        Chunk(**json.loads(line))
        for line in (index_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
