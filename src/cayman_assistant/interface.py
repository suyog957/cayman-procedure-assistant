"""Employee workspace views and an inspector backed by real response records."""

from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re

import streamlit as st

from .experience import (
    SHORT_NAMES,
    icon,
    source_html,
    source_integrity,
    response_badge,
    active_response,
    cited_sources,
)


def html(content: str):
    st.markdown(content, unsafe_allow_html=True)


def select_evidence(trace_id: str, label: str | None = None, view: str = "Evidence"):
    st.session_state.inspector_trace = trace_id
    st.session_state.inspector_view = view
    if label:
        st.session_state[f"source_select_{trace_id}"] = label


def queue_question(question: str):
    st.session_state.pending = question
    st.session_state.page = "Workspace"


def use_procedure(doc_id: str):
    st.session_state.scope = doc_id
    st.session_state.history = []
    st.session_state.page = "Workspace"


def reset_conversation():
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.feedback = {}
    st.session_state.pending = None
    st.session_state.inspector_trace = None
    st.session_state.inspector_view = "Evidence"
    st.session_state.page = "Workspace"


def record_feedback(trace_id: str, value: str):
    st.session_state.feedback[trace_id] = value


def sidebar(manifest: dict):
    with st.sidebar:
        html(
            '<div class="sidebar-title">Your procedure partner.</div><div class="sidebar-subtitle">A focused space to investigate branch questions and inspect the evidence.</div>'
        )
        st.button("＋  New investigation", on_click=reset_conversation, use_container_width=True)
        html('<div class="nav-label">YOUR WORKSPACE</div>')
        for page in ["Workspace", "Procedure library", "Evaluation"]:
            if st.button(
                page,
                type="primary" if st.session_state.page == page else "secondary",
                use_container_width=True,
                key=f"nav_{page}",
            ):
                st.session_state.page = page
                st.rerun()
        st.divider()
        st.selectbox(
            "Search scope",
            ["all"] + [d["doc_id"] for d in manifest["documents"]],
            format_func=lambda x: "All 11 procedures" if x == "all" else f"{x} · {SHORT_NAMES[x]}",
            key="scope",
            on_change=lambda: st.session_state.update(history=[]),
            help="The selected procedure restricts retrieval. Choose All procedures to switch topics freely.",
        )
        html(
            f'<div class="sidebar-stats"><div class="sidebar-stat"><strong>{manifest["document_count"]}</strong><span>source procedures</span></div><div class="sidebar-stat"><strong>{manifest["chunk_count"]:,}</strong><span>indexed passages</span></div></div>'
        )
        html(
            '<div class="sidebar-note"><span class="local-dot"></span>Runs on this device<br>Supplied Cayman Bank snapshot.<br>Check the cited procedure before acting.</div>'
        )
        answers = [m["result"] for m in st.session_state.messages if m["role"] == "assistant"]
        if answers:
            html('<div class="recent-label">THIS INVESTIGATION</div>')
            for r in answers[-3:]:
                label = r["question"][:47] + ("…" if len(r["question"]) > 47 else "")
                st.button(
                    label,
                    key=f"recent_{r['trace_id']}",
                    on_click=select_evidence,
                    args=(r["trace_id"],),
                    help=r["question"],
                    use_container_width=True,
                )
        if st.session_state.messages:
            export = {
                "schema_version": "2.0",
                "messages": st.session_state.messages,
                "feedback": st.session_state.feedback,
                "scope": st.session_state.scope,
                "notice": "Automatic checks are not independent correctness validation.",
            }
            st.download_button(
                "Export investigation",
                json.dumps(export, indent=2, ensure_ascii=False),
                file_name="branch_investigation.json",
                mime="application/json",
                use_container_width=True,
            )
        html(
            '<div class="sidebar-note">Use hypothetical scenarios without customer identifiers.<br><br>Interview prototype · not a Wells Fargo service.</div>'
        )


