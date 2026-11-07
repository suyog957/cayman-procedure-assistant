"""Read-only checks of the preserved final copy; never writes into demo/final."""
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'demo/final'
OUT=ROOT/'artifacts/final_review'


def main():
    approved=json.loads((DIRECTORY/'APPROVED_FINAL.json').read_text(encoding='utf-8'))
    assert approved['sha256']=='48bc8f2c63d31c7efd5080606f4c2b2165c873c0c31e79b9cb6b318afe0d2c0b'
    for name,digest in approved['files'].items():
        path=(DIRECTORY/name).resolve();path.relative_to(DIRECTORY.resolve())
        assert sha256(path.read_bytes()).hexdigest()==digest,name
    video=DIRECTORY/approved['approved_video']
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]))
    stream=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (stream['width'],stream['height'])==(2560,1440)
    assert not any(s['codec_type']=='audio' for s in probe['streams'])
    assert abs(float(probe['format']['duration'])-approved['duration_seconds'])<.1
    url='http://127.0.0.1:8502/final/Watch_Final_Demo.html'
    media='http://127.0.0.1:8502/final/'+approved['approved_video']
    with urllib.request.urlopen(urllib.request.Request(media,headers={'Range':'bytes=0-1023'})) as r:
        assert r.status==206 and len(r.read())==1024
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1536,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url,wait_until='networkidle',timeout=60000)
        page.wait_for_function('document.querySelector("video").readyState>=2',timeout=30000)
        assert 'Branch_Assist_Final_Approved.mp4' in page.locator('video').evaluate('(v)=>v.currentSrc')
        page.get_by_role('button',name='Play video',exact=True).click()
        page.wait_for_function('document.querySelector("video").currentTime>.25',timeout=30000)
        page.get_by_role('button',name='Pause video',exact=True).click()
        assert page.locator('#chapters button').count()==7
        page.locator('#chapters button').last.click()
        page.wait_for_function('document.querySelector("video").currentTime>521.2',timeout=30000)
        assert not page.locator('video').evaluate('(v)=>v.error')
        assert not errors
        browser.close()
    OUT.mkdir(exist_ok=True,parents=True)
    report={'status':'passed','approved_files_verified':len(approved['files']),'approved_sha256':approved['sha256'],
            'video_unchanged':True,'silent_1440p':True,'duration_seconds':float(probe['format']['duration']),
            'preserved_copy_browser_playback_and_chapter_seek':True,'byte_ranges':True,'client_errors':errors,'url':url}
    (OUT/'approved_video_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
