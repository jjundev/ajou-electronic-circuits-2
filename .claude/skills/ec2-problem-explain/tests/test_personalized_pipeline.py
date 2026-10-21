"""Real CLI lifecycle with explicitly synthetic approvals; actual QA is in the report."""
import hashlib
import json
from pathlib import Path
import re
import shutil
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
        if mutation == 'profile': target = p.repo / 'docs/learning/solution-style.md'
        elif mutation == 'overlay': target = p.overlay
        elif mutation == 'source': target = next((p.repo / '교과서').rglob('P9.23.md'))
        else: target = next((p.repo / '교과서').rglob('*.png'))
        target.write_bytes(target.read_bytes() + b'\n')
    result = p.run_answers(overlay)
    assert result.returncode != 0, result.stdout
    assert p.destination.read_bytes() == p.previous_answer_bytes
    assert not (p.build / 'personal-답안.json').exists()


def test_parent_failure_restores_coherent_pack(pipeline):
    """Back up a real published bundle; trigger real child rejection; run parent recipe."""
    p = pipeline
    p.approve_publish()
    old_answer = p.folder / '복습문제_1007_Diff_Amp-답안.pdf'
    old_answer.write_bytes(p.previous_answer_bytes)
    (p.folder / '.assets/정리노트_1007_Diff_Amp.md').write_text('old matching note')
    before = {f.relative_to(p.folder).as_posix(): f.read_bytes() for f in p.folder.rglob('*') if f.is_file()}
    restore_run = p.root / 'parent'; restore_run.mkdir()
    for kind in ('basic-pack', 'explanations'):
        backup = restore_run / kind
        roots = [f for base in (p.folder, p.folder / '.assets') for f in base.iterdir()
                 if f.name != '.assets' and (('문제설명' in f.name) == (kind == 'explanations'))]
        record = {'range': '1007', 'backup': str(backup), 'roots': [], 'files': {}, 'dirs': []}
        for source in roots:
            rel = source.relative_to(p.folder)
            dest = backup / rel; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, dest) if source.is_dir() else shutil.copy2(source, dest)
            record['roots'].append(rel.as_posix())
            for f in [dest, *(dest.rglob('*') if dest.is_dir() else [])]:
                name = f.relative_to(backup).as_posix()
                if f.is_dir(): record['dirs'].append(name)
                else: record['files'][name] = hashlib.sha256(f.read_bytes()).hexdigest()
        (restore_run / f'{kind}-backup.json').write_text(json.dumps(record))
    # A new parent assembly changes input, causing the real child source guard to fail.
    (p.folder / '.assets/problems.txt').write_text('P9.23 | changed selection\n')
    note = p.folder / '정리노트_1007_Diff_Amp.html'
    note.write_text('new unapproved note')
    result = p.call('build', '--run', p.run, success=False)
    assert result.returncode != 0 and '추출' in result.stderr
    assert old_answer.read_bytes() == p.previous_answer_bytes
    text = (REPO / '.claude/skills/ec2-review-pack/references/problem-explain-integration.md').read_text()
    recipe = re.search(r'''python3 - "\$REPO" "\$RUN" "\$RANGE" <<'EOF'\n(.*?)\nEOF''', text, re.S)
    assert recipe
    result = subprocess.run([sys.executable, '-', str(p.repo), str(restore_run), '1007'], input=recipe.group(1), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    after = {f.relative_to(p.folder).as_posix(): f.read_bytes() for f in p.folder.rglob('*') if f.is_file()}
    assert after == before
    withheld = next(restore_run.glob('withheld-*'))
    assert (withheld / '.assets/problems.txt').read_text() == 'P9.23 | changed selection\n'
    assert p.run_answers().returncode == 0  # restored bundle remains coherent to real consumer
