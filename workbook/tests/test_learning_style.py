"""개인 명세 바이트와 검토 감사의 완전성을 실제 파일로 확인한다."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from learning_style import (
    LearningStyleError,
    check_style,
    read_style,
    validate_style_audit,
)


def write_profile(tmp_path, ids):
    profile = tmp_path / 'docs/learning/solution-style.md'
    profile.parent.mkdir(parents=True)
    profile.write_text('# Profile\n\n' + '\n'.join(f'### {rule_id}\nRule.\n' for rule_id in ids), encoding='utf-8')
    return tmp_path


@pytest.fixture
def snapshot(tmp_path):
    return read_style(write_profile(tmp_path, ['UNIT-01', 'EXPLAIN-01']))


@pytest.fixture
def valid_audit(snapshot):
    return {
        'learning_style': copy.deepcopy(snapshot),
        'items': {'p1:main': {
            'status': 'pass', 'reviewer': 'content reviewer',
            'rules': {
                'UNIT-01': {'disposition': 'applied', 'evidence': 'Core step 1 converts μA to mA.'},
                'EXPLAIN-01': {'disposition': 'applied', 'evidence': 'Core precedes the detailed derivation.'},
            },
        }},
    }


def test_snapshot_detects_any_byte_change(tmp_path):
    repo = write_profile(tmp_path, ['UNIT-01', 'EXPLAIN-01'])
    snapshot = read_style(repo)
    assert snapshot['rule_ids'] == ['UNIT-01', 'EXPLAIN-01']
    assert snapshot['path'] == 'docs/learning/solution-style.md'
    profile = repo / snapshot['path']
    assert snapshot['sha256'] == hashlib.sha256(profile.read_bytes()).hexdigest()
    check_style(repo, snapshot)
    profile.write_bytes(profile.read_bytes() + b'\n')
    with pytest.raises(LearningStyleError, match='명세 변경'):
        check_style(repo, snapshot)


def test_missing_profile_fails(tmp_path):
    with pytest.raises(LearningStyleError):
        read_style(tmp_path)


def test_duplicate_rule_id_fails(tmp_path):
    with pytest.raises(LearningStyleError):
        read_style(write_profile(tmp_path, ['UNIT-01', 'UNIT-01']))


def test_no_rule_headings_fails(tmp_path):
    with pytest.raises(LearningStyleError):
        read_style(write_profile(tmp_path, []))


def test_titled_headings_keep_document_order_and_ignore_code(tmp_path):
    repo = write_profile(tmp_path, [])
    (repo / 'docs/learning/solution-style.md').write_text(
        '# Profile\n### EXPLAIN-01: 설명\n```md\n### FAKE-01\n```\n'
        '~~~md\n### FAKE-02\n~~~\n### UNIT-01: 단위\n', encoding='utf-8')
    assert read_style(repo)['rule_ids'] == ['EXPLAIN-01', 'UNIT-01']


def test_audit_rejects_missing_rule_or_item(valid_audit, snapshot):
    assert validate_style_audit(valid_audit, snapshot, ['p1:main']) == []
    del valid_audit['items']['p1:main']['rules']['UNIT-01']
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])
    assert validate_style_audit(valid_audit, snapshot, ['p1:main', 'p1:b'])


@pytest.mark.parametrize('evidence', ['', ' \n\t', None, 7])
def test_empty_reason_fails(valid_audit, snapshot, evidence):
    valid_audit['items']['p1:main']['rules']['UNIT-01']['evidence'] = evidence
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


def test_not_applicable_with_reason_passes(valid_audit, snapshot):
    valid_audit['items']['p1:main']['rules']['UNIT-01'] = {
        'disposition': 'not_applicable', 'evidence': 'This qualitative item contains no numeric units.',
    }
    assert validate_style_audit(valid_audit, snapshot, ['p1:main']) == []


def test_extra_item_fails(valid_audit, snapshot):
    valid_audit['items']['p2:main'] = copy.deepcopy(valid_audit['items']['p1:main'])
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


def test_extra_rule_fails(valid_audit, snapshot):
    valid_audit['items']['p1:main']['rules']['EXTRA-01'] = {
        'disposition': 'applied', 'evidence': 'Extra rule.',
    }
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


@pytest.mark.parametrize('status', ['not_run', 'fail', None, 'PASS'])
def test_only_actual_pass_status_is_accepted(valid_audit, snapshot, status):
    valid_audit['items']['p1:main']['status'] = status
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


def test_empty_reviewer_fails(valid_audit, snapshot):
    valid_audit['items']['p1:main']['reviewer'] = ' '
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


def test_unknown_disposition_fails(valid_audit, snapshot):
    valid_audit['items']['p1:main']['rules']['UNIT-01']['disposition'] = 'skipped'
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


@pytest.mark.parametrize('field,value', [
    ('sha256', '0' * 64), ('path', 'elsewhere.md'), ('rule_ids', ['EXPLAIN-01', 'UNIT-01']),
])
def test_stale_or_mismatched_audit_snapshot_fails(valid_audit, snapshot, field, value):
    valid_audit['learning_style'][field] = value
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])


@pytest.mark.parametrize('audit', [None, [], {}, {'items': []}, {'items': {'p1:main': None}}])
def test_malformed_audit_returns_errors(snapshot, audit):
    assert validate_style_audit(audit, snapshot, ['p1:main'])


def test_empty_item_set_and_duplicate_expected_items(valid_audit, snapshot):
    assert validate_style_audit({'learning_style': snapshot, 'items': {}}, snapshot, []) == []
    assert validate_style_audit(valid_audit, snapshot, ['p1:main', 'p1:main'])


def test_cli_snapshot_check_and_fail_closed(tmp_path):
    repo = write_profile(tmp_path, ['UNIT-01', 'EXPLAIN-01'])
    script = Path(__file__).resolve().parents[1] / 'learning_style.py'
    output = tmp_path / 'run/learning-style.json'
    command = [sys.executable, str(script)]
    result = subprocess.run(command + ['snapshot', '--repo', str(repo), '--out', str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    snapshot = json.loads(output.read_text())
    audit = {'learning_style': snapshot, 'items': {'p1:main': {
        'status': 'pass', 'reviewer': 'reviewer', 'rules': {
            rule_id: {'disposition': 'applied', 'evidence': 'Reviewed core.'}
            for rule_id in ['UNIT-01', 'EXPLAIN-01']
        },
    }}}
    audit_path = tmp_path / 'audit.json'
    audit_path.write_text(json.dumps(audit))
    check = command + ['check', '--repo', str(repo), '--snapshot', str(output), '--audit', str(audit_path), '--items', 'p1:main']
    result = subprocess.run(check, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'style PASS' in result.stdout
    audit['items']['p1:main']['status'] = 'not_run'
    audit_path.write_text(json.dumps(audit))
    result = subprocess.run(check, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'style PASS' not in result.stdout
    audit_path.write_text('{bad json')
    result = subprocess.run(check, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Traceback' not in result.stderr
