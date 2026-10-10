from pathlib import Path
import shutil
import tempfile
import unittest

from _util import MINI_RUN

import assemble
import check_html
import insert_why


def frag() -> str:
    return (MINI_RUN / "sections" / "why.html").read_text(encoding="utf-8")


def bare_note() -> str:
    """why 섹션이 없던 시절의 노트: 픽스처를 조립한 뒤 why 섹션과 목차 링크를 지운다."""
    tmp = Path(tempfile.mkdtemp())
    try:
        html = assemble.assemble(MINI_RUN, tmp).read_text(encoding="utf-8")
    finally:
        shutil.rmtree(tmp)
    start = html.index('<section id="why">')
    end = html.index('<section id="s1">')
    return (html[:start] + html[end:]).replace('<a href="#why">왜 쓸까</a>', "", 1)


class TestInsertWhy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_bare_note_has_no_why(self):
        self.assertNotIn('id="why"', bare_note())
        self.assertNotIn('href="#why"', bare_note())

    def test_inserts_section_before_first_section_and_toc_first(self):
        out = insert_why.insert_why(bare_note(), frag())
        self.assertLess(out.index('<section id="why"><h2>들어가며: 왜 이런 회로를 쓸까</h2>'), out.index('<section id="s1">'))
        self.assertIn('<nav class="toc" aria-label="목차"><a href="#why">왜 쓸까</a><a href="#s1">', out)

    def test_matches_assembled_note(self):
        tmp = self.tmp / "out"
        full = assemble.assemble(MINI_RUN, tmp).read_text(encoding="utf-8")
        self.assertEqual(insert_why.insert_why(bare_note(), frag()), full)

    def test_idempotent(self):
        once = insert_why.insert_why(bare_note(), frag())
        self.assertEqual(insert_why.insert_why(once, frag()), once)
        self.assertEqual(once.count('id="why"'), 1)
        self.assertEqual(once.count('href="#why"'), 1)

    def test_replaces_existing_why(self):
        once = insert_why.insert_why(bare_note(), frag())
        out = insert_why.insert_why(once, frag().replace("대푯값", "대표값X"))
        self.assertIn("대표값X", out)
        self.assertEqual(out.count('<section id="why">'), 1)

    def test_rejects_bad_fragment(self):
        bad = {"section": frag().replace("<h3>", "<section><h3>", 1),
               "h2": frag().replace("<h3>", "<h2>x</h2><h3>", 1),
               "script": frag() + "<script>1</script>",
               "no-article": frag().replace('id="why-circuit"', 'id="other"'),
               "no-sum": frag().replace('class="sum"', 'class="summary"'),
               "no-formal": frag().replace("layer formal", "layer other")}
        for name, f in bad.items():
            with self.subTest(name=name), self.assertRaises(insert_why.InsertError):
                insert_why.insert_why(bare_note(), f)

    def test_rejects_note_without_toc_or_section(self):
        for broken in (bare_note().replace('<nav class="toc" aria-label="목차">', "<nav>"),
                       bare_note().replace("<section id=", "<div id=")):
            with self.subTest(), self.assertRaises(insert_why.InsertError):
                insert_why.insert_why(broken, frag())

    def test_cli_rewrites_note(self):
        note = self.tmp / "n.html"
        note.write_text(bare_note(), encoding="utf-8")
        fragment = self.tmp / "why.html"
        fragment.write_text(frag(), encoding="utf-8")
        self.assertEqual(insert_why.main(["--note", str(note), "--fragment", str(fragment)]), 0)
        self.assertIn('<section id="why">', note.read_text(encoding="utf-8"))

    def test_cli_leaves_file_untouched_on_error(self):
        note = self.tmp / "n.html"
        note.write_text(bare_note(), encoding="utf-8")
        bad = self.tmp / "f.html"
        bad.write_text("<p>x</p>", encoding="utf-8")
        before = note.read_bytes()
        self.assertEqual(insert_why.main(["--note", str(note), "--fragment", str(bad)]), 1)
        self.assertEqual(note.read_bytes(), before)

    def test_result_passes_check_html(self):
        for pdf in ("문제", "답안"):  # 노트가 링크하는 복습문제 PDF를 만들어 broken-link를 피한다
            (self.tmp / f"복습문제_0101-0102_Mini_Test-{pdf}.pdf").write_bytes(b"%PDF")
        note = self.tmp / "n.html"
        note.write_text(insert_why.insert_why(bare_note(), frag()), encoding="utf-8")
        self.assertEqual(check_html.check_file(note), [])


if __name__ == "__main__":
    unittest.main()
