"""Publication boundaries using real temporary extract/build, synthetic approvals only."""
import json
from types import SimpleNamespace

import pytest
from _util import make_repo, fragment, approved
from epe_cli import extract, load_run, build, load_fragments, load_artifacts, rerender
from epe_publish import publish_explanation
from epe_render import dump, artifact_hashes
from epe_source import sha256
from epe_types import ExplainError


@pytest.fixture
def bundle(tmp_path):
    repo = make_repo(tmp_path / 'repo', ids=('E9.05',))
    run = tmp_path / 'run'
    assert extract(repo, '1007', run) == 0
    item = load_run(run)[0]
    p = item['pack'].problems[0]
    (item['folder'] / 'explanations/p1.html').write_text(fragment(p), encoding='utf-8')
    fragments = load_fragments(item)
    build(item, fragments)
    artifacts = load_artifacts(item)
    review = approved(item['pack'], fragments, artifacts)
    profile = repo / 'docs/learning/solution-style.md'
    overlay = artifacts.manifest.parent / 'answer-overlay.json'
    def publish():
        return publish_explanation(item['pack'], artifacts, fragments, review,
                                   item['pack'].folder, tmp_path / 'backup', repo)
    return SimpleNamespace(**locals())


def test_build_records_unapproved_style_audit_and_required_reference(bundle):
    review = json.loads((bundle.item['folder'] / 'review.json').read_text())
    assert review['learning_style_audit']['learning_style'] == bundle.item['pack'].learning_style
    item = review['learning_style_audit']['items']['p1:main']
    assert item['status'] == 'not_run' and item['reviewer'] == ''
    assert set(item['rules']) == set(bundle.item['pack'].learning_style['rule_ids'])
    assert all(rule['evidence'] == '' for rule in item['rules'].values())
    assert review['references'] == [{'path': str(bundle.profile), 'sha256': sha256(bundle.profile)}]


def test_personalization_not_run_blocks_publish(bundle):
    # Explicit synthetic audit keeps this RED about the missing gate, not missing helper fields.
    bundle.review['learning_style_audit'] = {'learning_style': bundle.item['pack'].learning_style,
        'items': {'p1:main': {'status': 'not_run', 'reviewer': '', 'rules': {}}}}
    with pytest.raises(ExplainError, match='개인화'):
        bundle.publish()


def test_profile_change_after_build_blocks_publish(bundle):
    bundle.profile.write_bytes(bundle.profile.read_bytes() + b'\n')
    with pytest.raises(ExplainError):
        bundle.publish()


def test_overlay_is_bound_to_artifact_hashes(bundle):
    relative = bundle.overlay.relative_to(bundle.artifacts.html.parent).as_posix()
    assert relative in bundle.review['artifact_hashes']
    manifest = json.loads(bundle.artifacts.manifest.read_text())
    assert manifest['answer_overlay'] == relative
    assert manifest['learning_style'] == bundle.item['pack'].learning_style
    assert relative in manifest['files']
    bundle.overlay.write_text('{}', encoding='utf-8')
    with pytest.raises(ExplainError):
        bundle.publish()


def test_missing_style_reference_rejected(bundle):
    bundle.review['references'] = []
    with pytest.raises(ExplainError, match='명세.*참조|참조.*명세'):
        bundle.publish()


def test_profile_missing_before_extract(tmp_path):
    repo = make_repo(tmp_path / 'repo', ids=('E9.05',))
    (repo / 'docs/learning/solution-style.md').unlink()
    assert extract(repo, '1007', tmp_path / 'run') == 1
    assert not list((tmp_path / 'run').rglob('source.json'))


def test_final_core_and_details_are_both_in_md(bundle):
    md = bundle.artifacts.md.read_text()
    for text in ('핵심 풀이', '최종 답은', '이 문제를 봤을 때 떠올릴 개념과 공식', '첫 식에서 계산하고'):
        assert text in md


def test_published_overlay_has_validation_and_review_hash(bundle):
    published = bundle.publish()
    dest = bundle.item['pack'].folder
    overlay = dest / bundle.overlay.relative_to(bundle.artifacts.html.parent)
    assert overlay in published
    validation = json.loads((overlay.parent / 'validation.json').read_text())
    assert validation['learning_style_audit']['items']['p1:main']['status'] == 'pass'
    assert validation['artifact_hashes'][overlay.relative_to(dest).as_posix()] == sha256(overlay)


def rebuilt(bundle, tmp_path):
    run = tmp_path / 'rebuilt'
    assert rerender(bundle.repo, '1007', run) == 0
    return json.loads((load_run(run)[0]['folder'] / 'review.json').read_text())


def test_old_policy_rerender_does_not_inherit(bundle, tmp_path):
    bundle.publish()
    validation = bundle.item['pack'].folder / bundle.artifacts.manifest.relative_to(bundle.artifacts.html.parent).parent / 'validation.json'
    stored = json.loads(validation.read_text())
    stored['review_policy_version'] = 'problem-explain-2026-10-18-smallsignal'
    dump(validation, stored)
    review = rebuilt(bundle, tmp_path)
    assert review['content']['status'] == 'not_run'
    assert review['independent']['status'] == 'not_run'
    assert review['learning_style_audit']['items']['p1:main']['status'] == 'not_run'


