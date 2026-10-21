import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_workbook  # noqa: E402
from assemble import Selection  # noqa: E402
from render import RenderError  # noqa: E402


class BuildCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.build = Path(self._tmp.name) / "build"
        self.pdf = Path(self._tmp.name) / "pdf"

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = build_workbook.main(["build_workbook.py", *argv,
                                        "--build-dir", str(self.build), "--pdf-dir", str(self.pdf)])
        return code, out.getvalue(), err.getvalue()

    def read_json(self, name):
        return json.loads((self.build / name).read_text(encoding="utf-8"))


class TestJsonOnly(BuildCase):
    def test_ids(self):
        code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t", "--json-only")
        self.assertEqual(code, 0, err)
        for name in ("t-문제.json", "t-문제.html", "t-답안.json", "t-답안.html"):
            self.assertTrue((self.build / name).exists(), name)
        self.assertEqual(self.read_json("t-문제.json")["meta"]["total"], 2)
        self.assertEqual(self.read_json("t-답안.json")["meta"]["title"], "t 답안")
        self.assertFalse(self.pdf.exists())

    def test_chapter(self):
        code, _, err = self.run_cli("ch09", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read_json("ch09-문제.json")["meta"]["total"], 110)

    def test_all(self):
        code, _, err = self.run_cli("--all", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(list(self.build.glob("*.json"))), 32)   # 장 3 + 기출 13, 각각 문제·답안


class TestErrors(BuildCase):
    def test_unknown_target_exit_2(self):
        code, _, err = self.run_cli("ch99", "--json-only")
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_bad_id_exit_2(self):
        code, _, err = self.run_cli("--ids", "Z1", "--name", "t", "--json-only")
        self.assertEqual(code, 2)
        self.assertIn("Z1", err)

    def test_target_required_exactly_once(self):
        for argv in ([], ["ch09", "--all"], ["--ids", "E9.01"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.run_cli(*argv)

    def test_md_error_exit_1(self):
        broken = Path(self._tmp.name) / "E9.01.md"
        broken.write_text('---\nid: E9.01\nkind: 예제\nnumber: "9.1"\n---\n본문만\n', encoding="utf-8")
        with patch.object(build_workbook, "selections", return_value=[Selection("bad", "bad", 0, [broken])]):
            code, _, err = self.run_cli("ch09", "--json-only")
        self.assertEqual(code, 1)
        self.assertIn(str(broken), err)

    def test_overflow_exit_1(self):
        with patch.object(build_workbook, "render_pdf", return_value=["P9.05"]):
            code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t")
        self.assertEqual(code, 1)
        self.assertIn("OVERFLOW t-문제: P9.05", err)
        self.assertIn("OVERFLOW t-답안: P9.05", err)

    def test_render_error_exit_1(self):
        with patch.object(build_workbook, "render_pdf", side_effect=RenderError("크롬 없음")):
            code, _, err = self.run_cli("--ids", "E9.01", "--name", "t")
        self.assertEqual(code, 1)
        self.assertIn("ERROR t: 크롬 없음", err)


class TestAnswerModes(BuildCase):
    def test_answers_mode_leaves_problem_pdf_untouched(self):
        self.pdf.mkdir()
        self.build.mkdir()
        original = {}
        for root, extensions in [(self.pdf, ['pdf']), (self.build, ['json','html'])]:
            for ext in extensions:
                path = root / f't-문제.{ext}'
                path.write_bytes(b'original problem output')
                original[path] = (path.read_bytes(), path.stat().st_mtime_ns)
        code, _, err = self.run_cli('--ids','E9.05','--name','t','--mode','answers','--json-only')
        self.assertEqual(code,0,err)
        for path, before in original.items():
            self.assertEqual((path.read_bytes(),path.stat().st_mtime_ns),before)
        self.assertTrue((self.build/'t-답안.json').exists())
        self.assertFalse((self.build/'t-문제-typography.html').exists())

    def test_problems_mode_writes_no_answers(self):
        code, _, err = self.run_cli('--ids','E9.05','--name','t','--mode','problems','--json-only')
        self.assertEqual(code,0,err)
        self.assertTrue((self.build/'t-문제.json').exists())
        self.assertFalse((self.build/'t-답안.json').exists())

    def test_legacy_without_overlay_preserves_json(self):
        from assemble import build_data, ids_selection
        for mode, suffix in [('problems','문제'),('answers','답안')]:
            expected = build_data(ids_selection(['E9.05'],'t'),mode)
            expected['meta']['layout'] = 'a4'
            code, _, err = self.run_cli('--ids','E9.05','--name','t','--json-only')
            self.assertEqual(code,0,err)
            self.assertEqual(self.read_json(f't-{suffix}.json'),expected)

    def test_overlay_usage_errors_exit_2(self):
        for args in [('ch09',), ('--all',), ('--ids','E9.05','--name','t','--mode','problems')]:
            with self.subTest(args=args), self.assertRaises(SystemExit) as error:
                self.run_cli(*args,'--answer-overlay','missing.json','--json-only')
            self.assertEqual(error.exception.code,2)

    def test_invalid_overlay_writes_no_outputs(self):
        code, _, err = self.run_cli('--ids','E9.05','--name','t','--answer-overlay',str(self.build/'missing.json'),'--json-only')
        self.assertEqual(code,1,err)
        self.assertIn('ERROR',err)
        self.assertFalse(self.build.exists())
        self.assertFalse(self.pdf.exists())


if __name__ == "__main__":
    unittest.main()
