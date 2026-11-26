import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _util import SKILL, make_repo, concise_fragment, fragment, approved
from epe_source import load_source
from epe_cli import load_run, load_artifacts, load_fragments

CLI = SKILL / 'scripts/epe_cli.py'


def call(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                          capture_output=True, text=True, encoding='utf-8')


class CliTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.run_dir = self.tmp / 'run'

    def repo(self, **kw):
        return make_repo(self.tmp / 'repo', **kw)

    def write_fragments(self, item, body=concise_fragment):
        for p in item['pack'].problems:
            (item['folder'] / 'explanations' / f'{p.id}.html').write_text(body(p), encoding='utf-8')

    def test_missing_target_returns_one(self):
        repo = self.repo()
        result = call('extract', '--repo', repo, '--target', '0101', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn('대상 없음', result.stderr)

    def test_extract_refuses_nonempty_run(self):
        repo = self.repo()
        self.run_dir.mkdir()
        (self.run_dir / 'keep.txt').write_text('keep')
        result = call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.run_dir / 'keep.txt').read_text(), 'keep')

    def test_forged_serialized_problem_is_rejected(self):
        repo = self.repo()
        self.assertEqual(call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir).returncode, 0)
        source_json = next(self.run_dir.rglob('source.json'))
        value = json.loads(source_json.read_text(encoding='utf-8'))
        value['problems'][0]['ask_html'] = '위조 조건'
        source_json.write_text(json.dumps(value), encoding='utf-8')
        result = call('check', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn('추출', result.stderr)

    def test_bucket_name_and_source_change_detected(self):
        repo = self.repo(ids=('P10.02',))
        self.assertEqual(call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir).returncode, 0)
        self.assertTrue((self.run_dir / 'review-1007-Diff_Amp/source.json').is_file())
        md = next((repo / '교과서').rglob('P10.02.md'))
        md.write_bytes(md.read_bytes() + b'\n')
        result = call('build', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn('추출', result.stderr)

    def test_range_extract_creates_bucket_per_pack(self):
        self.repo(range_='0909', slug='Alpha', ids=('P10.02',))
        repo = self.repo(range_='0910', slug='Beta', ids=('P10.02',))
        result = call('extract', '--repo', repo, '--target', '0909-0910', '--run', self.run_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.run_dir / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(index['targets'], ['review-0909-Alpha', 'review-0910-Beta'])

    def test_one_failing_pack_does_not_block_other(self):
        self.repo(range_='0909', slug='Alpha', ids=('P10.02',))
        repo = self.repo(range_='0910', slug='Beta', ids=('P10.02',))
        (repo / '복습노트/0910/.assets/problems.txt').write_text('P99.99 | 없는 문항\n', encoding='utf-8')
        result = call('extract', '--repo', repo, '--target', '0909-0910', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertTrue((self.run_dir / 'review-0909-Alpha/source.json').is_file())
        self.assertFalse((self.run_dir / 'review-0910-Beta/source.json').exists())

    def test_one_stale_pack_does_not_block_other_pack(self):
        self.repo(range_='0909', slug='Alpha', ids=('P10.02',))
        repo = self.repo(range_='0910', slug='Beta', ids=('P10.02',))
        self.assertEqual(call('extract', '--repo', repo, '--target', '0909-0910', '--run', self.run_dir).returncode, 0)
        for item in load_run(self.run_dir):
            self.write_fragments(item)
        later = repo / '복습노트/0910/.assets/problems.txt'
        later.write_bytes(later.read_bytes() + b'\n')
        result = call('build', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertTrue((self.run_dir / 'review-0909-Alpha/stage.json').is_file())
        self.assertFalse((self.run_dir / 'review-0910-Beta/stage.json').is_file())

    def test_check_refuses_fragments_changed_after_build(self):
        repo = self.repo(ids=('P10.02',))
        self.assertEqual(call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir).returncode, 0)
        item = load_run(self.run_dir)[0]
        self.write_fragments(item)
        self.assertEqual(call('build', '--run', self.run_dir).returncode, 0)
        (item['folder'] / 'explanations/p1.html').write_text('<p>풀이 누락</p>', encoding='utf-8')
        result = call('check', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        machine = json.loads((item['folder'] / 'machine.json').read_text(encoding='utf-8'))
        self.assertEqual(machine['status'], 'fail')

    def test_new_build_rejects_the_seven_section_format(self):
        repo = self.repo(ids=('E9.05',))
        result = call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write_fragments(load_run(self.run_dir)[0], fragment)
        result = call('build', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('p1: 새 원고', result.stderr)
        self.assertFalse(list(self.run_dir.rglob('stage.json')))

    def test_legacy_rerender_rechecks_the_published_origin(self):
        from shutil import copyfile
        from epe_render import build_explanation, dump

        repo = self.repo(ids=('E9.05',))
        result = call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        item, = load_run(self.run_dir)
        self.write_fragments(item, lambda problem: fragment(problem) + '\n')
        fragments = load_fragments(item)
        pack = item['pack']
        historical = build_explanation(pack, fragments, self.tmp / 'historical', repo)
        for source in historical.files:
            dest = pack.folder / source.relative_to(historical.html.parent)
            dest.parent.mkdir(parents=True, exist_ok=True)
            copyfile(source, dest)
        published_manifest = pack.folder / historical.manifest.relative_to(historical.html.parent)
        dump(published_manifest.with_name('validation.json'), approved(pack, fragments, historical))

        rebuilt = self.tmp / 'rebuilt'
        result = call('rerender', '--repo', repo, '--target', '1007', '--run', rebuilt)
        self.assertEqual(result.returncode, 0, result.stderr)
        rebuilt_item, = load_run(rebuilt)
        stage = load_artifacts(rebuilt_item)
        dump(rebuilt_item['folder'] / 'review.json', approved(pack, load_fragments(rebuilt_item), stage))
        self.assertEqual(call('check', '--run', rebuilt).returncode, 0)

        original_manifest = published_manifest.read_bytes()
        published_manifest.write_bytes(original_manifest + b'\n')
        for command in ('check', 'publish'):
            result = call(command, '--run', rebuilt)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('재렌더링 원본', result.stderr)

        published_manifest.write_bytes(original_manifest)

        explanation = rebuilt_item['folder'] / 'explanations/p1.html'
        original_fragment = explanation.read_bytes()
        self.assertIn(b'\n', original_fragment)
        explanation.write_bytes(original_fragment.replace(b'\n', b'\r\n'))
        for command in ('check', 'publish'):
            result = call(command, '--run', rebuilt)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('재렌더링 원본 조각', result.stderr)
        explanation.write_bytes(original_fragment)

        result = call('publish', '--run', rebuilt)
        self.assertEqual(result.returncode, 0, result.stderr)
        second = self.tmp / 'rebuilt-again'
        result = call('rerender', '--repo', repo, '--target', '1007', '--run', second)
        self.assertEqual(result.returncode, 0, result.stderr)
        second_item, = load_run(second)
        review = json.loads((second_item['folder'] / 'review.json').read_text(encoding='utf-8'))
        self.assertEqual(review['content']['status'], 'pass')
        self.assertEqual(review['browser']['status'], 'not_run')

    def test_end_to_end_publish(self):
        repo = self.repo(ids=('P10.02',))
        folder = repo / '복습노트/1007'
        inputs = {p: p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        self.assertEqual(call('extract', '--repo', repo, '--target', '1007', '--run', self.run_dir).returncode, 0)
        item = load_run(self.run_dir)[0]
        self.assertEqual(item['pack'], load_source(folder / '.assets' / 'problems.txt', repo))
        self.write_fragments(item)
        for command in ('build', 'check'):
            result = call(command, '--run', self.run_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = call('publish', '--run', self.run_dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn('보류', result.stderr)
        self.assertFalse(list(folder.glob('문제설명*')))
        item = load_run(self.run_dir)[0]
        artifacts = load_artifacts(item)
        reviews = approved(item['pack'], load_fragments(item), artifacts)
        (item['folder'] / 'review.json').write_text(json.dumps(reviews, ensure_ascii=False), encoding='utf-8')
        result = call('publish', '--run', self.run_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((folder / '문제설명_1007_Diff_Amp.html').is_file())
        self.assertTrue((folder / '.assets' / '문제설명_1007_Diff_Amp.md').is_file())
        for path, data in inputs.items():
            self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
