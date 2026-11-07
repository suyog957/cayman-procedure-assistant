"""Download public model weights only; procedure content is never uploaded."""
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from pathlib import Path
import argparse
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--include-baseline", action="store_true")
args = parser.parse_args()
models = [
    ("embedder", "sentence-transformers/all-MiniLM-L6-v2", "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"),
    ("reranker_v2", "cross-encoder/ms-marco-MiniLM-L6-v2", "233902d25c440f23af6f7d6e94d2946bac0bee0a"),
    ("verifier", "cross-encoder/nli-deberta-v3-small", "fa2804872c3b4bd748f38c0185cc85775361e735"),
    ("generator_v2", "Qwen/Qwen3-4B-GGUF", "bc640142c66e1fdd12af0bd68f40445458f3869b"),
]
if args.include_baseline:
    models.append(("generator", "Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"))
for name, repo, revision in models:
    print(f"Downloading {repo}", flush=True)
    target = ROOT / "models" / name
    patterns = [
        "*.json", "*.safetensors", "*.txt", "*.model", "README.md",
        "1_Pooling/*", "2_Normalize/*",
    ] if name != "generator_v2" else ["Qwen3-4B-Q4_K_M.gguf", "README.md"]
    snapshot_download(repo, revision=revision, local_dir=target, allow_patterns=patterns, max_workers=3)
    print(f"Ready: {target}", flush=True)
