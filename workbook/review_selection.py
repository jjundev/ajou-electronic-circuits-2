"""Versioned review-pack selection metadata shared by selectors and renderers.

This validates recorded decisions; it does not infer scope or approve mathematics.
"""
import hashlib
import json
from pathlib import Path

POLICY = 'exam-first-v2'
MAX_PROBLEMS = 20


def metadata_errors(manifest):
    policy = manifest.get('selection_policy')
    if policy is None:
        return []  # Historical packs remain readable.
    if policy != POLICY:
        return [f'selection_policy: 알 수 없는 정책: {policy}']
    errors = []
    for i, q in enumerate(manifest['problems']):
        prefix = f'problems[{i}]'
        if q.get('priority') not in ('core', 'extra'):
            errors.append(f'{prefix}.priority: core 또는 extra 필요')
        goals = q.get('learning_goals')
        if not isinstance(goals, list) or not goals or any(not isinstance(g, str) or not g.strip() for g in goals):
            errors.append(f'{prefix}.learning_goals: 비어 있지 않은 학습 목표 목록 필요')
        minutes = q.get('estimated_minutes')
        if type(minutes) is not int or minutes <= 0:
            errors.append(f'{prefix}.estimated_minutes: 양의 정수(추정 분) 필요')
    if manifest['problems'] and not any(q.get('priority') == 'core' for q in manifest['problems']):
        errors.append('problems: 핵심 문제가 최소 1개 필요')
    return errors


def validate_review(manifest, candidates, review):
    """Require explicit dispositions for selected items and all unused exam candidates."""
    errors = metadata_errors(manifest)
    if errors:
        raise ValueError('; '.join(errors))
    if not isinstance(review, dict) or review.get('policy') != POLICY:
        raise ValueError('exam-first-v2에는 selection-review.json이 필요합니다')
    if review.get('catalog_sha256') != candidates['catalog_sha256']:
        raise ValueError('선발 검토의 카탈로그 해시가 다릅니다')
    table = {q['id']: q for q in candidates['problems']}
    selected = {q['id']: q for q in manifest['problems']}
    rows = review.get('candidates')
    if not isinstance(rows, list) or any(not isinstance(q, dict) for q in rows):
        raise ValueError('선발 검토 candidates 목록 필요')
    decisions = {q.get('id'): q for q in rows}
    required = set(selected) | {q['id'] for q in table.values() if q['kind'] == '기출' and not q['used']}
    if len(decisions) != len(rows) or not required <= decisions.keys() or not decisions.keys() <= table.keys():
        raise ValueError('선발 검토: 선택 문항/미사용 기출 전부를 검토하고 중복/후보 외 ID를 제거하세요')
    for pid, row in decisions.items():
        disposition, scope = row.get('disposition'), row.get('scope')
        if disposition not in ('selected', 'excluded', 'deferred') or scope not in ('in_scope', 'out_of_scope', 'unclear'):
            raise ValueError(f'선발 검토 상태 오류: {pid}')
        if not isinstance(row.get('reason'), str) or not row['reason'].strip():
            raise ValueError(f'선발 검토 이유 필요: {pid}')
        if (pid in selected) != (disposition == 'selected') or (pid in selected and scope != 'in_scope'):
            raise ValueError(f'선발 목록/전체 소문항 범위 판정 불일치: {pid}')
        if disposition == 'deferred':
            missing = row.get('missing_concepts')
            if scope != 'out_of_scope' or not isinstance(missing, list) or not missing or any(not isinstance(g, str) or not g.strip() for g in missing):
                raise ValueError(f'보류 문항의 미학습 개념 필요: {pid}')
    coverage = review.get('coverage')
    if not isinstance(coverage, list) or (selected and not coverage):
        raise ValueError('학습 목표 coverage 목록 필요')
    goals = set()
    for row in coverage:
        if not isinstance(row, dict) or not isinstance(row.get('goal'), str) or not row['goal'].strip():
            raise ValueError('coverage 학습 목표 필요')
        goal = row['goal']
        ids = row.get('problem_ids')
        if goal in goals or not isinstance(ids, list) or len(ids) != len(set(ids)) or any(pid not in selected for pid in ids):
            raise ValueError(f'coverage 문항/중복 오류: {goal}')
        goals.add(goal)
        if any(goal not in selected[pid]['learning_goals'] for pid in ids):
            raise ValueError(f'coverage와 문항 학습 목표 불일치: {goal}')
        core = any(selected[pid]['priority'] == 'core' for pid in ids)
        if not core and not str(row.get('gap_reason', '')).strip():
            raise ValueError(f'핵심 문제로 다루지 못한 목표의 사유 필요: {goal}')
    if any(not set(q['learning_goals']) <= goals for q in selected.values()):
        raise ValueError('문항 학습 목표가 coverage에서 누락되었습니다')


def load_selection(path, ids):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if value.get('schema_version') != 2 or value.get('policy') != POLICY:
        raise ValueError('선발 기록 schema_version=2 / exam-first-v2 필요')
    rows = value.get('problems', [])
    if len(ids) != len(set(ids)) or [q['id'] for q in rows] != list(ids) or len(ids) > MAX_PROBLEMS:
        raise ValueError('선발 기록의 ID/순서가 문제 목록과 다릅니다')
    errors = metadata_errors(dict(selection_policy=POLICY, problems=rows))
    if errors:
        raise ValueError('; '.join(errors))
    for q in rows:
        if type(q.get('subpart_count')) is not int or q['subpart_count'] < 1:
            raise ValueError('선발 기록의 소문항 수 필요')
    workload = value.get('workload')
    if not isinstance(workload, dict) or workload.get('estimated_minutes') != sum(q['estimated_minutes'] for q in rows):
        raise ValueError('선발 기록의 총 예상 시간이 문항 합계와 다릅니다')
    return value


def workload_label(q):
    return f"{'핵심' if q['priority'] == 'core' else '추가 연습'} · 소문항 {q['subpart_count']}묶음 · 예상 {q['estimated_minutes']}분(추정)"


def apply_selection(data, selection):
    for p, q in zip(data['problems'], selection['problems']):
        if p['id'] != q['id']:
            raise ValueError('선발 기록의 ID/순서가 문제 목록과 다릅니다')
        p['review_selection'] = q
        p['review_workload_label'] = workload_label(q)
    data['meta']['review_workload'] = selection['workload']
    return data


def reviewed_selection_path(overlay, repo, explicit=None, *, pack_paths=None):
    bound = [(name, digest) for name, digest in overlay['source_inputs'].items()
             if Path(name).name == 'selection.json' and Path(name).parent.name == '.assets']
    if not bound:
        if explicit is not None:
            raise ValueError('선발 기록은 승인된 답안 입력에 포함되어야 합니다')
        return None
    if len(bound) != 1:
        raise ValueError('승인된 선발 기록은 정확히 하나여야 합니다')
    name, digest = bound[0]
    path = pack_paths.source_file(name) if pack_paths else Path(repo) / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('승인된 선발 기록이 변경되었습니다')
    if explicit is not None and hashlib.sha256(Path(explicit).read_bytes()).hexdigest() != digest:
        raise ValueError('선발 기록이 승인된 답안 입력과 다릅니다')
    return path
