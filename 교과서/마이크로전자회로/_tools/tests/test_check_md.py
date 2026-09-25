import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_md import check_body, check_file, check_netlist_line, main  # noqa: E402
from check_md import check_workbook_sections, hint_label_length, split_sections, split_subsections  # noqa: E402

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


CROP_MD = (VALID_MD.replace("panels: [a]}", "panels: [a], crop: a}")
           .replace("fig9-02.png)", "fig9-02-a.png)"))


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

    def test_symbolic_sizes_and_multiplier_valid(self):
        for line in [
            "Q1 a b c npn area={n}",
            "Q1 a b c npn area=4 m=2",
            "M1 d g s nmos W/L={(W/L)_n} m=3",
            "M2 d g s pmos W/L={(W/L)_p}",
            "M3 d g s nmos m={k}",
        ]:
            with self.subTest(line=line):
                self.assertIsNone(check_netlist_line(line))

    def test_symbolic_sizes_and_multiplier_invalid(self):
        for line in [
            "Q1 a b c npn area={}",
            "M1 d g s nmos W/L={a b}",
            "M1 d g s nmos m=",
        ]:
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
        self.assertTrue(any("sol" in e for e in errors), errors)

    def test_problem_sol_only_missing(self):
        text = (VALID_MD.replace("id: E9.01", "id: P9.01").replace("kind: 예제", "kind: 장말문제")
                .replace("pdf_page: 2\n", "pdf_page: 2\ndifficulty: 1\n"))
        errors, _ = self.run_check(text, rel="장말문제/P9.01.md")
        self.assertFalse(any("difficulty" in e for e in errors), errors)
        self.assertTrue(any("sol" in e for e in errors), errors)

    def test_unquoted_number_is_error(self):
        text = (VALID_MD.replace("id: E9.01", "id: E9.10")
                .replace('number: "9.1"', "number: 9.10"))
        errors, _ = self.run_check(text, rel="예제/E9.10.md")
        self.assertTrue(any("number" in e and "따옴표" in e for e in errors), errors)

    def test_number_must_match_id(self):
        text = VALID_MD.replace('number: "9.1"', 'number: "9.01"')
        errors, _ = self.run_check(text)
        self.assertTrue(any("number" in e and "9.1" in e for e in errors), errors)

    def test_number_two_digit_matches(self):
        text = (VALID_MD.replace("id: E9.01", "id: E9.10")
                .replace('number: "9.1"', 'number: "9.10"'))
        errors, _ = self.run_check(text, rel="예제/E9.10.md")
        self.assertEqual(errors, [])

    def test_figures_not_a_list_is_error(self):
        text = VALID_MD.replace('figures:\n  - {id: "9.2", role: problem, panels: [a]}',
                                'figures: "9.2"')
        errors, _ = self.run_check(text)
        self.assertTrue(any("figures" in e for e in errors), errors)

    def test_figure_item_not_mapping_is_error(self):
        text = VALID_MD.replace('  - {id: "9.2", role: problem, panels: [a]}', '  - "9.2"')
        errors, _ = self.run_check(text)
        self.assertTrue(any("figures" in e for e in errors), errors)

    def test_missing_dependency_is_only_warning(self):
        errors, warnings = self.run_check(VALID_MD.replace("depends_on: []", "depends_on: [E9.15]"))
        self.assertEqual(errors, [])
        self.assertTrue(any("E9.15" in w for w in warnings), warnings)

    def test_unquoted_figure_id_is_error(self):
        text = VALID_MD.replace('{id: "9.2", role: problem, panels: [a]}',
                                "{id: 9.20, role: problem, panels: [a]}")
        errors, _ = self.run_check(text)
        self.assertTrue(any("따옴표" in e for e in errors), errors)

    def run_crop_check(self, text, crop_png=True):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": text})
            if crop_png:
                (ch / "figures" / "fig9-02-a.png").write_bytes(b"\x89PNG")
            return check_file(ch / "예제/E9.01.md", ch)

    def test_crop_file_ok(self):
        self.assertEqual(self.run_crop_check(CROP_MD), ([], []))

    def test_bad_crop_value_is_error(self):
        errors, _ = self.run_crop_check(CROP_MD.replace("crop: a}", "crop: A}"))
        self.assertTrue(any("crop" in e and "형식 오류" in e for e in errors), errors)

    def test_crop_value_with_trailing_newline_is_error(self):
        errors, _ = self.run_crop_check(CROP_MD.replace("crop: a}", 'crop: "a\\n"}'))
        self.assertTrue(any("crop" in e and "형식 오류" in e for e in errors), errors)

    def test_missing_crop_png_is_error(self):
        errors, _ = self.run_crop_check(CROP_MD, crop_png=False)
        self.assertTrue(any("그림 파일 없음" in e and "fig9-02-a.png" in e for e in errors), errors)

    def test_crop_on_answer_entry_is_error(self):
        text = CROP_MD.replace('panels: [a], crop: a}',
                               'panels: [a], crop: a}\n  - {id: "9.2", role: answer, panels: [b], crop: a}')
        errors, _ = self.run_crop_check(text)
        self.assertIn("그림 9.2 role answer 항목에는 crop을 달지 않음", errors)


