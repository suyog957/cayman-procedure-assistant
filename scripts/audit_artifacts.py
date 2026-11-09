"""Audit extraction coverage and record exact local dependency/model artifacts."""

from hashlib import sha256
from pathlib import Path
import importlib.metadata as metadata
import json
import platform
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cayman_assistant.ingest import element_text, load_chunks, HEADING_LEVELS

root = Path(__file__).resolve().parents[1]
chunks = load_chunks(root / "artifacts/index")


def grams(text):
    words = re.findall(r"\w+", text.lower())
    return {tuple(words[i : i + 5]) for i in range(len(words) - 4)}


audit = []
for path in sorted((root / "Cayman_Bank_HTML_Files 2").glob("*.html")):
    doc_id = re.search(r"PR\d+", path.name).group()
    soup = BeautifulSoup(path.read_text(encoding="utf-8-sig"), "html.parser")
    originals, elements = set(), []
    for tag in soup.find_all(["p", "li"]):
        if tag.name == "li" or tag.find(["p", "li"]):
            continue
        excluded = {"PolicyTitle", "PublishDate", "PolicyFooter", "Footer", "Header"} | set(
            HEADING_LEVELS
        )
        if excluded.intersection(tag.get("class", [])):
            continue
        text = element_text(tag)
        g = grams(text)
        if g:
            originals.update(g)
            elements.append((text, g))
    extracted = set()
    for chunk in chunks:
        if chunk.doc_id == doc_id:
            extracted.update(grams(chunk.text))
    missing = originals - extracted
    audit.append(
        {
            "doc_id": doc_id,
            "source_5grams": len(originals),
            "missing_5grams": len(missing),
            "coverage": round(1 - len(missing) / max(1, len(originals)), 6),
            "missing_examples": [text for text, g in elements if g & missing][:8],
            "interpretation": "Text preservation diagnostic; does not validate table semantics or policy interpretation.",
        }
    )
(root / "artifacts/extraction_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

model_rows = []
for folder in ["embedder", "reranker_v2", "generator_v2", "verifier", "generator"]:
    model_dir = root / "models" / folder
    if not model_dir.exists():
        continue
    commit_file = model_dir / (
        ".cache/huggingface/download/Qwen3-4B-Q4_K_M.gguf.metadata"
        if folder == "generator_v2"
        else ".cache/huggingface/download/config.json.metadata"
    )
    revision = commit_file.read_text().splitlines()[0] if commit_file.exists() else "not_recorded"
    files = []
    for path in sorted(model_dir.rglob("*")):
        if path.is_file() and ".cache" not in path.parts:
            hasher = sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    hasher.update(block)
            files.append(
                {
                    "path": path.relative_to(model_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hasher.hexdigest(),
                }
            )
    model_rows.append(
        {
            "component": folder,
            "selected_runtime_component": folder != "generator",
            "revision": revision,
            "files": files,
        }
    )
packages = [
    "beautifulsoup4",
    "numpy",
    "scikit-learn",
    "torch",
    "transformers",
    "sentence-transformers",
    "sentencepiece",
    "huggingface-hub",
    "llama-cpp-python",
    "streamlit",
    "pytest",
    "python-pptx",
    "pypdf",
    "pymupdf",
]
runtime = {
    "python": platform.python_version(),
    "platform": platform.platform(),
    "packages": {name: metadata.version(name) for name in packages},
    "models": model_rows,
    "torch_threads": 6,
    "device": "cpu",
    "generation_format": "GGUF Q4_K_M",
    "disclosure": "Local dependency/model identity, not an enterprise software supply-chain attestation.",
}
(root / "artifacts/runtime_manifest.json").write_text(
    json.dumps(runtime, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "extraction": [
                {k: r[k] for k in ["doc_id", "coverage", "missing_5grams"]} for r in audit
            ],
            "model_revisions": {r["component"]: r["revision"] for r in model_rows},
        },
        indent=2,
    ),
    flush=True,
)
