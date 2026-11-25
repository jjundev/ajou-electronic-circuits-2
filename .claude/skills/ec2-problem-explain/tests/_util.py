"""Shared test helpers: puts scripts/ on sys.path and builds a minimal temp repo."""
import os
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))

# RUN folders and publication locks made by tests stay out of the user's ~/.cache.
# A spawned process re-imports this module and must keep its parent's locks.
if "EC2_CACHE_ROOT" not in os.environ:
    _cache_temp = tempfile.TemporaryDirectory(prefix="ec2-test-cache-", ignore_cleanup_errors=True)
    os.environ["EC2_CACHE_ROOT"] = _cache_temp.name

from epe_shared import (REPO, load_problem, problem_figures, textbook_figure_filename,  # noqa: E402
                        exam_figure_filename, TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR)
from epe_types import Problem, SourcePack  # noqa: E402

TEXTBOOK = Path('교과서/마이크로전자회로')
EXAMS = Path('from_the_past/md')


def _nfc(text):
    return unicodedata.normalize('NFC', text)


def _copy(rel, dest_root, optional=False):
    src = REPO / rel
    if not src.exists():
        if optional:
            return
        raise FileNotFoundError(src)
    dst = dest_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def _copy_problem(pid, dest_root):
    if m := TEXTBOOK_ID_RE.match(pid):
        md = TEXTBOOK / f'ch{int(m.group(2)):02d}' / KIND_DIR[m.group(1)] / f'{pid}.md'
        fig_dir = TEXTBOOK / f'ch{int(m.group(2)):02d}' / 'figures'
        exam = False
    elif m := EXAM_ID_RE.match(pid):
        md = EXAMS / m.group(1) / f'Q{m.group(2)}.md'
        fig_dir = EXAMS / m.group(1) / 'figures'
        exam = True
    else:
        raise ValueError(pid)
    _copy(md, dest_root)
    _copy(fig_dir / 'figures.yaml', dest_root, optional=True)
    if exam:
        _copy(md.parent / 'exam.yaml', dest_root)
    problem = load_problem(REPO / md)
    for fig_id, crop in problem_figures(problem):
        name = exam_figure_filename(fig_id) if exam else textbook_figure_filename(fig_id, crop)
        _copy(fig_dir / name, dest_root)
        if exam:  # redrawn art only exists for some figures
            _copy(fig_dir / 'redrawn' / name, dest_root, optional=True)


def make_repo(tmp, *, range_='1007', slug='Diff_Amp', ids=('P10.02', '2023-1_중간-Q4'), nfd=False):
    tmp = Path(tmp)
    form = (lambda s: unicodedata.normalize('NFD', s)) if nfd else (lambda s: s)
    _copy(Path('.claude/skills/ec2-review-pack/references/solution-style.md'), tmp)
    for pid in ids:
        _copy_problem(_nfc(pid), tmp)
    folder = tmp / form('복습노트') / range_
    (folder / '.assets').mkdir(parents=True, exist_ok=True)
    (folder / '.assets' / 'problems.txt').write_text(
        ''.join(f'{pid} | 테스트용 설명 {i}\n' for i, pid in enumerate(ids, 1)), encoding='utf-8')
    (folder / form(f'정리노트_{range_}_{slug}.html')).write_text(
        '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>정리노트</title></head>'
        '<body><article class="topic" id="s1-diff"><h2>차동쌍</h2><p>본문</p></article></body></html>\n',
        encoding='utf-8')
    (folder / form(f'복습문제_{range_}_{slug}-문제.pdf')).write_bytes(b'%PDF-1.4\ndummy\n')
    return tmp


def problem():
    return Problem('p1', 1, '행렬', 'HW1 Problem 1', '<p>Find (a), (b).</p>',
                   '<p>$A=1$</p>', '<ol><li>(a) $A$</li><li>(b) $A^2$</li></ol>',
                   (), ('계산',), '1', ('a', 'b'), 'E9.05')


def core_route(p):
    groups = ''.join(f'<div data-core-subpart="{key}">'
                     '<div data-solution-core="step" data-core-label="회로 판단">'
                     '<p>판단과 식은 $1=1$이에요.</p></div>'
                     '<div data-solution-core="answer"><p>최종 답은 $1$이에요.</p></div></div>'
                     for key in p.subparts)
    return '<div class="layer formal solution-route" data-personalization="route"><h4>핵심 풀이</h4>' + groups + '</div>'