NO_CIRCUIT_SECTION = """## 회로 — Fig 9.2(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스
- 표시: R_out 화살표
- 배치: 위→아래 Q1, Q2

![Fig 9.2](../figures/fig9-02.png)
"""

ANSWER_CIRCUIT = """### 정답 회로 — Fig 9.2
```spice
Q1  out  Vb1  n1  npn
```
- 단자: Vb1 = 이상적 DC 바이어스
- 표시: 없음
- 배치: Q1 하나

![Fig 9.2](../figures/fig9-02.png)
"""


class NoCircuitTest(unittest.TestCase):
    def run_check(self, text):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": text})
            return check_file(ch / "예제/E9.01.md", ch)

    def test_no_circuit_without_spice_is_ok(self):
        text = VALID_MD.replace(NO_CIRCUIT_SECTION, "## 회로 — 없음 (설계 문제, 그림은 풀이에만 있음)\n")
        self.assertNotIn("```spice", text)
        errors, _ = self.run_check(text)
        self.assertEqual(errors, [])

    def test_no_circuit_needs_reason(self):
        text = VALID_MD.replace(NO_CIRCUIT_SECTION, "## 회로 — 없음\n")
        errors, _ = self.run_check(text)
        self.assertTrue(any("이유" in e for e in errors), errors)

    def test_spice_under_no_circuit_is_error(self):
        text = VALID_MD.replace("## 회로 — Fig 9.2(a)", "## 회로 — 없음 (설계 문제)")
        errors, _ = self.run_check(text)
        self.assertTrue(any("없음" in e and "spice" in e for e in errors), errors)

    def test_no_circuit_example_with_answer_circuit_is_ok(self):
        text = (VALID_MD.replace(NO_CIRCUIT_SECTION, "## 회로 — 없음 (설계 문제, 그림은 풀이에만 있음)\n")
                + "\n" + ANSWER_CIRCUIT)
        errors, _ = self.run_check(text)
        self.assertEqual(errors, [])


