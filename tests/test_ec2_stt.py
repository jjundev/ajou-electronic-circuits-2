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
        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md must exist in .agents/skills/ec2-stt/")
        # Ensure it is NOT linked into .claude/skills (disallow Claude)
        self.assertFalse(CLAUDE_DIR.exists(), ".claude/skills/ec2-stt must NOT exist (disallow Claude)")

        content = skill_md.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "SKILL.md must have frontmatter")
        self.assertIn("name: ec2-stt", content)
        self.assertIn("description:", content)
        self.assertIn("Gemini Only", content, "SKILL.md must specify Gemini Only guard")
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
