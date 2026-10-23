import json
import unicodedata as u
import pytest
from _util import SCRIPTS
from pack_flow import FlowError
from pack_files import prepare_pack, inventory_pack, recover_pack

@pytest.fixture
def env(tmp_path):
    repo, run = tmp_path/'repo', tmp_path/'run'
    (repo/'STT').mkdir(parents=True); run.mkdir()
    pack=repo/'복습노트/0923'; (pack/'.assets').mkdir(parents=True)
    manifest=run/'manifest.json'
    manifest.write_text(json.dumps({'range':'0923','slug':'New','problems':[]}))
    return repo,run,pack,manifest

def put(pack, rel, data=b'old'):
    p=pack/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); return p

def test_prepare_keeps_first_backups(env):
    repo,run,pack,m=env; put(pack,'정리노트_0923_Old.html')
    prepare_pack(repo,run,m); before=(run/'basic-pack-backup.json').read_bytes()
    prepare_pack(repo,run,m)
    assert (run/'basic-pack-backup.json').read_bytes()==before

def test_failed_second_backup_preserves_pack(env,monkeypatch):
    import pack_files
    repo,run,pack,m=env; p=put(pack,'정리노트_0923_Old.html'); put(pack,'문제설명_0923_Old.html')
    original=pack_files.shutil.copy2
    def fail(src,dst,*a,**k):
        if '문제설명' in str(src): raise OSError('copy failed')
        return original(src,dst,*a,**k)
    monkeypatch.setattr(pack_files.shutil,'copy2',fail)
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    assert p.read_bytes()==b'old'

def test_slug_change_and_zero_problems_cleanup_only_owned(env):
    repo,run,pack,m=env
    for rel in ['정리노트_0923_Old.html','복습문제_0923_Old-답안.pdf','문제설명_0923_Old.html']: put(pack,rel)
    unrelated=put(pack,'정리노트_0923_Old-feedback.txt',b'unrelated')
    prepare_pack(repo,run,m)
    assert unrelated.read_bytes()==b'unrelated'
    assert not (pack/'정리노트_0923_Old.html').exists()

def test_nfd_round_trip_and_nfc_collision(env):
    repo,run,pack,m=env; rel=u.normalize('NFD','정리노트_0923_Old.html'); put(pack,rel,b'original')
    prepare_pack(repo,run,m); recover_pack(repo,run,'0923',inventory_pack(repo,'0923'))
    assert (pack/rel).read_bytes()==b'original'
    other=pack/u.normalize('NFC',rel)
    if other.exists(): pytest.skip('filesystem normalizes Unicode names')
    other.write_bytes(b'collision')
    with pytest.raises(FlowError): inventory_pack(repo,'0923')

def test_symlink_escape_rejected(env):
    repo,run,pack,m=env; outside=run/'outside'; outside.write_bytes(b'outside')
    try: (pack/'정리노트_0923_Old.html').symlink_to(outside)
    except OSError as e: pytest.skip(f'symlink privilege unavailable: {e}')
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    assert outside.read_bytes()==b'outside'

def test_external_edit_blocks_recovery(env):
    repo,run,pack,m=env; prepare_pack(repo,run,m); expected=inventory_pack(repo,'0923')
    put(pack,'정리노트_0923_New.html',b'external')
    with pytest.raises(FlowError): recover_pack(repo,run,'0923',expected)

def test_tampered_backup_does_not_remove_current(env):
    repo,run,pack,m=env; put(pack,'정리노트_0923_Old.html'); prepare_pack(repo,run,m)
    record=json.loads((run/'basic-pack-backup.json').read_text()); ( __import__('pathlib').Path(record['backup'])/'정리노트_0923_Old.html').write_bytes(b'tamper')
    p=put(pack,'정리노트_0923_New.html',b'current')
    with pytest.raises(FlowError): recover_pack(repo,run,'0923',inventory_pack(repo,'0923'))
    assert p.read_bytes()==b'current'

