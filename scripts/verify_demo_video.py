"""Check finished media, timestamps, provenance, and actual captured outcomes."""
from pathlib import Path
from hashlib import sha256
import json
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo'
BUILD=ROOT/'artifacts/video_build'


def main():
    video=OUT/'Branch_Assist_Full_Demo.mp4'
    manifest=json.loads((OUT/'production_manifest.json').read_text(encoding='utf-8'))
    timeline=json.loads((OUT/'timeline.json').read_text(encoding='utf-8'))
    capture=json.loads((BUILD/'capture_manifest.json').read_text(encoding='utf-8'))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(video)]))
    vs=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    subtitles=next(s for s in probe['streams'] if s['codec_type']=='subtitle')
    duration=float(probe['format']['duration'])
    assert vs['codec_name']=='h264' and (vs['width'],vs['height'])==(1920,1080)
    assert audio['codec_name']=='aac' and subtitles['codec_name']=='mov_text'
    assert 12*60<=duration<=14*60,duration
    assert abs(float(vs['duration'])-float(audio['duration']))<.16
    assert len(probe['chapters'])==5
    assert abs(timeline[-1]['end']-duration)<.12
    for left,right in zip(timeline,timeline[1:]):assert abs(left['end']-right['start'])<.001
    assert manifest['sha256']==sha256(video.read_bytes()).hexdigest()
    assert not manifest['source_code_shown'] and manifest['recorded_regressions']==['B02','N03']
    assert capture['status']=='passed' and not capture['client_errors']
    assert capture['complete_export_verified'] and capture['mobile_verified'] and capture['independent_session_starts_empty']
    expected={'coin':'answered','coin_followup':'answered','scope_conflict':'clarify','clarification':'clarify',
              'unsupported':'unsupported','unknown':'unsupported','instruction_guard':'refused'}
    for key,status in expected.items():assert capture['responses'][key]['status']==status
    assert '$5,250' in capture['responses']['coin']['answer']
    assert 'single control' in capture['responses']['coin_followup']['answer']
    assert capture['responses']['bond_exception']['status']=='evidence_only'
    assert capture['responses']['bond_exception']['metrics']['repair_attempted']
    srt=(OUT/'Branch_Assist_Demo.srt').read_text(encoding='utf-8')
    bounds=re.findall(r'(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})',srt)
    previous=0
    for b in bounds:
        nums=list(map(int,b));start=nums[0]*3600+nums[1]*60+nums[2]+nums[3]/1000;end=nums[4]*3600+nums[5]*60+nums[6]+nums[7]/1000
        assert previous<=start<end<=duration+.02
        previous=end
    assert len(bounds)>150
    print('Structure, source outcomes, captions and chapters passed; decoding entire video...',flush=True)
    decoded=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],
                           capture_output=True,text=True)
    assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
    print('Full decode passed; measuring narration level...',flush=True)
    loudness=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-vn','-sn','-af','ebur128=peak=true','-f','null','-'],
                            capture_output=True,text=True,check=True)
    tail=loudness.stderr[loudness.stderr.rfind('Summary:'):]
    (BUILD/'audio_loudness.log').write_text(tail,encoding='utf-8')
    integrated=float(re.search(r'I:\s+(-?[\d.]+) LUFS',tail).group(1))
    peak=float(re.search(r'Peak:\s+(-?[\d.]+) dBFS',tail).group(1))
    assert -18<=integrated<=-14,integrated
    assert peak<=-.9,peak
    print('Audio level passed; extracting a visual contact sheet...',flush=True)
    sheet=Image.new('RGB',(2400,math_rows(len(timeline))*292),'#f9f7f6')
    draw=ImageDraw.Draw(sheet);face=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',15)
    qc=BUILD/'qc';qc.mkdir(exist_ok=True)
    for index,scene in enumerate(timeline):
        path=qc/(scene['id']+'.png')
        seek=scene['start']+scene['duration']*.76
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(seek),'-i',str(video),
                        '-frames:v','1','-update','1',str(path)],check=True,capture_output=True)
        image=Image.open(path).convert('RGB').resize((480,270),Image.Resampling.LANCZOS)
        x=(index%5)*480;y=(index//5)*292;sheet.paste(image,(x,y))
        draw.text((x+5,y+271),f"{index+1:02d} {scene['id']}",font=face,fill='#3b3331')
    sheet.save(OUT/'Contact_Sheet.jpg',quality=90)
    # Retain genuine response records, without raw multi-minute capture intermediates.
    evidence={k:v for k,v in capture.items() if k not in {'raw_video','segments','downloads'}}
    evidence['segments']=[{'id':s['id'],'label':s['label'],'passed':s['passed']} for s in capture['segments']]
    (OUT/'capture_evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
    report={'status':'passed','duration_seconds':duration,'resolution':[vs['width'],vs['height']],
            'video_codec':vs['codec_name'],'audio_codec':audio['codec_name'],'embedded_captions':True,
            'chapter_count':len(probe['chapters']),'scene_count':len(timeline),'caption_cues':len(bounds),
            'full_media_decode_passed':True,'caption_timing_passed':True,'audio_video_duration_delta':round(abs(float(vs['duration'])-float(audio['duration'])),5),
            'integrated_loudness_lufs':integrated,'true_peak_dbfs':peak,'capture_assertions_passed':True,
            'client_errors':capture['client_errors'],'source_code_shown':False,'video_sha256':manifest['sha256'],
            'note':'Automated media checks and visual contact sheet support review; no independent SME validation is implied.'}
    (OUT/'qa_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


def math_rows(n):return (n+4)//5


if __name__=='__main__':main()
