"""Compose the source-free 1080p walkthrough from real UI footage and narration.

The app is never mocked. Explanatory cards use saved corpus/evaluation records;
recorded regression examples are labelled. Captions, chapters, a transcript,
poster, provenance, and a playback page accompany the encoded video.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import math
import re
import shutil
import subprocess
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'artifacts/video_build'
OUT = ROOT/'demo'
FRAMES = BUILD/'frames'
ENCODED = BUILD/'encoded'
for folder in [FRAMES, ENCODED, OUT]:
    folder.mkdir(exist_ok=True,parents=True)
W,H,FPS = 1920,1080,30
RED='#d71e28'; GOLD='#ffcd41'; INK='#3b3331'; MUTED='#746c69'; WARM='#f9f7f6'; LINE='#e2dbd7'
GREEN='#285e4c'; PURPLE='#5a469b'
FONT=Path('C:/Windows/Fonts')


def font(size, bold=False, serif=False):
    return ImageFont.truetype(str(FONT/('georgia.ttf' if serif else 'segoeuib.ttf' if bold else 'segoeui.ttf')),size)


def wrap(draw, text, face, width):
    lines=[]
    for paragraph in text.split('\n'):
        current=''
        for word in paragraph.split():
            candidate=(current+' '+word).strip()
            if draw.textlength(candidate,font=face)>width and current:
                lines.append(current);current=word
            else:current=candidate
        lines.append(current)
    return lines


def text(draw, xy, content, size=26, color=INK, width=1350, bold=False, serif=False, gap=8):
    face=font(size,bold,serif); x,y=xy
    for line in wrap(draw,content,face,width):
        draw.text((x,y),line,font=face,fill=color)
        y+=size+gap
    return y


def box(draw, bounds, fill='white', outline=LINE, radius=18):
    draw.rounded_rectangle(bounds,radius=radius,fill=fill,outline=outline,width=2)


def label(draw,xy,value,color=RED,size=17):
    return text(draw,xy,value,size,color,bold=True,gap=5)


def standard_frame(scene, index, total):
    im=Image.new('RGB',(W,H),WARM);d=ImageDraw.Draw(im)
    label(d,(28,9),scene['chapter'].upper(),RED,16)
    text(d,(28,32),scene['title'],31,INK,width=1530,bold=True,gap=0)
    label(d,(1635,16),'INTERVIEW PROTOTYPE',INK,15)
    text(d,(1635,40),f'{index:02d} / {total:02d}  ·  RECORDED DEMO',15,MUTED,width=260,gap=0)
    d.line((24,76,1896,76),fill=LINE,width=2)
    d.line((24,76,24+round(1872*index/total),76),fill=RED,width=4)
    box(d,(24,88,1560,952),fill='white',outline=LINE,radius=10)
    label(d,(1590,108),'WHAT TO NOTICE',RED,16)
    y=text(d,(1590,145),scene['tag'],22,INK,width=298,bold=True,gap=7)
    y+=30
    for n,p in enumerate(scene['points'],1):
        d.ellipse((1590,y+3,1618,y+31),fill=GOLD)
        text(d,(1597,y+3),str(n),16,INK,width=25,bold=True,gap=0)
        y=text(d,(1633,y),p,24,INK,width=250,gap=8)+28
    d.line((1590,754,1888,754),fill=LINE,width=2)
    mode='RECORDED APP' if scene['kind']=='browser' else 'EXPLANATORY GRAPHIC'
    if scene.get('layout') in ['correction','fallback']:
        mode='RECORDED REGRESSION'
    label(d,(1590,779),mode,RED,17)
    text(d,(1590,813),'Actual outputs.\nSome pauses shortened.\nSources remain inspectable.',18,MUTED,width=295,gap=10)
    text(d,(1590,918),'Synthetic narration · supplied snapshot',14,MUTED,width=300,gap=0)
    d.rectangle((0,968,W,H),fill=INK)
    return im


def panel(d,x,y,width,title,body,color=RED,height=280):
    box(d,(x,y,x+width,y+height))
    d.rounded_rectangle((x+20,y+23,x+27,y+height-23),radius=3,fill=color)
    bottom=text(d,(x+49,y+29),title,30,color,width=width-75,bold=True,gap=7)
    text(d,(x+49,bottom+24),body,25,INK,width=width-82,gap=12)


def make_card(scene,index,total,capture,rows):
    im=standard_frame(scene,index,total);d=ImageDraw.Draw(im);kind=scene['layout']
    if kind in ['opening','closing']:
        d.rounded_rectangle((24,88,1560,952),radius=10,fill=RED,outline=RED)
        logo=Image.open(ROOT/'assets/brand/wells-fargo-wordmark.png').convert('RGBA')
        logo=logo.resize((286,30),Image.Resampling.LANCZOS);im.paste(logo,(1215,124),logo)
        label(d,(78,154),'BRANCH ASSIST  /  SUPPLIED PROCEDURE SNAPSHOT',GOLD,20)
        headline='An answer\nyou can inspect.' if kind=='opening' else 'Ask. Inspect.\nRefine. Review.'
        y=text(d,(78,260),headline,87,'white',width=1370,bold=False,serif=True,gap=18)
        text(d,(82,y+37),'Grounded generation. Visible checks. Measured limitations.',35,'white',width=1320,gap=14)
        for x,value,caption in [(82,'11','supplied procedures'),(575,'1,388','traceable passages'),(1115,'Local','generative inference')]:
            text(d,(x,730),value,69,GOLD,width=400,bold=True,gap=0)
            text(d,(x,822),caption,23,'white',width=420,gap=0)
        label(d,(82,912),'RECORDED WALKTHROUGH  ·  SYNTHETIC VOICE  ·  NO SOURCE CODE',GOLD,16)
    elif kind=='architecture':
        label(d,(70,125),'OFFLINE / PREPARE THE SNAPSHOT',RED,20)
        for x,title,body in [(70,'Original HTML','11 documents\nSource fingerprints'),(555,'Structural passages','Sections, tables, conditions\nStable identities'),(1040,'Local indexes','BM25 term statistics\n384-dimensional vectors')]:
            panel(d,x,170,445,title,body,height=220)
        label(d,(70,434),'RUNTIME / A BOUNDED, OBSERVABLE ORCHESTRATOR',RED,20)
        entries=[('Resolve + verify','Question context\nScope and source checks'),('Retrieve + rerank','BM25 + dense + RRF\nBounded evidence'),('Generate + screen','Local Qwen3-4B\nCitations, numbers, claims')]
        for x,(title,body) in zip([70,555,1040],entries):panel(d,x,480,445,title,body,height=228)
        box(d,(70,756,1485,898),fill='#f4f0ed')
        text(d,(105,783),'PASS → release     FAIL → one correction with the same evidence\nSTILL FAILS → withhold draft and retain original passages',30,INK,width=1325,bold=True,gap=16)
    elif kind=='ingestion':
        for x,value,title,body in [(70,'11','Original procedures','UTF-8 structural parsing\nHeadings and list boundaries'),(555,'139','HTML tables','Column labels and row conditions\nNested tables flattened'),(1040,'1,388','Traceable passages','~110 narrative words\n20-word overlap when split')]:
            box(d,(x,140,x+445,658));text(d,(x+34,180),value,81,RED,width=380,bold=True)
            text(d,(x+34,300),title,31,INK,width=380,bold=True)
            text(d,(x+34,380),body,26,INK,width=377,gap=16)
        text(d,(80,721),'Every passage retains source identity, section, publication text,\nfile fingerprint, location, and table/row metadata when applicable.',31,INK,width=1390,gap=18)
        label(d,(80,866),'EXTERNAL LINKS ARE NOT FETCHED · CONDITIONS STILL NEED REVIEW',RED,20)
    elif kind=='retrieval':
        panel(d,75,150,665,'BM25 / exact matching','Procedure IDs, specialized terms,\namounts and literal wording',height=220)
        panel(d,790,150,665,'Dense / semantic matching','Paraphrases and related meaning\nMiniLM · 384 dimensions',height=220,color=PURPLE)
        text(d,(240,412),'Reciprocal rank fusion → cross-encoder reranking',38,INK,width=1180,bold=True)
        panel(d,75,510,1380,'A compact evidence pack','Up to 3 nonduplicate passages · about 520 words\nAdjacent qualifications can be included · hard prompt budget remains',height=210)
        text(d,(85,785),'Regression evidence hit@5:  BM25 90.0%   /   Dense 93.3%   /   Hybrid 100.0%',29,RED,width=1390,bold=True)
        text(d,(85,858),'30 labelled questions. These are retrieval diagnostics, not answer accuracy.',24,MUTED,width=1390)
    elif kind=='correction':
        result=rows['B02']['result']
        before=result['checks']['rejected_attempts'][0]['draft_answer']
        after=result['answer']
        label(d,(75,126),'ACTUAL SAVED CASE B02 / BUSINESS TRUST SALES THRESHOLD',RED,20)
        panel(d,75,185,1380,'WITHHELD FIRST DRAFT',before,height=155)
        panel(d,75,390,1380,'DETERMINISTIC FAILED-CHECK FEEDBACK','Preserve threshold wording exactly, including less than versus or less.',height=170,color=PURPLE)
        panel(d,75,610,1380,'REVISED DRAFT / CHECKS PASSED',after,height=180,color=GREEN)
        text(d,(90,845),'Same evidence · one correction · same screens run again',29,INK,width=1370,bold=True)
    elif kind=='fallback':
        result=rows['N03']['result']
        label(d,(75,126),'ACTUAL SAVED CASE N03 / NOTARY EXCEPTION',RED,20)
        panel(d,75,180,1380,'SOURCE REVIEW NEEDED','Two drafts screened; claim-support checks still failed.\nThe generated answer was withheld and original passages retained.',height=215)
        source=result['sources'][0]['text']
        match=re.search(r'Exceptions:.*?customer status\.',source)
        quote=match.group(0) if match else source[:490]
        panel(d,75,445,1380,'RETRIEVED PROCEDURE EXCERPT',quote,height=255,color=GREEN)
        text(d,(90,757),'A useful failure analysis: the classifier can withhold plausible\nsource-supported wording. Review coverage and false refusals.',31,INK,width=1370,gap=16)
        label(d,(90,875),'SOURCE-ONLY IS NOT COUNTED AS A SUCCESSFUL GENERATED ANSWER',RED,19)
    elif kind=='mobile':
        screenshot=Image.open(ROOT/'artifacts/video_build/capture/mobile.png').convert('RGB')
        screenshot=screenshot.resize((359,777),Image.Resampling.LANCZOS)
        box(d,(96,120,483,923),fill=INK,outline=INK,radius=25);im.paste(screenshot,(110,133))
        panel(d,550,180,895,'A narrow viewport, actually checked','390 × 844 browser viewport\nNo horizontal overflow\nInterview-prototype label remains visible',height=285)
        panel(d,550,520,895,'A separate session starts empty','No messages from the desktop investigation\nSession-scoped history and feedback\nExport before resetting',height=285,color=GREEN)
    elif kind=='metrics':
        stats=[('100.0%','Evidence hit@5','Labelled evidence in top 5\n30 procedure questions'),('76.7%','Answer fact proxy','All expected fact groups\n23 of 30 ordinary answers'),('6 / 35','Source-only outcomes','Generated draft withheld\n35 evaluated generated calls')]
        for x,(value,title,body) in zip([70,555,1040],stats):
            box(d,(x,145,x+445,535));text(d,(x+30,175),value,65,RED,width=390,bold=True)
            text(d,(x+30,277),title,30,INK,width=390,bold=True)
            text(d,(x+30,359),body,24,MUTED,width=383,gap=15)
        text(d,(85,598),'CPU latency: p50 13.81s / p95 23.92s  ·  cold model load excluded',29,INK,width=1360,bold=True)
        text(d,(85,673),'Corrections: 9 attempted / 2 released  ·  original follow-up proxies: 2 / 4',28,INK,width=1360)
        text(d,(85,748),'37 automated tests + real-browser integration passed.',30,GREEN,width=1350,bold=True)
        label(d,(85,859),'AI-AUTHORED LABELS · FALLIBLE AUTOMATIC CHECKS · NO INDEPENDENT ACCURACY CLAIM',RED,17)
    elif kind=='review':
        entries=[(75,155,'Accuracy','Correct guidance for this situation?\nPreserves amounts and conditions?'),(790,155,'Relevance','Answers the actual employee task?\nAvoids distracting related rules?'),(75,480,'Completeness','Material requirements and exceptions?\nMissing evidence acknowledged?'),(790,480,'Conciseness','Enough detail to act appropriately?\nNo unnecessary explanation?')]
        for x,y,title,body in entries:panel(d,x,y,665,title,body,height=250)
        label(d,(85,830),'PROPOSED: INDEPENDENT REVIEWERS · UNSEEN SCENARIOS · CRITICAL-ERROR TRACKING',RED,19)
        text(d,(85,873),'Also measure correct guidance, time to completion, and unnecessary refusals.',25,INK,width=1360)
    elif kind=='production':
        for x,title,body in [(75,'Policy authority','Approved source owners\nEffective dates and supersession\nVersioned releases and rollback'),(560,'Independent quality','Unseen operational scenarios\nSME adjudication\nRisk-based release criteria'),(1045,'Operational controls','Identity and entitlements\nAudit, retention and monitoring\nConcurrency and incident response')]:
            panel(d,x,170,435,title,body,height=450)
        text(d,(85,708),'Next decision: a scoped validation effort with operational owners.',35,INK,width=1360,bold=True)
        text(d,(85,800),'These gates are proposed work, not completed enterprise capabilities.',28,RED,width=1360)
    else:raise ValueError(kind)
    return im


def stamp(seconds,ass=False):
    scale=100 if ass else 1000
    value=round(seconds*scale)
    hours,value=divmod(value,3600*scale);minutes,value=divmod(value,60*scale);secs,fraction=divmod(value,scale)
    if ass:return f'{hours}:{minutes:02d}:{secs:02d}.{fraction:02d}'
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{fraction:03d}'


ASS_HEADER='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,29,&H00FFFFFF,&H00FFFFFF,&H0031333B,&H0031333B,0,0,0,0,100,100,0,0,1,1,0,2,60,60,22,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''


def caption_phrases(sentence):
    phrases=[];current=[]
    for word in sentence.split():
        if len(' '.join(current+[word]))>132 or len(current)>=21:
            phrases.append(' '.join(current));current=[]
        current.append(word)
    if current:phrases.append(' '.join(current))
    return phrases


def ffmpeg(args,log_path):
    with log_path.open('w',encoding='utf-8') as log:
        subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-loglevel','warning','-y',*map(str,args)],
                       cwd=ROOT,stdout=log,stderr=log,check=True)


def probe(path):
    return json.loads(subprocess.check_output([shutil.which('ffprobe'),'-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(path)]))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--frames-only',action='store_true');args=parser.parse_args()
    story=json.loads((OUT/'storyboard.json').read_text(encoding='utf-8'))
    capture=json.loads((BUILD/'capture_manifest.json').read_text(encoding='utf-8'))
    assert capture['status']=='passed' and capture['mobile_verified'] and capture['independent_session_starts_empty']
    rows={r['id']:r for r in json.loads((ROOT/'artifacts/evaluation/answer_details.json').read_text(encoding='utf-8'))}
    shots={s['id']:s for s in capture['segments']}
    audio={a['id']:a for a in json.loads((BUILD/'audio_timeline.json').read_text(encoding='utf-8'))}
    assert len(audio)==len(story['scenes']),'Narration is incomplete'
    # Bring a deliberately unhurried synthetic take to a normal presentation pace.
    # Pitch is preserved; sentence timings are transformed by exactly this factor.
    base_duration=sum(a['duration'] for a in audio.values())
    tempo=max(1.0,min(1.5,base_duration/(13*60+30)))
    offset=0.0;timeline=[];captions=[];transcript=[]
    chapters=[];previous_chapter=None
    raw=ROOT/capture['raw_video'];raw_duration=float(probe(raw)['format']['duration'])
    media_offset=raw_duration-max(s['end'] for s in shots.values())
    media_offset=min(0.0,max(-2.0,media_offset))
    for number,scene in enumerate(story['scenes'],1):
        base=audio[scene['id']]
        duration=math.ceil(base['duration']/tempo*FPS)/FPS
        if scene['chapter']!=previous_chapter:
            chapters.append({'start':offset,'title':scene['chapter'].split(' / ',1)[-1]})
            previous_chapter=scene['chapter']
        frame=standard_frame(scene,number,len(story['scenes'])) if scene['kind']=='browser' else make_card(scene,number,len(story['scenes']),capture,rows)
        frame_path=FRAMES/(scene['id']+'.png');frame.save(frame_path)
        if scene['id']=='opening':frame.save(OUT/'Branch_Assist_Cover.png')
        local_caps=[]
        for cap in base['captions']:
            phrases=caption_phrases(cap['text']);total_words=sum(len(s.split()) for s in phrases);spent=0
            for phrase in phrases:
                share=len(phrase.split())/total_words
                start=(cap['start']+(cap['end']-cap['start'])*spent/total_words)/tempo
                end=start+(cap['end']-cap['start'])*share/tempo
                local_caps.append({'start':start,'end':end,'text':phrase})
                captions.append({'start':offset+start,'end':offset+end,'text':phrase})
                spent+=len(phrase.split())
        ass=ASS_HEADER
        for cap in local_caps:
            body='\\N'.join(textwrap.wrap(cap['text'],width=108)).replace('{','').replace('}','')
            ass+=f"Dialogue: 0,{stamp(cap['start'],True)},{stamp(cap['end'],True)},Default,,0,0,0,,{body}\n"
        ass_path=FRAMES/(scene['id']+'.ass');ass_path.write_text(ass,encoding='utf-8')
        entry={'id':scene['id'],'title':scene['title'],'kind':scene['kind'],'chapter':scene['chapter'],
               'start':round(offset,4),'duration':duration,'end':round(offset+duration,4)}
        if scene['kind']=='browser':entry['capture']=scene['capture']
        timeline.append(entry)
        transcript.extend([f"### {int(offset//60):02d}:{int(offset%60):02d} — {scene['title']}",scene['narration'],''])
        offset+=duration
        if args.frames_only:continue
        target=ENCODED/(scene['id']+'.mp4')
        source_identity=shots[scene['capture']].get('raw_video',capture['raw_video']) if scene['kind']=='browser' else capture['raw_video']
        identity=sha256(json.dumps([scene,base['identity'],duration,tempo,source_identity,'layout-v3']).encode()).hexdigest()
        id_path=target.with_suffix('.sha256')
        if target.exists() and id_path.exists() and id_path.read_text()==identity:
            print('CACHED',scene['id'],flush=True);continue
        ass_arg=ass_path.relative_to(ROOT).as_posix()
        if scene['kind']=='browser':
            shot=shots[scene['capture']]
            start=max(0,shot['start']+media_offset)
            length=max(.2,shot['end']-shot['start']-.1)
            # Preserve normal motion when it fits; long processing pauses may be shortened.
            speed_factor=min(1.0,max(.2,(duration*.72)/length))
            graph=f'[0:v]setpts={speed_factor:.7f}*(PTS-STARTPTS),fps={FPS},scale=1536:864,tpad=stop_mode=clone:stop_duration={duration}[screen];[1:v][screen]overlay=24:88:shortest=1,ass={ass_arg}[v]'
            scene_raw=ROOT/shot['raw_video'] if shot.get('raw_video') else raw
            if shot.get('raw_video'):start=max(0,shot['start'])
            inputs=['-ss',start,'-t',length,'-i',scene_raw,'-loop','1','-framerate',FPS,'-i',frame_path]
        else:
            graph=f'[0:v]ass={ass_arg}[v]';inputs=['-loop','1','-framerate',FPS,'-i',frame_path]
        ffmpeg([*inputs,'-filter_complex',graph,'-map','[v]','-t',duration,'-r',FPS,'-an',
                '-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-threads','4',
                '-movflags','+faststart',target],ENCODED/(scene['id']+'.log'))
        id_path.write_text(identity)
        print('ENCODED',scene['id'],round(duration,1),'seconds',flush=True)
    (OUT/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
    if args.frames_only:return
    full_srt=''.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}\n\n" for i,c in enumerate(captions,1))
    (OUT/'Branch_Assist_Demo.srt').write_text(full_srt.rstrip()+'\n',encoding='utf-8')
    vtt='WEBVTT\n\n'+re.sub(r'(?<=\d),(?=\d{3}\b)', '.', re.sub(r'(?m)^\d+\n','',full_srt))
    (OUT/'Branch_Assist_Demo.vtt').write_text(vtt.rstrip()+'\n',encoding='utf-8')
    (OUT/'Branch_Assist_Transcript.md').write_text('# Branch Assist — narrated walkthrough\n\nRecorded application interactions. Synthetic narration. Supplied Cayman Bank snapshot; interview prototype.\n\n'+'\n'.join(transcript),encoding='utf-8')
    chapter_lines=[]
    for chapter in chapters:
        chapter_lines.append(f"{int(chapter['start']//60):02d}:{int(chapter['start']%60):02d} {chapter['title']}")
    (OUT/'chapters.txt').write_text('\n'.join(chapter_lines)+'\n',encoding='utf-8')
    metadata=';FFMETADATA1\ntitle=Branch Assist - Grounded AI Workflow\nartist=Suyog\ncomment=Recorded interview prototype; synthetic narration; supplied Cayman Bank procedures.\n'
    for i,c in enumerate(chapters):
        end=chapters[i+1]['start'] if i+1<len(chapters) else offset
        metadata+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['start']*1000)}\nEND={round(end*1000)}\ntitle={c['title']}\n"
    meta_path=BUILD/'chapters.ffmetadata';meta_path.write_text(metadata,encoding='utf-8')
    concat=BUILD/'concat.txt';concat.write_text(''.join("file '"+(ENCODED/(s['id']+'.mp4')).as_posix()+"'\n" for s in story['scenes']),encoding='utf-8')
    master=BUILD/'picture.mp4'
    ffmpeg(['-f','concat','-safe','0','-i',concat,'-c','copy',master],BUILD/'concat.log')
    # Time stretch each voice take, then pad/trim to the frame-aligned scene duration.
    joined=BUILD/'narration.wav'
    with sf.SoundFile(joined,'w',samplerate=24000,channels=1,subtype='PCM_16') as output:
        for entry in timeline:
            path=BUILD/'audio'/(entry['id']+'_paced.wav')
            ffmpeg(['-i',ROOT/audio[entry['id']]['wav'],'-af',f'atempo={tempo:.9f},apad,atrim=duration={entry["duration"]}',
                    '-ar','24000','-ac','1',path],BUILD/'pace.log')
            samples,rate=sf.read(path,dtype='float32');assert rate==24000
            output.write(samples)
    final=OUT/'Branch_Assist_Full_Demo.mp4'
    ffmpeg(['-i',master,'-i',joined,'-i',meta_path,'-i',OUT/'Branch_Assist_Demo.srt',
            '-map','0:v:0','-map','1:a:0','-map','3:s:0','-map_metadata','2','-map_chapters','2',
            '-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','128k',
            '-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata:s:a:0','language=eng',
            '-t',offset,'-movflags','+faststart',final],BUILD/'mux.log')
    manifest={'title':story['title'],'duration_seconds':round(offset,3),'resolution':[W,H],'fps':FPS,
              'scenes':len(timeline),'chapters':chapters,'narration':'Local Kokoro ONNX; synthetic af_heart voice',
              'narration_pacing_factor':round(tempo,6),'captions':'Burned in, embedded English, SRT and VTT; sentence-aligned timing',
              'source_capture':'Actual local application; no mocked or substituted responses',
              'editing':'Pauses may be shortened; final-frame holds support explanation. Model time remains visible.',
              'recorded_regressions':['B02','N03'],'source_code_shown':False,'pipeline_version':'2.0',
              'application_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'narrator_models':json.loads((ROOT/'models/narrator/manifest.json').read_text()),
              'bytes':final.stat().st_size,'sha256':sha256(final.read_bytes()).hexdigest()}
    (OUT/'production_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    template=(ROOT/'assets/demo_player.html').read_text(encoding='utf-8')
    player=template.replace('__CHAPTERS__',json.dumps(chapters,ensure_ascii=False)).replace('__SCENES__',json.dumps(timeline,ensure_ascii=False))
    (OUT/'Watch_Demo.html').write_bytes(player.encode('utf-8'))
    (OUT/'Branch_Assist_Transcript.txt').write_text('\n'.join(transcript),encoding='utf-8')
    coverage='''# Demonstration feature coverage

The main MP4 is a recorded, narrated walkthrough. Application scenes are genuine browser interactions. B02 and N03 are separately labelled saved regression examples. Explanatory graphics describe implemented design choices and proposed validation boundaries. Implementation source is not displayed.

| Time | Scene | Evidence type |
|---|---|---|
'''
    for scene in timeline:
        time=f"{int(scene['start']//60):02d}:{int(scene['start']%60):02d}"
        kind='Actual application capture' if scene['kind']=='browser' else 'Saved regression output' if scene['id'] in {'correction','fallback'} else 'Explanatory graphic'
        coverage+=f"| {time} | {scene['title']} | {kind} |\n"
    coverage+='\nCapture assertions, response outcomes and exports are retained in `capture_evidence.json`. Media checks are in `qa_report.json`. A timing/production manifest, captions, transcript and thumbnail accompany the video.\n'
    (OUT/'FEATURE_COVERAGE.md').write_text(coverage,encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':
    main()
