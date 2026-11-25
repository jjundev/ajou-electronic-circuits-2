import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from _util import MINI_RUN, REPO

import assemble
import check_html
import manifest


class TestPrimitives(unittest.TestCase):
    def test_adjacent_inline_math_in_list_items_is_not_display_math(self):
        doc = check_html.parse_html('<html lang="ko"><body><ol><li>$a$</li><li>$b$</li></ol></body></html>')
        self.assertEqual(check_html.math_delimiter_errors(doc.body_text), [])

    def test_unbalanced_inline_math(self):
        self.assertEqual(check_html.math_delimiter_errors("a $x b"), ["unbalanced $ (inline math)"])

    def test_widget_without_static(self):
        src = '<html lang="ko"><body><div class="widget" id="w1"><h4>x</h4></div></body></html>'
        problems = check_html.check_common(check_html.parse_html(src), src, Path("x.html"))
        self.assertEqual([p.code for p in problems], ["widget-static-missing"])

    def test_markdown_link(self):
        src = '<html lang="ko"><body><p>[평균](#s1-mean)으로 가요. 배열 a[0](x)는 괜찮아요.</p></body></html>'
        problems = check_html.check_common(check_html.parse_html(src), src, Path("x.html"))
        self.assertEqual([(p.code, p.detail) for p in problems], [("markdown-link", "[평균](#s1-mean)")])

    def test_leftover_slot_and_external(self):
        src = '<html lang="ko"><head><script src="https://cdn.tailwindcss.com"></script></head><body>{{TOC}}</body></html>'
        codes = sorted(p.code for p in check_html.check_common(check_html.parse_html(src), src, Path("x.html")))
        self.assertEqual(codes, ["external", "leftover-slot"])

    def test_no_review_checker_left(self):
        self.assertFalse(hasattr(check_html, "check_review"))


