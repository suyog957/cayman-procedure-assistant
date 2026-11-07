"""Behavioral regressions for attribution, bounded correction and inspectability."""
from hashlib import sha256
from pathlib import Path
import json
import numpy as np

from cayman_assistant.assistant import Assistant
from cayman_assistant.ingest import Chunk
from cayman_assistant.retrieval import Hit, Retriever
from cayman_assistant.verification import claims, Verifier
from cayman_assistant.validation import validate_answer
from cayman_assistant.experience import source_html, source_integrity, active_response


class NoEntailment:
    def predict(self, pairs, **kwargs):
        return np.tile([0., 0., 1.], (len(pairs), 1))


def verifier():
    instance = object.__new__(Verifier)
    instance.model = NoEntailment()
    return instance


def fake_assistant(drafts):
    text = "The maximum overnight coin storage amount is $5,250."
    chunk = Chunk("test-chunk", "PR63", "Coin-counting machines", "Published October 9, 2025", "source.html", "hash",
                  "Understand the rules", "anchor", 0, text, "paragraph")
    class Retrieval:
        called = False
        def validate_snapshot(self):
            return 1
        def search(self, *args, **kwargs):
            self.called = True
            return [Hit(chunk, 10., .8, .03, 5.)]
        def expand_qualifications(self, hits):
            return hits
    class Generation:
        model_id = "test-local-model"
        calls = 0
        def generate(self, question, evidence):
            answer = drafts[min(self.calls, len(drafts)-1)]
            self.calls += 1
            return answer, {"input_tokens": 100, "output_tokens": 20, "generation_seconds": .1}
    instance = object.__new__(Assistant)
    instance.retriever, instance.generator, instance.verifier = Retrieval(), Generation(), verifier()
    return instance


def test_explicit_sentence_citations_do_not_leak_between_claims():
    rows = claims("Use dual control [S1]. Verify the customer identity [S2].")
    assert rows[0]["labels"] == ["S1"]
    assert rows[1]["labels"] == ["S2"]


def test_post_period_citations_remain_with_their_sentences():
    rows = claims("Use dual control. [S1] Verify the customer identity. [S2]")
    assert [r["labels"] for r in rows] == [["S1"], ["S2"]]


def test_one_paragraph_footer_can_support_the_whole_paragraph():
    rows = claims("Use dual control. Verify the customer identity. [S1]")
    assert [r["labels"] for r in rows] == [["S1"], ["S1"]]


def test_numeric_fact_cannot_borrow_from_an_uncited_passage():
    evidence = [{"label":"S1","text":"The limit is $50."}, {"label":"S2","text":"The limit is $5,250."}]
    result = validate_answer("The limit is $5,250. [S1]", evidence)
    assert not result["passed"] and result["numeric_citation_conflicts"]
    assert not result["novel_numbers"]


def test_wrong_citation_cannot_borrow_verbatim_support():
    evidence = [{"label":"S1","text":"Transactions require a manager review."},
                {"label":"S2","text":"The maximum overnight coin storage amount is $5,250."}]
    result = verifier().check("The maximum overnight coin storage amount is $5,250. [S1]", evidence)
    assert not result["passed"]


def test_claim_record_includes_its_supporting_passage_and_quote():
    text = "The maximum overnight coin storage amount is $5,250."
    result = verifier().check(text + " [S1]", [{"label":"S1","text":text,"chunk_id":"source-chunk"}])
    row = result["claims"][0]
    assert row["supporting_label"] == "S1" and row["source_chunk_id"] == "source-chunk"
    assert text in row["support_quote"] and row["entailment"] is None


def test_failed_numeric_draft_can_be_corrected_once_without_releasing_it():
    assistant = fake_assistant(["The limit is $9,000. [S1]", "The maximum overnight coin storage amount is $5,250. [S1]"])
    events = []
    result = assistant.answer("What is the overnight coin machine storage limit?", on_event=events.append)
    assert result.status == "answered" and "$9,000" not in result.answer
    assert assistant.generator.calls == 2 and result.metrics["repair_attempted"]
    assert any(e["key"] == "repair" for e in events)
    assert result.grounding["claims_supported"] == 1 and result.grounding["source_files_verified_at_request"]


