"""카탈로그의 원문 보존과 오래된 입력 검출을 실제 파일로 확인한다."""
import json
from pathlib import Path
import sys
import tempfile
import unicodedata
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exam_catalog as catalog


class CatalogTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.folder = self.repo / 'from_the_past/md/2099-1_중간'
        self.folder.mkdir(parents=True)
        (self.folder / 'exam.yaml').write_text('exam: 시험\nnotes: [원본 주의사항]\n')
        (self.folder / 'figures/redrawn').mkdir(parents=True)
        (self.folder / 'figures/figures.yaml').write_text('dpi: 144\n')
        (self.folder / 'figures/fig-Q1.png').write_bytes(b'crop')
        (self.folder / 'figures/redrawn/fig-Q1.png').write_bytes(b'redrawn')
        self.md = self.folder / 'Q1.md'
        self.meta = dict(id='2099-1_중간-Q1', kind='기출', number='1', points=20,
                         source='../../original.pdf', pdf_page=1, textbook_chapters=[9, 10],
                         figures=[dict(id='Q1', role='problem', panels=['a', 'b'])],
                         depends_on=[], refs=['다른 문항 참고'])
        self.body = ('# 기출 2099-1 중간 1 — 캐스코드와 차동쌍\n\n'
                     '## 원문\n$g_m r_o \\gg 1$일 때 구하시오.\n\n'
                     '## 조건\n- $R = 1$ (원문에 없음)\n\n'
                     '## 구할 것\n- (1) 출력 저항\n- (2) 차동 이득\n\n'
                     '## 회로 — Fig Q1(a)\n```spice\nR1 a b 1k\n```\n\n'
                     '## 힌트\n### 반회로\n- 대칭을 사용\n\n'
                     '## 풀이\n### (1) 저항\n- $R_{out}=1$\n### (2) 이득\n- $A_v=2$\n'
                     '### 답\n- (1) 1 (2) 2\n')
        self.save()
        self.out = self.repo / 'from_the_past/json'

    def save(self):
        self.md.write_text('---\n' + yaml.safe_dump(self.meta, allow_unicode=True, sort_keys=False)
                           + '---\n' + self.body, encoding='utf-8')

    def test_lossless_detail_and_light_index(self):
        index, details = catalog.build_catalog(self.repo)
        item = details[self.meta['id']]
        self.assertEqual(item['raw_md'], self.md.read_text())
        self.assertEqual(item['metadata'], self.meta)
        self.assertEqual(item['exam']['notes'], ['원본 주의사항'])
        self.assertIn('원문에 없음', item['body_md'])
        self.assertIn('R1 a b 1k', str(item['sections']))
        self.assertEqual(item['selection']['status'], 'unclassified')
        self.assertEqual(len(index['problems']), 1)
        self.assertEqual(index['problems'][0]['adoption_unit'], 'whole')
        self.assertNotIn('raw_md', index['problems'][0])
        self.assertEqual(len(index['problems'][0]['subparts']), 2)
        self.assertTrue(item['figures'][0]['display_path'].endswith('redrawn/fig-Q1.png'))
        self.assertTrue(all(not Path(p).is_absolute() for p in item['input_hashes']))

    def test_no_solution_is_preserved_and_eligible(self):
        self.body = self.body.split('## 풀이')[0]
        self.save()
        index, details = catalog.build_catalog(self.repo)
        self.assertTrue(index['problems'][0]['eligible'])
        self.assertEqual(index['schema_version'], 2)
        self.assertEqual(index['problems'][0]['reference_solution'], 'none')
        self.assertIn(self.meta['id'], details)

    def test_hash_and_checked_generated_files_detect_changes(self):
        catalog.write_catalog(self.repo, self.out)
        self.assertEqual(catalog.check_catalog(self.repo, self.out), [])
        for file in [self.md, self.folder / 'exam.yaml', self.folder / 'figures/figures.yaml',
                     self.folder / 'figures/fig-Q1.png', self.folder / 'figures/redrawn/fig-Q1.png']:
            before = file.read_bytes()
            file.write_bytes(before + b'\n')
            self.assertTrue(catalog.check_catalog(self.repo, self.out), str(file))
            file.write_bytes(before)
        detail = self.out / 'problems' / f"{self.meta['id']}.json"
        detail.write_text('{}')
        self.assertTrue(catalog.check_catalog(self.repo, self.out))

    def test_selection_hash_does_not_hash_itself_and_stales_on_body_or_figure(self):
        before = catalog.content_hash(self.md)
        self.meta['selection'] = dict(topics=['캐스코드'], required_concepts=['出力抵抗'],
                                     circuit_types=['MOS'], learning_goals=['出力抵抗'],
                                     evidence_sections=['구할 것', '풀이'],
                                     reviewed_content_sha256=before, review_status='reviewed')
        self.save()
        self.assertEqual(catalog.content_hash(self.md), before)
        index, _ = catalog.build_catalog(self.repo)
        self.assertEqual(index['problems'][0]['selection']['status'], 'reviewed')
        self.body += '\n추가 조건\n'
        self.save()
        index, _ = catalog.build_catalog(self.repo)
        self.assertEqual(index['problems'][0]['selection']['status'], 'stale')

    def test_broken_figure_and_duplicate_id_are_errors(self):
        (self.folder / 'Q2.md').write_text(self.md.read_text())
        with self.assertRaises(catalog.CatalogError):
            catalog.build_catalog(self.repo)
        (self.folder / 'Q2.md').unlink()
        (self.folder / 'figures/fig-Q1.png').unlink()
        with self.assertRaisesRegex(catalog.CatalogError, '그림'):
            catalog.build_catalog(self.repo)

    def test_figure_config_is_required_for_renderable_problem(self):
        (self.folder / 'figures/figures.yaml').unlink()
        with self.assertRaisesRegex(catalog.CatalogError, 'figures.yaml'):
            catalog.build_catalog(self.repo)

    def test_nfd_directory_is_resolved(self):
        folder = self.folder.with_name(unicodedata.normalize('NFD', self.folder.name))
        self.folder.rename(folder)
        index, _ = catalog.build_catalog(self.repo)
        self.assertEqual(index['problems'][0]['id'], self.meta['id'])
        self.assertTrue((self.repo / index['problems'][0]['md_path']).is_file())

    def test_outside_repo_asset_is_rejected(self):
        (self.folder / 'figures/fig-Q1.png').unlink()
        (self.folder / 'figures/fig-Q1.png').symlink_to(Path(__file__))
        with self.assertRaises(catalog.CatalogError):
            catalog.build_catalog(self.repo)

    def test_invalid_selection_and_missing_dependency_are_errors(self):
        self.meta['selection'] = {'topics': 'wrong'}
        self.save()
        with self.assertRaises(catalog.CatalogError):
            catalog.build_catalog(self.repo)
        self.meta.pop('selection')
        self.meta['depends_on'] = ['missing']
        self.save()
        with self.assertRaisesRegex(catalog.CatalogError, '의존'):
            catalog.build_catalog(self.repo)

    def test_per_subpart_concepts_are_exposed_and_bad_labels_rejected(self):
        self.meta['selection'] = dict(topics=['차동쌍'], circuit_types=['MOS'],
            required_concepts=['출력 저항', '차동 이득'], learning_goals=['이득 계산'],
            evidence_sections=['구할 것'], reviewed_content_sha256=catalog.content_hash(self.md),
            review_status='draft', subpart_requirements=[
                dict(label='1', required_concepts=['출력 저항']),
                dict(label='2', required_concepts=['차동 이득'])])
        self.save()
        index, _ = catalog.build_catalog(self.repo)
        self.assertEqual(index['problems'][0]['subparts'][1]['required_concepts'], ['차동 이득'])
        self.meta['selection']['subpart_requirements'][0]['label'] = '9'
        self.save()
        with self.assertRaisesRegex(catalog.CatalogError, '소문항'):
            catalog.build_catalog(self.repo)

    def test_removed_problem_leaves_no_orphan_generated_detail(self):
        catalog.write_catalog(self.repo, self.out)
        (self.out / 'problems/stale.json').write_text('{}')
        self.assertTrue(catalog.check_catalog(self.repo, self.out))
        catalog.write_catalog(self.repo, self.out)
        self.assertFalse((self.out / 'problems/stale.json').exists())


if __name__ == '__main__':
    unittest.main()
