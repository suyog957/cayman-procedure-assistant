"""Local hybrid retrieval: BM25 + normalized dense vectors + RRF + reranking."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import re
import time

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from .ingest import Chunk, load_chunks

STOP = set(ENGLISH_STOP_WORDS) - {"no", "not", "without"}
ALIASES = {"id": "identification", "ids": "identification", "tin": "taxpayer identification number",
           "ssn": "social security number", "noncustomer": "non customer", "noncustomers": "non customers"}


def tokens(text: str) -> list[str]:
    found = re.findall(r"[a-z0-9]+", text.lower())
    expanded = []
    for term in found:
        if term not in STOP and len(term) > 1:
            expanded.append(term)
            expanded.extend(ALIASES.get(term, "").split())
    return expanded


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = .75):
        self.k1, self.b = k1, b
        self.counts = [Counter(tokens(t)) for t in texts]
        self.lengths = np.array([sum(c.values()) for c in self.counts], dtype=np.float32)
        self.avg = float(self.lengths.mean()) or 1.0
        df = Counter(t for c in self.counts for t in c)
        self.idf = {t: np.log(1 + (len(texts) - n + .5) / (n + .5)) for t, n in df.items()}

    def score(self, query: str) -> np.ndarray:
        scores = np.zeros(len(self.counts), dtype=np.float32)
        norm = self.k1 * (1 - self.b + self.b * self.lengths / self.avg)
        for term in set(tokens(query)):
            if term in self.idf:
                tf = np.array([c.get(term, 0) for c in self.counts], dtype=np.float32)
                scores += self.idf[term] * tf * (self.k1 + 1) / (tf + norm)
        return scores


@dataclass
class Hit:
    chunk: Chunk
    bm25: float
    cosine: float
    rrf: float
    rerank: float = 0.0
    expanded_from: str | None = None


def verify_sources(root: Path, index_dir: Path):
    manifest = json.loads((index_dir / "corpus_manifest.json").read_text(encoding="utf-8"))
    for doc in manifest["documents"]:
        source = root / doc["source_file"]
        if not source.is_file() or sha256(source.read_bytes()).hexdigest() != doc["sha256"]:
            raise ValueError(f"Source changed or missing: {doc['source_file']}. Rebuild the index.")


class Retriever:
    def __init__(self, root: Path, mode: str = "hybrid", verify: bool = True):
        from sentence_transformers import SentenceTransformer, CrossEncoder
        import torch
        torch.set_num_threads(6)
        self.root = root
        self.index_dir = root / "artifacts" / "index"
        if verify:
            verify_sources(root, self.index_dir)
        self.chunks = load_chunks(self.index_dir)
        self._integrity_files = ["corpus_manifest.json", "chunks.jsonl", "embedding_manifest.json"]
        self._snapshot_hashes = {name: sha256((self.index_dir / name).read_bytes()).hexdigest() for name in self._integrity_files}
        self.by_position = {(c.doc_id, c.ordinal): c for c in self.chunks}
        self.bm25 = BM25([c.search_text for c in self.chunks])
        self.encoder = SentenceTransformer(str(root / "models" / "embedder"), local_files_only=True, device="cpu", trust_remote_code=False)
        self.encoder.max_seq_length = 384
        self.vectors = np.load(self.index_dir / "embeddings.npy", allow_pickle=False)
        if self.vectors.shape[0] != len(self.chunks) or not np.isfinite(self.vectors).all():
            raise ValueError("Invalid embedding index; rebuild it")
        index_meta = json.loads((self.index_dir / "embedding_manifest.json").read_text(encoding="utf-8"))
        actual = sha256((self.index_dir / "chunks.jsonl").read_bytes()).hexdigest()
        if actual != index_meta["chunks_sha256"]:
            raise ValueError("Chunks do not match embeddings; rebuild the index")
        self.reranker = CrossEncoder(str(root / "models" / "reranker_v2"), device="cpu", max_length=512, local_files_only=True, trust_remote_code=False)
        self.mode = mode

    def validate_snapshot(self) -> int:
        """Reject stale cached objects after a source change or an index rebuild."""
        for name, expected in self._snapshot_hashes.items():
            path = self.index_dir / name
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("The indexed snapshot changed; reload the application.")
        verify_sources(self.root, self.index_dir)
        return len({c.doc_id for c in self.chunks})

    def search(self, query: str, k: int = 5, mode: str | None = None, doc_id: str | None = None) -> list[Hit]:
        mode = mode or self.mode
        lex = self.bm25.score(query)
        query_vector = self.encoder.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        dense = self.vectors @ query_vector
        allowed = np.array([not doc_id or c.doc_id == doc_id for c in self.chunks])
        lex = np.where(allowed, lex, -1e9)
        dense = np.where(allowed, dense, -1e9)
        count = min(30, int(allowed.sum()))
        lexical_ids = np.argsort(-lex, kind="stable")[:count]
        dense_ids = np.argsort(-dense, kind="stable")[:count]
        rrf = Counter()
        for ranking in [lexical_ids, dense_ids]:
            for rank, idx in enumerate(ranking, start=1):
                rrf[int(idx)] += 1 / (60 + rank)
        if mode == "bm25":
            candidates = list(lexical_ids)
        elif mode == "dense":
            candidates = list(dense_ids)
        else:
            candidates = [i for i, _ in rrf.most_common(30)]
        hits = [Hit(self.chunks[i], float(lex[i]), float(dense[i]), float(rrf[i])) for i in candidates]
        if mode == "hybrid":
            predictions = self.reranker.predict([(query, h.chunk.search_text) for h in hits], show_progress_bar=False)
            for h, score in zip(hits, predictions):
                h.rerank = float(score)
            hits.sort(key=lambda h: h.rerank, reverse=True)
        return hits[:k]

    def expand_qualifications(self, hits: list[Hit]) -> list[Hit]:
        """Include an adjacent qualification/row continuation for leading hits.

        This is bounded parent-context recovery, not a new relevance score. The
        inherited score is explicitly identified by expanded_from in evidence.
        """
        result, seen = [], set()
        for rank, hit in enumerate(hits):
            if hit.chunk.chunk_id not in seen:
                result.append(hit); seen.add(hit.chunk.chunk_id)
            if rank > 1:
                continue
            c = hit.chunk
            next_chunk = self.by_position.get((c.doc_id, c.ordinal + 1))
            if not next_chunk or next_chunk.section != c.section or next_chunk.chunk_id in seen:
                continue
            same_row = c.table_id and c.table_id == next_chunk.table_id and c.row_id == next_chunk.row_id
            qualification = not c.table_id and re.match(r"^(?:Exception|Note|Warning|Important|Caution|Unless|However)\b", next_chunk.text, re.I)
            if same_row or qualification:
                result.append(Hit(next_chunk, hit.bm25, hit.cosine, hit.rrf, hit.rerank, c.chunk_id))
                seen.add(next_chunk.chunk_id)
        return result


def build_embeddings(root: Path):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(6)
    index_dir = root / "artifacts" / "index"
    chunks = load_chunks(index_dir)
    encoder = SentenceTransformer(str(root / "models" / "embedder"), local_files_only=True, device="cpu", trust_remote_code=False)
    encoder.max_seq_length = 384
    start = time.perf_counter()
    vectors = encoder.encode([c.search_text for c in chunks], normalize_embeddings=True,
                             batch_size=32, show_progress_bar=True).astype(np.float32)
    np.save(index_dir / "embeddings.npy", vectors, allow_pickle=False)
    meta = {"model": "sentence-transformers/all-MiniLM-L6-v2", "dimensions": int(vectors.shape[1]),
            "chunks": len(chunks), "max_seq_length": 384,
            "chunks_sha256": sha256((index_dir / "chunks.jsonl").read_bytes()).hexdigest(),
            "elapsed_seconds": round(time.perf_counter() - start, 2)}
    (index_dir / "embedding_manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

