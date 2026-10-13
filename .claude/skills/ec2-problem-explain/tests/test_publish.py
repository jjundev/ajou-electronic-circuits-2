import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from _util import make_repo, fragment, approved
import epe_files
from epe_publish import publish_explanation
from epe_render import build_explanation
from epe_source import load_source, sha256
from epe_types import ExplainError


class PublishTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = make_repo(self.tmp / 'repo', ids=('P10.02',))
        self.src = self.repo / '복습노트' / '1007' / 'problems.txt'
        self.folder = self.src.parent
        self.backup = self.tmp / 'backup'
        self.pack = load_source(self.src, self.repo)
        self.fragments = {p.id: fragment(p) for p in self.pack.problems}
        self.artifacts = build_explanation(self.pack, self.fragments, self.tmp / 'stage', self.repo)

    def publish(self, reviews=None, pack=None, artifacts=None, destination=None):
        return publish_explanation(
            pack or self.pack, artifacts or self.artifacts, self.fragments,
            approved(self.pack, self.fragments, self.artifacts) if reviews is None else reviews,
            destination or self.folder, self.backup, self.repo)

    def test_no_review_keeps_existing_files(self):
        dst = self.folder / self.artifacts.html.name
        dst.write_bytes(b'old')
        source = self.src.read_bytes()
        with self.assertRaisesRegex(ExplainError, '보류'):
            self.publish({})
        self.assertEqual(dst.read_bytes(), b'old')
        self.assertEqual(self.src.read_bytes(), source)

    def test_stale_inputs_or_failed_reviews_are_refused(self):
        for change in ('source', 'fragment', 'artifact', 'report', 'browser', 'reference', 'manifest'):
            with self.subTest(change=change):
                self.tearDown_stage()
                reviews = approved(self.pack, self.fragments, self.artifacts)
                reference = self.tmp / 'repo' / 'reference.txt'
                reference.write_bytes(b'original')
                reviews['references'] = [{'path': str(reference), 'sha256': sha256(reference)}]
                if change == 'source':
                    self.src.write_bytes(self.src.read_bytes() + b'# changed\n')
                elif change == 'fragment':
                    self.fragments['p1'] += 'changed'
                elif change == 'artifact':
                    self.artifacts.html.write_bytes(self.artifacts.html.read_bytes() + b'changed')
                elif change == 'report':
                    reviews['artifact_hashes'] = {}
                elif change == 'manifest':
                    self.artifacts.manifest.write_bytes(self.artifacts.manifest.read_bytes() + b' ')
                elif change == 'reference':
                    reference.write_bytes(b'changed')
                else:
                    reviews['browser']['status'] = 'fail'
                with self.assertRaises(ExplainError):
                    self.publish(reviews)
                self.assertFalse((self.folder / self.artifacts.html.name).exists())

    def tearDown_stage(self):
        """Rebuild pristine source, fragments and stage for each subtest."""
        import shutil
        shutil.rmtree(self.tmp / 'stage', ignore_errors=True)
        shutil.rmtree(self.tmp / 'repo', ignore_errors=True)
        self.repo = make_repo(self.tmp / 'repo', ids=('P10.02',))
        self.pack = load_source(self.src, self.repo)
        self.fragments = {p.id: fragment(p) for p in self.pack.problems}
        self.artifacts = build_explanation(self.pack, self.fragments, self.tmp / 'stage', self.repo)

    def test_changed_figure_or_md_refuses_publish(self):
        for target in ('figure', 'md'):
            with self.subTest(target=target):
                self.tearDown_stage()
                reviews = approved(self.pack, self.fragments, self.artifacts)
                path = Path(next(i for i in self.pack.inputs
                                 if (i.endswith('.png') if target == 'figure' else i.endswith('.md'))))
                path.write_bytes(path.read_bytes() + b'\n ')
                with self.assertRaisesRegex(ExplainError, '입력 변경'):
                    self.publish(reviews)
                self.assertFalse((self.folder / self.artifacts.html.name).exists())

    def test_outside_stage_and_wrong_destination_refused(self):
        reviews = approved(self.pack, self.fragments, self.artifacts)
        outside = self.tmp / 'original.html'
        outside.touch()
        with self.assertRaises(ExplainError):
            self.publish(reviews, artifacts=replace(self.artifacts, files=self.artifacts.files + (outside,)))
        with self.assertRaises(ExplainError):
            self.publish(reviews, destination=self.tmp)

    def test_destination_equal_to_input_is_refused(self):
        # Pretend an input lives at an explanation-owned path: it must never be overwritten.
        owned = self.folder / self.artifacts.html.name
        owned.write_bytes(b'user file')
        pack = replace(self.pack, inputs=self.pack.inputs + (str(owned),))
        import epe_publish
        original = epe_publish.load_source
        epe_publish.load_source = lambda path, repo: pack
        self.addCleanup(setattr, epe_publish, 'load_source', original)
        artifacts = build_explanation(pack, self.fragments, self.tmp / 'stage2', self.repo)
        with self.assertRaisesRegex(ExplainError, '원본 덮어쓰기 금지'):
            publish_explanation(pack, artifacts, self.fragments,
                                approved(pack, self.fragments, artifacts), self.folder, self.backup, self.repo)
        self.assertEqual(owned.read_bytes(), b'user file')

    def test_success_preserves_original_and_saves_review(self):
        before = self.src.read_bytes()
        published = self.publish()
        self.assertEqual(self.src.read_bytes(), before)
        self.assertEqual((self.folder / self.artifacts.html.name).read_bytes(), self.artifacts.html.read_bytes())
        report = next(p for p in published if p.name == 'validation.json')
        self.assertEqual(json.loads(report.read_text(encoding='utf-8'))['browser']['status'], 'pass')

    def test_publish_preserves_note_pdf_and_problems_txt(self):
        protected = [p for p in self.folder.iterdir() if p.is_file()]
        self.assertTrue(any(p.suffix == '.pdf' for p in protected) and any(p.name.startswith('정리노트') for p in protected))
        before = {p: p.read_bytes() for p in protected}
        self.publish()
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)

    def test_republish_backs_up_previous_explanation(self):
        self.publish()
        dst = self.folder / self.artifacts.html.name
        self.assertFalse(self.backup.exists() and any(self.backup.rglob(f'*{dst.name}')))
        previous = dst.read_bytes()
        self.publish()
        saved = [p for p in self.backup.rglob('*') if p.is_file() and p.name.endswith(dst.name)]
        self.assertEqual([p.read_bytes() for p in saved], [previous])

    def test_replace_failure_rolls_back_pair(self):
        for file in (self.artifacts.html, self.artifacts.md):
            (self.folder / file.name).write_bytes(b'old-' + file.suffix.encode())
        real = epe_files._replace_copy
        calls = []
        def fail_once(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError('injected write failure')
            return real(source, destination)
        epe_files._replace_copy = fail_once
        self.addCleanup(setattr, epe_files, '_replace_copy', real)
        with self.assertRaisesRegex(ExplainError, 'injected'):
            self.publish()
        for file in (self.artifacts.html, self.artifacts.md):
            self.assertEqual((self.folder / file.name).read_bytes(), b'old-' + file.suffix.encode())
        self.assertFalse(list(self.folder.rglob('validation.json')))

    def test_overlapping_publication_lock_is_refused(self):
        with epe_files.publication_lock([self.folder / self.artifacts.html.name]):
            with self.assertRaisesRegex(ExplainError, '잠금'):
                self.publish()


if __name__ == '__main__':
    unittest.main()
