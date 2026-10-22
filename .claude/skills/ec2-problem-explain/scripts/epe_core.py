"""Validate shared core routes and export their final-stage DOM without rewriting it."""
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from epe_shared import Node, parse, inner, check_style, PERSONALIZED_REVIEW_POLICY
from epe_types import ExplainError, Problem, SourcePack

OVERLAY_POLICY_VERSION = PERSONALIZED_REVIEW_POLICY
CORE_MARKERS = ('data-core-subpart', 'data-solution-core', 'data-core-label')


def _elements(node):
    return [child for child in node.children if isinstance(child, Node)]


def _has_body(node):
    if isinstance(node, str):
        return bool(node.strip())
    if node.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        return False
    if node.tag in ('img', 'svg'):
        return True
    return any(_has_body(child) for child in node.children)


def _core_nodes(problem, markup):
    root = parse(markup)
    errors = []
    routes = list(root.find_all(lambda n: n.attrs.get('data-personalization') == 'route'))
    if len(routes) != 1:
        return root, None, [], ['직계 핵심 풀이 route 하나 필요']
    route = routes[0]
    if route.parent is not root or not {'layer', 'formal', 'solution-route'} <= route.classes or route.tag != 'div':
        errors.append('핵심 풀이 route는 직계 div.layer.formal.solution-route여야 해요')
    sections = list(root.find_all(lambda n: 'data-explanation' in n.attrs))
    if route.parent is root and any(n.parent is root and root.children.index(n) < root.children.index(route) for n in sections):
        errors.append('핵심 풀이 route는 일곱 설명 구역보다 먼저 와야 해요')
    headings = [n for n in _elements(route) if n.tag == 'h4']
    if len(headings) != 1 or not headings[0].text().strip():
        errors.append('핵심 풀이 route에는 내용이 있는 직계 h4 제목 하나 필요')
    if any((isinstance(c, str) and c.strip()) or
           (isinstance(c, Node) and c.tag != 'h4' and 'data-core-subpart' not in c.attrs)
           for c in route.children):
        errors.append('핵심 풀이의 모든 내용은 소문항 step/answer 안에 작성하세요')
    groups = list(route.find_all(lambda n: 'data-core-subpart' in n.attrs))
    if [g.attrs['data-core-subpart'] for g in groups] != list(problem.subparts):
        errors.append('핵심 풀이의 모든 소문항을 원문 순서대로 각각 한 번 작성하세요')
    if any('data-subpart' in node.attrs for node in [route, *route.find_all(lambda n: True)]):
        errors.append('data-subpart는 상세 solve/verify 전용이에요; 핵심 풀이에는 data-core-subpart를 쓰세요')
    allowed = {id(route)}
    for group in groups:
        allowed.add(id(group))
        if group.parent is not route or group.tag != 'div' or 'data-solution-core' in group.attrs:
            errors.append('핵심 소문항 그룹은 route의 직계 div여야 해요 (core 중첩 금지)')
        entries = _elements(group)
        kinds = [n.attrs.get('data-solution-core') for n in entries]
        if len(kinds) < 2 or kinds[-1:] != ['answer'] or any(k != 'step' for k in kinds[:-1]):
            errors.append('핵심 소문항마다 step 1개 이상과 마지막 answer 하나 필요')
        if any(isinstance(c, str) and c.strip() for c in group.children):
            errors.append('핵심 소문항 내용은 step/answer 안에 작성하세요')
        for entry in entries:
            allowed.add(id(entry))
            if entry.tag != 'div' or not _has_body(entry):
                errors.append('핵심 step/answer는 내용이 있는 div여야 해요')
            if entry.attrs.get('data-solution-core') == 'step':
                label = entry.attrs.get('data-core-label', '')
                if not label.strip() or '<' in label or '>' in label:
                    errors.append('핵심 step label은 비어 있지 않은 일반 텍스트여야 해요')
            elif 'data-core-label' in entry.attrs:
                errors.append('핵심 label은 step에서만 사용하세요')
    for node in root.find_all(lambda n: any(k in n.attrs for k in CORE_MARKERS)):
        if id(node) not in allowed or node is route:
            errors.append('핵심 표지는 route의 직계 그룹/step/answer에서만 사용하세요 (중첩 금지)')
        if 'data-core-label' in node.attrs and node.attrs.get('data-solution-core') != 'step':
            errors.append('핵심 label은 step에서만 사용하세요')
    return root, route, groups, errors


