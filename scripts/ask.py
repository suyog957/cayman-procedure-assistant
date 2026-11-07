"""CLI smoke test and serializable answer trace."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cayman_assistant.assistant import Assistant, Turn

parser = argparse.ArgumentParser()
parser.add_argument("questions", nargs="+")
parser.add_argument("--retrieval-only", action="store_true")
parser.add_argument("--output")
parser.add_argument("--backend", choices=["qwen3", "qwen2.5"], default="qwen3")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
assistant = Assistant(root, load_generator=not args.retrieval_only, generator_backend=args.backend)
history, results = [], []
for question in args.questions:
    result = assistant.answer(question, history)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True), flush=True)
    results.append(result.to_dict())
    if result.sources:
        history.append(Turn(question, result.retrieval_query, result.sources[0]["doc_id"]))
if args.output:
    Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
if assistant.generator and hasattr(assistant.generator, "close"):
    assistant.generator.close()
