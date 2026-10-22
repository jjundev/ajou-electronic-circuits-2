"""Core routes preserve workbook identity and final-stage resources."""
from dataclasses import replace
import hashlib
import json

import pytest

from _util import problem, core_fragment, core_route, make_repo, fragment
from epe_core import validate_core, extract_core, make_overlay
from epe_contract import validate_fragment
from epe_render import build_explanation
from epe_source import load_source, resolve_sources
from epe_shared import parse, outer, inner
from epe_types import ExplainError


@pytest.fixture
def scalar_problem():
    return replace(problem(), workbook_id='E9.05', subparts=('main',))


def mutated_core(p, mutation):
    root = parse(core_fragment(p))
    route = next(root.find_all(lambda n: n.attrs.get('data-personalization') == 'route'))
    groups = [n for n in route.children if not isinstance(n, str) and 'data-core-subpart' in n.attrs]
    if mutation == 'missing_b':
        route.children.remove(groups[1])
    elif mutation == 'duplicate_a':
        groups[1].attrs['data-core-subpart'] = 'a'
    elif mutation == 'wrong_order':
        a, b = (route.children.index(g) for g in groups)
        route.children[a], route.children[b] = route.children[b], route.children[a]
    elif mutation == 'empty_answer':
        next(groups[0].find_all(lambda n: n.attrs.get('data-solution-core') == 'answer')).children = []
    elif mutation == 'nested_core':
        next(groups[0].find_all(lambda n: n.attrs.get('data-solution-core') == 'step')).attrs['data-core-subpart'] = 'a'
    elif mutation == 'route_after_recall':
        root.children.remove(route)
        recall = next(root.find_all(lambda n: n.attrs.get('data-explanation') == 'recall'))
        root.children.insert(root.children.index(recall) + 1, route)
    return inner(root)


def test_core_maps_stable_id_and_keeps_equations(scalar_problem):
    markup = core_fragment(scalar_problem).replace('<p>최종 답은 $1$이에요.</p>', '<p>$W/L=15.625$</p>')
    result = extract_core(scalar_problem, markup)
    assert result['id'] == 'E9.05'
    assert result['explanation_id'] == 'p1'
    assert result['subparts'] == ['main']
    assert result['answers'] == [{'subpart': 'main', 'html': '<p>$W/L=15.625$</p>'}]


@pytest.mark.parametrize('mutation', ['missing_b', 'duplicate_a', 'wrong_order', 'empty_answer',
                                      'nested_core', 'route_after_recall'])
def test_invalid_core_is_rejected(mutation):
    markup = mutated_core(problem(), mutation)
    assert validate_core(problem(), markup)
    with pytest.raises(ExplainError):
        extract_core(problem(), markup)


@pytest.mark.parametrize('mutation', ['no_route', 'duplicate_route', 'no_step', 'answer_first',
                                      'duplicate_answer', 'empty_label', 'markup_label', 'heading_only'])
def test_malformed_core_is_rejected(mutation):
    p = replace(problem(), subparts=('main',))
    root = parse(core_fragment(p))
    route = next(root.find_all(lambda n: n.attrs.get('data-personalization') == 'route'))
    group = next(route.find_all(lambda n: 'data-core-subpart' in n.attrs))
    step, answer = [n for n in group.children if not isinstance(n, str)]
    if mutation == 'no_route': root.children.remove(route)
    elif mutation == 'duplicate_route': root.children.insert(0, route)
    elif mutation == 'no_step': group.children.remove(step)
    elif mutation == 'answer_first': group.children = [answer, step]
    elif mutation == 'duplicate_answer': group.children.append(answer)
    elif mutation == 'empty_label': step.attrs['data-core-label'] = ' '
    elif mutation == 'markup_label': step.attrs['data-core-label'] = '<b>판단</b>'
    elif mutation == 'heading_only': answer.children = parse('<h4>답</h4>').children
    assert validate_core(p, inner(root))


def test_original_seven_sections_still_required():
    assert validate_fragment(problem(), fragment(problem())) == []
    assert validate_fragment(problem(), core_fragment(problem()))
    assert validate_fragment(problem(), core_route(problem()))
    markup = core_fragment(problem())
    recall = next(parse(markup).find_all(lambda n: n.attrs.get('data-explanation') == 'recall'))
    assert validate_fragment(problem(), markup.replace(outer(recall), ''))
    assert validate_fragment(problem(), markup.replace('class="sum"', 'class="missing-sum"'))


def test_core_does_not_count_as_solve_subparts():
    p = problem()
    text = core_fragment(p).replace('data-subpart="b"', 'data-subpart="a"', 1)
    assert any('solve' in e for e in validate_fragment(p, text))
    assert validate_core(p, text) == []


@pytest.mark.parametrize('answer', ['<p>$V=2\\,\\mathrm{V}$</p>', '<p>차단 상태이므로 전류가 흐르지 않는다.</p>'])
def test_scalar_and_qualitative_answers(scalar_problem, answer):
    markup = core_fragment(scalar_problem).replace('<p>최종 답은 $1$이에요.</p>', answer)
    assert extract_core(scalar_problem, markup)['answers'] == [{'subpart': 'main', 'html': answer}]


