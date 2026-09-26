import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TEXTBOOK  # noqa: E402
from problem import (ProblemError, drop_circuit_lines, example_answer_md, exam_info,  # noqa: E402
                     figures, hints, html_fields, load_problem, solution, strip_markers)

FIGS = ('  - {id: "9.2", role: problem, panels: [a]}\n'
        '  - {id: "9.2", role: problem, panels: [b]}\n'
        '  - {id: "9.13", role: answer, panels: []}\n')

BODY = r"""
## 조건
- 회로: Fig 9.2(a) 바이폴라 캐스코드 전류원
  - 회로 아래 설명 줄
- $Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$ (원문에 없음)

## 구할 것
- 출력 저항 $R_{out}$ (괄호 안은 원문에 없음)

## 회로 — 없음 (테스트)

## 답 (검증용)
- $R_{out} \approx 328.9\ \text{k}\Omega$ (식 9.10)
> 참고: 무시

### 정답 회로 — Fig 9.3
- 무시
"""

EXAM_MD = r"""---
id: 2023-1_기말-Q1
kind: 기출
exam: "2023-1 기말고사"
number: "1"
points: 20
source: "../../2023-1/23-1 기말/기말고사.pdf"
pdf_page: 1
source_lang: ko
figures:
  - {id: "Q1", role: problem, panels: [a, b]}
textbook_chapters: [10, 11]
depends_on: []
refs: []
---
# 기출 2023-1 기말 1 — Miller 정리로 구하는 극점

## 조건
- 회로: 그림 (a), (b)
- $\lambda = 0$ (보조 출처: 손정리 노트)

## 구할 것
- (1) 극점

## 회로 — 없음 (테스트)
"""


def textbook_md(pid="E9.01", kind="예제", figures=FIGS, original="", extra=""):
    chapter, num = pid[1:].split(".")
    number = f"{int(chapter)}.{int(num)}"
    fig_yaml = "figures:\n" + figures if figures else "figures: []\n"
    return ("---\n"
            f"id: {pid}\nkind: {kind}\nnumber: \"{number}\"\n"
            "section: \"9.1.1 전류원으로서의 캐스코드\"\nbook_page: 451\npdf_page: 2\nsource_lang: en\n"
            + fig_yaml
            + "depends_on: []\nrefs: []\n---\n"
            f"# {kind} {number} — 바이폴라 캐스코드 전류원의 출력 저항\n"
            + ("\n" + original if original else "")
            + BODY + extra)


def make_png(path, w, h):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h), False)
    pix.set_rect(pix.irect, (255, 255, 255))
    pix.save(str(path))


class ProblemCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        fig_dir = self.root / "ch09" / "figures"
        fig_dir.mkdir(parents=True)
        (fig_dir / "figures.yaml").write_text("dpi: 144\nfigures: {}\n", encoding="utf-8")
        make_png(fig_dir / "fig9-02.png", 200, 182)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, text, pid="E9.01", kind="예제"):
        path = self.root / "ch09" / kind / f"{pid}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return load_problem(path)


class TestLoad(ProblemCase):
    def test_title_and_id(self):
        p = self.load(textbook_md())
        self.assertEqual(p.id, "E9.01")
        self.assertEqual(p.title, "바이폴라 캐스코드 전류원의 출력 저항")
        self.assertFalse(p.is_exam)

    def test_missing_h1_raises(self):
        with self.assertRaisesRegex(ProblemError, "H1"):
            self.load(textbook_md().replace("# 예제 9.1 — ", "예제 9.1 "))

    def test_invalid_workbook_section_raises(self):
        with self.assertRaisesRegex(ProblemError, "### 답"):
            self.load(textbook_md(extra="\n## 풀이\n### 단계\n- x\n"))

    def test_real_file(self):
        p = load_problem(TEXTBOOK / "ch09" / "예제" / "E9.01.md")
        self.assertEqual(p.title, "바이폴라 캐스코드 전류원의 출력 저항")


