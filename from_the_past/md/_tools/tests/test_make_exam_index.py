import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402
from make_exam_index import build_exam_index, main  # noqa: E402

EXAM_YAML = """exam: "2021-1 중간고사"
header: "Closed book, 풀이과정 필수"
sources:
  - ../../src/a.pdf
aux_sources:
  - ../../src/b.pdf
notes:
  - "스캔 답안지라 손글씨가 겹침"
"""

Q10 = VALID_Q2.replace("2021-1_중간-Q2", "2021-1_중간-Q10").replace('number: "2"', 'number: "10"') \
    .replace("textbook_chapters: [9, 10]", "textbook_chapters: [99]") \
    .replace("depends_on: []", "depends_on: [2021-1_중간-Q2]") \
    .replace("# 기출 2021-1 중간 2 — 캐스코드 출력 저항", "# 기출 2021-1 중간 10 — 열 번째 | 문제")


class BuildExamIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.exam = make_exam(Path(self.tmp.name), {
            "Q1.md": VALID_Q1, "Q2.md": VALID_Q2, "Q10.md": Q10, "exam.yaml": EXAM_YAML})
        self.text = build_exam_index(self.exam)

    def tearDown(self):
        self.tmp.cleanup()

    def test_header(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "# 2021-1 중간고사 — 문제 인덱스")
        self.assertIn("- 시험지 머리: Closed book, 풀이과정 필수", lines)
        self.assertIn("- 원본: `a.pdf`", lines)
        self.assertIn("- 보조 원본: `b.pdf`", lines)
        self.assertIn("- 문제 3개, 배점 합계 60점", lines)
        self.assertIn("- 스캔 답안지라 손글씨가 겹침", lines)

    def test_rows_numeric_order(self):
        rows = [l for l in self.text.splitlines() if l.startswith("| [Q")]
        self.assertEqual([r.split("]")[0] for r in rows], ["| [Q1", "| [Q2", "| [Q10"])

    def test_row_content(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q2]"))
        self.assertEqual(
            row,
            "| [Q2](Q2.md) | 캐스코드 출력 저항 | 20 | a.pdf | 1 | Q2(a) | "
            "[9장](../../../교과서/마이크로전자회로/ch09/README.md), "
            "[10장](../../../교과서/마이크로전자회로/ch10/README.md) | — |")

    def test_unknown_chapter_plain_and_escape_and_deps(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q10]"))
        self.assertIn("열 번째 \\| 문제", row)
        self.assertIn("| 99장 |", row)
        self.assertTrue(row.endswith("| [Q2](Q2.md) |"), row)

    def test_no_circuit_figures_dash(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q1]"))
        self.assertIn("| — |", row)


class MainTest(unittest.TestCase):
    def test_writes_readme(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1, "exam.yaml": EXAM_YAML})
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 0)
            self.assertEqual((exam / "README.md").read_text(encoding="utf-8"), build_exam_index(exam))

    def test_broken_frontmatter_is_error_without_writing(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": "frontmatter 없음\n", "exam.yaml": EXAM_YAML})
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 1)
            self.assertIn("ERROR", err.getvalue())
            self.assertIn("check_exam.py", err.getvalue())
            self.assertFalse((exam / "README.md").exists())

    def test_non_int_points_keeps_old_readme(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1.replace("points: 20", "points: 스무"),
                                       "exam.yaml": EXAM_YAML, "README.md": "기존\n"})
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 1)
            self.assertEqual((exam / "README.md").read_text(encoding="utf-8"), "기존\n")

    def test_missing_exam_yaml(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1})
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 2)


if __name__ == "__main__":
    unittest.main()