def core_fragment(p):
    return legacy_fragment(p)


def legacy_fragment(p=None):
    p = p or problem()
    parts = ''.join(f'<div data-subpart="{key}"><p>첫 식에서 계산하고 대입해 확인해요. $1=1$</p></div>'
                    for key in p.subparts)
    return (core_route(p) + '<div class="layer eli5" data-explanation="understand"><p>구할 것을 읽어요.</p></div>'
            '<div class="layer formal" data-explanation="recall">'
            '<h4>이 개념과 공식을 떠올려요</h4>'
            '<p>제곱을 구하라는 단서에서 같은 수의 곱을 떠올려요. '
            '$A^2=A\\cdot A$이며 A는 주어진 스칼라예요.</p></div>'
            '<div class="layer formal" data-explanation="start"><p>$A=1$부터 써요.</p></div>'
            f'<div class="layer formal" data-explanation="solve">{parts}</div>'
            f'<div class="layer formal" data-explanation="verify">{parts}</div>'
            '<div class="layer warn" data-explanation="pitfall"><p>행과 열을 바꾸지 않아요.</p></div>'
            '<div class="layer formal" data-explanation="retry"><ul><li>다시 계산해요.</li></ul></div>'
            '<div class="sum" hidden><p>시작·판단·검산</p></div>')


def fragment(p=None):
    """New authoring fixture: selected body, never a separate core copy."""
    from epe_solution import SECTION_TITLES
    p = p or problem()
    solve = ''.join(f'<div data-subpart="{key}"><div data-answer-step="회로 판단">'
        '<p>판단과 식은 $1=1$이에요.</p></div></div>' for key in p.subparts)
    verify = ''.join(f'<div data-subpart="{key}"><div data-answer-final>'
        '<p>최종 답은 $1$이에요.</p></div></div>' for key in p.subparts)
    bodies = ['<p>구할 것을 읽어요.</p>',
        '<p>제곱을 구하라는 단서에서 같은 수의 곱을 떠올려요. '
        '$A^2=A\\cdot A$이며 A는 주어진 스칼라예요.</p>',
        '<p>$A=1$부터 써요.</p>', solve, verify,
        '<p>행과 열을 바꾸지 않아요.</p>', '<ul><li>다시 계산해요.</li></ul>']
    return ''.join(f'<div class="layer {layer}" data-explanation="{key}"><h4>{title}</h4>{body}</div>'
        for (key,title),body,layer in zip(SECTION_TITLES.items(),bodies,
        ('eli5','formal','formal','formal','formal','warn','formal'))) + '<div class="sum" hidden><p>시작·판단·검산</p></div>'


def pack(path=Path('.assets/problems.txt')):
    from epe_shared import read_style
    return SourcePack('review', '1007', 'Diff_Amp', path, '0' * 64, (problem(),), (), read_style(REPO))


def approved(pack, fragments, artifacts=None):
    from epe_contract import payload_hash
    base = {'status': 'pass', 'reviewer': 'test fixture', 'evidence': 'fixture calculation at evidence.txt'}
    keys = [f'{p.id}:{s}' for p in pack.problems for s in p.subparts]
    from epe_review_policy import POLICY_VERSION
    result = {'review_policy_version': POLICY_VERSION, 'input_hash': payload_hash(pack, fragments),
              'source_visual': dict(base), 'browser': dict(base),
              'content': {**base, 'items': {k: dict(base) for k in keys}},
              'independent': {**base, 'items': {k: {**base, 'method': 'exact', 'conclusion': '1=1'} for k in keys}},
              'learning_style_audit': {'learning_style': pack.learning_style, 'items': {k: {
                  'status': 'pass', 'reviewer': 'unit test fixture (not actual review)',
                  'rules': {rule: {'disposition': 'not_applicable',
                      'evidence': 'unit test fixture only; no actual semantic review'}
                      for rule in pack.learning_style['rule_ids']}} for k in keys}},
              'references': [{'path': next((name for name in pack.inputs
                  if name.replace('\\', '/').endswith('/' + pack.learning_style['path'])),
                  str(REPO / pack.learning_style['path'])), 'sha256': pack.learning_style['sha256']}]}
    if artifacts:
        from epe_render import artifact_hashes
        result['artifact_hashes'] = artifact_hashes(artifacts)
    return result
