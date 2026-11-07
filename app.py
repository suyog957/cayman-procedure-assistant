"""Branch Assist: an observable, evidence-grounded local procedure workspace."""
from pathlib import Path
import json
import logging
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from cayman_assistant.assistant import Assistant, Turn, Response
from cayman_assistant.experience import brand_header, icon
from cayman_assistant.interface import (html, sidebar, landing, conversation, inspector, library, evaluation,
                                        queue_question, response_badge)

st.set_page_config(page_title="Branch Assist · Procedure workspace", page_icon="🧭", layout="wide", initial_sidebar_state="auto")
html('<style>' + (ROOT / "assets/workspace.css").read_text(encoding="utf-8") + '</style>')
html(brand_header(ROOT))


@st.cache_resource(show_spinner=False)
def get_assistant():
    return Assistant(ROOT)


defaults = {"messages": [], "history": [], "feedback": {}, "pending": None, "page": "Workspace",
            "scope": "all", "inspector_trace": None, "inspector_view": "Evidence", "reset_inspector": False}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
if st.session_state.reset_inspector:
    st.session_state.inspector_view = "Evidence"
    st.session_state.reset_inspector = False

manifest_path = ROOT / "artifacts/index/corpus_manifest.json"
if not manifest_path.exists() or not (ROOT / "models/generator_v2/Qwen3-4B-Q4_K_M.gguf").exists():
    st.error("Setup is incomplete. Run the local setup steps in README.md, then reload.")
    st.stop()
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
sidebar(manifest)
if st.session_state.page == "Procedure library":
    library(ROOT, manifest)
    st.stop()
if st.session_state.page == "Evaluation":
    evaluation(ROOT)
    st.stop()

if not st.session_state.messages and not st.session_state.pending:
    landing(manifest)
    st.stop()

question = st.chat_input("Ask about a procedure, or refine your scenario…", max_chars=1200)
if st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None
if question:
    st.session_state.messages.append({"role": "user", "content": question})

scope_label = "All 11 procedures" if st.session_state.scope == "all" else st.session_state.scope
html(f'<div class="workspace-heading"><div><div class="eyebrow" style="margin-top:0">PROCEDURE WORKSPACE</div><h1>Let’s work through it.</h1><p>Ask, refine, and inspect the evidence behind the answer.</p></div><div class="scope-pill">{icon("shield")}{scope_label}</div></div>')
left, right = st.columns([1.52, 1], gap="large")
with left:
    html('<div class="workspace-label">YOUR INVESTIGATION</div>')
    chat_slot = st.container(height=625, border=True)
    with chat_slot:
        conversation()
    latest = next((m["result"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
    if latest and latest.get("followups") and not question:
        st.caption("Continue the investigation")
        for col, suggestion in zip(st.columns(2), latest["followups"][:2]):
            with col:
                st.button(suggestion, key="follow_" + suggestion, on_click=queue_question,
                          args=(suggestion,), use_container_width=True)
with right:
    with st.container(height=690, border=True):
        inspector(ROOT)

if question:
    with chat_slot, st.chat_message("assistant"):
        with st.status("Preparing the local assistant…", expanded=True) as status:
            progress = st.empty()
            observed = {}

            def on_event(event):
                observed[event["key"]] = event
                status.update(label=event["label"], state="running")
                with progress.container():
                    for step in observed.values():
                        mark = "✓" if step["state"] == "complete" else "!" if step["state"] in {"review", "blocked"} else "•"
                        st.caption(f"{mark} {step['label']}")

            try:
                assistant = get_assistant()
                history = [Turn(**turn) for turn in st.session_state.history[-4:]]
                result = assistant.answer(question, history, on_event=on_event,
                                          scope_doc_id=None if st.session_state.scope == "all" else st.session_state.scope).to_dict()
                status.update(label=response_badge(result["status"])[0], state="complete", expanded=False)
            except Exception:
                logging.getLogger(__name__).exception("Local procedure request failed")
                result = Response("The local assistant could not complete this request. Check the local model setup and try again.",
                                  "unsupported", question, question).to_dict()
                status.update(label="The local assistant needs attention", state="error", expanded=False)
    st.session_state.messages.append({"role": "assistant", "result": result})
    if result["status"] in {"answered", "partial", "evidence_only"} and result["sources"]:
        st.session_state.history.append({"question": question, "retrieval_query": result["retrieval_query"],
                                         "doc_id": result["sources"][0]["doc_id"]})
    elif result["status"] in {"unsupported", "refused"}:
        st.session_state.history = []
    st.session_state.inspector_trace = result["trace_id"]
    st.session_state.reset_inspector = True
    st.rerun()
