import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_pages import SourceError, main, pending, render, source_pdf  # noqa: E402


def write_md(path, pid, kind, page, original=False, extra=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# 장말문제 9.1 — 제목\n\n" + ("## 원문\nText.\n\n" if original else "") + "## 조건\n- a\n"
    path.write_text(f"---\nid: {pid}\nkind: {kind}\npdf_page: {page}\n{extra}---\n{body}", encoding="utf-8")
    return path


def write_pdf(path, pages=3, text_pages=(1, 2)):
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page()
        if i in text_pages:
            page.insert_text((72, 72), f"Problem statement on page {i}, long enough.")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()
    return path


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["source_pages.py"] + argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ch = self.root / "ch09"
        self.out = self.root / "out"

    def tearDown(self):
        self._tmp.cleanup()


class TestPending(Base):
    def test_sorted_by_page_then_id_and_skips_done(self):
        write_md(self.ch / "장말문제/P9.02.md", "P9.02", "장말문제", 1)
        write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", 1, original=True)
        write_md(self.ch / "연습문제/X9.01.md", "X9.01", "연습문제", 2)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2)
        (self.ch / "README.md").write_text("# 9장\n", encoding="utf-8")
        self.assertEqual([p.name for p in pending(self.ch)], ["P9.02.md", "E9.01.md", "X9.01.md"])

    def test_missing_folder_raises(self):
        with self.assertRaises(SourceError):
            pending(self.root / "ch99")

    def test_folder_without_problem_md_raises(self):
        (self.ch / "figures").mkdir(parents=True)
        (self.ch / "README.md").write_text("# 9장\n", encoding="utf-8")
        with self.assertRaises(SourceError):
            pending(self.ch)

    def test_main_missing_exit_code(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2)
        code, out, err = run(["missing", str(self.ch)])
        self.assertEqual(code, 1)
        self.assertIn("E9.01.md", out)
        self.assertIn("원문 없음: 1개", err)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2, original=True)
        self.assertEqual(run(["missing", str(self.ch)])[0], 0)

    def test_main_next_size(self):
        for i in range(1, 4):
            write_md(self.ch / f"장말문제/P9.0{i}.md", f"P9.0{i}", "장말문제", i)
        code, out, _ = run(["next", str(self.ch), "--size", "2"])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["P9.01.md", "P9.02.md"])


class TestRender(Base):
    def test_textbook_page_and_next(self):
        write_pdf(self.root / "9장.pdf")
        md = write_md(self.ch / "장말문제/P9.18.md", "P9.18", "장말문제", 2)
        self.assertEqual(source_pdf(md, {"kind": "장말문제"}), self.root / "9장.pdf")
        names = sorted(p.name for p in render([md], self.out, dpi=50))
        self.assertEqual(names, ["P9.18-p2.png", "P9.18-p2.txt", "P9.18-p3.png"])
        self.assertIn("page 2", (self.out / "P9.18-p2.txt").read_text(encoding="utf-8"))

    def test_last_page_has_no_next(self):
        write_pdf(self.root / "9장.pdf")
        md = write_md(self.ch / "장말문제/P9.68.md", "P9.68", "장말문제", 3)
        self.assertEqual([p.name for p in render([md], self.out, dpi=50)], ["P9.68-p3.png"])

    def test_exam_source_relative_to_md(self):
        write_pdf(self.root / "src/exam.pdf", pages=1, text_pages=(1,))
        md = write_md(self.root / "md/2023-1_기말/Q1.md", "2023-1_기말-Q1", "기출", 1,
                      extra='source: "../../src/exam.pdf"\n')
        names = sorted(p.name for p in render([md], self.out, dpi=50))
        self.assertEqual(names, ["2023-1_기말-Q1-p1.png", "2023-1_기말-Q1-p1.txt"])

    def test_missing_pdf_is_error_line(self):
        md = write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1)
        code, _, err = run(["render", str(md), "--out", str(self.out)])
        self.assertEqual(code, 1)
        self.assertIn("ERROR 원본 PDF 없음", err)

    def test_page_out_of_range_is_error(self):
        write_pdf(self.root / "9장.pdf")
        for page in (0, 4):
            with self.subTest(page=page):
                md = write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", page)
                code, _, err = run(["render", str(md), "--out", str(self.out)])
                self.assertEqual(code, 1)
                self.assertIn("ERROR pdf_page", err)

    def test_bad_page_value_and_corrupt_pdf_are_error_lines(self):
        md = write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", "abc")
        write_pdf(self.root / "9장.pdf")
        code, _, err = run(["render", str(md), "--out", str(self.out)])
        self.assertEqual((code, err.startswith("ERROR ")), (1, True), err)
        (self.root / "9장.pdf").write_bytes(b"not a pdf")
        md = write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", 1)
        code, _, err = run(["render", str(md), "--out", str(self.out)])
        self.assertEqual((code, err.startswith("ERROR ")), (1, True), err)


if __name__ == "__main__":
    unittest.main()
