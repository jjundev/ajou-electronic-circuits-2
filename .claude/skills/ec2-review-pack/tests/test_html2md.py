from pathlib import Path
import shutil
import tempfile
import unicodedata
import unittest
import xml.dom.minidom

from _util import MINI_RUN

import assemble
import html2md
import manifest


def page(body):
    return f'<html><body><main><div class="hero"><h1>t</h1></div>{body}</main></body></html>'


def small_note(directory, body, nfd=False):
    name = "정리노트_0101_X.html"
    note = Path(directory) / (unicodedata.normalize("NFD", name) if nfd else name)
    note.write_text(page(body), encoding="utf-8")
    return note


class TestHtml2Md(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.note = assemble.assemble(MINI_RUN, self.tmp)
        m = manifest.load(MINI_RUN / "manifest.json")
        for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
            (self.tmp / name).write_bytes(b"%PDF-1.4\n")
        self.note_md, self.figs = html2md.convert_note(self.note)
        self.md = Path(self.note_md).read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_output_and_check_pass(self):
        self.assertEqual(Path(self.note_md).name, "정리노트_0101-0102_Mini_Test.md")
        self.assertEqual(html2md.check_md(self.note, self.note_md), [])

    def test_pdf_links_kept_as_pdf(self):
        self.assertIn("(복습문제_0101-0102_Mini_Test-문제.pdf)", self.md)
        self.assertIn("(복습문제_0101-0102_Mini_Test-답안.pdf)", self.md)

    def test_missing_pdf_is_reported(self):
        (self.tmp / "복습문제_0101-0102_Mini_Test-답안.pdf").unlink()
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(problems, ["링크 파일 없음: 복습문제_0101-0102_Mini_Test-답안.pdf"])

    def test_page_summary_rendered(self):
        self.assertIn("**페이지 요약**", self.md)
        self.assertIn("*핵심 식*", self.md)
        self.assertIn("- **분산(variance)** — 평균과의 차이를 제곱해 평균낸 값", self.md)

    def test_widget_static_becomes_figure_and_table(self):
        self.assertEqual(self.figs, 1)
        self.assertTrue((self.tmp / "figures_0101-0102" / "widget-mean-static.svg").exists())
        self.assertIn('<a id="widget-mean"></a>', self.md)
        self.assertIn("![평균 1.5 막대](figures_0101-0102/widget-mean-static.svg)", self.md)
        self.assertIn("| 1, 2 | $\\frac{3}{2}$ |", self.md)

    def test_reconversion_removes_orphan_svgs_only(self):
        fig = self.tmp / "figures_0101-0102"
        (fig / "old-orphan.svg").write_text("<svg/>", encoding="utf-8")
        (fig / "keep.txt").write_text("x", encoding="utf-8")
        (self.tmp / "outside.svg").write_text("<svg/>", encoding="utf-8")
        _, figs = html2md.convert_note(self.note)
        self.assertEqual(figs, 1)
        self.assertEqual(sorted(p.name for p in fig.iterdir()), ["keep.txt", "widget-mean-static.svg"])
        self.assertTrue((self.tmp / "outside.svg").exists())

    def test_table_math_pipes(self):
        ctx = html2md.Ctx([], str(self.tmp), "figures_x")
        b = html2md.Builder()
        b.feed(r"<table><tr><th>a</th></tr><tr><td>$\|x\|$ | $|y|$</td></tr></table>")
        table = next(b.root.find_all(lambda n: n.tag == "table"))
        self.assertEqual(html2md.render_table(table, ctx)[2], r"| $\Vert x\Vert $ \| $\vert y\vert $ |")

    def test_check_md_detects_missing_math(self):
        Path(self.note_md).write_text(self.md.replace(r"\bar{x} = ", ""), encoding="utf-8")
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("수식 누락"))

    def test_bad_filename_rejected(self):
        for bad in ("note.html", "복습문제_0101_X.html"):
            with self.subTest(bad=bad):
                path = self.tmp / bad
                shutil.copyfile(self.note, path)
                with self.assertRaises(ValueError):
                    html2md.convert_note(path)

    def test_svg_export_keeps_viewbox_case_and_size(self):
        ctx = html2md.Ctx([], str(self.tmp), "f")
        b = html2md.Builder()
        b.feed('<svg id="t" viewBox="0 0 720 400" width="100%" preserveAspectRatio="xMidYMid meet">'
               '<defs><marker id="m" markerWidth="6" markerHeight="6" refX="3" refY="3"/></defs></svg>')
        svg = next(b.root.find_all(lambda n: n.tag == "svg"))
        html2md.export_svg(svg, ctx)
        root = xml.dom.minidom.parse(str(self.tmp / "t.svg")).documentElement
        self.assertEqual(root.getAttribute("viewBox"), "0 0 720 400")
        self.assertEqual((root.getAttribute("width"), root.getAttribute("height")), ("720", "400"))
        marker = root.getElementsByTagName("marker")[0]
        self.assertEqual((marker.getAttribute("refX"), marker.getAttribute("markerWidth")), ("3", "6"))

    def test_unnamed_and_duplicate_figures_are_distinct_files(self):
        d = self.tmp / "p"
        d.mkdir()
        fig = '<figure><svg viewBox="0 0 10 10"><circle r="3"/></svg></figure>'
        dup = '<figure><svg id="same" viewBox="0 0 10 10"><rect width="1" height="1"/></svg></figure>'
        note = small_note(d, f'<section id="s"><h2>A</h2>{fig}{dup}{fig}{dup}</section>')
        note_md, figs = html2md.convert_note(note)
        self.assertEqual(figs, 4)
        self.assertEqual(sorted(x.name for x in (d / "figures_0101").iterdir()),
                         ["note-fig-1.svg", "note-fig-2.svg", "same-2.svg", "same.svg"])
        self.assertEqual(html2md.check_md(note, note_md), [])

    def test_check_md_detects_deleted_short_math(self):
        d = self.tmp / "m"
        d.mkdir()
        note = small_note(d, r'<section id="s"><h2>A</h2><p>Let $a$ be a value, $\alpha$ and $\alpha$.</p></section>')
        note_md, _ = html2md.convert_note(note)
        md = Path(note_md).read_text(encoding="utf-8")
        self.assertEqual(html2md.check_md(note, note_md), [])
        Path(note_md).write_text(md.replace("Let $a$ be", "Let be"), encoding="utf-8")
        problems = html2md.check_md(note, note_md)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("수식 누락: $a$"))
        Path(note_md).write_text(md.replace(r" and $\alpha$", " and"), encoding="utf-8")
        self.assertIn("(1/2)", html2md.check_md(note, note_md)[0])

    def test_check_md_detects_unrewritten_and_broken_links(self):
        md = self.md + "\n[a](./정리노트_0101-0102_Mini_Test.html#s1)\n[x](../%EC%97%86%EC%9D%8C/x.html)\n"
        Path(self.note_md).write_text(md, encoding="utf-8")
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(len(problems), 2)
        self.assertTrue(problems[0].startswith("링크 미변환(.html): ./정리노트"))
        self.assertTrue(problems[1].startswith("링크 파일 없음: ../"))

    def test_no_figures_dir_when_no_svgs(self):
        d = self.tmp / "nofig"
        d.mkdir()
        note = small_note(d, '<section id="s"><h2>A</h2><p>그림 없는 문단</p></section>')
        note_md, figs = html2md.convert_note(note)
        self.assertEqual(figs, 0)
        self.assertFalse((d / "figures_0101").exists())
        self.assertTrue(Path(note_md).exists())

    def test_nfd_named_note_converts(self):
        d = self.tmp / "nfd"
        d.mkdir()
        nfd_link = unicodedata.normalize("NFD", "./정리노트_0101_X.html") + "#s"
        note = small_note(d, f'<section id="s"><h2>A</h2><p><a href="{nfd_link}">self</a></p></section>', nfd=True)
        note_md, _ = html2md.convert_note(note)
        self.assertEqual(Path(note_md).name, "정리노트_0101_X.md")
        self.assertIn("(./정리노트_0101_X.md#s)", Path(note_md).read_text(encoding="utf-8"))
        self.assertEqual(html2md.check_md(note, note_md), [])


if __name__ == "__main__":
    unittest.main()
