"""Audit findings must all reach the one content-fix round."""
import json
from pathlib import Path

import pytest
from _util import SCRIPTS  # noqa: F401  (puts scripts on sys.path)
from pack_findings import blocking_findings, owner_of
from pack_support import make_run, workflow_until
import pack_flow as flow

REPORT = """# Style audit

## Critical
- none

## Important
- [s4-cheatsheet] summary panel lacks the cheat sheet
- [P12.04] selection title wording
  continued detail line

## Minor
- [s1] spacing

## Notes
- [ignored] outside the severity sections
"""

MANIFEST = {'sections': [{'id': 's1', 'topics': [{'id': 's1-intro'}]},
                         {'id': 's4', 'topics': [{'id': 's4-cheatsheet'}]}],
            'problems': [{'id': 'P12.04'}]}


def test_blocking_findings_parses_three_sections(tmp_path):
    report = tmp_path / 'report.md'; report.write_text(REPORT, encoding='utf-8')
    assert blocking_findings(report) == [('Important', 's4-cheatsheet'), ('Important', 'P12.04'), ('Minor', 's1')]


def test_owner_maps_problem_to_selection():
    assert owner_of('P12.04', MANIFEST) == 'selection'
    assert owner_of('s4-cheatsheet', MANIFEST) == 'author-s4'
    assert owner_of('s1', MANIFEST) == 'author-s1'
    assert owner_of('note-layout', MANIFEST) == 'scope-final'


def _audit_needs_fix(run, findings):
    report = run / 'work' / 'style-audit' / 'findings.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('## Important\n' + ''.join(f'- [{x}] synthetic finding\n' for x in findings), encoding='utf-8')
    def change(s):
        task = s['tasks']['style-audit']
        task['status'] = 'needs_fix'
        task['receipt'] = dict(task.get('receipt') or {}, report=str(report))
        return s
    flow.update_state(run, flow.load_state(run)['revision'], change)


def _request(run, items, **extra):
    detail = run / 'fix.md'; detail.write_text('synthetic corrections')
    path = run / 'fix.json'
    path.write_text(json.dumps(dict({'id': 'content-1', 'category': 'content',
        'items': [{'task_id': t, 'request_path': str(detail)} for t in items]}, **extra)))
    return path


def test_content_fix_rejects_missing_owner(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'browser-qa', problems=1)
    _audit_needs_fix(run, ['s1-topic', 'P10.02'])
    with pytest.raises(flow.FlowError, match=r'content fix misses findings: P10\.02→selection'):
        flow.request_fixes(run, _request(run, ['author-s1']))
    assert flow.load_state(run)['fix_rounds']['content'] == 0


def test_content_fix_accepts_waived(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'browser-qa', problems=1)
    _audit_needs_fix(run, ['s1-topic', 'P10.02'])
    flow.request_fixes(run, _request(run, ['author-s1'], waived=[{'id': 'P10.02', 'reason': 'title already fixed in PDF'}]))
    assert flow.load_state(run)['fix_rounds']['content'] == 1


def test_blocking_findings_accepts_heading_variants_and_id_lists(tmp_path):
    report = tmp_path / 'report.md'
    report.write_text('### Critical\n- [s1-intro] wrong sign\n\n## Important (2)\n'
                      '- [s4-cheatsheet, P12.04] two owners\n## Notes\n- [x] skip\n', encoding='utf-8')
    assert blocking_findings(report) == [('Critical', 's1-intro'), ('Important', 's4-cheatsheet'), ('Important', 'P12.04')]


def test_subheading_inside_severity_keeps_section(tmp_path):
    report = tmp_path / 'report.md'
    report.write_text('## Important\n### s1 섹션\n- [s1-intro] gap\n## Notes\n- [x] skip\n', encoding='utf-8')
    assert blocking_findings(report) == [('Important', 's1-intro')]
