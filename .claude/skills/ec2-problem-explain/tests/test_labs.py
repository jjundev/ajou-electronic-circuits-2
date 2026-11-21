import json
from urllib.parse import quote

import pytest

from _util import approved, fragment, make_repo
from epe_cli import build, extract, load_artifacts, load_run, main
from epe_publish import publish_explanation
from epe_render import check_artifacts, dump, names
from epe_source import sha256
from epe_types import ExplainError


@pytest.fixture
def context(tmp_path):
    repo = make_repo(tmp_path / 'repo', ids=('P10.02', 'E12.27'))
    run = tmp_path / 'run'
    assert extract(repo, '1007', run) == 0
    item, = load_run(run)
    fragments = {p.id: fragment(p) for p in item['pack'].problems}
    for pid, html in fragments.items():
        (item['folder'] / 'explanations' / f'{pid}.html').write_text(html, encoding='utf-8')
    return repo, run, item, fragments


def candidate(workbook_id, section='start'):
    return dict(workbook_id=workbook_id, section=section, subpart='main',
                decision='출력 부하 판단', action='포트 개방 또는 단락',
                observation='R2 전류가 달라져요.', return_to='출력 저항의 첫 식',
                label='감지 복제 결선해 보기')


def select(context, candidates):
    _, run, item, _ = context
    dump(item['folder'] / 'lab-candidates.json', candidates)
    assert main(['select-lab', '--run', str(run)]) == 0
    return item['folder'] / 'lab'


def finish(lab):
    (lab / 'lab.js').write_text('module.exports = {};', encoding='utf-8')
    (lab / 'index.html').write_text('<html><title>회로 실험</title></html>', encoding='utf-8')
    dump(lab / 'lab-validation.json', dict(
        source_sha256=sha256(lab / 'lab.js'), html_sha256=sha256(lab / 'index.html'),
        brief_sha256=sha256(lab / 'brief.json'),
        gates=dict.fromkeys(('machine', 'numeric_independent', 'probe', 'browser'), 'pass')))


def test_selection_prioritizes_start_and_selects_only_one(context):
    folder = select(context, [candidate('P10.02', 'retry'), candidate('E12.27')])
    selected = json.loads((folder / 'brief.json').read_text(encoding='utf-8'))
    assert selected['workbook_id'] == 'E12.27'
    assert len(list(folder.glob('*.json'))) == 1


def test_no_eligible_candidate_builds_regular_explanation(context, capsys):
    _, _, item, fragments = context
    empty = candidate('E12.27')
    empty['decision'] = ''
    select(context, [candidate('unknown'), empty])
    build(item, fragments)
    artifacts = load_artifacts(item)
    assert 'data-ec2-problem-lab' not in artifacts.html.read_text(encoding='utf-8')
    assert '후보 없음' in capsys.readouterr().out


def test_approved_lab_renders_at_workbook_section_and_survives_rerender(context, tmp_path):
    repo, _, item, fragments = context
    pack = item['pack']
    build(item, fragments, include_problem_pdf=False)
    base = load_artifacts(item)
    lab = select(context, [candidate('E12.27')])
    finish(lab)
    build(item, fragments, include_problem_pdf=False)
    artifacts = load_artifacts(item)
    assert not check_artifacts(pack, artifacts)
    html = artifacts.html.read_text(encoding='utf-8')
    assert 'data-ec2-problem-lab' not in html.split('<article class="topic" id="p2">')[0]
    assert 'data-ec2-problem-lab' in html.split('<article class="topic" id="p2">')[1]
    target = f'{names(pack)[2]}/labs/E12.27/index.html'
    assert f'href="{quote(".assets/" + target)}"' in html
    assert f']({quote("../.assets/" + target)})' in artifacts.md.read_text(encoding='utf-8')
    assert (base.manifest.parent / 'answer-overlay.json').read_bytes() == (
        artifacts.manifest.parent / 'answer-overlay.json').read_bytes()
    publish_explanation(pack, artifacts, fragments, approved(pack, fragments, artifacts),
                        pack.folder, tmp_path / 'backup', repo)
    assert (pack.folder / '.assets' / target).is_file()

    run = tmp_path / 'rerender'
    assert main(['rerender', '--repo', str(repo), '--target', '1007', '--run', str(run)]) == 0
    rerender, = load_run(run)
    rerendered = load_artifacts(rerender)
    assert (rerendered.html.parent / '.assets' / target).is_file()
    assert '원 문제 보기</a>' not in rerendered.html.read_text(encoding='utf-8')


