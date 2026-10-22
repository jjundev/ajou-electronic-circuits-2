"""Read-only checks shared by study notes and explanations; never rewrite sentences."""
import re
from html2md import Builder, Node

# These are source locators, not circuit time quantities (ms, tau) or ordinary clock examples.
LOCATION_RE = re.compile(
    r'\bSTT\s*(?:L\s*\d|\d{1,3}:\d{2}|(?:줄|라인)\s*\d)'
    r'|\bPart\s+\d{2}\b|시각\s*정보\s*없음'
    r'|[（(]\s*\d{4}\s+\d{1,3}:\d{2}(?::\d{2})?\s*[)）]'
    r'|\bSTT\s*(?:타임스탬프|timestamp)\s*[:：]?\s*\d', re.I)
MATH_RE = re.compile(r'\$\$[\s\S]*?\$\$|(?<!\\)\$(?:\\.|[^$])*?\$')
# Deliberately Korean sentence endings, not generic periods: 0.5, Fig., units and TeX survive.
END_RE = re.compile(r'(?:[가-힣]+(?:요|다)|함|임|됨|것)[.!?](?=\s|$|[”’"\'])')


def public_location_errors(text):
    return [('public-source-location', m.group(0)) for m in LOCATION_RE.finditer(text)]


def _readable_text(node):
    if isinstance(node, str):
        return node
    if node.tag in ('script', 'style', 'pre', 'code'):
        return ''
    return ''.join(_readable_text(c) for c in node.children)


def readability_errors(source):
    parser = Builder()
    parser.feed(source)
    root = parser.root
    errors = public_location_errors(_readable_text(root))
    errors.extend(gain_route_errors(root))
    for node in root.find_all(lambda n: True):
        for key in ('title', 'aria-label', 'alt', 'data-tooltip'):
            errors.extend(public_location_errors(node.attrs.get(key, '')))
        if 'review-workload' in node.classes:
            errors.append(('review-workload', '학습량 행은 공개 HTML에 출력하지 않아요'))
        if 'sum' not in node.classes:
            continue
        for p in node.find_all(lambda n: n.tag in ('p', 'li', 'dd')):
            # Parent list items may own separate sentence paragraphs: validate the leaves only.
            if any(isinstance(c, Node) and c.tag in ('p', 'li', 'dd', 'ul', 'ol', 'dl') for c in p.children):
                continue
            text = MATH_RE.sub(' 수식 ', p.text())
            if len(END_RE.findall(text)) > 1:
                errors.append(('summary-sentence', '요약은 한 문장마다 별도 문단으로 작성해요: ' + text.strip()[:80]))
            if p.tag == 'p' and not p.text().strip():
                errors.append(('summary-spacing', '요약의 빈 문단을 간격으로 사용하지 않아요'))
        if re.search(r'<br\s*/?>\s*<br\s*/?>', source_summary(node), re.I):
            errors.append(('summary-spacing', '요약의 연속 br 대신 문단을 사용해요'))
    return list(dict.fromkeys(errors))


def source_summary(node):
    # Only the tag structure matters here; preserve text for adjacent-br detection.
    if isinstance(node, str):
        return node
    return '<' + node.tag + '>' + ''.join(source_summary(c) for c in node.children) + '</' + node.tag + '>' if node.tag != 'br' else '<br>'


# Opt-in authorship contract. No equation-specific regex can prove a circuit result.
# Unmarked historic routes are left for the GAIN-01 semantic review, not guessed here.
def _explicitly_hidden(node):
    if 'hidden' in node.attrs or node.attrs.get('aria-hidden', '').lower() == 'true':
        return True
    if node.classes & {'hidden', 'd-none', 'sr-only', 'visually-hidden'}:
        return True
    style = re.sub(r'\s+', '', node.attrs.get('style', '')).lower()
    return bool(re.search(r'(?:^|;)(?:display:none|visibility:(?:hidden|collapse)|opacity:0)(?:!important)?(?:;|$)', style))


def _has_hidden_ancestor(node):
    while node is not None:
        if _explicitly_hidden(node):
            return True
        node = node.parent
    return False


def _visible_math_text(node):
    if isinstance(node, str):
        return node
    if (_explicitly_hidden(node) or node.tag in ('script', 'style', 'pre', 'code',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'svg')):
        return ''
    return ''.join(_visible_math_text(c) for c in node.children)


def gain_route_errors(root):
    errors = []
    routes = list(root.find_all(lambda n: 'data-gain-route' in n.attrs))
    stages = list(root.find_all(lambda n: 'data-gain-stage' in n.attrs))
    def owner(node):
        node = node.parent
        while node is not None:
            if 'data-gain-route' in node.attrs:
                return node
            node = node.parent
        return None
    for stage in stages:
        if owner(stage) is None:
            errors.append(('gain-route', 'data-gain-stage는 gm-rout 경로 안에 있어야 해요'))
    for route in routes:
        if route.attrs['data-gain-route'] != 'gm-rout' or owner(route) is not None:
            errors.append(('gain-route', 'gain 경로는 중첩 없이 gm-rout으로 선언해요'))
        owned = [n for n in stages if owner(n) is route]
        if [n.attrs['data-gain-stage'] for n in owned] != ['gm', 'rout', 'gain']:
            errors.append(('gain-route', '보이는 G_m → R_out → 이득 단계를 각각 한 번 순서대로 작성해요'))
        for stage in owned:
            if any(n is not stage and n in owned for n in stage.find_all(lambda n: 'data-gain-stage' in n.attrs)):
                errors.append(('gain-route', 'gain 단계는 서로 중첩하지 않아요'))
            text = _visible_math_text(stage)
            formulas = MATH_RE.findall(text)
            if (_has_hidden_ancestor(stage) or not any(f.strip('$').strip() for f in formulas)):
                errors.append(('gain-route', stage.attrs['data-gain-stage'] + ': 제목 밖에 숨기지 않은 중간 수식이 필요해요'))
    return errors
