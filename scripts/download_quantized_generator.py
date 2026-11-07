"""Download the official Qwen 4-bit model for a stronger CPU baseline."""
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from pathlib import Path
from huggingface_hub import snapshot_download
root = Path(__file__).resolve().parents[1]
snapshot_download("Qwen/Qwen3-4B-GGUF", revision="bc640142c66e1fdd12af0bd68f40445458f3869b", local_dir=root / "models/generator_v2",
                  allow_patterns=["Qwen3-4B-Q4_K_M.gguf", "README.md"], max_workers=2)
print("Qwen3 4B Q4_K_M ready", flush=True)
