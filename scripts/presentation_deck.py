"""Six-slide leadership narrative, built as editable native PowerPoint objects.

PowerPoint or local LibreOffice Impress exports the PDF and slide previews.
No generated slide image replaces editable text, diagrams or charts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
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
from learning_notes import load_learning_notes, apply_learning_note

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

    def notes(self,value):apply_learning_note(self.slide,value)

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
    learning_notes=load_learning_notes(root)
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
    deck.notes(learning_notes[0])

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
    deck.notes(learning_notes[1])

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
    deck.notes(learning_notes[2])

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
    deck.notes(learning_notes[3])

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
    deck.notes(learning_notes[4])

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
    deck.notes(learning_notes[5])

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
