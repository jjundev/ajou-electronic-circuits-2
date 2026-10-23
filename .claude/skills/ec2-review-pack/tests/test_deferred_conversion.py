"""Actual converter boundary for the planned-but-unpublished answer PDF."""
import json
from pathlib import Path
import pytest
from test_pack_actions import svg_conversion_run
import pack_actions as a
import pack_flow as f


def pending(tmp_path,monkeypatch,other=None):
    repo,run=svg_conversion_run(tmp_path,monkeypatch)
    manifest=run/'manifest.json'; m=json.loads(manifest.read_text(encoding='utf-8'))
    m['problems']=[{'id':'P10.02'}]; manifest.write_text(json.dumps(m),encoding='utf-8')
    p=a._paths(f.load_state(run)); note=p['note']
    extra=f'<a href="{p["answer"].name}">Answer</a>'
    if other: extra+=f'<a href="{other}">Other</a>'
    note.write_text(note.read_text(encoding='utf-8').replace('</article>',extra+'</article>'),encoding='utf-8')
    state=f.load_state(run)
    f.update_state(run,state['revision'],lambda s: dict(s,recovery={'last_inventory':a.inventory_pack(repo,'0909')}))
    return repo,run


def test_actual_provisional_conversion_defers_only_planned_answer(tmp_path,monkeypatch):
    _,run=pending(tmp_path,monkeypatch)
    result=a.run_action(run,'convert-md')
    assert result['status']=='done'
    assert not a._paths(f.load_state(run))['answer'].exists()
    assert len([x for x in result['outputs'] if x['path'].endswith('.svg')])==3


@pytest.mark.parametrize('other',['missing.pdf','nested/복습문제_0909_Synthetic-답안.pdf','복습문제_0909_Synthetic-답안.pdf#anchor'])
def test_other_missing_links_are_not_deferred(tmp_path,monkeypatch,other):
    _,run=pending(tmp_path,monkeypatch,other)
    result=a.run_action(run,'convert-md')
    assert result['status']!='done'
    assert '링크 파일 없음' in Path(result['stdout_path']).read_text(encoding='utf-8')


def test_final_postcondition_strictly_checks_md_without_writing(tmp_path,monkeypatch):
    _,run=pending(tmp_path,monkeypatch)
    a.run_action(run,'convert-md')
    state=f.load_state(run); p=a._paths(state)
    audit=run/'active-audit.json'; audit.write_text('{}'); state['active_audit']=str(audit)
    files=[p['note'],p['md'],*list((p['pack']/'.assets/figures_0909').glob('*.svg'))]
    before={str(x):x.read_bytes() for x in files}
    with pytest.raises(f.FlowError,match='MD'):
        a._postconditions(state,'final-check',run)
    p['answer'].write_bytes(b'%PDF-1.7\nsynthetic link-target fixture\n%%EOF')
    assert p['md'] in a._postconditions(state,'final-check',run)
    assert {str(x):x.read_bytes() for x in files}==before


def failed_legacy_conversion(tmp_path,monkeypatch):
    repo,run=pending(tmp_path,monkeypatch)
    original=a.action_argv
    def legacy(state,action):
        argv=original(state,action)
        if '--defer-answer-pdf' in argv:
            argv.remove('--defer-answer-pdf'); index=argv.index('--manifest'); del argv[index:index+2]
        return argv
    with monkeypatch.context() as patch:
        patch.setattr(a,'action_argv',legacy)
        failed=a.run_action(run,'convert-md')
    assert failed['exit_code']==1 and failed['status']=='recovery_required'
    return repo,run,failed


def test_stopped_failed_conversion_retries_with_new_attempt_and_same_budget(tmp_path,monkeypatch):
    _,run,failed=failed_legacy_conversion(tmp_path,monkeypatch)
    folder=Path(failed['stdout_path']).parent
    evidence={str(x):x.read_bytes() for x in folder.rglob('*') if x.is_file()}
    before=f.load_state(run)['fix_rounds']
    p=a._paths(f.load_state(run)); published=[p['note'],p['md'],*list((p['pack']/'.assets/figures_0909').glob('*.svg'))]
    published_bytes={str(x):x.read_bytes() for x in published}
    result=a.run_action(run,'convert-md')
    assert result['status']=='done' and result['attempt']!=failed['attempt']
    assert {path:Path(path).read_bytes() for path in evidence}==evidence
    assert f.load_state(run)['fix_rounds']==before
    assert {path:Path(path).read_bytes() for path in published_bytes}==published_bytes
    assert f.load_state(run)['actions']['convert-md']['history'][-1]['exit_code']==1


@pytest.mark.parametrize('damage',['no-stop','external','input','untrusted','no-baseline','child-extracted'])
def test_retry_rejects_uncertain_or_changed_failed_attempt(tmp_path,monkeypatch,damage):
    repo,run,failed=failed_legacy_conversion(tmp_path,monkeypatch)
    folder=Path(failed['stdout_path']).parent
    if damage=='no-stop': (folder/'stopped.json').unlink()
    elif damage=='external': (repo/'복습노트/0909/정리노트_0909_External.html').write_text('external')
    elif damage=='input': (repo/'STT/0909 전회2.md').write_text('changed')
    else:
        state=f.load_state(run)
        def change(s):
            if damage=='child-extracted':
                child=run/'problem-explain/extracted'; child.mkdir(parents=True)
                (child/'run.json').write_text('{"version":1,"targets":[]}')
                s['explain_run']=str(child)
            elif damage=='no-baseline': s['recovery'].pop('last_inventory')
            else: s['actions']['convert-md']['inventory_trusted']=False
            return s
        f.update_state(run,state['revision'],change)
    with pytest.raises(f.FlowError): a.run_action(run,'convert-md')
    assert f.load_state(run)['actions']['convert-md']['attempt']==failed['attempt']


def test_deferral_cli_requires_matching_manifest_note_identity(tmp_path,monkeypatch):
    import subprocess
    import sys
    _,run=pending(tmp_path,monkeypatch)
    state=f.load_state(run); note=a._paths(state)['note']
    manifest=run/'wrong-manifest.json'; data=json.loads((run/'manifest.json').read_text()); data['slug']='Other'
    manifest.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,str(Path(state['repo'])/'.claude/skills/ec2-review-pack/scripts/html2md.py'),
        str(note),'--check','--manifest',str(manifest),'--defer-answer-pdf'],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==2 and 'manifest must identify this note' in result.stderr
    assert not a._paths(state)['md'].exists()


def test_provisional_checker_still_rejects_missing_image(tmp_path,monkeypatch):
    from html2md import check_md
    _,run=pending(tmp_path,monkeypatch)
    assert a.run_action(run,'convert-md')['status']=='done'
    p=a._paths(f.load_state(run))
    with p['md'].open('a',encoding='utf-8') as stream: stream.write('\n![missing](missing.svg)\n')
    errors=check_md(p['note'],p['md'],deferred_answer=p['answer'].name)
    assert any('그림 없음' in error for error in errors)
