"""The fixed circuit can be selected as an answer step without duplicating it."""
from dataclasses import replace
import re

import pytest

from _util import SKILL, approved, make_repo, problem
from epe_core import extract_core
from epe_publish import publish_explanation
from epe_render import build_explanation, check_artifacts
from epe_source import load_source
from epe_types import ExplainError


FIGURE = (
    '<figure class="figure circuit" data-answer-step="개루프 회로" data-answer-subpart="a">'
    '<svg viewBox="0 0 100 100"><path d="M10 10 H90"/>'
    '<text class="fig-loc" x="10" y="20">㉠</text></svg>'
    '<figcaption>개루프 회로의 출력 가지</figcaption></figure>'
)


def concise(problem, figure=FIGURE):
    groups = ''.join(
        f'<div data-subpart="{key}"><h4>첫 식과 답</h4>'
        '<p data-answer-step="첫 식">출력 가지의 저항을 적용해요.</p>'
        '<div data-answer-final>$$R=2$$</div></div>'
        for key in problem.subparts
    )
    return ('<div class="layer formal circuit-explanation" data-explanation="solve">'
            + figure + groups + '</div><div class="sum" hidden><p>출력 가지를 확인해요.</p></div>')


def test_shared_fixed_circuit_is_exported_once_for_the_explicit_subpart():
    p = problem()
    result = extract_core(p, concise(p))
    assert [(step['subpart'], step['label']) for step in result['steps']] == [
        ('a', '개루프 회로'), ('a', '첫 식'), ('b', '첫 식')
    ]
    circuit = result['steps'][0]['html']
    assert '<figure' in circuit
    assert '<path d="M10 10 H90"/>' in circuit
    assert '<figcaption>개루프 회로의 출력 가지</figcaption>' in circuit
    assert 'fig-loc' not in circuit and '㉠' not in circuit
    assert [answer['subpart'] for answer in result['answers']] == ['a', 'b']


@pytest.mark.parametrize('figure', [
    FIGURE.replace(' data-answer-subpart="a"', ''),
    FIGURE.replace('data-answer-subpart="a"', 'data-answer-subpart="z"'),
    FIGURE.replace('class="figure circuit"', 'class="figure"'),
    FIGURE.replace('data-answer-step="개루프 회로"', 'data-answer-final'),
    re.sub(r'<svg.*?</svg>', '', FIGURE),
])
def test_fixed_circuit_does_not_infer_subpart_or_serve_as_final(figure):
    with pytest.raises(ExplainError):
        extract_core(problem(), concise(problem(), figure))


def test_concise_diagnostics_point_to_the_current_structure():
    from epe_contract import validate_fragment

    p = problem()
    markup = concise(p, FIGURE.replace(' data-answer-subpart="a"', '')) + '<p>구역 밖 문단</p>'
    errors = validate_fragment(p, markup, allow_legacy=False)
    assert any('단일 solve' in error and 'sum' in error for error in errors)
    assert any('solve' in error and '회로' in error and '소문항' in error for error in errors)
    assert all('일곱' not in error and 'verify' not in error for error in errors)


def test_fixed_circuit_cannot_replace_a_selected_step_in_the_subpart():
    p = replace(problem(), subparts=('a',))
    markup = concise(p).replace(' data-answer-step="첫 식"', '')
    with pytest.raises(ExplainError, match=r'^p1: a: 본문의 답안 step'):
        extract_core(p, markup)


def test_authoring_example_preserves_its_actual_circuit_through_answers_pdf(tmp_path):
    from answer_overlay import apply_answer_overlay, load_answer_overlay
    from epe_shared import workbook_assemble  # the name `assemble` may be either module
    build_data, ids_selection = workbook_assemble().build_data, workbook_assemble().ids_selection
    from render import inject, load_template, render_pdf
    import pymupdf

    authoring = (SKILL / 'references/authoring.md').read_text(encoding='utf-8')
    markup = re.search(r'```html\n(.*?)\n```', authoring, re.S)[1]
    # The sample isolates the output loading step of this feedback circuit.
    ids = ['E12.26']
    repo = make_repo(tmp_path / 'repo', range_='1120', slug='Nonideal_IO_Feedback', ids=ids)
    pack = load_source(repo / '복습노트/1120/.assets/problems.txt', repo)
    fragments = {'p1': markup}
    artifacts = build_explanation(pack, fragments, tmp_path / 'stage', repo)
    assert check_artifacts(pack, artifacts) == []
    caption = '감지 포트를 개방한 출력 부하망'
    assert caption in artifacts.html.read_text(encoding='utf-8')
    assert 'class="fig-loc"' in artifacts.html.read_text(encoding='utf-8')
    assert caption in artifacts.md.read_text(encoding='utf-8')
    assert any('fig-loc' in svg.read_text(encoding='utf-8')
               for svg in artifacts.files if svg.suffix == '.svg')

    publish_explanation(pack, artifacts, fragments, approved(pack, fragments, artifacts),
                        pack.folder, tmp_path / 'backups', repo)
    overlay_path = pack.folder / artifacts.manifest.parent.relative_to(artifacts.html.parent) / 'answer-overlay.json'
    overlay = load_answer_overlay(overlay_path, repo, ids)
    steps = overlay['problems'][0]['steps']
    assert steps[0]['label'] == '개루프 회로'
    assert caption in steps[0]['html'] and '<svg' in steps[0]['html']
    assert all('fig-loc' not in step['html'] and '㉠' not in step['html'] for step in steps)

    data = apply_answer_overlay(build_data(ids_selection(ids, '고정 회로'), 'answers'),
                                overlay, html_dir=tmp_path)
    answer_html = tmp_path / 'answer.html'
    answer_html.write_text(inject(load_template('answers'), data), encoding='utf-8')
    answer_pdf = tmp_path / 'answer.pdf'
    assert render_pdf(answer_html, answer_pdf) == []
    with pymupdf.open(answer_pdf) as pdf:
        text = ''.join(page.get_text() for page in pdf)
        assert caption in text
        assert '㉠' not in text
        assert any(sum(item[0] == 'l' for item in drawing['items']) >= 10
                   for page in pdf for drawing in page.get_drawings())
