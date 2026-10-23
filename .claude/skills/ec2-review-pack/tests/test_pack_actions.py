"""Execution boundary tests; synthetic gates never leave temporary fixtures."""
import json
import sys
from pathlib import Path
import pytest
from _util import REPO, prepare_mini_run
from pack_support import make_run, workflow_until
import pack_flow as f
import pack_actions as a


def ready(tmp_path, monkeypatch, action='assemble-note'):
    from pack_support import action_run
    return action_run(tmp_path,action=action)


def child(monkeypatch, text, *, write=True, exit_code=0):
    def command(state, action):
        output = a._paths(state)['note']
        script = 'from pathlib import Path; import sys; '
        if write: script += f'Path({str(output)!r}).parent.mkdir(parents=True,exist_ok=True); Path({str(output)!r}).write_text("note",encoding="utf-8"); '
        script += f'sys.stdout.write({text!r}); sys.exit({exit_code})'
        script_path=Path(state['run'])/'synthetic-child.py'
        script_path.write_text(script,encoding='utf-8')
        return [sys.executable,str(script_path)]
    monkeypatch.setattr(a, 'action_argv', command)


def test_warning_stdout_is_not_parsed_as_path(tmp_path, monkeypatch):
    _, run = ready(tmp_path, monkeypatch)
    noisy = 'PyMuPDF warning\nC:/not-a-file.pdf\n'
    child(monkeypatch, noisy)
    result = a.run_action(run, 'assemble-note')
    assert result['status'] == 'done'
    assert Path(result['stdout_path']).read_text(encoding='utf-8') == noisy
    assert result['outputs']


def test_large_logs_remain_in_files(tmp_path, monkeypatch):
    _, run = ready(tmp_path, monkeypatch)
    child(monkeypatch, 'x' * 300000)
    result = a.run_action(run, 'assemble-note')
    assert Path(result['stdout_path']).stat().st_size == 300000
    assert len(json.dumps(result)) < 10000


def test_exit_zero_without_expected_output_fails(tmp_path, monkeypatch):
    _, run = ready(tmp_path, monkeypatch)
    child(monkeypatch, 'OK', write=False)
    assert a.run_action(run, 'assemble-note')['status'] != 'done'


def test_workbook_argv_preserves_ids_layout_and_overlay(tmp_path):
    repo, run = make_run(tmp_path)
    (run/'manifest.json').write_text(json.dumps({'range':'0909','slug':'X','problems':[{'id':'P10.02'},{'id':'P9.01'}]}))
    state = f.load_state(run)
    state['published_overlay'] = str(repo/'published-overlay.json')
    argv = a.action_argv(state, 'build-answers')
    assert argv[argv.index('--ids')+1] == 'P10.02,P9.01'
    assert argv[argv.index('--layout')+1] == 'video-16x9'
    assert argv[argv.index('--answer-overlay')+1] == state['published_overlay']
    assert argv[argv.index('--pdf-dir')+1] == str(run/'answers')
    assert '--selection' in argv and '--display-titles' in argv


def test_final_check_has_no_deferral(tmp_path):
    _, run = make_run(tmp_path)
    (run/'manifest.json').write_text(json.dumps({'range':'0909','slug':'X','problems':[]}))
    state = f.load_state(run)
    assert '--defer-answer-pdf' not in a.action_argv(state, 'final-check')
    assert '--defer-answer-pdf' in a.action_argv(state, 'precheck')


def test_uncertain_write_requires_recovery(tmp_path, monkeypatch):
    _, run = ready(tmp_path, monkeypatch)
    state=f.load_state(run)
    def change(s):
        s['actions']['assemble-note'].update(status='running', attempt='lost', attempt_dir=str(run/'lost'))
        return s
    f.update_state(run,state['revision'],change)
    assert a.reconcile_action(run,'assemble-note')['status'] == 'recovery_required'
    with pytest.raises(f.FlowError, match='stopped|completion'):
        a.recover_run(run)
    with pytest.raises(f.FlowError): a.run_action(run,'assemble-note')


