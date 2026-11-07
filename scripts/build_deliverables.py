"""Build six editable slides, a matching PDF, reports and source-free package.

Deck content and measured figures come from the final corpus/evaluation files.
No source code, model files or evaluation internals enter the submission ZIP.
"""
from __future__ import annotations

from pathlib import Path
from html import escape
import json
import re
import textwrap
import zipfile
import xml.etree.ElementTree as ET

import pymupdf as fitz
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"
OUT.mkdir(exist_ok=True)
CORPUS = json.loads((ROOT / "artifacts/index/corpus_manifest.json").read_text())
METRICS = json.loads((ROOT / "artifacts/evaluation/metrics.json").read_text())
ANSWERS = json.loads((ROOT / "artifacts/evaluation/answer_details.json").read_text())
if "answers" not in METRICS:
    raise SystemExit("Complete the generative evaluation before building final deliverables")
A = METRICS["answers"]
generated_rows = [row for row in ANSWERS if row['result']['generator_used']]
# Aggregate from raw diagnostics so later-added guards are represented in the
# summary even when an earlier evaluator binary produced the same raw run.
mechanical_passes = [row for row in generated_rows if (
    row['result']['checks'].get('valid_citations') and row['result']['checks'].get('all_paragraphs_cited')
    and row['result']['checks'].get('all_claims_attributed',True) and not row['result']['checks'].get('numeric_citation_conflicts')
    and not row['result']['checks'].get('novel_numbers') and not row['result']['checks'].get('comparison_conflicts')
    and 0 < row['result']['checks'].get('word_count',999) <= 190)]
draft_lengths = [row['result']['checks']['word_count'] for row in generated_rows if 'word_count' in row['result']['checks']]
A['mechanical_validation_pass_rate'] = round(len(mechanical_passes) / len(generated_rows),4)
A['mean_word_count'] = round(sum(draft_lengths)/len(draft_lengths),1)
A['draft_word_count_n'] = len(draft_lengths)
METRICS['answers'] = A
(ROOT / 'artifacts/evaluation/metrics.json').write_text(json.dumps(METRICS,indent=2),encoding='utf-8')
BY_ID = {r["id"]: r for r in ANSWERS}
R = {r["mode"]: r for r in METRICS["retrieval"] if r["split"] == "all"}
browser_file=ROOT / "artifacts/browser_check.json"
browser_result=json.loads(browser_file.read_text()) if browser_file.exists() else {}
browser_ok=browser_result.get('pipeline_version')=='2.0' and all(browser_result.get(k) for k in ['welcome_loaded','followup_pass','export_includes_latest_turn','second_session_isolated','reset_pass','claim_map_pass','activity_record_pass','library_search_and_scope_pass'])
browser_summary=("The live browser integration check passed actual generation, an explicit single-versus-dual-control follow-up, source inspection, complete transcript export, independent browser sessions and reset. The browser reported no client errors. Results and screenshots are retained under `artifacts/`." if browser_ok else "Browser integration results are retained under `artifacts/` when the optional live browser check has completed.")
test_file=ROOT / 'artifacts/test_results.xml'
test_suites=list(ET.parse(test_file).getroot().iter('testsuite')) if test_file.exists() else []
test_total=sum(int(s.attrib.get('tests',0)) for s in test_suites)
test_failures=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in test_suites)
test_summary=f"The recorded automated test run contains {test_total} tests with {test_failures} failures/errors." if test_suites else "Run the automated tests using the README instructions."

NAVY = "3B3331"
TEAL = "D71E28"
LIGHT = "F9F7F6"
INK = "3B3331"
MUTED = "787070"
WHITE = "FFFFFF"
LINE = "E2DEDE"
GOLD = "FFCD41"


def pct(v):
    return f"{100*v:.1f}%"


