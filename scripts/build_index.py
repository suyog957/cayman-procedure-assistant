from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cayman_assistant.ingest import ingest
from cayman_assistant.retrieval import build_embeddings

root = Path(__file__).resolve().parents[1]
manifest = ingest(root, root / "Cayman_Bank_HTML_Files 2", root / "artifacts" / "index")
print(f"Parsed {manifest['document_count']} documents into {manifest['chunk_count']} chunks", flush=True)
for doc in manifest["documents"]:
    print(doc["doc_id"], doc["words"], "words;", doc["chunks"], "chunks;", doc["published"], flush=True)
print(build_embeddings(root), flush=True)