def test_recovery_preserves_empty_dirs(env):
    repo,run,pack,m=env; (pack/'.assets/figures_0923/empty').mkdir(parents=True)
    prepare_pack(repo,run,m); recover_pack(repo,run,'0923',inventory_pack(repo,'0923'))
    assert (pack/'.assets/figures_0923/empty').is_dir()

@pytest.mark.parametrize('bad',['','<range>','923'])
def test_bad_range_and_repo_fail(env,bad):
    repo,run,pack,m=env
    m.write_text(json.dumps({'range':bad,'slug':'A','problems':[]}))
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    assert not list(run.glob('previous-*'))
    with pytest.raises(FlowError): prepare_pack(repo/'missing',run,m)

@pytest.mark.parametrize('had_inputs',[True,False])
def test_title_selection_audit_and_bytes_restore_together(env,had_inputs):
    repo,run,pack,m=env
    original={'정리노트_0923_Old.html':b'old coherent note', '.assets/정리노트_0923_Old.md':b'old md', '복습문제_0923_Old-문제.pdf':b'%PDF problems', '복습문제_0923_Old-답안.pdf':b'%PDF answers', '.assets/figures_0923/a.svg':b'<svg/>', '.assets/problems.txt':b'E9.01 | old'}
    inputs=['.assets/display-titles.json','.assets/selection.json','.pack/selection-review.json']
    if had_inputs: original.update({rel:rel.encode() for rel in inputs})
    for rel,data in original.items(): put(pack,rel,data)
    unrelated=put(pack,'interactive.html',b'unrelated')
    other=put(repo/'복습노트/0918','정리노트_0918_Old.html',b'other')
    prepare_pack(repo,run,m)
    record=json.loads((run/'basic-pack-backup.json').read_text(encoding='utf-8'))
    import hashlib
    for rel,data in original.items(): assert record['files'][rel]==hashlib.sha256(data).hexdigest()
    for rel in inputs: put(pack,rel,b'new')
    put(pack,'정리노트_0923_New.html',b'unfinished')
    result=recover_pack(repo,run,'0923',inventory_pack(repo,'0923'))
    assert result['status']=='restored'
    assert all((pack/rel).read_bytes()==data for rel,data in original.items())
    assert all((pack/rel).exists()==had_inputs for rel in inputs)
    assert unrelated.read_bytes()==b'unrelated'
    assert other.read_bytes()==b'other'


def test_cleanup_preserves_unrecorded_owned_file(env):
    repo,run,pack,m=env; put(pack,'정리노트_0923_Old.html')
    prepare_pack(repo,run,m)
    unrecorded=put(pack,'정리노트_0923_Unrecorded.html',b'unrecorded')
    prepare_pack(repo,run,m)
    assert unrecorded.read_bytes()==b'unrecorded'

def test_cleanup_failure_restores_only_paths_touched_this_call(env, monkeypatch):
    repo,run,pack,m=env
    m.write_text(json.dumps({'range':'0923','slug':'Keep','problems':[]}))
    note=put(pack,'정리노트_0923_Keep.html',b'initial note')
    problem_list=put(pack,'.assets/problems.txt',b'initial ids')
    first=put(pack,'정리노트_0923_A.html',b'stale a')
    second=put(pack,'정리노트_0923_Z.html',b'stale z')
    prepare_pack(repo,run,m)
    note.write_bytes(b'current note'); problem_list.write_bytes(b'current ids')
    first.write_bytes(b'stale a'); second.write_bytes(b'stale z')
    before={p.relative_to(pack).as_posix():p.read_bytes() for p in pack.rglob('*') if p.is_file()}
    original_unlink=type(second).unlink
    def fail_second(path,*args,**kwargs):
        if path==second: raise PermissionError('synthetic delete failure')
        return original_unlink(path,*args,**kwargs)
    monkeypatch.setattr(type(second),'unlink',fail_second)
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    assert {p.relative_to(pack).as_posix():p.read_bytes() for p in pack.rglob('*') if p.is_file()}==before


