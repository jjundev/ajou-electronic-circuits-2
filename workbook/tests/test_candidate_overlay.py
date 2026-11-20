import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbook'))
from answer_overlay import AnswerOverlayError, load_answer_overlay
from overlay_fixture import OverlayBundle, digest, dump
from test_answer_overlay import _cli


def moved_bundle(tmp_path):
    bundle = OverlayBundle(tmp_path)
    assets = bundle.stage / '.assets'
    titles, selection = assets/'display-titles.json', assets/'selection.json'
    dump(titles, {pid:'Approved title' for pid in bundle.ids})
    rows = [dict(id=pid, priority='core', learning_goals=['gain'], estimated_minutes=10, subpart_count=1)
            for pid in bundle.ids]
    dump(selection, dict(schema_version=2, policy='exam-first-v2', problems=rows, workload=dict(estimated_minutes=20)))
    inputs = [bundle.source_files[0], titles, selection, *bundle.source_files[1:]]
    bundle.manifest['inputs'] = [str(p) for p in inputs]
    bundle.manifest['source_sha256'] = hashlib.sha256(''.join(digest(p) for p in inputs).encode()).hexdigest()
    bundle.overlay['source_inputs'] = {p.relative_to(bundle.repo).as_posix(): digest(p) for p in inputs}
    ref = bundle.stage / '.assets/reference.md'
    ref.write_text('Reviewed reference')
    bundle.validation['references'].append({'path': str(ref), 'sha256': digest(ref)})
    bundle.sync()
    core = load_answer_overlay(bundle.path, bundle.repo, bundle.ids)
    candidate = tmp_path / 'attempt' / '복습노트' / '1008'
    candidate.parent.mkdir(parents=True)
    bundle.stage.rename(candidate)
    return bundle, candidate, candidate / bundle.path.relative_to(bundle.stage), core


def test_candidate_overlay_matches_public_contract(tmp_path):
    bundle, candidate, overlay, public_core = moved_bundle(tmp_path)
    from pack_paths import PackPaths
    public_pack = bundle.stage
    paths = PackPaths(bundle.repo, public_pack, candidate)
    candidate_core = load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths)
    assert candidate_core == public_core
    assert not public_pack.exists()
    result = _cli(bundle, '--candidate-pack', str(candidate), '--public-pack', str(public_pack),
                  '--answer-overlay', str(overlay), '--mode', 'answers', '--json-only')
    assert result.returncode == 0, result.stderr
    data = json.loads((bundle.build_dir/'personal-답안.json').read_text())
    assert data['problems'][0]['solution']['answer'] == '<p>$W/L=15.625$</p>'


def test_changed_candidate_reference_is_rejected(tmp_path):
    bundle, candidate, overlay, _ = moved_bundle(tmp_path)
    from pack_paths import PackPaths
    shutil.copytree(candidate, bundle.stage)
    ref = candidate / '.assets/reference.md'
    ref.write_text('Modified')
    paths_after_tamper = PackPaths(bundle.repo, bundle.stage, candidate)
    with pytest.raises(AnswerOverlayError, match='hash|변경'):
        load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths_after_tamper)
    ref.unlink()
    with pytest.raises(AnswerOverlayError):
        load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths_after_tamper)


