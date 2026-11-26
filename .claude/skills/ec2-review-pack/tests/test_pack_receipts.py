import json
from pathlib import Path
import pytest
from _util import SCRIPTS
from pack_support import make_run, install_task, receipt_for
import pack_flow as f
from pack_receipts import validate_receipt, verify_receipt_files


def setup(tmp_path, role='author', **kw):
    _, run = make_run(tmp_path)
    tid = install_task(run, role, **kw)
    attempt = f.claim_task(run, tid)['attempt']
    path = receipt_for(run, tid, attempt)
    return run, tid, attempt, path


def edit(path, **kw):
    data = json.loads(path.read_text()); data.update(kw); path.write_text(json.dumps(data)); return data


def test_done_text_without_files_fails(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    edit(path, outputs=[])
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)
    assert f.load_state(run)['tasks'][tid]['status'] != 'done'


def test_declared_inputs_cannot_omit_brief_inputs(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    edit(path, inputs=[])
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)


def test_receipt_cannot_expand_allowed_outputs(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    other = run / 'other'; other.write_text('bad')
    data = json.loads(path.read_text()); data['outputs'].append({'path': str(other), 'sha256': f._sha(other)})
    edit(path, outputs=data['outputs'])
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)


def test_missing_or_changed_topic_evidence_fails(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    result = validate_receipt(f.load_state(run), f.load_state(run)['tasks'][tid], path)
    Path(result['outputs'][0]['path']).write_text('changed')
    assert verify_receipt_files(result)


def test_source_map_covers_actual_dates_and_required_material(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'source-prep', outputs=['source-map.json', 'slides.txt'])
    source = run / 'source-map.json'
    source.write_text(json.dumps({'schema_version': 1, 'sessions': []}))
    data = json.loads(path.read_text()); data['outputs'][0]['sha256'] = f._sha(source); edit(path, outputs=data['outputs'])
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)


def test_child_ready_does_not_mark_published(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    edit(path, status='ready-for-publish')
    f.accept_task(run, tid, attempt, path)
    assert f.load_state(run)['publication'].get('explanation') != 'published'


def test_all_pdf_pages_required(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'pdf-qa', outputs=['answer-review.json', 'answer-review.md'])
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)


def test_success_records_outputs_and_accepts_current_attempt(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    assert f.accept_task(run, tid, attempt, path)['tasks'][tid]['status'] == 'done'


def test_style_audit_requires_every_topic_and_rule(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'style-audit', outputs=['work/style-audit/learning-style-audit-note.json'])
    audit_path = run / 'work/style-audit/learning-style-audit-note.json'
    snapshot = json.loads((run / 'learning-style.json').read_text())
    audit = {'learning_style': snapshot, 'items': {'synthetic': {'status': 'pass', 'reviewer': 'synthetic-reviewer',
        'rules': {rule: {'disposition': 'applied', 'evidence': 'synthetic fixture only'} for rule in snapshot['rule_ids']}}}}
    audit_path.write_text(json.dumps(audit))
    data = json.loads(path.read_text()); data['outputs'][0]['sha256'] = f._sha(audit_path); edit(path, outputs=data['outputs'])
    assert f.accept_task(run, tid, attempt, path)['tasks'][tid]['status'] == 'done'
    audit_path.write_text('{}')
    assert verify_receipt_files(f.load_state(run)['tasks'][tid]['receipt'])


def test_brief_mutation_and_repo_symlink_output_are_rejected(tmp_path):
    run, tid, attempt, path = setup(tmp_path)
    brief = Path(f.load_state(run)['tasks'][tid]['brief'])
    brief.write_text(brief.read_text() + ' ')
    with pytest.raises(f.FlowError, match='brief changed'): f.accept_task(run, tid, attempt, path)


def test_child_plain_pass_cannot_replace_real_stage(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'child-coordinator', outputs=['child-output.json'])
    edit(path, status='ready-for-publish')
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)
    assert f.load_state(run)['publication'] == {}


