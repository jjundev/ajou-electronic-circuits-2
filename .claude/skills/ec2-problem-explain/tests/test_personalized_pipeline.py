"""Real CLI lifecycle with explicitly synthetic approvals; actual QA is in the report."""
import json
from pathlib import Path
import subprocess
import sys

import pytest
from _util import REPO, SKILL, approved, fragment, make_repo
from epe_cli import load_artifacts, load_fragments, load_run


class Pipeline:
    def __init__(self, root):
        self.root = root
        self.repo = make_repo(root / 'repo', ids=('P9.23',))  # real figure and a/b
        self.run = root / 'run'
        self.folder = self.repo / '복습노트/1007'
        self.build = root / 'answers'
        self.destination = self.build / 'personal-답안.pdf'
        self.build.mkdir()
        self.destination.write_bytes(b'previous answer PDF sentinel')
        self.previous_answer_bytes = self.destination.read_bytes()
        self.originals = {p: p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.call('extract', '--repo', self.repo, '--target', '1007', '--run', self.run)
        self.item = load_run(self.run)[0]
        p = self.item['pack'].problems[0]
        (self.item['folder'] / 'explanations/p1.html').write_text(fragment(p))
        self.call('build', '--run', self.run)
        self.call('check', '--run', self.run)
        self.artifacts = load_artifacts(self.item)
        self.overlay = self.folder / self.artifacts.manifest.relative_to(self.artifacts.html.parent).parent / 'answer-overlay.json'

    def call(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SKILL / 'scripts/epe_cli.py'), *map(str, args)], capture_output=True, text=True)
        if success: assert result.returncode == 0, result.stdout + result.stderr
        return result

    def approve_publish(self):
        review = approved(self.item['pack'], load_fragments(self.item), self.artifacts)
        (self.item['folder'] / 'review.json').write_text(json.dumps(review))
        self.call('publish', '--run', self.run)

    def run_answers(self, overlay=None):
        # Only repo path configuration is injected; all CLI and overlay code is real.
        wrapper = """import sys
from pathlib import Path
import build_workbook, assemble
build_workbook.paths.ROOT = Path(sys.argv[1])
assemble.TEXTBOOK = Path(sys.argv[1]) / '교과서/마이크로전자회로'
raise SystemExit(build_workbook.main(['build_workbook.py', *sys.argv[2:]]))
"""
        return subprocess.run([sys.executable, '-c', wrapper, str(self.repo), '--ids', 'P9.23',
            '--name', 'personal', '--mode', 'answers', '--answer-overlay', str(overlay or self.overlay),
            '--json-only', '--layout', 'video-16x9', '--build-dir', str(self.build), '--pdf-dir', str(self.build)],
            cwd=REPO / 'workbook', capture_output=True, text=True)


@pytest.fixture
def pipeline(tmp_path):
    return Pipeline(tmp_path)


def test_published_core_drives_pdf_data(pipeline):
    p = pipeline
    p.approve_publish()
    result = p.run_answers()
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((p.build / 'personal-답안.json').read_text())
    solution = data['problems'][0]['solution']
    assert '(a)' in solution['answer'] and '(b)' in solution['answer']
    assert solution['answer'].count('최종 답은 $1$') == 2
    assert [s['label'] for s in solution['steps']] == ['(a) 회로 판단', '(b) 회로 판단']
    assert '첫 식에서 계산하고' not in json.dumps(solution, ensure_ascii=False)
    assert all(path.read_bytes() == before for path, before in p.originals.items())
    assert p.destination.read_bytes() == p.previous_answer_bytes


@pytest.mark.parametrize('mutation', ['unreviewed', 'profile', 'overlay', 'source', 'figure'])
def test_unreviewed_or_changed_bundle_never_replaces_answer(pipeline, mutation):
    p = pipeline
    if mutation == 'unreviewed':
        result = p.call('publish', '--run', p.run, success=False)
        assert result.returncode != 0
        overlay = p.artifacts.manifest.parent / 'answer-overlay.json'
    else:
        p.approve_publish()
        overlay = p.overlay
        if mutation == 'profile': target = p.repo / '.claude/skills/ec2-review-pack/references/solution-style.md'
        elif mutation == 'overlay': target = p.overlay
        elif mutation == 'source': target = next((p.repo / '교과서').rglob('P9.23.md'))
        else: target = next((p.repo / '교과서').rglob('*.png'))
        target.write_bytes(target.read_bytes() + b'\n')
    result = p.run_answers(overlay)
    assert result.returncode != 0, result.stdout
    assert p.destination.read_bytes() == p.previous_answer_bytes
    assert not (p.build / 'personal-답안.json').exists()


def test_parent_failure_restores_coherent_pack(pipeline):
    """Real parent file APIs restore a published bundle after actual child rejection."""
    p = pipeline
    p.approve_publish()
    old_answer = p.folder / '복습문제_1007_Diff_Amp-답안.pdf'
    old_answer.write_bytes(p.previous_answer_bytes)
    (p.folder / '.assets/정리노트_1007_Diff_Amp.md').write_text('old matching note')
    before = {f.relative_to(p.folder).as_posix(): f.read_bytes() for f in p.folder.rglob('*') if f.is_file()}
    restore_run = p.root / 'parent'; restore_run.mkdir()
    parent_scripts = REPO / '.claude/skills/ec2-review-pack/scripts'
    sys.path.insert(0, str(parent_scripts))
    try:
        from pack_files import prepare_pack, inventory_pack, recover_pack
    finally:
        sys.path.remove(str(parent_scripts))
    (p.repo / 'STT').mkdir()
    manifest = restore_run / 'manifest.json'
    manifest.write_text(json.dumps({'range': '1007', 'slug': 'Diff_Amp',
                                    'problems': [{'id': 'P9.23'}]}))
    prepared = prepare_pack(p.repo, restore_run, manifest)
    assert Path(prepared['basic']).is_file() and Path(prepared['explanations']).is_file()
    # A new parent assembly changes input, causing the real child source guard to fail.
    (p.folder / '.assets/problems.txt').write_text('P9.23 | changed selection\n')
    note = p.folder / '정리노트_1007_Diff_Amp.html'
    note.write_text('new unapproved note')
    # Save the owned post-write inventory now, never recapture it at recovery.
    expected_current = inventory_pack(p.repo, '1007')
    result = p.call('build', '--run', p.run, success=False)
    assert result.returncode != 0 and '추출' in result.stderr
    assert old_answer.read_bytes() == p.previous_answer_bytes
    restored = recover_pack(p.repo, restore_run, '1007', expected_current)
    assert restored['status'] == 'restored'
    after = {f.relative_to(p.folder).as_posix(): f.read_bytes() for f in p.folder.rglob('*') if f.is_file()}
    assert after == before
    withheld = Path(restored['withheld'])
    assert (withheld / '.assets/problems.txt').read_text() == 'P9.23 | changed selection\n'
    assert p.run_answers().returncode == 0  # restored bundle remains coherent to real consumer