def test_problem_index_exists_without_note(tmp_path):
    bundle = OverlayBundle(tmp_path)
    public_pack = bundle.stage
    shutil.rmtree(public_pack)
    from pack_paths import PackPaths
    from epe_source import load_source
    candidate_pack = tmp_path/'outside'
    paths = PackPaths(bundle.repo, public_pack, candidate_pack)
    spec = importlib.util.spec_from_file_location('note_assemble', ROOT/'.claude/skills/ec2-review-pack/scripts/assemble.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    qs = [dict(id=pid, why='practice', kind='예제', priority='core', learning_goals=['gain'],
               estimated_minutes=10, subpart_count=1) for pid in bundle.ids]
    manifest = dict(range='1008', slug='Test', problems=qs, selection_policy='exam-first-v2')
    selection = tmp_path/'selection.json'
    dump(selection, dict(schema_version=2, policy='exam-first-v2', problems=qs,
         workload=dict(estimated_minutes=20), review=dict(candidates=[], coverage=[])))
    titles = tmp_path/'titles.json'
    dump(titles, {pid: 'Gain' for pid in bundle.ids})
    index = module.stage_problem_index(paths, manifest, selection, titles)
    assert set(index) == {'problems.txt', 'selection.json', 'display-titles.json', 'selection-review.json'}
    assert index['problems.txt'].is_file()
    pack = load_source(index['problems.txt'], bundle.repo, pack_paths=paths, slug=manifest['slug'])
    assert (pack.range, pack.slug) == ('1008', 'Test')
    assert pack.path == public_pack/'.assets/problems.txt'
    assert not public_pack.exists()
    assert not list(candidate_pack.glob('정리노트_*.html'))


def test_candidate_root_replaced_with_symlink_and_manifest_traversal_fail(tmp_path):
    from pack_paths import PackPaths
    repo = tmp_path/'repo'
    public = repo/'복습노트/0910'
    candidate = tmp_path/'candidate'
    paths = PackPaths(repo, public, candidate)
    public.mkdir(parents=True)
    (public/'stale').touch()
    candidate.symlink_to(public, target_is_directory=True)
    with pytest.raises(ValueError):
        paths.work_file('stale')
    with pytest.raises(ValueError):
        paths.source_file('복습노트/0910/../0910/stale')


def test_candidate_overlay_rejects_bad_reference_dependency_without_public_fallback(tmp_path):
    bundle, candidate, overlay, _ = moved_bundle(tmp_path)
    from pack_paths import PackPaths
    reference = bundle.repo/'concept.md'
    reference.write_text('![circuit](복습노트/1008/.assets/approved.svg)')
    image = candidate/'.assets/approved.svg'
    image.write_bytes(b'<svg/>')
    public_image = bundle.stage/'.assets/approved.svg'
    public_image.parent.mkdir(parents=True)
    public_image.write_bytes(image.read_bytes())
    validation = overlay.with_name('validation.json')
    proof = json.loads(validation.read_text())
    proof['references'] += [{'path': str(reference), 'sha256': digest(reference)},
                            {'path': str(public_image), 'sha256': digest(image)}]
    dump(validation, proof)
    paths = PackPaths(bundle.repo, bundle.stage, candidate)
    assert load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths)
    image.write_bytes(b'changed')
    with pytest.raises(AnswerOverlayError, match='참조 자료 변경'):
        load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths)
    image.unlink()
    with pytest.raises(AnswerOverlayError):
        load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=paths)


def test_problem_workbook_maps_public_title_path_to_candidate(tmp_path):
    bundle, candidate, _, _ = moved_bundle(tmp_path)
    title_path = bundle.stage/'.assets/display-titles.json'
    title_path.parent.mkdir(parents=True)
    dump(title_path, {pid:'Stale title' for pid in bundle.ids})
    dump(candidate/'.assets/display-titles.json', {pid:'Approved title' for pid in bundle.ids})
    result = _cli(bundle, '--mode', 'problems', '--json-only', '--candidate-pack', str(candidate),
                  '--public-pack', str(bundle.stage), '--display-titles', str(title_path))
    assert result.returncode == 0, result.stderr
    data = json.loads((bundle.build_dir/'personal-문제.json').read_text())
    assert data['problems'][0]['title'] == 'P1. Approved title'


def test_candidate_overlay_detects_conflicting_assembled_note_slug(tmp_path):
    bundle, candidate, overlay, _ = moved_bundle(tmp_path)
    from pack_paths import PackPaths
    note = next(candidate.glob('정리노트_*.html'))
    note.rename(candidate/'정리노트_1008_Different.html')
    view = PackPaths(bundle.repo, bundle.stage, candidate)
    with pytest.raises(AnswerOverlayError, match='slug'):
        load_answer_overlay(overlay, bundle.repo, bundle.ids, pack_paths=view)
