import hashlib
import multiprocessing
from pathlib import Path

import pytest
from _util import SCRIPTS
import manifest
from pack_files import inventory_pack
from pack_paths import PackPaths

DATE = '0923'
NOTE = '정리노트_0923_X.html'
MD = '.assets/정리노트_0923_X.md'
ANSWER = '복습문제_0923_X-답안.pdf'


def put(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def transaction(tmp_path):
    repo = tmp_path / 'repo'
    public = repo / '복습노트' / DATE
    candidate = tmp_path / 'candidate'
    for name in (NOTE, MD):
        put(public, name, b'initial')
        put(candidate, name, b'candidate')
    paths = PackPaths(repo, public, candidate)
    return paths, tmp_path / 'run', dict(expected=inventory_pack(repo, DATE),
        candidate_inventory={name: digest(b'candidate') for name in (NOTE, MD)}, verify=lambda root: None)


def test_publish_rejects_changed_baseline(transaction):
    import pack_publication as pub
    paths, run, options = transaction
    file = put(paths.public_pack, NOTE, b'edited')
    conflict = pub.publish_pack(paths, run, **options)
    assert conflict['error_code'] == 'publication_conflict'
    assert file.read_bytes() == b'edited'


def _publisher(paths, run, options, queue, entered, release, started):
    import pack_publication as pub
    def verify(root):
        if root == paths.work_pack and entered:
            entered.set()
            if not release.wait(15):
                raise ValueError('test synchronization timed out')
    started.set()
    queue.put(pub.publish_pack(paths, run, verify=verify, **options))


def test_same_date_publishers_serialize(transaction):
    paths, run, options = transaction
    opts = {k: v for k, v in options.items() if k != 'verify'}
    ctx = multiprocessing.get_context('spawn')
    entered, release, queue = ctx.Event(), ctx.Event(), ctx.Queue()
    started = ctx.Event()
    first_started = ctx.Event()
    p1 = ctx.Process(target=_publisher, args=(paths, run, opts, queue, entered, release, first_started))
    p2 = ctx.Process(target=_publisher, args=(paths, run.with_name('second'), opts, queue, None, None, started))
    p1.start()
    try:
        assert entered.wait(10)
        p2.start()
        assert started.wait(10)
        p2.join(0.3)
        assert p2.is_alive()
        assert inventory_pack(paths.repo, DATE) == opts['expected']
    finally:
        release.set()
        p1.join(10)
        if p2.pid:
            p2.join(10)
    assert p1.exitcode == p2.exitcode == 0
    results = [queue.get(timeout=2), queue.get(timeout=2)]
    assert {r.get('error_code') or r['status'] for r in results} == {'published', 'publication_conflict'}


class Crash(BaseException):
    pass


def crash_after_replace(paths, run, options, monkeypatch):
    import pack_publication as pub
    replace = pub.os.replace
    def interrupt(src, dst):
        replace(src, dst)
        if Path(dst).is_relative_to(paths.public_pack):
            raise Crash
    with monkeypatch.context() as patch:
        patch.setattr(pub.os, 'replace', interrupt)
        with pytest.raises(Crash):
            pub.publish_pack(paths, run, **options)
    return run / 'publication/journal.json'


def test_reconcile_after_replace_before_checkpoint(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    journal = crash_after_replace(paths, run, options, monkeypatch)
    before = options['expected']
    assert inventory_pack(paths.repo, DATE) != before
    recovered = pub.reconcile_publication(paths, journal, verify=options['verify'])
    assert recovered['status'] == 'restored'
    assert inventory_pack(paths.repo, DATE) == before


def test_reconcile_preserves_unexpected_bytes(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    journal = crash_after_replace(paths, run, options, monkeypatch)
    user_bytes = b'changed after crash'
    external_file = put(paths.public_pack, NOTE, user_bytes)
    assert pub.reconcile_publication(paths, journal, verify=options['verify'])['status'] == 'recovery_required'
    assert external_file.read_bytes() == user_bytes


def test_zero_problem_replacement_retains_unowned_files(transaction):
    import pack_publication as pub
    paths, run, options = transaction
    stale_owned_answer = put(paths.public_pack, ANSWER, b'stale')
    put(paths.public_pack, '.assets/figures_0923/old.svg', b'old')
    original_unowned = b'vendor bytes'
    unowned_file = put(paths.public_pack, '.assets/vendor/test', original_unowned)
    options['expected'] = inventory_pack(paths.repo, DATE)
    verified = []
    result = pub.publish_pack(paths, run, **dict(options, verify=verified.append))
    assert result['status'] == 'published'
    assert verified == [paths.work_pack, paths.public_pack]
    assert not stale_owned_answer.exists()
    assert unowned_file.read_bytes() == original_unowned
    assert inventory_pack(paths.repo, DATE) == result['after']


def test_recovery_requires_verified_backup_and_active_journal(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    journal = crash_after_replace(paths, run, options, monkeypatch)
    current = inventory_pack(paths.repo, DATE)
    again = pub.publish_pack(paths, run.with_name('other'), **dict(options, expected=current))
    assert again['status'] == 'recovery_required'
    put(journal.parent / 'before', MD, b'broken backup')
    assert pub.reconcile_publication(paths, journal, verify=options['verify'])['status'] == 'recovery_required'
    assert inventory_pack(paths.repo, DATE) == current


def test_reject_unowned_candidate_and_unsafe_run(transaction):
    import pack_publication as pub
    paths, run, options = transaction
    put(paths.work_pack, '.assets/vendor/no', b'x')
    with pytest.raises(ValueError):
        pub.publish_pack(paths, run, **options)
    with pytest.raises(ValueError):
        pub.publish_pack(paths, paths.public_pack / 'run', **options)
    assert not (paths.public_pack / 'run').exists()


def test_publication_verifier_requires_bound_pdf_review(transaction, monkeypatch):
    import pack_actions
    import subprocess
    paths, _, _ = transaction
    m = dict(range=DATE, slug='X', problems=[{'id': 'P10.02'}])
    checked = []
    monkeypatch.setattr(pack_actions, 'verify_note_view', lambda m, view, audit: checked.append(view.work_pack))
    def record(argv, **kwargs):
        checked.append([str(arg) for arg in argv])
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(subprocess, 'run', record)
    with pytest.raises(ValueError, match='review'):
        pack_actions.publication_verifier(m, paths, Path('audit'))(paths.public_pack)
    review = Path('accepted/answer-review.json')
    check = pack_actions.publication_verifier(m, paths, Path('audit'), answer_review=review)
    for root in (paths.work_pack, paths.public_pack):
        check(root)
        args = checked[-1]
        assert checked[-2] == root
        assert args[args.index('--review') + 1] == str(review)
        assert args[args.index('--pdf') + 1] == str(root / ANSWER)
        assert args[args.index('--ids') + 1] == 'P10.02'
        assert args[args.index('--overlay') + 1] == str(root / '.assets/자료_문제설명_0923_X/answer-overlay.json')


def test_out_of_order_candidate_bytes_cannot_be_rolled_back(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    third = '문제설명_0923_X.html'
    put(paths.public_pack, third, b'old')
    put(paths.work_pack, third, b'candidate')
    options['candidate_inventory'][third] = digest(b'candidate')
    options['expected'] = inventory_pack(paths.repo, DATE)
    journal = crash_after_replace(paths, run, options, monkeypatch)
    # Simulate another program installing a later file with identical candidate
    # bytes while the first replacement has no completion checkpoint.
    put(paths.public_pack, NOTE, b'candidate')
    current = inventory_pack(paths.repo, DATE)
    assert pub.reconcile_publication(paths, journal, verify=options['verify'])['status'] == 'recovery_required'
    assert inventory_pack(paths.repo, DATE) == current


def test_fully_applied_final_intent_is_validated_and_completed(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    (paths.work_pack / MD).write_bytes(b'initial')
    options['candidate_inventory'][MD] = digest(b'initial')
    journal = crash_after_replace(paths, run, options, monkeypatch)
    verified = []
    result = pub.reconcile_publication(paths, journal, verify=verified.append)
    assert result['status'] == 'published'
    assert verified == [paths.public_pack]


def test_second_crash_during_restore_is_resumable(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    journal = crash_after_replace(paths, run, options, monkeypatch)
    replace = pub.os.replace
    def crash(src, dst):
        replace(src, dst)
        if Path(dst).is_relative_to(paths.public_pack):
            raise Crash
    with monkeypatch.context() as patch:
        patch.setattr(pub.os, 'replace', crash)
        with pytest.raises(Crash):
            pub.reconcile_publication(paths, journal, verify=options['verify'])
    result = pub.reconcile_publication(paths, journal, verify=options['verify'])
    assert result['status'] == 'restored'
    assert inventory_pack(paths.repo, DATE) == options['expected']


def test_legacy_live_action_uses_date_lock(tmp_path):
    import pack_actions
    import pack_publication
    from pack_support import action_run
    repo, run = action_run(tmp_path)
    pack = repo / '복습노트/0909'
    with pack_publication.publication_lock(pack):
        with pytest.raises(ValueError, match='lock'):
            pack_actions.run_action(run, 'assemble-note')


def test_external_explanation_and_concept_use_pending_date(transaction, monkeypatch):
    import subprocess
    import sys
    paths, run, opts = transaction
    crash_after_replace(paths, run, opts, monkeypatch)
    for skill, module, expr in [
            ('ec2-problem-explain', 'epe_files', 'm.publication_lock([p/"x.html"])'),
            ('ec2-concept-check', 'concept', 'm.publication_lock(p)')]:
        scripts = SCRIPTS.parents[1] / skill / 'scripts'
        code = ("import sys; from pathlib import Path; "
                "sys.path.insert(0, sys.argv[1]); p=Path(sys.argv[2]); "
                f"import {module} as m\nwith {expr}: print('accepted')\n")
        result = subprocess.run([sys.executable, '-c', code, str(scripts), str(paths.public_pack)],
                                capture_output=True, text=True, timeout=10)
        assert result.returncode != 0 and 'recovery' in result.stderr


def test_directory_in_place_of_a_named_file_is_not_owned(transaction):
    import pack_publication as pub
    paths, run, options = transaction
    user_file = put(paths.public_pack, ANSWER + '/keep', b'user')
    options['expected'] = inventory_pack(paths.repo, DATE)
    with pytest.raises(ValueError):
        pub.publish_pack(paths, run, **options)
    assert user_file.read_bytes() == b'user'


def test_no_public_intent_crash_can_be_settled(transaction, monkeypatch):
    import pack_publication as pub
    paths, run, options = transaction
    save = pub._save
    def crash_before_register(path, data):
        if path.name.endswith('.publication.json'):
            raise Crash
        save(path, data)
    with monkeypatch.context() as patch:
        patch.setattr(pub, '_save', crash_before_register)
        with pytest.raises(Crash):
            pub.publish_pack(paths, run, **options)
    result = pub.reconcile_publication(paths, run / 'publication/journal.json', verify=options['verify'])
    assert result['status'] == 'restored'
    assert inventory_pack(paths.repo, DATE) == options['expected']


def test_zero_problem_final_gate_rejects_stale_owned_workbook(transaction, monkeypatch):
    import pack_actions
    paths, _, _ = transaction
    monkeypatch.setattr(pack_actions, 'verify_note_view', lambda *args: None)
    put(paths.work_pack, ANSWER, b'unexpected')
    check = pack_actions.publication_verifier(dict(range=DATE, slug='X', problems=[]), paths, Path('audit'))
    with pytest.raises(ValueError, match='unexpected'):
        check(paths.work_pack)


def test_raw_unicode_baseline_is_preserved_in_journal(transaction, monkeypatch):
    import unicodedata
    import pack_publication as pub
    paths, run, options = transaction
    nfd = unicodedata.normalize('NFD', ANSWER)
    put(paths.public_pack, nfd, b'old')
    options['expected'] = inventory_pack(paths.repo, DATE)
    journal = crash_after_replace(paths, run, options, monkeypatch)
    result = pub.reconcile_publication(paths, journal, verify=options['verify'])
    assert result['before'] == options['expected']
    assert inventory_pack(paths.repo, DATE) == options['expected']


def test_final_public_verifier_checks_real_overlay_pdf_and_evidence(tmp_path, monkeypatch):
    import json
    import pymupdf
    import pack_actions
    import sys
    fixtures = str(SCRIPTS.parents[3] / 'workbook/tests')
    sys.path.append(fixtures)
    try:
        from overlay_fixture import OverlayBundle
    finally:
        # workbook/paths.py installs its own tool-module lookup once per process.
        # Keep that lookup when removing this fixture directory.
        sys.path.remove(fixtures)
    bundle = OverlayBundle(tmp_path)
    m = dict(range='1008', slug='샘플', problems=[dict(id=pid) for pid in bundle.ids])
    paths = PackPaths(bundle.repo, bundle.stage)
    for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
        with pymupdf.open() as pdf:
            pdf.new_page(width=1920, height=1080)
            pdf.save(bundle.stage / name)
    evidence = [put(tmp_path, 'page.png', bundle.asset.read_bytes()), put(tmp_path, 'review.md', b'fixture only')]
    review = tmp_path / 'answer-review.json'
    review.write_text(json.dumps(dict(schema_version=1, reviewer='fixture', status='pass', overflow=[],
        pdf_sha256=digest((bundle.stage / manifest.answer_pdf_name(m)).read_bytes()),
        overlay_sha256=digest(bundle.path.read_bytes()), learning_style_sha256=bundle.overlay['learning_style']['sha256'],
        evidence=[dict(path=p.name, sha256=digest(p.read_bytes())) for p in evidence])))
    # The focused integration runs the actual final PDF and overlay validator.
    # HTML/MD gates have separate fixtures and are covered by verify_note_view.
    monkeypatch.setattr(pack_actions, 'verify_note_view', lambda *args: None)
    verify = pack_actions.publication_verifier(m, paths, Path('audit'), answer_review=review)
    verify(bundle.stage)
    evidence[0].write_bytes(b'changed page review')
    with pytest.raises(ValueError, match='Evidence changed'):
        verify(bundle.stage)


def test_swapped_public_parent_cannot_redirect_writes(transaction):
    import shutil
    import pack_publication as pub
    paths, run, opts = transaction
    notes = paths.public_pack.parent
    external = run.parent / 'external-notes'
    shutil.copytree(notes, external)
    def swap(root):
        if root == paths.work_pack:
            notes.rename(run.parent / 'original-notes')
            notes.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError):
        pub.publish_pack(paths, run, **dict(opts, verify=swap))
    assert (external / DATE / NOTE).read_bytes() == b'initial'


def test_delegated_command_reuses_real_lock_handle(transaction):
    import os
    import subprocess
    import sys
    import pack_publication as pub
    if os.name == 'nt':
        pytest.skip('Unix open file description inheritance')
    paths, _, _ = transaction
    code = ("import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from pack_publication import publication_lock\n"
            "with publication_lock(Path(sys.argv[2])): print('verified')\n")
    with pub.publication_lock(paths.public_pack):
        proc = subprocess.run([sys.executable, '-c', code, str(SCRIPTS), str(paths.public_pack)],
                              **pub.child_lock_options(paths.public_pack), capture_output=True, text=True, timeout=5)
    assert proc.returncode == 0 and proc.stdout.strip() == 'verified', proc.stderr


def test_file_only_receipt_cannot_introduce_unadopted_empty_tree(transaction):
    import pack_publication as pub
    paths, run, opts = transaction
    (paths.work_pack / '.assets/figures_0923/unknown').mkdir(parents=True)
    with pytest.raises(ValueError, match='inventory'):
        pub.publish_pack(paths, run, **opts)
    assert inventory_pack(paths.repo, DATE) == opts['expected']


def test_swapped_run_cannot_install_journal_in_unowned_directory(transaction):
    import pack_publication as pub
    paths, run, opts = transaction
    run.mkdir()
    unowned = paths.public_pack / '.assets/vendor'
    unowned.mkdir()
    def swap(root):
        if root == paths.work_pack:
            run.rmdir()
            run.symlink_to(unowned, target_is_directory=True)
    with pytest.raises(ValueError):
        pub.publish_pack(paths, run, **dict(opts, verify=swap))
    assert not (unowned / 'publication').exists()
    assert inventory_pack(paths.repo, DATE) == opts['expected']


def _die_during_publication(paths, run, expected, candidate):
    import os
    import pack_publication as pub
    replace = os.replace
    def abrupt(src, dst):
        replace(src, dst)
        if Path(dst).is_relative_to(paths.public_pack):
            os._exit(19)
    pub.os.replace = abrupt
    pub.publish_pack(paths, run, expected=expected, candidate_inventory=candidate, verify=lambda root: None)


def test_process_exit_releases_date_and_keeps_undo_evidence(transaction):
    import pack_publication as pub
    paths, run, opts = transaction
    child = multiprocessing.get_context('spawn').Process(target=_die_during_publication, args=(
        paths, run, opts['expected'], opts['candidate_inventory']))
    child.start()
    child.join(10)
    assert child.exitcode == 19
    record = pub.reconcile_publication(paths, run / 'publication/journal.json', verify=opts['verify'])
    assert record['status'] == 'restored'
    assert inventory_pack(paths.repo, DATE) == opts['expected']