def test_failure_after_first_pack_write_restores_coherent_pack(tmp_path, monkeypatch):
    repo, run = ready(tmp_path,monkeypatch, 'prepare-pack')
    pack=repo/'복습노트/0909'; pack.mkdir(parents=True)
    old=pack/'정리노트_0909_Old.html'; old.write_text('old')
    assert a.run_action(run,'prepare-pack')['status']=='done'
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],'assemble-note':dict(id='assemble-note',status='pending',dependencies=['prepare-pack'])}))
    child(monkeypatch,'failure',exit_code=1)
    result=a.run_action(run,'assemble-note')
    assert result['status']!='done'
    restored=a.recover_run(run)
    assert restored['status'] in ('restored','withheld')
    assert old.read_text()=='old'
    assert not (pack/'정리노트_0909_Synthetic.html').exists()


def test_action_allowlist_rejects_prepare_argv(tmp_path):
    _,run=make_run(tmp_path)
    for action in ('prepare-pack','arbitrary'):
        with pytest.raises(f.FlowError): a.action_argv(f.load_state(run),action)


def test_missing_completion_record_reconciles_full_publication(tmp_path, monkeypatch):
    _,run=ready(tmp_path,monkeypatch)
    child(monkeypatch,'warning')
    result=a.run_action(run,'assemble-note')
    Path(result['stdout_path']).with_name('result.json').unlink()
    state=f.load_state(run)
    def change(s):
        s['actions']['assemble-note']['status']='running'
        return s
    f.update_state(run,state['revision'],change)
    assert a.reconcile_action(run,'assemble-note')['status']=='done'


def test_answer_gate_failure_never_marks_published(tmp_path,monkeypatch):
    _,run=make_run(tmp_path)
    workflow_until(run,'publish-answer',problems=1)
    # The genuine publisher rejects absent published overlay. Never substitute a success receipt.
    result=a.run_action(run,'publish-answer')
    assert result['status']!='done'
    assert not f.load_state(run)['publication'].get('answer')


def test_confirmation_does_not_authorize_external_inventory(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch)
    child(monkeypatch,'OK')
    result=a.run_action(run,'assemble-note'); folder=Path(result['stdout_path']).parent
    (folder/'stopped.json').unlink()
    process=json.loads((folder/'process.json').read_text())
    (folder/'stopped-confirmation.json').write_text(json.dumps({'schema_version':1,'attempt':result['attempt'],
        'confirmed_by':'synthetic-main','reason':'test process wait completed','process':process}))
    a._paths(f.load_state(run))['note'].write_text('external edit')
    assert a.reconcile_action(run,'assemble-note')['status']=='recovery_required'
    with pytest.raises(f.FlowError): a.recover_run(run)


def test_report_records_actual_files_and_recovery(tmp_path):
    _,run=make_run(tmp_path)
    data=json.loads(a.write_report(run).read_text(encoding='utf-8'))
    assert data['range']=='0909' and 'checks' in data and 'recovery' in data


def genuine_action_publication(tmp_path):
    from pack_support import genuine_child_run
    import shutil
    repo,run,_,child_run=genuine_child_run(tmp_path)
    for rel in ('.claude/skills/ec2-problem-explain/scripts','.claude/skills/ec2-review-pack/scripts','workbook','교과서/마이크로전자회로/_tools','from_the_past/md/_tools'):
        (repo/rel).mkdir(parents=True,exist_ok=True)
        for module in (REPO/rel).glob('*.py'): shutil.copyfile(module,repo/rel/module.name)
    def change(s):
        s['actions']['publish-explanation']=dict(id='publish-explanation',status='pending',dependencies=[])
        return s
    f.update_state(run,f.load_state(run)['revision'],change)
    return repo,run


def test_actual_publication_reconciles_all_files(tmp_path):
    _,run=genuine_action_publication(tmp_path)
    result=a.run_action(run,'publish-explanation')
    assert result['status']=='done', (Path(result['stderr_path']).read_text(),Path(result['stdout_path']).parent.joinpath('error.txt').read_text() if Path(result['stdout_path']).parent.joinpath('error.txt').exists() else '')
    folder=Path(result['stdout_path']).parent
    (folder/'result.json').unlink()
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],'publish-explanation':dict(s['actions']['publish-explanation'],status='running',invalidated_active=True)}))
    assert a.reconcile_action(run,'publish-explanation')['status']=='done'
    output=next(Path(x['path']) for x in result['outputs'] if x['path'].endswith('.html'))
    output.write_text('external')
    assert a.reconcile_action(run,'publish-explanation')['status']=='recovery_required'