def rgb(value):
    return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Pt(960)
        self.prs.slide_height = Pt(540)
        self.pdf = fitz.open()
        self.slide = None
        self.page = None

    def new(self, number, section, title, subtitle="", dark=False):
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.page = self.pdf.new_page(width=960, height=540)
        fill = TEAL if dark else LIGHT
        self.rect(0, 0, 960, 540, fill)
        self.text(40, 24, 800, 20, f"BRANCH ASSIST / INTERVIEW PROTOTYPE / {section.upper()}", 10, GOLD if dark else TEAL, True)
        if dark:
            logo = ROOT / "assets/brand/wells-fargo-wordmark.png"
            self.slide.shapes.add_picture(str(logo), Pt(760), Pt(24), width=Pt(160))
            self.page.insert_image(fitz.Rect(760,24,920,41),filename=str(logo),keep_proportion=True)
        self.text(40, 65, 880, 80, title, 29, WHITE if dark else NAVY, True)
        if subtitle:
            self.text(40, 136, 880, 35, subtitle, 13, "FCEDEE" if dark else MUTED)
        self.rect(40, 505, 880, 1, "EF777D" if dark else LINE)
        self.rect(40, 505, 880 * number/6, 2, GOLD if dark else TEAL)
        self.text(40, 516, 800, 15, "EXERCISE PROTOTYPE  ·  SUPPLIED CAYMAN BANK DOCUMENTS  ·  NOVEMBER 7, 2026", 8, "FBE5E6" if dark else MUTED)
        self.text(887, 515, 36, 16, f"{number:02d}/06", 9, "FBE5E6" if dark else MUTED)

    def rect(self, x, y, w, h, fill, border=None, rounded=False):
        shape = self.slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rounded else MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                                             Pt(x), Pt(y), Pt(w), Pt(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
        if border:
            shape.line.color.rgb = RGBColor.from_string(border)
            shape.line.width = Pt(.6)
        else:
            shape.line.fill.background()
        self.page.draw_rect(fitz.Rect(x,y,x+w,y+h), color=rgb(border) if border else None, fill=rgb(fill), width=.6)

    def text(self, x, y, w, h, text, size=16, color=INK, bold=False):
        fontfile = str(Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf"))
        fontname = "SegoeBold" if bold else "Segoe"
        final_size = size
        while True:
            spare = self.page.insert_textbox(fitz.Rect(x,y,x+w,y+h), text, fontsize=final_size,
                                             fontname=fontname, fontfile=fontfile, color=rgb(color), lineheight=1.14)
            if spare >= 0:
                break
            final_size -= .5
            if final_size < size - 3:
                raise ValueError(f"Text overflow: {text[:70]}")
        box = self.slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.name = "Segoe UI"
            p.font.size = Pt(final_size)
            p.font.bold = bold
            p.font.color.rgb = RGBColor.from_string(color)
            p.space_after = Pt(3)

    def card(self, x, y, w, h, title, body, accent=TEAL):
        self.rect(x,y,w,h,WHITE,LINE,rounded=True)
        self.rect(x,y,4,h,accent)
        self.text(x+18,y+15,w-36,34,title,16,NAVY,True)
        self.text(x+18,y+57,w-36,h-67,body,14,MUTED)

    def notes(self, text):
        self.slide.notes_slide.notes_text_frame.text = textwrap.dedent(text).strip()


deck = Deck()
deck.new(1, "The business problem", "Branch guidance employees\ncan inspect and question.", dark=True)
deck.text(40, 174, 525, 78, "Turn a procedure search into a concise answer,\nwith the applicable conditions and visible evidence.", 21, WHITE)
for x, value, label in [(40,"11","supplied procedures"),(245,f"{CORPUS['chunk_count']:,}","traceable passages"),(450,"Local","generative inference")]:
    deck.text(x,286,190,52,value,37,GOLD,True)
    deck.text(x,341,190,30,label,12,"FCEDEE")
deck.rect(674,178,246,221,"B01C24")
deck.text(694,198,205,28,"DELIVERED",11,GOLD,True)
deck.text(694,237,205,130,"Working chat\nFollow-up questions\nSource inspection\nMeasured evaluation\nSix-slide presentation",16,WHITE)
deck.text(40,418,858,48,"Decision support over the supplied snapshot.\nEmployees verify the cited procedure before acting; the assistant does not execute transactions.",14,"FCEDEE")
deck.notes("""
    Timing: 0:00–3:00. Start with the employee's task, not the model name.

    Branch employees need to find a specific operational requirement in long documents, often while a customer is waiting. The problem is not simply locating a keyword. The employee needs to understand the right action for the customer's particular situation, including qualifications and exceptions.

    I built a working conversational assistant over all eleven supplied procedures. The collection contains roughly seventy-nine thousand extracted words and many tables. A business-account procedure is substantially larger than the others, so treating every document as one unit would make retrieval uneven.

    The assistant generates an answer from retrieved passages and lets the employee inspect the evidence. It can carry a scenario into a follow-up, recognize a new topic, request clarification, and withhold a draft that fails checks. It does not perform transactions. Its knowledge boundary is the supplied snapshot; linked procedures and current production policy are outside that boundary.

    The deliverables include the local application, explicit evaluation cases, raw response traces, architecture decisions, and this six-slide presentation with a timed demonstration. Implementation source is kept separate from the presentation materials, as the assignment requires.

    Generative AI was used both to assist development and to generate runtime answers. The evaluation labels were AI-authored and source-checked, which means they are useful regression material but not independent ground truth. I will explain measured results and observed weaknesses rather than imply this is an approved production banking tool.

    The leadership question is whether the approach is promising enough for independent operational validation. The objective for a future pilot would be faster access to correct guidance with clear evidence and appropriate escalation. No employee productivity savings have been measured yet. Transition: the next slide shows how the system creates that evidence boundary.
""")

deck.new(2, "Methodology and architecture", "Retrieve the evidence before generating the answer.", "A transparent RAG pipeline, sized for eleven procedures and a local CPU demonstration.")
deck.text(40,181,180,22,"PREPARE ONCE",11,TEAL,True)
for x, title, sub in [(40,"Original HTML","11 files · immutable source hashes"),(340,"Structural parsing","Sections · lists · table conditions"),(640,"Local indexes","BM25 + 384-dimensional vectors")]:
    deck.rect(x,211,280,72,WHITE,LINE)
    deck.text(x+14,220,250,24,title,16,NAVY,True)
    deck.text(x+14,250,250,22,sub,11,MUTED)
deck.text(40,308,180,22,"EACH QUESTION",11,TEAL,True)
steps=[("Question +\nsession context",NAVY),("Hybrid retrieval\n+ reranking",TEAL),("Bounded evidence\n+ local Qwen3",NAVY),("Claim checks +\none correction",TEAL),("Answer +\nsource passages",NAVY)]
for i,(label,fill) in enumerate(steps):
    x=40+i*180
    deck.rect(x,341,160,70,fill)
    deck.text(x+12,355,136,46,label,14,WHITE,True)
    if i < 4:
        deck.text(x+162,359,18,30,"›",21,TEAL,True)
deck.text(40,440,880,42,"Why RAG: source updates and citations stay explicit. Exact local search avoids unnecessary infrastructure.\nWeak retrieval → abstain. Failed answer checks → clearly labelled source excerpts.",14,INK)
deck.notes("""
    Timing: 3:00–6:30. Trace the complete path and explain the alternatives.

    The offline path parses the eleven original HTML documents. The parser removes presentation-only material but preserves headings, instructions and table conditions. It produces a passage store with metadata and source hashes. BM25 term statistics and normalized embedding vectors are built from the same passages.

    At question time, the application resolves whether the user is asking a new question or continuing an earlier scenario. It retrieves exact lexical matches and semantic matches, combines the rankings with reciprocal rank fusion, and uses a cross-encoder to rerank the candidates. Only a small selected evidence pack goes to the generative model.

    The final generator is a locally executed Qwen3 four-billion-parameter model in four-bit GGUF form through llama.cpp. Quantization makes a larger model practical on the available CPU laptop. This was an empirical choice: the initial smaller model frequently added irrelevant details or produced drafts that were withheld. A stronger approved private or hosted model should be compared before any real deployment.

    The output passes citation, number, length and claim-support screening. Explicit claim citations bind locally, and numeric values must match the passage actually cited. A failed draft can receive one correction using the same evidence and deterministic failed-check feedback. The revised answer must pass the same checks. Otherwise the interface shows labelled source excerpts. Actual actions, durations and the release decision are exposed in the activity record, not a simulated chain of thought. Weak retrieval produces clarification or abstention.

    I chose RAG because the task is access to a small, revisable evidence collection. Fine-tuning does not itself give reliable citations or explicit deletion of obsolete procedures. Sending the entire corpus would be inefficient and would expose the generator to many unrelated conditions. Search alone is a valuable fallback but would not satisfy the requested generative chat experience.

    The implementation uses a straightforward pipeline instead of an autonomous transaction agent. The corpus fits exact in-memory vector search, so a managed vector database is unnecessary for this exercise. Production entitlements, identity, signed source releases, concurrency and monitoring remain separate platform work. Transition: the next slide explains the most important content decision—keeping each instruction attached to its conditions.
""")

deck.new(3, "Content and information retrieval", "Preserve conditions, exceptions and source identity.", "Shorter passages reduce competing instructions; structured rows preserve situation-to-action relationships.")
deck.card(40,185,424,125,"Structure-aware preparation",f"139 HTML tables, including nested tables\n~110 narrative words; 20-word overlap for long blocks\nTable labels, row conditions and source anchors retained")
deck.card(40,326,424,146,"Retrieval with complementary strengths","BM25: identifiers and exact terms\nVectors: paraphrases and related language\nRRF top candidates → cross-encoder reranking\nUp to 3 passages / 520 words sent as evidence")
deck.rect(490,185,430,175,WHITE,LINE)
deck.text(509,199,390,30,"EXAMPLE: PR63 / MONTHLY TESTING",11,TEAL,True)
deck.text(509,236,390,39,"Situation and control stay together",19,NAVY,True)
deck.text(509,283,385,56,"Monthly testing → single control\nWeekly balancing / random monthly count → dual control",15,INK)
deck.text(490,383,424,84,"Every passage retains procedure ID, section, publication text, original filename and SHA256.\nChanged source files require an index rebuild.",15,MUTED)
deck.notes("""
    Timing: 6:30–10:00. Use the monthly-testing example to make the data decisions tangible.

    The input files are HTML exports with meaningful policy classes, not just standard headings. Parsing only h1 or h2 tags would miss much of the structure. The parser explicitly recognizes the title, publication date, major sections and subsections. It decodes UTF-8 directly to preserve punctuation and does not follow external links or execute scripts.

    Tables contain many operational branches. The parser serializes rows with their column labels, carries conditions through rowspans, accounts for colspans, and includes nested table text once. Long rows repeat the leftmost condition in continuation passages. That reduces, but does not eliminate, the risk of an action being detached from its situation. A production solution should represent complex branching tables more formally and have subject-matter review of extraction semantics.

    Narrative grouping targets roughly one hundred and ten whitespace words within a section, with twenty-word overlap for long blocks. These are word targets, not exact model-token counts. The generator also has a hard prompt-token budget. The initial larger passages diluted narrow rules; shorter passages improved retrieval on the regression questions.

    The coin-machine procedure illustrates why distinctions matter: monthly testing is single control, while weekly balancing and random monthly cash counts are dual control. A broad answer about coin-machine tasks can be fluent and still omit the distinction the employee needs.

    Keyword matching preserves exact transaction codes and identifiers. Dense search handles paraphrases. RRF combines ranking positions rather than comparing incomparable raw scores. The cross-encoder considers the question and passage jointly. On this small collection, exact vector search is fast and operationally simple.

    Every passage has a source hash and stable identity. An identical rebuild preserves IDs; a changed source intentionally changes them. The text-preservation audit found all checked source paragraph five-word sequences, but that does not prove correct table semantics. Source versions and effective policy authority require more than a publication date. Transition: now show how these choices appear to an employee in conversation.
""")

deck.new(4, "Experience and follow-ups", "Carry the scenario forward. Retrieve fresh evidence.", "Answers, source inspection, clarification, topic changes and honest fallback belong in the same workflow.")
deck.rect(40,185,535,284,WHITE,LINE)
deck.text(58,201,497,20,"DEMONSTRATION SCENARIO / PR63 SOURCE FACTS",10,TEAL,True)
deck.text(58,234,497,36,"What is the coin-counting machine overnight limit?",16,NAVY,True)
deck.text(58,279,497,46,"$5,250 in a single machine. [Source: PR63]",17,TEAL,True)
deck.rect(58,337,497,1,LINE)
deck.text(58,354,497,40,"And is monthly testing done in single or dual control?",16,NAVY,True)
deck.text(58,400,497,48,"Single control. Inspect the cited procedure passage.",17,TEAL,True)
deck.text(610,187,300,35,"Useful context, bounded memory",18,NAVY,True)
deck.text(610,235,300,98,"Prior user questions resolve context.\nNew topics replace old scope.\nPrevious generated claims are not evidence.",14,MUTED)
deck.text(610,350,300,35,"Inspectable outcomes",18,NAVY,True)
deck.text(610,397,300,74,"Evidence / checks / actual activity\nFailed draft: one bounded correction\nStill unsupported: source review",14,MUTED)
deck.notes("""
    Timing: 10:00–13:00. The short dialogue summarizes source-checked facts; the demonstration will show actual generated responses and status.

    The interface starts with three concrete example questions and a visible eleven-document collection. An employee can ask a question, inspect the returned sources, download an original procedure, ask a follow-up, switch topics or reset. Each source panel includes the section, publication text and passage identity. A trace and elapsed time are available without exposing implementation code.

    Session memory is scoped to the browser conversation. Shared cached model objects do not contain user histories. The resolver prioritizes explicit procedure IDs and recognizes a small set of named topics. A named new topic overrides previous scope. An elliptical follow-up can retain the prior question and procedure reference, but it always triggers new retrieval.

    For the coin-machine example, the follow-up names a new task in the same procedure. The resolver retains the procedure scope but avoids repeating overnight-limit keywords that would distract retrieval from testing. For a notary question followed by 'what if the requester is physically present', the prior emailed-document scenario remains necessary context. These are different conversational cases and are tested separately.

    The resolver is deterministic and transparent, not a claim of unrestricted conversational understanding. Ambiguous entities and long histories remain limitations. Short or pronominal questions without usable history prompt clarification. Unsupported topics clear the interface's prior topic context. A new-conversation control gives the user an explicit reset.

    A helpful experience also includes honest uncertainty. The application distinguishes a generated answer, partial support, source excerpts after withholding a draft, and insufficient evidence. It does not display a made-up confidence percentage. Citation and NLI checks are screening signals, not guarantees. A source-only response can be useful, but it is counted as lost generated-answer coverage in evaluation.

    The application uses hypothetical examples, blocks a few obvious identifier patterns and has no automatic persistent chat logging. Those choices are appropriate to this demo but are not comprehensive privacy controls. Transition: we should judge the experience using separate measures of retrieval, response quality and coverage.
""")

deck.new(5, "Evaluation and observed results", "Finding evidence and answering correctly are separate tests.", "30 procedure questions · 4 two-turn conversations · 6 guardrail cases · AI-authored, source-checked labels.")
deck.text(40,185,430,28,"EVIDENCE HIT IN TOP FIVE",12,TEAL,True)
for i,(mode,label) in enumerate([("bm25","Keyword"),("dense","Semantic"),("hybrid","Hybrid + reranker")]):
    y=232+i*62
    deck.text(40,y,175,27,label,14,INK,True)
    deck.rect(215,y+2,190,17,LINE)
    deck.rect(215,y+2,190*R[mode]["hit_at_5"],17,TEAL if mode=="hybrid" else "87ABB4")
    deck.text(418,y-1,70,26,pct(R[mode]["hit_at_5"]),14,NAVY,True)
deck.text(40,424,445,44,f"Hybrid MRR@5: {R['hybrid']['mrr_at_5']:.3f}\nThis measures evidence ranking, not answer accuracy.",13,MUTED)
deck.rect(515,185,405,278,WHITE,LINE)
deck.text(533,201,365,28,"GENERATED ANSWER DIAGNOSTICS",12,TEAL,True)
deck.text(533,243,365,42,f"{pct(A['all_required_facts_proxy'])}  all required fact groups",21,NAVY,True)
deck.text(533,290,365,70,f"{A['evidence_only_fallbacks']} withheld drafts / {A['generated_n']} generated evaluations\nGuardrail expected status: {pct(A['guardrail_expected_status_rate'])}\nCPU p50 / p95: {A['p50_seconds']:.1f}s / {A['p95_seconds']:.1f}s",14,INK)
deck.text(533,380,365,64,"Fact matching and NLI can be wrong.\nReview accuracy, relevance, completeness and conciseness independently.",13,MUTED)
deck.notes(f"""
    Timing: 13:00–17:00. Do not describe any automatic proxy as independently established accuracy.

    The included suite has thirty single-turn questions covering all eleven procedures, four two-turn conversations, and six guardrail questions. The labels were AI-authored from the supplied sources and evidence locators were checked against the extracted content. Nineteen questions are development cases and eleven are challenge cases, but after development inspection the challenge split is not a blind external holdout.

    The retrieval comparison uses the same questions and specific relevant passages. Keyword search finds labelled evidence in {pct(R['bm25']['hit_at_5'])} of top-five results, semantic search in {pct(R['dense']['hit_at_5'])}, and hybrid search with reranking in {pct(R['hybrid']['hit_at_5'])}. Reciprocal rank measures how early the first relevant passage appears. These figures do not establish that every applicable exception was retrieved, or that the generated answer is correct.

    For generated responses, {pct(A['all_required_facts_proxy'])} of the thirty ordinary cases contain all required fact groups under the automatic proxy. That proxy can miss a correct paraphrase or pass an incorrect statement containing expected words. Source-only fallbacks count as failures of generated-answer coverage, even if their excerpts contain the answer. Across generated evaluations, {A['evidence_only_fallbacks']} drafts were withheld. Guardrail expected-status agreement was {pct(A['guardrail_expected_status_rate'])}. Local serial CPU response latency was p50 {A['p50_seconds']:.1f} seconds and p95 {A['p95_seconds']:.1f} seconds, excluding initial model loading.

    Early tests showed a notary response with a correct permission decision and an invented general exemption, and a metal-card answer that borrowed instructions from the wrong situation. This demonstrates why citations and word matching are not sufficient. NLI adds a useful screening signal but also rejects valid answers and can miss errors.

    The next evaluation needs independent subject-matter reviewers scoring every material instruction for accuracy, relevance, completeness and conciseness. Critical errors—such as reversed prohibitions or wrong monetary thresholds—must be reported separately from averages. We also need realistic employee tasks, unseen scenarios, calibrated abstention, and latency under concurrency. Transition: these results justify further validation, not an unqualified operational rollout.
""")

deck.new(6, "Decision and path forward", "Validate the workflow before an operational pilot.", "The prototype demonstrates the approach; independent review determines where it is safe and useful.")
deck.card(40,191,280,225,"Working now","Local generative chat\nAll 11 sources indexed\nInspectable citations\nFollow-ups and topic switches\nMeasured retrieval alternatives\nVisible abstention / fallback")
deck.card(340,191,280,225,"Validate next","Independent SME labels\nAccuracy and missing exceptions\nStronger-model comparison\nThreshold calibration\nEmployee task success\nTime-to-guidance baseline")
deck.card(640,191,280,225,"Before a pilot","SSO and source entitlements\nAuthoritative policy versions\nRedacted audit / retention\nLoad tests and monitoring\nEscalation and rollback\nRequired enterprise approvals",accent=GOLD)
deck.text(40,444,880,41,"Recommendation: a scoped, SME-reviewed validation phase with explicit critical-error and coverage gates.",17,NAVY,True)
deck.notes("""
    Timing: 17:00–20:00. End with a practical decision and concrete ownership.

    The working prototype demonstrates end-to-end access to the supplied procedures, actual local generation, inspectable sources and bounded conversational context. It includes reproducible evaluation and recorded failures. It does not establish current policy authority, independent response correctness or enterprise readiness.

    The first next step is a scoped validation effort with procedure owners and operational subject-matter experts. They should independently author and adjudicate scenarios, especially conditional tables, exceptions, eligibility and escalations. Review both generated answers and source-only fallbacks. A system that answers very little can appear safe while failing to help employees, so coverage must remain visible.

    AI engineering should compare stronger approved model options on the same unseen scenarios and measure end-to-end latency and infrastructure cost. Retrieval improvements should focus on conditions, cross-references and exceptions, rather than adding an agent framework without a demonstrated need. Product and branch operations should compare task success and time to correct guidance against current search, with no claimed savings until measured.

    Before any operational pilot, identity and security teams need SSO, document-level authorization before retrieval, session controls and approved data handling. Procedure owners need authoritative effective dates, supersession rules and rollback. Platform teams need concurrency controls, redacted audit logging, retention, monitoring and incident response. The business sponsor and governance owners define the release decision.

    Proposed gates include zero critical unsupported instructions on an independently reviewed release suite, acceptable factual correctness and completeness, explicit refusal/fallback coverage, and an agreed answer-time target. Those are proposals for approval, not achieved enterprise service levels or guarantees of zero future errors.

    Generative AI helped create this solution and also powers the assistant. The candidate must understand and be able to defend the design, its measured evidence and its limits. The presentation materials deliberately exclude source code, as requested. Transition to the fifteen-minute walkthrough: I will now show a factual question, a follow-up, an exception, a topic change, and how the application exposes or withholds evidence-supported answers.
""")

deck.prs.core_properties.title = "Cayman Bank Procedure Assistant"
deck.prs.core_properties.subject = "Six-slide leadership presentation for the supplied simulation exercise"
deck.prs.core_properties.author = "Candidate preparation materials"
deck.prs.core_properties.comments = "AI-assisted prototype; labels and results require independent review. No source code in this deck."
deck.prs.save(OUT / "Cayman_Procedure_Assistant.pptx")
deck.pdf.save(OUT / "Cayman_Procedure_Assistant.pdf", deflate=True)
for i in range(6):
    dest = ROOT / "artifacts/slides"
    dest.mkdir(exist_ok=True)
    deck.pdf[i].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(dest / f"slide_{i+1}.png")
deck.pdf.close()


def markdown_html(markdown: str) -> str:
    """Small report formatter; no fenced source or active content is emitted."""
    lines, output, paragraph, table, list_open = markdown.splitlines(), [], [], [], False
    def inline(s):
        s = escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r"<span>\1</span>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
        return s
    def flush():
        nonlocal paragraph
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph = []
    def flush_table():
        nonlocal table
        if table:
            output.append("<table>")
            for i, row in enumerate(table):
                if re.match(r"^\s*\|?[\s:|\-]+\|?\s*$", row):
                    continue
                cells = row.strip().strip("|").split("|")
                tag = "th" if i == 0 else "td"
                output.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in cells) + "</tr>")
            output.append("</table>")
            table=[]
    in_fence = False
    for line in lines + [""]:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("|"):
            flush()
            table.append(line)
            continue
        flush_table()
        if line.startswith("#"):
            flush()
            if list_open:
                output.append("</ul>"); list_open=False
            level = min(4, len(line) - len(line.lstrip("#")))
            output.append(f"<h{level}>" + inline(line[level:].strip()) + f"</h{level}>")
        elif re.match(r"^(?:- |\d+\. )", line):
            flush()
            if not list_open:
                output.append("<ul>"); list_open=True
            output.append("<li>" + inline(re.sub(r"^(?:- |\d+\. )", "", line)) + "</li>")
        elif not line.strip():
            flush()
            if list_open:
                output.append("</ul>"); list_open=False
        else:
            paragraph.append(line)
    return "<html><body>" + "\n".join(output) + "</body></html>"