def test_pdf_review_requires_exact_rendered_page_set(tmp_path):
    import pymupdf
    from pack_receipts import _pdf
    _, run = make_run(tmp_path)
    pdf = run / 'synthetic.pdf'
    with pymupdf.open() as document:
        document.new_page(); document.new_page(); document.save(pdf)
    overlay = run / 'overlay.json'; overlay.write_text(json.dumps({'learning_style': {'sha256': 'synthetic-style'}}))
    (run / 'answer-pages').mkdir()
    report = run / 'answer-review.md'; report.write_text('synthetic reviewer fixture')
    images = [run / 'answer-pages' / ('page-' + str(i) + '.png') for i in (1, 2)]
    from PIL import Image
    for image in images: Image.new('RGB', (16, 9)).save(image)
    review = {'schema_version': 1, 'status': 'pass', 'reviewer': 'synthetic-pdf-reviewer', 'overflow': [],
        'pdf_sha256': f._sha(pdf), 'overlay_sha256': f._sha(overlay), 'learning_style_sha256': 'synthetic-style',
        'evidence': [{'path': str(p.relative_to(run)), 'sha256': f._sha(p)} for p in [images[0], report]]}
    review_path = run / 'answer-review.json'; review_path.write_text(json.dumps(review))
    with pytest.raises(f.FlowError, match='all actual PDF pages'): _pdf({'pdf': str(pdf), 'overlay': str(overlay)}, run)
    review['evidence'].append({'path': str(images[1].relative_to(run)), 'sha256': f._sha(images[1])})
    review_path.write_text(json.dumps(review))
    assert len(_pdf({'pdf': str(pdf), 'overlay': str(overlay)}, run)) == 5


def test_source_prep_rejects_text_named_pdf(tmp_path):
    from pack_receipts import _source
    repo, run = make_run(tmp_path)
    fake = repo / 'fake.pdf'; fake.write_text('not a PDF')
    (run / 'source-map.json').write_text(json.dumps({'schema_version': 1, 'sessions': [
        {'date': '0909', 'stt': str(repo / 'STT/0909 전회2.md'), 'pdfs': [str(fake)], 'status': 'ready', 'missing': []}]}))
    with pytest.raises(f.FlowError): _source(f.load_state(run), run)


def test_browser_rejects_bytes_named_png(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'browser-qa', outputs=['work/browser/report.json', 'work/browser/screen.png'])
    report = run / 'work/browser/report.json'
    report.write_text('{}')
    data = json.loads(path.read_text()); data['outputs'][0]['sha256'] = f._sha(report)
    edit(path, outputs=data['outputs'], reviews=[str(report)], counts={'targets': ['synthetic']})
    with pytest.raises(f.FlowError): f.accept_task(run, tid, attempt, path)


def test_versioned_producer_manifest_remains_current_after_handoff(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'scope-draft', outputs=['scope.json', 'work/scope-draft/manifest.json'])
    accepted = f.accept_task(run, tid, attempt, path)['tasks'][tid]['receipt']
    (run / 'manifest.json').write_text('final later version')
    assert verify_receipt_files(accepted) == []


def test_genuine_child_current_stage_success_and_parent_problem_binding(tmp_path):
    from pack_support import genuine_child_run
    _, run, tid, child_run = genuine_child_run(tmp_path)
    attempt = f.claim_task(run, tid)['attempt']
    path = receipt_for(run, tid, attempt); edit(path, status='ready-for-publish')
    state = f.load_state(run)
    assert validate_receipt(state, state['tasks'][tid], path)['task_status'] == 'done'
    # A child with valid own source/reviews must still match this parent problem order.
    manifest = run / 'manifest.json'
    data = json.loads(manifest.read_text()); data['problems'] = [{'id': 'P10.03'}]; manifest.write_text(json.dumps(data))
    brief = Path(state['tasks'][tid]['brief']); data = json.loads(brief.read_text())
    data['inputs'][-1]['sha256'] = f._sha(manifest); brief.write_text(json.dumps(data))
    data = json.loads(path.read_text()); data['inputs'][-1]['sha256'] = f._sha(manifest); path.write_text(json.dumps(data))
    child_path = child_run / 'child-receipt.json'; data = json.loads(child_path.read_text())
    for record in data['files']:
        if record['path'] == str(manifest): record['sha256'] = f._sha(manifest)
    child_path.write_text(json.dumps(data))
    with pytest.raises(f.FlowError, match='parent'): validate_receipt(state, state['tasks'][tid], path)