def landing(manifest: dict):
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        html(
            '<div class="hero"><div class="eyebrow">BRANCH KNOWLEDGE, WITH CONTEXT</div><h1>Clear answers.<br>Visible evidence.</h1><p>Work through a procedure question, refine the situation, and see the sources and checks behind each answer.</p><div class="hero-features">'
            + "".join(
                f'<span class="feature-pill">{icon(i)}{t}</span>'
                for i, t in [
                    ("file", "Cited guidance"),
                    ("shield", "Source checks"),
                    ("activity", "Observable workflow"),
                ]
            )
            + "</div></div>"
        )
    with right:
        html(
            '<div class="journey-card"><div class="eyebrow">WHAT HAPPENS WHEN YOU ASK</div><h3>An answer you can inspect.</h3>'
            + "".join(
                f'<div class="journey-row"><span class="journey-icon">{icon(i)}</span><span>{t}</span></div>'
                for i, t in [
                    ("search", "Find the relevant procedure"),
                    ("layers", "Keep conditions with the rule"),
                    ("shield", "Check each cited statement"),
                ]
            )
            + f'<div class="journey-foot">{manifest["document_count"]} supplied procedures · local generative AI</div></div>'
        )
    with st.form("initial_question_form", clear_on_submit=True, border=False):
        question_col, submit_col = st.columns([4.8, 1])
        with question_col:
            initial_question = st.text_input(
                "Ask a procedure question",
                placeholder="What procedure would you like to work through?",
                max_chars=1200,
                label_visibility="collapsed",
            )
        with submit_col:
            submit = st.form_submit_button(
                "Investigate →", type="primary", use_container_width=True
            )
        if submit and initial_question.strip():
            queue_question(initial_question.strip())
            st.rerun()
    html(
        '<div class="section-heading"><strong>Start with a branch scenario</strong><span>Choose a question, then make it your own.</span></div>'
    )
    scenarios = [
        (
            "coins",
            "CASH OPERATIONS",
            "How much coin can stay in a machine overnight?",
            "PR63",
            "Explore coin limits",
            "What is the overnight storage limit for a coin-counting machine?",
        ),
        (
            "file",
            "NOTARY SERVICES",
            "Can an emailed document be notarized in person?",
            "PR1000",
            "Review notary rules",
            "Can a notary notarize an emailed document if the requester is physically present?",
        ),
        (
            "shield",
            "SAVINGS BONDS",
            "Can the bank charge a bond redemption fee?",
            "PR1949",
            "Check redemption fees",
            "May the bank charge a fee to redeem a U.S. savings bond?",
        ),
    ]
    for column, (glyph, category, title, doc, button, question) in zip(
        st.columns(3, gap="medium"), scenarios
    ):
        with column, st.container(border=True):
            html(
                f'<div class="scenario-icon">{icon(glyph)}</div><div class="scenario-category">{category}</div><div class="scenario-title">{title}</div><div class="scenario-source">{doc} · Supplied procedure</div>'
            )
            st.button(
                button + " →",
                key=f"scenario_{doc}",
                on_click=queue_question,
                args=(question,),
                disabled=st.session_state.scope not in {"all", doc},
                use_container_width=True,
            )
    html(
        '<p class="small-note" style="margin-top:21px">Ask a follow-up naturally. If the evidence is incomplete, the assistant will ask for context or show the source instead of releasing an unsupported draft.</p>'
    )


def render_message(result: dict, index: int):
    badge, tone = response_badge(result["status"])
    html(
        f'<div class="message-label"><span class="assistant-emblem">{icon("spark")}</span>BRANCH ASSIST<span class="answer-type {tone}">{escape(badge)}</span></div>'
    )
    if result["status"] == "evidence_only":
        st.markdown(
            "I held back the draft because a required check did not pass. Review the original passages in the **Evidence desk** for the applicable conditions."
        )
    else:
        # Procedure amounts are currency, so dollar signs must not start math.
        st.markdown(re.sub(r"(?<!\\)\$", r"\\$", result["answer"]))
    metrics = result.get("metrics", {})
    elapsed = metrics.get("total_seconds")
    fragments = [
        f"{elapsed:.1f}s" if elapsed is not None else None,
        f"{len(result['sources'])} source passage" + ("s" if len(result["sources"]) != 1 else "")
        if result["sources"]
        else None,
        "1 correction" if metrics.get("repair_attempted") else None,
    ]
    html('<div class="answer-meta">' + " · ".join(escape(f) for f in fragments if f) + "</div>")
    selected_sources = cited_sources(result)
    if selected_sources:
        cols = st.columns(len(selected_sources))
        for col, source in zip(cols, selected_sources):
            with col:
                st.button(
                    f"[{source['label']}] {source['doc_id']}",
                    key=f"citation_{result['trace_id']}_{source['label']}",
                    on_click=select_evidence,
                    args=(result["trace_id"], source["label"]),
                    help=source["section"],
                    use_container_width=True,
                )
        html(
            '<a class="mobile-evidence-link" href="#evidence-desk">View the selected evidence ↓</a>'
        )
    if result.get("grounding"):
        st.button(
            "Inspect answer checks",
            key=f"inspect_{result['trace_id']}",
            on_click=select_evidence,
            args=(result["trace_id"], None, "Checks"),
        )


