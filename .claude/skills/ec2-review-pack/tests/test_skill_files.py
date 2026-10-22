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

    def test_referenced_files_exist(self):
        refs = set(re.findall(r"(?:references|scripts|assets)/[\w.-]+\.(?:md|py|html)", self.text))
        self.assertGreaterEqual(len(refs), 12)
        for rel in sorted(refs):
            with self.subTest(rel=rel):
                self.assertTrue((SKILL / rel).exists(), rel)

    def test_every_reference_is_used(self):
        for path in sorted((SKILL / "references").glob("*.md")):
            with self.subTest(ref=path.name):
                self.assertIn(f"references/{path.name}", self.text)

    def test_steps_present(self):
        for n in range(10):
            with self.subTest(step=n):
                self.assertRegex(self.text, rf"\n### {n}\. ")

    def test_workbook_build_command(self):
        self.assertRegex(self.text, r'workbook/build_workbook\.py"? --ids')
        self.assertIn("--pdf-dir", self.text)
        self.assertIn("--build-dir", self.text)


class TestBackupSnippet(unittest.TestCase):
    """SKILL.md 4단계 백업 스니펫(python 부분)을 임시 폴더에서 실제로 실행한다."""

    @classmethod
    def setUpClass(cls):
        text = SKILL_MD.read_text(encoding="utf-8")
        m = re.search(r"```bash\nRANGE=<range> REPO=… RUN=… python3 - <<'EOF'\n(.*?)\nEOF\n```", text, re.S)
        assert m, "SKILL.md 4단계 백업 스니펫을 찾지 못함"
        cls.code = m.group(1)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.notes = self.tmp / "repo" / "복습노트"
        self.notes.mkdir(parents=True)
        (self.tmp / "repo" / "STT").mkdir()
        self.run_dir = self.tmp / "run"
        self.run_dir.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def backup(self, range_):
        env = dict(os.environ, RANGE=range_, REPO=str(self.tmp / "repo"), RUN=str(self.run_dir))
        return subprocess.run([sys.executable, "-"], input=self.code, env=env, capture_output=True, text=True)

    def backups(self):
        return sorted(p for p in self.run_dir.iterdir() if p.name.startswith("previous-"))

    def test_nothing_to_back_up(self):
        r = self.backup("0923")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("백업할 기존 팩 없음", r.stdout)
        self.assertEqual(self.backups(), [])

    def test_backs_up_note_pdfs_and_problem_list(self):
        pack = self.notes / "0923"
        assets = pack / ".assets"
        (assets / "figures_0923").mkdir(parents=True)
        (assets / "figures_0923" / "a.svg").write_text("<svg/>", encoding="utf-8")
        (pack / "정리노트_0923_A.html").write_text("n", encoding="utf-8")
        (assets / unicodedata.normalize("NFD", "정리노트_0923_A.md")).write_text("m", encoding="utf-8")
        (pack / "복습문제_0923_A-문제.pdf").write_bytes(b"%PDF")
        (pack / unicodedata.normalize("NFD", "복습문제_0923_A-답안.pdf")).write_bytes(b"%PDF")
        (assets / "problems.txt").write_text("P10.01 | x\n", encoding="utf-8")
        (assets / "문제설명_0923_A.md").write_text("다른 스킬 소유", encoding="utf-8")
        (self.notes / "0918").mkdir()
        (self.notes / "0918" / "정리노트_0918_B.html").write_text("other", encoding="utf-8")
        for _ in range(2):  # 같은 세션에서 다시 실행해도 이전 백업을 덮지 않는다
            r = self.backup("0923")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("백업 6항목(파일 6개)", r.stdout)
        dirs = self.backups()
        self.assertEqual(len(dirs), 2)
        names = sorted(unicodedata.normalize("NFC", n) for n in os.listdir(dirs[0]))
        self.assertEqual(names, [".assets", "복습문제_0923_A-답안.pdf", "복습문제_0923_A-문제.pdf", "정리노트_0923_A.html"])
        names = sorted(unicodedata.normalize("NFC", n) for n in os.listdir(dirs[0] / ".assets"))
        self.assertEqual(names, ["figures_0923", "problems.txt", "정리노트_0923_A.md"])

    def test_title_map_rolls_back_with_its_published_pack(self):
        integration = (SKILL / "references/problem-explain-integration.md").read_text(encoding="utf-8")
        match = re.search(r'python3 - "\$REPO" "\$RUN" "\$RANGE" <<\'EOF\'\n(.*?)\nEOF', integration, re.S)
        self.assertIsNotNone(match)
        pack = self.notes / "0923"
        assets = pack / ".assets"
        assets.mkdir(parents=True)
        note = pack / "정리노트_0923_A.html"
        note.write_text("old published note", encoding="utf-8")
        titles = assets / "display-titles.json"
        for had_titles in (True, False):
            with self.subTest(had_titles=had_titles):
                if had_titles:
                    titles.write_text('{"E9.05":"old"}', encoding="utf-8")
                else:
                    titles.unlink(missing_ok=True)
                backup = self.backup("0923")
                self.assertEqual(backup.returncode, 0, backup.stderr)
                record = json.loads((self.run_dir / "basic-pack-backup.json").read_text())
                self.assertEqual(".assets/display-titles.json" in record["files"], had_titles)
                (self.run_dir / "explanations-backup.json").write_text(json.dumps(
                    {"range":"0923", "backup":None, "roots":[], "files":{}, "dirs":[]}), encoding="utf-8")
                titles.write_text('{"E9.05":"new"}', encoding="utf-8")
                note.write_text("unfinished note", encoding="utf-8")
                result = subprocess.run([sys.executable, "-", str(self.tmp / "repo"), str(self.run_dir), "0923"],
                    input=match.group(1), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(note.read_text(encoding="utf-8"), "old published note")
                self.assertEqual(titles.exists(), had_titles)
                if had_titles:
                    self.assertEqual(titles.read_text(encoding="utf-8"), '{"E9.05":"old"}')

    def test_bad_range_fails_loudly(self):
        for bad in ("", "<range>", "923"):
            with self.subTest(bad=bad):
                r = self.backup(bad)
                self.assertEqual(r.returncode, 1)
                self.assertIn("백업 중단", r.stderr)
        self.assertEqual(self.backups(), [])

    def test_bad_repo_fails_loudly(self):
        env = dict(os.environ, RANGE="0923", REPO=str(self.tmp / "not-a-repo"), RUN=str(self.run_dir))
        r = subprocess.run([sys.executable, "-"], input=self.code, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("백업 중단", r.stderr)
        self.assertEqual(self.backups(), [])

    def test_backup_records_hashes_and_rejects_symlink(self):
        pack = self.notes / "0923"
        pack.mkdir()
        note = pack / "정리노트_0923_A.html"
        note.write_text("old coherent note")
        result = self.backup("0923")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((self.run_dir / "basic-pack-backup.json").read_text())
        import hashlib
        self.assertEqual(record["files"][note.name], hashlib.sha256(note.read_bytes()).hexdigest())
        target = self.tmp / "outside"
        target.write_text("outside original")
        note.unlink()
        note.symlink_to(target)
        result = self.backup("0923")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(note.is_symlink())


class TestCleanupSnippet(unittest.TestCase):
    """SKILL.md 4단계 정리 스니펫이 맨 위와 .assets/ 의 옛 산출물만 지우는지 실제로 실행한다."""

    def test_removes_stale_outputs_in_both_levels(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        m = re.search(r"```bash\npython3 - \"\$RUN/manifest.json\" \"\$REPO/복습노트/<range>\" <<'EOF'\n(.*?)\nEOF\n```", text, re.S)
        self.assertIsNotNone(m, "SKILL.md 4단계 정리 스니펫을 찾지 못함")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "manifest.json").write_text(json.dumps({"range": "0923", "slug": "A", "problems": []}), encoding="utf-8")
            (tmp / "STT").mkdir()
            pack = tmp / "복습노트" / "0923"
            (pack / ".assets" / "figures_0923").mkdir(parents=True)
            for rel in ("정리노트_0923_A.html", "정리노트_0923_Old.html", "복습문제_0923_A-문제.pdf",
                        ".assets/정리노트_0923_A.md", ".assets/정리노트_0923_Old.md", ".assets/문제설명_0923_A.md"):
                (pack / rel).write_text("x", encoding="utf-8")
            backup = re.search(r"RANGE=<range> REPO=… RUN=… python3 - <<'EOF'\n(.*?)\nEOF", text, re.S).group(1)
            r = subprocess.run([sys.executable, "-"], input=backup,
                env=dict(os.environ, RANGE="0923", REPO=str(tmp), RUN=str(tmp)), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([sys.executable, "-", str(tmp / "manifest.json"), str(pack)], input=m.group(1),
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            left = sorted(p.relative_to(pack).as_posix() for p in pack.rglob("*"))
            self.assertEqual(left, [".assets", ".assets/figures_0923", ".assets/문제설명_0923_A.md",
                                    ".assets/정리노트_0923_A.md", "정리노트_0923_A.html"])


    def test_cleanup_preserves_same_prefix_non_owned_and_unrecorded_files(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        backup = re.search(r"RANGE=<range> REPO=… RUN=… python3 - <<'EOF'\n(.*?)\nEOF", text, re.S).group(1)
        cleanup = re.search(r"python3 - \"\$RUN/manifest.json\" \"\$REPO/복습노트/<range>\" <<'EOF'\n(.*?)\nEOF", text, re.S).group(1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, run = tmp / "repo", tmp / "run"
            run.mkdir()
            (repo / "STT").mkdir(parents=True)
            pack = repo / "복습노트/0923"
            (pack / ".assets").mkdir(parents=True)
            owned = ("정리노트_0923_A.html", "정리노트_0923_Old.html", ".assets/정리노트_0923_A.md",
                     ".assets/정리노트_0923_Old.md", "복습문제_0923_Old-문제.pdf", "복습문제_0923_Old-답안.pdf")
            preserved = ("정리노트_0923_Old-feedback.txt", "복습문제_0923_Old-feedback.pdf",
                         ".assets/정리노트_0923_Old-feedback.txt", ".assets/복습문제_0923_Old-답안.pdf",
                         "정리노트_0918_Old.html", ".assets/정리노트_0918_Old.md")
            for rel in (*owned, *preserved):
                (pack / rel).write_text(rel, encoding="utf-8")
            other = repo / "복습노트/0918/정리노트_0918_A.html"
            other.parent.mkdir(); other.write_text("other date", encoding="utf-8")
            result = subprocess.run([sys.executable, "-"], input=backup,
                env=dict(os.environ, RANGE="0923", REPO=str(repo), RUN=str(run)), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads((run / "basic-pack-backup.json").read_text())
            self.assertEqual(set(record["roots"]), set(owned))
            self.assertEqual(set(record["files"]), set(owned))
            self.assertTrue(all((Path(record["backup"]) / rel).read_bytes() == (pack / rel).read_bytes() for rel in owned))
            unrecorded = pack / "정리노트_0923_Unrecorded.html"
            unrecorded.write_text("created after backup", encoding="utf-8")
            manifest = run / "manifest.json"
            manifest.write_text(json.dumps({"range": "0923", "slug": "A", "problems": []}), encoding="utf-8")
            result = subprocess.run([sys.executable, "-", str(manifest), str(pack)], input=cleanup, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(all((pack / rel).read_text(encoding="utf-8") == rel for rel in preserved))
            self.assertEqual(unrecorded.read_text(encoding="utf-8"), "created after backup")
            self.assertEqual(other.read_text(encoding="utf-8"), "other date")
            retained = {"정리노트_0923_A.html", ".assets/정리노트_0923_A.md"}
            self.assertTrue(all((pack / rel).exists() == (rel in retained) for rel in owned))


class TestWhyPageDocs(unittest.TestCase):
    def read(self, rel):
        return (SKILL / rel).read_text(encoding="utf-8")

    def test_manifest_guide_fixes_why_section(self):
        t = self.read("references/manifest-guide.md")
        for s in ('"why"', "why-circuit", "들어가며: 왜 이런 회로를 쓸까", "왜 쓸까"):
            self.assertIn(s, t)

    def test_content_rules_has_why_section(self):
        self.assertIn("## 왜 쓰는가 페이지 (`why-circuit`)", self.read("references/content-rules.md"))

    def test_summary_prompt_collects_motivation(self):
        self.assertIn("## 동기 발언", self.read("references/stt-summary-prompt.md"))

    def test_review_prompt_checks_why(self):
        self.assertIn("why-circuit", self.read("references/review-prompt.md"))

    def test_skill_md_mentions_retrofit(self):
        t = self.read("SKILL.md")
        self.assertIn("scripts/insert_why.py", t)
        self.assertIn("## 기존 팩에 왜 페이지 붙이기", t)


class TestLearningStyleBriefs(unittest.TestCase):
    def test_parent_briefs_include_profile_and_audit(self):
        author = (SKILL / "references/content-rules.md").read_text()
        reviewer = (SKILL / "references/review-prompt.md").read_text()
        for brief in (author, reviewer):
            self.assertIn("<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md", brief)
            self.assertIn("learning_style", brief)
            self.assertIn("핵심 관계", brief)
        self.assertIn("learning-style-audit.json", reviewer)
        skill = SKILL_MD.read_text()
        for required in ("--mode problems", "--mode answers --answer-overlay", "--defer-answer-pdf", "publish_answer.py", "answer-review.json"):
            self.assertIn(required, skill)


if __name__ == "__main__":
    unittest.main()
