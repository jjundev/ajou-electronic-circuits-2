"""`task probe`: an author checks its own section fragment before handoff."""
import json
from pathlib import Path

import pytest

from _util import FIXTURES, prepare_mini_run
import pack_flow as flow
from pack_probe import fragment_probe
from test_pack_graph import parallel, seed

FIXTURE = FIXTURES / 'mini-run'
SID = 's1'
CLEAN = lambda html, out: (0, {'checks': []})  # noqa: E731


def attempt_dir(run, tid):
    return Path(flow.load_state(run)['tasks'][tid]['attempt_dir'])


def claimed_author(tmp_path, *, fragment=None, text=None, links=()):
    """Seed through scope-final with the mini-run manifest, claim author-s1, write its fragment.

    The seeding is `test_pack_graph.selected` applied to the persisted state, then scope-final.
    """
    from pack_graph import refresh
    _, run, _ = parallel(tmp_path)
    fixture = prepare_mini_run(run / 'note-fixture')
    manifest = json.loads((fixture / 'manifest.json').read_text(encoding='utf-8'))
    manifest['links'] += [{'topic': 's1-mean', 'href': href} for href in links]
    (fixture / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')

    def setup(s):
        seed(s, ['source-prep', 'stt-0909', 'candidate-index', 'scope-draft'])
        s['scope_sections'] = manifest['sections']
        s['link_sections'] = []
        s['selected_ids'] = []
        seed(s, ['selection', 'render-preflight'])
        for tid in ('scope-draft', 'selection'):
            s['tasks'][tid].setdefault('artifacts', {})['manifest.json'] = str(fixture / 'manifest.json')
        seed(s, ['scope-final'])
        s['tasks']['scope-final'].setdefault('artifacts', {})['manifest.json'] = str(fixture / 'manifest.json')
        return refresh(s)
    flow.update_state(run, flow.load_state(run)['revision'], setup)
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


def test_probe_ignores_hrefs_listed_in_manifest_links(tmp_path):
    # Cross-note links resolve against the published pack, never against <attempt>/probe/.
    listed = '../0930/정리노트_0930_Other.html#s1-mean'
    text = (f'<article class="topic" id="s1-mean"><p><a href="{listed}">listed</a> '
            '<a href="../0930/unlisted.html#x">unlisted</a></p></article>')
    run, tid, attempt = claimed_author(tmp_path, text=text, links=[listed])
    result = fragment_probe(run, tid, attempt, layout=CLEAN)
    assert [(p['code'], p['detail']) for p in result['problems']] == [('broken-link', '../0930/unlisted.html#x')]
    assert result['status'] == 'defects'


def test_probe_listed_cross_note_link_passes(tmp_path):
    listed = '../0930/정리노트_0930_Other.html#s1-mean'
    text = f'<article class="topic" id="s1-mean"><p><a href="{listed}">listed</a></p></article>'
    run, tid, attempt = claimed_author(tmp_path, text=text, links=[listed])
    assert fragment_probe(run, tid, attempt, layout=CLEAN)['status'] == 'pass'


@pytest.mark.parametrize('reason', [
    'Page resource failed to load: http://127.0.0.1/x.png',
    'KaTeX not loaded',
    'circuit note: no topic figure was measured',
])
def test_probe_page_errors_are_layout_defects(tmp_path, reason):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (2, {'error': reason}))
    out = attempt_dir(run, tid)/'probe/layout.json'
    assert result['layout'] == {'status': 'defects', 'defects': 1, 'report': str(out)}
    assert result['status'] == 'defects' and flow._read(out) == {'error': reason}


@pytest.mark.parametrize('reason', [
    "No module named 'playwright'",
    "Playwright Chromium: BrowserType.launch: Executable doesn't exist at C:\\ms-playwright\\chrome.exe\n"
    "Google Chrome: BrowserType.launch: Chromium distribution 'chrome' is not found",
])
def test_probe_missing_browser_reason_is_unavailable(tmp_path, reason):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (2, {'error': reason}))
    out = attempt_dir(run, tid)/'probe/layout.json'
    assert result['layout'] == {'status': 'unavailable', 'defects': 0, 'report': str(out)}
    assert result['status'] == 'pass' and flow._read(out) == {'error': reason}


def test_run_layout_keeps_the_error_reason(tmp_path, monkeypatch):
    import layout_probe, pack_probe
    def failing(html, widths, themes, *, pack_paths=None):
        raise RuntimeError('KaTeX not loaded')
    monkeypatch.setattr(layout_probe, 'probe', failing)
    preview = tmp_path/'preview.html'; preview.write_text('<html></html>', encoding='utf-8')
    assert pack_probe.run_layout(preview, tmp_path/'layout.json') == (2, {'error': 'KaTeX not loaded'})


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