def test_missing_second_backup_retry_rejects_changed_first_inventory(env, monkeypatch):
    import pack_files
    repo,run,pack,m=env
    note=put(pack,'정리노트_0923_Old.html',b'first note')
    explanation=put(pack,'문제설명_0923_Old.html',b'first explanation')
    original_copy=pack_files.shutil.copy2
    def fail_explanation(src,dst,*args,**kwargs):
        if src==explanation: raise OSError('synthetic second-backup failure')
        return original_copy(src,dst,*args,**kwargs)
    monkeypatch.setattr(pack_files.shutil,'copy2',fail_explanation)
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    basic=(run/'basic-pack-backup.json').read_bytes()
    monkeypatch.setattr(pack_files.shutil,'copy2',original_copy)
    explanation.write_bytes(b'external replacement')
    with pytest.raises(FlowError,match='inventory|changed'): prepare_pack(repo,run,m)
    assert note.read_bytes()==b'first note'
    assert explanation.read_bytes()==b'external replacement'
    assert (run/'basic-pack-backup.json').read_bytes()==basic
    assert not (run/'explanations-backup.json').exists()


@pytest.mark.parametrize('problems,previous_ids,keeps_answer',[
    ([{'id':'E9.01'}],b'E9.01 | old\n',True),
    ([{'id':'E9.02'}],b'E9.01 | old\n',False),
    ([],b'E9.01 | old\n',False),
])
def test_same_slug_and_non_owned_matrix(env,problems,previous_ids,keeps_answer):
    repo,run,pack,m=env
    m.write_text(json.dumps({'range':'0923','slug':'A','problems':problems}))
    owned=('정리노트_0923_A.html','정리노트_0923_Old.html','.assets/정리노트_0923_A.md',
           '.assets/정리노트_0923_Old.md','복습문제_0923_A-문제.pdf','복습문제_0923_A-답안.pdf',
           '복습문제_0923_Old-문제.pdf','복습문제_0923_Old-답안.pdf')
    preserved=('정리노트_0923_Old-feedback.txt','복습문제_0923_Old-feedback.pdf',
               '.assets/정리노트_0923_Old-feedback.txt','.assets/복습문제_0923_Old-답안.pdf',
               '정리노트_0918_Old.html','.assets/정리노트_0918_Old.md')
    for rel in (*owned,*preserved): put(pack,rel,rel.encode())
    put(pack,'.assets/problems.txt',previous_ids)
    other=put(repo/'복습노트/0918','정리노트_0918_A.html',b'other date')
    prepare_pack(repo,run,m)
    retained={'정리노트_0923_A.html','.assets/정리노트_0923_A.md'}
    if problems: retained.add('복습문제_0923_A-문제.pdf')
    if keeps_answer: retained.add('복습문제_0923_A-답안.pdf')
    assert all((pack/rel).exists()==(rel in retained) for rel in owned)
    assert all((pack/rel).read_bytes()==rel.encode() for rel in preserved)
    assert other.read_bytes()==b'other date'

def test_missing_second_backup_retry_reuses_matching_first_state(env, monkeypatch):
    import pack_files
    repo,run,pack,m=env
    note=put(pack,'정리노트_0923_Old.html',b'first note')
    explanation=put(pack,'문제설명_0923_Old.html',b'first explanation')
    original_copy=pack_files.shutil.copy2
    def fail_explanation(src,dst,*args,**kwargs):
        if src==explanation: raise OSError('synthetic second-backup failure')
        return original_copy(src,dst,*args,**kwargs)
    monkeypatch.setattr(pack_files.shutil,'copy2',fail_explanation)
    with pytest.raises(FlowError): prepare_pack(repo,run,m)
    basic=(run/'basic-pack-backup.json').read_bytes()
    first_inventory=(run/'pack-first-inventory.json').read_bytes()
    monkeypatch.setattr(pack_files.shutil,'copy2',original_copy)
    prepare_pack(repo,run,m)
    assert (run/'basic-pack-backup.json').read_bytes()==basic
    assert (run/'pack-first-inventory.json').read_bytes()==first_inventory
    recover_pack(repo,run,'0923',inventory_pack(repo,'0923'))
    assert note.read_bytes()==b'first note'
    assert explanation.read_bytes()==b'first explanation'
