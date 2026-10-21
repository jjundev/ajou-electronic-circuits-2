import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from overlay_fixture import OverlayBundle, dump
from answer_overlay import AnswerOverlayError, load_answer_overlay, apply_answer_overlay


@pytest.fixture
def bundle(tmp_path):
    return OverlayBundle(tmp_path)


def test_applies_only_answer_fields(bundle):
    data = {'meta': {'mode':'answers'}, 'problems':[{'id':p, 'html':{'original':'Keep me'}, 'solution':{'answer':'old'}} for p in bundle.ids]}
    original = copy.deepcopy(data)
    overlay = load_answer_overlay(bundle.path, bundle.repo, bundle.ids)
    out = apply_answer_overlay(data, overlay, html_dir=bundle.build_dir)
    assert data == original
    assert out['meta'] == data['meta']
    assert out['problems'][0]['html'] == data['problems'][0]['html']
    assert out['problems'][0]['solution']['answer'] == '<p>$W/L=15.625$</p>'
    assert out['problems'][0]['solution']['steps'][0]['label'] == '판단 &amp; 계산'
    body = out['problems'][0]['solution']['steps'][0]['html']
    assert 'data:image/png;base64,' in body
    assert '<a' not in body and 'Details' in body
    assert out['problems'][1]['solution']['steps'][0]['label'] == '(a) Calculate'
    assert '(a)' in out['problems'][1]['solution']['answer']
    assert '(b)' in out['problems'][1]['solution']['answer']
    assert not bundle.build_dir.exists()


@pytest.mark.parametrize('mutation', ['missing_id','duplicate_id','reordered_ids','missing_subpart','modified_profile',
    'modified_source','modified_asset','missing_validation','not_run_review','missing_audit','missing_rule',
    'unknown_schema','unknown_manifest','old_policy','input_hash','missing_source_hash','missing_artifact',
    'missing_reference','changed_reference','missing_review_item','bad_numerical','empty_step','empty_answer',
    'reordered_subparts','wrong_explanation_id'])
def test_invalid_overlay_fails_without_fallback(bundle, mutation):
    if mutation == 'missing_id': bundle.overlay['problems'].pop()
    elif mutation == 'duplicate_id': bundle.overlay['problems'][1]['id'] = 'E9.05'
    elif mutation == 'reordered_ids': bundle.overlay['problems'].reverse()
    elif mutation == 'missing_subpart': bundle.overlay['problems'][1]['answers'].pop()
    elif mutation == 'modified_profile': (bundle.repo/'docs/learning/solution-style.md').write_text('Changed')
    elif mutation == 'modified_source': bundle.source_files[1].write_text('Changed')
    elif mutation == 'modified_asset': bundle.asset.write_bytes(b'changed')
    elif mutation == 'not_run_review': bundle.validation['browser']['status'] = 'not_run'
    elif mutation == 'missing_audit': bundle.validation.pop('learning_style_audit')
    elif mutation == 'missing_rule': bundle.validation['learning_style_audit']['items']['p1:main']['rules'] = {}
    elif mutation == 'unknown_schema': bundle.overlay['schema_version'] = 2
    elif mutation == 'unknown_manifest': bundle.manifest['version'] = 2
    elif mutation == 'old_policy': bundle.validation['review_policy_version'] = 'old'
    elif mutation == 'input_hash': bundle.validation['input_hash'] = 'b'*64
    elif mutation == 'missing_source_hash': bundle.overlay['source_inputs'].pop(next(iter(bundle.overlay['source_inputs'])))
    elif mutation == 'missing_reference': bundle.validation['references'] = []
    elif mutation == 'changed_reference': bundle.validation['references'][0]['sha256'] = 'b'*64
    elif mutation == 'missing_review_item': bundle.validation['content']['items'].pop('p2:b')
    elif mutation == 'bad_numerical': bundle.validation['independent']['items']['p1:main'].update(method='numerical', residual=2, tolerance=1)
    elif mutation == 'empty_step': bundle.overlay['problems'][0]['steps'][0]['html'] = ''
    elif mutation == 'empty_answer': bundle.overlay['problems'][0]['answers'][0]['html'] = ''
    elif mutation == 'reordered_subparts': bundle.overlay['problems'][1]['subparts'].reverse()
    elif mutation == 'wrong_explanation_id': bundle.overlay['problems'][0]['explanation_id'] = 'p9'
    bundle.sync()
    if mutation == 'missing_validation': (bundle.data/'validation.json').unlink()
    if mutation == 'missing_artifact': bundle.validation['artifact_hashes'].pop(next(iter(bundle.validation['artifact_hashes']))); dump(bundle.data/'validation.json',bundle.validation)
    with pytest.raises(AnswerOverlayError):
        load_answer_overlay(bundle.path, bundle.repo, bundle.ids)


