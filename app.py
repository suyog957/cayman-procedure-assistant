"""Interactive demo. Launch with: python -m streamlit run app.py"""
from pathlib import Path
import json
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from cayman_assistant.assistant import Assistant, Turn

st.set_page_config(page_title="Cayman · Procedure Assistant", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp { background:#f5f7fa; color:#172d42; }
[data-testid="stSidebar"] { background:#e9eef4; }
.block-container { padding-top:2.4rem; max-width:1120px; }
h1,h2,h3 { color:#102b43; letter-spacing:-0.035em; }
[data-testid="stChatMessage"] { border:1px solid #dce4ed; border-radius:14px; background:white; }
.eyebrow { color:#087f83; font-size:12px; font-weight:700; letter-spacing:.14em; }
.intro { color:#52667b; font-size:17px; max-width:740px; margin-bottom:24px; }
.metric { background:#fff; border:1px solid #dce4ed; padding:14px 18px; border-radius:10px; }
div.stButton > button { border-radius:9px; }
[data-testid="stToolbar"] { display:none; }
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_assistant():
    return Assistant(ROOT)


@st.cache_data
def get_manifest():
    return json.loads((ROOT / "artifacts/index/corpus_manifest.json").read_text(encoding="utf-8"))


for key, initial in [("messages", []), ("history", []), ("feedback", {}), ("pending", None)]:
    if key not in st.session_state:
        st.session_state[key] = initial

manifest_path = ROOT / "artifacts/index/corpus_manifest.json"
if not manifest_path.exists() or not (ROOT / "models/generator_v2/Qwen3-4B-Q4_K_M.gguf").exists():
    st.error("Setup is incomplete. Run the setup steps in README.md, then reload this page.")
    st.stop()
manifest = get_manifest()

with st.sidebar:
    st.markdown("### ◈ Cayman Bank")
    st.caption("BRANCH KNOWLEDGE · LOCAL DEMO")
    st.divider()
    st.markdown("**Procedure collection**")
    st.caption(f"{manifest['document_count']} documents · {manifest['chunk_count']:,} passages")
    for d in manifest["documents"]:
        with st.expander(d["doc_id"] + " · " + d["title"].split(" - PR")[0][:34]):
            st.write(d["title"])
            st.caption(d["published"])
            st.download_button("Download procedure", (ROOT / d["source_file"]).read_bytes(), file_name=Path(d["source_file"]).name,
                               mime="text/html", key="source_" + d["doc_id"])
    st.divider()
    st.caption("Answers use the supplied document snapshot. Check the cited procedure before acting. Use hypothetical examples without customer identifiers.")
    st.caption("Generation: Qwen3 4B · 4-bit · on this computer")
    if st.button("Start a new conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.feedback = {}
        st.session_state.pending = None
        st.rerun()
    if st.session_state.messages:
        st.download_button("Export this conversation", json.dumps(st.session_state.messages, indent=2, ensure_ascii=False),
                           file_name="procedure_conversation.json", mime="application/json", use_container_width=True)

st.markdown('<div class="eyebrow">OPERATIONAL KNOWLEDGE / EVIDENCE FIRST</div>', unsafe_allow_html=True)
st.title("A clearer path through procedures.")
st.markdown('<div class="intro">Ask a branch procedure question, refine the situation, and inspect the passages behind the answer.</div>', unsafe_allow_html=True)

if not st.session_state.messages:
    columns = st.columns(3)
    for col, label, question in zip(columns,
        ["Coin machine limits", "Notary document rules", "Savings bond redemption"],
        ["What is the overnight storage limit for a coin-counting machine?",
         "Can a notary notarize an emailed document if the requester is physically present?",
         "What is the savings bond redemption limit for an account open less than 12 months, and what is the exception?"]):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.pending = question
                st.rerun()
    st.caption("Try a follow-up: “And is monthly testing done in single or dual control?” You can switch topics or start a new conversation at any time.")


def render_result(result: dict, index: int):
    st.markdown(result["answer"])
    labels = {"answered": "Generated answer · inspect citations", "partial": "Partial support · review sources",
              "evidence_only": "Retrieved excerpts · generated answer withheld", "unsupported": "Insufficient source support",
              "clarify": "More context needed", "refused": "Outside the assistant’s task"}
    st.caption(labels.get(result["status"], result["status"]))
    if result["sources"]:
        with st.expander(f"View {len(result['sources'])} source passages"):
            for source in result["sources"]:
                st.markdown(f"**[{source['label']}] {source['doc_id']} · {source['section']}**")
                st.caption(source["published"] + " · " + source["chunk_id"])
                st.text(source["text"])
                if source.get("table_id"):
                    st.caption(f"Table {source['table_id']} · row {source['row_id']} (zero-based)")
                st.caption("Source SHA256: " + source["source_sha256"])
                st.divider()
    if result.get("metrics"):
        with st.expander("Answer details"):
            st.write({"Model": result.get("model") or "Generation not used",
                      "Elapsed seconds": result["metrics"].get("total_seconds"),
                      "Question context": result["metrics"].get("context_resolution"),
                      "Trace": result["trace_id"]})
            st.caption("Citation and number checks are mechanical safeguards; they do not establish that every claim is correct or complete.")
    if result["status"] in {"answered", "partial", "evidence_only"}:
        selected = st.radio("Was this helpful?", ["Not rated", "Helpful", "Needs review"],
                            key=f"feedback_{index}", horizontal=True, label_visibility="collapsed")
        st.session_state.feedback[result["trace_id"]] = selected


for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_result(message["result"], i)

question = st.chat_input("Ask about a supplied procedure…", max_chars=1200)
if st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Finding procedure passages and preparing an answer…"):
                assistant = get_assistant()
                history = [Turn(**t) for t in st.session_state.history[-4:]]
                result = assistant.answer(question, history).to_dict()
            st.session_state.messages.append({"role": "assistant", "result": result})
            if result["sources"]:
                st.session_state.history.append({"question": question, "retrieval_query": result["retrieval_query"],
                                                 "doc_id": result["sources"][0]["doc_id"]})
            elif result["status"] in {"unsupported", "refused"}:
                # A refused/unsupported topic must not inherit an earlier subject.
                st.session_state.history = []
            render_result(result, len(st.session_state.messages) - 1)
            # Rebuild sidebar export data after adding the completed turn.
            st.rerun()
        except Exception:
            st.error("The assistant could not complete this request. Check the local setup and model files, then try again. Your question was not sent to an external model service.")
