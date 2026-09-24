import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_md import check_file, check_netlist_line, main  # noqa: E402

VALID_MD = """---
id: E9.01
kind: 예제
number: "9.1"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 451
pdf_page: 2
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: []
refs: ["식 9.7"]
---
# 예제 9.1 — 테스트

## 조건
- I_C = 1 mA

## 구할 것
- R_out

## 회로 — Fig 9.2(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스
- 표시: R_out 화살표
- 배치: 위→아래 Q1, Q2

![Fig 9.2](../figures/fig9-02.png)

## 답 (검증용)
- 328.9 kΩ
"""


def make_chapter(root: Path, files: dict, with_png: bool = True) -> Path:
    ch = root / "ch09"
    (ch / "figures").mkdir(parents=True)
    if with_png:
        (ch / "figures" / "fig9-02.png").write_bytes(b"\x89PNG")
    for rel, text in files.items():
        p = ch / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return ch


class NetlistLineTest(unittest.TestCase):
    def test_valid_lines(self):
        for line in [
            "Q1 out Vb1 n1 npn",
            "QR1 X X 0 npn area=4",
            "Q2 X Vb2 VCC pnp",
            "M4 n3 Vb3 VDD pmos W/L=20/0.18",
            "IREF VCC X 0.2mA",
            "RP Vb1 n1",
            "R1 VREF n1 {R_1}",
            "VB 0 n3",
            "X1 0 n1 V1 opamp",
            'X1 n1 0 box "Circuit"',
            "* 주석 줄",
            "Q1 a b c npn   ; 뒤 주석",
            "",
        ]:
            with self.subTest(line=line):
                self.assertIsNone(check_netlist_line(line))

    def test_invalid_lines(self):
        for line in ["Q1 a b npn", "M1 d g s nfet", "Z1 a b", "X1 a b opamp", "Q1 a b c npn area=x"]:
            with self.subTest(line=line):
                self.assertIsNotNone(check_netlist_line(line))


class CheckFileTest(unittest.TestCase):
    def run_check(self, text, rel="예제/E9.01.md", with_png=True):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {rel: text}, with_png=with_png)
            return check_file(ch / rel, ch)

    def test_valid_file_has_no_errors(self):
        self.assertEqual(self.run_check(VALID_MD), ([], []))

    def test_missing_frontmatter_key(self):
        errors, _ = self.run_check(VALID_MD.replace("pdf_page: 2\n", ""))
        self.assertTrue(any("pdf_page" in e for e in errors), errors)

    def test_filename_must_match_id(self):
        errors, _ = self.run_check(VALID_MD, rel="예제/E9.02.md")
        self.assertTrue(any("파일명" in e for e in errors), errors)

    def test_folder_must_match_kind(self):
        errors, _ = self.run_check(VALID_MD, rel="장말문제/E9.01.md")
        self.assertTrue(any("폴더" in e for e in errors), errors)

    def test_bad_netlist_line(self):
        errors, _ = self.run_check(VALID_MD.replace("Q2  n1   Vb2  0   npn", "Q2  n1   Vb2  npn"))
        self.assertTrue(any("넷리스트 문법 오류" in e for e in errors), errors)

    def test_missing_layout_bullet(self):
        errors, _ = self.run_check(VALID_MD.replace("- 배치: 위→아래 Q1, Q2\n", ""))
        self.assertTrue(any("- 배치:" in e for e in errors), errors)

    def test_missing_image_and_figure(self):
        errors, _ = self.run_check(VALID_MD, with_png=False)
        self.assertTrue(any("이미지 없음" in e for e in errors), errors)
        self.assertTrue(any("그림 파일 없음" in e for e in errors), errors)

    def test_example_needs_answer_section(self):
        errors, _ = self.run_check(VALID_MD.split("## 답 (검증용)")[0])
        self.assertTrue(any("## 답 (검증용)" in e for e in errors), errors)

    def test_problem_needs_difficulty_and_sol(self):
        text = VALID_MD.replace("id: E9.01", "id: P9.01").replace("kind: 예제", "kind: 장말문제")
        errors, _ = self.run_check(text, rel="장말문제/P9.01.md")
        self.assertTrue(any("difficulty" in e for e in errors), errors)

    def test_missing_dependency_is_only_warning(self):
        errors, warnings = self.run_check(VALID_MD.replace("depends_on: []", "depends_on: [E9.15]"))
        self.assertEqual(errors, [])
        self.assertTrue(any("E9.15" in w for w in warnings), warnings)


class MainTest(unittest.TestCase):
    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            ok = make_chapter(Path(t) / "ok", {"예제/E9.01.md": VALID_MD})
            bad = make_chapter(Path(t) / "bad", {"예제/E9.01.md": VALID_MD}, with_png=False)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check_md.py", str(ok)]), 0)
                self.assertEqual(main(["check_md.py", str(bad)]), 1)
                self.assertEqual(main(["check_md.py"]), 2)


if __name__ == "__main__":
    unittest.main()
