"""Create the silent, UI-only cut from original browser footage.

No audio or narrated-video frames enter this edit. A compact heading and
one-line tag sit above the full UI; corner highlights appear on genuine final
capture frames. No architecture, evaluation graphics, or presentation slides.
"""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo/tool-only'
BUILD=ROOT/'artifacts/video_build/tool-only'
FRAMES=BUILD/'frames';ENCODED=BUILD/'encoded'
for directory in [OUT,FRAMES,ENCODED]:directory.mkdir(exist_ok=True,parents=True)
W,H,FPS=1920,1080,30
APP=(98,110,1724,970)
INK='#3b3331';RED='#d71e28';GOLD='#ffcd41';WARM='#f9f7f6'


def face(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)


def heading(scene,index,total):
    im=Image.new('RGB',(W,H),WARM);d=ImageDraw.Draw(im)
    d.ellipse((18,20,58,60),fill=GOLD)
    number=f'{index:02d}';f=face(19,True)
    d.text((38-d.textlength(number,font=f)/2,25),number,font=f,fill=INK)
    d.text((76,11),scene['title'],font=face(31,True),fill=INK)
    note=scene['note'];f=face(22)
    assert d.textlength(note,font=f)<=1480,('Note too long',scene['capture'])
    d.text((76,64),note,font=f,fill='#6b625c')
    d.text((1630,7),f'TOOL DEMO  ·  {index:02d} / {total:02d}',font=face(15,True),fill=INK)
    tag=scene['tag'];f=face(16,True);width=d.textlength(tag,font=f)+26
    x=1889-width;d.rounded_rectangle((x,34,1889,65),radius=15,fill=RED)
    d.text((x+13,38),tag,font=f,fill='white')
    d.text((1713,78),'Pauses shortened',font=face(14),fill='#746c69')
    d.line((98,105,1822,105),fill='#e2dbd7',width=3)
    d.line((98,105,98+round(1724*index/total),105),fill=RED,width=3)
    return im


def highlights(scene):
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    for x,y,width,height in scene['highlights']:
        assert x>=0 and y>=0 and x+width<=1536 and y+height<=864,scene['capture']
        x1=APP[0]+x*APP[2]/1536;y1=APP[1]+y*APP[3]/864
        x2=x1+width*APP[2]/1536;y2=y1+height*APP[3]/864
        k=min(24,(x2-x1)/4,(y2-y1)/3)
        for points in [[(x1,y1+k),(x1,y1),(x1+k,y1)],[(x2-k,y1),(x2,y1),(x2,y1+k)],
                       [(x1,y2-k),(x1,y2),(x1+k,y2)],[(x2-k,y2),(x2,y2),(x2,y2-k)]]:
            d.line(points,fill=(59,51,49,115),width=9,joint='curve')
            d.line(points,fill=(255,205,65,255),width=5,joint='curve')
    return im


def run(args,log):
    with log.open('w',encoding='utf-8') as output:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y',*map(str,args)],
                       cwd=ROOT,stdout=output,stderr=output,check=True)