def test_label_is_exported_as_plain_text(scalar_problem):
    markup = core_fragment(scalar_problem).replace('data-core-label="회로 판단"', 'data-core-label="전류 &amp; 전압"')
    assert extract_core(scalar_problem, markup)['steps'][0]['label'] == '전류 & 전압'


def test_overlay_uses_stage_image_paths(tmp_path):
    repo = make_repo(tmp_path / 'repo', ids=('E9.05',))
    pfile = resolve_sources(repo, '1007')[0]
    pack = load_source(pfile, repo)
    image = pack.folder / 'core.png'
    image.write_bytes(b'route-image')
    fragments = {p.id: fragment(p).replace('<p>판단과 식은 $1=1$이에요.</p>',
                 '<p>판단과 식은 $1=1$이에요.</p><figure><img src="core.png" alt="회로"></figure>') for p in pack.problems}
    artifacts = build_explanation(pack, fragments, tmp_path / 'stage', repo)
    overlay = make_overlay(pack, artifacts.html, repo)
    assert overlay['schema_version'] == 1
    assert overlay['review_policy_version'] == 'problem-explain-2026-10-21-learning-style'
    assert overlay['range'] == '1007'
    assert overlay['slug'] == 'Diff_Amp'
    assert overlay['learning_style'] == pack.learning_style
    manifest = json.loads(artifacts.manifest.read_text(encoding='utf-8'))
    assert overlay['input_hash'] == manifest['input_hash']
    item = overlay['problems'][0]
    assert item['id'] == 'E9.05'
    assert item['explanation_id'] == 'p1'
    src = next(parse(item['steps'][0]['html']).find_all(lambda n: n.tag == 'img')).attrs['src']
    assert src.startswith('.assets/figures_') and src != 'core.png'
    assert overlay['assets'][src] == hashlib.sha256(b'route-image').hexdigest()
    assert overlay['source_inputs']['docs/learning/solution-style.md'] == pack.learning_style['sha256']
    assert overlay['source_inputs']['복습노트/1007/.assets/problems.txt'] == hashlib.sha256(pfile.read_bytes()).hexdigest()
    image_stage = artifacts.html.parent / src
    image_stage.unlink()
    with pytest.raises(ExplainError):
        make_overlay(pack, artifacts.html, repo)


@pytest.mark.parametrize('manifest_value', [None, '{invalid json', '{"version": 1}',
                                           '{"version": 1, "input_hash": "wrong"}',
                                           '{"version": 99, "input_hash": "' + '0' * 64 + '"}'])
def test_overlay_requires_known_stage_manifest(tmp_path, manifest_value):
    repo = make_repo(tmp_path / 'repo', ids=('E9.05',))
    pack = load_source(resolve_sources(repo, '1007')[0], repo)
    stage_html = tmp_path / 'stage' / 'note.html'
    stage_html.parent.mkdir()
    stage_html.write_text('<article id="p1">' + core_fragment(pack.problems[0]) + '</article>', encoding='utf-8')
    manifest = stage_html.parent / '.assets/자료_문제설명_1007_Diff_Amp/manifest.json'
    if manifest_value is not None:
        manifest.parent.mkdir(parents=True)
        manifest.write_text(manifest_value, encoding='utf-8')
    with pytest.raises(ExplainError, match='manifest'):
        make_overlay(pack, stage_html, repo)


def test_core_rejects_old_subpart_marker_in_route():
    markup = core_fragment(problem()).replace('data-core-subpart="a"', 'data-core-subpart="a" data-subpart="a"')
    assert validate_core(problem(), markup)


@pytest.mark.parametrize('extra', ['<p>이 조건도 핵심이다.</p>', '중요한 조건', '<div>누락되면 안 되는 조건</div>'])
def test_core_does_not_silently_drop_route_content(extra):
    markup = core_fragment(problem()).replace('<h4>핵심 풀이</h4>', '<h4>핵심 풀이</h4>' + extra)
    assert validate_core(problem(), markup)


def test_core_requires_route_heading():
    assert validate_core(problem(), core_fragment(problem()).replace('<h4>핵심 풀이</h4>', ''))


def test_core_keeps_multiple_steps_in_source_subpart_order():
    text = core_fragment(problem()).replace('<div data-solution-core="answer">',
        '<div data-solution-core="step" data-core-label="계산"><p>$2-1=1$</p></div><div data-solution-core="answer">', 1)
    result = extract_core(problem(), text)
    assert [step['subpart'] for step in result['steps']] == ['a', 'a', 'b']
    assert result['steps'][1] == {'subpart': 'a', 'label': '계산', 'html': '<p>$2-1=1$</p>'}
    assert [answer['subpart'] for answer in result['answers']] == ['a', 'b']