def test_actual_assemble_and_check_gate(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch)
    result=a.run_action(run,'assemble-note')
    assert result['status']=='done'
    audit=run/'audit.json'
    m=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    audit.write_text(json.dumps({'learning_style':m['learning_style'],'items':{}}))
    state=f.load_state(run)
    def change(s):
        s['active_audit']=str(audit)
        s['actions']['precheck']=dict(id='precheck',status='pending',dependencies=['assemble-note'])
        return s
    f.update_state(run,state['revision'],change)
    result=a.run_action(run,'precheck')
    assert result['status']=='needs_fix'
    assert 'style' in Path(result['stdout_path']).read_text(encoding='utf-8').lower()
    assert f.load_state(run)['actions']['precheck']['status']!='done'


def test_live_command_blocks_second_launch_and_recovery(tmp_path,monkeypatch):
    import threading
    import time
    _,run=ready(tmp_path,monkeypatch)
    entered=run/'entered'; release=run/'release'
    def command(state,action):
        return [sys.executable,'-c',f'from pathlib import Path; import time; Path({str(entered)!r}).touch();\nwhile not Path({str(release)!r}).exists(): time.sleep(.02)']
    monkeypatch.setattr(a,'action_argv',command)
    results=[]
    thread=threading.Thread(target=lambda: results.append(a.run_action(run,'assemble-note')))
    thread.start()
    try:
        deadline=time.monotonic()+10
        while not entered.exists() and time.monotonic()<deadline: time.sleep(.02)
        assert entered.exists()
        with pytest.raises(f.FlowError,match='lock'): a.run_action(run,'assemble-note')
        with pytest.raises(f.FlowError,match='lock'): a.recover_run(run)
        with pytest.raises(f.FlowError,match='lock'): a.reconcile_action(run,'assemble-note')
    finally:
        release.touch(); thread.join(10)
    assert not thread.is_alive() and results[0]['status']!='done'


def test_input_edit_during_failed_command_cannot_become_recovery_baseline(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch,'prepare-pack')
    pack=repo/'복습노트/0909'; pack.mkdir(parents=True)
    old=pack/'정리노트_0909_Old.html'; old.write_text('old')
    assert a.run_action(run,'prepare-pack')['status']=='done'
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],'assemble-note':dict(id='assemble-note',status='pending',dependencies=['prepare-pack'])}))
    def command(state,action):
        note=a._paths(state)['note']; manifest=run/'manifest.json'
        return [sys.executable,'-c',f'from pathlib import Path; Path({str(note)!r}).write_text("partial"); Path({str(manifest)!r}).write_text("external"); raise SystemExit(1)']
    monkeypatch.setattr(a,'action_argv',command)
    assert a.run_action(run,'assemble-note')['status']=='recovery_required'
    with pytest.raises(f.FlowError): a.recover_run(run)



def test_actual_answer_publish_and_receipt_reconciliation(tmp_path):
    import shutil
    import pymupdf
    from PIL import Image
    _,run=genuine_action_publication(tmp_path)
    assert a.run_action(run,'publish-explanation')['status']=='done'
    state=f.load_state(run); p=a._paths(state)
    pdf=run/'answers/test.pdf'; pdf.parent.mkdir()
    with pymupdf.open() as document: document.new_page(); document.save(pdf)
    overlay=run/'answers/answer-overlay.json'; shutil.copyfile(p['overlay'],overlay)
    png=run/'page-1.png'; Image.new('RGB',(16,9)).save(png)
    report=run/'screen.md'; report.write_text('Synthetic test only')
    review={'schema_version':1,'status':'pass','reviewer':'synthetic','overflow':[],
        'pdf_sha256':f._sha(pdf),'overlay_sha256':f._sha(overlay),
        'learning_style_sha256':json.loads(overlay.read_text())['learning_style']['sha256'],
        'evidence':[{'path':x.name,'sha256':f._sha(x)} for x in (png,report)]}
    (run/'answer-review.json').write_text(json.dumps(review))
    def change(s):
        s.update(answer_pdf=str(pdf),answer_overlay=str(overlay))
        s['actions']['publish-answer']=dict(id='publish-answer',status='pending',dependencies=['publish-explanation'])
        return s
    f.update_state(run,state['revision'],change)
    result=a.run_action(run,'publish-answer')
    assert result['status']=='done', Path(result['stderr_path']).read_text()
    assert p['answer'].read_bytes()==pdf.read_bytes()
    folder=Path(result['stdout_path']).parent; (folder/'result.json').unlink()
    assert a.reconcile_action(run,'publish-answer')['status']=='done'
    p['answer'].write_bytes(b'external')
    assert a.reconcile_action(run,'publish-answer')['status']=='recovery_required'