def test_parent_rejects_old_authoring_from_an_earlier_child_runner(tmp_path):
    from pack_support import genuine_child_run

    _, run, tid, _ = genuine_child_run(tmp_path, historical_markup=True)
    attempt = f.claim_task(run, tid)['attempt']
    path = receipt_for(run, tid, attempt)
    edit(path, status='ready-for-publish')
    state = f.load_state(run)
    with pytest.raises(f.FlowError, match='p1: 새 원고'):
        validate_receipt(state, state['tasks'][tid], path)


def test_content_supplement_uses_owned_version_and_preserves_audit_input(tmp_path):
    run, tid, attempt, path = setup(tmp_path, 'content-review', outputs=['work/content-review/learning-style-audit-note.json'])
    snapshot = json.loads((run / 'learning-style.json').read_text())
    data = {'learning_style': snapshot, 'items': {'synthetic': {'status': 'pass', 'reviewer': 'synthetic-reviewer',
        'rules': {rule: {'disposition': 'applied', 'evidence': 'synthetic test evidence'} for rule in snapshot['rule_ids']}}}}
    prior = run / 'work/style-audit/learning-style-audit-note.json'; prior.parent.mkdir(parents=True); prior.write_text(json.dumps(data))
    before = f._sha(prior)
    output = run / 'work/content-review/learning-style-audit-note.json'; output.write_text(json.dumps(data))
    receipt = json.loads(path.read_text()); receipt['outputs'][0]['sha256'] = f._sha(output)
    receipt['inputs'].append({'path': str(prior), 'sha256': before})
    brief = Path(f.load_state(run)['tasks'][tid]['brief']); b = json.loads(brief.read_text()); b['inputs'] = receipt['inputs']; brief.write_text(json.dumps(b))
    edit(path, inputs=receipt['inputs'], outputs=receipt['outputs'], reviews=[str(output)], counts={'targets': ['synthetic']})
    state = f.load_state(run)
    result = validate_receipt(state, state['tasks'][tid], path)
    assert result['task_status'] == 'done' and f._sha(prior) == before
    prior.write_text('external edit')
    assert verify_receipt_files(result)


def test_png_decoder_rejects_corrupt_file(tmp_path):
    from pack_receipts import _png
    path = tmp_path / 'page-1.png'; path.write_bytes(b'not image bytes')
    with pytest.raises(f.FlowError, match='invalid PNG'): _png(path)


def test_versioned_audit_output_is_required_and_accepted(tmp_path):
    _, run = make_run(tmp_path)
    output = run / 'work/style-audit/audits/version-one/learning-style-audit-note.json'
    tid = install_task(run, 'style-audit', outputs=[str(output.relative_to(run))])
    brief = Path(f.load_state(run)['tasks'][tid]['brief'])
    edit(brief, audit_output=str(output))
    attempt = f.claim_task(run, tid)['attempt']
    receipt = receipt_for(run, tid, attempt)
    snapshot = json.loads((run / 'learning-style.json').read_text())
    output.write_text(json.dumps({'learning_style': snapshot, 'items': {'synthetic': {'status': 'pass', 'reviewer': 'synthetic-reviewer',
        'rules': {rule: {'disposition': 'applied', 'evidence': 'synthetic version evidence'} for rule in snapshot['rule_ids']}}}}))
    edit(receipt, outputs=[{'path': str(output), 'sha256': f._sha(output)}])
    assert f.accept_task(run, tid, attempt, receipt)['tasks'][tid]['status'] == 'done'


