import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents/skills/ec2-stt"
CLAUDE_DIR = ROOT / ".claude/skills/ec2-stt"

class Ec2SttTests(unittest.TestCase):
    def setUp(self):
        import sys
        scripts_dir = str(SKILL_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

    def test_01_skill_entrypoints_and_metadata(self):
        import yaml

        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md must exist in .agents/skills/ec2-stt/")
        # Ensure it is NOT linked into .claude/skills (disallow Claude)
        self.assertFalse(CLAUDE_DIR.exists(), ".claude/skills/ec2-stt must NOT exist (disallow Claude)")

        content = skill_md.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "SKILL.md must have frontmatter")

        # Ensure frontmatter is valid YAML and parsed cleanly
        parts = content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "SKILL.md must have valid frontmatter delimiters")
        data = yaml.safe_load(parts[1])
        self.assertIsInstance(data, dict, "Frontmatter must be a valid YAML dictionary")
        self.assertEqual(data.get("name"), "ec2-stt")
        self.assertIn("description", data)
        self.assertIsInstance(data["description"], str)
        self.assertIn("Gemini Only", data["description"], "description must specify Gemini Only guard")

        self.assertIn("Model Compatibility Gate", content, "SKILL.md must contain Model Compatibility Gate")
        self.assertIn("STT/<MMDD> 전회2.md", content, "SKILL.md must document standard output path")

    def test_02_parse_date(self):
        from infer_context import parse_date

        self.assertEqual(parse_date("20261002_전회2.m4a"), "1002")
        self.assertEqual(parse_date("1002 전회2.mp3"), "1002")
        self.assertEqual(parse_date("1002.m4a"), "1002")
        self.assertEqual(parse_date("녹음_0923.wav"), "0923")
        self.assertEqual(parse_date("/path/to/2026-0930-class.m4a"), "0930")
        self.assertEqual(parse_date("audio.m4a", date_override="1002"), "1002")

        with self.assertRaises(ValueError):
            parse_date("audio_without_date.m4a")

    def test_03_infer_chapter(self):
        from infer_context import infer_chapter

        # 0909 covers Chapter 9 (Cascode)
        ch_0909 = infer_chapter(ROOT, "0909")
        self.assertEqual(ch_0909, 9)

        # 0923 covers Chapter 10 (Differential Amp)
        ch_0923 = infer_chapter(ROOT, "0923")
        self.assertEqual(ch_0923, 10)

        # 1002 covers Chapter 10 (Differential Amp)
        ch_1002 = infer_chapter(ROOT, "1002")
        self.assertEqual(ch_1002, 10)

        # 1014 covers Chapter 11 (Frequency Response)
        ch_1014 = infer_chapter(ROOT, "1014")
        self.assertEqual(ch_1014, 11)

    def test_03b_infer_chapters_at_chapter_switch(self):
        import tempfile
        from infer_context import infer_chapters

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            assets = repo / "복습노트" / "1016" / ".assets"
            assets.mkdir(parents=True)
            (assets / "정리노트_1016_Miller_High_Frequency_Models.md").write_text("x", encoding="utf-8")
            lec = repo / "강의노트"
            lec.mkdir()
            (lec / "2026F_Lec5_FrequencyResponse_rev4.pdf").write_bytes(b"")

            # 새 단원 강의노트가 없으면 복습노트 단원만
            self.assertEqual(infer_chapters(repo, "1028"), [11])

            # 새 단원 강의노트가 올라오고 복습노트가 아직 없으면 두 단원 모두
            (lec / "2026F_Lec6_Ch12_Feedback_rev1.pdf").write_bytes(b"")
            self.assertEqual(infer_chapters(repo, "1104"), [11, 12])

            # 복습노트가 있는 날짜는 그 단원 그대로
            self.assertEqual(infer_chapters(repo, "1016"), [11])

    def test_04_extract_terms(self):
        from infer_context import extract_chapter_terms

        terms = extract_chapter_terms(ROOT, chapter=10)
        self.assertIsInstance(terms, list)
        self.assertGreater(len(terms), 10)
        term_text = " ".join(terms)
        self.assertTrue(any(k in term_text for k in ["차동", "디퍼렌셜", "gm", "하프", "버추얼", "테일"]))

    def test_05_build_stt_prompt(self):
        from infer_context import build_stt_prompt

        prompt = build_stt_prompt(
            chapter=10,
            chapter_title="Differential Amplifiers",
            terms=["디퍼렌셜 페어", "하프 서킷", "gm", "테일 커런트"]
        )
        self.assertIn("전자회로2", prompt)
        self.assertIn("권익진 교수님", prompt)
        self.assertIn("10장", prompt)
        self.assertIn("디퍼렌셜", prompt)
        self.assertIn("캐스코드", prompt)  # Common error correction rule
        self.assertIn("버추얼 그라운드", prompt)

    def test_05b_frequency_response_terms_and_rules(self):
        from infer_context import extract_chapter_terms, build_stt_prompt

        terms = extract_chapter_terms(ROOT, chapter=11)
        # Lec5 slide titles, not a dump of long English words
        self.assertTrue(any("Source Follower" in t for t in terms))
        self.assertNotIn("applicability", terms)
        self.assertNotIn("Identification", terms)

        prompt = build_stt_prompt(11, "Frequency Response", terms)
        self.assertIn("11장", prompt)
        self.assertIn("C_GS", prompt)
        self.assertIn("보드 플롯", prompt)

    def test_05c_feedback_chapter_seeded(self):
        from infer_context import extract_chapter_terms, build_stt_prompt

        terms = extract_chapter_terms(ROOT, chapter=12)
        self.assertIn("루프 게인", terms)
        self.assertIn("이득 둔감화", terms)

        prompt = build_stt_prompt([11, 12], "11장 주파수 응답 / 12장 귀환", terms)
        self.assertIn("션트", prompt)
        self.assertIn("C_GS", prompt)  # 11장 규칙도 함께

    def test_06_merge_transcripts(self):
        import tempfile
        from merge_transcripts import merge_transcripts

        with tempfile.TemporaryDirectory() as tmpdir:
            part1 = Path(tmpdir) / "1002 전회2_part01.md"
            part2 = Path(tmpdir) / "1002 전회2_part02.md"
            part1.write_text("첫 번째 파트 발화 내용입니다.\n\n디퍼렌셜 페어에 대해 설명합니다.\n", encoding="utf-8")
            part2.write_text("두 번째 파트 발화 내용입니다.\n\n하프 서킷으로 등가 해석을 수행합니다.\n", encoding="utf-8")

            out_file = Path(tmpdir) / "1002 전회2.md"
            res = merge_transcripts(
                target_dir=tmpdir,
                prefix="1002 전회2",
                out_file=str(out_file),
                keep_parts=True,
                group_parts=1,
            )
            self.assertTrue(out_file.is_file())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("# 1002 전회2 전체 오디오 전사본", content)
            self.assertIn("## Part 01", content)
            self.assertIn("## Part 02", content)
            self.assertIn("디퍼렌셜 페어에 대해 설명합니다.", content)
            self.assertIn("하프 서킷으로 등가 해석을 수행합니다.", content)

if __name__ == "__main__":
    unittest.main()
