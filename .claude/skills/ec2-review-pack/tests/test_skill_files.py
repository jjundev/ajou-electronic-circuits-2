"""참조 문서·SKILL.md 형식과, 본문이 가리키는 파일이 모두 있는지 확인한다."""

import json
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


SKILL_MD = SKILL / "SKILL.md"
EXECUTION_GUIDE = SKILL / "references/execution-guide.md"


class TestSkillMd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_MD.read_text(encoding="utf-8")

    def test_frontmatter(self):
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", self.text)
        self.assertIsNotNone(m, "frontmatter는 name, description 두 줄")
        self.assertEqual(m.group(1), "ec2-review-pack")
        for word in ("전자회로2", "정리노트", "복습문제"):
            self.assertIn(word, m.group(2))
        self.assertLessEqual(len(m.group(2)), 1024)

    def test_doc_links_and_required_contracts_resolve(self):
        # Follow real local Markdown links, allowing progressive disclosure.
        pending = [SKILL_MD]
        visited = set()
        while pending:
            path = pending.pop().resolve()
            if path in visited:
                continue
            visited.add(path)
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+\.(?:md|py|html)(?:#[^)]*)?)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                child = (path.parent / target.split("#")[0]).resolve()
                self.assertTrue(child.is_file(), (path, target))
                if child.suffix == ".md" and child.is_relative_to(SKILL):
                    pending.append(child)
        self.assertIn((SKILL / "references/runner-contract.md").resolve(), visited)
        for reference in (SKILL / "references").glob("*.md"):
            self.assertIn(reference.resolve(), visited, reference.name)
        # Documented command/action interface is checked against actual argparse.
        from pack_cli import main
        from contextlib import redirect_stdout
        from io import StringIO
        for args in (["--help"], ["task", "--help"]):
            output = StringIO()
            with redirect_stdout(output):
                code = main(args)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["schema_version"], 1)


# Backup/cleanup behavior is exercised directly in test_pack_files.py.
# Documentation contains API calls rather than a second implementation.


class TestWhyPageDocs(unittest.TestCase):
    def read(self, rel):
        return (SKILL / rel).read_text(encoding="utf-8")

    def test_manifest_guide_fixes_why_section(self):
        t = self.read("references/manifest-guide.md")
        for s in ('"why"', "why-circuit", "들어가며: 왜 이런 회로를 쓸까", "왜 쓸까"):
            self.assertIn(s, t)

    def test_content_rules_has_why_section(self):
        self.assertIn("## 왜 쓰는가 페이지 (`why-circuit`)", self.read("references/content-rules.md"))

    def test_guide_rules_for_author_reviewer_and_template(self):
        rules = self.read("references/content-rules.md")
        self.assertIn("## 정확히 말하면의 길잡이", rules)
        for s in ('<h4 class="sub">', '<div class="quiz after">', 'class="drow"', "folded-body", "formal-no-subheads"):
            self.assertIn(s, rules)
        self.assertIn("정확히 말하면의 길잡이", self.read("references/review-prompt.md"))
        template = self.read("assets/note-template.html")
        for s in ('data-guide="1"', ".layer.formal h4.sub", ".drow", ".quiz.after"):
            self.assertIn(s, template)
        self.assertNotIn("details.more", template)

    def test_topic_circuits_for_author_reviewer_designer_and_template(self):
        rules = self.read("references/content-rules.md")
        self.assertIn("## 토픽 회로 (`figure.circuit`)", rules)
        for s in ('<figure class="figure circuit">', "fig-loc", '<span class="loc">', "data-symbol", "loc-unused"):
            self.assertIn(s, rules)
        self.assertIn('`circuits`', self.read("references/manifest-guide.md"))
        self.assertIn("**토픽 회로**", self.read("references/review-prompt.md"))
        self.assertIn("## 토픽 회로", self.read("references/browser-check.md"))
        self.assertIn("위치 표시 예외", self.read("references/solution-style.md"))
        template = self.read("assets/note-template.html")
        for s in ('data-circuits="1"', "{{CIRCUIT_STYLES}}", "<span>요약</span>"):
            self.assertIn(s, template)
        circuit_styles = self.read("assets/circuit-figure.css")
        for s in (".js .layer .circuit { position: sticky", ".fig-loc"):
            self.assertIn(s, circuit_styles)
        for s in ("placeCircuits", 'class="circuits"', "회로와 요약", "회로·요약"):
            self.assertNotIn(s, template)

    def test_summary_prompt_collects_motivation(self):
        self.assertIn("## 동기 발언", self.read("references/stt-summary-prompt.md"))

    def test_review_prompt_checks_why(self):
        self.assertIn("why-circuit", self.read("references/review-prompt.md"))

    def test_skill_md_mentions_retrofit(self):
        t = self.read("SKILL.md")
        self.assertIn("references/execution-guide.md", t)
        self.assertIn("기존 팩에 왜 페이지 붙이기", t)
        guide = EXECUTION_GUIDE.read_text(encoding="utf-8")
        self.assertIn("scripts/insert_why.py", guide)
        self.assertIn("## 기존 팩에 왜 페이지 붙이기", guide)


