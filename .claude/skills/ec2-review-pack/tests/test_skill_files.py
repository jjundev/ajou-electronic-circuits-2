"""참조 문서·SKILL.md 형식과, 본문이 가리키는 파일이 모두 있는지 확인한다."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest

from _util import SKILL

REFERENCES = ("stt-summary-prompt", "manifest-guide", "content-rules", "widget-rules",
              "problem-selection", "review-prompt", "browser-check")
ML_LEFTOVERS = ("MML", "머신러닝", "정방철", "REVIEW_HREF", "answers.py", "card-rules", "review-template")


def skill_texts():
    for path in sorted(SKILL.rglob("*")):
        if path.suffix in (".md", ".py") and "tests" not in path.parts and "__pycache__" not in path.parts:
            yield path, path.read_text(encoding="utf-8")


class TestReferences(unittest.TestCase):
    def test_reference_files_exist(self):
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertTrue((SKILL / "references" / f"{name}.md").exists())

    def test_no_ml_leftovers(self):
        for path, text in skill_texts():
            for word in ML_LEFTOVERS:
                with self.subTest(path=path.name, word=word):
                    self.assertNotIn(word, text)

    def test_pdf_tokens_documented(self):
        rules = (SKILL / "references" / "content-rules.md").read_text(encoding="utf-8")
        self.assertIn("{{PROBLEM_PDF}}", rules)
        self.assertIn("{{ANSWER_PDF}}", rules)

    def test_selection_rules_use_index_tool(self):
        text = (SKILL / "references" / "problem-selection.md").read_text(encoding="utf-8")
        self.assertIn("scripts/problem_index.py", text)
        self.assertIn("--used", text)


if __name__ == "__main__":
    unittest.main()