def report_pdf(markdown: str, output: Path):
    css = """body {font-family: sans-serif; font-size:10pt; color:#3b3331; line-height:1.35}
    h1{font-size:23pt;color:#3b3331} h2{font-size:15pt;color:#b01c24;margin-top:18pt}
    h3{font-size:12pt;color:#3b3331} p{margin-bottom:8pt} table{border-collapse:collapse;font-size:8.5pt;width:100%;margin:9pt 0}
    th{background:#e8eff4;color:#3b3331}td,th{border:0.4pt solid #ccd8e1;padding:5pt;vertical-align:top}
    li{margin-bottom:5pt} """
    story = fitz.Story(html=markdown_html(markdown), user_css=css)
    writer = fitz.DocumentWriter(str(output))
    media = fitz.paper_rect("a4")
    where = fitz.Rect(40,40,media.width-40,media.height-45)
    more=1
    while more:
        device=writer.begin_page(media)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()
    del writer
    doc=fitz.open(output)
    for i,page in enumerate(doc):
        page.insert_text((40,media.height-22), f"Cayman Procedure Assistant | Exercise prototype | {i+1}/{len(doc)}", fontsize=8, color=rgb(MUTED))
    doc.save(str(output)+".tmp", deflate=True)
    doc.close()
    Path(str(output)+".tmp").replace(output)