class TestHtmlFields(ProblemCase):
    def test_circuit_line_dropped_when_problem_has_figure(self):
        f = html_fields(self.load(textbook_md()))
        self.assertEqual(f["conditions"], r"<ul><li>$Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$</li></ul>")
        self.assertEqual(f["ask"], r"<ul><li>출력 저항 $R_{out}$</li></ul>")

    def test_circuit_line_kept_without_figure(self):
        f = html_fields(self.load(textbook_md(figures="")))
        self.assertEqual(f["conditions"],
                         r"<ul><li>회로: Fig 9.2(a) 바이폴라 캐스코드 전류원<ul><li>회로 아래 설명 줄</li></ul></li>"
                         r"<li>$Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$</li></ul>")

    def test_original_optional(self):
        self.assertNotIn("original", html_fields(self.load(textbook_md())))
        p = self.load(textbook_md(original="## 원문\nRepeat Example 9.1 if $I_1 < 1$.\n"))
        self.assertEqual(html_fields(p)["original"], "<p>Repeat Example 9.1 if $I_1 &lt; 1$.</p>")

    def test_strip_markers(self):
        cases = [
            ("가정 (원문에 없음)", "가정"),
            ("메모 (원문의 메모)", "메모"),
            ("값 (보조 출처: 손정리 노트)", "값"),
            ('설계 (원문에 없음, 원문은 "설계하라"만 적음)', "설계"),
            ("이득 (크기 $|A_v| = 5$로 해석, 원문에 없음)", "이득"),
            ("$f(x)$ 가정 (원문에 없음)", "$f(x)$ 가정"),
            ("$\\text{(원문에 없음)}$", "$\\text{(원문에 없음)}$"),
            ('예제 (E10.09, 원문 표기 "Example 10-9")', '예제 (E10.09, 원문 표기 "Example 10-9")'),
            ("a (원문에 없음)\nb", "a\nb"),
        ]
        for src, want in cases:
            with self.subTest(src=src):
                self.assertEqual(strip_markers(src), want)

    def test_circuit_line_with_value_kept(self):
        kept = [
            "- 회로: Fig 9.79의 전류 거울, $I_1 = 0.5\\ \\text{mA}$를 공급\n- 값",
            "- 회로: Fig 9.50 캐스코드 전류원, 바이어스 전류 $0.5\\ \\text{mA}$로 설계\n- 값",
            "- 회로: Fig 11.91, $Q_3$가 $Q_1$ 바이어스 전류의 75%를 공급\n- 값",
            "- 회로: Fig 9.30\n  - $I_{REF} = 0.2\\ \\text{mA}$\n- 값",
        ]
        for md in kept:
            with self.subTest(md=md):
                self.assertEqual(drop_circuit_lines(md), md)
        self.assertEqual(drop_circuit_lines("- 회로: Fig 9.13(a) CS 단 ($M_1$, 드레인 저항 $R_D$)\n- 값"), "- 값")

    def test_drop_circuit_lines(self):
        self.assertEqual(drop_circuit_lines("- 회로: Fig 1\n  - 설명\n  이어짐\n- 값\n  - 하위"), "- 값\n  - 하위")


class TestFigures(ProblemCase):
    def test_problem_role_only_and_dedup(self):
        figs = figures(self.load(textbook_md()))
        self.assertEqual(len(figs), 1)
        self.assertEqual((figs[0]["w_mm"], figs[0]["h_mm"]), (35.3, 32.1))
        self.assertTrue(figs[0]["src"].startswith("data:image/png;base64,iVBOR"))

    def test_missing_figure_file_raises(self):
        (self.root / "ch09" / "figures" / "fig9-02.png").unlink()
        with self.assertRaisesRegex(ProblemError, "그림 파일 없음"):
            figures(self.load(textbook_md()))

    def test_distinct_crops_kept_same_deduped(self):
        make_png(self.root / "ch09" / "figures" / "fig9-02-a.png", 100, 50)
        figs_yaml = ('  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
                     '  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
                     '  - {id: "9.2", role: problem, panels: [b]}\n')
        figs = figures(self.load(textbook_md(figures=figs_yaml)))
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figs], [(17.6, 8.8), (35.3, 32.1)])

    def test_missing_crop_file_raises(self):
        figs_yaml = '  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
        with self.assertRaisesRegex(ProblemError, "fig9-02-a.png"):
            figures(self.load(textbook_md(figures=figs_yaml)))


