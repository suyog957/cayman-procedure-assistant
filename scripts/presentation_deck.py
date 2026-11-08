"""Six-slide leadership narrative, built as editable native PowerPoint objects.

PowerPoint itself exports the PDF and slide previews. No generated slide image
is used in place of editable text, diagrams or charts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import textwrap

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
STAGES=['Need','Content','Architecture','Experience','Evidence','Decision']


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
        self.text(638,28,120,16,'INTERVIEW PROTOTYPE',8.1,MUTED,True,role='source')
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


def build_leadership_deck(root,corpus,metrics):
    deck=LeadershipDeck(root)
    answer=metrics['answers'];retrieval={r['mode']:r for r in metrics['retrieval'] if r['split']=='all'}
    count=answer['ordinary_n'];fact_pass=round(answer['all_required_facts_proxy']*count)

    # 1. The mandate and a tangible employee outcome, without a red cover wall.
    deck.new(1,'The employee need')
    deck.text(44,71,490,20,'THE EMPLOYEE NEED',10.5,RED,True,role='label')
    deck.text(44,102,492,101,'From procedure search\nto guidance you can verify.',33,INK,True,font='Georgia',role='headline')
    deck.text(44,213,475,57,'A working conversational assistant for the situation behind a branch employee’s question.',17,MUTED)
    deck.text(44,286,475,17,'EMPLOYEE TASK',10.5,RED,True,role='label')
    deck.text(44,308,475,43,'Find the applicable rule, conditions and exceptions.',16)
    deck.text(44,354,475,17,'DESIGN RESPONSE',10.5,RED,True,role='label')
    deck.text(44,376,485,29,'Ask → inspect the source → refine the situation.',16)
    deck.rect(560,88,356,318,WHITE,LINE,radius=True)
    deck.text(580,107,316,18,'A REAL PROCEDURE QUESTION',10,RED,True,role='label')
    deck.rect(580,138,316,58,PALE,radius=True)
    deck.text(593,149,290,43,'How much coin can stay in a machine overnight?',16)
    deck.text(580,216,316,17,'BRANCH ASSIST / RECORDED ANSWER',9.5,MUTED,True,role='label')
    deck.text(580,245,165,48,'$5,250',34,TEAL,True)
    deck.text(751,249,143,43,'maximum overnight\nin a single machine',13.5,MUTED)
    deck.text(580,308,316,45,'Open the cited rule and inspect its conditions.',16)
    deck.pill(580,368,235,'PR63  ·  original source available')
    for x,value,label in [(44,'11','supplied procedures'),(341,'139','HTML tables'),(638,f"{corpus['chunk_count']:,}",'traceable passages')]:
        deck.text(x,424,95,37,value,25,INK,True)
        deck.text(x+100,435,175,23,label,13,MUTED)
    deck.line(44,414,872)
    deck.text(44,469,872,21,'Business goal to test: faster access to correct guidance, with evidence employees can inspect.',13.4,TEAL,True)
    deck.source('Interview prototype · supplied Cayman Bank snapshot · AI-assisted development and runtime answers · no transaction execution')
    deck.notes('''
        Timing: 0:00–2:30. The leadership story starts with an employee trying to find the right rule for a particular situation.

        Branch employees often need a specific answer from a long procedure while they are helping someone. Finding a keyword is only part of the task. The employee needs the applicable action, the conditions that make it applicable, and any exception that changes the outcome. The business objective is faster access to correct guidance, with evidence the employee can inspect. No time savings or productivity uplift have been measured in this exercise.

        I built a functional conversational assistant over all eleven supplied Cayman Bank procedures. The collection includes 139 HTML tables and produces 1,388 traceable passages. The example on the right is a real source fact and a recorded tool outcome: the overnight limit is $5,250 in a single coin-counting machine. The employee can open the original passage rather than taking the fluent answer on trust.

        Three ideas hold the solution together. First, keep the rule attached to its situation during document preparation. Second, retrieve relevant source material before asking a language model to write an answer. Third, make sources, checks and appropriate fallback part of the employee experience. A follow-up starts a fresh evidence search; a previous generated answer is never treated as proof.

        The delivered prototype includes actual local language-model inference, a conversational workspace, source inspection, procedure search, feedback, exports and measured evaluation. It does not execute transactions or establish that the supplied snapshot is current production policy. The Wells Fargo-inspired visual treatment is explicitly an interview prototype over the supplied Cayman Bank documents.

        Generative AI assisted requirements analysis, implementation, tests and presentation preparation, and powers runtime answers. The candidate owns the review and must be able to explain the decisions personally. AI-authored evaluation cases are useful regression material, not independent ground truth. The recommendation is a scoped validation phase with procedure owners before any operational pilot.

        Transition: to understand why this answer can be checked, first look at how the original rules were organized.
    ''')

    # 2. A source rule stays attached to its situation throughout preparation.
    deck.new(2,'Organize the rules','Reliable answers start with\nwell-organized rules.',
             'Preserve the situation attached to each instruction before searching for an answer.')
    deck.rect(44,191,300,176,WHITE,LINE,radius=True)
    deck.text(59,203,270,22,'PR63: keep the task and control together',13.8,INK,True)
    deck.rect(59,236,270,25,PALE)
    deck.text(69,240,155,18,'Situation',11.5,MUTED,True,role='label')
    deck.text(230,240,95,18,'Control',11.5,MUTED,True,role='label')
    for y,task,control in [(271,'Monthly testing','Single'),(300,'Weekly balancing','Dual'),(329,'Random monthly cash count','Dual')]:
        deck.text(69,y,153,31,task,12.8)
        deck.text(230,y,85,23,control,13.5,TEAL,True)
    for x,label,title,body in [
        (366,'01 / PARSE','Keep structure','HTML headings, lists and table rows. Linked content is not fetched.'),
        (553,'02 / CHUNK','Keep context','~110 narrative words; 20-word overlap. Carry table labels and conditions.'),
        (740,'03 / TRACE','Keep identity','Procedure, section, date and original-file fingerprint on each passage.')]:
        deck.text(x,197,176,18,label,10,RED,True,role='label')
        deck.text(x,227,176,27,title,17,INK,True)
        deck.text(x,266,176,99,body,14.2,MUTED)
    deck.text(44,385,872,18,'SEARCH THE SAME VERIFIED PASSAGE COLLECTION',10.5,RED,True,role='label')
    for i,(title,detail) in enumerate([
        ('Exact terms','BM25 keyword search'),('Same meaning','MiniLM · 384 dimensions'),
        ('Combine + rerank','Rank fusion + cross-encoder'),('Select evidence','≤3 passages / ~520 words')]):
        x=44+i*222
        deck.rect(x,412,206,57,WHITE,LINE,radius=True)
        deck.text(x+11,421,184,23,title,14.7,INK,True)
        deck.text(x+11,447,184,19,detail,10.8,MUTED,role='label')
        if i<3:deck.arrow(x+209,434,10,12)
    deck.source('Supplied PR63 facts · 110 words is a narrative target, not an exact token count · table continuations repeat their condition')
    deck.notes('''
        Timing: 2:30–6:00. Continue the coin-machine example to explain the data choices, not simply the tools.

        A monthly task is not enough context to choose a control level. In PR63, monthly testing is single control, while weekly balancing and random monthly cash counts use dual control. If extraction separates the action from its row label, the generator can retrieve the right words and still give the wrong instruction. This is why the content design comes before model selection.

        The eleven input files are HTML exports with meaningful policy classes. The parser recognizes titles, publication text, sections and subsections, and explicitly decodes UTF-8. It removes scripts and presentation-only material, never executes source HTML, and does not fetch linked procedures. Linked material is outside the supplied evidence boundary.

        Tables are serialized with column labels, row conditions and positions. Rowspans carry their conditions forward; colspans preserve alignment; nested table content is included once. Oversized row continuations repeat the leftmost condition. This reduces detachment of a requirement from its situation, but does not prove that every complex table has been semantically interpreted correctly.

        Narrative passages target roughly 110 whitespace words within a section. Long blocks overlap by 20 words. Unsplit table rows can reach 130 words, and a repeated condition can make a continuation longer. These are word targets. The generator separately enforces its prompt-token budget. An earlier larger grouping diluted specific instructions, so shorter passages were selected after observing development failures.

        Every passage retains its procedure ID, source filename and hash, section, publication text, anchor and table location. The original eleven files remain unchanged. Identical input produces stable passage identities; changed input requires rebuilding the index. Extraction diagnostics found all checked paragraph five-word sequences, which is evidence of text preservation, not proof of policy interpretation.

        Search then combines complementary strengths: BM25 for exact identifiers and specialized wording; MiniLM vectors for paraphrases; reciprocal rank fusion to combine positions; and a cross-encoder to judge question and passage jointly. It selects up to three nonduplicate passages, targeting about 520 words. Ranking scores choose evidence; they are not probabilities that an answer is correct.

        Transition: the next slide follows that evidence through the live request, including the release and fallback decisions.
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
    deck.source('MiniLM-L6 embeddings/reranker · DeBERTa NLI support screen · bounded orchestration · no transaction tools or confidence percentage')
    deck.notes('''
        Timing: 6:00–9:30. Explain the request in order, then defend the choices and their limits.

        A request first passes basic length, identifier and direct-instruction checks. The resolver identifies an explicit procedure, a new named topic or a continuation of the user's situation. Search scope is enforced before retrieval. Sources and cached index artifacts are checked for changes, including the vector-matrix hash, dimensions and normalization.

        BM25 and normalized MiniLM embeddings search the same 1,388 passages. Reciprocal rank fusion combines their top candidates without comparing incompatible raw scores. The ms-marco MiniLM cross-encoder reranks the fused candidates. Weak retrieval signals lead to clarification or insufficient support. The small collection fits exact in-memory vector search, so a managed vector database would add infrastructure without demonstrated benefit here.

        Relevant source passages, including a bounded adjacent qualification when applicable, become the evidence pack. Qwen3-4B in Q4_K_M GGUF form generates locally through llama.cpp on CPU. Non-thinking operation, greedy decoding, a 3,800-input-token limit and a 240-output-token limit suit this constrained answer task. The prompt asks for the exact fact first, relevant conditions and citations, using only evidence. Greedy decoding does not guarantee correctness.

        Qwen3 was selected after development comparisons with a smaller Qwen2.5 baseline that produced more distracting detail and withheld drafts. This was an end-to-end engineering iteration, not an isolated causal experiment. Local inference avoids API-key and hosted inference dependencies for the exercise, while adding CPU latency. A stronger approved deployment model still needs comparison before a pilot.

        Checks bind claims to their actual citations, compare numeric values and recognizable thresholds, and screen support. Substantive exact wording is matched to the cited passage; paraphrases use a DeBERTa NLI model. Its thresholds are development settings, not calibrated confidence. A failed draft gets at most one correction with the same evidence and failed-check feedback. If it still fails, the draft is withheld and source text remains available. The screen can also reject a correct answer or miss an error.

        This is one observable orchestrator with read-only evidence access, not an autonomous bank transaction agent. Activity records show real actions, counts and timings, not private model reasoning. RAG was chosen over fine-tuning for source replacement and traceability; sending every document would waste context and mix unrelated conditions.

        Transition: these controls matter only if an employee can understand and use them in conversation.
    ''')

    # 4. Genuine dialogue, plus a real source-pane crop from the approved take.
    deck.new(4,'Use the conversation','One question becomes a conversation\nyou can inspect.',
             'Use the source to check the answer, then change the task or refine the situation.')
    deck.text(44,189,500,19,'RECORDED TOOL WORKFLOW / PR63',10.2,RED,True,role='label')
    deck.rect(44,219,500,48,PALE,radius=True)
    deck.text(57,227,474,39,'What is the overnight storage limit for a coin-counting machine?',15.2)
    deck.text(57,282,474,54,'The overnight storage limit for a coin-counting machine is $5,250 [S1].',17,TEAL,True)
    deck.rect(44,344,500,45,PALE,radius=True)
    deck.text(57,351,474,38,'And is monthly testing done in single or dual control?',15.2)
    deck.text(57,405,474,36,'Monthly testing is done in single control. [S2]',17,TEAL,True)
    deck.text(584,187,332,18,'[S2] PR63 / MONTHLY TESTING',10.3,RED,True,role='label')
    deck.rect(578,211,338,258,WHITE,LINE,radius=True)
    deck.image_crop(root/'assets/presentation/recorded_followup_evidence.png',584,217,328,248,
                    (2108,600,844,638))
    deck.text(44,459,500,23,'Same procedure. Fresh evidence for the new task.',12.8,INK,True)
    deck.source('Actual recorded answers and source-pane capture · inspect Evidence / Checks / Activity · topic switch, reset, feedback and export are supported')
    deck.notes('''
        Timing: 9:30–13:00. Read the short conversation and point to the selected evidence, then explain the broader experience.

        The dialogue reproduces actual recorded application responses. First the employee asks about the overnight coin-machine limit. The assistant answers $5,250 and cites S1. The employee then asks whether monthly testing is single or dual control. The assistant retrieves the monthly-testing instruction and answers single control with S2. The source crop on the right is an unaltered browser capture from the approved recording, displayed through a native PowerPoint crop.

        The useful behavior is fresh evidence for a different task within the same procedure. The resolver retains PR63 as the topic but does not dilute testing retrieval with overnight-storage wording. Citation buttons select the exact passage for that particular answer. The employee can read the section, date and surrounding conditions or download the original procedure.

        Different follow-ups require different handling. After an emailed-document notary question, saying that the requester is physically present must retain the emailed-document situation. The supplied rule still prohibits it. A hypothetical repeating the notary topic or PR1000 now preserves that original condition too. An explicitly different topic, such as savings-bond fees, replaces old scope and retrieves a new procedure. This is bounded deterministic context handling; ambiguous long conversations remain a limitation.

        The workspace includes guided starters, optional procedure scope, a searchable library and an Evidence desk. Evidence shows original text and source identity. Checks exposes citation, amount, threshold and support screening. Activity shows the actions that actually ran and their timings. A failed draft can be corrected once; a still-failing draft is withheld while original evidence stays available. The interface does not show a fabricated certainty score.

        Search scope is a real restriction: a question about a different selected procedure prompts clarification. New investigation clears conversation context. Browser sessions keep histories isolated, while model objects are cached for reuse. The employee can mark a response for review and export the conversation with sources, checks, activity and feedback. These are session features, not an implemented enterprise audit service.

        The demo later shows these cases in the live tool or the approved silent recording. Source-code editors and terminals are excluded, as required by the assignment.

        Transition: now distinguish a convincing interaction from evidence that the solution answers reliably.
    ''')

    # 5. Explicitly cover all four required response-quality dimensions.
    deck.new(5,'Measure the evidence','Finding evidence is the first test.\nAnswer quality is the next.',
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

    # 6. A clear demo handoff and a responsible leadership decision.
    deck.new(6,'Demonstrate and decide','Demonstrate the workflow.\nValidate before a pilot.',
             'The working prototype is ready to inspect; the next decision is a scoped validation phase.')
    deck.text(44,190,475,19,'DEMONSTRATE / LIVE TOOL OR APPROVED RECORDING',10,RED,True,role='label')
    demo_rows=[('01','Ask a routine rule','Coin overnight limit → monthly-testing follow-up.','$5,250 overnight; single control for testing. [PR63]'),
               ('02','Change a condition','Emailed notary document → requester is present.','The emailed-document restriction still applies. [PR1000]'),
               ('03','Inspect an exception','Newer account → Private Bank Experience exception.','$1,000/day rule; review the source if checks fail. [PR1949]')]
    for i,(number,title,prompt,outcome) in enumerate(demo_rows):
        y=220+i*69
        deck.pill(44,y,35,number,PALE,RED,size=10.4)
        deck.text(91,y-1,444,23,title,15.1,INK,True)
        deck.text(91,y+25,444,20,prompt,11.7,MUTED)
        deck.text(91,y+44,444,22,outcome,11.7,TEAL,True)
    deck.line(560,190,1,height=238)
    deck.text(584,190,332,20,'VALIDATE / OWNERS AND GATES',10,RED,True,role='label')
    for y,title,body in [(220,'Quality · procedure owners + SMEs','Unseen scenarios; four quality scores.\nCritical errors and coverage are separate gates.'),
                         (291,'Value · branch operations + AI team','Task success; time to correct guidance.\nCompare with current search.'),
                         (362,'Pilot controls · security + platform','Identity, source access/versioning, monitoring and rollback.')]:
        deck.text(584,y,332,25,title,13.9,INK,True)
        deck.text(584,y+29,332,41,body,12.5,MUTED)
    deck.rect(44,448,872,29,GREEN_PALE,radius=True)
    deck.text(56,454,848,22,'Recommendation: validate quality and employee value before an operational pilot.',14,TEAL,True)
    deck.source('20-minute presentation → 15-minute walkthrough · approved silent recording 9:25 + live inspection/Q&A · AI assistance disclosed; candidate owns decisions')
    deck.notes('''
        Timing: 17:00–20:00, followed by the separate 15-minute technical walkthrough. Close the leadership story with a concrete demonstration and decision.

        We started with an employee trying to find the applicable branch rule. We preserved the rule's situation during ingestion, retrieved evidence before generation, exposed the checks and tested retrieval and response quality separately. The working prototype demonstrates the approach; independent validation determines where it is safe and useful.

        The walkthrough will use the actual application or the clearly labelled approved silent recording. First, ask the overnight coin limit and follow up about monthly testing. Inspect both source passages to show that a different task uses fresh evidence. Next, ask about notarizing an emailed document and change the condition by making the requester physically present. The prohibition remains. Finally, ask the savings-bond limit for an account younger than twelve months, then the Private Bank Experience exception. The source's $1,000 daily aggregate limit has a stated exception; in the approved recording, the generated exception draft fails a check after one correction, so the tool retains the original source text for review. Do not present that fallback as a successful generated answer.

        During the walkthrough, also show a topic switch, missing context after reset, unsupported requests, feedback and the evidence export. Share the application and slides, never implementation source. The approved 9:25 recording fits within the 15-minute allocation and leaves time for live source inspection and questions. Keep the local model warm and the recorded backup available; a recording must be identified as such.

        The recommendation is a scoped validation phase. Procedure owners and two independent subject-matter reviewers should evaluate unseen scenarios across accuracy, relevance, completeness and conciseness. Critical unsupported instructions need explicit investigation and a release gate; coverage and unnecessary refusal must stay visible. The business and validation teams must agree acceptable thresholds rather than treating the development metrics as achieved enterprise service levels.

        Branch operations and AI engineering should measure task success and time to correct guidance against current search, and compare stronger approved models with realistic latency and cost. Before an operational pilot, security and platform owners need employee identity, document entitlements, authoritative source versions, approved audit and retention, monitoring, escalation and rollback. These are future production requirements, not completed features of the exercise.

        Generative AI assisted design, implementation, evaluation drafting and these materials; local Qwen generation powers the tool. Candidate understanding, accurate disclosure and ownership remain essential. The six-slide presentation and its supporting PDFs exclude implementation source, and the approved final video remains preserved unchanged.

        Handoff: move into the prepared walkthrough and ask the first coin-machine question.
    ''')

    deck.prs.core_properties.title='Branch Assist | From procedure search to verifiable guidance'
    deck.prs.core_properties.subject='Six-slide senior leadership narrative over eleven supplied procedures'
    deck.prs.core_properties.author='Candidate preparation materials'
    deck.prs.core_properties.comments='AI-assisted interview prototype; measured diagnostics are not independent correctness validation. No implementation source.'
    output=root/'submission/Cayman_Procedure_Assistant.pptx'
    deck.prs.save(output)
    render_in_powerpoint(deck,output)
    return deck