# Detailed, candidate-facing overview: engineering evidence and limitations.
inventory = "\n".join(f"| {d['doc_id']} | {d['title'].split(' - PR')[0]} | {d['words']:,} | {d['chunks']} | {d['published'].replace('Published ','')} |" for d in CORPUS["documents"])
failed = [r["id"] for r in ANSWERS if r.get("all_required_facts_proxy") is False]
ordinary = [r for r in ANSWERS if r["id"] in {c["id"] for c in json.loads((ROOT/'evaluation/cases.json').read_text())["cases"]}]
status_counts = {status: sum(r['result']['status']==status for r in ordinary) for status in sorted({r['result']['status'] for r in ordinary})}
follow = ", ".join(k + ": " + ("pass" if v else "miss") for k,v in A["followup_fact_passes"].items())
overview = f"""# Detailed solution overview

The complete assignment PDF was reviewed and an end-to-end, locally runnable generative chat solution was built over all eleven supplied procedures. The deliverables include six editable PowerPoint slides with speaker notes, a matching PDF, a timed demonstration guide, measured evaluation, raw evidence traces and a source-free presentation archive. This is a tested exercise prototype, not a bank-approved operational deployment.

## What was built and why

The system helps employees ask a procedure question, inspect the supporting passages and refine the situation conversationally. Retrieval-augmented generation was chosen to keep the evidence explicit and replaceable. Fine-tuning would not itself provide reliable citations or source version control. A local model removes the API-key dependency and makes the demonstration reproducible on this computer.

The final generator is {A['model']}. The Qwen3 model uses four-bit GGUF inference through llama.cpp on CPU. An earlier Qwen2.5 1.5B float32 baseline produced too many distracting details and withheld drafts; its complete results are retained separately. Model choice was evaluated empirically rather than inferred from published benchmarks.

The solution uses structure-aware HTML parsing, a JSONL passage store, BM25 lexical search, 384-dimensional MiniLM embeddings, reciprocal rank fusion, MiniLM cross-encoder reranking, bounded evidence, actual local generation, citation-local numeric checks and a DeBERTa NLI screening signal. The Wells Fargo–inspired version 2 workspace exposes a searchable procedure library and an Evidence desk with Evidence, Checks and Activity views. The brand asset is the unmodified official website wordmark, and the interface is explicitly labelled as an interview prototype using the supplied Cayman Bank documents.

Version 2 checks original sources and cached-index fingerprints on every supported request. It binds explicit citations to individual claims and records the source passage and evidence window behind each support check. A failed draft may receive one correction using the same evidence; the revised draft must pass the same checks or be withheld. Actual stage events and deterministic decision criteria are visible; the interface does not fabricate private model reasoning or a confidence percentage. Details are in [the version 2 design](docs/EXPERIENCE_V2.md).

## Assignment alignment

The PDF asks for a functional generative conversational solution grounded in eleven documents, approximately five to six PPT slides, methodology and architecture, technology and design decisions, document processing/chunking/retrieval, quality measurement, follow-ups and a demonstration. It allows generative AI, requires explanation of its use and validation, and excludes source code from the presentation and demonstration. Each expectation is mapped in [the assignment review](docs/ASSIGNMENT_REVIEW.md).

The deck has exactly six slides. Presenter notes support a 20-minute delivery; the runbook allocates the separate 15-minute walkthrough. Presentation files are isolated from implementation source. The recruiter-specific deadline, recipient and meeting details were not supplied and are not inferred from the PDF date. No materials have been sent externally.

## Input review and content preservation

The supplied corpus contains {sum(d['words'] for d in CORPUS['documents']):,} extracted words and 139 HTML tables including nested tables. It is indexed into {CORPUS['chunk_count']:,} passages. PR1779 is much larger than the other procedures and contains several account-type workflows.

| Procedure | Subject | Extracted words | Passages | Publication in supplied source |
|---|---|---:|---:|---|
{inventory}

The original files were preserved. Each passage records its procedure ID, title, publication text, source filename, source SHA256, section hierarchy, anchor, ordinal, text, content type and table/row metadata when applicable. A source revision changes passage identity and requires rebuilding the index.

The parser recognizes the HTML export's policy classes and handles UTF-8 explicitly. It excludes scripts and display-only styling, does not follow links, and retains table column labels, row conditions, rowspans and colspans. Nested table text is included once. Long table rows repeat their leftmost condition in continuation passages.

Narrative grouping targets roughly 110 words within sections, with 20-word overlap when splitting long content. Unsplit table rows can reach 130 words; continuation condition prefixes can make them longer. These are word targets, not exact token counts. All checked source paragraph five-word sequences were found by the extraction audit across the eleven documents; that establishes a limited text-preservation diagnostic, not semantic validation of the table parser.

## How a question is answered

1. Bound and check the question. Recognize an explicit procedure, a named topic or a contextual follow-up.
2. Search BM25 and normalized dense vectors. Combine the rankings with RRF and rerank the candidates jointly with the question.
3. Abstain if evidence signals are weak. Otherwise construct a pack of up to three nonduplicate passages, targeting at most 520 words.
4. Give the selected evidence and resolved question to the local generative model. The prompt requires a direct, concise answer with conditions, exceptions and source labels.
5. Check citation labels, claim-local attribution, numeric values and recognized boundaries against the cited passages; screen claim support with verbatim matching or NLI.
6. If a draft fails, allow one bounded correction with the same evidence and deterministic feedback, then apply the same checks. Display a passing answer with evidence; otherwise withhold it and show sources. Unsupported questions receive abstention or clarification. Record the actual stages and decision for inspection.

Source hashes detect changed originals; the embedding manifest binds vectors to the passage-file hash. Plain JSON and NumPy files avoid loading pickled index objects. Runtime model loading uses local files; external linked documents are not retrieved. Some supplied links are placeholders and are not treated as evidence.

## Follow-ups and user experience

Browser sessions own their question history; cached models/indexes do not own user conversation memory. Prior user questions can resolve an elliptical follow-up. A follow-up naming a new task in the same procedure retains scope without repeating unrelated prior-task keywords. Named topic changes replace previous scope. Every follow-up performs fresh retrieval; previous generated claims are never authoritative evidence.

The interface provides starter scenarios, a searchable procedure library, optional document-scoped retrieval, citation selection, original-procedure downloads, publication information, reset, opt-in investigation export and feedback. The Evidence desk separates exact passages, claim-support checks and observed activity. Conflicting document scope prompts clarification, and a new unsupported response does not silently show an earlier response's sources. The resolver remains bounded and can misinterpret ambiguous or long conversations.

## Measured results

The suite includes 30 ordinary procedure questions, four two-turn conversations and six guardrail questions. Labels are AI-authored and source-checked. The 19/11 development/challenge split is not an independent blind holdout after development inspection.

| Retrieval method | Evidence hit@5 | MRR@5 | Local median retrieval seconds |
|---|---:|---:|---:|
| BM25 | {pct(R['bm25']['hit_at_5'])} | {R['bm25']['mrr_at_5']:.3f} | {R['bm25']['p50_seconds']:.3f} |
| Dense | {pct(R['dense']['hit_at_5'])} | {R['dense']['mrr_at_5']:.3f} | {R['dense']['p50_seconds']:.3f} |
| Hybrid + reranker | {pct(R['hybrid']['hit_at_5'])} | {R['hybrid']['mrr_at_5']:.3f} | {R['hybrid']['p50_seconds']:.3f} |

Retrieval hit@5 measures whether at least one labelled relevant passage was in the first five, not whether all applicable evidence was retrieved or an answer was correct. Repeated equivalent passages are allowed by the label locators.

| Answer diagnostic | Observed result |
|---|---|
| Ordinary questions with all required fact groups, automatic proxy | {pct(A['all_required_facts_proxy'])} of {A['ordinary_n']} |
| Mean required-fact group coverage, automatic proxy | {pct(A['fact_coverage_proxy'])} |
| Withheld drafts shown as source excerpts | {A['evidence_only_fallbacks']} of {A['generated_n']} generated evaluations |
| Expected guardrail response status | {pct(A['guardrail_expected_status_rate'])} of {A['guardrails_n']} |
| Serial local end-to-end p50 / p95, generated evaluations | {A['p50_seconds']:.2f}s / {A['p95_seconds']:.2f}s |
| Mean generated-draft word count | {A['mean_word_count']:.1f} |
| Bounded correction attempts / revised answers released | {A.get('repair_attempts',0)} / {A.get('repairs_released',0)} |
| Ordinary-question response outcome counts | {status_counts} |
| Follow-up final-turn fact proxies | {follow} |

The latency measurements exclude initial model loading and are from serial requests on the local CPU; they are not a throughput benchmark. Word count is a conciseness diagnostic, not proof of sufficient context. Term matching can pass wrong statements or miss correct paraphrases. NLI is fallible. These results must not be described as independently established accuracy.

Version 2 permits one correction after a failed draft, using the same evidence and check feedback. This increases the worst-case generation work. {A.get('repairs_released',0)} of {A.get('repair_attempts',0)} revised evaluated drafts passed release checks in this run. This is a screened-release count, not independent confirmation of the revisions' correctness.

Regression cases missing at least one required fact group, including source-only outcomes: {', '.join(failed) or 'none'}. Review their raw responses and evidence in `artifacts/evaluation/answer_details.json`. The report does not hide fallback as generated-answer success.

## Testing and observed engineering lessons

Focused automated tests cover table row/column condition preservation, nested table duplication, UTF-8, stable IDs, source revisions, real-corpus facts, follow-up scope, topic changes, session isolation, invalid citations, invented amounts, equivalent currency formatting, missing paragraph citations, stale sources, direct instruction attacks and obvious identifiers. Separate browser checks exercise the actual local app and save screenshots.

{test_summary} {browser_summary}

Initial failures combined rules from different situations and invented an exception rationale despite valid citations. Shorter passages, stronger reranking and a larger quantized generator reduced some weaknesses. Claim screening adds a conservative boundary but can withhold valid answers. A narrow evidence pack also trades lower distraction against missing exceptions elsewhere. These are documented tradeoffs, not solved problems.

## What a production version still needs

Independent SME-authored and adjudicated cases are the first priority. Evaluate accuracy, relevance, completeness and conciseness separately, and treat critical errors independently of averages. Include unseen scenarios, long conversations, cross-references, conditional tables, outdated/conflicting sources, malicious retrieved content and realistic employee tasks.

Production also needs authoritative effective policy versions, approved ingestion and rollback, employee SSO, document-level entitlements, approved model selection, redacted audit/retention, monitoring, rate limits, concurrency, timeouts, escalation and required enterprise review. The prototype's local processing and simple identifier patterns do not replace these controls.

The recommended next step is a scoped validation phase with procedure owners and model/platform teams. A pilot should depend on agreed critical-error, coverage, correctness, completeness and latency gates and measured employee benefit over existing search. No productivity, cost saving or enterprise-compliance achievement is claimed here.

## Where to find the deliverables

- `submission/Cayman_Procedure_Assistant.pptx`: six editable slides and presenter notes.
- `submission/Cayman_Procedure_Assistant.pdf`: matching slide PDF.
- `submission/Demo_Runbook.pdf`: timed presentation and demonstration guide.
- `submission/Recorded_Demo.pdf`: clearly labelled saved responses for rehearsal and backup.
- `submission/Presentation_Materials.zip`: allowlisted source-free presentation package.
- `docs/ARCHITECTURE.md`: component design, decisions, parameters and production path.
- `docs/ASSIGNMENT_REVIEW.md`: every requirement, acceptance evidence and three-day plan.
- `docs/AI_USE_AND_VALIDATION.md`: development/runtime AI use and validation boundaries.
- `docs/TECHNICAL_WALKTHROUGH.md`: design defense and interview questions.
- `evaluation/REVIEW_RUBRIC.md`: independent-review scoring and proposed release gates.
- `artifacts/index/`, `artifacts/evaluation/` and `artifacts/runtime_manifest.json`: reproducible source, measurement and model provenance.

Run the application with the instructions in `README.md`. Review the source traces and personalize the narrative before presenting. The candidate must verify deadline/submission logistics and be able to explain and defend the work personally.
"""
(ROOT / "SOLUTION_OVERVIEW.md").write_text(overview, encoding="utf-8")
report_pdf(overview, ROOT / "SOLUTION_OVERVIEW.pdf")

