"""Refresh real UI footage affected by the currency display fix.

The original narrated capture remains intact. This separate manifest updates
only the silent cut's savings-bond, review, and export interactions.
"""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json
import re
import time

from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'artifacts/video_build/tool-only'
CAPTURE=BUILD/'capture'
CAPTURE.mkdir(parents=True,exist_ok=True)


def main():
    report=deepcopy(json.loads((ROOT/'artifacts/video_build/capture_manifest.json').read_text(encoding='utf-8')))
    report['status']='recording'
    report['currency_rendering']='Dollar signs are escaped for display; response text and evidence remain unchanged.'
    report['interface_sha256']=sha256((ROOT/'src/cayman_assistant/interface.py').read_bytes()).hexdigest()
    manifest=BUILD/'capture_manifest.json'
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1536,'height':864},record_video_dir=str(CAPTURE),
                                    record_video_size={'width':1536,'height':864})
        clock=time.perf_counter();page=context.new_page();video=page.video;updated=[];errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8501',wait_until='networkidle',timeout=60000)
        page.get_by_role('heading',name='Clear answers. Visible evidence.').wait_for(timeout=30000)

        def responses():
            return page.locator('[data-testid="stChatMessage"]').filter(has=page.locator('.assistant-emblem'))

        def ask(question,initial=False):
            count=responses().count()
            field=page.get_by_role('textbox',name='Ask a procedure question',exact=True) if initial else page.locator('[data-testid="stChatInputTextArea"]')
            field.press_sequentially(question,delay=26)
            if initial:page.get_by_role('button',name='Investigate →',exact=True).click()
            else:field.press('Enter')
            response=responses().nth(count)
            response.locator('.answer-type').wait_for(timeout=240000)
            page.wait_for_timeout(800)
            return response

        def frame(scroll=0):
            page.evaluate("document.querySelector('section.main').scrollTop=160")
            page.wait_for_timeout(700)
            page.evaluate("""(offset)=>{let e=document.querySelector('.source-text');
              while(e && !(e.clientHeight>200 && ['auto','scroll'].includes(getComputedStyle(e).overflowY)))e=e.parentElement;
              if(e)e.scrollTop=offset;
            }""",scroll)
            page.mouse.move(1510,35);page.wait_for_timeout(1500)

        @contextmanager
        def shot(name,label):
            entry={'id':name,'label':label,'start':round(time.perf_counter()-clock,3)}
            print('CAPTURE',name,flush=True)
            yield
            image=CAPTURE/(name+'.png');page.screenshot(path=str(image))
            entry.update(end=round(time.perf_counter()-clock,3),screenshot=str(image.relative_to(ROOT)),passed=True)
            updated.append(entry)

        def export(name):
            button=page.get_by_role('button',name='Export investigation',exact=True)
            button.scroll_into_view_if_needed()
            with page.expect_download() as info:button.click()
            path=CAPTURE/(name+'.json');info.value.save_as(str(path))
            return json.loads(path.read_text(encoding='utf-8'))

        def citation(message):
            message.get_by_role('button',name=re.compile(r'\[S\d+\] PR1949')).first.click()
            page.locator('.source-text').wait_for(timeout=15000)

        with shot('bond_limit','Savings-bond limit with readable currency amounts'):
            result=ask('What is the savings bond redemption limit for an account open less than 12 months?',initial=True)
            expect(result).to_contain_text('$1,000')
            expect(result.locator('.katex')).to_have_count(0)
            citation(result);frame(150)
        saved=export('bond_limit')
        report['responses']['bond_limit']=saved['messages'][-1]['result']
        report['currency_display_verified']=True

        with shot('bond_exception','A genuine withheld exception follow-up with original sources'):
            result=ask('What if they are eligible for The Private Bank Experience?')
            citation(result);frame(100)
        saved=export('bond_exception')
        report['responses']['bond_exception']=saved['messages'][-1]['result']

        with shot('feedback_export','Review feedback and a complete investigation export'):
            result.get_by_role('button',name='Inspect answer checks',exact=True).click()
            review=page.get_by_role('button',name='Needs review',exact=True)
            review.scroll_into_view_if_needed();review.click()
            page.get_by_role('button',name='✓ Needs review',exact=True).wait_for(timeout=15000)
            saved=export('investigation')
            assert len(saved['messages'])==4 and 'Needs review' in saved['feedback'].values()
            page.evaluate("document.querySelector('section.main').scrollTop=160")
            page.mouse.move(1510,35);page.wait_for_timeout(1800)
        report['complete_export_verified']=True
        report['silent_feedback']='Needs review'
        report['silent_client_errors']=errors
        assert not errors and not page.locator('[data-testid="stException"]').count()
        context.close();raw=str(Path(video.path()).relative_to(ROOT));browser.close()
        for entry in updated:
            entry['raw_video']=raw
            report['segments']=[s for s in report['segments'] if s['id']!=entry['id']]+[entry]
        report['status']='passed'
        manifest.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'status':report['status'],'currency_display_verified':True,
                      'exception_status':report['responses']['bond_exception']['status'],
                      'exception_repair':report['responses']['bond_exception']['metrics'].get('repair_attempted'),
                      'feedback':report['silent_feedback']},indent=2),flush=True)


