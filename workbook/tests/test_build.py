import io
import json
import sys
import tempfile
import unicodedata
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
    def test_selection_metadata_applies_to_both_pdfs(self):
        selection = Path(self._tmp.name) / 'selection.json'
        selection.write_text(json.dumps(dict(schema_version=2, policy='exam-first-v2',
            workload=dict(estimated_minutes=20), problems=[dict(id=pid, priority='core',
                learning_goals=['이득'], estimated_minutes=10, subpart_count=1)
                for pid in ['E9.01', 'P9.05']])), encoding='utf-8')
        code, _, err = self.run_cli('--ids', 'E9.01,P9.05', '--name', 't', '--json-only',
                                    '--selection', str(selection))
        self.assertEqual(code, 0, err)
        for suffix in ['문제', '답안']:
            data = self.read_json(f't-{suffix}.json')
            self.assertIn('핵심', data['problems'][0]['review_workload_label'])
            self.assertEqual(data['meta']['review_workload']['estimated_minutes'], 20)

    def test_ids(self):
        code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t", "--json-only")
        self.assertEqual(code, 0, err)
        for name in ("t-문제.json", "t-문제.html", "t-답안.json", "t-답안.html"):
            self.assertTrue((self.build / name).exists(), name)
        self.assertEqual(self.read_json("t-문제.json")["meta"]["total"], 2)
        self.assertEqual(self.read_json("t-답안.json")["meta"]["title"], "t 답안")
        self.assertFalse(self.pdf.exists())

    def test_explicit_pack_titles_preserve_source_and_apply_to_both_modes(self):
        titles = Path(self._tmp.name) / "titles.json"
        titles.write_text(json.dumps({"E9.01": "캐스코드 출력저항", "P9.05": "차동 이득"}), encoding="utf-8")
        code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t", "--json-only",
                                    "--display-titles", str(titles))
        self.assertEqual(code, 0, err)
        for suffix in ("문제", "답안"):
            problems = self.read_json(f"t-{suffix}.json")["problems"]
            self.assertEqual([p["title"] for p in problems], ["P1. 캐스코드 출력저항", "P2. 차동 이득"])
            self.assertTrue(all(p["source_title"] for p in problems))
            self.assertTrue(all(p["html"]["conditions"] for p in problems))

    def test_chapter(self):
        code, _, err = self.run_cli("ch09", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read_json("ch09-문제.json")["meta"]["total"], 110)

    def test_all(self):
        code, _, err = self.run_cli("--all", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(list(self.build.glob("*.json"))), 36)   # 장 5 + 기출 13, 각각 문제·답안


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

    def make_titled_overlay(self):
        import hashlib
        from overlay_fixture import OverlayBundle, digest
        bundle = OverlayBundle(Path(self._tmp.name) / 'overlay')
        titles = bundle.stage / '.assets/display-titles.json'
        titles.write_text(json.dumps({'E9.05':'캐스코드 출력저항','E9.06':'병렬 출력저항'}), encoding='utf-8')
        bundle.source_files.insert(1, titles)
        bundle.overlay['source_inputs'] = {p.relative_to(bundle.repo).as_posix():digest(p) for p in bundle.source_files}
        bundle.manifest['inputs'] = [str(p) for p in bundle.source_files]
        bundle.manifest['source_sha256'] = hashlib.sha256(''.join(digest(p) for p in bundle.source_files).encode()).hexdigest()
        bundle.sync()
        return bundle, titles

    def test_approved_overlay_uses_its_bound_titles_without_explicit_flag(self):
        bundle, _ = self.make_titled_overlay()
        with patch.object(build_workbook.paths, 'ROOT', bundle.repo):
            code, _, err = self.run_cli('--ids','E9.05,E9.06','--name','t','--mode','answers',
                '--answer-overlay', str(bundle.path), '--json-only')
        self.assertEqual(code, 0, err)
        self.assertEqual([p['title'] for p in self.read_json('t-답안.json')['problems']],
                         ['P1. 캐스코드 출력저항','P2. 병렬 출력저항'])

    def test_approved_overlay_rejects_unreviewed_explicit_title_map(self):
        bundle, _ = self.make_titled_overlay()
        other = Path(self._tmp.name) / 'other-titles.json'
        other.write_text(json.dumps({'E9.05':'다른 제목','E9.06':'바꾼 제목'}), encoding='utf-8')
        with patch.object(build_workbook.paths, 'ROOT', bundle.repo):
            code, _, err = self.run_cli('--ids','E9.05,E9.06','--name','t','--mode','answers',
                '--answer-overlay', str(bundle.path), '--display-titles', str(other), '--json-only')
        self.assertEqual(code, 1, err)
        self.assertIn('표시 제목', err)
        self.assertFalse(self.build.exists())

    def test_legacy_overlay_rejects_unreviewed_new_title_map(self):
        from overlay_fixture import OverlayBundle
        bundle = OverlayBundle(Path(self._tmp.name) / 'legacy-overlay')
        other = Path(self._tmp.name) / 'new-titles.json'
        other.write_text(json.dumps({'E9.05':'새 제목','E9.06':'다른 제목'}), encoding='utf-8')
        with patch.object(build_workbook.paths, 'ROOT', bundle.repo):
            code, _, err = self.run_cli('--ids','E9.05,E9.06','--name','t','--mode','answers',
                '--answer-overlay', str(bundle.path), '--display-titles', str(other), '--json-only')
        self.assertEqual(code, 1, err)
        self.assertIn('표시 제목', err)
        self.assertFalse(self.build.exists())

    def test_legacy_overlay_without_title_map_preserves_source_titles(self):
        from overlay_fixture import OverlayBundle
        from assemble import build_data, ids_selection
        bundle = OverlayBundle(Path(self._tmp.name) / 'legacy-no-map')
        expected = [p['title'] for p in build_data(ids_selection(['E9.05','E9.06'],'t'),'answers')['problems']]
        with patch.object(build_workbook.paths, 'ROOT', bundle.repo):
            code, _, err = self.run_cli('--ids','E9.05,E9.06','--name','t','--mode','answers',
                '--answer-overlay', str(bundle.path), '--json-only')
        self.assertEqual(code, 0, err)
        self.assertEqual([p['title'] for p in self.read_json('t-답안.json')['problems']], expected)

    def test_invalid_overlay_writes_no_outputs(self):
        code, _, err = self.run_cli('--ids','E9.05','--name','t','--answer-overlay',str(self.build/'missing.json'),'--json-only')
        self.assertEqual(code,1,err)
        self.assertIn('ERROR',err)
        self.assertFalse(self.build.exists())
        self.assertFalse(self.pdf.exists())


if __name__ == "__main__":
    unittest.main()


def test_root_spelling_matches_nfc_argument_under_nfd_root(monkeypatch, tmp_path):
    nfd = tmp_path / unicodedata.normalize("NFD", "전자회로2")
    (nfd / "복습노트").mkdir(parents=True)
    monkeypatch.setattr(build_workbook.paths, "ROOT", nfd)
    arg = unicodedata.normalize("NFC", str(nfd / "복습노트/x/.assets/a/answer-overlay.json"))
    root = build_workbook.root_spelling(arg)
    assert str(root) == unicodedata.normalize("NFC", str(nfd))


def test_root_spelling_keeps_root_for_outside_path(monkeypatch, tmp_path):
    monkeypatch.setattr(build_workbook.paths, "ROOT", tmp_path / "repo")
    assert build_workbook.root_spelling(tmp_path / "repo-copy/a.json") == tmp_path / "repo"