def conversation():
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                html('<div class="message-label">YOU</div>')
                st.write(message["content"])
            else:
                render_message(message["result"], i)


def evidence_view(root: Path, result: dict):
    if not result["sources"]:
        html(
            f'<div class="empty-desk"><div class="empty-desk-icon">{icon("book")}</div><h3>No evidence selected.</h3><p>This response needs more context or falls outside the supplied procedures. Earlier sources are not treated as evidence for a new question.</p></div>'
        )
        return
    by_label = {s["label"]: s for s in result["sources"]}
    label = st.selectbox(
        "Source passage",
        list(by_label),
        key=f"source_select_{result['trace_id']}",
        format_func=lambda k: f"[{k}] {by_label[k]['doc_id']} · {by_label[k]['section']}",
    )
    source = by_label[label]
    html(
        f'<span class="doc-badge">[{label}] {source["doc_id"]}</span><div class="source-title">{escape(SHORT_NAMES.get(source["doc_id"], source["title"]))}</div><div class="source-section">{escape(source["section"])}<br>{escape(source["published"])}</div>'
    )
    valid = source_integrity(root, source)
    html(
        f'<div class="integrity-line {"" if valid else "failed"}">{icon("shield")} {"Source file matches the supplied snapshot" if valid else "Source changed or unavailable — check before using"}</div>'
    )
    if source.get("expanded_from"):
        html(
            '<div class="small-note">Adjacent qualification or row continuation included to preserve context.</div>'
        )
    html(source_html(source))
    if source.get("table_id"):
        st.caption(f"Table {source['table_id']} · source row {source['row_id'] + 1}")
    with st.expander("Source provenance"):
        st.caption(source["title"])
        st.caption("Passage " + source["chunk_id"])
        st.caption("Source SHA256: " + source["source_sha256"])
        st.caption("Original file: " + source["source_file"])
        if source.get("anchor"):
            st.caption("Original section anchor: " + source["anchor"])
        st.caption(
            "Publication in the supplied document does not establish current policy authority."
        )
    with st.expander("Retrieval signals"):
        st.json(source.get("retrieval", {}))
        st.caption(
            "These are matching and ranking signals, not calibrated answer confidence. Expanded passages inherit their originating hit's signals."
        )
    path = (root / source["source_file"]).resolve()
    try:
        path.relative_to(root.resolve())
        if path.is_file():
            st.download_button(
                "Download original procedure",
                path.read_bytes(),
                file_name=path.name,
                mime="text/html",
                key=f"original_{result['trace_id']}_{label}",
                use_container_width=True,
            )
    except ValueError:
        pass


def checks_view(result: dict):
    report = result.get("grounding", {})
    if not report:
        st.caption("This older response does not contain the current check summary.")
        return
    title = (
        "Required checks passed." if result["status"] == "answered" else "A reviewable decision."
    )
    html(
        f'<div class="check-summary">{title}</div><p class="small-note">{escape(report["decision"])}</p>'
    )
    for rule in report["rules"]:
        symbol = "✓" if rule["state"] == "passed" else "!" if rule["state"] == "failed" else "–"
        html(
            f'<div class="check-row"><span class="check-state {rule["state"]}">{symbol}</span><div><strong>{escape(rule["label"])}</strong><p>{escape(rule["detail"]) if rule["state"] != "not_run" else "Not run for this response."}</p></div></div>'
        )
    claims = result.get("checks", {}).get("claim_support", {}).get("claims", [])
    if claims:
        html(
            f'<div class="section-heading"><strong>Statement-to-source map</strong><span>{report["claims_supported"]} / {len(claims)}</span></div>'
        )
        if result["status"] not in {"answered", "partial"}:
            st.caption("These checks describe the withheld draft, not a released answer.")
        for i, claim in enumerate(claims):
            supported = claim.get("supported", False)
            label = claim.get("supporting_label")
            method = (
                "Exact source wording"
                if claim.get("support_method") == "verbatim_match"
                else "NLI support screen"
            )
            quote = claim.get("support_quote", "")
            html(
                f'<div class="claim-card"><div class="claim-label">STATEMENT {i + 1}</div><p>{escape(claim["claim"])}</p><div class="claim-support {"" if supported else "failed"}">{"Supported by check" if supported else "Needs review"} · {method}</div>'
                + (f'<div class="claim-quote">{escape(quote)}</div>' if quote else "")
                + "</div>"
            )
            if label:
                st.button(
                    f"Open [{label}] evidence",
                    key=f"claim_source_{result['trace_id']}_{i}",
                    on_click=select_evidence,
                    args=(result["trace_id"], label),
                )
    if result.get("metrics", {}).get("repair_attempted"):
        st.caption(
            "One correction was attempted using the same evidence after the first draft failed checks."
        )
    html(
        '<p class="small-note" style="margin-top:18px">Automatic checks can miss errors or reject a correct answer. They do not establish independent correctness or a confidence percentage.</p>'
    )
    st.caption("Was this guidance helpful?")
    for col, value in zip(st.columns(2), ["Helpful", "Needs review"]):
        with col:
            selected = st.session_state.feedback.get(result["trace_id"]) == value
            st.button(
                ("✓ " if selected else "") + value,
                key=f"feedback_{result['trace_id']}_{value}",
                on_click=record_feedback,
                args=(result["trace_id"], value),
                use_container_width=True,
            )


