"""Generate local synthetic narration with sentence-aligned caption timing.

Uses a separately downloaded, pinned Kokoro ONNX artifact; no procedure text
is sent to a hosted TTS service. The voice is synthetic, not the candidate's.
"""
from pathlib import Path
from hashlib import sha256
import json
import math
import re

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'artifacts/video_build'
AUDIO = BUILD / 'audio'
AUDIO.mkdir(parents=True, exist_ok=True)
STORY = json.loads((ROOT/'demo/storyboard.json').read_text(encoding='utf-8'))
RATE = 24000


def main():
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(ROOT/'models/narrator/kokoro-v1.0.onnx'), sess_options=options,
                                  providers=['CPUExecutionProvider'])
    voice = Kokoro.from_session(session, str(ROOT/'models/narrator/voices-v1.0.bin'))
    timeline=[]
    offset=0.0
    for scene in STORY['scenes']:
        identity=sha256(json.dumps([scene['narration'],STORY['voice'],STORY['speed'],'sentence-v1']).encode()).hexdigest()
        record_path=AUDIO/(scene['id']+'.json')
        wav_path=AUDIO/(scene['id']+'.wav')
        cached=json.loads(record_path.read_text()) if record_path.exists() else {}
        if cached.get('identity')==identity and wav_path.exists():
            record=cached
        else:
            chunks=[np.zeros(round(RATE*.55),dtype=np.float32)]
            position=.55
            captions=[]
            for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z])',scene['narration']):
                samples, rate=voice.create(sentence,voice=STORY['voice'],speed=STORY['speed'],lang='en-us')
                assert rate==RATE and len(samples)>0
                duration=len(samples)/RATE
                captions.append({'start':round(position,4),'end':round(position+duration,4),'text':sentence})
                chunks.extend([samples,np.zeros(round(RATE*.18),dtype=np.float32)])
                position+=duration+.18
            chunks.append(np.zeros(round(RATE*.65),dtype=np.float32))
            samples=np.concatenate(chunks)
            # Frame-aligned lengths keep captions, chapters and concatenated media in sync.
            duration=math.ceil(len(samples)/RATE*30)/30
            samples=np.pad(samples,(0,round(duration*RATE)-len(samples)))
            sf.write(wav_path,samples,RATE,subtype='PCM_16')
            record={'identity':identity,'id':scene['id'],'duration':duration,'captions':captions,
                    'peak':float(np.max(np.abs(samples))),'rms':float(np.sqrt(np.mean(samples**2)))}
            record_path.write_text(json.dumps(record,indent=2),encoding='utf-8')
        record['start']=round(offset,4)
        record['wav']=str(wav_path.relative_to(ROOT))
        timeline.append(record)
        offset+=record['duration']
        (BUILD/'audio_timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
        print(scene['id'],round(record['duration'],1),'seconds; total',round(offset,1),flush=True)
    print('NARRATION COMPLETE',round(offset/60,2),'minutes',flush=True)


if __name__=='__main__':
    main()
