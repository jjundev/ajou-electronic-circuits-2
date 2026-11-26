"""Regression contracts for the common explanation update; synthetic inputs only."""
import sys, json
from pathlib import Path
from dataclasses import replace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from epe_types import SourcePack
from epe_render import build_explanation, check_artifacts
from epe_source import load_source, resolve_sources, subparts
from _util import fragment, problem, _copy


def synthetic(tmp_path):
    repo=tmp_path/'repo'
    src=repo/'복습노트/1007/복습문제_1007_Test.html'
    src.parent.mkdir(parents=True)
    src.write_text('<html><body id="p1">fixture</body></html>',encoding='utf-8')
    _copy(Path('.claude/skills/ec2-review-pack/references/solution-style.md'), repo)
    from epe_shared import read_style
    p=problem()
    pack=SourcePack('review','1007','Test',src.parent/'.assets/problems.txt','0'*64,(p,),(),read_style(repo))
    return repo,pack,{p.id:fragment(p)}


def test_stage_has_separate_problem_and_original(tmp_path):
    repo,pack,fragments=synthetic(tmp_path)
    a=build_explanation(pack,fragments,tmp_path/'stage',repo)
    text=a.html.read_text(encoding='utf-8')
    from epe_shared import parse
    doc=parse(text)
    assert len(list(doc.find_all(lambda n:n.attrs.get('data-problem-for')=='p1')))==1
    assert 'id="panel-prob"' in text
    assert 'data-original-problem="p1"' in text
    assert check_artifacts(pack,a)==[]


def test_legacy_policy_cannot_reuse_approval():
    from epe_review_policy import carry_reviews
    old={'content':{'status':'pass'},'independent':{'status':'pass'}}
    fresh={'content':{'status':'not_run'},'independent':{'status':'not_run'}}
    result=carry_reviews(old,fresh,[],True)
    assert result['content']['status']=='not_run'
    assert result['independent']['status']=='not_run'


def test_current_policy_reuses_only_when_inputs_and_references_verified():
    from epe_review_policy import carry_reviews, POLICY_VERSION
    from _util import approved, pack
    from epe_contract import initial_reviews
    source = pack()
    fragments = {p.id: fragment(p) for p in source.problems}
    old = approved(source, fragments)
    fresh = initial_reviews(source, fragments)
    assert carry_reviews(old,fresh,[],True)['content']['status']=='pass'
    assert carry_reviews(old,fresh,[],True)['browser']['status']=='not_run'
    assert carry_reviews(old,fresh,[],False)['independent']['status']=='not_run'


def test_old_policy_rejected_by_review_gate(tmp_path):
    from epe_contract import initial_reviews,validate_reviews
    repo,pack,fragments=synthetic(tmp_path)
    review=initial_reviews(pack,fragments)
    review.pop('review_policy_version',None)
    assert any('검토 기준' in e for e in validate_reviews(pack,fragments,review))


def test_source_svg_numeric_stroke_width_is_allowed(tmp_path):
    repo,pack,fragments=synthetic(tmp_path)
    p=replace(pack.problems[0],figures_html=('<svg viewBox="0 0 20 20"><path style="stroke-width:2px" d="M0 0L10 10"/></svg>',))
    pack=replace(pack,problems=(p,))
    a=build_explanation(pack,fragments,tmp_path/'stage',repo)
    assert 'stroke-width:2px' in a.html.read_text(encoding='utf-8')


def test_all_selects_only_ready_review_packs_newest_first(tmp_path):
    from _util import make_repo
    repo=make_repo(tmp_path/'repo',range_='1007',ids=('P10.02',))
    make_repo(repo,range_='1014',ids=('P10.02',))
    assert [p.parent.parent.name for p in resolve_sources(repo,'all')]==['1014','1007']


def test_canonically_equal_sibling_directory_is_not_inside_repo(tmp_path):
    import unicodedata
    from epe_source import inside
    from epe_types import ExplainError
    repo=tmp_path/'저장소'
    other=tmp_path/unicodedata.normalize('NFD','저장소')
    repo.mkdir()
    other.mkdir(exist_ok=True)
    source=other/'outside.txt';source.write_text('outside')
    if repo.samefile(other):
        # APFS treats the two spellings as one directory: this is actually inside.
        canonical = repo / source.name
        assert canonical.samefile(source)
        assert inside(canonical, repo).samefile(source)
    else:
        # Filesystems retaining distinct NFC/NFD siblings must reject the lookalike.
        with pytest.raises(ExplainError,match='저장소 밖'):
            inside(source,repo)
    distinct = tmp_path / 'distinct-outside'
    distinct.mkdir()
    outside = distinct / 'outside.txt'; outside.write_text('outside')
    with pytest.raises(ExplainError,match='저장소 밖'):
        inside(outside,repo)


