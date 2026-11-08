"""State durability, process locking, and explicit input provenance."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from _util import SCRIPTS
from pack_support import make_run
import pack_flow as flow


def test_init_rejects_nonempty_run(tmp_path):
    repo, run = make_run(tmp_path)
    before = (run / "run-status.json").read_bytes()
    with pytest.raises(flow.FlowError, match="nonempty"):
        flow.init_run(repo, run, "0909", allow_tmp=True)
    assert (run / "run-status.json").read_bytes() == before


def test_snapshot_uses_explicit_repo(tmp_path):
    repo, run = make_run(tmp_path, lite=True)
    profile = repo / ".claude/skills/ec2-review-pack/references/solution-style.md"
    profile.write_bytes(profile.read_bytes() + b"\nexplicit repo provenance\n")
    run = tmp_path / "second run"
    flow.init_run(repo, run, "0909", lite=True, allow_tmp=True)
    state = flow.load_state(run)
    assert state["schema_version"] == 1 and state["revision"] == 0
    assert state["fix_rounds"] == {"content": 0, "machine_browser": 0}
    snapshot = json.loads((run / "learning-style.json").read_text(encoding="utf-8"))
    assert snapshot["sha256"] == hashlib.sha256((repo / snapshot["path"]).read_bytes()).hexdigest()
    assert state["repo"] == str(repo.resolve()) and state["lite"] is True


def test_atomic_write_failure_preserves_previous_state(tmp_path, monkeypatch):
    _, run = make_run(tmp_path)
    before = (run / "run-status.json").read_bytes()
    def fail(*args):
        raise OSError("injected replace failure")
    monkeypatch.setattr(flow.os, "replace", fail)
    with pytest.raises(flow.FlowError, match="injected"):
        flow.update_state(run, 0, lambda s: dict(s, phase=1))
    assert (run / "run-status.json").read_bytes() == before
    assert flow.load_state(run)["revision"] == 0


def test_lock_blocks_second_writer_and_releases_after_exit(tmp_path):
    _, run = make_run(tmp_path)
    marker = run / "entered"
    code = "import sys,time; from pathlib import Path; import pack_flow as f; " + \
        "f.update_state(Path(sys.argv[1]),0,lambda s: (Path(sys.argv[2]).write_text('yes'),time.sleep(60),s)[2])"
    env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
    child = subprocess.Popen([sys.executable, "-c", code, str(run), str(marker)], env=env)
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.05)
        assert marker.exists()
        with pytest.raises(flow.FlowError, match="lock"):
            flow.update_state(run, 0, lambda s: s)
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert flow.update_state(run, 0, lambda s: s)["revision"] == 1


def test_revision_conflict_preserves_state(tmp_path):
    _, run = make_run(tmp_path)
    flow.update_state(run, 0, lambda s: dict(s, phase=1))
    before = (run / "run-status.json").read_bytes()
    with pytest.raises(flow.FlowError, match="revision"):
        flow.update_state(run, 0, lambda s: dict(s, phase=2))
    assert (run / "run-status.json").read_bytes() == before


def test_status_is_read_only(tmp_path):
    repo, run = make_run(tmp_path)
    before = {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()}
    state = flow.load_state(run)
    assert flow.inspect_state(run)["run_id"] == state["run_id"]
    assert {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()} == before


def test_status_detects_changed_inputs_without_mutating_state(tmp_path):
    repo, run = make_run(tmp_path)
    before = (run / "run-status.json").read_bytes()
    (repo / "STT/0909 전회2.md").write_text("changed", encoding="utf-8")
    view = flow.inspect_state(run)
    assert view["status"] == "needs_fix"
    assert str(repo / "STT/0909 전회2.md") in view["stale_inputs"]
    assert (run / "run-status.json").read_bytes() == before


@pytest.mark.parametrize("field,value", [("schema_version", 2), ("revision", -1), ("repo", "relative"), ("status", "invented"), ("status", []), ("capabilities", {"browser_owner": [], "pdf_owner": "main"})])
def test_invalid_state_rejected_without_writing(tmp_path, field, value):
    _, run = make_run(tmp_path)
    with pytest.raises(flow.FlowError):
        flow.update_state(run, 0, lambda s: dict(s, **{field: value}))
    assert flow.load_state(run)["revision"] == 0


def test_claim_is_exclusive(tmp_path):
    from pack_support import install_task
    _, run = make_run(tmp_path); tid = install_task(run)
    assert flow.claim_task(run, tid)['brief']
    with pytest.raises(flow.FlowError): flow.claim_task(run, tid)


def test_late_attempt_is_rejected(tmp_path):
    from pack_support import install_task, receipt_for
    _, run = make_run(tmp_path); tid = install_task(run)
    old = flow.claim_task(run, tid)['attempt']; path = receipt_for(run, tid, old)
    flow.release_task(run, tid, old, 'confirmed stopped')
    flow.claim_task(run, tid)
    with pytest.raises(flow.FlowError): flow.accept_task(run, tid, old, path)


def test_release_keeps_history(tmp_path):
    from pack_support import install_task
    _, run = make_run(tmp_path); tid = install_task(run)
    attempt = flow.claim_task(run, tid)['attempt']
    flow.bind_task(run, tid, attempt, 'synthetic-agent')
    task = flow.release_task(run, tid, attempt, 'confirmed stopped')['tasks'][tid]
    assert task['history'][-1]['attempt'] == attempt
    assert task['history'][-1]['agent_id'] == 'synthetic-agent'

from pack_support import workflow_accept, workflow_action, workflow_until


def test_next_follows_all_phase_dependencies(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    assert [t['id'] for t in flow.next_work(run, slots=1)['tasks']] == ['author-why']
    workflow_accept(run, 'author-why')
    assert flow.next_work(run, slots=3)['tasks'][0]['id'] == 'author-s1'
    workflow_until(run, 'final-check')
    workflow_action(run, 'final-check')
    assert flow.next_work(run, slots=0)['kind'] == 'report'


def test_manifest_has_single_writer(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'scope-draft')
    workflow_accept(run, 'scope-draft')
    assert not (run / 'manifest.json').exists()
    selection = flow.load_state(run)['tasks']['selection']
    brief = json.loads(Path(selection['brief']).read_text())
    assert str(run / 'work/scope-draft/manifest.json') in [x['path'] for x in brief['inputs']]
    workflow_accept(run, 'selection')
    assert not (run / 'manifest.json').exists()
    workflow_accept(run, 'scope-final')
    assert all(t['status'] == 'done' for t in flow.inspect_state(run)['tasks'].values() if t['id'] in ('scope-draft', 'selection', 'scope-final'))


def test_zero_slots_waits_without_claiming(tmp_path):
    _, run = make_run(tmp_path)
    before = {str(p): p.read_bytes() for p in run.rglob('*') if p.is_file()}
    assert flow.next_work(run, slots=0)['kind'] == 'wait'
    assert before == {str(p): p.read_bytes() for p in run.rglob('*') if p.is_file()}


def test_zero_slots_does_not_block_machine_action(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'prepare-pack')
    assert flow.next_work(run, slots=0)['action'] == 'prepare-pack'


def test_lite_requires_main_audit(tmp_path):
    _, run = make_run(tmp_path, lite=True)
    workflow_until(run, 'style-audit')
    assert flow.next_work(run, slots=0)['kind'] == 'review_locally'
    workflow_until(run, 'final-check')
    assert 'content-review' not in flow.load_state(run)['tasks']


def test_zero_problems_still_requires_final_check(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'final-check')
    state = flow.load_state(run)
    assert 'child-coordinator' not in state['tasks']
    assert 'build-answers' not in state['actions']
    assert flow.next_work(run, slots=0)['action'] == 'final-check'


@pytest.mark.parametrize('owner,kind', [('workers', 'dispatch'), ('main', 'review_locally'), ('unavailable', 'blocked')])
def test_visual_owner_routes_workers_main_and_unavailable(tmp_path, owner, kind):
    _, run = make_run(tmp_path, browser_owner=owner)
    workflow_until(run, 'browser-qa')
    assert flow.next_work(run, slots=2)['kind'] == kind
    assert Path(flow.load_state(run)['tasks']['browser-qa']['brief']).is_file()


def test_fix_round_shared_across_authors_and_idempotent(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'prepare-pack')
    request = run / 'fix.json'
    detail = run / 'fix.md'; detail.write_text('synthetic corrections')
    for n in (1, 2):
        request.write_text(json.dumps({'id': str(n), 'category': 'machine_browser', 'items': [
            {'task_id': tid, 'request_path': str(detail)} for tid in ('author-why', 'author-s1')]}))
        flow.request_fixes(run, request)
        flow.request_fixes(run, request)
    assert flow.load_state(run)['fix_rounds']['machine_browser'] == 2
    request.write_text(request.read_text().replace('"id": "2"', '"id": "3"'))
    with pytest.raises(flow.FlowError): flow.request_fixes(run, request)


def test_changed_note_invalidates_downstream(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'final-check')
    (run / 'note.html').write_text('changed note')
    view = flow.inspect_state(run)
    assert view['tasks']['style-audit']['status'] == 'stale'
    assert view['tasks']['browser-qa']['status'] == 'stale'
    assert flow.next_work(run, slots=2)['kind'] != 'report'


def test_post_extract_change_requires_new_explain_run(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'child-coordinator', problems=1)
    original = flow.load_state(run)['explain_run']
    (run / 'note.html').write_text('changed after extract')
    view = flow.inspect_state(run)
    assert view['explain_run'] is None
    assert original in view['stale_explain_runs']


def test_content_review_audit_update_requires_precheck_again(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'content-review')
    workflow_accept(run, 'content-review', supplement=True)
    state = flow.load_state(run)
    assert state['active_audit'] == json.loads(Path(state['tasks']['content-review']['brief']).read_text())['audit_output']
    assert state['tasks']['content-review']['status'] == 'done'
    assert flow.next_work(run, slots=3)['action'] == 'precheck'
    workflow_action(run, 'precheck')
    assert flow.next_work(run, slots=3)['tasks'][0]['id'] == 'browser-qa'


def test_status_only_machine_completion_is_not_current(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'prepare-pack')
    state = flow.load_state(run)
    def false_completion(s):
        s['actions']['prepare-pack']['status'] = 'done'
        return s
    flow.update_state(run, state['revision'], false_completion)
    assert flow.inspect_state(run)['actions']['prepare-pack']['status'] == 'stale'
    assert flow.next_work(run, slots=3)['action'] == 'prepare-pack'


def test_claim_rechecks_changed_predecessor_evidence(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    (run / 'work/selection/manifest.json').write_text('{}')
    with pytest.raises(flow.FlowError): flow.claim_task(run, 'author-why')


def test_accept_rechecks_current_dependency_review_evidence(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    # A predecessor's report is part of its receipt but not a section author's input.
    report = Path(flow.load_state(run)['tasks']['scope-final']['receipt']['report'])
    with pytest.raises(flow.FlowError):
        workflow_accept(run, 'author-why', before_accept=lambda: report.write_text('changed approval evidence'))


def test_pending_author_brief_does_not_acquire_sibling_outputs(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    brief = Path(flow.load_state(run)['tasks']['author-s1']['brief'])
    before = brief.read_bytes()
    workflow_accept(run, 'author-why')
    assert brief.read_bytes() == before


def test_running_action_is_not_requested_twice(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'prepare-pack')
    def running(s):
        s['actions']['prepare-pack']['status'] = 'running'
        return s
    flow.update_state(run, flow.load_state(run)['revision'], running)
    assert flow.next_work(run, slots=3)['kind'] == 'wait'


def test_stale_active_attempt_requires_confirmed_release(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    attempt = flow.claim_task(run, 'author-why')['attempt']
    flow.bind_task(run, 'author-why', attempt, 'synthetic-active-author')
    (run / 'work/scope-draft/manifest.json').write_text('{}')
    # Reclaim must not silently replace a possibly still writing worker.
    with pytest.raises(flow.FlowError): flow.claim_task(run, 'author-why')
    flow.update_state(run, flow.load_state(run)['revision'], flow._current)
    state = flow.release_task(run, 'author-why', attempt, 'confirmed stopped')
    assert state['tasks']['author-why']['attempt'] is None


def test_problem_path_requires_child_and_pdf_before_final_check(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'final-check', problems=1)
    state = flow.load_state(run)
    assert state['tasks']['child-coordinator']['status'] == 'done'
    assert state['tasks']['pdf-qa']['status'] == 'done'
    assert state['actions']['publish-explanation']['status'] == 'done'
    assert state['actions']['publish-answer']['status'] == 'done'
    workflow_action(run, 'final-check')
    assert flow.next_work(run, slots=0)['kind'] == 'report'


def test_selection_fix_regenerates_final_targets_before_authors(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'author-why')
    detail = run / 'fix.md'; detail.write_text('synthetic new section')
    request = run / 'fix.json'; request.write_text(json.dumps({'id': 'rescope', 'category': 'content',
        'items': [{'task_id': 'selection', 'request_path': str(detail)}]}))
    flow.request_fixes(run, request)
    workflow_accept(run, 'selection', section_ids=('why', 's2'))
    assert flow.load_state(run)['tasks']['scope-final']['targets'] == ['why', 's2']
    workflow_accept(run, 'scope-final', section_ids=('why', 's2'))
    assert [t['id'] for t in flow.next_work(run, slots=3)['tasks']] == ['author-why', 'author-s2']


def test_content_audit_correction_preserves_prior_version(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'content-review')
    workflow_accept(run, 'content-review', supplement=True)
    workflow_action(run, 'precheck')
    old = Path(flow.load_state(run)['active_audit'])
    old_bytes = old.read_bytes()
    detail = run / 'fix-audit.md'; detail.write_text('synthetic audit evidence correction')
    request = run / 'fix-audit.json'; request.write_text(json.dumps({'id': 'audit-correction', 'category': 'content',
        'items': [{'task_id': 'content-review', 'request_path': str(detail)}]}))
    flow.request_fixes(run, request)
    brief = json.loads(Path(flow.load_state(run)['tasks']['content-review']['brief']).read_text())
    assert str(old) in [x['path'] for x in brief['inputs']]
    assert str(old) not in brief['allowed_outputs']
    workflow_accept(run, 'content-review', supplement=True, audit_evidence='synthetic corrected evidence')
    active = Path(flow.load_state(run)['active_audit'])
    assert active != old and active.read_bytes() != old_bytes
    assert old.read_bytes() == old_bytes
    assert flow.next_work(run, slots=3)['action'] == 'precheck'
    workflow_action(run, 'precheck')
    assert flow.next_work(run, slots=3)['tasks'][0]['id'] == 'browser-qa'


def test_invalidated_running_action_waits_after_predecessor_repair(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'prepare-pack')
    def running(s):
        s['actions']['prepare-pack']['status'] = 'running'
        return s
    flow.update_state(run, flow.load_state(run)['revision'], running)
    detail = run / 'fix-author.md'; detail.write_text('synthetic author correction')
    request = run / 'fix-author.json'; request.write_text(json.dumps({'id': 'author-correction', 'category': 'content',
        'items': [{'task_id': 'author-why', 'request_path': str(detail)}]}))
    flow.request_fixes(run, request)
    workflow_accept(run, 'author-why')
    assert flow.load_state(run)['actions']['prepare-pack']['invalidated_active'] is True
    before = (run / 'run-status.json').read_bytes()
    assert flow.next_work(run, slots=3)['kind'] == 'wait'
    assert before == (run / 'run-status.json').read_bytes()
    # Action runner may clear this flag only after explicit reconciliation.
    def reconciled(s):
        s['actions']['prepare-pack'].pop('invalidated_active')
        s['actions']['prepare-pack']['status'] = 'pending'
        return s
    flow.update_state(run, flow.load_state(run)['revision'], reconciled)
    assert flow.next_work(run, slots=3)['action'] == 'prepare-pack'
