import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from pathlib import Path
from huggingface_hub import snapshot_download
root = Path(__file__).resolve().parents[1]
for name, repo in [("reranker_v2", "cross-encoder/ms-marco-MiniLM-L6-v2"),
                   ("verifier", "cross-encoder/nli-deberta-v3-small")]:
    print(repo, flush=True)
    snapshot_download(repo, local_dir=root / "models" / name,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "README.md"], max_workers=3)
    print("Ready", name, flush=True)