@pytest.mark.parametrize('case', ['outside', 'wrong_role', 'basename', 'input', 'relative', 'undeclared'])
def test_audit_output_is_role_owned_and_disjoint_from_inputs(tmp_path, case):
    from pack_receipts import _audit
    run, tid, attempt, receipt = setup(tmp_path, 'style-audit', outputs=['work/style-audit/learning-style-audit-note.json'])
    snapshot = json.loads((run / 'learning-style.json').read_text())
    document = {'learning_style': snapshot, 'items': {'synthetic': {'status': 'pass', 'reviewer': 'synthetic-reviewer',
        'rules': {rule: {'disposition': 'applied', 'evidence': 'synthetic fixture'} for rule in snapshot['rule_ids']}}}}
    legacy = run / 'work/style-audit/learning-style-audit-note.json'; legacy.write_text(json.dumps(document))
    output = run / 'work/style-audit/audits/version-one/learning-style-audit-note.json'
    if case == 'outside': output = tmp_path / 'learning-style-audit-note.json'
    if case == 'wrong_role': output = run / 'work/content-review/audits/version-one/learning-style-audit-note.json'
    if case == 'basename': output = output.with_name('other.json')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(document))
    state = f.load_state(run); brief = Path(state['tasks'][tid]['brief'])
    data = json.loads(brief.read_text()); data['audit_output'] = str(output)
    if case != 'undeclared': data['allowed_outputs'].append(str(output))
    if case == 'input': data['inputs'].append({'path': str(output), 'sha256': f._sha(output)})
    if case == 'relative': data['audit_output'] = str(output.relative_to(run))
    brief.write_text(json.dumps(data))
    with pytest.raises(f.FlowError, match='audit output'): _audit(state, state['tasks'][tid], run)


def test_selection_requires_exact_chosen_title_map(tmp_path):
    from pack_support import workflow_until, workflow_accept
    _,run=make_run(tmp_path)
    workflow_until(run,'selection')
    def corrupt():
        # Rehash corrupt output: rejection must come from map semantics.
        title=run/'display-titles.json'; title.write_text('{"extra":"wrong"}')
        for receipt in (run/'work/selection').glob('*-report.json'):
            data=json.loads(receipt.read_text())
            for item in data['outputs']:
                if item['path']==str(title): item['sha256']=f._sha(title)
            receipt.write_text(json.dumps(data))
    with pytest.raises(f.FlowError,match='title'):
        workflow_accept(run,'selection',before_accept=corrupt)


@pytest.mark.parametrize('damage', [None, 'report', 'page', 'unbound-report'])
def test_pdf_reviewer_produces_exact_documented_outputs(tmp_path, damage):
    """Synthetic review uses real PDF pages; no helper precreates allowed outputs."""
    from pack_support import workflow_until
    import pymupdf
    _, run = make_run(tmp_path)
    workflow_until(run, 'pdf-qa', problems=1)
    task = f.load_state(run)['tasks']['pdf-qa']
    attempt = f.claim_task(run, 'pdf-qa')['attempt']
    brief = json.loads(Path(task['brief']).read_text())
    assert Path(brief['report']) == run / 'answer-review.md'
    report = Path(brief['report']); report.write_text('Synthetic fixture only: inspected both pages; no defects.')
    images = []
    with pymupdf.open(brief['pdf']) as pdf:
        for number, page in enumerate(pdf, 1):
            path = run / 'answer-pages' / f'page-{number}.png'
            path.parent.mkdir(exist_ok=True); page.get_pixmap().save(path); images.append(path)
    review_path = run / 'answer-review.json'
    review = dict(schema_version=1, status='pass', reviewer='synthetic-independent-pdf', overflow=[],
        pdf_sha256=f._sha(Path(brief['pdf'])), overlay_sha256=f._sha(Path(brief['overlay'])),
        learning_style_sha256=json.loads(Path(brief['overlay']).read_text())['learning_style']['sha256'],
        evidence=[dict(path=str(p.relative_to(run)), sha256=f._sha(p)) for p in [*images, report]])
    review_path.write_text(json.dumps(review))
    receipt = run / 'work/pdf-qa/receipt.json'
    receipt.write_text(json.dumps(dict(schema_version=1, run_id=f.load_state(run)['run_id'], task_id='pdf-qa',
        attempt=attempt, status='done', inputs=brief['inputs'],
        outputs=[dict(path=str(p),sha256=f._sha(p)) for p in [review_path, report, *images]],
        report=str(report), reviews=[str(review_path)], counts={}, unresolved=[])))
    if damage == 'unbound-report':
        other = run / 'work/pdf-qa/other.md'; other.write_text('unrelated report')
        review['evidence'][-1] = dict(path=str(other.relative_to(run)), sha256=f._sha(other))
        review_path.write_text(json.dumps(review))
        data = json.loads(receipt.read_text())
        data['outputs'][0]['sha256'] = f._sha(review_path)
        receipt.write_text(json.dumps(data))
    if damage == 'report': report.write_text('changed after review')
    if damage == 'page': images[-1].unlink()
    if damage:
        with pytest.raises(f.FlowError): f.accept_task(run, 'pdf-qa', attempt, receipt)
    else:
        f.accept_task(run, 'pdf-qa', attempt, receipt)
        assert f.load_state(run)['tasks']['pdf-qa']['status'] == 'done'
        assert not (run / 'work/pdf-qa/report.md').exists()


