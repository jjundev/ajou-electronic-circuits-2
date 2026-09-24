import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from make_index import build_index  # noqa: E402

EXAMPLE = """---
id: E9.01
kind: 예제
number: "9.1"
section: "9.1.1 절"
book_page: 451
pdf_page: 2
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: []
refs: []
---
# 예제 9.1 — 출력 저항
"""

EXERCISE = """---
id: X9.01
kind: 연습문제
number: "9.1"
section: "9.1.1 절"
book_page: 452
pdf_page: 3
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: [E9.01]
refs: []
---
# 연습문제 9.1 — Early 전압
"""

PROBLEM = """---
id: P9.10
kind: 장말문제
number: "9.10"
section: "9.1.1 절"
book_page: 486
pdf_page: 21
difficulty: 2
sol: true
source_lang: en
figures:
  - {id: "9.30", role: answer, panels: []}
depends_on: []
refs: []
---
# 장말문제 9.10 — 설계
"""


def make_chapter(root: Path) -> Path:
    ch = root / "ch09"
    for kind, name, text in [("예제", "E9.01", EXAMPLE), ("연습문제", "X9.01", EXERCISE),
                             ("장말문제", "P9.10", PROBLEM)]:
        (ch / kind).mkdir(parents=True, exist_ok=True)
        (ch / kind / f"{name}.md").write_text(text, encoding="utf-8")
    (ch / "figures").mkdir()
    (ch / "figures" / "figures.yaml").write_text("pdf: ../../9장.pdf\nfigures: {}\n", encoding="utf-8")
    return ch


class BuildIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.index = build_index(make_chapter(Path(self.tmp.name)), "9장 테스트")

    def tearDown(self):
        self.tmp.cleanup()

    def test_title_and_counts(self):
        self.assertTrue(self.index.startswith("# 9장 테스트 — 문제 인덱스"))
        self.assertIn("| 합계 | 3 |", self.index)

    def test_dependency_both_directions(self):
        row_e = next(l for l in self.index.splitlines() if l.startswith("| [E9.01]"))
        row_x = next(l for l in self.index.splitlines() if l.startswith("| [X9.01]"))
        self.assertTrue(row_e.endswith("| — | [X9.01](연습문제/X9.01.md) |"))
        self.assertTrue(row_x.endswith("| [E9.01](예제/E9.01.md) | — |"))

    def test_problem_columns(self):
        row = next(l for l in self.index.splitlines() if l.startswith("| [P9.10]"))
        self.assertIn("| ** | SOL | 9.30 답 |", row)

    def test_figure_usage_in_kind_order(self):
        self.assertIn("| [Fig 9.2](figures/fig9-02.png) | E9.01(a), X9.01(a) | — |", self.index)
        self.assertIn("| [Fig 9.30](figures/fig9-30.png) | — | P9.10 |", self.index)


if __name__ == "__main__":
    unittest.main()
