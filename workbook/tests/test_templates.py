import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TEMPLATES  # noqa: E402

PLACEHOLDER = "__WORKBOOK_DATA__"


def read(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


class TestTemplates(unittest.TestCase):
    def test_placeholder_once(self):
        for name in ("problem.html", "answer.html"):
            with self.subTest(name=name):
                t = read(name)
                self.assertEqual(t.count(PLACEHOLDER), 1)
                self.assertIn(f'id="workbook-data">{PLACEHOLDER}</script>', t)

    def test_samples_extracted(self):
        for name, mode in (("sample-problem.json", "problems"), ("sample-answer.json", "answers")):
            with self.subTest(name=name):
                data = json.loads(read(name))
                self.assertEqual(data["meta"]["mode"], mode)
                self.assertEqual(len(data["problems"]), 12)

    def test_exam_kind_supported(self):
        for name in ("problem.html", "answer.html"):
            with self.subTest(name=name):
                t = read(name)
                self.assertIn("--kind-exam: #7A4FA0;", t)
                self.assertIn('[data-kind="exam"]', t)
                self.assertIn("'기출': 'exam'", t)
                self.assertIn("p.book_page != null", t)
                self.assertNotIn("p.${p.book_page} · ${n}", t)

    def test_original_block_in_both_templates(self):
        for name in ("problem.html", "answer.html"):
            with self.subTest(name=name):
                t = read(name)
                self.assertIn("block('문제 원문', p.html.original, 'original', p.original_lang || 'en')", t)
                self.assertIn(".original {", t)


if __name__ == "__main__":
    unittest.main()