class TestPack(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run = self.tmp / "run"
        shutil.copytree(MINI_RUN, self.run)
        self.out = self.tmp / "out"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def m(self) -> dict:
        return json.loads((self.run / "manifest.json").read_text(encoding="utf-8"))

    def build(self) -> Path:
        note = assemble.assemble(self.run, self.out)
        m = self.m()
        if m["problems"]:  # 실제로는 build_workbook.py가 만든다
            for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
                (self.out / name).write_bytes(b"%PDF-1.4\n")
        return note

    def codes(self, note: Path | None = None) -> list[str]:
        note = note or self.build()
        return sorted(p.code for p in check_html.check_pack(self.m(), note, repo=REPO, style_audit=json.loads((self.run / "learning-style-audit.json").read_text())))

    def edit(self, rel: str, old: str, new: str):
        path = self.run / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def test_mini_pack_passes(self):
        self.assertEqual(self.codes(), [])

    def test_missing_required_term(self):
        self.edit("sections/s1.html", "무게중심", "가운데")
        self.assertEqual(self.codes(), ["missing-term"])

    def test_forbidden_term_outside_preview(self):
        self.edit("sections/s1.html", "분산은 흩어진 정도예요.", "분산은 d-separation과 무관해요.")
        self.assertEqual(self.codes(), ["forbidden-term"])

    def test_missing_layer(self):
        self.edit("sections/s1.html", '<div class="layer prof"><span class="layer-title">교수님 말씀</span><p>"평균부터 봐요."</p></div>', "")
        self.assertEqual(self.codes(), ["missing-layer"])

    def test_missing_supp_badge(self):
        self.edit("sections/s1.html", '<span class="badge supp">보충 · 수업에서 유도하진 않았어요</span>', "")
        self.assertEqual(self.codes(), ["missing-supp"])

    def test_missing_sum(self):
        self.edit("sections/s1.html", '<div class="sum" hidden>\n          <p class="sum-lead">평균은', '<div class="summary" hidden>\n          <p class="sum-lead">평균은')
        self.assertEqual(self.codes(), ["missing-sum"])

    def test_widget_static_required(self):
        self.edit("sections/s1.html", 'class="widget-static"', 'class="widget-snap"')
        self.assertEqual(self.codes(), ["widget-static-missing"])

    def test_missing_pdf_is_broken_link(self):
        note = self.build()
        (self.out / manifest.answer_pdf_name(self.m())).unlink()
        self.assertEqual(self.codes(note), ["broken-link"])

    def test_leftover_review_token(self):
        self.edit("sections/s2.html", "{{PROBLEM_PDF}}", "{{REVIEW_HREF}}")
        self.assertEqual(self.codes(), ["broken-link", "leftover-slot", "missing-link"])

    def test_zero_problem_pack_passes_without_pdfs(self):
        m = self.m()
        m["problems"], m["links"] = [], []
        (self.run / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        self.edit("sections/s2.html",
                  '<ul><li><a href="{{PROBLEM_PDF}}">복습문제 PDF</a></li><li><a href="{{ANSWER_PDF}}">복습문제 답안 PDF</a></li></ul>',
                  "<p>이번 범위에는 복습문제가 없어요.</p>")
        self.assertEqual(self.codes(), [])

    def test_missing_check_quiz(self):
        self.edit("sections/s1.html", '<div class="quiz after"><p class="q">확인해 봐요. $2$와', '<div class="quiz"><p class="q">확인해 봐요. $2$와')
        self.assertEqual(self.codes(), ["missing-check-quiz"])

    def test_check_quiz_needs_answer_toggle(self):
        self.edit("sections/s1.html", "<details><summary>답 보기</summary><p>$\\frac{2+4}{2}=3$이에요.</p></details>",
                  "<p>$\\frac{2+4}{2}=3$이에요.</p>")
        self.assertEqual(self.codes(), ["missing-check-quiz"])

    def test_folded_body(self):
        self.edit("sections/s1.html", '<p>$$\\bar{x} = \\frac{1}{N}\\sum_{n=1}^{N} x_n$$</p></div>',
                  '<details><summary>유도</summary><p>$$\\bar{x} = \\frac{1}{N}\\sum_{n=1}^{N} x_n$$</p></details></div>')
        self.assertEqual(self.codes(), ["folded-body"])

    def test_folded_body_outside_layers(self):
        self.edit("sections/s1.html", '<div class="layer prof"><span class="layer-title">교수님 말씀</span><p>"평균부터 봐요."</p></div>',
                  '<div class="layer prof"><span class="layer-title">교수님 말씀</span></div>'
                  '<div class="folds"><details class="more"><summary>교수님 말씀</summary><p>"평균부터 봐요."</p></details></div>')
        self.assertEqual(self.codes(), ["folded-body"])

    def test_long_formal_needs_subheads(self):
        old = '<p>$\\sigma^2 = \\frac{1}{N}\\sum_{n}(x_n - \\bar{x})^2$</p>'
        self.edit("sections/s1.html", old, old + "<p>가</p>" * 5)
        self.assertEqual(self.codes(), ["formal-no-subheads"])
        self.edit("sections/s1.html", '<span class="layer-title">정확히 말하면</span><p>$\\sigma',
                  '<span class="layer-title">정확히 말하면</span><h4 class="sub">정의</h4><p>$\\sigma')
        self.assertEqual(self.codes(), [])

    def test_guide_checks_skip_notes_without_marker(self):
        note = self.build()
        text = note.read_text(encoding="utf-8").replace(' data-guide="1"', "")
        note.write_text(text.replace('<div class="quiz after">', '<div class="quiz">'), encoding="utf-8")
        self.assertEqual(self.codes(note), [])

    # ---- 토픽 회로 ----
    FORMAL = '<span class="layer-title">정확히 말하면</span><p>$$'
    CIRCUIT = ('<figure class="figure circuit"><svg id="fig-circuit-mean" viewBox="0 0 60 60" role="img" aria-label="회로">'
               '<text class="fig-text fig-loc" x="9" y="9">㉠</text></svg><figcaption><span class="loc">㉠</span> 입력 (강의노트 s1)</figcaption></figure>')

    def plan(self, circuits):
        path = self.run / "manifest.json"
        m = self.m()
        m["sections"][1]["topics"][0]["circuits"] = circuits
        path.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")

    def draw(self, figure=None, text='<p><span class="loc">㉠</span> 입력이에요.</p>'):
        self.plan([{"id": "fig-circuit-mean", "source": "L01 s1"}])
        self.edit("sections/s1.html", self.FORMAL,
                  '<span class="layer-title">정확히 말하면</span>' + (figure or self.CIRCUIT) + text + '<p>$$')

    def test_planned_circuit_passes(self):
        self.draw()
        self.assertEqual(self.codes(), [])

    def test_missing_planned_circuit(self):
        self.plan([{"id": "fig-circuit-mean", "source": "L01 s1"}])
        self.assertEqual(self.codes(), ["missing-circuit"])

    def test_circuit_after_first_display_math(self):
        self.draw()
        text = (self.run / "sections/s1.html").read_text(encoding="utf-8").replace(self.CIRCUIT, "", 1)
        (self.run / "sections/s1.html").write_text(
            text.replace("x_n$$</p></div>", "x_n$$</p>" + self.CIRCUIT + "</div>", 1), encoding="utf-8")
        self.assertEqual(self.codes(), ["circuit-after-math"])

    def test_circuit_must_be_direct_child_of_formal(self):
        self.draw("<div>" + self.CIRCUIT + "</div>")
        self.assertEqual(self.codes(), ["circuit-place"])

    def test_circuit_needs_caption_and_id(self):
        self.draw(self.CIRCUIT.replace('<span class="loc">㉠</span> 입력 (강의노트 s1)', ""))
        self.assertEqual(self.codes(), ["circuit-caption"])
        self.edit("sections/s1.html", "fig-circuit-mean", "fig-mean-circuit")
        self.assertEqual(self.codes(), ["circuit-caption", "circuit-id", "missing-circuit"])

    def test_too_many_circuits(self):
        self.draw(self.CIRCUIT + "".join(self.CIRCUIT.replace("circuit-mean", f"circuit-mean-{n}") for n in (2, 3)))
        self.assertEqual(self.codes(), ["too-many-circuits"])

    def test_location_marks_must_match_both_ways(self):
        self.draw(text='<p><span class="loc">㉡</span> 없는 곳이에요.</p>')
        self.assertEqual(self.codes(), ["loc-not-in-circuit", "loc-unused"])

    def test_caption_alone_does_not_use_a_mark(self):
        self.draw(text="")
        self.assertEqual(self.codes(), ["loc-unused"])

    def test_circuit_is_refused_in_why_page(self):
        self.edit("sections/why.html", '<span class="layer-title">정확히 말하면</span>',
                  '<span class="layer-title">정확히 말하면</span>' + self.CIRCUIT + '<p><span class="loc">㉠</span></p>')
        self.assertEqual(self.codes(), ["circuit-place"])

    def test_circuit_checks_skip_notes_without_marker(self):
        self.plan([{"id": "fig-circuit-mean", "source": "L01 s1"}])
        note = self.build()
        note.write_text(note.read_text(encoding="utf-8").replace(' data-circuits="1"', ""), encoding="utf-8")
        self.assertEqual(self.codes(note), [])

    def test_cli_exit_codes(self):
        note = self.build()
        args = ["--manifest", str(self.run / "manifest.json"), "--note", str(note)]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(check_html.main(args), 0)
            self.assertEqual(check_html.main([str(note)]), 0)
            note.write_text(note.read_text(encoding="utf-8").replace('lang="ko"', 'lang="en"'), encoding="utf-8")
            self.assertEqual(check_html.main(args), 1)
        self.assertIn("[lang]", out.getvalue())

    def test_cli_manifest_requires_note(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            check_html.main(["--manifest", str(self.run / "manifest.json")])


if __name__ == "__main__":
    unittest.main()