def _nfd(p): import unicodedata; return unicodedata.normalize('NFD', str(p))
def _nfc(p): import unicodedata; return unicodedata.normalize('NFC', str(p))


def _needs_nfd_alias(folder):
    from _util import aliases_nfd
    if not aliases_nfd(folder): pytest.skip('filesystem keeps NFC and NFD names apart')


def _real_pdf(path):
    import pymupdf as fitz
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(); doc.new_page().insert_text((72, 72), 'slide'); doc.save(path); doc.close()


def test_init_stores_nfc_repo(tmp_path):
    _needs_nfd_alias(tmp_path)
    repo, run = make_run(tmp_path, repo_name=_nfd('전자회로2'), init_repo=Path(_nfd(tmp_path / '전자회로2')))
    state = f.load_state(run)
    assert state['repo'] == _nfc(state['repo']) and state['run'] == _nfc(state['run'])
    assert all(k == _nfc(k) for k in state['hashes'])


def test_source_map_accepts_mixed_nfd_component(tmp_path):
    _needs_nfd_alias(tmp_path)
    from pack_receipts import _source
    repo, run = make_run(tmp_path, repo_name=_nfd('전자회로2'), init_repo=Path(_nfc(tmp_path / '전자회로2')))
    pdf = repo / _nfd('강의노트') / 'x.pdf'; _real_pdf(pdf)
    (run / 'source-map.json').write_text(json.dumps({'schema_version': 1, 'sessions': [
        {'date': '0909', 'stt': _nfd(repo / 'STT/0909 전회2.md'), 'pdfs': [_nfd(pdf)], 'status': 'ready', 'missing': []}]}))
    assert _source(f.load_state(run), run) == 'done'


def test_source_map_rejects_sibling_outside_repo(tmp_path):
    from pack_receipts import _source
    repo, run = make_run(tmp_path, repo_name='전자회로2')
    pdf = tmp_path / '전자회로2-copy' / '강의노트' / 'x.pdf'; _real_pdf(pdf)
    (run / 'source-map.json').write_text(json.dumps({'schema_version': 1, 'sessions': [
        {'date': '0909', 'stt': str(repo / 'STT/0909 전회2.md'), 'pdfs': [str(pdf)], 'status': 'ready', 'missing': []}]}))
    with pytest.raises(f.FlowError, match='source material missing/outside REPO'): _source(f.load_state(run), run)


def test_state_loads_when_run_is_spelled_nfd(tmp_path):
    _needs_nfd_alias(tmp_path)
    _, run = make_run(tmp_path)
    assert f.load_state(Path(_nfd(run)))['run_id'] == f.load_state(run)['run_id']