def test_main_stop_confirmation_allows_only_saved_inventory_recovery(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch,'prepare-pack')
    pack=repo/'복습노트/0909'; pack.mkdir(parents=True)
    old=pack/'정리노트_0909_Old.html'; old.write_text('old')
    assert a.run_action(run,'prepare-pack')['status']=='done'
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],'assemble-note':dict(id='assemble-note',status='pending',dependencies=['prepare-pack'])}))
    child(monkeypatch,'failed',exit_code=1)
    result=a.run_action(run,'assemble-note'); folder=Path(result['stdout_path']).parent
    (folder/'stopped.json').unlink()
    (folder/'stopped-confirmation.json').write_text(json.dumps({'schema_version':1,'attempt':result['attempt'],
        'confirmed_by':'synthetic-main','reason':'actual test subprocess returned and no descendants launched',
        'process':json.loads((folder/'process.json').read_text())}))
    assert a.reconcile_action(run,'assemble-note')['status']=='recovery_required'
    assert a.recover_run(run)['status']=='restored'
    assert old.read_text()=='old'


def test_frozen_input_is_not_rehashed_between_guard_and_spawn(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch)
    original=a._inputs
    def race(state,action):
        (repo/'STT/0909 전회2.md').write_text('changed after guard',encoding='utf-8')
        return original(state,action)
    monkeypatch.setattr(a,'_inputs',race)
    child(monkeypatch,'must not run')
    result=a.run_action(run,'assemble-note')
    assert result['status']!='done'
    assert not (Path(result['stdout_path']).parent/'process.json').exists()


@pytest.mark.parametrize('external_change', ['add', 'edit', 'delete'])
def test_between_actions_external_owned_change_is_not_adopted(tmp_path,monkeypatch,external_change):
    repo,run=ready(tmp_path,monkeypatch,'prepare-pack')
    pack=repo/'복습노트/0909'; pack.mkdir(parents=True)
    retained=pack/'정리노트_0909_Synthetic.html'; retained.write_text('original retained note')
    assert a.run_action(run,'prepare-pack')['status']=='done'
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],
        'assemble-note':dict(id='assemble-note',status='pending',dependencies=['prepare-pack'])}))
    trusted=f.load_state(run)['recovery']['last_inventory']
    if external_change=='add': (pack/'정리노트_0909_External.html').write_text('external work')
    elif external_change=='edit': retained.write_text('externally edited work')
    else: retained.unlink()
    external_inventory=a.inventory_pack(repo,'0909')
    child(monkeypatch,'must not launch')
    with pytest.raises(f.FlowError,match='inventory'):
        a.run_action(run,'assemble-note')
    assert f.load_state(run)['recovery']['last_inventory']==trusted
    assert not (run/'synthetic-child.py').exists()
    assert a.inventory_pack(repo,'0909')==external_inventory
    with pytest.raises(f.FlowError): a.recover_run(run)
    assert a.inventory_pack(repo,'0909')==external_inventory


