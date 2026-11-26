"""Validate the integrated formal body and select its existing answer elements.

Selection attributes annotate visible content; they never create a second route.
Legacy extraction lives in epe_core solely for intact historic publications.
"""
from epe_shared import Node, parse, inner, outer
from epe_types import ExplainError

SECTION_TITLES = {
    'understand': '문제를 읽어요',
    'recall': '이 개념과 공식을 떠올려요',
    'start': '종이에 쓸 첫 줄',
    'solve': '이렇게 풀어요',
    'verify': '완성 답과 검산',
    'pitfall': '주의할 점',
    'retry': '조건을 바꾸어 생각해요',
}
SELECTION = ('data-answer-step', 'data-answer-final', 'data-answer-subpart')
LEGACY = ('data-personalization', 'data-core-subpart', 'data-solution-core', 'data-core-label')
CONCISE_CLASS = 'circuit-explanation'


def _body(node):
    if isinstance(node, str):
        return bool(node.strip())
    if node.tag.startswith('h') and node.tag[1:] in ('1', '2', '3', '4', '5', '6'):
        return False
    return node.tag in ('img', 'svg') or any(_body(c) for c in node.children)


def _fixed_circuit(node, section):
    return (section is not None and node.parent is section
            and section.attrs.get('data-explanation') == 'solve'
            and CONCISE_CLASS in section.classes
            and node.tag == 'figure' and 'circuit' in node.classes)


def solution_nodes(problem, markup, *, fragment_only=True):
    root = parse(markup)
    errors, steps, answers = [], [], []
    sections = list(root.find_all(lambda n: 'data-explanation' in n.attrs))
    concise = any(CONCISE_CLASS in section.classes for section in sections)
    expected_sections = ['solve'] if concise else list(SECTION_TITLES)
    if [n.attrs['data-explanation'] for n in sections] != expected_sections:
        errors.append('간략 해설은 단일 solve 구역이 필요해요' if concise
                      else '통합 일곱 설명 구역과 원문 순서가 필요해요')
    if any(list(root.find_all(lambda n: k in n.attrs)) for k in LEGACY):
        errors.append('새 저작에는 별도 핵심 풀이 route/구형 표지를 넣지 마세요')
    for child in root.children if fragment_only else ():
        if isinstance(child, str):
            if child.strip():
                errors.append('구역 밖 본문 금지')
        elif child not in sections and not (child.tag == 'div' and 'sum' in child.classes
                                            and 'hidden' in child.attrs):
            errors.append('간략 해설의 직계 요소는 단일 solve와 숨긴 sum뿐이어야 해요' if concise
                          else '통합 원고의 직계 요소는 일곱 구역과 숨긴 sum뿐이어야 해요')
    groups = {}
    for section in sections:
        key = section.attrs['data-explanation']
        headings = [n for n in section.children if isinstance(n, Node) and n.tag == 'h4']
        if section.parent is not root or not _body(section):
            errors.append(f'{key}: 내용이 있는 직계 구역과 확정한 h4 제목이 필요해요')
        elif not concise and (len(headings) != 1 or headings[0].text().strip() != SECTION_TITLES.get(key)):
            errors.append(f'{key}: 내용이 있는 직계 구역과 확정한 h4 제목이 필요해요')
        items = list(section.find_all(lambda n: 'data-subpart' in n.attrs))
        if key in ('solve', 'verify'):
            if ([n.attrs['data-subpart'] for n in items] != list(problem.subparts)
                    or any(n.parent is not section or not _body(n) for n in items)):
                errors.append(f'{key}: 모든 소문항을 원문 순서의 직계 그룹으로 작성하세요')
            for n in items:
                groups[id(n)] = n.attrs['data-subpart']
        elif items:
            errors.append('data-subpart 그룹은 solve/verify에만 사용하세요')
    body_step_subparts = set()
    for node in root.find_all(lambda n: any(k in n.attrs for k in SELECTION)):
        step, final = 'data-answer-step' in node.attrs, 'data-answer-final' in node.attrs
        ancestors = []
        parent = node.parent
        while parent is not None and parent is not root:
            ancestors.append(parent)
            parent = parent.parent
        section = next((n for n in ancestors if 'data-explanation' in n.attrs), None)
        group = next((n for n in [node, *ancestors] if id(n) in groups), None)
        key = section.attrs['data-explanation'] if section else ''
        subpart = groups.get(id(group)) if group else None
        explicit = node.attrs.get('data-answer-subpart')
        fixed_step = step and _fixed_circuit(node, section)
        if fixed_step:
            subpart = explicit
            if not any(node.find_all(lambda n: n.tag in ('svg', 'img'))):
                errors.append('답안에 넣는 고정 회로에 SVG 또는 이미지가 필요해요')
                continue
        elif key == 'start':
            subpart = explicit or (problem.subparts[0] if len(problem.subparts) == 1 else None)
        if (step == final or not _body(node) or key not in ('start', 'solve', 'verify')
                or (final and key != ('solve' if concise else 'verify')) or (step and key == 'verify')
                or subpart not in problem.subparts or (explicit is not None and explicit != subpart)
                or any(any(k in n.attrs for k in SELECTION[:2]) for n in ancestors)):
            errors.append('solve의 소문항 안에 step과 final을 쓰고, 직계 고정 회로 step에 대상 소문항을 표시하세요'
                          if concise else
                          '답안 선택은 start/solve의 비중첩 step 또는 verify의 final이며 소문항 범위가 명확해야 해요')
            continue
        if step:
            label = node.attrs['data-answer-step']
            if not label.strip() or '<' in label or '>' in label:
                errors.append('답안 step 제목은 비어 있지 않은 일반 텍스트여야 해요')
            steps.append((subpart, label, node))
            if not fixed_step:
                body_step_subparts.add(subpart)
        else:
            answers.append((subpart, node))
    for subpart in problem.subparts:
        if subpart not in body_step_subparts:
            errors.append(f'{subpart}: 본문의 답안 step 하나 이상 필요')
        if sum(s == subpart for s, _ in answers) != 1:
            errors.append(f'{subpart}: 본문의 답안 final 정확히 하나 필요')
    return steps, answers, errors


def extract_solution(problem, markup):
    steps, answers, errors = solution_nodes(problem, markup, fragment_only=False)
    if errors or not problem.workbook_id.strip():
        raise ExplainError(f'{problem.id}: ' + ' / '.join(errors or ['workbook ID 누락']))

    def answer_markup(node):
        section = node.parent
        while section is not None and 'data-explanation' not in section.attrs:
            section = section.parent
        if section is not None and CONCISE_CLASS in section.classes:
            # Answer sheets use node and component names without HTML location marks.
            for mark in list(node.find_all(lambda n: n.tag == 'span' and 'loc' in n.classes)):
                mark.parent.children.remove(mark)
            if _fixed_circuit(node, section):
                for mark in list(node.find_all(lambda n: 'fig-loc' in n.classes)):
                    mark.parent.children.remove(mark)
        return inner(node) if node.tag == 'div' else outer(node)

    return {'id': problem.workbook_id, 'explanation_id': problem.id,
            'subparts': list(problem.subparts),
            'steps': [{'subpart': s, 'label': label, 'html': answer_markup(n)}
                      for s in problem.subparts for part, label, n in steps if part == s],
            'answers': [{'subpart': s, 'html': answer_markup(n)}
                        for s in problem.subparts for part, n in answers if part == s]}