def mmss(t):return f'{int(t//60):02d}:{int(t%60):02d}'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--frames-only',action='store_true')
    args=parser.parse_args()
    story=json.loads((OUT/'storyboard.json').read_text(encoding='utf-8'))
    path=BUILD/'capture_manifest.json'
    if args.frames_only and not path.exists():path=ROOT/'artifacts/video_build/capture_manifest.json'
    capture=json.loads(path.read_text(encoding='utf-8'));assert capture['status']=='passed'
    if not args.frames_only:assert capture['currency_display_verified']
    shots={s['id']:s for s in capture['segments']}
    timeline=[];chapters=[];offset=0
    for index,scene in enumerate(story['scenes'],1):
        shot=shots[scene['capture']];assert shot['passed']
        header=heading(scene,index,len(story['scenes']));marker=highlights(scene)
        header_path=FRAMES/(scene['capture']+'_header.png');header.save(header_path)
        marker_path=FRAMES/(scene['capture']+'_highlights.png');marker.save(marker_path)
        still=ROOT/shot['screenshot']
        preview=header.copy();preview.paste(Image.open(still).convert('RGB').resize(APP[2:],Image.Resampling.LANCZOS),APP[:2])
        preview=Image.alpha_composite(preview.convert('RGBA'),marker).convert('RGB')
        preview.save(FRAMES/(scene['capture']+'_preview.png'))
        if index==1:preview.save(OUT/'Cover.png')
        if not chapters or chapters[-1]['title']!=scene['chapter']:
            chapters.append({'start':offset,'title':scene['chapter']})
        duration=scene['duration']
        timeline.append({'id':scene['capture'],'title':scene['title'],'tag':scene['tag'],'note':scene['note'],
                         'start':offset,'end':offset+duration,'duration':duration,'kind':'actual_app_capture'})
        offset+=duration
        if args.frames_only:continue
        raw=ROOT/shot.get('raw_video',capture['raw_video'])
        length=max(.25,shot['end']-shot['start']-.12)
        # Keep the initial interaction and final UI movement at normal speed.
        # Shorten the intervening processing pause, then hold the real screenshot.
        motion=min(length,duration-4.0)
        hold=duration-motion
        graph=f'[0:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,scale={APP[2]}:{APP[3]},setsar=1,format=yuv420p[raw];'
        if length>motion+.12:
            head=min(3.0,motion*.25);tail=min(3.0,motion*.25)
            middle=length-head-tail;middle_out=motion-head-tail
            ratio=middle_out/middle
            graph+=f'[raw]split=3[a][b][c];[a]trim=duration={head},setpts=PTS-STARTPTS[head];'
            graph+=f'[b]trim=start={head}:end={length-tail},setpts={ratio:.9f}*(PTS-STARTPTS),fps={FPS}[middle];'
            graph+=f'[c]trim=start={length-tail},setpts=PTS-STARTPTS[tail];'
            graph+='[head][middle][tail]concat=n=3:v=1:a=0[moving];'
        else:graph+='[raw]null[moving];'
        graph+=f'[1:v]scale={APP[2]}:{APP[3]},setsar=1,format=yuv420p,trim=duration={hold},setpts=PTS-STARTPTS[still];'
        graph+=f'[moving][still]concat=n=2:v=1:a=0,fps={FPS},tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration}[screen];'
        graph+=f'[2:v][screen]overlay={APP[0]}:{APP[1]}:shortest=1[base];'
        graph+=f"[base][3:v]overlay=0:0:enable='between(t,{motion+.25:.4f},{duration-.2:.4f})'[v]"
        target=ENCODED/(scene['capture']+'.mp4')
        identity=sha256(json.dumps([scene,str(raw),sha256(still.read_bytes()).hexdigest(),
                                   sha256(header_path.read_bytes()).hexdigest(),'silent-layout-v1']).encode()).hexdigest()
        stamp=target.with_suffix('.sha256')
        if target.exists() and stamp.exists() and stamp.read_text()==identity:
            print('CACHED',scene['capture'],flush=True);continue
        run(['-ss',max(0,shot['start']),'-t',length,'-i',raw,
             '-loop','1','-framerate',FPS,'-i',still,
             '-loop','1','-framerate',FPS,'-i',header_path,
             '-loop','1','-framerate',FPS,'-i',marker_path,
             '-filter_complex',graph,'-map','[v]','-an','-sn','-dn','-t',duration,'-r',FPS,
             '-c:v','libx264','-preset','veryfast','-crf','22','-threads','4','-pix_fmt','yuv420p',
             '-movflags','+faststart',target],ENCODED/(scene['capture']+'.log'))
        stamp.write_text(identity)
        print('ENCODED',scene['capture'],duration,'seconds',flush=True)
    (OUT/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
    if args.frames_only:return
    metadata=';FFMETADATA1\ntitle=Branch Assist - Silent Tool Demo\ncomment=Actual UI, tags and highlights; no audio; pauses shortened; interview prototype.\n'
    for i,c in enumerate(chapters):
        end=chapters[i+1]['start'] if i+1<len(chapters) else offset
        metadata+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={c['start']*1000}\nEND={end*1000}\ntitle={c['title']}\n"
    meta_path=BUILD/'chapters.ffmetadata';meta_path.write_text(metadata,encoding='utf-8')
    concat=BUILD/'concat.txt'
    concat.write_text(''.join("file '"+(ENCODED/(s['capture']+'.mp4')).as_posix()+"'\n" for s in story['scenes']),encoding='utf-8')
    final=OUT/'Branch_Assist_Tool_Demo.mp4'
    run(['-f','concat','-safe','0','-i',concat,'-i',meta_path,'-map','0:v:0','-map_metadata','1','-map_chapters','1',
         '-c:v','copy','-an','-sn','-dn','-movflags','+faststart',final],BUILD/'mux.log')
    template=(ROOT/'assets/tool_demo_player.html').read_text(encoding='utf-8')
    player=template.replace('__CHAPTERS__',json.dumps(chapters,ensure_ascii=False)).replace('__SCENES__',json.dumps(timeline,ensure_ascii=False))
    (OUT/'Watch_Tool_Demo.html').write_bytes(player.encode('utf-8'))
    guide='# Silent tool walkthrough — scenes and on-screen tags\n\nOnly actual application capture is shown. There is no audio track, narration, slide deck or presentation graphic. Processing pauses may be shortened; real final capture frames are held for reading.\n\n| Time | Action | On-screen information |\n|---|---|---|\n'
    for row in timeline:guide+=f"| {mmss(row['start'])} | {row['title']} | {row['note']} |\n"
    (OUT/'SCENE_GUIDE.md').write_text(guide,encoding='utf-8')
    (OUT/'chapters.txt').write_text('\n'.join(mmss(c['start'])+' '+c['title'] for c in chapters)+'\n',encoding='utf-8')
    manifest={'title':story['title'],'duration_seconds':offset,'resolution':[W,H],'fps':FPS,
              'scene_count':len(timeline),'chapters':chapters,'audio_streams':0,'narration':False,
              'presentation_slides':False,'browser_only':True,'on_screen_information':'Short action tags, one-line context, corner highlights',
              'editing':'Initial/final motion preserved; some processing pauses shortened; real final UI frames held for reading.',
              'currency_display_verified':capture['currency_display_verified'],
              'interface_sha256':capture['interface_sha256'],'capture_manifest_sha256':sha256(path.read_bytes()).hexdigest(),
              'source_code_shown':False,'bytes':final.stat().st_size,'sha256':sha256(final.read_bytes()).hexdigest()}
    (OUT/'production_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':main()
