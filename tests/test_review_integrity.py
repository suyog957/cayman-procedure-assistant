"""Review regressions: corrupted indexes and incomplete runs must fail safely."""
from hashlib import sha256
import json
import numpy as np
import pytest

from cayman_assistant.retrieval import load_embedding_index, Retriever
from cayman_assistant.evaluation_runs import new_run_directory, publish_completed_run


def embedding_fixture(folder, vectors):
    folder.mkdir(exist_ok=True)
    (folder / "chunks.jsonl").write_bytes(b"original passages\n")
    np.save(folder / "embeddings.npy", vectors, allow_pickle=False)
    meta = {"chunks": 2, "dimensions": 384,
            "chunks_sha256": sha256((folder / "chunks.jsonl").read_bytes()).hexdigest(),
            "embeddings_sha256": sha256((folder / "embeddings.npy").read_bytes()).hexdigest()}
    (folder / "embedding_manifest.json").write_text(json.dumps(meta), encoding="utf-8")


def test_changed_embedding_bytes_cannot_keep_the_old_manifest(tmp_path):
    vectors = np.eye(2, 384, dtype=np.float32)
    embedding_fixture(tmp_path, vectors)
    assert np.array_equal(load_embedding_index(tmp_path, 2), vectors)
    np.save(tmp_path / "embeddings.npy", np.roll(vectors, 1, axis=1), allow_pickle=False)
    with pytest.raises(ValueError, match="manifest"):
        load_embedding_index(tmp_path, 2)


def test_loaded_retriever_rejects_an_embedding_file_changed_after_loading(tmp_path):
    path = tmp_path / "embeddings.npy"
    path.write_bytes(b"original matrix")
    instance = object.__new__(Retriever)
    instance.index_dir = tmp_path
    instance._snapshot_hashes = {path.name: sha256(path.read_bytes()).hexdigest()}
    path.write_bytes(b"changed matrix")
    with pytest.raises(ValueError, match="snapshot changed"):
        instance.validate_snapshot()


@pytest.mark.parametrize("vectors", [np.eye(2, 383), np.zeros((2, 384)), np.full((2, 384), np.nan)])
def test_invalid_embedding_shape_norm_or_values_rejected_even_with_matching_hash(tmp_path, vectors):
    embedding_fixture(tmp_path, vectors)
    with pytest.raises(ValueError, match="Invalid embedding"):
        load_embedding_index(tmp_path, 2)


def test_retrieval_only_runs_cannot_write_into_the_published_directory(tmp_path):
    canonical = tmp_path / "artifacts/evaluation"
    canonical.mkdir(parents=True)
    (canonical / "metrics.json").write_text("published answers")
    run = new_run_directory(tmp_path, None, "retrieval")
    assert run != canonical and run.is_dir()
    with pytest.raises(ValueError, match="isolated"):
        new_run_directory(tmp_path, canonical, "retrieval")
    assert (canonical / "metrics.json").read_text() == "published answers"


def test_incomplete_evaluation_does_not_replace_published_evidence(tmp_path):
    run = tmp_path / "run"; run.mkdir()
    destination = tmp_path / "published"; destination.mkdir()
    (destination / "metrics.json").write_text("previous complete run")
    for name, data in {"metrics.json": {"answers": {"ordinary_n": 1}},
                       "answer_details.json": [], "retrieval_details.json": []}.items():
        (run / name).write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Incomplete"):
        publish_completed_run(run, destination, expected_ordinary=30, expected_total=40)
    assert (destination / "metrics.json").read_text() == "previous complete run"


def test_complete_evaluation_publication_binds_all_three_files(tmp_path):
    run = tmp_path / "run"; run.mkdir()
    for name, data in {"metrics.json": {"answers": {"ordinary_n": 1}},
                       "answer_details.json": [{"id": "test"}],
                       "retrieval_details.json": [{"mode": m} for m in ["bm25", "dense", "hybrid"]]}.items():
        (run / name).write_bytes(json.dumps(data,indent=2).replace('\n','\r\n').encode('utf-8'))
    destination = tmp_path / "published"
    publish_completed_run(run, destination, expected_ordinary=1, expected_total=1)
    manifest = json.loads((destination / "run_manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha256((destination / name).read_bytes()).hexdigest() == digest
        assert b'\r\n' not in (destination / name).read_bytes()
