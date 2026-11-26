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
        self.assertEqual(Path(self.note_md), self.tmp / ".assets" / "정리노트_0101-0102_Mini_Test.md")
        self.assertEqual(html2md.check_md(self.note, self.note_md), [])

    def test_location_mark_color_only_where_used(self):
        note = small_note(self.tmp, '<figure class="figure circuit"><svg id="fig-circuit-a" viewBox="0 0 60 60"><text class="fig-text fig-loc" x="9" y="20">㉠</text></svg><figcaption><span class="loc">㉠</span> 입력</figcaption></figure>'
                          '<figure><svg id="fig-plain" viewBox="0 0 60 60"><text class="fig-text" x="9" y="20">A</text></svg></figure>')
        md, count = html2md.convert_note(note)
        self.assertEqual(count, 2)
        svg = {p.stem: p.read_text(encoding="utf-8") for p in Path(md).parent.rglob("fig-*.svg")}
        self.assertIn("svg .fig-loc {", svg["fig-circuit-a"])
        self.assertNotIn("fig-loc", svg["fig-plain"])
        self.assertIn("*㉠ 입력*", Path(md).read_text(encoding="utf-8"))

    def test_location_mark_redrawn_with_pretendard_jamo(self):
        """Pretendard has no ㉠–㉭: the standalone SVG draws a ring and a Pretendard jamo instead."""
        import base64
        import io
        import re
        from fontTools.ttLib import TTFont
        marks = ('<text class="fig-text fig-loc" style="font-size:20px" text-anchor="middle" x="40" y="50" data-node="n1">㉠</text>'
                 '<text class="fig-text fig-loc" x="10" y="30">㉭</text>'
                 '<text class="fig-text fig-loc" x="90" y="30" text-anchor="end" transform="rotate(5)">㉡</text>')
        note = small_note(self.tmp, f'<figure class="figure circuit"><svg id="fig-circuit-a" viewBox="0 0 120 80">{marks}</svg>'
                                    '<figcaption><span class="loc">㉠</span> 입력</figcaption></figure>')
        html2md.convert_note(note)
        svg = (self.tmp / ".assets/figures_0101/fig-circuit-a.svg").read_text(encoding="utf-8")
        doc = xml.dom.minidom.parseString(svg)
        self.assertIsNone(re.search("[㉠-㉭]", svg))
        groups = doc.getElementsByTagName("g")
        self.assertEqual([g.getAttribute("class") for g in groups], ["fig-loc-mark"] * 3)
        rings = [g.getElementsByTagName("circle")[0] for g in groups]
        texts = [g.getElementsByTagName("text")[0] for g in groups]
        self.assertEqual([t.firstChild.data for t in texts], ["ㄱ", "ㅎ", "ㄴ"])
        # middle: centred on x; start: half an em right; end: half an em left. Centre 0.38 em above the baseline.
        self.assertEqual([(c.getAttribute("cx"), c.getAttribute("cy"), c.getAttribute("r")) for c in rings],
                         [("40", "42.4", "8.8"), ("16.5", "25.06", "5.72"), ("83.5", "25.06", "5.72")])
        self.assertTrue(all(t.getAttribute("x") == c.getAttribute("cx") and t.getAttribute("text-anchor") == "middle"
                            for t, c in zip(texts, rings)))
        self.assertTrue(all("fig-loc" in t.getAttribute("class").split() for t in texts))
        self.assertEqual(groups[0].getAttribute("data-node"), "n1")
        self.assertEqual(groups[2].getAttribute("transform"), "rotate(5)")
        css = doc.getElementsByTagName("style")[0].firstChild.data
        self.assertIn("svg .fig-loc-ring {", css)
        raw = base64.b64decode(re.search(r"base64,([A-Za-z0-9+/=]+)", css).group(1))
        cmap = TTFont(io.BytesIO(raw)).getBestCmap()
        for ch in "ㄱㄴㅎ":
            self.assertIn(ord(ch), cmap)

    def test_inline_serialize_keeps_location_mark(self):
        """Pages load fonts themselves: only standalone export redraws the mark."""
        parser = html2md.Builder()
        parser.feed('<svg><text class="fig-text fig-loc" x="1" y="2">㉠</text></svg>')
        self.assertIn(">㉠</text>", html2md.serialize(parser.root.children[0]))
        self.assertNotIn("fig-loc-mark", html2md.serialize(parser.root.children[0]))

    def test_exported_svg_contains_real_semibold_and_native_subscripts(self):
        import base64
        import io
        import re
        from fontTools.ttLib import TTFont
        note = small_note(self.tmp, '<figure><svg viewBox="0 0 240 120"><text class="fig-text fig-math" font-family="Times New Roman" font-style="italic" x="12" y="30">g<tspan baseline-shift="sub" font-size="72%">m3</tspan></text></svg></figure>')
        _, count = html2md.convert_note(note)
        self.assertEqual(count, 1)
        svg = next((self.tmp / '.assets/figures_0101').glob('*.svg')).read_text(encoding='utf-8')
        doc = xml.dom.minidom.parseString(svg)
        css = doc.getElementsByTagName('style')[0].firstChild.data
        data = re.search(r'data:font/(woff2?);base64,([A-Za-z0-9+/=]+)', css)
        self.assertIsNotNone(data, 'Standalone SVG must load its own actual 600 font')
        raw = base64.b64decode(data.group(2))
        self.assertEqual(data.group(1), 'woff2', 'Standalone SVG must embed the required WOFF2 font')
        self.assertEqual(raw[:4], b'wOF2', 'The embedded bytes must be WOFF2, not only its MIME label')
        self.assertLess(len(raw), 30_000)
        cmap = TTFont(io.BytesIO(raw)).getBestCmap()
        for ch in ('g', 'm', '3'):
            self.assertIn(ord(ch), cmap)
        self.assertIn('font-weight: 600', css)
        self.assertIn('font-style: normal', css)
        self.assertIn('svg text tspan', css)
        self.assertIn('font-size: 78%', css)
        self.assertIn('baseline-shift="sub"', svg)
        self.assertIn('SIL OPEN FONT LICENSE', css)

    def test_exported_svg_without_text_skips_font_embedding(self):
        note = small_note(self.tmp, '<figure><svg viewBox="0 0 100 40"><rect x="10" y="10" width="80" height="20"/></svg></figure>')
        _, count = html2md.convert_note(note)
        self.assertEqual(count, 1)
        svg = next((self.tmp / '.assets/figures_0101').glob('*.svg')).read_text(encoding='utf-8')
        self.assertNotIn('data:font/', svg)

    def test_guide_structure_converts(self):
        note = small_note(self.tmp, '<article class="topic" id="t1"><h3>T</h3><div class="layer formal">'
                          '<span class="layer-title">정확히 말하면</span><h4 class="sub">왜 정확한가요</h4>'
                          '<p>설명. <b>비로 정해져요.</b></p><ol class="steps"><li><div class="drow">'
                          '<div>$$K^*=K$$</div><p class="why">약분돼요.</p></div></li></ol></div>'
                          '<div class="quiz after"><p class="q">확인해 봐요. $x$는?</p>'
                          '<details><summary>답 보기</summary><p>$1$이에요.</p></details></div></article>')
        md_path, _ = html2md.convert_note(note)
        md = Path(md_path).read_text(encoding="utf-8")
        self.assertIn("#### 왜 정확한가요", md)
        self.assertIn("**비로 정해져요.**", md)
        self.assertLess(md.index("K^*=K"), md.index("약분돼요."))
        self.assertIn("확인해 봐요. $x$는?", md)
        self.assertIn("<details><summary>답 보기</summary>", md)
        self.assertEqual(html2md.check_md(note, md_path), [])

    def test_pdf_links_kept_as_pdf(self):
        self.assertIn("(../복습문제_0101-0102_Mini_Test-문제.pdf)", self.md)
        self.assertIn("(../복습문제_0101-0102_Mini_Test-답안.pdf)", self.md)

    def test_missing_pdf_is_reported(self):
        (self.tmp / "복습문제_0101-0102_Mini_Test-답안.pdf").unlink()
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(problems, ["링크 파일 없음: ../복습문제_0101-0102_Mini_Test-답안.pdf"])

    def test_page_summary_rendered(self):
        self.assertIn("**페이지 요약**", self.md)
        self.assertIn("*핵심 식*", self.md)
        self.assertIn("- **분산(variance)** — 평균과의 차이를 제곱해 평균낸 값", self.md)

    def test_widget_static_becomes_figure_and_table(self):
        self.assertEqual(self.figs, 1)
        self.assertTrue((self.tmp / ".assets" / "figures_0101-0102" / "widget-mean-static.svg").exists())
        self.assertIn('<a id="widget-mean"></a>', self.md)
        self.assertIn("![평균 1.5 막대](figures_0101-0102/widget-mean-static.svg)", self.md)
        self.assertIn("| 1, 2 | $\\frac{3}{2}$ |", self.md)

    def test_reconversion_removes_orphan_svgs_only(self):
        fig = self.tmp / ".assets" / "figures_0101-0102"
        (fig / "old-orphan.svg").write_text("<svg/>", encoding="utf-8")
        (fig / "keep.txt").write_text("x", encoding="utf-8")
        (self.tmp / ".assets" / "outside.svg").write_text("<svg/>", encoding="utf-8")
        _, figs = html2md.convert_note(self.note)
        self.assertEqual(figs, 1)
        self.assertEqual(sorted(p.name for p in fig.iterdir()), ["keep.txt", "widget-mean-static.svg"])
        self.assertTrue((self.tmp / ".assets" / "outside.svg").exists())

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
        self.assertEqual(sorted(x.name for x in (d / ".assets" / "figures_0101").iterdir()),
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
        md = self.md + "\n[a](./정리노트_0101-0102_Mini_Test.html#s1)\n[x](../../%EC%97%86%EC%9D%8C/x.html)\n"
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
        self.assertFalse((d / ".assets" / "figures_0101").exists())
        self.assertTrue(Path(note_md).exists())

    def test_folded_widget_keeps_anchor_and_text(self):
        d = self.tmp / "folded"
        d.mkdir()
        note = small_note(d, '<section id="s"><h2>A</h2><div class="widget" id="widget-f"><details><summary>결과 확인</summary>'
                             '<p class="widget-help">도움말</p><p class="legend"><span>범례 하나</span></p>'
                             '<div class="widget-static" hidden><p>정적 표</p></div></details></div></section>')
        note_md, _ = html2md.convert_note(note)
        md = Path(note_md).read_text(encoding="utf-8")
        for part in ('<a id="widget-f"></a>', "#### 결과 확인", "도움말", "범례: 범례 하나", "정적 표"):
            self.assertIn(part, md)
        self.assertEqual(html2md.check_md(note, note_md), [])

    def test_nfd_named_note_converts(self):
        d = self.tmp / "nfd"
        d.mkdir()
        nfd_link = unicodedata.normalize("NFD", "./정리노트_0101_X.html") + "#s"
        note = small_note(d, f'<section id="s"><h2>A</h2><p><a href="{nfd_link}">self</a></p></section>', nfd=True)
        note_md, _ = html2md.convert_note(note)
        self.assertEqual(Path(note_md).name, "정리노트_0101_X.md")
        self.assertIn("(./정리노트_0101_X.md#s)", Path(note_md).read_text(encoding="utf-8"))
        self.assertEqual(html2md.check_md(note, note_md), [])

    def test_relative_links_rebased_from_assets(self):
        d = self.tmp / "links"
        (d / "pack").mkdir(parents=True)
        (d / "other").mkdir()
        (d / "other" / "정리노트_0100_Y.html").write_text("<p id='t'>y</p>", encoding="utf-8")
        (d / "w.pdf").write_bytes(b"%PDF")
        body = ('<section id="s"><h2>A</h2><p><a href="../other/정리노트_0100_Y.html#t">o</a> '
                '<a href="../w.pdf">w</a> <a href="https://example.com/x">e</a> <a href="#s">a</a></p></section>')
        note = small_note(d / "pack", body)
        note_md, _ = html2md.convert_note(note)
        md = Path(note_md).read_text(encoding="utf-8")
        self.assertIn("(../../other/정리노트_0100_Y.html#t)", md)
        self.assertIn("(../../w.pdf)", md)
        self.assertIn("(https://example.com/x)", md)
        self.assertIn("(#s)", md)
        self.assertEqual(html2md.check_md(note, note_md), [])


if __name__ == "__main__":
    unittest.main()