def published_fixture(tmp_path, reference=False):
    import shutil
    from epe_cli import extract, load_run, build, load_artifacts, load_fragments
    from _util import approved, concise_fragment
    repo=tmp_path/'published-repo'
    from _util import make_repo
    make_repo(repo,ids=('P10.02',))
    source=repo/'복습노트/1007/.assets/problems.txt'
    run=tmp_path/'first-run'
    target='1007' if True else str(source)
    assert extract(repo,target,run)==0
    item=load_run(run)[0]
    for problem in item['pack'].problems:
        (item['folder']/'explanations'/f'{problem.id}.html').write_text(concise_fragment(problem),encoding='utf-8')
    build(item,load_fragments(item))
    artifacts=load_artifacts(item)
    reviews=approved(item['pack'],load_fragments(item),artifacts)
    if reference:
        from epe_source import sha256
        ref=repo/'reference.html';ref.write_text('<p>theory</p>',encoding='utf-8')
        reviews['references'].append({'path':str(ref),'sha256':sha256(ref)})
    destination=item['pack'].folder
    shutil.copytree(artifacts.html.parent,destination,dirs_exist_ok=True)
    data=destination/artifacts.manifest.relative_to(artifacts.html.parent).parent
    (data/'validation.json').write_text(json.dumps(reviews),encoding='utf-8')
    return repo,source,data


def rebuilt_review(tmp_path,repo,source):
    from epe_cli import rerender, load_run
    run=tmp_path/'rebuilt'
    assert rerender(repo,'1007' if True else str(source),run)==0
    folder=load_run(run)[0]['folder']
    return json.loads((folder/'review.json').read_text(encoding='utf-8'))


def test_rerender_current_policy_preserves_only_content_checks(tmp_path):
    repo,source,data=published_fixture(tmp_path)
    review=rebuilt_review(tmp_path,repo,source)
    assert review['content']['status']=='pass'
    assert review['independent']['status']=='pass'
    assert review['browser']['status']=='not_run'
    assert review['source_visual']['status']=='not_run'


def test_rerender_legacy_policy_requires_fresh_content_checks(tmp_path):
    repo,source,data=published_fixture(tmp_path)
    p=data/'validation.json';old=json.loads(p.read_text());old.pop('review_policy_version')
    p.write_text(json.dumps(old),encoding='utf-8')
    review=rebuilt_review(tmp_path,repo,source)
    assert review['content']['status']=='not_run'
    assert review['independent']['status']=='not_run'


@pytest.mark.parametrize('action',['change','remove'])
def test_rerender_changed_or_missing_reference_resets_approval(tmp_path,action):
    repo,source,data=published_fixture(tmp_path,reference=True)
    ref=repo/'reference.html'
    if action=='remove': ref.unlink()
    else: ref.write_text('<p>different theory</p>')
    review=rebuilt_review(tmp_path,repo,source)
    assert review['content']['status']=='not_run'
    assert review['independent']['status']=='not_run'


def test_rerender_rejects_changed_published_fragment(tmp_path):
    from epe_cli import rerender
    repo,source,data=published_fixture(tmp_path)
    p=data/'fragments/p1.html';p.write_text(p.read_text()+'<p>tampered</p>')
    assert rerender(repo,'1007' if True else str(source),tmp_path/'rebuilt')==1


@pytest.mark.parametrize('kind',['md','image'])
def test_rerender_composite_input_change_resets_approval(tmp_path,kind):
    from epe_source import load_source
    repo,source,data=published_fixture(tmp_path)
    pack=load_source(source,repo)
    paths=[Path(s) for s in pack.inputs]
    if kind=='md':
        target=next(p for p in paths if p.suffix=='.md')
        target.write_bytes(target.read_bytes()+b'\n')
    else:
        target=next(p for p in paths if p.suffix=='.png')
        target.write_bytes(target.read_bytes()+b'changed')
    review=rebuilt_review(tmp_path,repo,source)
    assert review['content']['status']=='not_run'
    assert review['independent']['status']=='not_run'


def test_reference_relocation_cannot_compare_replacement_image_to_itself(tmp_path):
    from epe_rerender import equivalent_text
    repo=tmp_path/'repo';source=repo/'1007/reference.html'
    target=source.parent/'.pack/figures/image.png';target.parent.mkdir(parents=True)
    target.write_bytes(b'changed-image')
    assert not equivalent_text(b'<img src="figures/image.png">',b'<img src=".pack/figures/image.png">',source,source,repo)


def test_reference_image_dependency_must_have_its_own_hash(tmp_path):
    from epe_rerender import verified_references
    from epe_source import sha256
    repo=tmp_path/'repo';repo.mkdir()
    ref=repo/'theory.html';ref.write_text('<img src="theory.png">')
    image=repo/'theory.png';image.write_bytes(b'old-image')
    records=[{'path':str(ref),'sha256':sha256(ref)}]
    assert verified_references(records,repo,repo)[1] is False
    records.append({'path':str(image),'sha256':sha256(image)})
    assert verified_references(records,repo,repo)[1] is True
    image.write_bytes(b'changed-image')
    assert verified_references(records,repo,repo)[1] is False


def test_source_image_unicode_spelling_resolves_before_hashing(tmp_path):
    import unicodedata
    repo,pack,fragments=synthetic(tmp_path)
    base=pack.folder
    (base/'그림.png').write_bytes(b'fixture-image')
    p=replace(pack.problems[0],figures_html=('<img src="'+unicodedata.normalize('NFD','그림.png')+'" alt="fixture">',))
    result=build_explanation(replace(pack,problems=(p,)),fragments,tmp_path/'stage',repo)
    assert result.html.is_file()