def test_current_profile_change_never_uses_html_equivalence(bundle, tmp_path):
    bundle.publish()
    # A script-only delta normally qualifies for HTML equivalence; style bytes never do.
    bundle.profile.write_text(bundle.profile.read_text() + '\n<script>void 0</script>\n')
    review = rebuilt(bundle, tmp_path)
    assert review['content']['status'] == 'not_run'
    assert review['independent']['status'] == 'not_run'
    assert review['learning_style_audit']['items']['p1:main']['status'] == 'not_run'
    assert review['references'][0]['sha256'] != sha256(bundle.profile)


def test_legacy_fragment_requires_new_authoring_and_preserves_publication(bundle, tmp_path, capsys):
    bundle.publish()
    folder = bundle.item['pack'].folder
    data = folder / bundle.artifacts.manifest.relative_to(bundle.artifacts.html.parent).parent
    fragment_path = data / 'fragments/p1.html'
    from epe_shared import parse, outer
    root = parse(fragment_path.read_text())
    fragment_path.write_text(''.join(outer(n) for n in root.children
        if not (getattr(n, 'attrs', {}).get('data-personalization') == 'route')))
    manifest_path = data / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files'][fragment_path.relative_to(folder).as_posix()] = sha256(fragment_path)
    dump(manifest_path, manifest)
    before = {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert rerender(bundle.repo, '1007', tmp_path / 'rebuilt') == 1
    assert '새 저작 필요' in capsys.readouterr().err
    assert {p: p.read_bytes() for p in before} == before


def test_style_reference_bytes_cannot_use_git_html_equivalence(bundle):
    import subprocess
    from epe_rerender import verified_references
    for args in (['init', '-q'], ['add', 'docs/learning/solution-style.md'],
                 ['-c', 'user.name=Unit Test', '-c', 'user.email=fixture@example.invalid',
                  'commit', '-qm', 'synthetic fixture profile']):
        subprocess.run(['git', *args], cwd=bundle.repo, check=True, capture_output=True)
    refs = [{'path': str(bundle.profile), 'sha256': sha256(bundle.profile)}]
    bundle.profile.write_text(bundle.profile.read_text() + '\n<script>void 0</script>\n')
    carried, valid = verified_references(refs, bundle.repo, bundle.repo)
    assert not valid
    assert not carried


@pytest.mark.parametrize('change', ['snapshot', 'rule', 'evidence', 'item', 'reviewer'])
def test_incomplete_style_audit_blocks_publish(bundle, change):
    audit = bundle.review['learning_style_audit']
    item = audit['items']['p1:main']
    if change == 'snapshot': audit['learning_style'] = {**audit['learning_style'], 'sha256': '0' * 64}
    elif change == 'rule': item['rules'].pop(next(iter(item['rules'])))
    elif change == 'evidence': next(iter(item['rules'].values()))['evidence'] = ''
    elif change == 'item': audit['items'].clear()
    else: item['reviewer'] = ''
    with pytest.raises(ExplainError, match='개인화'):
        bundle.publish()


@pytest.mark.parametrize('kind', ['manifest_policy', 'audit_shape'])
def test_rerender_never_inherits_mismatched_manifest_or_malformed_audit(bundle, tmp_path, kind):
    bundle.publish()
    data = bundle.item['pack'].folder / bundle.artifacts.manifest.relative_to(bundle.artifacts.html.parent).parent
    if kind == 'manifest_policy':
        path = data / 'manifest.json'
        value = json.loads(path.read_text()); value['review_policy_version'] = 'old-policy'
    else:
        path = data / 'validation.json'
        value = json.loads(path.read_text()); value['learning_style_audit'] = []
    dump(path, value)
    review = rebuilt(bundle, tmp_path)
    assert review['content']['status'] == 'not_run'
    assert review['independent']['status'] == 'not_run'
    assert review['learning_style_audit']['items']['p1:main']['status'] == 'not_run'


@pytest.mark.parametrize('change', ['version', 'snapshot', 'missing', 'shape'])
def test_overlay_contract_cannot_be_removed_or_relabelled(bundle, change):
    manifest = json.loads(bundle.artifacts.manifest.read_text())
    relative = bundle.overlay.relative_to(bundle.artifacts.html.parent).as_posix()
    if change == 'missing':
        manifest.pop('answer_overlay')
    else:
        overlay = json.loads(bundle.overlay.read_text())
        if change == 'version': overlay['schema_version'] = 999
        elif change == 'snapshot': overlay['learning_style']['sha256'] = '0' * 64
        else: overlay = []
        dump(bundle.overlay, overlay)
        manifest['files'][relative] = sha256(bundle.overlay)
    dump(bundle.artifacts.manifest, manifest)
    bundle.review['artifact_hashes'] = artifact_hashes(bundle.artifacts)
    with pytest.raises(ExplainError, match='overlay'):
        bundle.publish()


def test_current_rerender_reuses_style_audit_but_requires_fresh_visual_reviews(bundle, tmp_path):
    bundle.publish()
    review = rebuilt(bundle, tmp_path)
    assert review['learning_style_audit'] == bundle.review['learning_style_audit']
    assert review['content']['status'] == 'pass'
    assert review['independent']['status'] == 'pass'
    assert review['browser']['status'] == 'not_run'
    assert review['source_visual']['status'] == 'not_run'
