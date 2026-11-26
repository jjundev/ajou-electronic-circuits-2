"""The source-prep machine action reads every lecture PDF without a worker."""
import json

import pymupdf

import _util  # noqa: F401  (puts scripts on sys.path)
from pack_sources import prepare_sources


def lecture_repo(tmp_path, *, pdfs=True):
    repo = tmp_path/'repo'; (repo/'강의노트').mkdir(parents=True); (repo/'STT').mkdir()
    stt = repo/'STT/0909 전회2.md'; stt.write_text('x', encoding='utf-8')
    if pdfs:
        for n, text in ((2, 'second'), (1, 'first')):
            with pymupdf.open() as d:
                d.new_page().insert_text((72, 72), text); d.save(repo/f'강의노트/2026F_Lec{n}_T.pdf')
    return repo, stt


def test_source_prep_extracts_every_lecture_pdf(tmp_path):
    repo, stt = lecture_repo(tmp_path)
    files = prepare_sources(repo, ['0909'], {'0909': stt}, tmp_path/'out')
    slides = files['slides.txt'].read_text(encoding='utf-8')
    assert slides.index('=== L01 s1 ===') < slides.index('=== L02 s1 ===') and 'first' in slides
    session, = json.loads(files['source-map.json'].read_text(encoding='utf-8'))['sessions']
    assert session['status'] == 'ready' and len(session['pdfs']) == 2 and session['missing'] == []


def test_source_prep_skips_unreadable_pdf(tmp_path):
    # Review Focus 1: one damaged PDF does not fail the whole extraction.
    repo, stt = lecture_repo(tmp_path)
    (repo/'강의노트/2026F_Lec3_Bad.pdf').write_bytes(b'not a pdf')
    files = prepare_sources(repo, ['0909'], {'0909': stt}, tmp_path/'out')
    session, = json.loads(files['source-map.json'].read_text(encoding='utf-8'))['sessions']
    assert session['missing'] == ['2026F_Lec3_Bad.pdf: unreadable'] and len(session['pdfs']) == 2
    assert '=== L03' not in files['slides.txt'].read_text(encoding='utf-8')


def test_source_prep_without_pdfs_is_stt_only(tmp_path):
    repo, stt = lecture_repo(tmp_path, pdfs=False)
    files = prepare_sources(repo, ['0909'], {'0909': stt}, tmp_path/'out')
    session, = json.loads(files['source-map.json'].read_text(encoding='utf-8'))['sessions']
    assert session['pdfs'] == [] and session['missing'] == ['강의노트 PDF 없음']
    assert session['status'] == 'ready' and session['stt'] == str(stt)
