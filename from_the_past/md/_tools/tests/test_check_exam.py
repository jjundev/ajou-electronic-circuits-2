import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_exam import check_file, exam_title, main, md_files  # noqa: E402
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402


class ExamTitleTest(unittest.TestCase):
    def test_title(self):
        self.assertEqual(exam_title("2023-1_기말"), "2023-1 기말고사")

    def test_nfd_name(self):
        import unicodedata
        self.assertEqual(exam_title(unicodedata.normalize("NFD", "2023-1_기말")), "2023-1 기말고사")

    def test_bad_name(self):
        with self.assertRaises(ValueError):
            exam_title("2023_기말")

    def test_section_suffix(self):
        self.assertEqual(exam_title("2017-1_중간_D반"), "2017-1 중간고사 (D반)")
        self.assertEqual(exam_title("2017-1_중간_C030"), "2017-1 중간고사 (C030)")
        with self.assertRaises(ValueError):
            exam_title("2017-1_중간_")


class CheckFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, text, name="Q2.md"):
        exam = make_exam(self.root, {name: text})
        return check_file(exam / name, exam)

    def assertError(self, text, fragment, name="Q2.md"):
        errors, _ = self.check(text, name)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid(self):
        self.assertEqual(self.check(VALID_Q2), ([], []))

    def test_valid_no_circuit(self):
        self.assertEqual(self.check(VALID_Q1, "Q1.md"), ([], []))

    def test_id_other_exam(self):
        self.assertError(VALID_Q2.replace("id: 2021-1_중간-Q2", "id: 2023-1_중간-Q2"), "폴더")

    def test_filename_mismatch(self):
        self.assertError(VALID_Q2, "파일명", name="Q3.md")

    def test_number_unquoted(self):
        self.assertError(VALID_Q2.replace('number: "2"', "number: 2"), "따옴표")

    def test_number_mismatch(self):
        self.assertError(VALID_Q2.replace('number: "2"', 'number: "3"'), "number")

    def test_kind(self):
        self.assertError(VALID_Q2.replace("kind: 기출", "kind: 예제"), "kind")

    def test_exam_title_mismatch(self):
        self.assertError(VALID_Q2.replace('exam: "2021-1 중간고사"', 'exam: "2021 중간"'), "exam")

    def test_points_not_int(self):
        self.assertError(VALID_Q2.replace("points: 20", 'points: "20점"'), "points")

    def test_source_missing(self):
        self.assertError(VALID_Q2.replace("../../src/a.pdf", "../../src/none.pdf"), "source PDF 없음")

    def test_pdf_page_out_of_range(self):
        self.assertError(VALID_Q2.replace("pdf_page: 1", "pdf_page: 2"), "범위 밖")

    def test_textbook_chapters_not_ints(self):
        self.assertError(VALID_Q2.replace("textbook_chapters: [9, 10]", 'textbook_chapters: ["9장"]'), "textbook_chapters")

    def test_answer_role_rejected(self):
        self.assertError(VALID_Q2.replace("role: problem", "role: answer"), "role")

    def test_figure_png_missing(self):
        exam = make_exam(self.root, {"Q2.md": VALID_Q2}, with_png=False)
        errors, _ = check_file(exam / "Q2.md", exam)
        self.assertIn("그림 파일 없음: figures/fig-Q2.png", errors)

    def test_depends_on_other_exam(self):
        self.assertError(VALID_Q2.replace("depends_on: []", "depends_on: [2023-1_중간-Q1]"), "다른 시험")

    def test_depends_on_missing_file_warns(self):
        errors, warnings = self.check(VALID_Q2.replace("depends_on: []", "depends_on: [2021-1_중간-Q1]"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["depends_on 2021-1_중간-Q1 파일이 아직 없음"])

    def test_answer_section_rejected(self):
        self.assertError(VALID_Q2 + "\n## 답 (검증용)\n- 1 kΩ\n", "기출에는 답 절을 두지 않음")

    def test_solution_section_allowed(self):
        solution = "\n## 풀이\n### (1) 소신호 파라미터\n- $g_m = 1\\ \\text{mS}$\n### 답\n- (1) $1\\ \\text{k}\\Omega$\n"
        self.assertEqual(self.check(VALID_Q2 + solution), ([], []))

    def test_body_checked(self):
        self.assertError(VALID_Q2.replace("- 배치: M1 하나\n", ""), "'- 배치:' bullet 없음")

    def test_missing_key(self):
        self.assertError(VALID_Q2.replace("points: 20\n", ""), "키 누락: points")

    def test_nfd_exam_dir(self):
        import unicodedata
        exam = make_exam(self.root, {"Q2.md": VALID_Q2})
        nfd = Path(unicodedata.normalize("NFD", str(exam)))
        self.assertEqual(check_file(nfd / "Q2.md", nfd), ([], []))


class MdFilesTest(unittest.TestCase):
    def test_md_files_numeric_order(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q10.md": "", "Q2.md": "", "README.md": "", "Q2 copy.md": ""})
            self.assertEqual([p.name for p in md_files(exam)], ["Q2.md", "Q10.md"])


class MainTest(unittest.TestCase):
    def run_main(self, exam):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["check_exam.py", str(exam)])
        return code, out.getvalue()

    def test_ok(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1, "Q2.md": VALID_Q2})
            code, out = self.run_main(exam)
        self.assertEqual(code, 0)
        self.assertIn("2개 파일, 오류 0개", out)

    def test_error(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q2.md": VALID_Q2.replace("kind: 기출", "kind: 예제")})
            code, out = self.run_main(exam)
        self.assertEqual(code, 1)

    def test_stray_md_warns(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q2.md": VALID_Q2, "Q2 copy.md": VALID_Q2, "README.md": ""})
            code, out = self.run_main(exam)
        self.assertEqual(code, 0)
        self.assertIn("알 수 없는 md 파일: Q2 copy.md", out)
        self.assertNotIn("README.md", out)
        self.assertIn("1개 파일, 오류 0개", out)

    def test_bad_folder_name(self):
        with tempfile.TemporaryDirectory() as t:
            bad = Path(t) / "midterm"
            bad.mkdir()
            code, _ = self.run_main(bad)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