def activity_view(result: dict):
    html(
        '<p class="small-note">Observed actions and decision criteria. This is an execution record, not the model’s private chain of thought.</p>'
    )
    for step in result.get("activity", []):
        symbol = "✓" if step["state"] == "complete" else "!" if step["state"] == "review" else "–"
        html(
            f'<div class="activity-step"><span class="activity-node {step["state"]}">{symbol}</span><div class="activity-body"><div class="activity-name">{escape(step["label"])}<span>{step["elapsed_seconds"]:.2f}s</span></div><p>{escape(step["detail"])}</p></div></div>'
        )
    with st.expander("Technical record"):
        st.write(
            {
                "Trace ID": result["trace_id"],
                "Model": result.get("model") or "Not used",
                "Pipeline": result.get("metrics", {}).get("pipeline_version", "Earlier version"),
                "Question resolution": result.get("metrics", {}).get("context_resolution"),
                "Generation attempts": result.get("metrics", {}).get("generation_attempts", 0),
                "Input tokens": result.get("metrics", {}).get("input_tokens", 0),
                "Output tokens": result.get("metrics", {}).get("output_tokens", 0),
            }
        )
        st.text(result["retrieval_query"])
        st.caption(
            "Source integrity and support are screening checks, not enterprise approval or proof of correctness."
        )
    st.download_button(
        "Download evidence record",
        json.dumps(result, indent=2, ensure_ascii=False),
        file_name=f"evidence_{result['trace_id']}.json",
        mime="application/json",
        key=f"trace_download_{result['trace_id']}",
        use_container_width=True,
    )


def inspector(root: Path):
    html(
        f'<div class="desk-heading" id="evidence-desk">{icon("book")} Evidence desk</div><p class="desk-subtitle">The passages, checks and activity behind a specific answer.</p>'
    )
    result = active_response(st.session_state.messages, st.session_state.inspector_trace)
    if result is None:
        html(
            f'<div class="empty-desk"><div class="empty-desk-icon">{icon("file")}</div><h3>Evidence starts with a question.</h3><p>Select a scenario or ask about a procedure. Source passages and answer checks will appear here.</p></div>'
        )
        return
    html(f'<div class="desk-question">{escape(result["question"])}</div>')
    view = st.radio(
        "Inspector view",
        ["Evidence", "Checks", "Activity"],
        horizontal=True,
        key="inspector_view",
        label_visibility="collapsed",
    )
    {
        "Evidence": lambda: evidence_view(root, result),
        "Checks": lambda: checks_view(result),
        "Activity": lambda: activity_view(result),
    }[view]()


def library(root: Path, manifest: dict):
    html('<div class="eyebrow">SUPPLIED KNOWLEDGE COLLECTION</div>')
    st.title("The procedure library.")
    st.caption(
        "Explore the original documents, inspect their publication details, or focus the workspace on a procedure."
    )
    search = st.text_input("Find a procedure", placeholder="Search a topic, procedure name or ID…")
    docs = [
        d
        for d in manifest["documents"]
        if search.lower() in (d["title"] + " " + SHORT_NAMES[d["doc_id"]]).lower()
    ]
    st.caption(f"{len(docs)} of {len(manifest['documents'])} procedures")
    if not docs:
        st.info("No matching procedure. Try a topic such as notary, coin or identification.")
    for start in range(0, len(docs), 2):
        for column, doc in zip(st.columns(2, gap="medium"), docs[start : start + 2]):
            with column, st.container(border=True):
                html(
                    f'<span class="catalog-card-icon">{icon("file")}</span><span class="doc-badge">{doc["doc_id"]}</span><div class="catalog-title">{escape(SHORT_NAMES[doc["doc_id"]])}</div><div class="catalog-details">{escape(doc["title"])}<br><br>{escape(doc["published"])}<br>{len(doc["sections"])} sections · {doc["chunks"]} indexed passages</div>'
                )
                controls = st.columns(2)
                with controls[0]:
                    st.button(
                        "Use in workspace",
                        key=f"use_{doc['doc_id']}",
                        on_click=use_procedure,
                        args=(doc["doc_id"],),
                        use_container_width=True,
                    )
                with controls[1]:
                    st.download_button(
                        "Original document",
                        (root / doc["source_file"]).read_bytes(),
                        file_name=Path(doc["source_file"]).name,
                        mime="text/html",
                        key=f"library_download_{doc['doc_id']}",
                        use_container_width=True,
                    )
                with st.expander("Source identity"):
                    st.caption("SHA256: " + doc["sha256"])
                    st.caption(
                        "Dates are from the supplied snapshot; linked procedures were not fetched."
                    )