suite = json.loads((ROOT / "evaluation/cases.json").read_text())
case_map = {c["id"]: c for c in suite["cases"]}
case_table = []
for row in ordinary:
    result=row["result"]
    reason=("model abstention" if result["status"]=="unsupported" else
            "numeric/comparator check" if result["checks"].get("novel_numbers") or result["checks"].get("comparison_conflicts") else
            "claim support screen" if not result["checks"].get("claim_support",{}).get("passed",True) else
            "missing fact group" if not row.get("all_required_facts_proxy") else "fact proxy passed")
    case_table.append(f"| {row['id']} | {case_map[row['id']]['doc_id']} | {result['status']} | {'pass' if row.get('all_required_facts_proxy') else 'miss'} | {reason} |")
per_doc=[]
for doc in CORPUS["documents"]:
    relevant=[row for row in ordinary if case_map[row['id']]['doc_id']==doc['doc_id']]
    per_doc.append(f"| {doc['doc_id']} | {len(relevant)} | {sum(bool(row.get('all_required_facts_proxy')) for row in relevant)} | {sum(row['result']['status']=='evidence_only' for row in relevant)} |")
baseline_path=ROOT / "artifacts/experiments/qwen2_5_complete/metrics.json"
baseline=json.loads(baseline_path.read_text())["answers"] if baseline_path.exists() else None
comparison=(f"The retained initial 1.5B pipeline had {pct(baseline['all_required_facts_proxy'])} all-fact proxy coverage and p50 {baseline['p50_seconds']:.2f}s; the final pipeline has {pct(A['all_required_facts_proxy'])} and p50 {A['p50_seconds']:.2f}s. Model, prompts, evidence packing and screening changed between these runs, so this is an end-to-end iteration comparison, not an isolated causal model ablation." if baseline else "No initial comparison artifact is present.")
v1_path=ROOT / "artifacts/experiments/v1_complete_before_workspace_v2/metrics.json"
v1=json.loads(v1_path.read_text())["answers"] if v1_path.exists() else None
v2_comparison=(f"On the same 30-question regression set, the previous version had {pct(v1['all_required_facts_proxy'])} all-fact proxy coverage and {v1['evidence_only_fallbacks']} source-only outcomes; the current version has {pct(A['all_required_facts_proxy'])} and {A['evidence_only_fallbacks']}. The strict sales-boundary and savings-bond exception cases were recovered through bounded correction, while some other cases remain withheld or unnecessarily refused. Local timing and pipeline changes prevent treating this as an isolated model-performance experiment." if v1 else "")
evaluation_report=f"""# Evaluation report

Final model: {A['model']}. All figures below are calculated from the saved final local run. The test suite uses AI-authored, source-checked labels and is not an independently adjudicated benchmark. Review the original sources and [the scoring rubric](../evaluation/REVIEW_RUBRIC.md) before interpreting these figures.

## Retrieval versus response quality

BM25 evidence hit@5: {pct(R['bm25']['hit_at_5'])}; dense: {pct(R['dense']['hit_at_5'])}; hybrid plus reranking: {pct(R['hybrid']['hit_at_5'])}. Hybrid MRR@5 is {R['hybrid']['mrr_at_5']:.3f}. These use specific evidence locators and allow repeated equivalent relevant passages. They do not establish complete evidence retrieval or correct responses.

All required fact groups occur in {pct(A['all_required_facts_proxy'])} of the 30 ordinary generated-answer evaluations. Mean fact-group coverage is {pct(A['fact_coverage_proxy'])}. A source-only fallback fails the generated-answer proxy even when its excerpts contain the answer. Keyword proxies can miss valid paraphrases and pass incorrect statements containing expected words.

The output-screen pass rate is {pct(A.get('output_screen_pass_rate',A['mechanical_validation_pass_rate']))}. This is a combination of mechanical and support screening, not a correctness estimate. There are {A['evidence_only_fallbacks']} source-only outcomes among {A['generated_n']} evaluated generated calls. Guardrail expected-status agreement is {pct(A['guardrail_expected_status_rate'])} on six deliberately selected cases; six cases do not establish general security effectiveness.

The version 2 engine attempted {A.get('repair_attempts',0)} bounded corrections and released {A.get('repairs_released',0)} revised answers after the same checks. Each correction keeps the same evidence pack. The record retains rejected draft details, and the activity view reports a correction only when it occurred. Additional attempts can increase CPU response time; safety and coverage must be assessed together with that latency cost.

Serial local generated-call latency is p50 {A['p50_seconds']:.2f}s and p95 {A['p95_seconds']:.2f}s. First model load is excluded. Mean draft length is {A['mean_word_count']:.1f} words. Neither length nor speed establishes usefulness or completeness. Concurrent users, network deployments and cold starts were not benchmarked.

## Every ordinary case

| Case | Procedure | Response outcome | All-fact proxy | Diagnostic |
|---|---|---|---|---|
{chr(10).join(case_table)}

## Per-procedure view

| Procedure | Questions | All-fact proxy passes | Source-only fallbacks |
|---|---:|---:|---:|
{chr(10).join(per_doc)}

These small per-procedure counts are useful for finding weak areas, not statistical estimates of production accuracy. The corpus's largest document does not dominate the question count.

## Follow-ups and unsupported questions

Final-turn fact checks: {follow}. Inspect the full resolved query, selected evidence and status in the raw details file. The coin-machine follow-up asking simply for a “control” can produce the task name while omitting the control level. The live runbook uses the clearer single-versus-dual-control question, while the original ambiguous regression question remains in the suite and its miss remains visible.

Guardrail cases cover unrelated content, a direct instruction attack, an unknown procedure, missing context, an obvious customer identifier, and unavailable current interest rates. Pattern checks are narrow. The suite does not establish defenses against indirect prompt injection, comprehensive privacy protection, source poisoning or enterprise authorization failures.

## Observed failure patterns and corrective choices

- A notary draft in an early run invented an exemption from other rules despite a correct main permission decision. Citation/term checks alone did not catch it. This motivated claim screening and explicit condition preservation.
- A metal-card draft borrowed instructions from a found-card scenario. Shorter passages and narrower evidence reduced distraction, but situation applicability still needs human review.
- Some correct paraphrases are withheld by the NLI screen. Literal substantive source matches use a direct support check; NLI is used for paraphrases. Neither proves applicability to the user's situation.
- A model changed “less than $2 million” into an inclusive threshold. A comparator guard and regression test now withhold such a draft. The number comparison check covers recognizable patterns, not general mathematical reasoning.
- An evidence pack can miss an exception even when top-five retrieval contains the general rule. Leading hits now recover the next same-section qualification or table-row continuation. Remote cross-references remain outside scope.
- Fact completeness and relevance remain imperfect. The application may omit a requested condition, refuse a valid question or add related but unnecessary detail. These are exposed in raw traces and the table above.

{comparison}

{v2_comparison}

## Interpretation and next validation

Do not report these proxies as independently established accuracy. Have two operational SMEs independently score accuracy, relevance, completeness and conciseness, adjudicate disagreements, and mark critical errors separately. Use unseen scenarios, realistic branch tasks, source-version conflicts and long conversations. Measure answer coverage, correct abstention, unnecessary refusal, employee task success and time to correct guidance against existing search.

Proposed pilot gates are in the rubric and are not achieved enterprise service levels. This exercise demonstrates a measurable prototype with explicit limits; it does not justify unsupervised operational deployment.

Raw metrics: `artifacts/evaluation/metrics.json`. Retrieval rankings: `artifacts/evaluation/retrieval_details.json`. Answers, withheld drafts, sources, checks and timings: `artifacts/evaluation/answer_details.json`. Earlier experiments are retained separately under `artifacts/experiments/`.
"""
(ROOT / "docs/EVALUATION_REPORT.md").write_text(evaluation_report,encoding="utf-8")
report_pdf(evaluation_report,ROOT / "docs/EVALUATION_REPORT.pdf")
report_pdf((ROOT / "docs/DEMO_RUNBOOK.md").read_text(encoding="utf-8"), OUT / "Demo_Runbook.pdf")

