from pathlib import Path
import json

from bs4 import BeautifulSoup

from cayman_assistant.ingest import parse_document, table_rows, load_chunks

ROOT = Path(__file__).resolve().parents[1]


def test_table_grid_carries_rowspan_condition_and_colspan_alignment():
    html = """<table><tr><th>Situation</th><th>Action</th><th>Owner</th></tr>
    <tr><td rowspan="2">Customer present</td><td>Check ID</td><td>Teller</td></tr>
    <tr><td colspan="2">Escalate if ID fails</td></tr></table>"""
    rows = list(table_rows(BeautifulSoup(html, "html.parser").table, "T1"))
    assert "Situation: Customer present | Action: Check ID | Owner: Teller" == rows[1]["text"]
    assert "Situation: Customer present | Action: Escalate if ID fails" == rows[2]["text"]


def test_nested_table_is_not_emitted_as_duplicate_rows():
    table = BeautifulSoup(
        "<table><tr><td>Condition</td><td>First<table><tr><td>Nested action</td></tr></table></td></tr></table>",
        "html.parser",
    ).table
    rows = list(table_rows(table, "T1"))
    assert len(rows) == 1
    assert rows[0]["text"].count("Nested action") == 1


def test_utf8_and_source_anchor_and_stable_identity(tmp_path):
    path = tmp_path / "PR123_Cayman_Bank.html"
    path.write_text(
        '<html><body><p class="PolicyTitle">Test – PR123</p><p class="PublishDate">Published today</p><p><a name="anchor1"></a></p><p class="PolicyMajorSectionHead">Rules</p><p>Customer’s document must be physical.</p></body></html>',
        encoding="utf-8",
    )
    meta, first = parse_document(path, tmp_path)
    _, second = parse_document(path, tmp_path)
    assert first[0].text == "Customer’s document must be physical."
    assert first[0].anchor == "anchor1"
    assert first[0].chunk_id == second[0].chunk_id
    path.write_text(
        path.read_text(encoding="utf-8").replace("physical", "original"), encoding="utf-8"
    )
    changed_meta, changed = parse_document(path, tmp_path)
    assert changed_meta["sha256"] != meta["sha256"]
    assert changed[0].chunk_id != first[0].chunk_id


def test_real_corpus_contains_every_procedure_and_key_table_facts():
    chunks = load_chunks(ROOT / "artifacts/index")
    manifest = json.loads((ROOT / "artifacts/index/corpus_manifest.json").read_text())
    assert len({c.doc_id for c in chunks}) == 11
    assert len({c.chunk_id for c in chunks}) == len(chunks) == manifest["chunk_count"]
    assert all(c.source_sha256 and c.section and c.text for c in chunks)
    text = " ".join(c.text for c in chunks if c.doc_id == "PR63")
    assert "$36.00" in text and "390 units" in text
    assert any(
        "Customer brought their non-Cayman Bank metal card" in c.text and "Do not accept" in c.text
        for c in chunks
    )
