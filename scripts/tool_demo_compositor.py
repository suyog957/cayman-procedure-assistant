"""1440p silent workflow edit with high-density PNG footage and reading pauses."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import argparse
import json
import math
import subprocess
import textwrap

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/tool-only'
BUILD=ROOT/'artifacts/video_build/tool-only/hd'
FRAMES=BUILD/'composition';ENCODED=BUILD/'encoded'
for p in [OUT,FRAMES,ENCODED]:p.mkdir(exist_ok=True,parents=True)
W,H,FPS=2560,1440,30
APP=(296,76,1968,1107)
CARD=(160,1200,2240,154)
RED='#d71e28';GOLD='#ffcd41';INK='#3b3331'
CAMERA_FRAMES=36


def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)


def lines(draw,value,face,width):
    output=[];row=''
    for word in value.split():
        candidate=(row+' '+word).strip()
        if row and draw.textlength(candidate,font=face)>width:output.append(row);row=word
        else:row=candidate
    if row:output.append(row)
    return output


def focus_region(boxes):
    x1=min(b[0] for b in boxes);y1=min(b[1] for b in boxes)
    x2=max(b[0]+b[2] for b in boxes);y2=max(b[1]+b[3] for b in boxes)
    width=min(1536,math.ceil(max(1200,x2-x1+48,(y2-y1+60)*16/9)/16)*16)
    if width>=1488:return [0,0,1536,864]
    height=width*9/16
    # Align the camera to the actual column edge so text in the conversation
    # is not cut in half when the evidence pane receives the focus.
    x=288 if width==1200 and x1>=288 and x2<=1488 else max(0,min(1536-width,(x1+x2-width)/2))
    y=min(864-height,max(76,y2+12-height))
    assert all(x-1<=b[0] and b[0]+b[2]<=x+width+1 and y-1<=b[1] and b[1]+b[3]<=y+height+1 for b in boxes)
    return [x,y,width,height]


def backdrop(scene,index,total,wait_cut):
    image=Image.new('RGB',(W,H));draw=ImageDraw.Draw(image)
    for y in range(H):
        t=y/(H-1);color=tuple(round(a+(b-a)*t) for a,b in zip((238,232,227),(250,248,246)))
        draw.line((0,y,W,y),fill=color)
    shadow=Image.new('RGBA',(W,H),(0,0,0,0));s=ImageDraw.Draw(shadow)
    x,y,w,h=APP;s.rounded_rectangle((x,y+12,x+w,y+h+12),radius=20,fill=(45,36,31,45))
    shadow=shadow.filter(ImageFilter.GaussianBlur(15))
    image=Image.alpha_composite(image.convert('RGBA'),shadow);draw=ImageDraw.Draw(image)
    draw.ellipse((208,13,252,57),fill=GOLD)
    number=f'{index:02d}';face=font(21,True)
    draw.text((230-draw.textlength(number,font=face)/2,19),number,font=face,fill=INK)
    draw.text((296,13),scene['title'],font=font(36,True),fill=INK)
    draw.text((2320,17),f'{index:02d} / {total:02d}',font=font(20,True),fill=INK)
    draw.text((2297,44),'PROTOTYPE',font=font(18,True),fill='#746c69')
    draw.line((APP[0],66,APP[0]+APP[2],66),fill='#d8cec7',width=3)
    draw.line((APP[0],66,APP[0]+round(APP[2]*index/total),66),fill=RED,width=3)
    cx,cy,cw,ch=CARD
    draw.rounded_rectangle((cx,cy,cx+cw,cy+ch),radius=19,fill='#312a27',outline='#51433b',width=1)
    draw.rounded_rectangle((cx+17,cy+20,cx+21,cy+ch-20),radius=2,fill=GOLD)
    draw.text((cx+40,cy+10),scene['tag'],font=font(20,True),fill=GOLD)
    meta='Idle pause shortened  ·  actual UI' if wait_cut else 'Recorded UI  ·  silent'
    face=font(16);draw.text((cx+cw-28-draw.textlength(meta,font=face),cy+13),meta,font=face,fill='#d1c7c0')
    rows=lines(draw,scene['description'],font(40),cw-80)
    assert len(rows)<=2,('Description exceeds two lines',scene['capture'])
    for n,row in enumerate(rows):draw.text((cx+40,cy+(43 if len(rows)==2 else 56)+n*48),row,font=font(40),fill='#fffdfb')
    return image.convert('RGB'),len(rows)


def marker(scene,roi):
    image=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(image)
    rx,ry,rw,rh=roi
    for x,y,width,height in scene['highlights']:
        x1=APP[0]+(x-rx)*APP[2]/rw;y1=APP[1]+(y-ry)*APP[3]/rh
        x2=x1+width*APP[2]/rw;y2=y1+height*APP[3]/rh
        k=min(24,(x2-x1)/4,(y2-y1)/3)
        for points in [[(x1,y1+k),(x1,y1),(x1+k,y1)],[(x2-k,y1),(x2,y1),(x2,y1+k)],
                       [(x1,y2-k),(x1,y2),(x1+k,y2)],[(x2-k,y2),(x2,y2),(x2,y2-k)]]:
            d.line(points,fill=(255,255,255,210),width=7,joint='curve')
            d.line(points,fill=(226,169,28,255),width=3,joint='curve')
    return image


def crop(source,roi):
    x,y,w,h=roi
    return source.resize(APP[2:],Image.Resampling.LANCZOS,box=(x*2,y*2,(x+w)*2,(y+h)*2))


def round_frame(value):return math.ceil(value*FPS-1e-7)/FPS


def stable_tail(shot):
    # Deduplicate only an unchanged ending, then add a deliberate reading hold
    # later. The fixed chat-input caret is excluded from this comparison.
    final=Image.open(ROOT/shot['screenshot']).convert('RGB').crop((0,0,3072,1520)).resize((192,95),Image.Resampling.BOX)
    stable_start=shot['end']
    for frame in reversed(shot['frames']):
        if shot['end']-frame['time']>2.5:break
        sample=Image.open(ROOT/frame['file']).convert('RGB').crop((0,0,3072,1520)).resize((192,95),Image.Resampling.BOX)
        if ImageChops.difference(final,sample).getbbox():break
        stable_start=frame['time']
    return max(0,min(2.1,shot['end']-stable_start-.4))


def motion_sequence(shot,folder):
    start,end=shot['start'],shot['end'];cut_start=cut_end=0
    if shot.get('wait_start') is not None and shot.get('wait_end') is not None:
        a=shot['wait_start']+2.5;b=shot['wait_end']-.6
        if b>a+1.0:cut_start,cut_end=a,b
    removed=cut_end-cut_start
    tail_removed=stable_tail(shot)
    end-=tail_removed
    def mapped(t):return t-start-max(0,min(t,cut_end)-cut_start) if removed else t-start
    frames=[]
    for frame in shot['frames']:
        t=frame['time']
        if cut_start<t<cut_end or t>end:continue
        frames.append((max(0,mapped(t)),ROOT/frame['file']))
    frames.sort(key=lambda row:row[0])
    assert frames
    if frames[0][0]>.001:frames.insert(0,(0,frames[0][1]))
    motion=round_frame(end-start-removed)
    frames.append((motion,ROOT/shot['screenshot']))
    entries=[]
    for (t,path),(next_t,_) in zip(frames,frames[1:]):
        delta=next_t-t
        if delta<=0:continue
        entries.extend([f"file '{path.as_posix()}'",f'duration {delta:.8f}'])
    entries.extend([f"file '{frames[-1][1].as_posix()}'",'duration 0.10000000',f"file '{frames[-1][1].as_posix()}'"])
    path=folder/'motion.ffconcat';path.write_text('\n'.join(entries)+'\n',encoding='utf-8')
    return path,motion,removed,tail_removed


def run(arguments,path):
    with path.open('w',encoding='utf-8') as log:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y',*map(str,arguments)],
                       cwd=ROOT,stdout=log,stderr=log,check=True)


def encode_scene(arguments,log_path,cache,identity,name,duration,reading):
    run(arguments,log_path)
    cache.write_text(identity)
    print('ENCODED',name,round(duration,2),'seconds; reading hold',round(reading,2),flush=True)


def stamp(t,srt=False):
    value=round(t*1000);hour,value=divmod(value,3600000);minute,value=divmod(value,60000);second,ms=divmod(value,1000)
    return f'{hour:02d}:{minute:02d}:{second:02d}'+(',' if srt else '.')+f'{ms:03d}'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--frames-only',action='store_true')
    parser.add_argument('--workers',type=int,choices=(1,2),default=2,help='Concurrent independent scene encodes.')
    args=parser.parse_args()
    story=json.loads((OUT/'storyboard.json').read_text(encoding='utf-8'))
    capture_path=BUILD/'capture_manifest.json';capture=json.loads(capture_path.read_text(encoding='utf-8'))
    assert capture['status']=='passed' and capture['pixel_dimensions']==[3072,1728]
    assert capture['currency_display_verified'] and capture['responses']['bond_exception']['status']=='evidence_only'
    shots={s['id']:s for s in capture['segments']}
    report_boxes=capture['report_button_boxes']
    for scene in story['scenes']:
        if scene['capture']=='report_download':scene['highlights']=report_boxes
    (OUT/'storyboard.json').write_text(json.dumps(story,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    mask=Image.new('L',APP[2:],0);ImageDraw.Draw(mask).rounded_rectangle((0,0,APP[2]-1,APP[3]-1),radius=18,fill=255)
    mask_path=FRAMES/'window_mask.png';mask.save(mask_path)
    timeline=[];chapters=[];offset=0;captions=[]
    encoder=ThreadPoolExecutor(max_workers=args.workers);jobs=[]
    for index,scene in enumerate(story['scenes'],1):
        shot=shots[scene['capture']];assert shot['passed']
        folder=FRAMES/scene['capture'];folder.mkdir(exist_ok=True)
        sequence,motion,removed,tail_removed=motion_sequence(shot,folder)
        roi=[0,0,1536,864] if scene['capture']=='welcome' else focus_region(scene['highlights'])
        zoom=CAMERA_FRAMES/FPS
        duration=round_frame(max(scene['duration'],motion+zoom+scene['min_reading_seconds']))
        reading=round(duration-motion-zoom,8)
        background,row_count=backdrop(scene,index,len(story['scenes']),removed+tail_removed>0)
        background_path=folder/'background.png';background.save(background_path)
        source=Image.open(ROOT/shot['screenshot']).convert('RGB');assert source.size==(3072,1728)
        focused=crop(source,roi);focused_path=folder/'focused.png';focused.save(focused_path)
        corners=marker(scene,roi);marker_path=folder/'marker.png';corners.save(marker_path)
        reference_path=folder/'reference.png'
        previous_reference=sha256(reference_path.read_bytes()).hexdigest() if reference_path.exists() else None
        preview=background.copy();preview.paste(focused,APP[:2],mask)
        preview=Image.alpha_composite(preview.convert('RGBA'),corners).convert('RGB')
        preview.save(reference_path)
        reference_hash=sha256(reference_path.read_bytes()).hexdigest()
        if index==1:preview.save(OUT/'Cover.png')
        if not chapters or chapters[-1]['title']!=scene['chapter']:chapters.append({'start':round(offset,5),'title':scene['chapter']})
        row={'id':scene['capture'],'title':scene['title'],'tag':scene['tag'],'description':scene['description'],
             'start':round(offset,5),'end':round(offset+duration,5),'duration':duration,'kind':'actual_app_capture',
             'motion_seconds':motion,'camera_transition_seconds':zoom,'reading_seconds':reading,
             'minimum_reading_seconds':scene['min_reading_seconds'],'wait_removed_seconds':round(removed,5),
             'unchanged_tail_removed_seconds':round(tail_removed,5),
             'focus_css_region':roi,'description_lines':row_count,'description_font_pixels':40,
             'description_characters_per_second':round(len(scene['description'])/duration,3)}
        timeline.append(row);captions.append({'start':offset,'end':offset+duration,'text':scene['description']});offset+=duration
        if args.frames_only:continue
        camera_identity=sha256(json.dumps([roi,sha256((ROOT/shot['screenshot']).read_bytes()).hexdigest(),'camera-v1']).encode()).hexdigest()
        cache_path=folder/'camera.sha256';cached=cache_path.exists() and cache_path.read_text()==camera_identity
        for n in range(CAMERA_FRAMES):
            path=folder/f'camera_{n:03d}.png'
            if cached and path.exists():continue
            progress=n/(CAMERA_FRAMES-1);ease=progress*progress*(3-2*progress)
            view=[roi[0]*ease,roi[1]*ease,1536+(roi[2]-1536)*ease,864+(roi[3]-864)*ease]
            crop(source,view).save(path)
        cache_path.write_text(camera_identity)
        target=ENCODED/(scene['capture']+'.mp4')
        identity_inputs=[row,sha256(background_path.read_bytes()).hexdigest(),
                         sha256((ROOT/shot['screenshot']).read_bytes()).hexdigest(),
                         sha256(sequence.read_bytes()).hexdigest(),'1440p-png-v4-crf15-fast']
        previous_identity=sha256(json.dumps(identity_inputs).encode()).hexdigest()
        identity=sha256(json.dumps(identity_inputs+[reference_hash]).encode()).hexdigest()
        cache=target.with_suffix('.sha256')
        cached_identity=cache.read_text() if cache.exists() else None
        if target.exists() and (cached_identity==identity or
            cached_identity==previous_identity and previous_reference==reference_hash):
            cache.write_text(identity)
            print('CACHED',scene['capture'],flush=True);continue
        graph=f'[0:v]scale={APP[2]}:{APP[3]}:flags=lanczos,fps={FPS},settb=1/{FPS},setsar=1,format=rgba,trim=duration={motion},setpts=PTS-STARTPTS[m];'
        graph+=f'[1:v]fps={FPS},settb=1/{FPS},setsar=1,format=rgba,setpts=PTS-STARTPTS[z];'
        graph+='[m][z]concat=n=2:v=1:a=0,format=rgba[screen];'
        graph+='[screen][3:v]alphamerge[window];'
        graph+=f'[2:v][window]overlay={APP[0]}:{APP[1]}:shortest=1,trim=duration={motion+zoom},setpts=PTS-STARTPTS[picture];'
        graph+=f'[4:v]fps={FPS},settb=1/{FPS},setsar=1,format=rgba,trim=duration={reading},setpts=PTS-STARTPTS[s];'
        # The reading hold is a lossless, already-composited reference frame.
        # Reusing it avoids recomputing masks and overlays on unchanged pixels.
        graph+=f'[picture][s]concat=n=2:v=1:a=0,fps={FPS},tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration}[rgb];'
        graph+='[rgb]scale=iw:ih:out_color_matrix=bt709,format=yuv420p[v]'
        arguments=['-threads','1','-f','concat','-safe','0','-i',sequence,
             '-threads','1','-framerate',FPS,'-start_number','0','-i',folder/'camera_%03d.png',
             '-threads','1','-loop','1','-framerate',FPS,'-i',background_path,
             '-threads','1','-loop','1','-framerate',FPS,'-i',mask_path,
             '-threads','1','-loop','1','-framerate',FPS,'-i',folder/'reference.png',
             '-filter_complex_threads','2','-filter_complex',graph,'-map','[v]','-an','-sn','-dn',
             '-t',duration,'-r',FPS,'-c:v','libx264','-preset','fast','-crf','15','-threads','4',
             '-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
             '-movflags','+faststart','-progress',folder/'progress.txt','-stats_period','1',target]
        jobs.append(encoder.submit(encode_scene,arguments,folder/'encode.log',cache,identity,
                                   scene['capture'],duration,reading))
    try:
        for job in jobs:job.result()
    finally:
        encoder.shutdown(wait=True,cancel_futures=True)
    (OUT/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
    if args.frames_only:return
    meta=';FFMETADATA1\ntitle=Branch Assist - Readable Silent Tool Demo\ncomment=Double-density PNG app capture; bottom descriptions; normal-speed actions; idle waits may be cut; silent.\n'
    for i,c in enumerate(chapters):
        end=chapters[i+1]['start'] if i+1<len(chapters) else offset
        meta+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['start']*1000)}\nEND={round(end*1000)}\ntitle={c['title']}\n"
    metadata=BUILD/'chapters.ffmetadata';metadata.write_text(meta,encoding='utf-8')
    concat=BUILD/'concat.txt';concat.write_text(''.join("file '"+(ENCODED/(s['capture']+'.mp4')).as_posix()+"'\n" for s in story['scenes']),encoding='utf-8')
    final=OUT/'Branch_Assist_Tool_Demo.mp4'
    run(['-f','concat','-safe','0','-i',concat,'-i',metadata,'-map','0:v:0','-map_metadata','1','-map_chapters','1',
         '-c:v','copy','-an','-sn','-dn','-movflags','+faststart',final],BUILD/'mux.log')
    digest=sha256(final.read_bytes()).hexdigest()
    template=(ROOT/'assets/tool_demo_player.html').read_text(encoding='utf-8')
    player=template.replace('__CHAPTERS__',json.dumps(chapters,ensure_ascii=False)).replace('__SCENES__',json.dumps(timeline,ensure_ascii=False)).replace('__VIDEO_VERSION__',digest[:12])
    (OUT/'Watch_Tool_Demo.html').write_bytes(player.encode('utf-8'))
    srt=''.join(f"{i}\n{stamp(c['start'],True)} --> {stamp(c['end'],True)}\n"+'\n'.join(textwrap.wrap(c['text'],width=105))+'\n\n' for i,c in enumerate(captions,1))
    (OUT/'Descriptions.srt').write_text(srt.rstrip()+'\n',encoding='utf-8')
    vtt='WEBVTT\n\n'+''.join(f"{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}\n\n" for c in captions)
    (OUT/'Descriptions.vtt').write_text(vtt.rstrip()+'\n',encoding='utf-8')
    guide='# Silent tool walkthrough — readable edition\n\nActual UI only, with double-density lossless PNG capture. Descriptions remain in a large bottom panel; focus zooms and normal-speed interactions are followed by deliberate reading holds. Only idle processing waits may be cut. No audio, narration or slides.\n\n| Time | Step | Bottom description | Reading hold |\n|---|---|---|---|\n'
    for row in timeline:guide+=f"| {int(row['start']//60):02d}:{int(row['start']%60):02d} | {row['title']} | {row['description']} | {row['reading_seconds']:.1f}s |\n"
    (OUT/'SCENE_GUIDE.md').write_text(guide,encoding='utf-8')
    (OUT/'chapters.txt').write_text('\n'.join(f"{int(c['start']//60):02d}:{int(c['start']%60):02d} {c['title']}" for c in chapters)+'\n',encoding='utf-8')
    manifest={'title':story['title'],'layout_version':'2.0','duration_seconds':round(offset,5),'resolution':[W,H],'fps':FPS,
              'scene_count':len(timeline),'chapters':chapters,'audio_streams':0,'narration':False,'presentation_slides':False,
              'browser_only':True,'capture_format':'lossless PNG','capture_pixel_dimensions':[3072,1728],
              'capture_device_scale_factor':2,'capture_frames':capture['total_png_frames'],
              'encoding':'H.264 CRF 15 fast; Lanczos resampling; BT.709; yuv420p',
              'description_position':'dedicated bottom panel outside the UI','description_font_pixels':40,
              'description_max_lines':2,'player_control_safe_bottom_pixels':86,
              'min_reading_hold_seconds':round(min(r['reading_seconds'] for r in timeline),3),
              'max_description_characters_per_second':max(r['description_characters_per_second'] for r in timeline),
              'interaction_speed':1.0,'idle_waits_removed_seconds':round(sum(r['wait_removed_seconds'] for r in timeline),3),
              'unchanged_tails_removed_seconds':round(sum(r['unchanged_tail_removed_seconds'] for r in timeline),3),
              'app_frame_pixels':list(APP),'description_panel_pixels':list(CARD),
              'editing':'Normal-speed interaction PNGs; idle processing waits and unchanged tails may be cut; 1.2s eased focus zoom; unhurried reading hold.',
              'currency_display_verified':capture['currency_display_verified'],'interface_sha256':capture['interface_sha256'],
              'capture_manifest_sha256':sha256(capture_path.read_bytes()).hexdigest(),'source_code_shown':False,
              'bytes':final.stat().st_size,'sha256':digest}
    (OUT/'production_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':main()
