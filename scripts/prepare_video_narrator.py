"""Download and hash-check the separately used local synthetic narration model."""
from hashlib import sha256
from pathlib import Path
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models/narrator'
FILES={
    'kokoro-v1.0.onnx':('beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',325505369),
    'voices-v1.0.bin':('bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',28214398),
}


def main():
    OUT.mkdir(parents=True,exist_ok=True);records=[]
    for name,(digest,size) in FILES.items():
        target=OUT/name
        url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+name
        if not target.exists():
            temporary=target.with_suffix(target.suffix+'.part')
            request=urllib.request.Request(url,headers={'User-Agent':'BranchAssist-DemoBuild/1.0'})
            with urllib.request.urlopen(request,timeout=45) as response,temporary.open('wb') as destination:
                while data:=response.read(1024*1024):destination.write(data)
            assert temporary.stat().st_size==size and sha256(temporary.read_bytes()).hexdigest()==digest,name
            temporary.replace(target)
        assert target.stat().st_size==size and sha256(target.read_bytes()).hexdigest()==digest,name
        records.append({'name':name,'url':url,'bytes':size,'sha256':digest})
        print(name,'verified',flush=True)
    (OUT/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')


if __name__=='__main__':main()
