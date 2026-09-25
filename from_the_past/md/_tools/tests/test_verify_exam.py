import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_exam import crop_all  # noqa: E402
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402
from make_exam_index import build_exam_index  # noqa: E402
from verify_exam import main, verify  # noqa: E402

FIGURES_YAML = """dpi: 72
figures:
  "Q2": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 100, 50]}
"""
EXAM_YAML = """exam: "2021-1 중간고사"
header: "Closed book"
sources:
  - ../../src/a.pdf
"""


def make_full_exam(root: Path) -> Path:
    exam = make_exam(root, {"Q1.md": VALID_Q1, "Q2.md": VALID_Q2, "exam.yaml": EXAM_YAML}, with_png=False)
    (exam / "figures" / "figures.yaml").write_text(FIGURES_YAML, encoding="utf-8")
    crop_all(exam)
    (exam / "README.md").write_text(build_exam_index(exam), encoding="utf-8")
    return exam


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.exam = make_full_exam(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def assertHas(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), errors)

    def rebuild_readme(self):
        (self.exam / "README.md").write_text(build_exam_index(self.exam), encoding="utf-8")

    def test_valid_exam_passes(self):
        self.assertEqual(verify(self.exam, recrop=True), [])

    def test_empty_exam_is_error(self):
        empty = self.root / "md" / "2023-1_기말"
        empty.mkdir(parents=True)
        self.assertEqual(verify(empty), ["문제 md가 없음"])

    def test_missing_number(self):
        (self.exam / "Q1.md").unlink()
        self.rebuild_readme()
        self.assertHas(verify(self.exam), "번호가 빠짐: Q1")

    def test_stray_md_is_error(self):
        (self.exam / "Q2 copy.md").write_text(VALID_Q2, encoding="utf-8")
        self.assertHas(verify(self.exam), "알 수 없는 md 파일: Q2 copy.md")

    def test_unused_yaml_figure(self):
        (self.exam / "figures" / "figures.yaml").write_text(
            FIGURES_YAML + '  "Q3": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n', encoding="utf-8")
        crop_all(self.exam)
        self.assertHas(verify(self.exam), "md가 쓰지 않는 그림: Q3")

    def test_extra_png(self):
        (self.exam / "figures" / "fig-Q9.png").write_bytes(b"\x89PNG")
        self.assertHas(verify(self.exam), "figures.yaml에 없는 PNG: fig-Q9.png")

    def test_image_link_missing(self):
        q2 = (self.exam / "Q2.md").read_text(encoding="utf-8").replace("![Q2](figures/fig-Q2.png)\n", "")
        (self.exam / "Q2.md").write_text(q2, encoding="utf-8")
        self.assertHas(verify(self.exam), "그림 Q2 이미지 링크 없음")

    def test_stale_readme(self):
        q1 = (self.exam / "Q1.md").read_text(encoding="utf-8").replace("— 서술형", "— 바뀐 제목")
        (self.exam / "Q1.md").write_text(q1, encoding="utf-8")
        self.assertHas(verify(self.exam), "README.md가 최신이 아님")

    def test_answer_section_rejected(self):
        with (self.exam / "Q1.md").open("a", encoding="utf-8") as f:
            f.write("\n## 답 (검증용)\n- 없음\n")
        self.assertHas(verify(self.exam), "'## 답' 절이 있음")

    def test_exam_yaml_mismatch(self):
        (self.exam / "exam.yaml").write_text(EXAM_YAML.replace("2021-1 중간고사", "2021-2 중간고사"), encoding="utf-8")
        self.assertHas(verify(self.exam), "exam.yaml")

    def test_exam_yaml_source_missing(self):
        (self.exam / "exam.yaml").write_text(EXAM_YAML.replace("a.pdf", "none.pdf"), encoding="utf-8")
        self.assertHas(verify(self.exam), "원본 없음: ../../src/none.pdf")

    def test_recrop_detects_changed_png(self):
        (self.exam / "figures" / "figures.yaml").write_text(FIGURES_YAML.replace("100, 50", "90, 50"), encoding="utf-8")
        self.assertHas(verify(self.exam, recrop=True), "다시 자른 결과와 다름")

    def test_recrop_missing_pdf_is_error(self):
        (self.root / "src" / "a.pdf").unlink()
        self.assertHas(verify(self.exam, recrop=True), "다시 자르기 실패")

    def test_broken_frontmatter_reported_not_raised(self):
        (self.exam / "Q1.md").write_text("frontmatter 없음\n", encoding="utf-8")
        self.assertHas(verify(self.exam), "Q1.md: frontmatter 읽기 실패")


class MainTest(unittest.TestCase):
    def test_ok_and_usage(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_full_exam(Path(t))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["verify_exam.py", str(exam), "--recrop"]), 0)
            self.assertIn("오류 0개", out.getvalue())
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["verify_exam.py"]), 2)


if __name__ == "__main__":
    unittest.main()