transcript = ["# Recorded demonstration responses", "These are saved outputs from the final local evaluation, not a live session. Sources, status and elapsed time are preserved. Automatic screening does not guarantee correctness; inspect the applicable procedure."]
for case_id in ["M01", "F01.2", "N01", "F02.2", "S01", "F03.2", "F04.2", "N03", "G01", "G04", "G06"]:
    row=BY_ID[case_id]; result=row["result"]
    transcript += [f"## {case_id}: {result['question']}", f"Status: {result['status']} | Model: {result.get('model') or 'generation not used'} | Elapsed: {result['metrics'].get('total_seconds','not applicable')} seconds", result["answer"]]
    for source in result["sources"]:
        transcript += [f"### [{source['label']}] {source['doc_id']} — {source['section']}", source["published"], source["text"]]
transcript_text="\n\n".join(transcript)
(ROOT / "artifacts/recorded_demo.md").write_text(transcript_text, encoding="utf-8")
report_pdf(transcript_text, OUT / "Recorded_Demo.pdf")
notes="\n\n".join(f"## Slide {i+1}\n\n{s.notes_slide.notes_text_frame.text}" for i,s in enumerate(deck.prs.slides))
report_pdf("# Presenter notes\n\n"+notes, OUT / "Presenter_Notes.pdf")