def test_reviewed_lab_tampering_blocks_publication(context, tmp_path):
    repo, _, item, fragments = context
    pack = item['pack']
    lab = select(context, [candidate('E12.27')])
    finish(lab)
    build(item, fragments)
    artifacts = load_artifacts(item)
    reviews = approved(pack, fragments, artifacts)
    staged_lab = next(path for path in artifacts.files if path.name == 'index.html')
    staged_lab.write_text('changed', encoding='utf-8')
    with pytest.raises(ExplainError, match='생성 파일 변경/누락'):
        publish_explanation(pack, artifacts, fragments, reviews, pack.folder,
                            tmp_path / 'backup', repo)


def test_incomplete_or_stale_lab_has_no_public_link(context, capsys):
    _, _, item, fragments = context
    select(context, [candidate('E12.27')])
    build(item, fragments)
    assert 'data-ec2-problem-lab' not in load_artifacts(item).html.read_text(encoding='utf-8')
    assert '실험 보류' in capsys.readouterr().out
    finish(item['folder'] / 'lab')
    changed = {**fragments, 'p2': fragments['p2'].replace('구할 것을 읽어요.', '조건을 읽어요.')}
    build(item, changed)
    assert 'data-ec2-problem-lab' not in load_artifacts(item).html.read_text(encoding='utf-8')
    assert '실험 보류' in capsys.readouterr().out


def test_reviewed_resource_paths_allow_equivalent_parent_components(tmp_path):
    from epe_rerender import verified_resources

    (tmp_path / 'notes').mkdir()
    image = tmp_path / 'figure.svg'
    image.write_text('<svg />', encoding='utf-8')
    digest = sha256(image)
    assert verified_resources({'figure.svg': digest}, {'notes/../figure.svg': digest}, tmp_path)


def test_lab_changing_between_validation_and_staging_is_detected(context, tmp_path):
    from epe_labs import load_lab
    from epe_render import build_explanation

    repo, _, item, fragments = context
    pack = item['pack']
    folder = select(context, [candidate('E12.27')])
    finish(folder)
    lab, diagnostic = load_lab(item['folder'], pack, fragments)
    assert not diagnostic
    (folder / 'index.html').write_text('changed before stage', encoding='utf-8')
    artifacts = build_explanation(pack, fragments, tmp_path / 'stage', repo, lab=lab)
    assert any('실험' in error for error in check_artifacts(pack, artifacts))


def test_lab_link_stays_outside_selected_answer_step(context, tmp_path):
    from dataclasses import replace

    from epe_labs import load_lab, select_lab
    from epe_render import build_explanation

    repo, _, item, fragments = context
    first, second = item['pack'].problems
    second = replace(second, subparts=('a', 'b'))
    pack = replace(item['pack'], problems=(first, second))
    fragments[second.id] = fragment(second).replace(
        '<div data-subpart="a"><div data-answer-step="회로 판단">'
        '<p>판단과 식은 $1=1$이에요.</p></div></div>',
        '<div data-subpart="a" data-answer-step="회로 판단">'
        '<p>판단과 식은 $1=1$이에요.</p></div>',
    )
    base = build_explanation(pack, fragments, tmp_path / 'base', repo)
    dump(item['folder'] / 'lab-candidates.json', [{**candidate('E12.27', 'solve'), 'subpart': 'a'}])
    assert select_lab(item['folder'], pack, fragments)
    finish(item['folder'] / 'lab')
    lab, diagnostic = load_lab(item['folder'], pack, fragments)
    assert not diagnostic
    artifacts = build_explanation(pack, fragments, tmp_path / 'stage', repo, lab=lab)
    assert not check_artifacts(pack, artifacts)
    assert (base.manifest.parent / 'answer-overlay.json').read_bytes() == (
        artifacts.manifest.parent / 'answer-overlay.json').read_bytes()
