import contextlib
import io
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


if __name__ == "__main__":
    unittest.main()