def evaluation(root: Path):
    html('<div class="eyebrow">MEASUREMENT & LIMITS</div>')
    st.title("Evidence before confidence.")
    st.caption(
        "Inspect the recorded evaluation. Retrieval performance and generated-answer quality are different measures."
    )
    metrics = json.loads((root / "artifacts/evaluation/metrics.json").read_text(encoding="utf-8"))
    answers = metrics.get("answers")
    if not answers:
        st.info(
            "Evaluation is running. Complete results will appear after the current run finishes."
        )
        return
    html(
        f'<div class="evaluation-banner">{icon("shield")}<p>AI-authored, source-checked regression cases. These are automatic diagnostics, not an independently adjudicated accuracy benchmark. Pipeline recorded: {escape(metrics.get("pipeline_version", "1.0"))}.</p></div>'
    )
    retrieval = next(
        r for r in metrics["retrieval"] if r["split"] == "all" and r["mode"] == "hybrid"
    )
    cards = [
        (
            "EVIDENCE RETRIEVAL",
            f"{retrieval['hit_at_5'] * 100:.0f}%",
            "Labelled evidence in the top five · 30 procedure questions",
        ),
        (
            "ANSWER FACT PROXY",
            f"{answers['all_required_facts_proxy'] * 100:.1f}%",
            "All expected fact groups present · includes fallback misses",
        ),
        (
            "SOURCE-ONLY FALLBACKS",
            str(answers["evidence_only_fallbacks"]),
            f"Withheld drafts among {answers['generated_n']} evaluated generated calls",
        ),
    ]
    for column, (title, value, caption) in zip(st.columns(3), cards):
        with column, st.container(border=True):
            html(
                f'<div class="metric-title">{title}</div><div class="metric-value">{value}</div><div class="metric-caption">{caption}</div>'
            )
    html(
        '<div class="section-heading"><strong>What the evaluation actually measures</strong></div>'
    )
    st.dataframe(
        [
            {
                "Dimension": "Retrieval",
                "Included measure": "Evidence hit@5 and MRR@5",
                "Limit": "Does not establish complete evidence or a correct answer",
            },
            {
                "Dimension": "Accuracy / completeness",
                "Included measure": "Required-fact phrase groups",
                "Limit": "Can miss paraphrases or pass incorrect text with expected words",
            },
            {
                "Dimension": "Grounding",
                "Included measure": "Citation, numeric and claim checks",
                "Limit": "Automatic support checks remain fallible",
            },
            {
                "Dimension": "Conversation",
                "Included measure": "Four regression conversations",
                "Limit": "Some ambiguous follow-ups remain unresolved",
            },
            {
                "Dimension": "Responsiveness",
                "Included measure": f"CPU p50 {answers['p50_seconds']:.1f}s / p95 {answers['p95_seconds']:.1f}s",
                "Limit": "Serial local requests; cold model load excluded",
            },
        ],
        hide_index=True,
        use_container_width=True,
    )
    st.caption(
        "A real pilot needs independent SME review, authoritative policy versions, employee access controls, and employee task-success measurement."
    )
    for column, filename, label in zip(
        st.columns(3),
        [
            "docs/EVALUATION_REPORT.pdf",
            "SOLUTION_OVERVIEW.pdf",
            "submission/Cayman_Procedure_Assistant.pdf",
        ],
        ["Evaluation report", "Solution overview", "Presentation"],
    ):
        with column:
            st.download_button(
                label,
                (root / filename).read_bytes(),
                file_name=Path(filename).name,
                mime="application/pdf",
                use_container_width=True,
            )
