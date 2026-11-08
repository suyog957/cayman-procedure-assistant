"""Six-slide leadership narrative, built as editable native PowerPoint objects.

PowerPoint or local LibreOffice Impress exports the PDF and slide previews.
No generated slide image replaces editable text, diagrams or charts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import textwrap
import os
import shutil
import uuid
import re
import unicodedata

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Pt
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn

BG='FBFAF7'; WHITE='FFFFFF'; INK='302B28'; MUTED='665F59'
RED='C51E2A'; GOLD='E8B532'; LINE='E4DED7'; PALE='F2EEE7'
TEAL='24655F'; GREEN_PALE='EAF2EE'; AMBER_PALE='FCF3DF'
DECK_BASENAME='Branch_Assist_Solution_Presentation_Final'
STAGES=['Solution','Data','Architecture','Experience','Evaluation','Demo']


@dataclass
class LeadershipDeck:
    root: Path

    def __post_init__(self):
        self.prs=Presentation()
        self.prs.slide_width=Pt(960);self.prs.slide_height=Pt(540)
        self.slide=None;self.number=0;self.records=[]

    def rect(self,x,y,w,h,fill=WHITE,border=None,radius=False):
        shape=self.slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                                         Pt(x),Pt(y),Pt(w),Pt(h))
        if radius:shape.adjustments[0]=.08
        style=shape._element.find(qn('p:style'))
        if style is not None:
            effect=style.find(qn('a:effectRef'))
            if effect is not None:effect.set('idx','0')
        shape._element.spPr.append(OxmlElement('a:effectLst'))
        shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(fill)
        if border:shape.line.color.rgb=RGBColor.from_string(border);shape.line.width=Pt(.7)
        else:shape.line.fill.background()
        return shape

    def text(self,x,y,w,h,text,size=15,color=INK,bold=False,font='Segoe UI',align=None,role='body'):
        shape=self.slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(h))
        shape.name=f'text_{self.number}_{len(self.records):03d}'
        frame=shape.text_frame;frame.clear();frame.word_wrap=True;frame.auto_size=MSO_AUTO_SIZE.NONE
        frame.margin_left=frame.margin_right=frame.margin_top=frame.margin_bottom=0
        frame.vertical_anchor=MSO_ANCHOR.TOP
        for i,line in enumerate(text.split('\n')):
            paragraph=frame.paragraphs[0] if i==0 else frame.add_paragraph()
            paragraph.text=line;paragraph.font.name=font;paragraph.font.size=Pt(size)
            paragraph.font.bold=bold;paragraph.font.color.rgb=RGBColor.from_string(color)
            paragraph.line_spacing=1.08;paragraph.space_before=paragraph.space_after=Pt(0)
            if align is not None:paragraph.alignment=align
        self.records.append({'slide':self.number,'shape':shape.name,'text':text,'size':size,'role':role,
                             'box':[x,y,w,h]})
        return shape

    def line(self,x,y,w,color=LINE,height=.8):self.rect(x,y,w,height,color)

    def arrow(self,x,y,w=12,h=13):
        shape=self.slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.CHEVRON,Pt(x),Pt(y),Pt(w),Pt(h))
        shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(GOLD);shape.line.fill.background()

    def pill(self,x,y,w,label,fill=GREEN_PALE,color=TEAL,size=11.5):
        self.rect(x,y,w,25,fill,radius=True)
        self.text(x+9,y+4,w-18,18,label,size,color,True,role='label')

    def new(self,number,section,title=None,subtitle=None):
        self.number=number;self.slide=self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.rect(0,0,960,540,BG)
        self.text(44,23,690,19,'BRANCH ASSIST  /  LEADERSHIP BRIEF  /  '+section.upper(),10,RED,True,role='label')
        self.rect(766,20,150,28,RED)
        self.slide.shapes.add_picture(str(self.root/'assets/brand/wells-fargo-wordmark.png'),Pt(777),Pt(27),width=Pt(128))
        if title:self.text(44,65,872,72,title,29,INK,True,font='Georgia',role='headline')
        if subtitle:self.text(44,145,872,34,subtitle,14,MUTED)
        self.line(44,503,872)
        for i,label in enumerate(STAGES):
            x=44+i*137
            if i==number-1:
                self.rect(x,502,112,2,RED)
            self.text(x,514,123,16,f'{i+1:02d}  {label}',8.8,RED if i==number-1 else MUTED,i==number-1,role='navigation')
        self.text(886,514,30,16,f'{number}/6',9,MUTED,align=PP_ALIGN.RIGHT,role='navigation')

    def source(self,value):self.text(44,486,872,13,value,8.5,MUTED,role='source')

    def notes(self,value):self.slide.notes_slide.notes_text_frame.text=textwrap.dedent(value).strip()

    def image_crop(self,path,x,y,w,h,roi):
        from PIL import Image
        with Image.open(path) as image:iw,ih=image.size
        rx,ry,rw,rh=roi
        assert abs((rw/rh)/(w/h)-1)<.02,'Picture crop would distort the UI.'
        shape=self.slide.shapes.add_picture(str(path),Pt(x),Pt(y),width=Pt(w),height=Pt(h))
        shape.crop_left=rx/iw;shape.crop_top=ry/ih
        shape.crop_right=1-(rx+rw)/iw;shape.crop_bottom=1-(ry+rh)/ih


def render_in_powerpoint(deck,output):
    """Open only our deck without a window; leave other presentations alone."""
    import pythoncom
    import win32com.client
    import pymupdf
    already_running='POWERPNT.EXE' in subprocess.check_output(
        ['tasklist','/FI','IMAGENAME eq POWERPNT.EXE','/FO','CSV','/NH'],text=True).upper()
    pythoncom.CoInitialize();app=None;presentation=None
    bounds=[];issues=[]
    try:
        app=win32com.client.DispatchEx('PowerPoint.Application')
        presentation=app.Presentations.Open(str(output.resolve()),ReadOnly=True,Untitled=False,WithWindow=False)
        for slide in presentation.Slides:
            for shape in slide.Shapes:
                if not shape.HasTextFrame or not shape.TextFrame.HasText:continue
                text=shape.TextFrame2.TextRange
                row={'slide':slide.SlideIndex,'shape':shape.Name,'width':float(shape.Width),
                     'height':float(shape.Height),'text_width':float(text.BoundWidth),
                     'text_height':float(text.BoundHeight)}
                bounds.append(row)
                if row['text_height']>row['height']+1.8 or row['text_width']>row['width']+1.8:issues.append(row)
        folder=deck.root/'artifacts/slides';folder.mkdir(exist_ok=True)
        presentation.SaveAs(str(output.with_suffix('.pdf').resolve()),32)
        for slide in presentation.Slides:
            slide.Export(str((folder/f'slide_{slide.SlideIndex}.png').resolve()),'PNG',1920,1080)
    finally:
        if presentation is not None:presentation.Close()
        if app is not None and not already_running and app.Presentations.Count==0:app.Quit()
        pythoncom.CoUninitialize()
    qa=deck.root/'artifacts/presentation';qa.mkdir(exist_ok=True)
    with pymupdf.open(output.with_suffix('.pdf')) as pdf:
        assert len(pdf)==6 and all(abs(p.rect.width/p.rect.height-16/9)<.001 for p in pdf)
    report={'status':'passed' if not issues else 'needs_layout_fix','render_engine':'Microsoft PowerPoint',
            'slide_count':6,'native_editable_text_boxes':len(bounds),'text_bound_overflows':issues,
            'bounds':bounds,'layout':deck.records}
    (qa/'layout_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if issues:raise ValueError('PowerPoint text overflow: '+str(issues))


def render_in_libreoffice(deck,output,office_error):
    """Render locally in an independent engine when Office rejects new opens."""
    import pymupdf
    cache=deck.root/'artifacts/video_build/render_tools'
    configured=os.environ.get('BRANCH_ASSIST_SOFFICE') or shutil.which('soffice')
    candidates=[Path(configured)] if configured else []
    candidates += list((cache/'libreoffice').rglob('soffice.exe'))
    if not candidates:raise RuntimeError('No independent local renderer available.') from office_error
    profile=cache/('profile_'+uuid.uuid4().hex[:8])
    result=subprocess.run([str(candidates[0]),'-env:UserInstallation='+profile.resolve().as_uri(),
                           '--headless','--convert-to','pdf:impress_pdf_Export','--outdir',str(output.parent.resolve()),str(output.resolve())],
                          capture_output=True,text=True,timeout=120,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not output.with_suffix('.pdf').exists():
        raise RuntimeError('Independent presentation render failed: '+result.stderr)
    def compact(value):return ''.join(re.findall(r'\w+',unicodedata.normalize('NFKC',value).casefold()))
    issues=[];bounds=[];folder=deck.root/'artifacts/slides';folder.mkdir(exist_ok=True)
    with pymupdf.open(output.with_suffix('.pdf')) as pdf:
        assert len(pdf)==6
        for record in deck.records:
            x,y,w,h=record['box'];page=pdf[record['slide']-1]
            clipped=compact(page.get_text(clip=pymupdf.Rect(x-2.5,y-2.5,x+w+2.5,y+h+2.5)))
            fits=compact(record['text']) in clipped
            bounds.append({'slide':record['slide'],'shape':record['shape'],'fits_exported_box':fits})
            if not fits:issues.append(record)
        for i,page in enumerate(pdf):
            assert abs(page.rect.width/page.rect.height-16/9)<.001
            page.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(folder/f'slide_{i+1}.png')
    qa=deck.root/'artifacts/presentation';qa.mkdir(exist_ok=True)
    report={'status':'passed' if not issues else 'needs_layout_fix','render_engine':'LibreOffice Impress',
            'bounds_method':'Exported PDF text within intended native text-box rectangles',
            'powerpoint_background_open_unavailable':True,'slide_count':6,'native_editable_text_boxes':len(bounds),
            'text_bound_overflows':issues,'bounds':bounds,'layout':deck.records}
    (qa/'layout_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if issues:raise ValueError('Rendered text exceeds its intended box: '+str(issues))


def build_leadership_deck(root,corpus,metrics):
    deck=LeadershipDeck(root)
    answer=metrics['answers'];retrieval={r['mode']:r for r in metrics['retrieval'] if r['split']=='all'}
    count=answer['ordinary_n'];fact_pass=round(answer['all_required_facts_proxy']*count)

    # 1. Establish the objective, implemented scope and solution methodology.
    deck.new(1,'Solution overview','Generative AI for grounded\nprocedure guidance.',
             'Conversational access to eleven operational procedures, with traceable answers and contextual follow-ups.')
    deck.text(44,194,402,19,'BUSINESS OBJECTIVE',10.5,RED,True,role='label')
    deck.text(44,222,402,68,'Help branch employees find and verify applicable guidance across long, conditional procedures.',17)
    deck.text(44,305,402,19,'SOLUTION METHODOLOGY',10.5,RED,True,role='label')
    deck.text(44,333,420,71,'Retrieve supporting passages, generate a concise answer, then check each claim against its cited source.',16,MUTED)
    deck.rect(494,193,422,225,WHITE,LINE,radius=True)
    deck.text(511,207,389,19,'IMPLEMENTED CAPABILITIES',10.2,RED,True,role='label')
    for x,y,title,body in [
        (511,241,'Generative chat','Answers from procedure evidence with source citations.'),
        (716,241,'Follow-up handling','Retain the situation and retrieve fresh evidence.'),
        (511,330,'Evidence workspace','Original text, answer checks and execution activity.'),
        (716,330,'Quality evaluation','Retrieval comparisons and response-quality diagnostics.')]:
        deck.text(x,y,184,25,title,14.6,INK,True)
        deck.text(x,y+31,184,55,body,13.2,MUTED)
    deck.line(44,429,872)
    for x,value,label in [(44,'11','source procedures'),(341,'139','HTML tables'),(638,f"{corpus['chunk_count']:,}",'indexed passages')]:
        deck.text(x,436,95,34,value,24,INK,True)
        deck.text(x+100,445,175,22,label,12.7,MUTED)
    deck.text(44,472,872,21,'Value to measure: accurate, relevant, complete and concise guidance with less search effort.',13.2,TEAL,True)
    deck.source('Implementation scope: provided Cayman Bank procedures · local model inference · source citations and reviewable check records')
    deck.notes('''
        Timing: 0:00 to 2:30. Establish the business objective, implemented solution and methodology before moving into the technical design.

        Branch employees need efficient access to information in operational procedures. The information task includes finding the applicable requirement, understanding its conditions and exceptions, and verifying that the answer is supported by the source. The business objective is to reduce search effort while retaining the detail needed for a correct decision. Productivity improvement is an outcome to measure, not a saving already established by this work.

        Branch Assist is a working generative conversational solution over the eleven provided Cayman Bank procedures. The collection contains 139 HTML tables and is organized into 1,388 traceable passages. Questions execute an actual local language model. The interface supports generated answers, contextual follow-ups, procedure selection, citations, source inspection, feedback and conversation export.

        The methodology is retrieval-augmented generation. The system first finds relevant procedure evidence, then asks a model to synthesize a concise answer from that evidence. It checks source references, numeric values, recognizable thresholds and claim support before releasing a draft. The source text and check record remain available to the employee. If support is insufficient, the system asks for context or withholds the draft and exposes the original passages.

        Four design principles define the solution. Keep each requirement attached to its conditions during document preparation. Retrieve evidence for the current question instead of using a previous generated answer as proof. Make the evidence and response decision inspectable. Evaluate retrieval and response quality separately, including the coverage lost when answers are withheld.

        The knowledge boundary is the eleven provided files; external linked procedures and live policy updates are not ingested. The system answers information questions and does not execute bank transactions. The local runtime was selected to work on the available CPU without an API key; its latency and model limitations are measured explicitly.

        Success must be judged across accuracy, relevance, completeness and conciseness. Those dimensions drive the evaluation approach later in the presentation. The implemented controls and recorded diagnostics support review; they do not replace independent assessment of substantive instructions.

        Transition: the first engineering step is turning the original documents into structured, traceable evidence that retrieval can use.
    ''')

    # 2. Explain the complete document-engineering method without a domain example.
    deck.new(2,'Document engineering','From original documents\nto structured, searchable evidence.',
             'Preserve content, conditions and source identity throughout ingestion, chunking and indexing.')
    total_words=sum(d['words'] for d in corpus['documents'])
    columns=[
        ('01 / PROFILE','Inventory\nand profile',f"11 HTML files; {total_words:,}\nextracted words; 139 tables.\nCapture titles, IDs and\npublication details."),
        ('02 / EXTRACT','Parse\nstructure','UTF-8 headings, lists and\ntable rows. Preserve column\nlabels, row conditions and\nnested content.'),
        ('03 / ORGANIZE','Chunk\nwith context','~110 narrative words;\n20-word overlap. Repeat\ntable conditions on\ncontinuation passages.'),
        ('04 / INDEX','Index\nand trace',f"{corpus['chunk_count']:,} passages; BM25 +\n384D dense vectors. Record\nsource, section and\noriginal-file hash.")]
    for i,(label,title,body) in enumerate(columns):
        x=44+i*222
        deck.rect(x,191,206,204,WHITE,LINE,radius=True)
        deck.text(x+14,205,178,19,label,10.2,RED,True,role='label')
        deck.text(x+14,237,178,46,title,17,INK,True)
        deck.text(x+14,294,182,92,body,13.2,MUTED)
        if i<3:deck.arrow(x+209,280,10,14)
    deck.rect(44,413,872,60,PALE,radius=True)
    deck.text(57,426,145,19,'DESIGN RATIONALE',10.2,RED,True,role='label')
    deck.text(213,422,687,45,'Focused passages improve retrieval; repeated conditions protect applicability. Source fingerprints and index checks detect changed inputs.',13.5)
    deck.source('Narrative chunk size is a word target · table rows preserve their labels and conditions · original source bytes remain unchanged')
    deck.notes('''
        Timing: 2:30 to 6:00. Explain what happens to all eleven documents and why each preparation decision matters.

        The input is a collection of eleven HTML exports with approximately seventy-nine thousand extracted words and 139 tables, including nested tables. Document sizes are uneven, with the business-deposit-account procedure substantially larger than the others. The ingestion process profiles file identity, document title, publication text, section structure and tables before building the searchable collection.

        Extraction uses the meaningful policy classes in the HTML exports, including headings that are not ordinary heading tags. It explicitly decodes UTF-8 and retains paragraphs and lists. Scripts and display-only material are excluded, and linked content is not fetched. The original files are preserved so every derived passage can be checked against its source.

        Tables need more than plain text extraction. The parser retains column labels, carries conditions through rowspans, accounts for colspans and includes nested table text once. Oversized row continuations repeat their leftmost condition. This is intended to reduce the risk of separating an action from the situation in which it applies. Text-preservation checks are useful, but do not establish that every table branch has been interpreted correctly.

        Narrative passages target roughly 110 whitespace words within a section. Long blocks use a 20-word overlap to reduce context loss at a boundary. Unsplit table rows can reach 130 words, and repeating a condition can make a continuation longer. These are word targets; a separate model-token budget limits the prompt. Shorter passages were selected after larger groupings introduced competing instructions during development. The choice is empirical rather than a universal optimum.

        Each passage records its procedure ID, section, source filename, publication text, original-file hash, stable passage identity and table location where relevant. An identical rebuild preserves passage IDs. Source changes require reindexing. The vector matrix is bound to the passage store and checked for shape, finite values, normalization and its own file hash.

        The resulting collection has 1,388 passages with a BM25 keyword index and normalized 384-dimensional MiniLM vectors. These complementary indexes support exact terminology and paraphrases. At question time, rankings are combined and reranked before selecting the evidence pack. Retrieval scores rank source matches; they do not estimate the probability that a generated answer is correct.

        Transition: the prepared collection now feeds the request architecture, where evidence selection, generation and output checks operate together.
    ''')

    # 3. One traceable pipeline, with explicit choices and failure paths.
    deck.new(3,'Build the answer','Retrieve the rule. Generate an answer.\nCheck the claims before release.',
             'A small local pipeline makes evidence, control decisions and failure outcomes inspectable.')
    deck.rect(44,185,872,26,PALE,radius=True)
    deck.text(57,190,846,18,'PREPARED OFFLINE   Verified passages + keyword statistics + normalized vectors',11.6,MUTED,role='label')
    stages=[('UNDERSTAND','Question context\n+ search scope'),('RETRIEVE','BM25 + MiniLM\nfusion + rerank'),
            ('SELECT','≤3 passages\n~520 words'),('GENERATE','Qwen3-4B Q4\nlocal CPU'),
            ('CHECK','Citations\nNumbers\nSupport'),('RESPOND','Cited answer\nor source review')]
    for i,(label,body) in enumerate(stages):
        x=44+i*148
        deck.text(x,227,132,17,label,9.5,RED,True,role='label')
        deck.rect(x,252,132,75,WHITE,LINE,radius=True)
        if i in {3,4}:deck.rect(x,252,132,3,GOLD if i==4 else RED)
        box=deck.text(x+10,260,112,59,body,13.4,INK,True)
        box.text_frame.vertical_anchor=MSO_ANCHOR.MIDDLE
        if i<5:deck.arrow(x+135,278,10,13)
    deck.rect(44,340,429,34,AMBER_PALE,radius=True)
    deck.text(55,348,407,25,'Weak evidence → clarify or report insufficient support.',12.5)
    deck.rect(488,340,428,34,AMBER_PALE,radius=True)
    deck.text(499,348,406,25,'Failed checks → one revision → withhold if still failing.',12.5)
    for x,title,body in [(44,'Why retrieval-augmented generation?','Replaceable source material and explicit citations.'),
                         (341,'Why hybrid search?','Exact identifiers plus paraphrases; jointly rerank.'),
                         (638,'Why this runtime?','Local CPU, no API key; small in-memory index.')]:
        deck.text(x,399,278,29,title,14.1,INK,True)
        deck.text(x,435,278,42,body,13.3,MUTED)
    deck.source('MiniLM-L6 embeddings and reranking · DeBERTa NLI support screening · source identity and claim-local citations')
    deck.notes('''
        Timing: 6:00–9:30. Explain the request in order, then defend the choices and their limits.

        A request first passes basic length, identifier and direct-instruction checks. The resolver identifies an explicit procedure, a new named topic or a continuation of the user's situation. Search scope is enforced before retrieval. Sources and cached index artifacts are checked for changes, including the vector-matrix hash, dimensions and normalization.

        BM25 and normalized MiniLM embeddings search the same 1,388 passages. Reciprocal rank fusion combines their top candidates without comparing incompatible raw scores. The ms-marco MiniLM cross-encoder reranks the fused candidates. Weak retrieval signals lead to clarification or insufficient support. The small collection fits exact in-memory vector search, so a managed vector database would add infrastructure without demonstrated benefit here.

        Relevant source passages, including a bounded adjacent qualification when applicable, become the evidence pack. Qwen3-4B in Q4_K_M GGUF form generates locally through llama.cpp on CPU. Non-thinking operation, greedy decoding, a 3,800-input-token limit and a 240-output-token limit suit this constrained answer task. The prompt asks for the exact fact first, relevant conditions and citations, using only evidence. Greedy decoding does not guarantee correctness.

        Qwen3 was selected after development comparisons with a smaller Qwen2.5 baseline that produced more distracting detail and withheld drafts. This was an end-to-end engineering iteration, not an isolated causal experiment. Local inference avoids API-key and hosted inference dependencies for the local runtime, while adding CPU latency. A stronger approved deployment model still needs comparison before a pilot.

        Checks bind claims to their actual citations, compare numeric values and recognizable thresholds, and screen support. Substantive exact wording is matched to the cited passage; paraphrases use a DeBERTa NLI model. Its thresholds are development settings, not calibrated confidence. A failed draft gets at most one correction with the same evidence and failed-check feedback. If it still fails, the draft is withheld and source text remains available. The screen can also reject a correct answer or miss an error.

        This is one observable orchestrator with read-only evidence access, not an autonomous bank transaction agent. Activity records show real actions, counts and timings, not private model reasoning. RAG was chosen over fine-tuning for source replacement and traceability; sending every document would waste context and mix unrelated conditions.

        Transition: these controls matter only if an employee can understand and use them in conversation.
    ''')

    # 4. Put conversation design first; keep the example in a bounded panel.
    deck.new(4,'Experience and follow-ups','Context, citations and review\nin one conversational workflow.',
             'A follow-up retains the user’s situation while retrieving new supporting evidence.')
    for y,title,body in [
        (196,'Search and scope','Procedure library and guided starters; selected documents restrict retrieval.'),
        (287,'Follow-up resolution','Retain the situation. A new topic changes scope; every turn retrieves evidence.'),
        (390,'Inspect and review','Open citations, checks and activity; flag a response and export the investigation.')]:
        deck.text(44,y,300,28,title,16,INK,True)
        deck.text(44,y+35,300,60,body,13.7,MUTED)
    deck.rect(374,191,542,282,WHITE,LINE,radius=True)
    deck.text(391,207,508,19,'RECORDED CONVERSATION / PR63',10.2,RED,True,role='label')
    deck.text(391,239,508,41,'What is the overnight storage limit for a coin-counting machine?',14.6)
    deck.text(391,286,508,49,'The overnight storage limit for a coin-counting machine is $5,250 [S1].',15.5,TEAL,True)
    deck.line(391,341,508)
    deck.text(391,356,508,38,'And is monthly testing done in single or dual control?',14.6)
    deck.text(391,400,508,40,'Monthly testing is done in single control. [S2]',15.5,TEAL,True)
    deck.text(391,447,508,20,'S1: overnight storage → S2: monthly testing',11.7,MUTED)
    deck.source('Every turn retrieves evidence · prior generated answers are not source material · scope, reset, session isolation, feedback and export are supported')
    deck.notes('''
        Timing: 9:30 to 13:00. Explain the employee workflow and context rules, then use the short recorded dialogue as supporting evidence.

        The experience begins with focused access to the procedure collection. Employees can ask directly, use a guided starter, search the procedure library or restrict retrieval to a selected document. Scope is enforced: a question naming a different procedure asks the user to change the selected scope rather than answering from the wrong collection.

        Conversation state uses prior user questions to resolve the current situation. Previous generated claims are never factual evidence. A newly named task in the same procedure retains procedure scope while avoiding irrelevant terms from the earlier task. A hypothetical changing a condition keeps the earlier situation, even when the user repeats the procedure name or ID. An explicitly different topic replaces that context and searches the new procedure. Ambiguous or long conversations remain a limitation of the deterministic resolver.

        The panel reproduces actual recorded responses. The first question asks about overnight coin storage and receives the $5,250 answer with S1. The follow-up asks about single or dual control for monthly testing. The system retrieves the testing instruction and answers single control with S2. The example illustrates the context rule; the product capability is fresh evidence retrieval for each turn.

        Citation buttons select the source passage belonging to that answer. The Evidence desk exposes the procedure, section, publication text, source-file check and original document. Checks shows citation attribution, numeric consistency, recognized thresholds and support screening. Activity shows observed execution stages and elapsed times, with a deterministic explanation of the response decision rather than simulated private model reasoning.

        A failed draft may receive one correction using the same evidence and check feedback. If it still fails, the system withholds the draft and leaves the source passages available for review. Weak evidence or missing context produces an explicit insufficient-support or clarification outcome. These controls can still miss errors or reject a correct answer, so the original procedure remains inspectable.

        Browser sessions isolate conversation histories. New investigation resets the situation. Employees can mark a response for review and export the questions, answers, evidence, checks, activity and feedback. The export is opt-in; an enterprise audit and retention service is separate deployment work.

        Transition: the interface makes responses inspectable; evaluation must determine their accuracy, relevance, completeness and conciseness independently of presentation quality.
    ''')

    # 5. Explicitly cover all four required response-quality dimensions.
    deck.new(5,'Measure the evidence','Evaluate retrieval and response quality\nas separate measures.',
             'Measured local regression results; independent review is still required for an operational decision.')
    deck.text(44,189,305,18,'RELEVANT PASSAGE IN TOP FIVE',10.1,RED,True,role='label')
    for i,(label,mode) in enumerate([('Keyword','bm25'),('Semantic','dense'),('Hybrid + rerank','hybrid')]):
        y=223+i*34;value=retrieval[mode]['hit_at_5']
        deck.text(44,y,114,23,label,12.4,INK,i==2)
        deck.rect(165,y+5,126,11,LINE)
        deck.rect(165,y+5,126*value,11,RED if i==2 else '86A9A0')
        deck.text(300,y-1,65,25,f'{round(value*count)}/{count}',15.3,INK,True)
    deck.text(44,330,310,45,f'{fact_pass}/{count}',31,INK,True)
    deck.text(135,338,228,43,'answers pass the\nexpected-fact proxy',13.8,INK,True)
    deck.text(44,382,323,37,'Phrase matching can miss valid wording or pass an incorrect answer.',11.7,MUTED)
    deck.text(390,188,526,18,'WHAT TO MEASURE / WHAT A REVIEWER MUST JUDGE',10.1,RED,True,role='label')
    rows=[('Accuracy','Citations, numbers and support screens.','Is every instruction correct for this situation?'),
          ('Relevance','Passage ranking and direct response.','Does it answer the exact question?'),
          ('Completeness',f'{fact_pass}/{count} expected-fact proxy.','Are material conditions and exceptions included?'),
          ('Conciseness',f"{answer['mean_word_count']:.0f}-word mean draft; bounded output.",'Is it brief without losing necessary guidance?')]
    for i,(label,measure,judge) in enumerate(rows):
        y=218+i*47
        deck.line(390,y-4,526)
        deck.text(390,y+2,112,27,label,13.3,INK,True)
        deck.text(508,y,408,22,measure,12.2,MUTED)
        deck.text(508,y+21,408,22,judge,12.6,INK)
    deck.text(390,409,526,22,'Next: two independent reviewers, unseen scenarios, critical-error checks.',11.7,TEAL,True)
    deck.rect(44,442,872,35,PALE,radius=True)
    for x,value in [(56,f"{answer['evidence_only_fallbacks']}/{answer['generated_n']} generated evaluations: source only"),
                    (363,'2/4 original follow-ups: fact-proxy pass'),
                    (656,f"CPU p50 / p95: {answer['p50_seconds']:.1f}s / {answer['p95_seconds']:.1f}s")]:
        deck.text(x,450,292 if x==56 else 281 if x==363 else 248,23,value,10.8,INK,role='label')
    deck.source('30 procedure questions + 4 two-turn conversations + 6 selected guardrails · AI-authored/source-checked labels · cold load excluded · draft length n=32')
    deck.notes(f'''
        Timing: 13:00–17:00. This is the evidence slide. Separate passage retrieval, answer diagnostics, coverage and independent correctness.

        The suite contains 30 ordinary questions covering all eleven procedures, four two-turn conversations and six selected boundary cases. Nineteen ordinary questions are development cases and eleven are challenge cases. Labels were AI-authored from the supplied documents and source-checked; after development inspection, the challenge split is not a blind external holdout. Results describe this regression set, not enterprise accuracy.

        For the same questions, keyword search finds a labelled relevant passage in the first five results for 27 of 30 cases, semantic search for 28, and hybrid retrieval plus reranking for all 30. Hybrid mean reciprocal rank at five is {retrieval['hybrid']['mrr_at_5']:.4f}. Finding one labelled passage does not establish that every material exception was retrieved or that the generated answer is correct.

        The automatic expected-fact proxy passes {fact_pass} of 30 ordinary cases. It checks phrase groups, so it can miss a correct paraphrase and pass a wrong statement containing expected terms. A source-only fallback counts as a failure of generated-answer coverage even if the excerpts contain the answer. Across 35 generated evaluations, six drafts were withheld after checks. The four original final-turn follow-up proxies include two misses; those misses remain in the report. Six deliberately chosen boundary cases matched their expected statuses, which is not a general security assessment.

        The table makes the four requested quality dimensions explicit. Accuracy needs an independent reviewer to assess every instruction against the source and stated situation; citations, numeric consistency and NLI are only diagnostics. Relevance asks whether the exact question is answered without unrelated workflow detail. Completeness asks whether applicable conditions, exceptions, warnings and escalation requirements are present. Conciseness asks whether wording is brief without becoming incomplete. The measured mean draft length is {answer['mean_word_count']:.0f} words across {answer['draft_word_count_n']} drafts with recorded length, including withheld drafts; it is not a measure of answer usefulness.

        Serial local CPU latency is p50 {answer['p50_seconds']:.2f} and p95 {answer['p95_seconds']:.2f} seconds, excluding initial model load. The engineering suite has 49 passing tests for mechanics and safeguards, and real browser workflows were checked. Neither test count nor latency proves substantive correctness.

        Next, two operational subject-matter reviewers should independently score all four dimensions on unseen scenarios, adjudicate disagreements, and report critical errors separately from average scores. Include false refusals, answer coverage, source-version conflicts and long conversations. Compare employee task success and time to correct guidance against existing search before claiming business value.

        Transition: these findings shape both what we will demonstrate now and what leadership should validate next.
    ''')

    # 6. Demonstrate the implemented behavior and conclude with engineering next steps.
    deck.new(6,'Demonstration','Demonstrate answers, follow-ups\nand evidence review.',
             'Show the functional chat with procedure questions, changed conditions and a clear review path.')
    deck.text(44,190,475,19,'DEMONSTRATION SEQUENCE',10,RED,True,role='label')
    demo_rows=[('01','Ask a routine rule','Coin overnight limit → monthly-testing follow-up.','$5,250 overnight; single control for testing. [PR63]'),
               ('02','Change a condition','Emailed notary document → requester is present.','The emailed-document restriction still applies. [PR1000]'),
               ('03','Inspect an exception','Newer account → Private Bank Experience exception.','$1,000/day base rule; inspect the exception. [PR1949]')]
    for i,(number,title,prompt,outcome) in enumerate(demo_rows):
        y=220+i*69
        deck.pill(44,y,35,number,PALE,RED,size=10.4)
        deck.text(91,y-1,444,23,title,15.1,INK,True)
        deck.text(91,y+25,444,20,prompt,11.7,MUTED)
        deck.text(91,y+44,444,22,outcome,11.7,TEAL,True)
    deck.line(560,190,1,height=238)
    deck.text(584,190,332,20,'WHAT TO OBSERVE',10,RED,True,role='label')
    for y,title,body in [
        (220,'Grounding and traceability','Inspect the exact passage and the checks behind the released response.'),
        (291,'Conversation continuity','Preserve applicable conditions; change topics without carrying old evidence.'),
        (362,'Bounded failure handling','Clarify missing context or show sources when an answer cannot pass checks.')]:
        deck.text(584,y,332,25,title,13.9,INK,True)
        deck.text(584,y+29,332,43,body,12.5,MUTED)
    deck.rect(44,448,872,29,GREEN_PALE,radius=True)
    deck.text(56,454,848,22,'Next: independent quality review, broader exception tests and deployment controls.',13.8,TEAL,True)
    deck.source('Generative AI: development assistance and local runtime answering · recorded outputs and test results are checked against source procedures')
    deck.notes('''
        Timing: 17:00 to 20:00, followed by the separate 15-minute solution walkthrough. Demonstrate the implemented behavior and connect it to the engineering decisions.

        The demonstration should show three aspects of the solution: source grounding, conversation continuity and a clear outcome when evidence is insufficient. Use the live application or identify the approved silent recording as a recording. The saved walkthrough lasts 9 minutes 25 seconds and leaves time within the 15-minute segment for live source inspection and technical questions.

        Begin with the coin-machine overnight limit and a follow-up about monthly testing. Open the source for each answer and show that the second turn uses the testing passage. Next, ask about notarizing an emailed document and change the condition by making the requester physically present. The supplied restriction remains applicable; the changed condition must not become unsupported permission.

        Then ask the savings-bond limit for an account open less than twelve months and follow up about The Private Bank Experience. PR1949 states a $1,000 daily aggregate limit and an exception for eligible customers regardless of account age. Other applicable conditions remain. In the approved recording, the exception draft still fails a check after one correction. The tool therefore exposes the original text for review instead of presenting that draft as an accepted answer.

        Also show a topic change, missing context after reset, an unsupported question, review feedback and the evidence export. Use the Evidence, Checks and Activity views to explain how the system reached its release or source-review decision. These are observable actions and screening results; a fluent answer and a passing screen do not establish independent correctness.

        The technical conclusions follow from the evidence. Structural ingestion and source identity support traceability. Hybrid retrieval combines exact terminology and paraphrases. A bounded local model call keeps the evidence boundary inspectable, with CPU latency as a tradeoff. Context rules improve continuity while keeping prior generated answers out of the evidence. Output screening increases inspectability but can cause unnecessary withholding and still needs independent assessment.

        The next engineering work is independent review of all four response-quality dimensions, broader condition and exception coverage, and stronger-model, latency and concurrency comparisons. Any operational deployment also requires authoritative source versions, employee access controls, monitoring, escalation and rollback. Those capabilities are future work and are not presented as implemented.

        Generative AI assisted design, implementation, test-case drafting and presentation preparation, and Qwen powers runtime answering. Validation includes source checks, automated engineering tests, retained response traces and actual browser workflows. AI-authored labels remain subject to independent review.

        Handoff: open the prepared tool workflow and ask the first procedure question.
    ''')

    deck.prs.core_properties.title='Branch Assist | Grounded conversational procedure guidance'
    deck.prs.core_properties.subject='Solution methodology, architecture, document engineering, user experience and evaluation'
    deck.prs.core_properties.author='Branch Assist'
    deck.prs.core_properties.comments='Generative conversational solution over eleven procedures. Measured diagnostics and independent quality assessment are distinguished.'
    working=root/'artifacts/video_build'/('presentation_build_'+uuid.uuid4().hex[:8])
    working.mkdir(parents=True)
    output=working/(DECK_BASENAME+'.pptx')
    deck.prs.save(output)
    try:
        render_in_powerpoint(deck,output)
    except Exception as error:
        if type(error).__module__ not in {'pywintypes','builtins'} or isinstance(error,ValueError):raise
        render_in_libreoffice(deck,output,error)
    for suffix in ['.pptx','.pdf']:
        shutil.copy2(output.with_suffix(suffix),root/'submission'/(DECK_BASENAME+suffix))
    return deck
