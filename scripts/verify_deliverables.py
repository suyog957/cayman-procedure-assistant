"""Final consistency and source-free packaging checks."""
from pathlib import Path
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pymupdf
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cayman_assistant.retrieval import verify_sources

verify_sources(ROOT,ROOT/'artifacts/index')
manifest=json.loads((ROOT/'artifacts/index/corpus_manifest.json').read_text())
vectors=np.load(ROOT/'artifacts/index/embeddings.npy',allow_pickle=False)
assert vectors.shape == (manifest['chunk_count'],384)
assert np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5)
deck=Presentation(ROOT/'submission/Cayman_Procedure_Assistant.pptx')
assert len(deck.slides)==6
notes_counts=[len(s.notes_slide.notes_text_frame.text.split()) for s in deck.slides]
assert min(notes_counts)>150
pdf=pymupdf.open(ROOT/'submission/Cayman_Procedure_Assistant.pdf')
assert len(pdf)==6 and all(len(p.get_text())>200 for p in pdf)
assert all(abs(p.rect.width/p.rect.height-16/9)<.001 for p in pdf)
pdf.close()
allowlist={'Cayman_Procedure_Assistant.pptx','Cayman_Procedure_Assistant.pdf','Demo_Runbook.pdf','Recorded_Demo.pdf','Presenter_Notes.pdf','README.txt'}
with zipfile.ZipFile(ROOT/'submission/Presentation_Materials.zip') as archive:
    assert set(archive.namelist())==allowlist
    assert archive.testzip() is None
    assert all(info.file_size>0 for info in archive.infolist())
metrics=json.loads((ROOT/'artifacts/evaluation/metrics.json').read_text())
answers=json.loads((ROOT/'artifacts/evaluation/answer_details.json').read_text())
assert len(answers)==40
assert metrics['answers']['ordinary_n']==30 and metrics['answers']['guardrails_n']==6
assert sum(r['result']['status']=='evidence_only' for r in answers if r['result']['generator_used'])==metrics['answers']['evidence_only_fallbacks']
assert not any(r['result']['checks'].get('comparison_conflicts') and r['result']['status']=='answered' for r in answers)
browser=json.loads((ROOT/'artifacts/browser_check.json').read_text())
for key in ['welcome_loaded','followup_pass','export_includes_latest_turn','second_session_isolated','reset_pass']:
    assert browser[key] is True
assert not browser['client_errors']
test_doc=ET.parse(ROOT/'artifacts/test_results.xml').getroot()
test_suites=list(test_doc.iter('testsuite'))
tests=sum(int(s.attrib.get('tests',0)) for s in test_suites)
assert tests>=19 and not any(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in test_suites)
summary={
    'original_sources_unchanged':True,'documents':manifest['document_count'],'passages':manifest['chunk_count'],
    'embedding_shape':list(vectors.shape),'embedding_norms_valid':True,
    'slides':len(deck.slides),'speaker_note_words_per_slide':notes_counts,
    'slide_pdf_valid':True,'submission_archive_source_free':True,'archive_files':sorted(allowlist),
    'automated_tests_passed':tests,'browser_integration_passed':True,
    'recorded_evaluation_cases':len(answers),'metrics_consistent':True,
    'limitation':'Structural and integration verification, not independent SME validation of generated answers.'}
(ROOT/'artifacts/verification_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
