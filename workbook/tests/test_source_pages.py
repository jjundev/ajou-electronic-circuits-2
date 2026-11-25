import io
import sys
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_pages import SourceError, main, pending, read_ledger, render, source_pdf  # noqa: E402


def write_md(path, pid, kind, page, original=False, extra="", tail=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# 장말문제 9.1 — 제목\n\n" + ("## 원문\nText.\n\n" if original else "") + "## 조건\n- a\n" + tail
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


class TestLedger(Base):
    def ledger(self, text):
        path = self.root / "hints-ledger.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_pending_skips_judged_ids(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        ledger = read_ledger(self.ledger("# 힌트 판정 원장 — ch09\n\n- E9.01 | 없음 | 대입만\n"))
        self.assertEqual(ledger, {"E9.01": 0})
        self.assertEqual([p.name for p in pending(self.ch, ledger)], ["E9.02.md"])

    def test_missing_ledger_file_is_empty(self):
        self.assertEqual(read_ledger(self.root / "none.md"), {})

    def test_bad_line_raises(self):
        with self.assertRaises(SourceError):
            read_ledger(self.ledger("- E9.01 | 아마 | 모름\n"))

    def test_malformed_list_line_raises(self):
        for line in ("-E9.01 | 없음 | x", "  - E9.01 | 없음 | x", "* E9.01 | 없음 | x", "E9.01 | 없음 | x"):
            with self.subTest(line=line), self.assertRaises(SourceError):
                read_ledger(self.ledger(f"# 원장\n\n{line}\n"))

    def test_duplicate_id_raises(self):
        with self.assertRaises(SourceError):
            read_ledger(self.ledger("- E9.01 | 없음 | a\n- E9.01 | 힌트 1 | b\n"))

    def test_main_missing_reports_mismatch(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True,
                 tail="\n## 힌트\n### 반회로로 본다\n- 대칭\n")
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        path = self.ledger("- E9.01 | 힌트 1 | 대칭\n- E9.02 | 힌트 1 | 절을 빠뜨림\n")
        code, out, err = run(["missing", str(self.ch), "--ledger", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("MISMATCH E9.02: 원장 1개, md 0개", out)
        self.assertNotIn("E9.01", out)
        self.assertIn("판정 없음: 0개", err)

    def test_main_next_with_ledger(self):
        for i in range(1, 4):
            write_md(self.ch / f"장말문제/P9.0{i}.md", f"P9.0{i}", "장말문제", i, original=True)
        path = self.ledger("- P9.01 | 없음 | 대입만\n")
        code, out, _ = run(["next", str(self.ch), "--ledger", str(path), "--size", "5"])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["P9.02.md", "P9.03.md"])


class TestSection(Base):
    SOL = "\n## 풀이\n### 소신호 파라미터\n- $g_m = 1$\n### 답\n- 1\n"

    def test_pending_section_skips_solved(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True, tail=self.SOL)
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        self.assertEqual([p.name for p in pending(self.ch, section="풀이")], ["E9.02.md"])
        self.assertEqual(pending(self.ch), [])

    def test_pending_on_kind_subfolder(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", 1, original=True)
        self.assertEqual([p.name for p in pending(self.ch / "예제", section="풀이")], ["E9.01.md"])

    def test_main_missing_section(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        code, out, err = run(["missing", str(self.ch), "--section", "풀이"])
        self.assertEqual(code, 1)
        self.assertIn("E9.01.md", out)
        self.assertIn("풀이 없음: 1개", err)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True, tail=self.SOL)
        self.assertEqual(run(["missing", str(self.ch), "--section", "풀이"])[0], 0)

    def test_section_argument_nfd_accepted(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        code, out, _ = run(["next", str(self.ch), "--section", unicodedata.normalize("NFD", "풀이")])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["E9.01.md"])

    def test_section_with_ledger_is_error(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        ledger = self.root / "hints-ledger.md"
        ledger.write_text("- E9.01 | 없음 | 대입만\n", encoding="utf-8")
        code, _, err = run(["next", str(self.ch), "--section", "풀이", "--ledger", str(ledger)])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)
        self.assertIn("--section 풀이", err)


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