def test_correction_budget_cannot_loop_until_an_answer_looks_supported():
    assistant = fake_assistant(["The limit is $9,000. [S1]"])
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert result.status == "evidence_only" and assistant.generator.calls == 2
    assert result.checks["withheld_draft"] == "The limit is $9,000. [S1]"
    assert result.grounding["rules"][2]["state"] == "failed"


def test_passing_first_draft_does_not_claim_a_correction_happened():
    assistant = fake_assistant(["The maximum overnight coin storage amount is $5,250. [S1]"])
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert assistant.generator.calls == 1 and not result.metrics["repair_attempted"]
    assert not any(s["key"] == "repair" for s in result.activity)


def test_model_abstention_does_not_claim_the_procedure_lacks_the_rule():
    assistant = fake_assistant(["INSUFFICIENT_EVIDENCE"])
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert result.status == "unsupported" and assistant.generator.calls == 1
    assert "could not produce" in result.answer
    assert all(rule["state"] == "not_run" for rule in result.grounding["rules"])


def test_retrieval_only_mode_does_not_claim_a_draft_was_generated():
    assistant = fake_assistant(["unused"])
    assistant.generator = None
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert result.status == "evidence_only" and not result.generator_used
    assert "not used" in result.grounding["decision"]
    assert not any(s["key"] in {"draft","repair","validate"} for s in result.activity)


def test_header_only_results_do_not_claim_supporting_passages_exist():
    assistant = fake_assistant(["unused"])
    hit = assistant.retriever.search("test")[0]
    hit.chunk.kind = "table_header"
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert result.status == "unsupported" and assistant.generator.calls == 0
    assert not result.sources and "complete supporting passage" in result.answer


def test_selected_procedure_cannot_silently_answer_another_topic():
    assistant = fake_assistant(["unused"])
    result = assistant.answer("Can a notary charge a fee?", scope_doc_id="PR63")
    assert result.status == "clarify" and not assistant.retriever.called
    assert "PR1000" in result.answer and "PR63" in result.answer


def test_changed_snapshot_stops_generation_even_when_the_engine_is_cached():
    assistant = fake_assistant(["unused"])
    def fail():
        raise ValueError("snapshot changed")
    assistant.retriever.validate_snapshot = fail
    result = assistant.answer("What is the overnight coin machine storage limit?")
    assert result.status == "unsupported" and assistant.generator.calls == 0
    assert not result.grounding["source_files_verified_at_request"]


def test_snapshot_rebuild_invalidates_cached_retrieval(tmp_path):
    instance = object.__new__(Retriever)
    instance.index_dir = tmp_path
    instance._snapshot_hashes = {"chunks.jsonl":"old-digest"}
    (tmp_path/"chunks.jsonl").write_text("new index")
    try:
        instance.validate_snapshot()
    except ValueError as error:
        assert "reload" in str(error)
    else:
        raise AssertionError("A stale cached index must be rejected")


def test_untrusted_source_text_is_escaped_for_the_evidence_inspector():
    rendered = source_html({"text":'<script>alert("bad")</script> Customer <name>'})
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered


def test_visible_integrity_badge_checks_current_bytes_and_rejects_path_escape(tmp_path):
    source = tmp_path/"source.html"
    source.write_bytes(b"original")
    record = {"source_file":"source.html","source_sha256":sha256(b"original").hexdigest()}
    assert source_integrity(tmp_path, record)
    source.write_bytes(b"changed")
    assert not source_integrity(tmp_path, record)
    assert not source_integrity(tmp_path, {"source_file":"../outside.html","source_sha256":"hash"})


def test_a_new_unsupported_response_does_not_show_previous_evidence():
    previous = {"trace_id":"old","sources":[{"label":"S1"}]}
    latest = {"trace_id":"new","sources":[],"status":"unsupported"}
    messages = [{"role":"assistant","result":previous},{"role":"assistant","result":latest}]
    assert active_response(messages, None) is latest
