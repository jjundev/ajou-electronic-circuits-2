import tempfile
import unittest
from pathlib import Path

from _util import FAKE, REPO, make_root
from scripts.ec2_report import config


class ConfigTests(unittest.TestCase):
    def test_load_real_course_info(self):
        info = config.load_course_info(REPO)
        self.assertTrue(set(config.REQUIRED) <= set(info))
        self.assertIsInstance(info["chrome"], list)
        self.assertEqual(config.missing_identity(info), [])

    def test_load_fake_course_info(self):
        with tempfile.TemporaryDirectory() as d:
            info = config.load_course_info(make_root(d))
        self.assertEqual(info["student_id"], "20990001")
        self.assertIsNone(info["notion_parent_page_id"])

    def test_missing_required_key_names_it(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "course_code"):
                config.load_course_info(make_root(d, drop=("course_code",)))

    def test_missing_identity_reports_none_values(self):
        self.assertEqual(
            config.missing_identity({"professor": "x", "class_section": None,
                                     "student_id": "", "student_name": "y"}),
            ["class_section", "student_id"])

    def test_paths_for_assignment_1(self):
        p = config.paths(1, REPO, FAKE)
        self.assertEqual(p.final_pdf.name, "전자회로2_설계과제1_20990001_홍길동.pdf")
        self.assertEqual(p.report_md.relative_to(REPO).as_posix(),
                         "설계과제/과제1/report/설계과제1_보고서.md")
        self.assertEqual(p.baseline(3).name, "baseline_v3.md")
        self.assertEqual(p.pulled(2).name, "pulled_v2.md")
        self.assertEqual(p.cover_pdf.name, "설계과제1 표지.pdf")

    def test_assignment_dir_missing(self):
        with self.assertRaises(FileNotFoundError):
            config.assignment_dir(99, REPO)

    def test_document_title(self):
        self.assertEqual(config.document_title(2), "전자회로2 설계과제2 보고서")

    def test_find_root_from_repo(self):
        self.assertEqual(config.find_root(REPO / "scripts"), REPO)


if __name__ == "__main__":
    unittest.main()