class TestHintsAndSolution(ProblemCase):
    def test_hints(self):
        extra = "\n## 힌트\n### 식 9.5\n> 띠: $R = r_O$\n- 캐스코드\n### 참고\n- $a < b$\n"
        self.assertEqual(hints(self.load(textbook_md(extra=extra))), [
            {"label": "식 9.5", "html": "<ul><li>캐스코드</li></ul>", "formula": "R = r_O"},
            {"label": "참고", "html": "<ul><li>$a &lt; b$</li></ul>"},
        ])

    def test_no_hints(self):
        self.assertEqual(hints(self.load(textbook_md())), [])

    def test_solution_section(self):
        extra = "\n## 풀이\n### $g_m$ 계산\n- $g_m = 1/26$\n### 답\n$R \\approx 1$\n"
        self.assertEqual(solution(self.load(textbook_md(extra=extra))), {
            "steps": [{"label": "$g_m$ 계산", "html": "<ul><li>$g_m = 1/26$</li></ul>"}],
            "answer": "$R \\approx 1$",
        })

    def test_example_answer_fallback(self):
        self.assertEqual(solution(self.load(textbook_md())),
                         {"steps": [], "answer": r"$R_{out} \approx 328.9\ \text{k}\Omega$ (식 9.10)"})

    def test_non_example_without_solution_is_none(self):
        p = self.load(textbook_md(pid="X9.01", kind="연습문제"), pid="X9.01", kind="연습문제")
        self.assertIsNone(solution(p))

    def test_example_answer_md_stops_at_subsection_and_code(self):
        self.assertEqual(example_answer_md("- a\n> 참고: b\n\n### 정답 회로\n- c\n"), "- a")
        self.assertEqual(example_answer_md("- a\n```spice\nQ1 a b c npn\n```\n"), "- a")


class TestExam(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        exam_dir = Path(self._tmp.name) / "2023-1_기말"
        (exam_dir / "figures").mkdir(parents=True)
        (exam_dir / "exam.yaml").write_text('exam: "2023-1 기말고사"\n', encoding="utf-8")
        (exam_dir / "figures" / "figures.yaml").write_text("dpi: 144\nfigures: {}\n", encoding="utf-8")
        make_png(exam_dir / "figures" / "fig-Q1.png", 144, 72)
        (exam_dir / "Q1.md").write_text(EXAM_MD, encoding="utf-8")
        self.p = load_problem(exam_dir / "Q1.md")

    def tearDown(self):
        self._tmp.cleanup()

    def test_exam_problem(self):
        self.assertTrue(self.p.is_exam)
        self.assertEqual(self.p.title, "Miller 정리로 구하는 극점")
        self.assertEqual(exam_info(self.p.path.parent)["exam"], "2023-1 기말고사")
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figures(self.p)], [(25.4, 12.7)])
        self.assertEqual(html_fields(self.p)["conditions"], r"<ul><li>$\lambda = 0$</li></ul>")

    def test_exam_crop_rejected(self):
        path = self.p.path
        path.write_text(EXAM_MD.replace("panels: [a, b]}", "panels: [a, b], crop: a}"), encoding="utf-8")
        with self.assertRaisesRegex(ProblemError, "crop"):
            figures(load_problem(path))

    def test_redrawn_replaces_crop_at_crop_width(self):
        fig_dir = self.p.path.parent / "figures"
        crop_src = figures(self.p)[0]["src"]
        (fig_dir / "redrawn").mkdir()
        make_png(fig_dir / "redrawn" / "fig-Q1.png", 432, 288)
        figs = figures(self.p)
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figs], [(25.4, 16.9)])
        self.assertNotEqual(figs[0]["src"], crop_src)

    def test_redrawn_needs_crop_for_size(self):
        fig_dir = self.p.path.parent / "figures"
        (fig_dir / "redrawn").mkdir()
        make_png(fig_dir / "redrawn" / "fig-Q1.png", 432, 288)
        (fig_dir / "fig-Q1.png").unlink()
        with self.assertRaisesRegex(ProblemError, "그림 파일 없음"):
            figures(self.p)


if __name__ == "__main__":
    unittest.main()
