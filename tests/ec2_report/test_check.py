import tempfile
import unittest
from pathlib import Path

from _util import REPO
from scripts.ec2_report import check

FIXTURE = Path(__file__).parent / "fixtures" / "probe_roundtrip.md"
PROBE_SRC = Path(__file__).parent / "fixtures" / "probe_source.md"
PROBE_PULLED = Path(__file__).parent / "fixtures" / "probe_pulled.md"

CLEAN = """# 1. Design Problem

**(a) 이득을 구하라.**

**▶** 반쪽 회로에서 $g_m$ 과 출력저항으로 이득을 구한다.

$$
A_v = G_m R_{out}
$$

| MOSFET | W |
|---|---|
| M1 | 65.48 |

![그림 1](figs/01_a.png)
"""


class CheckMarkdownTests(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.dir = Path(self._d.name)

    def tearDown(self):
        self._d.cleanup()

    def run_check(self, text):
        p = self.dir / "r.md"
        p.write_text(text, encoding="utf-8")
        return check.check_markdown(p)

    def errors(self, text):
        return [f for f in self.run_check(text) if f.level == "error"]

    def test_clean_report_has_no_errors(self):
        f = self.run_check(CLEAN)
        self.assertEqual([x for x in f if x.level == "error"], [])
        info = [x for x in f if x.level == "info"]
        self.assertEqual(len(info), 1)
        self.assertIn("1장", info[0].msg)
        self.assertIn("figs/01_a.png", info[0].msg)

    def test_image_outside_figs_is_error(self):
        e = self.errors("![그림 1](../figures/a.png)\n\n![그림 2](figs/sub/b.png)\n")
        self.assertEqual(len(e), 2)
        self.assertIn("figs/", e[0].msg)

    def test_image_index_must_follow_body_order(self):
        ok = "![](figs/01_a.png)\n\n![](figs/02_b.png)\n"
        self.assertEqual(self.errors(ok), [])
        e = self.errors("![](figs/02_b.png)\n\n![](figs/01_a.png)\n\n![](figs/c.png)\n")
        self.assertEqual(len(e), 3)
        self.assertIn("'01_<이름>'", e[0].msg)

    def test_unused_image_in_figs_is_warn(self):
        (self.dir / "figs").mkdir()
        for n in ("01_a.png", "old.png", "notes.txt"):
            (self.dir / "figs" / n).write_bytes(b"")
        warn = [x for x in self.run_check(CLEAN) if x.level == "warn"]
        self.assertEqual(len(warn), 1)
        self.assertIn("old.png", warn[0].msg)
        self.assertNotIn("01_a.png", warn[0].msg)

    def test_old_question_number_ref_is_error(self):
        e = self.errors("1 % 차이는 2-(d)에서 확인한다.\n\n| a | b |\n|---|---|\n| x | 조정, 2-(a) |\n")
        self.assertEqual(len(e), 2)
        self.assertIn("Spice Problem (a)", e[0].msg)
        ok = "Spice Problem (d)에서 확인한다.\n\n$$\nV = 1-(a)\n$$\n\nv1.2-(b) 아님\n"
        self.assertEqual(self.errors(ok), [])

    def test_figure_caption_alt_is_warn(self):
        f = self.run_check("![그림 1. 회로](figs/01_a.png)\n\n![회로도](figs/02_b.png)\n")
        warn = [x for x in f if x.level == "warn"]
        self.assertEqual(len(warn), 1)
        self.assertIn("그림 1.", warn[0].msg)

    def test_wrapped_prose_is_one_error(self):
        e = self.errors("첫 줄 산문\n둘째 줄 산문\n셋째 줄 산문\n")
        self.assertEqual(len(e), 1)
        self.assertIn("2곳", e[0].msg)

    def test_table_cell_mismatch(self):
        e = self.errors("| a | b |\n|---|---|\n| 1 | 2 | 3 |\n")
        self.assertEqual(len(e), 1)
        self.assertIn("셀", e[0].msg)

    def test_table_12_columns(self):
        head = "|" + "|".join(f" c{i} " for i in range(12)) + "|"
        sep = "|" + "|".join("---" for _ in range(12)) + "|"
        row = "|" + "|".join(" 1 " for _ in range(12)) + "|"
        e = self.errors(f"{head}\n{sep}\n{row}\n")
        self.assertEqual(len(e), 1)
        self.assertIn("12열", e[0].msg)

    def test_escaped_pipe_is_not_a_cell(self):
        self.assertEqual(self.errors("| a | b |\n|---|---|\n| x \\| y | 2 |\n"), [])

    def test_raw_html_col0(self):
        e = self.errors("<div>x</div>\n")
        self.assertEqual(len(e), 1)
        self.assertIn("HTML", e[0].msg)

    def test_notion_block_tags_are_not_raw_html(self):
        text = '<table_of_contents color="gray"/>\n\n<empty-block/>\n# 설계 조건\n'
        self.assertEqual(self.errors(text), [])
        self.assertEqual(len(self.errors("<table>\n")), 1)

    def test_h5_heading(self):
        self.assertEqual(len(self.errors("##### 너무 깊다\n")), 1)

    def test_footnote(self):
        self.assertEqual(len(self.errors("본문[^1]\n\n[^1]: 각주\n")), 1)

    def test_backtick_in_heading(self):
        self.assertEqual(len(self.errors("# 1. `Vout` 계산\n")), 1)

    def test_odd_block_math(self):
        e = self.errors("$$\nA\n$$\n\n$$\nB\n")
        self.assertEqual(len(e), 1)
        self.assertIn("$$", e[0].msg)

    def test_odd_inline_dollar(self):
        e = self.errors("이득은 $A_v 이다.\n")
        self.assertEqual(len(e), 1)
        self.assertIn("1행", e[0].where)

    def test_math_single_line_block_and_escaped_dollar(self):
        self.assertEqual(self.errors("$$x$$\n\n가격 \\$5 이고 $g_m$ 이다.\n"), [])

    def test_block_math_inner_lines_are_not_prose(self):
        self.assertEqual(self.errors("$$\nA_v = 1\n\\approx 2\n$$\n"), [])

    def test_ai_words_blocked(self):
        e = self.errors("# 1. 계산\n\nClaude 로 검산했다.\n")
        self.assertEqual(len(e), 1)
        self.assertIn("3행", e[0].msg)

    def test_ai_standalone_blocked(self):
        self.assertEqual(len(self.errors("AI 도움을 받았다.\n")), 1)

    def test_leading_arrow_becomes_toggle(self):
        e = self.errors("▶ 풀이 문단\n")
        self.assertEqual(len(e), 1)
        self.assertIn("토글", e[0].msg)

    def test_bold_or_escaped_arrow_allowed(self):
        self.assertEqual(self.errors("**▶** 풀이\n\n\\▶ 풀이\n\n본문 ▶ 가운데\n"), [])

    def test_code_fence_lines_are_skipped(self):
        text = "넷리스트:\n\n```spice\nM1 x in1 s 0 CMOSN W=65u\nM2 y in2 s 0 CMOSN W=65u\necho $HOME\n<tag>\n```\n"
        self.assertEqual(self.errors(text), [])

    def test_more_ai_words_blocked(self):
        for w in ("GPT 로 검산", "OpenAI", "Anthropic", "Copilot", "인공지능"):
            self.assertEqual(len(self.errors(w + "\n")), 1, w)

    def test_ai_inside_word_allowed(self):
        self.assertEqual(self.errors("MAIN 과 RAIL 은 낱말이다.\n"), [])


class ShapeTests(unittest.TestCase):
    def test_shape_counts_html_tables_and_backtick_math(self):
        s = check.shape(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual((s["tables"], s["inline_math"]), (1, 1))
        self.assertEqual(s["headings"], 1)

    def test_shape_of_clean_source(self):
        s = check.shape(CLEAN)
        self.assertEqual(s, {"headings": 1, "tables": 1, "math_blocks": 1,
                             "inline_math": 1, "images": 1})

    def test_shape_counts_probe_block_math(self):
        s = check.shape(PROBE_PULLED.read_text(encoding="utf-8"))
        self.assertEqual((s["math_blocks"], s["tables"], s["inline_math"]), (1, 1, 7))

    def test_roundtrip_detects_probe_heading_loss(self):
        e = check.roundtrip(PROBE_SRC.read_text(encoding="utf-8"),
                            PROBE_PULLED.read_text(encoding="utf-8"))
        self.assertEqual([x.msg for x in e], ["헤딩 개수가 1개에서 0개로 줄었다"])

    def test_roundtrip_reports_only_losses(self):
        src = "| a |\n|---|\n| 1 |\n\n| b |\n|---|\n| 2 |\n\n$$\nx\n$$\n"
        base = "<table header-row=\"true\">\n<tr>\n<td>a</td>\n</tr>\n</table>\n$$\nx\n$$\n"
        e = check.roundtrip(src, base)
        self.assertEqual(len(e), 1)
        self.assertIn("표", e[0].msg)
        self.assertIn("2개에서 1개", e[0].msg)

    def test_roundtrip_gain_is_not_error(self):
        self.assertEqual(check.roundtrip("본문\n", "# 생김\n본문\n"), [])


class PulledImageTests(unittest.TestCase):
    def test_pulled_images_empty_target(self):
        e = check.check_pulled_images("![회로도]()\n![x](figs/a.png)\n![y](https://n.so/a.png)\n")
        self.assertEqual(len(e), 2)
        self.assertEqual(e[0].msg, "그림 빈자리: 회로도")
        self.assertEqual(str(e[0])[:5], "error")


if __name__ == "__main__":
    unittest.main()
