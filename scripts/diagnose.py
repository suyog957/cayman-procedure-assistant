from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cayman_assistant.retrieval import Retriever
from cayman_assistant.verification import Verifier

root = Path(__file__).resolve().parents[1]
r = Retriever(root)
for question in [
    "Can a business account require multiple signatures?",
    "What notary service limit may a branch apply per requester?",
    "What control level applies to monthly coin-counting machine testing?",
]:
    print(question, flush=True)
    for h in r.search(question, k=8):
        print(h.chunk.chunk_id, round(h.rerank, 2), h.chunk.section, h.chunk.text[:150], flush=True)
v = Verifier(root)
old = json.loads((root / "artifacts/experiments/initial_tinybert/answer_details.json").read_text())
for row in old[:6]:
    if row["result"]["status"] == "answered":
        print(
            row["id"],
            json.dumps(v.check(row["result"]["answer"], row["result"]["sources"]), indent=2),
            flush=True,
        )
