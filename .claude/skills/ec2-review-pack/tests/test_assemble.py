import json
from pathlib import Path
import shutil
import tempfile
import unittest

from _util import ML_SKILL, MINI_RUN, SKILL

import assemble


class TestAssemble(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.note = assemble.assemble(MINI_RUN, self.tmp)
        self.html = self.note.read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def copy_run(self) -> Path:
        run = self.tmp / "run"
        shutil.copytree(MINI_RUN, run)
        return run

    def test_output_name(self):
        self.assertEqual(self.note.name, "정리노트_0101-0102_Mini_Test.html")

    def test_only_note_is_written(self):
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), [".assets", "정리노트_0101-0102_Mini_Test.html"])
        self.assertEqual([p.name for p in (self.tmp / ".assets").iterdir()], ["problems.txt"])

    def test_sections_toc_and_titles(self):
        self.assertIn('<nav class="toc" aria-label="목차"><a href="#why">왜 쓸까</a><a href="#s1">1 기초</a><a href="#s2">2 요약·예고</a></nav>', self.html)
        self.assertLess(self.html.index('<section id="why">'), self.html.index('<section id="s1">'))
        self.assertIn('<section id="s1"><h2>1. 기초 통계</h2>', self.html)
        self.assertIn("<h1>Mini — 테스트 정리노트</h1>", self.html)
        self.assertIn("<title>전자회로2 정리노트 0101-0102</title>", self.html)

    def test_scripts_moved_after_main(self):
        self.assertGreater(self.html.index('<script id="widget-mean-ui">'), self.html.index("</main>"))

    def test_pdf_tokens_replaced_and_no_slots_left(self):
        self.assertIn('href="복습문제_0101-0102_Mini_Test-문제.pdf"', self.html)
        self.assertIn('href="복습문제_0101-0102_Mini_Test-답안.pdf"', self.html)
        self.assertNotIn("{{", self.html)

    def test_progress_key_and_theme(self):
        self.assertIn('data-range="0101-0102"', self.html)
        self.assertIn("const KEY = 'od-note-read:' + RANGE;", self.html)
        self.assertIn('id="theme-toggle"', self.html)
        self.assertIn("localStorage.getItem('od-theme')", self.html.split("</head>", 1)[0])

    @unittest.skipUnless((ML_SKILL / "assets" / "note-template.html").exists(), "ML 스킬 없음")
    def test_template_is_identical_to_ml(self):
        ours = (SKILL / "assets" / "note-template.html").read_bytes()
        self.assertEqual(ours, (ML_SKILL / "assets" / "note-template.html").read_bytes())

    def test_problems_txt(self):
        self.assertEqual((self.tmp / ".assets" / "problems.txt").read_text(encoding="utf-8"),
                         "P9.01 | 테스트용 장말문제\n2023-1_기말-Q1 | 테스트용 기출\n")

    def test_zero_problems_removes_stale_problems_txt(self):
        run = self.copy_run()
        m = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        m["problems"], m["links"] = [], []
        (run / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        assemble.assemble(run, self.tmp)
        self.assertFalse((self.tmp / ".assets" / "problems.txt").exists())

    def test_missing_fragment_writes_nothing(self):
        run = self.copy_run()
        (run / "sections" / "s2.html").unlink()
        out = self.tmp / "out"
        with self.assertRaises(assemble.AssembleError):
            assemble.assemble(run, out)
        self.assertFalse(out.exists())
        before = self.note.read_bytes()
        with self.assertRaises(assemble.AssembleError):
            assemble.assemble(run, self.tmp)
        self.assertEqual(self.note.read_bytes(), before)

    def test_fill_rejects_missing_slot(self):
        with self.assertRaises(assemble.AssembleError):
            assemble.fill("<p>{{NOPE}}</p>", {})

    def test_fill_does_not_expand_slots_inside_values(self):
        self.assertEqual(assemble.fill("{{A}}", {"A": "{{B}}"}), "{{B}}")


if __name__ == "__main__":
    unittest.main()