class TestLearningStyleBriefs(unittest.TestCase):
    def test_parent_briefs_include_profile_and_audit(self):
        author = (SKILL / "references/content-rules.md").read_text()
        reviewer = (SKILL / "references/review-prompt.md").read_text()
        for brief in (author, reviewer):
            self.assertIn("<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md", brief)
            self.assertIn("learning_style", brief)
            self.assertIn("핵심 관계", brief)
        self.assertIn("learning-style-audit.json", reviewer)
        skill = SKILL_MD.read_text() + EXECUTION_GUIDE.read_text()
        for required in ("--mode problems", "--mode answers --answer-overlay", "--defer-answer-pdf", "publish_answer.py", "answer-review.json"):
            self.assertIn(required, skill)


class TestHardenedContracts(unittest.TestCase):
    """1106 run lessons must stay in the documents workers and the main agent read."""

    def read(self, rel):
        return (SKILL / rel).read_text(encoding="utf-8")

    def test_worker_prompt_has_placeholders(self):
        text = self.read("references/worker-prompt.md")
        for token in ("{role}", "{brief}", "{attempt}", "{run_id}", "task check", "800자"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_docs_mention_new_contracts(self):
        expected = {
            "SKILL.md": ("~/.cache/ec2-review-pack", "NFC", "worker-prompt.md", "waived"),
            "references/runner-contract.md": ("task check", "--allow-tmp", "waived", "~/.cache/ec2-review-pack"),
            "references/delegation.md": ("layout_probe.py", "task check",
                                         "작성자는 인계 전에 `<python> <SKILL>/scripts/pack_cli.py task probe"),
            "references/worker-prompt.md": (
                "<python> <SKILL>/scripts/pack_cli.py task probe --run <RUN> --task {task_id} --attempt {attempt}"
                "   # author만: status pass 확인\n<python> <SKILL>/scripts/pack_cli.py task build-receipt",),
            "references/problem-explain-integration.md": ("bucket", "폴더 이름", "SVG", "task check"),
            "references/execution-guide.md": ("~/.cache/ec2-review-pack", "재부팅"),
        }
        for rel, tokens in expected.items():
            text = self.read(rel)
            for token in tokens:
                with self.subTest(file=rel, token=token):
                    self.assertIn(token, text)


class TestPerProblemDocs(unittest.TestCase):
    def read(self, rel):
        return (SKILL / rel).read_text(encoding="utf-8")

    def test_per_problem_explanation_documented(self):
        expected = {
            "references/runner-contract.md": ("explain-author-pN", "같은 문항", "pN:<소문항>", "선택된 workbook ID"),
            "references/problem-explain-integration.md": ("explain-author-pN", "explain-blind-pN", "problem_contract"),
            "references/worker-prompt.md": ("sealed/pN/",),
        }
        for rel, tokens in expected.items():
            text = self.read(rel)
            for token in tokens:
                with self.subTest(file=rel, token=token):
                    self.assertIn(token, text)


class TestUnboundedDocs(unittest.TestCase):
    def test_docs_have_no_slot_caps_or_python3(self):
        refs = SKILL / "references"
        text = "\n".join(p.read_text(encoding="utf-8") for p in refs.glob("*.md"))
        for banned in ("전체 슬롯 최대 4", "메인+직접 작업자 최대 3명",
                       "예상 종료 시각으로 슬롯을 재배정하지 않는다", "python3 "):
            self.assertNotIn(banned, text)
        self.assertIn("준비된 독립 작업은 한 메시지에서 모두 띄운다",
                      (refs / "delegation.md").read_text(encoding="utf-8"))
        self.assertIn("reference_sections",
                      (refs / "worker-prompt.md").read_text(encoding="utf-8"))

    def test_contract_runs_document_probe_sources_and_brief_fields(self):
        refs = SKILL / "references"
        guide = (refs / "execution-guide.md").read_text(encoding="utf-8")
        runner = (refs / "runner-contract.md").read_text(encoding="utf-8")
        prompt = (refs / "worker-prompt.md").read_text(encoding="utf-8")
        self.assertIn("`probe_contract`가 있는 RUN의 작성자는 인계 전에 `<python> <SKILL>/scripts/pack_cli.py "
                      "task probe --run <RUN> --task <id> --attempt <UUID>`로 status pass를 확인한 뒤 `task check`",
                      guide)
        self.assertIn("fragment probe missing, stale or failing", guide)
        self.assertIn("`reference_sections`(없으면 `references`)의 절", runner)
        self.assertIn("작업자 명령의 `<python>`은 브리프의 `python` 값이다", runner)
        self.assertIn("`source_contract`가 있는 RUN에서 source-prep은 작업자 역할이 아니라 기계 작업이다", runner)
        self.assertIn("**기존 RUN(`source_contract` 없음)**", runner)
        self.assertIn("메인 검토(`review_locally`)만 기다리는 동안에는 기계 작업을 계속 실행하고", runner)
        self.assertNotIn("가용 슬롯", runner)
        self.assertIn("`layout.status`가 `unavailable`이어도", prompt)
        self.assertIn("browser-qa가 확인한다", prompt)

    def test_summarizers_match_slides_themselves(self):
        refs = SKILL / "references"
        self.assertIn("slides.txt 전체에서 이 날짜 STT가 다룬 강의 블록을 찾아",
                      (refs / "stt-summary-prompt.md").read_text(encoding="utf-8"))
        self.assertNotIn("| 자료 준비자 |",
                         (refs / "delegation.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