(OUT / "README.txt").write_text(
    "CAYMAN PROCEDURE ASSISTANT — PRESENTATION MATERIALS\n\n"
    "Six-slide deck with speaker notes; matching PDF; timed runbook; recorded demonstration backup.\n"
    "No implementation source or model files are included.\n"
    "Recorded responses are saved outputs, not a live demonstration.\n"
    "AI assisted development and runtime answering. Regression labels are AI-authored/source-checked, not independently adjudicated.\n"
    "Check the recruiter email for the exact deadline, recipient and meeting instructions.\n"
    "Nothing has been submitted externally.\n", encoding="utf-8")
allowlist=["Cayman_Procedure_Assistant.pptx","Cayman_Procedure_Assistant.pdf","Demo_Runbook.pdf","Recorded_Demo.pdf","Presenter_Notes.pdf","README.txt"]
with zipfile.ZipFile(OUT / "Presentation_Materials.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in allowlist:
        archive.write(OUT / name, name)
with zipfile.ZipFile(OUT / "Presentation_Materials.zip") as archive:
    if sorted(archive.namelist()) != sorted(allowlist):
        raise ValueError("Unexpected submission archive contents")
print(json.dumps({"slides":len(deck.prs.slides),"files":[str(OUT/name) for name in allowlist],
                  "overview":str(ROOT / "SOLUTION_OVERVIEW.md"),"archive":"Presentation_Materials.zip"},indent=2))
