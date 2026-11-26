"""`task probe`: an author checks its own section fragment before handoff."""
import json
from pathlib import Path

import pytest

from _util import FIXTURES, prepare_mini_run
import pack_flow as flow
from pack_probe import fragment_probe
from test_pack_graph import seed, selected

FIXTURE = FIXTURES / 'mini-run'
SID = 's1'
CLEAN = lambda html, out: (0, {'checks': []})  # noqa: E731


def attempt_dir(run, tid):
    return Path(flow.load_state(run)['tasks'][tid]['attempt_dir'])


def claimed_author(tmp_path, *, fragment=None, text=None):
    """Seed through scope-final with the mini-run manifest, claim author-s1, write its fragment."""
    state = selected(tmp_path, [])
    run = Path(state['run'])
    fixture = prepare_mini_run(run / 'note-fixture')
    manifest = json.loads((fixture / 'manifest.json').read_text(encoding='utf-8'))
    state['scope_sections'] = manifest['sections']
    state['link_sections'] = []
    for tid in ('scope-draft', 'selection'):
        state['tasks'][tid].setdefault('artifacts', {})['manifest.json'] = str(fixture / 'manifest.json')
    seed(state, ['scope-final'])
    state['tasks']['scope-final'].setdefault('artifacts', {})['manifest.json'] = str(fixture / 'manifest.json')
    from pack_graph import refresh
    flow.update_state(run, flow.load_state(run)['revision'], lambda s: refresh(state))
    tid = 'author-' + SID
    attempt = flow.claim_task(run, tid)['attempt']
    target = attempt_dir(run, tid) / 'sections' / (SID + '.html')
    target.parent.mkdir(parents=True, exist_ok=True)
    if fragment is not None:
        target.write_bytes(Path(fragment).read_bytes())
    else:
        target.write_text(text, encoding='utf-8', newline='\n')
    return run, tid, attempt


def test_probe_passes_clean_fragment(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda html, out: (0, {'checks': []}))
    assert result['status'] == 'pass' and result['problems'] == []
    assert result['fragment_sha256'] == flow._sha(attempt_dir(run, tid)/'sections/s1.html')


def test_probe_reports_fragment_defect(tmp_path):
    bad = '<article class="topic" id="dup"></article><article class="topic" id="dup"></article>'
    run, tid, attempt = claimed_author(tmp_path, text=bad)
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (0, {'checks': []}))
    assert result['status'] == 'defects' and any(p['code'] == 'duplicate-id' for p in result['problems'])


def test_probe_treats_missing_browser_as_unavailable(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (2, None))
    assert result['layout']['status'] == 'unavailable' and result['status'] == 'pass'


def test_probe_real_layout(tmp_path):
    pytest.importorskip('playwright')
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    assert fragment_probe(run, tid, attempt)['layout']['status'] in ('pass', 'defects')


def test_probe_writes_schema_under_attempt(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=CLEAN)
    root = attempt_dir(run, tid)
    assert flow._read(root/'probe/probe.json') == result
    assert (root/'probe/preview.html').is_file()
    assert set(result) == {'schema_version', 'task_id', 'attempt', 'fragment_sha256', 'problems', 'layout', 'status'}
    assert (result['schema_version'], result['task_id'], result['attempt']) == (1, tid, attempt)
    assert result['layout'] == {'status': 'pass', 'defects': 0, 'report': str(root/'probe/layout.json')}


def test_probe_counts_layout_defects(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    report = {'checks': [{'overflow': [{'id': 'x'}], 'label_gaps': []}], 'circuits': [{'id': 'c'}]}
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (1, report))
    assert result['layout']['status'] == 'defects' and result['layout']['defects'] == 2
    assert result['status'] == 'defects'


def test_probe_ignores_links_resolved_only_in_the_full_note(tmp_path):
    # PDF/note names and anchors into other manifest sections exist only after assembly.
    text = ('<article class="topic" id="s1-mean"><p><a href="{{PROBLEM_PDF}}">p</a> <a href="{{ANSWER_PDF}}">a</a> '
            '<a href="{{NOTE_HREF}}">n</a> <a href="#why-circuit">w</a> <a href="#nowhere">x</a></p></article>')
    run, tid, attempt = claimed_author(tmp_path, text=text)
    result = fragment_probe(run, tid, attempt, layout=CLEAN)
    assert [(p['code'], p['detail']) for p in result['problems']] == [('broken-link', '#nowhere')]


def test_probe_rejects_inactive_attempt_and_non_author(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    with pytest.raises(flow.FlowError):
        fragment_probe(run, tid, 'not-the-attempt', layout=CLEAN)
    with pytest.raises(flow.FlowError):
        fragment_probe(run, 'scope-final', attempt, layout=CLEAN)


def test_cli_probe_is_read_only_and_compact(tmp_path, monkeypatch):
    import io, sys
    import pack_cli, pack_probe
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    monkeypatch.setattr(pack_probe, 'run_layout', CLEAN)
    before = (run/'run-status.json').read_bytes()
    out = io.StringIO(); monkeypatch.setattr(sys, 'stdout', out)
    code = pack_cli.main(['task', 'probe', '--run', str(run), '--task', tid, '--attempt', attempt])
    text = out.getvalue()
    data = json.loads(text)
    assert code == 0 and len(text) <= 2000
    assert data['status'] == 'pass' and data['details_path'] == str(attempt_dir(run, tid)/'probe/probe.json')
    assert (run/'run-status.json').read_bytes() == before
    assert not (run/'work'/'cli').exists()


def test_parallel_init_sets_probe_contract(tmp_path):
    from test_pack_graph import parallel
    _, _, state = parallel(tmp_path)
    assert state['probe_contract'] == 1
