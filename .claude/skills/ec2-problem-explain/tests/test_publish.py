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
        self.src = self.repo / '복습노트' / '1007' / '.assets' / 'problems.txt'
        self.folder = self.src.parent.parent
        self.backup = self.tmp / 'backup'
        self.pack = load_source(self.src, self.repo)
        self.fragments = {p.id: fragment(p) for p in self.pack.problems}
        self.artifacts = build_explanation(self.pack, self.fragments, self.tmp / 'stage', self.repo)

    def publish(self, reviews=None, pack=None, artifacts=None, destination=None):
        return publish_explanation(
            pack or self.pack, artifacts or self.artifacts, self.fragments,
            approved(self.pack, self.fragments, self.artifacts) if reviews is None else reviews,
            destination or self.folder, self.backup, self.repo)

    def write_index(self):
        assets = self.src.parent
        (assets / 'display-titles.json').write_text(json.dumps({'P10.02': '차동쌍'}))
        (assets / 'selection.json').write_text(json.dumps({
            'schema_version': 2, 'policy': 'exam-first-v2', 'workload': {'estimated_minutes': 10},
            'problems': [{'id': 'P10.02', 'priority': 'core', 'learning_goals': ['gain'],
                          'estimated_minutes': 10, 'subpart_count': 1}]}))

    def test_candidate_requires_both_selection_inputs(self):
        from pack_paths import PackPaths
        self.write_index()
        candidate = self.tmp / 'candidate'
        self.folder.rename(candidate)
        view = PackPaths(self.repo, self.folder, candidate)
        for name in ('display-titles.json', 'selection.json'):
            with self.subTest(name=name):
                path = candidate / '.assets' / name
                valid = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ExplainError, name):
                    load_source(self.src, self.repo, pack_paths=view, slug=self.pack.slug)
                path.write_bytes(valid)

    def test_candidate_review_refuses_physical_attempt_reference(self):
        from pack_paths import PackPaths
        from epe_publish import build_explanation_candidate
        self.write_index()
        candidate = self.repo / 'attempt'
        self.folder.rename(candidate)
        view = PackPaths(self.repo, self.folder, candidate)
        pack = load_source(self.src, self.repo, pack_paths=view, slug=self.pack.slug)
        artifacts = build_explanation(pack, self.fragments, self.tmp / 'candidate-stage', self.repo)
        reviews = approved(pack, self.fragments, artifacts)
        path = candidate / '.assets/problems.txt'
        reviews['references'].append({'path': str(path), 'sha256': sha256(path)})
        with self.assertRaisesRegex(ExplainError, '공개 경로'):
            build_explanation_candidate(pack, artifacts, self.fragments, reviews, candidate, self.repo)
        self.assertFalse((candidate / artifacts.html.name).exists())
        reviews['references'][-1]['path'] = str(self.src)
        outputs = build_explanation_candidate(pack, artifacts, self.fragments, reviews, candidate, self.repo)
        record = json.loads(next(p for p in outputs if p.name == 'validation.json').read_text())
        self.assertEqual(record['references'][-1]['path'], str(self.src))

    def test_candidate_materialization_uses_verified_public_identity(self):
        from pack_paths import PackPaths
        from epe_publish import build_explanation_candidate
        from epe_cli import extract, load_run
        self.write_index()
        candidate = self.tmp / 'candidate'
        self.folder.rename(candidate)
        view = PackPaths(self.repo, self.folder, candidate)
        child = self.tmp / 'child'
        self.assertEqual(extract(self.repo, '1007', child, pack_paths=view, slug=self.pack.slug), 0)
        pack = load_run(child)[0]['pack']
        artifacts = build_explanation(pack, self.fragments, self.tmp / 'candidate-stage', self.repo)
        reviews = approved(pack, self.fragments, artifacts)
        paths = build_explanation_candidate(pack, artifacts, self.fragments, reviews, candidate, self.repo)
        self.assertTrue(all(p.is_relative_to(candidate) for p in paths))
        self.assertTrue(any(p.name == 'validation.json' for p in paths))
        self.assertFalse(self.folder.exists())
        self.assertEqual(json.loads(artifacts.manifest.read_text())['source'], str(self.src))

    def test_verified_stage_materializes_in_separate_output_attempt(self):
        from epe_publish import build_explanation_candidate
        destination = self.tmp / 'consumer'
        review = approved(self.pack, self.fragments, self.artifacts)
        with self.assertRaisesRegex(ExplainError, 'selection.json|display-titles.json'):
            build_explanation_candidate(self.pack, self.artifacts, self.fragments, review, destination, self.repo)
        self.write_index()
        pack = load_source(self.src, self.repo)
        artifacts = build_explanation(pack, self.fragments, self.tmp / 'complete-stage', self.repo)
        review = approved(pack, self.fragments, artifacts)
        outputs = build_explanation_candidate(pack, artifacts, self.fragments, review, destination, self.repo)
        self.assertTrue(all(p.is_relative_to(destination) for p in outputs))
        self.assertFalse((self.folder / self.artifacts.html.name).exists())
        self.assertFalse((artifacts.manifest.parent / 'validation.json').exists())

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