@pytest.mark.parametrize('asset', ['https://example.com/x.png','../../outside.png','file:///tmp/x.png','//example.com/x.png'])
def test_external_or_escaping_asset_rejected(bundle, asset):
    bundle.overlay['assets'] = {asset: 'a'*64}
    bundle.overlay['problems'][0]['steps'][0]['html'] = f'<img src="{asset}">'
    bundle.sync()
    with pytest.raises(AnswerOverlayError): load_answer_overlay(bundle.path,bundle.repo,bundle.ids)


def test_nfd_and_spaces_resolve_images(bundle):
    out = load_answer_overlay(bundle.path,bundle.repo,bundle.ids)
    assert next(iter(out['_asset_data'].values())).startswith('data:image/png;base64,')
    assert '_asset_data' not in json.loads(bundle.path.read_text())


def test_published_bundle_loads_in_clean_process(bundle):
    script = 'from answer_overlay import load_answer_overlay; import sys; from pathlib import Path; print(load_answer_overlay(Path(sys.argv[1]),Path(sys.argv[2]),["E9.05","E9.06"])["schema_version"])'
    result = subprocess.run([sys.executable,'-c',script,str(bundle.path),str(bundle.repo)], cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '1'


def _cli(bundle, *extra):
    # Redirect the real CLI's repository configuration to a genuine temporary
    # corpus. All parsing, source loading, validation and rendering stay real.
    script = '''import sys
from pathlib import Path
import build_workbook, assemble
build_workbook.paths.ROOT = Path(sys.argv[1])
assemble.TEXTBOOK = Path(sys.argv[1]) / '교과서/마이크로전자회로'
raise SystemExit(build_workbook.main(['build_workbook.py', *sys.argv[2:]]))
'''
    return subprocess.run([sys.executable,'-c',script,str(bundle.repo),'--ids',','.join(bundle.ids),
        '--name','personal','--build-dir',str(bundle.build_dir),'--pdf-dir',str(bundle.build_dir/'pdf'),*extra],
        cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)


def test_cli_personalized_answers_from_published_bundle(bundle):
    result = _cli(bundle,'--mode','answers','--answer-overlay',str(bundle.path),'--json-only')
    assert result.returncode == 0, result.stderr
    data = json.loads((bundle.build_dir/'personal-답안.json').read_text())
    assert data['problems'][0]['solution']['answer'] == '<p>$W/L=15.625$</p>'
    assert not (bundle.build_dir/'personal-문제.json').exists()


def test_profile_missing_fails_personalized_only(bundle):
    (bundle.repo/'docs/learning/solution-style.md').unlink()
    result = _cli(bundle,'--answer-overlay',str(bundle.path),'--json-only')
    assert result.returncode == 1, result.stderr
    assert not bundle.build_dir.exists()
    legacy = _cli(bundle,'--json-only')
    assert legacy.returncode == 0, legacy.stderr
    assert (bundle.build_dir/'personal-문제.json').exists()
    assert (bundle.build_dir/'personal-답안.json').exists()


def test_changed_review_writes_no_outputs_even_in_both_mode(bundle):
    bundle.validation['content']['items']['p2:b']['status'] = 'not_run'
    bundle.sync()
    result = _cli(bundle,'--answer-overlay',str(bundle.path),'--json-only')
    assert result.returncode == 1, result.stderr
    assert not bundle.build_dir.exists()


def test_failed_validation_preserves_existing_outputs(bundle):
    bundle.build_dir.mkdir()
    outputs = [bundle.build_dir/f'personal-{kind}.{ext}' for kind in ['문제','답안'] for ext in ['json','html']]
    for path in outputs: path.write_bytes(b'Existing output')
    before = {p: (p.read_bytes(),p.stat().st_mtime_ns) for p in outputs}
    (bundle.data/'validation.json').unlink()
    result = _cli(bundle,'--answer-overlay',str(bundle.path),'--json-only')
    assert result.returncode == 1, result.stderr
    assert {p: (p.read_bytes(),p.stat().st_mtime_ns) for p in outputs} == before
    assert set(bundle.build_dir.iterdir()) == set(outputs)


def test_symlinked_asset_rejected(bundle, tmp_path):
    outside = tmp_path/'outside.png'
    outside.write_bytes(bundle.asset.read_bytes())
    bundle.asset.unlink()
    bundle.asset.symlink_to(outside)
    bundle.sync()
    with pytest.raises(AnswerOverlayError): load_answer_overlay(bundle.path,bundle.repo,bundle.ids)


@pytest.mark.parametrize('markup', [
    '<svg viewBox="0 0 1 1"><image href="https://example.com/p.png"/></svg>',
    '<svg viewBox="0 0 1 1"><use href="../../outside.svg#shape"/></svg>',
    '<svg viewBox="0 0 1 1"><path d="M0 0 L1 1" fill="url(https://example.com/fill.svg#x)"/></svg>',
])
def test_untracked_svg_resources_are_rejected(bundle, markup):
    bundle.overlay['problems'][0]['steps'][0]['html'] += markup
    bundle.sync()
    with pytest.raises(AnswerOverlayError): load_answer_overlay(bundle.path,bundle.repo,bundle.ids)
