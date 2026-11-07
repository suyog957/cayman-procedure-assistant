"""Isolated evaluation runs; publish complete evidence bundles explicitly."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import json


def new_run_directory(root: Path, requested: Path | None, kind: str) -> Path:
    canonical = (root / "artifacts/evaluation").resolve()
    target = ((root / requested) if requested else root / "artifacts/experiments" /
              (kind + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:6])).resolve()
    if target == canonical:
        raise ValueError("Use an isolated output directory; --publish promotes a completed full run.")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Evaluation output directory must be new or empty.")
    target.mkdir(parents=True, exist_ok=True)
    return target


def publish_completed_run(run: Path, destination: Path, expected_ordinary: int, expected_total: int):
    names = ("metrics.json", "retrieval_details.json", "answer_details.json")
    # Canonical JSON uses LF so its hashes survive the repository's checkout
    # normalization on Windows and Unix. JSON string escapes are unaffected.
    payloads = {name: (run / name).read_bytes().replace(b"\r\n", b"\n") for name in names}
    metrics = json.loads(payloads["metrics.json"])
    answers = json.loads(payloads["answer_details.json"])
    retrieval = json.loads(payloads["retrieval_details.json"])
    if (metrics.get("answers", {}).get("ordinary_n") != expected_ordinary
            or len(answers) != expected_total or len(retrieval) != expected_ordinary * 3):
        raise ValueError("Incomplete evaluation; the published results were not changed.")
    manifest = {"completed_utc": datetime.now(timezone.utc).isoformat(), "run_directory": str(run),
                "files": {name: sha256(data).hexdigest() for name, data in payloads.items()}}
    payloads["run_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=True)
    pending = []
    for name, data in payloads.items():
        temporary = destination / (name + ".pending")
        temporary.write_bytes(data)
        pending.append((temporary, destination / name))
    # Each file is replaced atomically; the manifest is published last, so a
    # consumer can detect an interrupted multi-file promotion by its hashes.
    for temporary, target in pending:
        temporary.replace(target)
