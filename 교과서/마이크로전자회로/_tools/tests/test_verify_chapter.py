import io
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_figures import crop_all, figure_filename  # noqa: E402
from make_index import build_index  # noqa: E402
from verify_chapter import main, verify  # noqa: E402

KIND = {"E": "예제", "X": "연습문제", "P": "장말문제"}
FIGURES_YAML = (
    "pdf: ../../book.pdf\n"
    "dpi: 144\n"
    "figures:\n"
    '  "9.2": {pdf_page: 1, bbox: [0, 0, 72, 36]}\n'
)


def make_md(id_, figures=(), depends=(), sections=None):
    prefix, chapter, num = id_[0], id_[1:].split(".")[0], id_.split(".")[1]
    kind = KIND[prefix]
    number = f"{int(chapter)}.{int(num)}"
    fm = ["---", f"id: {id_}", f"kind: {kind}", f'number: "{number}"', 'section: "9.1.1 절"',
          "book_page: 451", "pdf_page: 2"]
    if prefix == "P":
        fm += ["difficulty: 0", "sol: false"]
    fm += ["source_lang: ko"]
    if figures:
        fm += ["figures:"] + [f'  - {{id: "{f}", role: problem, panels: []}}' for f in figures]
    else:
        fm += ["figures: []"]
    fm += [f"depends_on: [{', '.join(depends)}]", "refs: []", "---"]
    if sections is None:
        sections = ["## 조건", "## 구할 것"]
        sections += [f"## 회로 — Fig {f}\n![Fig {f}](../figures/{figure_filename(f)})" for f in figures] \
            or ["## 회로 — 없음 (그림 없는 글 문제)"]
        if prefix == "E":
            sections.append("## 답 (검증용)")
    title = f"# {kind} {number} — 제목 {id_}"
    return "\n".join(fm) + "\n" + title + "\n\n" + "\n\n".join(s + "\n- 내용" for s in sections) + "\n"


def write_md(ch, id_, text=None, **kw):
    path = ch / KIND[id_[0]] / f"{id_}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text is not None else make_md(id_, **kw), encoding="utf-8")
    return path


