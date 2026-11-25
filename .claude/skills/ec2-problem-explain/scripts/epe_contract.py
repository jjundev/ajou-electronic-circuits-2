from epe_review_policy import POLICY_VERSION
"""Structural checks do not claim mathematical or visual correctness."""
import hashlib
import json
from epe_independent import independent_errors
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from epe_shared import Node, parse, math_delimiter_errors, validate_style_audit
from epe_solution import solution_nodes
from readability import readability_errors

KEYS = ('understand', 'recall', 'start', 'solve', 'verify', 'pitfall', 'retry')

def payload_hash(pack, fragments):
    payload = {'source_sha256': pack.sha256, 'fragments': fragments, 'learning_style': pack.learning_style}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()

def markup_errors(root, allow_summary=False):
    errors = []
    for node in root.find_all(lambda n: True):
        summary = allow_summary and node.parent is root and node.tag == 'div' and 'sum' in node.classes
        if node.tag in ('details', 'script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'link', 'meta', 'base'):
            errors.append(f'허용하지 않는 태그: {node.tag}')
        if 'hidden' in node.attrs and not summary:
            errors.append('본문 숨김 금지')
        for key, value in node.attrs.items():
            if key.startswith('on') or key in ('style', 'srcdoc'):
                errors.append(f'허용하지 않는 속성: {key}')
            if key in ('href', 'src', 'xlink:href'):
                scheme = urlsplit(''.join(value.split())).scheme.lower()
                if scheme and scheme not in ('http', 'https'):
                    errors.append(f'허용하지 않는 URL: {key}')
    return errors

def _body_text(node):
    """Exclude headings even when authors wrap them in layout containers."""
    if isinstance(node, str):
        return node
    if node.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        return ''
    return ''.join(_body_text(child) for child in node.children)

def _text_leaves(node):
    """KaTeX auto-render matches delimiters inside one text node, never across elements."""
    for child in node.children:
        if isinstance(child, str):
            yield child
        elif child.tag not in ('script', 'style'):
            yield from _text_leaves(child)

def math_errors(root):
    errors = []
    for leaf in _text_leaves(root):
        errors.extend(e for e in math_delimiter_errors(leaf) if e not in errors)
    return errors

def validate_fragment(problem, fragment):
    root = parse(fragment)
    errors = markup_errors(root, allow_summary=True)
    errors.extend(f'{code}: {detail}' for code, detail in readability_errors(fragment))
    errors.extend(solution_nodes(problem, fragment)[2])
    sections = list(root.find_all(lambda n: 'data-explanation' in n.attrs))
    counts = Counter(n.attrs['data-explanation'] for n in sections)
    if counts != Counter(KEYS):
        errors.append('일곱 설명 구역(understand/recall/start/solve/verify/pitfall/retry)을 각각 한 번 작성하세요')
    if tuple(n.attrs['data-explanation'] for n in sections) != KEYS:
        errors.append('설명 구역 순서는 understand/recall/start/solve/verify/pitfall/retry여야 해요')
    for node in sections:
        if node.attrs['data-explanation'] == 'recall':
            body = _body_text(node)
            if not body.strip():
                errors.append('recall: 제목 외에 단서·개념·공식·적용 조건 설명이 필요해요')
        if node.parent is not root or 'layer' not in node.classes or not node.text().strip():
            errors.append('설명 구역은 내용이 있는 직계 layer여야 해요')
        if node.attrs['data-explanation'] in ('solve', 'verify'):
            items = list(node.find_all(lambda n: 'data-subpart' in n.attrs))
            if Counter(n.attrs['data-subpart'] for n in items) != Counter(problem.subparts) or any(not n.text().strip() for n in items):
                errors.append(f"{node.attrs['data-explanation']}: 모든 소문항 풀이·검산을 각각 한 번 작성하세요")
        if node.attrs['data-explanation'] == 'retry':
            items = list(node.find_all(lambda n: n.tag == 'li'))
            if not 1 <= len(items) <= 3 or any(not n.text().strip() for n in items):
                errors.append('retry: 비어 있지 않은 재풀이 항목 1~3개 필요')
    if not all(any(layer in node.classes for node in sections) for layer in ('eli5', 'formal', 'warn')):
        errors.append('eli5/formal/warn 설명 층 필요')
    summaries = list(root.find_all(lambda n: 'sum' in n.classes))
    if len(summaries) != 1 or summaries[0].parent is not root or 'hidden' not in summaries[0].attrs or not summaries[0].text().strip():
        errors.append('직계 sum[hidden] 요약 하나 필요')
    errors.extend(math_errors(root))
    return [f'{problem.id}: {e}' for e in errors]

def initial_reviews(pack, fragments):
    keys = [f'{p.id}:{s}' for p in pack.problems for s in p.subparts]
    pending = {'status': 'not_run', 'reviewer': '', 'evidence': ''}
    style_path = next((name for name in pack.inputs
                       if Path(name).as_posix().endswith('/' + pack.learning_style['path'])), None)
    references = [{'path': style_path, 'sha256': pack.learning_style['sha256']}] if style_path else []
    audit = {'learning_style': pack.learning_style, 'items': {k: {
        'status': 'not_run', 'reviewer': '', 'rules': {rule: {
            'disposition': '', 'evidence': ''} for rule in pack.learning_style['rule_ids']}} for k in keys}}
    return {'review_policy_version': POLICY_VERSION, 'input_hash': payload_hash(pack, fragments),
            'references': references, 'learning_style_audit': audit,
            'source_visual': dict(pending), 'browser': dict(pending),
            'content': {**pending, 'items': {k: dict(pending) for k in keys}},
            'independent': {**pending, 'items': {k: {**pending, 'method': '', 'conclusion': ''} for k in keys}}}

def validate_review_records(snapshot, item_ids, reviews, *, input_hash):
    """Check published review records without requiring unpublished raw fragments."""
    errors = []
    if not isinstance(reviews, dict):
        return ['검토 기록은 JSON 객체여야 해요']
    if reviews.get('review_policy_version') != POLICY_VERSION:
        errors.append('검토 기준 변경: 현재 기준으로 실제 검토가 필요해요')
    if reviews.get('input_hash') != input_hash:
        errors.append('입력·조각 hash가 검토와 달라요')
    expected = set(item_ids)
    errors.extend('개인화: ' + error for error in validate_style_audit(
        reviews.get('learning_style_audit'), snapshot, sorted(expected)))
    def check(entry, label):
        if not isinstance(entry, dict):
            errors.append(f'{label}: 검토 없음')
            return False
        if entry.get('status') != 'pass' or any(not isinstance(entry.get(k), str) or not entry[k].strip() for k in ('reviewer', 'evidence')):
            errors.append(f'{label}: 실제 검토 pass/reviewer/evidence 필요')
        return True
    for kind in ('source_visual', 'content', 'independent', 'browser'):
        entry = reviews.get(kind)
        if not check(entry, kind) or kind not in ('content', 'independent'):
            continue
        items = entry.get('items', {})
        if not isinstance(items, dict) or set(items) != expected:
            errors.append(f'{kind}: 모든 문항/소문항 검토 필요')
            continue
        for key, item in items.items():
            if not check(item, key) or kind != 'independent':
                continue
            errors.extend(independent_errors(key, item))
    return errors


def validate_reviews(pack, fragments, reviews):
    errors = validate_review_records(pack.learning_style,
        [f'{p.id}:{s}' for p in pack.problems for s in p.subparts], reviews,
        input_hash=payload_hash(pack, fragments))
    if set(fragments) != {p.id for p in pack.problems}:
        errors.append('문항별 설명 조각 집합 불일치')
    return errors