def submit_author(run, tid, attempt):
    """The submission/build-receipt half of `pack_support.parallel_worker` for an already-claimed author.

    build-receipt writes the receipt before it prechecks it, so a refused precheck still
    leaves the receipt for `task check` to judge.
    """
    from pack_receipts import build_receipt
    state = flow.load_state(run)
    if not state['tasks'][tid].get('agent_id'):
        flow.bind_task(run, tid, attempt, 'synthetic-' + tid)
    brief = json.loads(Path(state['tasks'][tid]['brief']).read_text(encoding='utf-8'))
    outputs = [Path(name) for name in brief['required_outputs']]
    report = Path(brief['report'])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('Synthetic fixture review only.')
    info = dict(status='done', report=str(report), reviews=[str(report)],
                outputs=[str(p) for p in outputs if p.is_file()], counts={'targets': brief['targets']},
                unresolved=[])
    submission = Path(brief['run'])/'worker.json'
    submission.write_text(json.dumps(info))
    try:
        build_receipt(flow.inspect_state(run), tid, attempt, submission)
    except flow.FlowError:
        pass
    return Path(brief['receipt'])


def test_author_receipt_requires_current_passing_probe(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    receipt = submit_author(run, tid, attempt)                # build-receipt까지
    assert flow.check_task(run, tid, attempt, receipt)['reason'] == 'fragment probe missing, stale or failing'
    fragment_probe(run, tid, attempt, layout=lambda h, o: (0, {'checks': []}))
    assert flow.check_task(run, tid, attempt, receipt)['status'] == 'ok'
    (attempt_dir(run, tid)/'sections/s1.html').write_text('changed', encoding='utf-8')
    receipt = submit_author(run, tid, attempt)
    assert flow.check_task(run, tid, attempt, receipt)['status'] == 'failed'


def test_author_receipt_rejects_failing_probe_and_records_passing_one(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    receipt = submit_author(run, tid, attempt)
    fragment_probe(run, tid, attempt, layout=lambda h, o: (1, {'checks': [{'overflow': [{'id': 'x'}]}]}))
    assert flow.check_task(run, tid, attempt, receipt)['reason'] == 'fragment probe missing, stale or failing'
    fragment_probe(run, tid, attempt, layout=CLEAN)
    from pack_parallel import validate_worker
    state = flow.load_state(run)
    verified = validate_worker(state, state['tasks'][tid], receipt)['verified_files']
    probe = attempt_dir(run, tid)/'probe/probe.json'
    assert {'path': str(flow.nfc_path(probe)), 'sha256': flow._sha(probe)} in verified


def test_author_receipt_without_probe_contract_is_unchanged(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    flow.update_state(run, flow.load_state(run)['revision'], lambda s: (s.pop('probe_contract'), s)[1])
    receipt = submit_author(run, tid, attempt)
    assert flow.check_task(run, tid, attempt, receipt)['status'] == 'ok'


def test_probe_uses_the_note_builder_even_after_workbook_assemble_loaded(tmp_path, monkeypatch):
    # workbook/assemble.py shares the module name; a test or action may import it first.
    import sys, types
    monkeypatch.setitem(sys.modules, 'assemble', types.ModuleType('assemble'))
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    assert fragment_probe(run, tid, attempt, layout=CLEAN)['status'] == 'pass'


def test_probe_walks_circuits_only_when_the_section_draws_figures(tmp_path):
    # A circuit note fails "no topic figure was measured" when nothing is drawn. In the full
    # note other sections hold figures; alone, a figure-free section must still be measurable.
    plain = '<article class="topic" id="s1-mean"><p>글만 있는 토픽</p></article>'
    run, tid, attempt = claimed_author(tmp_path, text=plain)
    fragment_probe(run, tid, attempt, layout=CLEAN)
    assert 'data-circuits' not in (attempt_dir(run, tid)/'probe/preview.html').read_text(encoding='utf-8')
    run, tid, attempt = claimed_author(tmp_path/'drawn', fragment=FIXTURE/'sections/s1.html')
    fragment_probe(run, tid, attempt, layout=CLEAN)
    assert 'data-circuits' in (attempt_dir(run, tid)/'probe/preview.html').read_text(encoding='utf-8')


def test_probe_real_layout_passes_a_figure_free_section(tmp_path):
    pytest.importorskip('playwright')
    run, tid, attempt = claimed_author(tmp_path, text='<article class="topic" id="s1-mean"><p>글</p></article>')
    assert fragment_probe(run, tid, attempt)['layout']['status'] in ('pass', 'unavailable')