def reports_only():
    manifest=BUILD/'capture_manifest.json';report=json.loads(manifest.read_text(encoding='utf-8'))
    updates=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1536,'height':864},record_video_dir=str(CAPTURE),
                                    record_video_size={'width':1536,'height':864})
        clock=time.perf_counter();page=context.new_page();video=page.video
        page.goto('http://127.0.0.1:8501',wait_until='networkidle')
        page.get_by_role('button',name='Evaluation',exact=True).wait_for(timeout=30000)
        start=time.perf_counter()-clock
        page.get_by_role('button',name='Evaluation',exact=True).click()
        page.get_by_role('heading',name='Evidence before confidence.').wait_for(timeout=15000)
        page.evaluate("document.querySelector('section.main').scrollTop=0")
        page.wait_for_timeout(1600)
        image=CAPTURE/'evaluation.png';page.screenshot(path=str(image))
        updates.append({'id':'evaluation','label':'Inspect actual evaluation view','start':start,'end':time.perf_counter()-clock,
                        'screenshot':str(image.relative_to(ROOT)),'passed':True})
        start=time.perf_counter()-clock
        for name in ['Evaluation report','Solution overview','Presentation']:
            button=page.get_by_role('button',name=name,exact=True);button.scroll_into_view_if_needed()
            with page.expect_download() as info:button.click()
            info.value.save_as(str(CAPTURE/info.value.suggested_filename))
        page.mouse.move(1510,35);page.wait_for_timeout(1500)
        page.evaluate("(()=>{const m=document.querySelector('section.main');m.scrollTop=m.scrollHeight})()")
        page.wait_for_timeout(700)
        boxes=[]
        for name in ['Evaluation report','Solution overview','Presentation']:
            box=page.get_by_role('button',name=name,exact=True).bounding_box()
            assert box and box['y']+box['height']<=864,box
            boxes.append([round(box['x']),round(box['y']),round(box['width']),round(box['height'])])
        image=CAPTURE/'report_download.png';page.screenshot(path=str(image))
        updates.append({'id':'report_download','label':'Actual report and presentation downloads','start':start,'end':time.perf_counter()-clock,
                        'screenshot':str(image.relative_to(ROOT)),'passed':True})
        context.close();raw=str(Path(video.path()).relative_to(ROOT));browser.close()
    for update in updates:
        update['raw_video']=raw
        report['segments']=[s for s in report['segments'] if s['id']!=update['id']]+[update]
    manifest.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    story_path=ROOT/'demo/tool-only/storyboard.json';story=json.loads(story_path.read_text(encoding='utf-8'))
    next(s for s in story['scenes'] if s['capture']=='report_download')['highlights']=boxes
    story_path.write_text(json.dumps(story,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Report downloads captured and button highlights measured',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--reports-only',action='store_true')
    if parser.parse_args().reports_only:reports_only()
    else:main()