class MainTest(unittest.TestCase):
    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            ok = make_chapter(Path(t) / "ok", {"예제/E9.01.md": VALID_MD})
            bad = make_chapter(Path(t) / "bad", {"예제/E9.01.md": VALID_MD}, with_png=False)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["check_md.py", str(ok)]), 0)
                self.assertEqual(main(["check_md.py", str(bad)]), 1)
                self.assertEqual(main(["check_md.py"]), 2)

    def test_missing_chapter_dir_returns_2(self):
        with tempfile.TemporaryDirectory() as t:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main(["check_md.py", str(Path(t) / "nope")]), 2)
            self.assertIn("nope", err.getvalue())

    def test_malformed_file_does_not_stop_run(self):
        broken = VALID_MD.replace("id: E9.01", "id: E9.02").replace('number: "9.1"', 'number: "9.2"')
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": VALID_MD, "예제/E9.02.md": broken})
            out = io.StringIO()
            with patch("check_md.check_file", side_effect=[([], []), RuntimeError("boom")]), \
                    redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["check_md.py", str(ch)]), 1)
            text = out.getvalue()
            self.assertIn("검사 중 예외", text)
            self.assertIn("E9.02.md", text)
            self.assertIn("2개 파일, 오류 1개", text)

    def test_figures_string_reported_not_crash(self):
        broken = (VALID_MD.replace("id: E9.01", "id: E9.02").replace('number: "9.1"', 'number: "9.2"')
                  .replace('figures:\n  - {id: "9.2", role: problem, panels: [a]}', 'figures: "9.2"'))
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": VALID_MD, "예제/E9.02.md": broken})
            out = io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["check_md.py", str(ch)]), 1)
            text = out.getvalue()
            self.assertIn("2개 파일", text)
            self.assertNotIn("E9.01.md:", text)
            self.assertIn("E9.02.md", text)


BODY_NO_ANSWER = """# 기출 2021-1 중간 2 — 테스트

## 조건
- I_D = 1 mA

## 구할 것
- (1) R_out

## 회로 — 그림
```spice
M1  out  Vin  0  nmos
```
- 단자: Vin = 입력 (개방 원)
- 표시: 노드 라벨 Vin
- 배치: M1 하나
"""


