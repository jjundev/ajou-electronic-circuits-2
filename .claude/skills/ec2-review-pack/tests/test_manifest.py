import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest

from _util import MINI_RUN, REPO

import manifest

HAS_WORKBOOK = (REPO / "workbook" / "build_workbook.py").exists()


def mini() -> dict:
    return json.loads((MINI_RUN / "manifest.json").read_text(encoding="utf-8"))


class TestManifest(unittest.TestCase):
    def test_mini_manifest_is_valid(self):
        self.assertEqual(manifest.validate(mini()), [])

    def test_missing_top_level_key(self):
        m = mini()
        del m["problems"]
        self.assertIn("manifest.problems: list 필요", manifest.validate(m))

    def test_review_keys_are_not_required(self):
        # 복습문제 HTML이 없으므로 ML의 review_* / parts 키는 요구하지 않는다.
        for key in ("review_title", "review_intro", "footer_review", "parts"):
            self.assertNotIn(key, manifest.TOP_LEVEL_TYPES)

    def test_bad_range_and_slug(self):
        m = mini()
        m["range"], m["slug"] = "9/21", "한글"
        errors = manifest.validate(m)
        self.assertTrue(any(e.startswith("manifest.range") for e in errors))
        self.assertTrue(any(e.startswith("manifest.slug") for e in errors))

    def test_duplicate_topic_id(self):
        m = mini()
        m["sections"][0]["topics"][1]["id"] = "s1-mean"
        self.assertTrue(any("중복 id: s1-mean" in e for e in manifest.validate(m)))

    def test_unknown_layer(self):
        m = mini()
        m["sections"][0]["topics"][0]["layers"].append("fun")
        self.assertTrue(any("알 수 없는 레이어" in e for e in manifest.validate(m)))

    def test_preview_topic_must_exist(self):
        m = copy.deepcopy(mini())
        m["preview_topic"] = "s9"
        self.assertIn("preview_topic: 토픽 id가 아님: s9", manifest.validate(m))

    def test_problem_anchor_must_be_topic(self):
        m = mini()
        m["problems"][0]["anchor"] = "s9-nope"
        self.assertIn("problems[0].anchor: 없는 토픽: s9-nope", manifest.validate(m))

    def test_problem_id_format(self):
        for bad in ("P9.1", "Q9.01", "2023-1_기말-Q0", "2023-3_기말-Q1", "p9.01"):
            with self.subTest(bad=bad):
                m = mini()
                m["problems"][0]["id"] = bad
                self.assertIn(f"problems[0].id: workbook id 형식 오류: {bad}", manifest.validate(m))

    def test_problem_kind_must_match_id(self):
        m = mini()
        m["problems"][0]["kind"] = "예제"
        self.assertIn("problems[0].kind: P9.01는 장말문제", manifest.validate(m))

    def test_problem_kind_of_each_prefix(self):
        self.assertEqual(manifest.problem_kind("E10.03"), "예제")
        self.assertEqual(manifest.problem_kind("X11.12"), "연습문제")
        self.assertEqual(manifest.problem_kind("P9.40"), "장말문제")
        self.assertEqual(manifest.problem_kind("2021-1_중간-Q7"), "기출")
        self.assertIsNone(manifest.problem_kind("E10.3"))

    def test_nfd_exam_id_is_accepted(self):
        m = mini()
        m["problems"][1]["id"] = unicodedata.normalize("NFD", "2023-1_기말-Q1")
        self.assertEqual(manifest.validate(m), [])

    def test_duplicate_problem(self):
        m = mini()
        m["problems"][1] = dict(m["problems"][0])
        self.assertIn("problems[1].id: 중복 문제: P9.01", manifest.validate(m))

    def test_problem_date_and_why(self):
        m = mini()
        m["problems"][0]["date"] = "9/23"
        m["problems"][0]["why"] = "  "
        errors = manifest.validate(m)
        self.assertIn("problems[0].date: MMDD 형식이어야 함: 9/23", errors)
        self.assertIn("problems[0].why: 빈 문자열", errors)

    def test_too_many_problems(self):
        m = mini()
        m["problems"] = [{"id": f"P9.{i:02d}", "kind": "장말문제", "anchor": "s1-mean", "date": "0101", "why": "x"}
                         for i in range(1, 14)]
        self.assertIn("problems: 최대 12개 (13개)", manifest.validate(m))

    def test_pdf_links_required_when_problems(self):
        m = mini()
        m["links"] = m["links"][:1]
        self.assertIn("links: 복습문제 PDF 링크 필요: 복습문제_0101-0102_Mini_Test-답안.pdf", manifest.validate(m))

    def test_zero_problems_is_valid_without_pdf_links(self):
        m = mini()
        m["problems"], m["links"] = [], []
        self.assertEqual(manifest.validate(m), [])

    def test_zero_problems_rejects_pdf_links(self):
        m = mini()
        m["problems"] = []
        errors = manifest.validate(m)
        self.assertIn("links: 문제가 0개인데 PDF 링크가 있음: 복습문제_0101-0102_Mini_Test-문제.pdf", errors)

    def test_repo_check_finds_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = manifest.validate(mini(), repo=tmp)
        self.assertTrue(any(e.startswith("problems[0].id: 문제 파일 없음:") for e in errors), errors)

    @unittest.skipUnless(HAS_WORKBOOK, "workbook 없음")
    def test_repo_check_passes_on_real_repo(self):
        self.assertEqual(manifest.validate(mini(), repo=REPO), [])

    def test_problem_md_path(self):
        repo = Path("/r")
        self.assertEqual(manifest.problem_md_path(repo, "E10.03"), repo / "교과서/마이크로전자회로/ch10/예제/E10.03.md")
        self.assertEqual(manifest.problem_md_path(repo, "2023-1_기말-Q1"), repo / "from_the_past/md/2023-1_기말/Q1.md")
        with self.assertRaises(ValueError):
            manifest.problem_md_path(repo, "nope")

    def test_load_raises_on_invalid(self):
        m = mini()
        m["problems"][0]["kind"] = "기출"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(manifest.ManifestError) as cm:
                manifest.load(path)
        self.assertIn("problems[0].kind: P9.01는 장말문제", str(cm.exception))

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manifest.main([str(MINI_RUN / "manifest.json")]), 0)
        self.assertEqual(out.getvalue().strip(), "OK")

    def test_cli_with_missing_repo_file_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manifest.main([str(MINI_RUN / "manifest.json"), tmp]), 1)
        self.assertIn("문제 파일 없음", out.getvalue())

    def test_non_dict_top_level(self):
        for value in ([], "x", 3, None):
            self.assertEqual(manifest.validate(value), ["manifest: JSON 객체 필요"])

    def test_non_dict_list_item_is_reported_and_skipped(self):
        m = mini()
        m["problems"].insert(0, "oops")
        m["sessions"].append(7)
        errors = manifest.validate(m)
        self.assertIn("problems[0]: 객체 필요", errors)
        self.assertIn(f"sessions[{len(m['sessions']) - 1}]: 객체 필요", errors)

    def test_non_string_layer_is_reported(self):
        m = mini()
        m["sections"][0]["topics"][0]["layers"].append(["eli5"])
        self.assertTrue(any("layers" in e for e in manifest.validate(m)))

    def test_load_invalid_json_raises_manifest_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(manifest.ManifestError):
                manifest.load(path)
            with self.assertRaises(manifest.ManifestError):
                manifest.load(Path(tmp) / "missing.json")

    def test_cli_invalid_manifest_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "manifest.json"
            bad.write_text("[]", encoding="utf-8")
            for arg in (bad, Path(tmp) / "missing.json"):
                with contextlib.redirect_stdout(io.StringIO()) as out, \
                        contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(manifest.main([str(arg)]), 1)
                self.assertTrue(out.getvalue().strip())
                self.assertNotIn("Traceback", out.getvalue() + err.getvalue())

    def test_cli_usage_exits_2(self):
        for argv in ([], ["a", "b", "c"]):
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(manifest.main(argv), 2)
            self.assertIn("사용법", err.getvalue())

    def test_term_lists_require_nonempty_strings(self):
        for bad in (0.2, 3, None, "", ["x"]):
            with self.subTest(bad=bad):
                m = mini()
                m["sections"][0]["topics"][0]["required_terms"].append(bad)
                m["forbidden_outside_preview"].append(bad)
                errors = manifest.validate(m)
                for where in ("sections[0].topics[0].required_terms[", "forbidden_outside_preview["):
                    self.assertTrue(any(e.startswith(where) and "빈 문자열이 아닌 문자열 필요" in e for e in errors), (where, errors))

    def test_names(self):
        m = mini()
        self.assertEqual(manifest.note_name(m), "정리노트_0101-0102_Mini_Test.html")
        self.assertEqual(manifest.problem_set_name(m), "복습문제_0101-0102_Mini_Test")
        self.assertEqual(manifest.problem_pdf_name(m), "복습문제_0101-0102_Mini_Test-문제.pdf")
        self.assertEqual(manifest.answer_pdf_name(m), "복습문제_0101-0102_Mini_Test-답안.pdf")
        self.assertEqual(manifest.fig_dir_name("0101-0102"), "figures_0101-0102")
        self.assertEqual(manifest.PROBLEMS_TXT, "problems.txt")
        self.assertFalse(hasattr(manifest, "review_name"))


if __name__ == "__main__":
    unittest.main()
