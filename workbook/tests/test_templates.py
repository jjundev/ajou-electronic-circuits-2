import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TEMPLATES  # noqa: E402

PLACEHOLDER = "__WORKBOOK_DATA__"
EQ_SECTION_START = "/* ---------- 등식 줄바꿈 ---------- */"
EQ_SECTION_END = "/* ---------- 쪽 틀과 헤더 (공용) ---------- */"


def read(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def equation_section(name):
    """템플릿의 '등식 줄바꿈' 절(헤더 주석부터 다음 절 헤더 직전까지)."""
    t = read(name)
    for marker in (EQ_SECTION_START, EQ_SECTION_END):
        if t.count(marker) != 1:
            raise AssertionError(f"{name}: 절 표식 {marker!r}이 {t.count(marker)}번 있음 (1번이어야 함)")
    return t[t.index(EQ_SECTION_START):t.index(EQ_SECTION_END)]


# 절 코드를 stdin으로 받아 breakEquations만 꺼내고, 사례별 결과를 JSON으로 돌려준다
NODE_RUNNER = r"""
const fs = require('fs');
const { section, cases } = JSON.parse(fs.readFileSync(0, 'utf8'));
const { breakEquations } = new Function(section + '\nreturn { breakEquations };')();
process.stdout.write(JSON.stringify(cases.map(breakEquations)));
"""

# (이름, breakEquations 입력 HTML, 기대하는 \begin{aligned} 수)
BREAK_CASES = [
    ("미리 정렬한 식",
     r"<p>$$\begin{aligned} A_v &amp;= -g_m (R_D \parallel r_o) \\ &amp;\approx -10 \end{aligned}$$</p>", 1),
    ("\\\\ 줄바꿈만 있는 식",
     r"<p>$$A_v = -g_m (R_D \parallel r_o) \\ \approx -2\,\text{mS}\cdot 5\,\text{k}\Omega$$</p>", 0),
    ("&amp; 정렬만 있는 식",
     r"<p>$A_v &amp;= -g_m (R_D \parallel r_o) = -2\,\text{mS}\cdot 5\,\text{k}\Omega$</p>", 0),
    ("40자 넘는 보통 등식",
     r"<p>$A_v = -g_m (R_D \parallel r_o) \approx -2\,\text{mS}\cdot 5\,\text{k}\Omega$</p>", 1),
    ("&lt;가 든 등식",
     r"<p>$V_{GS} - V_{TH} &lt; V_{DS} = 1.2\,\text{V} - 0.4\,\text{V} = 0.8\,\text{V}$</p>", 1),
]


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

    def test_hint_entry_shows_kind(self):
        # 한 장 안에서 예제·연습문제·장말문제 번호가 겹친다(예: 10.12). Hint 쪽 항목은 종류를 붙여 구분한다
        t = read("answer.html")
        self.assertIn("const KIND_SHORT = { '예제': '예제', '연습문제': '연습', '장말문제': '문제', '기출': '문항' };", t)
        self.assertIn("txt('a', 'hint-entry-num', `${KIND_SHORT[p.kind] || ''} ${p.number}`.trim())", t)

    def test_equation_section_identical(self):
        # 한쪽만 고치면 다른 쪽에 같은 버그가 남는다(36606b69는 answer.html만 고쳤다)
        self.maxDiff = None
        self.assertEqual(
            equation_section("problem.html"), equation_section("answer.html"),
            "문제지·답안 템플릿의 등식 줄바꿈 절은 똑같아야 한다. 한쪽을 고쳤다면 다른 쪽에도 같이 고친다.")


@unittest.skipUnless(shutil.which("node"), "node 없음")
class TestBreakEquations(unittest.TestCase):
    """작성자가 이미 나눈 식은 다시 나누지 않고, 긴 보통 등식만 관계 기호마다 나눈다."""

    def run_cases(self, name):
        payload = json.dumps({"section": equation_section(name), "cases": [c[1] for c in BREAK_CASES]})
        result = subprocess.run(["node", "-e", NODE_RUNNER], input=payload,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_break_equations(self):
        for name in ("problem.html", "answer.html"):
            outputs = self.run_cases(name)
            for (label, src, aligned), out in zip(BREAK_CASES, outputs):
                with self.subTest(template=name, case=label):
                    self.assertEqual(out.count(r"\begin{aligned}"), aligned, out)
                    if aligned == 0 or label == "미리 정렬한 식":
                        self.assertIn(src[3:-4].strip("$"), out)    # 식 본문이 그대로 남는다
            plain = outputs[3]
            with self.subTest(template=name, case="나뉜 관계 기호"):
                self.assertIn(r"&amp;=", plain)
                self.assertIn(r"&amp;\approx", plain)


if __name__ == "__main__":
    unittest.main()
