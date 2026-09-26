import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from _util import MINI_RUN

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
        return sorted(p.code for p in check_html.check_pack(self.m(), note))

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
        self.edit("sections/s1.html", '<div class="layer prof"><span class="layer-title">교수님 말씀</span><p>"평균부터 봐요." (0101 01:00)</p></div>', "")
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
