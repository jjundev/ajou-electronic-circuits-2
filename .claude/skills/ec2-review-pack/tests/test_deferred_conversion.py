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


def test_attempt_view_copies_only_adopted_files_and_checks_hashes(tmp_path):
    from hashlib import sha256
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    producer = tmp_path/'producer'
    producer.mkdir()
    note = producer/'note.html'
    note.write_bytes(b'adopted')
    (producer/'other').touch()
    record = {'root': producer, 'files': {'note.html': sha256(b'adopted').hexdigest()}}
    view = a.compose_candidate_view(repo, public, tmp_path/'consumer', {'assemble-note': record})
    assert view.work_file('note.html').read_bytes() == b'adopted'
    assert not view.work_file('other').exists()
    assert not public.exists()
    with pytest.raises(ValueError, match='producer|중복'):
        a.compose_candidate_view(repo, public, tmp_path/'duplicate', {'one': record, 'two': record})
    note.write_bytes(b'changed')
    assert view.work_file('note.html').read_bytes() == b'adopted'
    with pytest.raises(ValueError, match='hash'):
        a.compose_candidate_view(repo, public, tmp_path/'new', {'assemble-note': record})


def test_candidate_link_checks_use_course_sources_and_no_public_fallback(tmp_path):
    from check_html import broken_links, parse_html
    from pack_paths import PackPaths
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    public.mkdir(parents=True)
    (public/'missing.pdf').touch()
    (repo/'guide.html').write_text('<p id="go">Guide</p>')
    paths = PackPaths(repo, public, tmp_path/'candidate')
    paths.work_pack.mkdir()
    doc = parse_html('<a href="../../guide.html#go">Guide</a><a href="missing.pdf">old</a>')
    assert broken_links(doc, paths.work_pack, pack_paths=paths) == ['missing.pdf']


def test_candidate_converter_checks_repository_links_and_final_answer(tmp_path, monkeypatch):
    from hashlib import sha256
    repo, run = pending(tmp_path, monkeypatch)
    state = f.load_state(run)
    p = a._paths(state)
    p['note'].write_text(p['note'].read_text().replace('</article>', '<a href="../../guide.pdf">Guide</a></article>'))
    (repo/'guide.pdf').touch()
    public = p['pack']
    record = {'root': public, 'files': {p['note'].name: sha256(p['note'].read_bytes()).hexdigest()}}
    attempt = tmp_path/'attempt'
    view = a.compose_candidate_view(repo, public, attempt, {'assemble-note': record})
    outputs = a.candidate_action(state, 'convert-md', view, attempt)
    assert all(path.is_relative_to(view.work_pack) for path in outputs)
    assert p['md'].name in {path.name for path in outputs}
    from html2md import check_md
    md = view.work_file('.assets/'+p['md'].name)
    assert any(p['answer'].name in item for item in check_md(view.work_file(p['note'].name), md, pack_paths=view))
    view.work_file(p['answer'].name).touch()
    assert not check_md(view.work_file(p['note'].name), md, pack_paths=view)
    assert not p['md'].exists()


def test_candidate_note_verifies_assembled_image_and_stylesheet(tmp_path):
    from check_html import check_common, parse_html
    from pack_paths import PackPaths
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    public.mkdir(parents=True)
    (public/'plot.svg').touch()
    view = PackPaths(repo, public, tmp_path/'attempt')
    markup = '<html lang="ko"><link rel="stylesheet" href="missing.css"><img src="plot.svg"></html>'
    errors = check_common(parse_html(markup), markup, view.work_file('note.html'), pack_paths=view)
    assert {'missing.css', 'plot.svg'} == {p.detail for p in errors if p.code == 'missing-resource'}


def test_candidate_svg_and_srcset_resources_use_view(tmp_path):
    from check_html import check_common, parse_html
    from pack_paths import PackPaths
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    public.mkdir(parents=True)
    paths = PackPaths(repo, public, tmp_path/'candidate')
    paths.work_pack.mkdir()
    missing = {'external.svg#plot', 'old.svg', 'large.png', 'fallback.png'}
    for name in missing:
        (public/name.split('#')[0]).touch()
    paths.work_file('small.png').touch()
    markup = """<html lang="ko"><svg><image href="external.svg#plot"/><image xlink:href="old.svg"/>
        <use href="#plot"/><image href="data:image/png;base64,AAAA"/></svg>
        <picture><source srcset="small.png 300w, large.png 900w">
        <img srcset="data:image/png;base64,AAAA 1x, fallback.png 2x"></picture></html>"""
    errors = check_common(parse_html(markup), markup, paths.work_file('note.html'), pack_paths=paths)
    assert {p.detail for p in errors if p.code == 'missing-resource'} == missing
    for name in missing:
        paths.work_file(name.split('#')[0]).touch()
    assert not check_common(parse_html(markup), markup, paths.work_file('note.html'), pack_paths=paths)


def test_unrelated_machine_attempt_is_not_a_permanent_course_reference(tmp_path):
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    other_attempt = repo/'arbitrary-scratch'
    other_view = a.compose_candidate_view(repo, public, other_attempt, {})
    producer_file = other_view.work_file('plot.svg')
    producer_file.write_text('<svg/>')
    evidence = other_attempt/'evidence.txt'
    evidence.write_text('temporary proof')
    stable = repo/'ordinary-source/evidence.txt'
    stable.parent.mkdir()
    stable.write_text('course reference')
    consumer = a.compose_candidate_view(repo, public, repo/'elsewhere', {})
    assert consumer.source_file(str(stable)) == stable
    for private in (producer_file, evidence):
        with pytest.raises(ValueError, match='공개 경로'):
            consumer.source_file(str(private))
