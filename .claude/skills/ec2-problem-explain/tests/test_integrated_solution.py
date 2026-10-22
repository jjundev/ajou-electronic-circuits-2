"""Integrated authoring and final-DOM answer selection, without duplicate routes."""
from dataclasses import replace
import pytest
from _util import problem, core_route
from epe_contract import validate_fragment
from epe_core import extract_core
from epe_types import ExplainError

TITLES = ('문제를 읽어요', '이 개념과 공식을 떠올려요', '종이에 쓸 첫 줄',
          '이렇게 풀어요', '완성 답과 검산', '주의할 점', '조건을 바꾸어 생각해요')
KEYS = ('understand', 'recall', 'start', 'solve', 'verify', 'pitfall', 'retry')

def integrated(p=None):
    p = p or problem()
    bodies = ['<p>단서를 읽어요.</p>', '<p>제곱은 곱셈이에요.</p>',
              '<p data-answer-step="첫 식" data-answer-subpart="'+p.subparts[0]+'">$$A=1$$</p>',
              ''.join(f'<div data-subpart="{s}"><div data-answer-step="계산"><figure><svg viewBox="0 0 10 10"><path d="M0 0 H10"/></svg></figure>$$A^2=1$$</div><p>상세 이유는 HTML에 남아요.</p></div>' for s in p.subparts),
              ''.join(f'<div data-subpart="{s}"><p data-answer-final>최종 답은 $1$이에요.</p><p>검산은 본문에 남아요.</p></div>' for s in p.subparts),
              '<p>조건을 확인해요.</p>', '<ul><li>입력을 두 배로 바꿔 보세요.</li></ul>']
    return ''.join(f'<div class="layer {layer}" data-explanation="{key}"><h4>{title}</h4>{body}</div>'
                   for key,title,body,layer in zip(KEYS,TITLES,bodies,('eli5','formal','formal','formal','formal','warn','eli5'))) + '<div class="sum" hidden><p>요약이에요.</p></div>'

def test_integrated_build_contract_and_selected_equations():
    p = problem(); markup = integrated(p)
    assert validate_fragment(p, markup) == []
    result = extract_core(p, markup)
    assert result['id'] == p.workbook_id
    assert [(x['subpart'],x['label']) for x in result['steps']] == [('a','첫 식'),('a','계산'),('b','계산')]
    assert '$$A=1$$' in result['steps'][0]['html']
    assert '<svg' in result['steps'][1]['html']
    assert [x['subpart'] for x in result['answers']]==list(p.subparts)
    assert all('최종 답은 $1$이에요.' in x['html'] for x in result['answers'])
    assert all('상세 이유' not in x['html'] and '검산은' not in x['html'] for x in result['steps']+result['answers'])

@pytest.mark.parametrize('before,after', [
    ('이렇게 풀어요','이유를 따라 풀어요'),
    ('data-answer-final','data-old-final'),
    ('data-answer-step="계산"','data-old-step="계산"'),
    ('data-answer-subpart="a"','data-answer-subpart="z"'),
    ('data-subpart="b"','data-subpart="a"'),
    ('<div data-answer-step="계산">','<div data-answer-step="">'),
    ('<p data-answer-final>','<p data-answer-final data-answer-step="중복">'),
])
def test_integrated_invalid_selection_is_rejected(before,after):
    markup = integrated().replace(before,after)
    assert validate_fragment(problem(),markup)
    with pytest.raises(ExplainError): extract_core(problem(),markup)

def test_new_authoring_rejects_duplicate_legacy_route():
    assert validate_fragment(problem(), core_route(problem())+integrated())

def test_scalar_start_can_inherit_its_only_subpart():
    p=replace(problem(),subparts=('main',))
    markup=integrated(p).replace(' data-answer-subpart="main"','')
    assert validate_fragment(p,markup)==[]
    assert extract_core(p,markup)['steps'][0]['subpart']=='main'

def test_nested_selection_and_unscoped_multi_start_are_rejected():
    for markup in [integrated().replace('<figure>','<figure data-answer-step="중첩">'),
                   integrated().replace(' data-answer-subpart="a"','')]:
        assert validate_fragment(problem(),markup)
        with pytest.raises(ExplainError): extract_core(problem(),markup)

def test_subparts_must_follow_original_order():
    markup=integrated().replace('data-subpart="a"','data-subpart="temp"').replace('data-subpart="b"','data-subpart="a"').replace('data-subpart="temp"','data-subpart="b"')
    assert validate_fragment(problem(),markup)

@pytest.mark.parametrize('media', ['<img src="circuit.png" alt="회로">', '<svg viewBox="0 0 10 10"><path d="M0 0 H10"/></svg>'])
def test_selecting_media_itself_preserves_the_element(media):
    p=replace(problem(),subparts=('main',))
    markup=integrated(p).replace('<p data-answer-step="첫 식" data-answer-subpart="main">$$A=1$$</p>', media.replace(' ', ' data-answer-step="회로" ', 1))
    assert validate_fragment(p,markup)==[]
    result=extract_core(p,markup)['steps'][0]['html']
    assert ('<img ' if media.startswith('<img') else '<svg ') in result


def test_extractor_rejects_mixed_legacy_and_integrated_shapes():
    with pytest.raises(ExplainError):
        extract_core(problem(), core_route(problem())+integrated())

@pytest.mark.parametrize('extra', ['<p>별도 풀이</p>', '<div class="layer formal"><p>핵심 사본</p></div>', '구역 밖 본문'])
def test_only_seven_visible_sections_and_summary_are_allowed(extra):
    assert validate_fragment(problem(),extra+integrated())