def test_during_command_unexpected_owned_addition_is_not_adopted(tmp_path,monkeypatch):
    repo,run=ready(tmp_path,monkeypatch,'prepare-pack')
    assert a.run_action(run,'prepare-pack')['status']=='done'
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,actions={**s['actions'],
        'assemble-note':dict(id='assemble-note',status='pending',dependencies=['prepare-pack'])}))
    trusted=f.load_state(run)['recovery']['last_inventory']
    external=repo/'복습노트/0909/정리노트_0909_External.html'
    def command(state,action):
        note=a._paths(state)['note']
        return [sys.executable,'-c',f'from pathlib import Path; Path({str(note)!r}).parent.mkdir(parents=True,exist_ok=True); Path({str(note)!r}).write_text("note"); Path({str(external)!r}).write_text("external work")']
    monkeypatch.setattr(a,'action_argv',command)
    result=a.run_action(run,'assemble-note')
    assert result['status']=='recovery_required'
    assert f.load_state(run)['recovery']['last_inventory']==trusted
    assert a.reconcile_action(run,'assemble-note')['status']=='recovery_required'
    with pytest.raises(f.FlowError): a.recover_run(run)
    assert external.read_text()=='external work'


def svg_conversion_run(tmp_path,monkeypatch):
    import shutil
    repo,run=ready(tmp_path,monkeypatch,'convert-md')
    vendor=Path('.claude/skills/ec2-problem-explain/assets/vendor/pretendard')
    shutil.copytree(REPO/vendor,repo/vendor)
    note=a._paths(f.load_state(run))['note']; note.parent.mkdir(parents=True)
    note.write_text('<!doctype html><html><body><main><header class="hero"><h1>SVG fixture</h1></header>'
        '<section id="s1"><h2>Section</h2><article class="topic" id="topic-one"><h3>Topic</h3>'
        '<svg id="circuit/one" viewBox="0 0 10 10"><path d="M0 0L10 10"/></svg>'
        '<svg id="circuit/one" viewBox="0 0 10 10"><path d="M0 10L10 0"/></svg>'
        '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="2"/></svg>'
        '</article></section></main></body></html>',encoding='utf-8')
    figures=note.parent/'.assets/figures_0909'; figures.mkdir(parents=True)
    (figures/'obsolete.svg').write_text('previous generated svg')
    (figures/'keep.txt').write_text('preserved non-SVG asset')
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,recovery={'last_inventory':a.inventory_pack(repo,'0909')}))
    return repo,run


def test_conversion_rejects_unexpected_svg_added_during_actual_converter(tmp_path,monkeypatch):
    repo,run=svg_conversion_run(tmp_path,monkeypatch)
    trusted=f.load_state(run)['recovery']['last_inventory']
    original=a.action_argv
    extra=repo/'복습노트/0909/.assets/figures_0909/unrelated.svg'
    def command(state,action):
        argv=original(state,action)
        code=f'import subprocess; from pathlib import Path; result=subprocess.run({argv!r}); Path({str(extra)!r}).write_text("external svg"); raise SystemExit(result.returncode)'
        return [sys.executable,'-c',code]
    monkeypatch.setattr(a,'action_argv',command)
    result=a.run_action(run,'convert-md')
    assert result['status']=='recovery_required'
    assert f.load_state(run)['recovery']['last_inventory']==trusted
    assert a.reconcile_action(run,'convert-md')['status']=='recovery_required'
    with pytest.raises(f.FlowError): a.recover_run(run)
    assert extra.read_text()=='external svg'


def test_actual_converter_allows_only_derived_svg_names(tmp_path,monkeypatch):
    _,run=svg_conversion_run(tmp_path,monkeypatch)
    result=a.run_action(run,'convert-md')
    assert result['status']=='done',Path(result['stdout_path']).read_text(encoding='utf-8')
    started=json.loads(Path(result['stdout_path']).with_name('started.json').read_text())
    names={Path(name).name for name in started['write_set']['files'] if name.endswith('.svg')}
    assert names=={'circuit_one.svg','circuit_one-2.svg','note-fig-1.svg'}
    figures=a._paths(f.load_state(run))['pack']/'.assets/figures_0909'
    assert not (figures/'obsolete.svg').exists()
    assert (figures/'keep.txt').read_text()=='preserved non-SVG asset'
    assert {Path(item['path']).name for item in result['outputs'] if item['path'].endswith('.svg')}==names