def make_chapter(root: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.draw_rect(fitz.Rect(10, 10, 40, 30), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(str(root / "book.pdf"))
    ch = root / "ch09"
    (ch / "figures").mkdir(parents=True)
    (ch / "figures" / "figures.yaml").write_text(FIGURES_YAML, encoding="utf-8")
    write_md(ch, "E9.01", figures=["9.2"])
    write_md(ch, "X9.01", figures=["9.2"], depends=["E9.01"])
    write_md(ch, "P9.01")
    crop_all(ch)
    (ch / "README.md").write_text(build_index(ch, "9장 테스트"), encoding="utf-8")
    return ch


class ChapterCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ch = make_chapter(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def assertError(self, *needles, recrop=False):
        errors, _ = verify(self.ch, recrop=recrop)
        self.assertTrue(any(all(n in e for n in needles) for e in errors),
                        f"{needles} 를 담은 오류가 없음: {errors}")


class CleanChapterTest(ChapterCase):
    def test_clean_chapter_passes(self):
        self.assertEqual(verify(self.ch), ([], []))


class NumberingTest(ChapterCase):
    def test_gap_in_problem_numbers(self):
        write_md(self.ch, "P9.03")
        self.assertError("장말문제", "P9.02")

    def test_exercise_without_example(self):
        write_md(self.ch, "X9.02")
        self.assertError("X9.02", "E9.02")

    def test_example_without_exercise_is_info(self):
        write_md(self.ch, "E9.02")
        errors, infos = verify(self.ch)
        self.assertFalse(any("E9.02" in e for e in errors), errors)
        self.assertTrue(any("E9.02" in i and "연습문제 없음" in i for i in infos), infos)


class FigureTest(ChapterCase):
    def add_yaml_line(self, line):
        path = self.ch / "figures" / "figures.yaml"
        path.write_text(path.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")

    def test_unused_figure_in_yaml(self):
        self.add_yaml_line('  "9.5": {pdf_page: 1, bbox: [0, 0, 10, 10]}')
        crop_all(self.ch)
        self.assertError("figures.yaml에만", "9.5")

    def test_md_refs_figure_missing_from_yaml(self):
        write_md(self.ch, "P9.02", figures=["9.7"])
        self.assertError("figures.yaml에 없는", "9.7")

    def test_missing_png(self):
        (self.ch / "figures" / "fig9-02.png").unlink()
        self.assertError("PNG 없음", "fig9-02.png")

    def test_stray_png(self):
        shutil.copy(self.ch / "figures" / "fig9-02.png", self.ch / "figures" / "fig9-99.png")
        self.assertError("figures.yaml에 없는 PNG", "fig9-99.png")

    def test_missing_image_link(self):
        write_md(self.ch, "E9.01", figures=["9.2"],
                 sections=["## 조건", "## 구할 것", "## 회로 — Fig 9.2", "## 답 (검증용)"])
        self.assertError("E9.01", "9.2", "이미지 링크 없음")

    def test_broken_image_link(self):
        text = make_md("P9.02").replace("## 회로 — 없음 (그림 없는 글 문제)",
                                        "## 회로 — 없음 (그림 없는 글 문제)\n![x](../figures/nope.png)")
        write_md(self.ch, "P9.02", text=text)
        self.assertError("P9.02", "깨진 이미지 링크", "nope.png")

    def test_unquoted_figure_id(self):
        self.add_yaml_line("  9.30: {pdf_page: 1, bbox: [0, 0, 10, 10]}")
        self.assertError("따옴표")


class StructureTest(ChapterCase):
    def test_section_order(self):
        write_md(self.ch, "P9.02", sections=["## 구할 것", "## 조건", "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "순서")

    def test_missing_required_section(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "필수 절 없음", "구할 것")

    def test_unknown_section(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 구할 것", "## 메모",
                                             "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "알 수 없는 절", "메모")

    def test_example_without_answer(self):
        write_md(self.ch, "E9.01", figures=["9.2"],
                 sections=["## 조건", "## 구할 것", "## 회로 — Fig 9.2\n![Fig 9.2](../figures/fig9-02.png)"])
        self.assertError("E9.01", "'## 답' 절 없음")

    def test_problem_with_answer(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 구할 것",
                                             "## 회로 — 없음 (그림 없는 글 문제)", "## 답 (검증용)"])
        self.assertError("P9.02", "예제가 아닌데")

    def test_missing_title_line(self):
        text = re.sub(r"^# .*\n", "", make_md("P9.02"), flags=re.M)
        write_md(self.ch, "P9.02", text=text)
        self.assertError("P9.02", "제목 줄")


class RobustnessTest(ChapterCase):
    def test_broken_frontmatter_reported_not_raised(self):
        write_md(self.ch, "P9.02", text="frontmatter 없음\n")
        self.assertError("P9.02.md", "frontmatter")

    def test_empty_chapter_is_error(self):
        empty = self.root / "ch12"
        (empty / "figures").mkdir(parents=True)
        (empty / "figures" / "figures.yaml").write_text("pdf: ../../book.pdf\nfigures:\n", encoding="utf-8")
        errors, _ = verify(empty)
        self.assertIn("문제 md가 없음", errors)


class CliTest(ChapterCase):
    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["verify_chapter.py", *args])
        return code, out.getvalue()

    def test_clean_exit_zero(self):
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 0)
        self.assertIn("오류 0개, 참고 0개", out)

    def test_error_exit_one(self):
        write_md(self.ch, "P9.03")
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 1)
        self.assertIn("ERROR ", out)

    def test_info_only_exit_zero(self):
        write_md(self.ch, "E9.02")
        (self.ch / "README.md").write_text(build_index(self.ch, "9장 테스트"), encoding="utf-8")
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 0)
        self.assertIn("INFO  E9.02", out)

    def test_usage(self):
        self.assertEqual(main(["verify_chapter.py"]), 2)
        self.assertEqual(main(["verify_chapter.py", str(self.root / "없는폴더")]), 2)


if __name__ == "__main__":
    unittest.main()
