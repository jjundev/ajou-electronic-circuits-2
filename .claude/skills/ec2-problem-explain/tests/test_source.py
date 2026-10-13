import shutil
import tempfile
import unittest
import unicodedata
from urllib.parse import unquote
from pathlib import Path

from _util import make_repo, REPO, EXAMS
from epe_source import resolve_sources, load_source, md_path, figure_paths, subparts
from epe_types import ExplainError
from epe_shared import load_problem

EXAM_FIG = Path('from_the_past/md/2023-1_중간/figures/fig-Q4.png')


def add_pack(repo, name, problems=True, folder_form=lambda s: s):
    folder = Path(repo) / folder_form('복습노트') / name
    folder.mkdir(parents=True, exist_ok=True)
    if problems:
        (folder / 'problems.txt').write_text('P10.02 | x\n', encoding='utf-8')
    return folder


class SourceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def repo(self, **kw):
        return make_repo(self.tmp, **kw)

    def plain_exam_figure(self, repo):
        """make_repo copies the real redrawn art when it exists; drop it to test the plain crop."""
        shutil.rmtree(repo / EXAM_FIG.parent / 'redrawn', ignore_errors=True)

    def names(self, paths):
        return [unicodedata.normalize('NFC', p.parent.name) for p in paths]

    def test_latest_pack_with_problems_is_default(self):
        repo = self.repo()
        add_pack(repo, '0904', problems=False)
        self.assertEqual(self.names(resolve_sources(repo, None)), ['1007'])

    def test_default_with_tied_end_date_is_ambiguous(self):
        repo = self.repo()
        add_pack(repo, '1005-1007')
        with self.assertRaisesRegex(ExplainError, '여러 후보'):
            resolve_sources(repo, None)

    def test_pack_without_problems_txt_is_refused(self):
        repo = self.repo()
        add_pack(repo, '0904', problems=False)
        with self.assertRaisesRegex(ExplainError, '문제 없는 팩'):
            resolve_sources(repo, '0904')

    def test_range_skips_packs_without_problems(self):
        repo = self.repo()
        add_pack(repo, '0902', problems=False)
        add_pack(repo, '0909')
        add_pack(repo, '0911')
        self.assertEqual(self.names(resolve_sources(repo, '0902-0911')), ['0909', '0911'])

    def test_combined_and_individual_range_is_ambiguous(self):
        repo = self.repo()
        add_pack(repo, '0909-0911')
        add_pack(repo, '0909')
        with self.assertRaisesRegex(ExplainError, '여러 후보'):
            resolve_sources(repo, '0909-0911')

    def test_combined_folder_alone_is_chosen(self):
        repo = self.repo()
        add_pack(repo, '0909-0911')
        self.assertEqual(self.names(resolve_sources(repo, '0909-0911')), ['0909-0911'])

    def test_bad_dates_and_reversed_range(self):
        repo = self.repo()
        with self.assertRaisesRegex(ExplainError, '날짜 범위 순서 오류'):
            resolve_sources(repo, '0911-0909')
        with self.assertRaisesRegex(ExplainError, '잘못된 날짜'):
            resolve_sources(repo, '1340')

    def test_nfd_folder_resolves(self):
        repo = self.repo(nfd=True)
        found = resolve_sources(repo, '1007')
        self.assertEqual(self.names(found), ['1007'])
        self.assertEqual(self.names(resolve_sources(repo, None)), ['1007'])
        self.assertEqual(load_source(found[0], repo).slug, 'Diff_Amp')

    def test_problems_txt_blank_and_malformed_lines(self):
        repo = self.repo()
        txt = resolve_sources(repo, '1007')[0]
        txt.write_text('\nP10.02 | 설명\n\n', encoding='utf-8')
        self.assertEqual([p.id for p in load_source(txt, repo).problems], ['p1'])
        txt.write_text('P10.02 | 설명\nP10.02\n', encoding='utf-8')
        with self.assertRaisesRegex(ExplainError, '2행 형식 오류'):
            load_source(txt, repo)

    def test_load_source_order_ids_and_subparts(self):
        repo = self.repo()
        pack = load_source(resolve_sources(repo, '1007')[0], repo)
        self.assertEqual([p.id for p in pack.problems], ['p1', 'p2'])
        self.assertTrue(pack.problems[0].source.startswith('P10.02 · 장말문제'))
        self.assertEqual(pack.problems[0].subparts, ('main',))
        self.assertEqual(pack.problems[1].subparts, ('1', '2', '3'))
        self.assertEqual((pack.slug, pack.range, pack.profile), ('Diff_Amp', '1007', 'review'))
        self.assertEqual(len(pack.sha256), 64)
        self.assertEqual(pack.inputs[0], str(pack.path))

    def test_slug_must_be_unique(self):
        repo = self.repo()
        folder = resolve_sources(repo, '1007')[0].parent
        (folder / '정리노트_1007_Other.html').write_text('x', encoding='utf-8')
        with self.assertRaisesRegex(ExplainError, '정리노트'):
            load_source(folder / 'problems.txt', repo)

    def test_figure_src_is_relative_repo_file(self):
        repo = self.repo()
        txt = resolve_sources(repo, '1007')[0]
        pack = load_source(txt, repo)
        html = ''.join(h for p in pack.problems for h in p.figures_html)
        import re
        srcs = re.findall(r'src="([^"]+)"', html)
        self.assertTrue(srcs)
        for src in srcs:
            self.assertTrue(src.endswith('.png'))
            self.assertTrue((txt.parent / unquote(src)).resolve().is_file(), src)
            self.assertEqual((txt.parent / unquote(src)).resolve().parts[:len(repo.resolve().parts)], repo.resolve().parts)

    def test_exam_prefers_redrawn_figure(self):
        repo = self.repo()
        self.plain_exam_figure(repo)
        md = md_path(repo, '2023-1_중간-Q4')
        p = load_problem(md)
        self.assertEqual(figure_paths(p), [repo / EXAM_FIG])
        redrawn = repo / EXAM_FIG.parent / 'redrawn' / 'fig-Q4.png'
        redrawn.parent.mkdir(exist_ok=True)
        redrawn.write_bytes((repo / EXAM_FIG).read_bytes())
        self.assertEqual(figure_paths(p), [redrawn])
        pack = load_source(resolve_sources(repo, '1007')[0], repo)
        self.assertIn(str(redrawn), pack.inputs)
        self.assertIn('redrawn/fig-Q4.png', pack.problems[1].figures_html[0])

    def test_digest_changes_when_figure_changes(self):
        repo = self.repo()
        self.plain_exam_figure(repo)
        txt = resolve_sources(repo, '1007')[0]
        before = load_source(txt, repo).sha256
        with (repo / EXAM_FIG).open('ab') as f:
            f.write(b'\0')
        self.assertNotEqual(load_source(txt, repo).sha256, before)

    def test_unknown_id_reports_id(self):
        repo = self.repo()
        txt = resolve_sources(repo, '1007')[0]
        txt.write_text('P99.99 | x\n', encoding='utf-8')
        with self.assertRaisesRegex(ExplainError, 'P99.99'):
            load_source(txt, repo)
        txt.write_text('bogus | x\n', encoding='utf-8')
        with self.assertRaisesRegex(ExplainError, 'bogus'):
            load_source(txt, repo)

    def test_path_outside_repo_is_refused(self):
        repo = self.repo()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        (outside / 'problems.txt').write_text('P10.02 | x\n', encoding='utf-8')
        with self.assertRaisesRegex(ExplainError, '저장소 밖'):
            load_source(outside / 'problems.txt', repo)

    def test_subparts_rules(self):
        self.assertEqual(subparts('<ul><li>구하라</li></ul>'), ('main',))
        self.assertEqual(subparts('<ol><li>(a) x</li><li>(b) y</li></ol>'), ('a', 'b'))
        self.assertEqual(subparts('<ul><li>(a) x<ul><li>(z) n</li></ul></li></ul>'), ('a',))
        # R3: unlabeled items coexist with labeled ones and are ignored (was: 소문항 표지 불일치 error)
        self.assertEqual(subparts('<ul><li>(1) x</li><li>y</li></ul>'), ('1',))
        with self.assertRaises(ExplainError):
            subparts('<ul><li>(1) x</li><li>(1) y</li></ul>')

    def test_subparts_figure_part_references_are_not_labels(self):
        def ul(*items):
            return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
        self.assertEqual(subparts(ul('(a), (b) 각 단의 공통 모드 제거비(CMRR)', '두 결과를 비교')), ('main',))
        self.assertEqual(subparts(ul('(a)–(c) 각 회로의 $I_{copy}$', '오차를 정규화')), ('main',))
        self.assertEqual(subparts(ul('다음 각 경우 테일 노드 전압은?', '(a) $M_1$과 x', '(b) $I_{SS}$가 두 배',
                                     '(c) 게이트 y')), ('a', 'b', 'c'))
        self.assertEqual(subparts(ul('(a)–(c) 각 회로의 차동 전압 이득')), ('main',))
        self.assertEqual(subparts(ul('(a), (b), (c) 각 경우에')), ('main',))
        self.assertEqual(subparts(ul('(a)-(c) 각 회로')), ('main',))
        with self.assertRaisesRegex(ExplainError, '소문항 표지 중복'):
            subparts(ul('(a) x', '그냥', '(a) y'))

    def test_real_packs_with_figure_part_references_load(self):
        repo = self.repo(ids=('P10.70', 'P10.35', 'P9.46', 'P10.52', 'P10.17'))
        pack = load_source(repo / '복습노트' / '1007' / 'problems.txt', repo)
        self.assertEqual([p.subparts for p in pack.problems], [('main',), ('a', 'b', 'c'), ('main',), ('main',), ('main',)])


if __name__ == '__main__':
    unittest.main()
