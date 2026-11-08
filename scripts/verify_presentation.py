"""Check the leadership artifact, its measured claims and actual Office render."""
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata
import zipfile

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/presentation'


def normalized(value):
    return ''.join(re.findall(r'\w+',unicodedata.normalize('NFKC',value).casefold()))


def main():
    pptx=ROOT/'submission/Cayman_Procedure_Assistant.pptx'
    pdf_path=pptx.with_suffix('.pdf')
    deck=Presentation(pptx)
    layout=json.loads((OUT/'layout_review.json').read_text(encoding='utf-8'))
    metrics=json.loads((ROOT/'artifacts/evaluation/metrics.json').read_text(encoding='utf-8'))
    assert len(deck.slides)==6 and layout['status']=='passed'
    assert layout['render_engine']=='Microsoft PowerPoint' and not layout['text_bound_overflows']
    assert deck.slide_width/deck.slide_height==16/9
    words=[];bodies=[];notes=[];editable=0
    with pymupdf.open(pdf_path) as pdf:
        assert len(pdf)==6
        for i,slide in enumerate(deck.slides):
            text='\n'.join(s.text for s in slide.shapes if s.has_text_frame)
            body=normalized(text);note=slide.notes_slide.notes_text_frame.text
            bodies.append(body);notes.append(normalized(note));words.append(len(note.split()))
            assert len(note.split())>150
            exported=normalized(pdf[i].get_text())
            for shape in slide.shapes:
                assert shape.left>=0 and shape.top>=0
                assert shape.left+shape.width<=deck.slide_width+100
                assert shape.top+shape.height<=deck.slide_height+100
                if not shape.has_text_frame or not shape.text.strip():continue
                editable+=1
                assert normalized(shape.text) in exported,('PDF text differs from PPT',i+1,shape.name)
    assert editable>=150
    assert all(x in bodies[1] for x in ['110','20','bm25','384','conditions'])
    assert all(x in bodies[2] for x in ['qwen3','localcpu','citations','revision','withhold'])
    assert all(x in bodies[3] for x in ['5250','singlecontrol','s1','s2'])
    assert all(x in bodies[4] for x in ['accuracy','relevance','completeness','conciseness','proxy'])
    assert all(x in bodies[5] for x in ['pr63','pr1000','pr1949','validation','pilot'])
    count=metrics['answers']['ordinary_n']
    for mode in ['bm25','dense','hybrid']:
        row=next(r for r in metrics['retrieval'] if r['split']=='all' and r['mode']==mode)
        assert str(round(row['hit_at_5']*count))+str(count) in bodies[4]
    assert '2330' in bodies[4] and '635' in bodies[4] and '24' in bodies[4]
    assert '28wordmeandraft' in bodies[4] and 'draftlengthn32' in bodies[4]
    for value in [metrics['answers']['p50_seconds'],metrics['answers']['p95_seconds']]:
        assert normalized(f'{value:.1f}s') in bodies[4]
    image_meta=json.loads((ROOT/'assets/presentation/PROVENANCE.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(pptx) as archive:
        media=[archive.read(name) for name in archive.namelist() if name.startswith('ppt/media/')]
        assert any(sha256(data).hexdigest()==image_meta['sha256'] for data in media)
        assert not any('vbaproject' in name.lower() or name.startswith('ppt/embeddings/') for name in archive.namelist())
    with zipfile.ZipFile(ROOT/'submission/Presentation_Materials.zip') as archive:
        assert all(archive.read(name)==(ROOT/'submission'/name).read_bytes() for name in archive.namelist())
        assert not any(Path(name).suffix in {'.py','.js','.html'} for name in archive.namelist())
    approved=json.loads((ROOT/'demo/final/APPROVED_FINAL.json').read_text(encoding='utf-8'))
    for name,digest in approved['files'].items():
        assert sha256((ROOT/'demo/final'/name).read_bytes()).hexdigest()==digest
    cover=np.asarray(Image.open(ROOT/'artifacts/slides/slide_1.png').convert('RGB')).astype(np.int16)
    red_fraction=float(np.mean((cover[:,:,0]>140)&(cover[:,:,1]<100)&(cover[:,:,2]<110)))
    assert red_fraction<.08,'The cover should remain predominantly light.'
    sheet=Image.new('RGB',(1920,1716),'#fbfaf7');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
    for i in range(6):
        image=Image.open(ROOT/f'artifacts/slides/slide_{i+1}.png').convert('RGB').resize((960,540),Image.Resampling.LANCZOS)
        x=i%2*960;y=i//2*572;sheet.paste(image,(x,y));draw.text((x+22,y+546),f'{i+1:02d} / 06',font=font,fill='#665f59')
    sheet.save(OUT/'Leadership_Deck_Preview.jpg',quality=94)
    report={'status':'passed','slides':6,'render_engine':'Microsoft PowerPoint',
            'native_editable_text_boxes':editable,'powerpoint_text_bound_overflows':0,
            'all_pdf_text_matches_editable_slide_text':True,'speaker_note_words_per_slide':words,
            'total_speaker_note_words':sum(words),'planned_presentation_minutes':20,'separate_walkthrough_minutes':15,
            'cover_red_pixel_fraction':round(red_fraction,4),'all_four_response_quality_dimensions_visible':True,
            'measured_counts_and_limitations_verified':True,'real_approved_capture_embedded_without_pixel_changes':True,
            'source_free_archive_matches_current_files':True,'approved_final_video_and_sidecars_unchanged':True,
            'pptx_sha256':sha256(pptx.read_bytes()).hexdigest(),'pdf_sha256':sha256(pdf_path.read_bytes()).hexdigest()}
    (OUT/'content_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
