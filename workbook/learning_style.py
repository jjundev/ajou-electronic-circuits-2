"""개인 풀이 명세의 바이트 스냅샷과 적용 감사 형식을 검사한다.

이 검사는 집합·형식·해시만 확인한다. evidence의 의미 검토와 실제 검산은
작성자와 리뷰어가 수행하며, 이 모듈이 검토 기록을 만들어 주지는 않는다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Literal, TypedDict


STYLE_PATH = 'docs/learning/solution-style.md'
RULE_HEADING = re.compile(r'^### ([A-Z][A-Z0-9]*-[0-9]{2})(?=[ \t:]|$)')


class StyleSnapshot(TypedDict):
    path: str
    sha256: str
    rule_ids: list[str]


class RuleAudit(TypedDict):
    disposition: Literal['applied', 'not_applicable']
    evidence: str


class ItemAudit(TypedDict):
    status: Literal['pass', 'not_run', 'fail']
    reviewer: str
    rules: dict[str, RuleAudit]


class StyleAudit(TypedDict):
    learning_style: StyleSnapshot
    items: dict[str, ItemAudit]


class LearningStyleError(ValueError):
    pass


def read_style(repo: Path) -> StyleSnapshot:
    """명세 원본 바이트를 해시하고 코드 블록 밖의 규칙 제목을 순서대로 읽는다."""
    try:
        data = (Path(repo) / STYLE_PATH).read_bytes()
        source = data.decode('utf-8')
    except (OSError, UnicodeError) as exc:
        raise LearningStyleError(f'개인 명세를 읽을 수 없어요: {STYLE_PATH}: {exc}') from exc

    rule_ids: list[str] = []
    fence_char = ''
    fence_length = 0
    for line in source.splitlines():
        fence = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            marker, trailing = fence.groups()
            if not fence_char:
                fence_char, fence_length = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length and not trailing.strip():
                fence_char = ''
            continue
        if fence_char:
            continue
        match = RULE_HEADING.match(line)
        if match:
            rule_id = match.group(1)
            if rule_id in rule_ids:
                raise LearningStyleError(f'개인 명세 규칙 ID 중복: {rule_id}')
            rule_ids.append(rule_id)
    if not rule_ids:
        raise LearningStyleError('개인 명세 규칙 제목이 없어요: ### UNIT-01 형식 필요')
    return {'path': STYLE_PATH, 'sha256': hashlib.sha256(data).hexdigest(), 'rule_ids': rule_ids}


def check_style(repo: Path, expected: StyleSnapshot) -> None:
    """명세의 어떤 바이트라도 바뀌면 이전 검토를 거부한다."""
    if read_style(repo) != expected:
        raise LearningStyleError('개인 명세 변경: 현재 명세로 다시 검토해야 해요')


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_style_audit(audit: dict, snapshot: StyleSnapshot, item_ids: list[str]) -> list[str]:
    """기대 문항/규칙 전체의 실제 pass 기록과 비어 있지 않은 근거를 요구한다."""
    errors: list[str] = []
    if len(set(item_ids)) != len(item_ids):
        errors.append('검토 대상 item ID 중복')
    if not isinstance(audit, dict):
        return errors + ['개인화 감사는 객체여야 해요']
    if audit.get('learning_style') != snapshot:
        errors.append('개인화 감사의 명세 스냅샷 불일치')
    items = audit.get('items')
    if not isinstance(items, dict):
        return errors + ['개인화 감사 items 객체 누락']
    if set(items) != set(item_ids):
        errors.append('개인화 감사 item 집합 불일치')
    expected_rules = set(snapshot['rule_ids'])
    for item_id in item_ids:
        item = items.get(item_id)
        if not isinstance(item, dict):
            errors.append(f'{item_id}: 검토 객체 누락')
            continue
        if item.get('status') != 'pass':
            errors.append(f'{item_id}: 실제 pass 검토 필요')
        if not _nonempty_text(item.get('reviewer')):
            errors.append(f'{item_id}: reviewer 누락')
        rules = item.get('rules')
        if not isinstance(rules, dict):
            errors.append(f'{item_id}: rules 객체 누락')
            continue
        if set(rules) != expected_rules:
            errors.append(f'{item_id}: 규칙 집합 불일치')
        for rule_id in snapshot['rule_ids']:
            rule = rules.get(rule_id)
            if not isinstance(rule, dict):
                errors.append(f'{item_id}/{rule_id}: 규칙 감사 누락')
                continue
            if rule.get('disposition') not in ('applied', 'not_applicable'):
                errors.append(f'{item_id}/{rule_id}: disposition 오류')
            if not _nonempty_text(rule.get('evidence')):
                errors.append(f'{item_id}/{rule_id}: 적용 근거 또는 비적용 이유 누락')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    snapshot_parser = subparsers.add_parser('snapshot')
    snapshot_parser.add_argument('--repo', type=Path, required=True)
    snapshot_parser.add_argument('--out', type=Path, required=True)
    check_parser = subparsers.add_parser('check')
    check_parser.add_argument('--repo', type=Path, required=True)
    check_parser.add_argument('--snapshot', type=Path, required=True)
    check_parser.add_argument('--audit', type=Path, required=True)
    check_parser.add_argument('--items', nargs='*', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'snapshot':
            snapshot = read_style(args.repo)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'style snapshot: {args.out}')
        else:
            snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
            check_style(args.repo, snapshot)
            audit = json.loads(args.audit.read_text(encoding='utf-8'))
            errors = validate_style_audit(audit, snapshot, args.items)
            if errors:
                raise LearningStyleError('\n'.join(errors))
            print('style PASS')
    except (LearningStyleError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'style FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
