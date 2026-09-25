import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mdsub import answer_html, to_html  # noqa: E402


class TestToHtml(unittest.TestCase):
    def test_flat_list(self):
        self.assertEqual(to_html("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")

    def test_nested_list(self):
        self.assertEqual(to_html("- a\n  - b\n  - c\n- d"),
                         "<ul><li>a<ul><li>b</li><li>c</li></ul></li><li>d</li></ul>")

    def test_nested_list_closed_at_end(self):
        self.assertEqual(to_html("- a\n  - b"), "<ul><li>a<ul><li>b</li></ul></li></ul>")

    def test_skipped_indent_is_one_level(self):
        self.assertEqual(to_html("- a\n    - b"), "<ul><li>a<ul><li>b</li></ul></li></ul>")

    def test_continuation_lines_join_item(self):
        md = "- 특성:\n  $$I_D = \\gamma V^3$$\n  $\\gamma$는 계수\n- 다음"
        self.assertEqual(to_html(md),
                         "<ul><li>특성: $$I_D = \\gamma V^3$$ $\\gamma$는 계수</li><li>다음</li></ul>")

    def test_paragraphs(self):
        self.assertEqual(to_html("첫 줄\n이어짐\n\n둘째"), "<p>첫 줄 이어짐</p><p>둘째</p>")

    def test_math_kept_and_escaped(self):
        self.assertEqual(to_html(r"- $a_{1} < b \\ c$ & d"),
                         r"<ul><li>$a_{1} &lt; b \\ c$ &amp; d</li></ul>")

    def test_bold_outside_math_only(self):
        self.assertEqual(to_html("**굵게** $**x**$"), "<p><b>굵게</b> $**x**$</p>")

    def test_empty(self):
        self.assertEqual(to_html(""), "")
        self.assertEqual(to_html("\n\n"), "")


class TestAnswerHtml(unittest.TestCase):
    def test_single_bullet_is_inline(self):
        self.assertEqual(answer_html("- $R \\approx 1$ (식 9.10)\n"), "$R \\approx 1$ (식 9.10)")

    def test_single_line_is_inline(self):
        self.assertEqual(answer_html("$R$"), "$R$")

    def test_many_lines_use_blocks(self):
        self.assertEqual(answer_html("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")


if __name__ == "__main__":
    unittest.main()
