import contextlib
import io
import json
import shutil
from pathlib import Path
import tempfile
import unicodedata
import unittest

from _util import REPO

import problem_index

HAS_WORKBOOK = (REPO / "workbook" / "problem.py").exists()


def by_id(rows):
    return {r[0]: r for r in rows}


class TestUnits(unittest.TestCase):
    def test_secnum(self):
        self.assertEqual(problem_index.secnum({"kind": "장말문제", "section": "10.2.3 소신호 해석"}), "10.2.3")
        self.assertEqual(problem_index.secnum({"kind": "장말문제", "section": "Design Problems"}), "Design Problems")
        self.assertEqual(problem_index.secnum({"kind": "기출", "textbook_chapters": [9, 10]}), "ch9,10")

    def test_used_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0909" / ".assets").mkdir(parents=True)
            (notes / "0909" / ".assets" / "problems.txt").write_text(
                "P9.01 | 이유\n\n" + unicodedata.normalize("NFD", "2023-1_기말-Q1") + " | 기출\n", encoding="utf-8")
            self.assertEqual(problem_index.used_ids(notes), {"P9.01", "2023-1_기말-Q1"})
            self.assertEqual(problem_index.used_ids(notes / "missing"), set())

    def test_used_ids_ignores_top_level_problems_txt(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0909").mkdir()
            (notes / "0909" / "problems.txt").write_text("P9.01 | 옛 위치\n", encoding="utf-8")
            self.assertEqual(problem_index.used_ids(notes), set())

    def test_used_ids_exclude_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0918" / ".assets").mkdir(parents=True)
            (notes / "0918" / ".assets" / "problems.txt").write_text("P9.01 | 이유\n", encoding="utf-8")
            (notes / "0923" / ".assets").mkdir(parents=True)
            (notes / "0923" / ".assets" / "problems.txt").write_text("P9.02 | 이유\n", encoding="utf-8")
            self.assertEqual(problem_index.used_ids(notes), {"P9.01", "P9.02"})
            self.assertEqual(problem_index.used_ids(notes, exclude="0923"), {"P9.01"})


@unittest.skipUnless(HAS_WORKBOOK, "workbook 없음")
class TestRealRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.errors = problem_index.index(REPO)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_textbook_row(self):
        row = by_id(self.rows)["P9.01"]
        self.assertEqual(row[1:6], ["장말문제", "9.1.1", "9.1.1 전류원으로서의 캐스코드", "0", "-"])
        self.assertTrue(row[6].startswith("바이폴라 캐스코드"))

    def test_exam_row(self):
        row = by_id(self.rows)["2023-1_기말-Q1"]
        self.assertEqual(row[1:3], ["기출", "ch10,11"])
        self.assertEqual(row[4], "-")

    def test_chapter_filter(self):
        rows, _ = problem_index.index(REPO, chapters={9})
        ids = set(by_id(rows))
        textbook = {i for i in ids if not i[0].isdigit()}
        self.assertTrue(textbook and all(i[1:].startswith("9.") for i in textbook))
        self.assertEqual(len(textbook), 110)
        self.assertNotIn("2023-1_기말-Q1", ids)  # textbook_chapters [10, 11]

    def test_used_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "0909" / ".assets").mkdir(parents=True)
            (Path(tmp) / "0909" / ".assets" / "problems.txt").write_text("P9.01 | x\n", encoding="utf-8")
            rows, _ = problem_index.index(REPO, used_dir=Path(tmp), chapters={9})
        table = by_id(rows)
        self.assertEqual(table["P9.01"][5], "USED")
        self.assertEqual(table["P9.02"][5], "-")

    def test_index_exclude_range_keeps_other_ranges_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0918" / ".assets").mkdir(parents=True)
            (notes / "0918" / ".assets" / "problems.txt").write_text("P9.01 | x\n", encoding="utf-8")
            (notes / "0923" / ".assets").mkdir(parents=True)
            (notes / "0923" / ".assets" / "problems.txt").write_text("P9.02 | x\n", encoding="utf-8")
            rows, _ = problem_index.index(REPO, used_dir=notes, chapters={9}, exclude_range="0923")
        table = by_id(rows)
        self.assertEqual(table["P9.01"][5], "USED")
        self.assertEqual(table["P9.02"][5], "-")

    def test_cli_exclude_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0923" / ".assets").mkdir(parents=True)
            (notes / "0923" / ".assets" / "problems.txt").write_text("P9.01 | x\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(problem_index.main(
                    ["--repo", str(REPO), "--used", str(notes), "--chapters", "9", "--exclude-range", "0923"]), 0)
        lines = {r.split("\t")[0]: r for r in out.getvalue().splitlines()[1:]}
        self.assertEqual(lines["P9.01"].split("\t")[5], "-")

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(problem_index.main(["--repo", str(REPO), "--chapters", "9"]), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], problem_index.HEADER)
        self.assertTrue(all(len(line.split("\t")) == 7 for line in lines))

    def test_bad_md_is_reported_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "workbook").symlink_to(REPO / "workbook", target_is_directory=True)
            bad = repo / "교과서" / "마이크로전자회로" / "ch99" / "예제"
            bad.mkdir(parents=True)
            (bad / "E99.01.md").write_text("no frontmatter\n", encoding="utf-8")
            (repo / "from_the_past" / "md").mkdir(parents=True)
            rows, errors = problem_index.index(repo)
            self.assertEqual(rows, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("E99.01.md", errors[0])
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(problem_index.main(["--repo", str(repo)]), 1)
            self.assertIn("ERROR", err.getvalue())

    def test_problem_without_solution_is_included(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "workbook").symlink_to(REPO / "workbook", target_is_directory=True)
            exam = repo / "from_the_past" / "md" / "2099-1_중간"
            exam.mkdir(parents=True)
            head = ("---\nid: 2099-1_중간-Q{n}\nkind: 기출\nexam: \"2099-1 중간고사\"\nnumber: \"{n}\"\n"
                    "points: 10\nsource: ../../x.pdf\npdf_page: 1\nsource_lang: ko\nfigures: []\n"
                    "textbook_chapters: [9]\ndepends_on: []\nrefs: []\n---\n# 기출 2099-1 중간 {n} — 제목\n\n"
                    "## 조건\n- $R = 1$\n\n## 구할 것\n- (1) $A_v$\n\n## 회로 — 없음 (서술형)\n")
            (exam / "Q1.md").write_text(head.format(n=1), encoding="utf-8")
            (exam / "Q2.md").write_text(head.format(n=2) + "\n## 풀이\n### (1) 이득\n- $A_v = 1$\n### 답\n- (1) $A_v = 1$\n",
                                        encoding="utf-8")
            rows, errors = problem_index.index(repo)
            self.assertEqual(errors, [])
            self.assertEqual([r[0] for r in rows], ["2099-1_중간-Q1", "2099-1_중간-Q2"])

    def test_non_dict_frontmatter_is_reported_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "workbook").symlink_to(REPO / "workbook", target_is_directory=True)
            bad = repo / "교과서" / "마이크로전자회로" / "ch99" / "예제"
            bad.mkdir(parents=True)
            (bad / "E99.02.md").write_text(
                "---\n- id\n- kind\n- number\n---\n# 예제 99.2 — x\n", encoding="utf-8")
            (repo / "from_the_past" / "md").mkdir(parents=True)
            rows, errors = problem_index.index(repo)
            self.assertEqual(rows, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("E99.02.md", errors[0])


class TestJSON(unittest.TestCase):
    def test_new_policy_cli_accepts_unsolved_exam_and_requires_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'workbook').symlink_to(REPO / 'workbook', target_is_directory=True)
            exam = repo / 'from_the_past/md/2099-1_중간'
            exam.mkdir(parents=True)
            (exam / 'exam.yaml').write_text('exam: synthetic fixture\n', encoding='utf-8')
            (exam / 'Q1.md').write_text('---\nid: 2099-1_중간-Q1\nkind: 기출\nnumber: "1"\n'
                'points: 10\nsource: ../../x.pdf\npdf_page: 1\nsource_lang: ko\nfigures: []\n'
                'textbook_chapters: [9]\ndepends_on: []\nrefs: []\n---\n'
                '# 기출 2099-1 중간 1 — 합성 테스트\n\n## 조건\n- $R=1$\n\n'
                '## 구할 것\n- (1) 저항\n\n## 회로 — 없음 (서술형)\n', encoding='utf-8')
            notes = repo / '복습노트'
            notes.mkdir()
            candidates, errors = problem_index.candidate_data(repo, notes, {9}, '1007')
            self.assertEqual(errors, [])
            q = candidates['problems'][0]
            self.assertEqual(q['reference_solution'], 'none')
            snapshot = repo / 'candidates.json'
            snapshot.write_text(json.dumps(candidates), encoding='utf-8')
            m = dict(range='1007', selection_policy='exam-first-v2', problems=[dict(id=q['id'],
                kind='기출', why='합성 테스트', priority='core', learning_goals=['저항'], estimated_minutes=5)])
            (repo / 'manifest.json').write_text(json.dumps(m), encoding='utf-8')
            review = dict(policy='exam-first-v2', catalog_sha256=candidates['catalog_sha256'],
                candidates=[dict(id=q['id'], disposition='selected', scope='in_scope', reason='합성 테스트')],
                coverage=[dict(goal='저항', problem_ids=[q['id']])])
            (repo / 'review.json').write_text(json.dumps(review), encoding='utf-8')
            args = ['--repo', str(repo), '--chapters', '9', '--format', 'json', '--catalog-out', str(repo/'catalog'),
                    '--candidates-input', str(snapshot), '--selection-manifest', str(repo/'manifest.json'),
                    '--selection-review', str(repo/'review.json'), '--selection-out', str(repo/'selection.json')]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(problem_index.main(args), 1)
            self.assertFalse((repo/'selection.json').exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(problem_index.main(args + ['--used', str(notes), '--exclude-range', '1007']), 0)
            recorded = json.loads((repo/'selection.json').read_text(encoding='utf-8'))
            self.assertEqual(recorded['problems'][0]['reference_solution'], 'none')
            self.assertEqual(recorded['workload']['estimated_minutes'], 5)

    def test_new_policy_requires_audit_and_keeps_strict_reuse(self):
        data = dict(catalog_sha256='abc', problems=[dict(id='Q', kind='기출', used=False,
            depends_on=[], subparts=[{'label': '1'}], reference_solution='none')])
        manifest = dict(range='1007', selection_policy='exam-first-v2', problems=[dict(
            id='Q', kind='기출', why='기본형', priority='core', learning_goals=['이득'], estimated_minutes=15)])
        review = dict(policy='exam-first-v2', catalog_sha256='abc', candidates=[dict(
            id='Q', disposition='selected', scope='in_scope', reason='기본형')],
            coverage=[dict(goal='이득', problem_ids=['Q'])])
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data)
        record = problem_index.record_selection(manifest, data, review)
        self.assertEqual(record['schema_version'], 2)
        self.assertEqual(record['problems'][0]['priority'], 'core')
        self.assertEqual(record['problems'][0]['subpart_count'], 1)
        self.assertEqual(record['problems'][0]['reference_solution'], 'none')
        self.assertEqual(record['workload']['estimated_minutes'], 15)
        data['problems'][0]['used'] = True
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data, review)

    def test_previously_used_dependency_is_never_exempt(self):
        data = dict(catalog_sha256='abc', problems=[
            dict(id='A', kind='기출', used=True, depends_on=[]),
            dict(id='B', kind='기출', used=False, depends_on=['A'])])
        m = dict(range='1007', problems=[dict(id='A', kind='기출', why='전제'), dict(id='B', kind='기출', why='응용')])
        with self.assertRaisesRegex(ValueError, '이전 팩'):
            problem_index.record_selection(m, data)
        m['problems'].pop(0)
        with self.assertRaisesRegex(ValueError, '의존'):
            problem_index.record_selection(m, data)

    def test_missing_goals_and_wrong_coverage_fail(self):
        data = dict(catalog_sha256='abc', problems=[dict(id='A', kind='기출', used=False, depends_on=[])])
        m = dict(range='1007', selection_policy='exam-first-v2', problems=[dict(
            id='A', kind='기출', why='전제', priority='core', learning_goals=['이득'], estimated_minutes=10)])
        r = dict(policy='exam-first-v2', catalog_sha256='abc', candidates=[dict(
            id='A', disposition='selected', scope='in_scope', reason='이득')], coverage=[])
        with self.assertRaisesRegex(ValueError, 'coverage'):
            problem_index.record_selection(m, data, r)
        r['coverage'] = [dict(goal='다른 목표', problem_ids=['A'])]
        with self.assertRaisesRegex(ValueError, '불일치'):
            problem_index.record_selection(m, data, r)

    def test_new_policy_requires_reviewing_unselected_exams_and_all_subparts(self):
        data = dict(catalog_sha256='abc', problems=[dict(id='Q', kind='기출', used=False,
            depends_on=[], subparts=[{'label': '1'}])])
        manifest = dict(range='1007', selection_policy='exam-first-v2', problems=[])
        review = dict(policy='exam-first-v2', catalog_sha256='abc', candidates=[], coverage=[])
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data, review)
        review['candidates'] = [dict(id='Q', disposition='deferred', scope='out_of_scope',
                                    reason='주파수 응답 미학습', missing_concepts=['주파수 응답'])]
        result = problem_index.record_selection(manifest, data, review)
        self.assertEqual(result['review']['candidates'][0]['disposition'], 'deferred')
        review['candidates'][0]['scope'] = 'in_scope'
        manifest['problems'] = [dict(id='Q', kind='기출', why='x', priority='core',
            learning_goals=['이득'], estimated_minutes=10)]
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data, review)

    def test_textbook_figure_and_config_changes_invalidate_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'workbook').symlink_to(REPO / 'workbook', target_is_directory=True)
            chapter = Path('교과서/마이크로전자회로/ch09')
            (repo / chapter / '장말문제').mkdir(parents=True)
            (repo / 'from_the_past/md').mkdir(parents=True)
            shutil.copy(REPO / chapter / '장말문제/P9.01.md', repo / chapter / '장말문제/P9.01.md')
            shutil.copytree(REPO / chapter / 'figures', repo / chapter / 'figures')
            before, errors = problem_index.candidate_data(repo)
            self.assertEqual(errors, [])
            q = before['problems'][0]
            for rel in ['fig9-02-a.png', 'figures.yaml']:
                file = repo / chapter / 'figures' / rel
                old = file.read_bytes()
                file.write_bytes(old + b'\n')
                after, _ = problem_index.candidate_data(repo)
                self.assertNotEqual(q['content_sha256'], after['problems'][0]['content_sha256'], rel)
                file.write_bytes(old)

    def test_candidates_have_full_exam_scope_and_live_used_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / '1007/.assets').mkdir(parents=True)
            (notes / '1007/.assets/problems.txt').write_text('2023-1_중간-Q4 | x\n')
            data, errors = problem_index.candidate_data(REPO, notes, {10}, '1007')
            self.assertEqual(errors, [])
            q = {p['id']: p for p in data['problems']}['2023-1_중간-Q4']
            self.assertFalse(q['used'])
            self.assertEqual(q['adoption_unit'], 'whole')
            self.assertEqual(len(q['subparts']), 3)
            self.assertIn('selection', q)
            self.assertIn('depends_on', q)
            other, _ = problem_index.candidate_data(REPO, notes, {10})
            self.assertTrue({p['id']: p for p in other['problems']}[q['id']]['used'])

    def test_json_cli_writes_catalog_only_to_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'catalog'
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                result = problem_index.main(['--repo', str(REPO), '--chapters', '10',
                                             '--format', 'json', '--catalog-out', str(out)])
            self.assertEqual(result, 0)
            data = json.loads(stdout.getvalue())
            index = json.loads((out / 'index.json').read_text())
            self.assertEqual(data['catalog_sha256'], index['catalog_sha256'])
            self.assertEqual(data['catalog_root'], str(out))
            for q in data['problems']:
                if q['kind'] == '기출':
                    self.assertTrue((out / q['detail_path']).is_file())

    def test_selection_record_rejects_unknown_used_partial_and_missing_dependency(self):
        data = dict(schema_version=1, catalog_sha256='abc', problems=[
            dict(id='2023-1_중간-Q4', kind='기출', used=False, depends_on=[],
                 adoption_unit='whole', content_sha256='123', subparts=[{'label': '1'}])])
        manifest = dict(range='1007', problems=[dict(id='2023-1_중간-Q4', kind='기출', why='CMRR')])
        record = problem_index.record_selection(manifest, data)
        self.assertEqual(record['problems'][0]['adoption_unit'], 'whole')
        self.assertEqual(record['catalog_sha256'], 'abc')
        manifest['problems'][0]['subparts'] = ['1']
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data)
        manifest['problems'][0].pop('subparts')
        for change in [dict(used=True), dict(depends_on=['P9.01'])]:
            q = {**data['problems'][0], **change}
            with self.assertRaises(ValueError):
                problem_index.record_selection(manifest, {**data, 'problems': [q]})
        manifest['problems'][0]['id'] = 'unknown'
        with self.assertRaises(ValueError):
            problem_index.record_selection(manifest, data)

    def test_json_cli_records_manifest_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps(dict(range='1007', problems=[
                dict(id='2023-1_중간-Q4', kind='기출', why='CMRR'),
                dict(id='P9.01', kind='장말문제', why='캐스코드')]), ensure_ascii=False))
            data, errors = problem_index.candidate_data(REPO)
            self.assertEqual(errors, [])
            snapshot = root / 'candidates.json'
            snapshot.write_text(json.dumps(data, ensure_ascii=False))
            with contextlib.redirect_stdout(io.StringIO()):
                code = problem_index.main(['--repo', str(REPO), '--format', 'json',
                    '--catalog-out', str(root / 'catalog'), '--selection-manifest', str(manifest),
                    '--candidates-input', str(snapshot),
                    '--selection-out', str(root / 'selection.json')])
            self.assertEqual(code, 0)
            record = json.loads((root / 'selection.json').read_text())
            self.assertEqual([p['id'] for p in record['problems']], ['2023-1_중간-Q4', 'P9.01'])

            data['catalog_sha256'] = 'stale'
            snapshot.write_text(json.dumps(data))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                code = problem_index.main(['--repo', str(REPO), '--format', 'json',
                    '--catalog-out', str(root / 'catalog'), '--selection-manifest', str(manifest),
                    '--candidates-input', str(snapshot), '--selection-out', str(root / 'stale-selection.json')])
            self.assertEqual(code, 1)
            self.assertIn('다시 검토', err.getvalue())
            self.assertFalse((root / 'stale-selection.json').exists())


if __name__ == "__main__":
    unittest.main()