class CheckBodyTest(unittest.TestCase):
    def test_exam_kind_needs_no_answer(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(check_body(BODY_NO_ANSWER, Path(t) / "Q2.md", "기출"), [])

    def test_example_kind_needs_answer(self):
        with tempfile.TemporaryDirectory() as t:
            errors = check_body(BODY_NO_ANSWER, Path(t) / "E9.01.md", "예제")
        self.assertIn("예제에 절 누락: ## 답 (검증용)", errors)

    def test_missing_bullet_reported(self):
        body = BODY_NO_ANSWER.replace("- 배치: M1 하나\n", "")
        with tempfile.TemporaryDirectory() as t:
            errors = check_body(body, Path(t) / "Q2.md", "기출")
        self.assertTrue(any("'- 배치:' bullet 없음" in e for e in errors), errors)


WB_BASE = """# 연습문제 9.1 — 제목

## 조건
- a

## 구할 것
- b

## 회로 — 없음 (글 문제)
"""
WB_ORIGINAL = "## 원문\nRepeat Example 9.1.\n\n"
WB_HINTS = "\n## 힌트\n### 식 9.5\n> 띠: $R = r_O$\n- 캐스코드\n"
WB_SOLUTION = "\n## 풀이\n### 소신호\n- $g_m$\n### 답\n$R \\approx 1$\n"


def wb_body(original=True, hints=True, solution=True):
    head, rest = WB_BASE.split("\n\n", 1)
    body = head + "\n\n" + (WB_ORIGINAL if original else "") + rest
    return body + (WB_HINTS if hints else "") + (WB_SOLUTION if solution else "")


class TestWorkbookSections(unittest.TestCase):
    def assert_error(self, body, fragment):
        errors = check_workbook_sections(body)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_all_sections(self):
        self.assertEqual(check_workbook_sections(wb_body()), [])

    def test_valid_without_workbook_sections(self):
        self.assertEqual(check_workbook_sections(wb_body(False, False, False)), [])

    def test_original_must_be_first(self):
        self.assert_error(WB_BASE.replace("## 구할 것", WB_ORIGINAL + "## 구할 것"), "## 원문")

    def test_hint_after_solution_rejected(self):
        self.assert_error(WB_BASE + WB_SOLUTION + WB_HINTS, "## 힌트, ## 풀이")

    def test_section_after_hints_rejected(self):
        self.assert_error(WB_BASE + WB_HINTS + "\n## 상속·참조\n- x\n", "## 힌트, ## 풀이")

    def test_empty_section_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n", "비어 있음")

    def test_solution_must_end_with_answer(self):
        self.assert_error(WB_BASE + "\n## 풀이\n### 소신호\n- x\n", "### 답")

    def test_two_answers_rejected(self):
        self.assert_error(WB_BASE + "\n## 풀이\n### 답\n- x\n### 답\n- y\n", "### 답")

    def test_subsection_without_body(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식 9.5\n### 식 9.7\n- y\n", "### 식 9.5: 내용 없음")

    def test_text_before_first_subsection(self):
        self.assert_error(WB_BASE + "\n## 풀이\n먼저\n### 답\n- x\n", "첫 ### 소절 앞")

    def test_bad_formula_line(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식\n> 띠: R = r_O\n- x\n", "띠 식 줄")

    def test_two_strip_lines_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식\n> 띠: $a$\n> 띠: $b$\n- x\n", "하나만")

    def test_indented_strip_line_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 반회로\n- 대칭\n  > 띠: $R = r_O$\n", "들여 쓰지")

    def test_hint_label_too_long_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### " + "가" * 25 + "\n- x\n", "24자까지")

    def test_hint_label_math_counts_visible_chars(self):
        body = WB_BASE + "\n## 힌트\n### $C_{\\mu}$를 밀러로 입력과 출력에 나눈다\n- x\n"
        self.assertEqual(check_workbook_sections(body), [])
        self.assertEqual(hint_label_length("$C_{\\mu}$를 밀러로 입력과 출력에 나눈다"), 19)
        self.assertEqual(hint_label_length("$I = 1\\ \\text{mA}$"), 5)

    def test_three_hints_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 가\n- x\n### 나\n- y\n### 다\n- z\n", "2개까지")

    def test_duplicate_section(self):
        self.assert_error(WB_BASE + WB_HINTS + WB_HINTS, "두 번")

    def test_split_sections_and_subsections(self):
        self.assertEqual(split_sections(wb_body())[0], ("원문", "Repeat Example 9.1."))
        self.assertEqual(split_subsections("앞\n### a\nx\n### b\ny"), [("", "앞"), ("a", "x"), ("b", "y")])

    def test_check_body_reports_workbook_errors(self):
        errors = check_body(WB_BASE + "\n## 풀이\n### 소신호\n- x\n", Path("X9.01.md"), "연습문제")
        self.assertTrue(any("### 답" in e for e in errors), errors)

    def test_original_author_marker_rejected(self):
        body = wb_body().replace("Repeat Example 9.1.", "Repeat Example 9.1 (원문에 없음).")
        self.assert_error(body, "작성자 표시")

    def test_original_single_emphasis_rejected(self):
        self.assert_error(wb_body().replace("Repeat Example 9.1.", "a *higher* gain"), "기울임")

    def test_original_bold_and_math_star_allowed(self):
        body = wb_body().replace("Repeat Example 9.1.", "a **higher** gain with $V^*$ and $a * b$.")
        self.assertEqual(check_workbook_sections(body), [])

    def test_original_subsection_and_image_rejected(self):
        body = wb_body().replace("Repeat Example 9.1.", "Text.\n![Fig](a.png)\n### (a)\nMore.")
        errors = check_workbook_sections(body)
        self.assertTrue(any("이미지" in e for e in errors), errors)
        self.assertTrue(any("### 소절" in e for e in errors), errors)

    def test_original_marker_mid_parenthesis_rejected(self):
        body = wb_body().replace("Repeat Example 9.1.", "Find the gain (see 원문의 Fig. 9.3 caption).")
        self.assert_error(body, "작성자 표시")


if __name__ == "__main__":
    unittest.main()