def validate_core(problem: Problem, markup: str) -> list[str]:
    """Check core structure independently of the seven detailed sections."""
    return _core_nodes(problem, markup)[3]


def extract_core(problem: Problem, markup: str) -> dict:
    """Keep equations and HTML content; labels remain plain text for consumers to escape."""
    if not list(parse(markup).find_all(lambda n: n.attrs.get("data-personalization") == "route")):
        from epe_solution import extract_solution
        return extract_solution(problem, markup)
    if list(parse(markup).find_all(lambda n: any(k in n.attrs for k in
            ('data-answer-step', 'data-answer-final', 'data-answer-subpart')))):
        raise ExplainError(f'{problem.id}: 구형 route와 통합 답안 표지 혼합 금지')
    _, _, groups, errors = _core_nodes(problem, markup)
    if errors:
        raise ExplainError(f'{problem.id}: ' + ' / '.join(errors))
    if not problem.workbook_id.strip():
        raise ExplainError(f'{problem.id}: workbook ID 누락')
    steps, answers = [], []
    for group in groups:
        subpart = group.attrs['data-core-subpart']
        for entry in _elements(group):
            item = {'subpart': subpart, 'html': inner(entry)}
            if entry.attrs['data-solution-core'] == 'step':
                item['label'] = entry.attrs['data-core-label']
                steps.append(item)
            else:
                answers.append(item)
    return {'id': problem.workbook_id, 'explanation_id': problem.id,
            'subparts': list(problem.subparts), 'steps': steps, 'answers': answers}


def make_overlay(pack: SourcePack, stage_html: Path, repo: Path) -> dict:
    """Read the final stage route and its manifest's original-fragment payload hash."""
    from epe_source import inside, existing_path, sha256

    stage_html, repo = Path(stage_html), Path(repo)
    stage = stage_html.parent.resolve()
    manifest_path = stage / '.assets' / f'자료_문제설명_{pack.range}_{pack.slug}' / 'manifest.json'
    try:
        check_style(repo, pack.learning_style)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or type(manifest.get('version')) is not int or manifest['version'] != 1:
            raise ExplainError('지원하지 않는 stage manifest version')
        input_hash = manifest['input_hash']
        if not isinstance(input_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', input_hash):
            raise ExplainError('stage manifest의 input_hash가 올바르지 않아요')
        document = parse(stage_html.read_text(encoding='utf-8'))
        problems = []
        for problem in pack.problems:
            articles = list(document.find_all(lambda n: n.tag == 'article' and n.attrs.get('id') == problem.id))
            if len(articles) != 1:
                raise ExplainError(f'{problem.id}: stage 문항을 정확히 하나 찾을 수 있어야 해요')
            problems.append(extract_core(problem, inner(articles[0])))
        source_inputs = {}
        for name in (*pack.inputs, str(repo / pack.learning_style['path'])):
            path = inside(existing_path(Path(name)), repo)
            source_inputs[path.resolve().relative_to(repo.resolve()).as_posix()] = sha256(path)
        assets = {}
        for problem in problems:
            for item in (*problem['steps'], *problem['answers']):
                for image in parse(item['html']).find_all(lambda n: n.tag == 'img'):
                    src = image.attrs.get('src', '')
                    url = urlsplit(src)
                    if url.scheme or url.netloc or not url.path or Path(unquote(url.path)).is_absolute():
                        raise ExplainError('overlay 그림은 stage 상대 경로여야 해요: ' + src)
                    path = inside(existing_path(stage / unquote(url.path)), stage)
                    assets[src] = sha256(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, ExplainError):
            raise
        raise ExplainError(f'답안 overlay 생성 실패 (stage manifest/입력/그림 확인): {exc}') from exc
    return {'schema_version': 1, 'review_policy_version': OVERLAY_POLICY_VERSION,
            'range': pack.range, 'slug': pack.slug, 'learning_style': pack.learning_style,
            'input_hash': input_hash, 'source_inputs': source_inputs, 'problems': problems, 'assets': assets}
