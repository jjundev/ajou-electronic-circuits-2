import io
import os
from contextlib import redirect_stdout
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _util import make_root
from scripts.ec2_report import config, notion, sync

BODY = """# 설계 과제 1: MOS 차동 증폭기

주어진 조건을 이용하여 다음 차동 증폭기를 설계하시오.

# 1. Design Problem

**(a) 이득을 구하라.**

**▶** 반쪽 회로에서 $g_m$ 으로 구한다.

![그림 1](../figures/fig1.png)
"""


class SyncTestBase(unittest.TestCase):
    parent = "parent123"

    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.root = make_root(self._d.name, notion_parent_page_id=self.parent)
        self.p = config.paths(1, self.root, config.load_course_info(self.root))
        self.write_body(BODY)

    def tearDown(self):
        self._d.cleanup()

    def write_body(self, text):
        self.p.report_md.write_text(text, encoding="utf-8")


class StripTitleTests(unittest.TestCase):
    def test_strip_title_only_leading_h1(self):
        self.assertEqual(sync.strip_title("\n\n# 제목\n\n# 1. Design\n", "제목"), "# 1. Design\n")
        no_title = "본문 첫 문단\n\n# 1. Design\n"
        self.assertEqual(sync.strip_title(no_title, "제목"), no_title)

    def test_strip_title_keeps_numbered_section(self):
        text = "# 1. Design Problem (설계과정 필수)\n\n본문\n"
        self.assertEqual(sync.strip_title(text, "x"), text)

    def test_strip_title_keeps_h2_first_line(self):
        text = "## 소제목\n\n본문\n"
        self.assertEqual(sync.strip_title(text, "x"), text)


class PushTests(SyncTestBase):
    def fake_request(self, uploaded):
        def _req(method, path, token, payload=None, timeout=120):
            if method == "POST":
                uploaded.append(payload)
                return {"id": "p1", "url": "https://notion.so/p1"}
            return {"markdown": uploaded[-1]["markdown"]}
        return _req

    def test_push_blocked_on_errors(self):
        self.write_body(BODY + "\nClaude 로 검산했다.\n")
        with mock.patch.object(notion, "_request") as req:
            with self.assertRaises(sync.SyncBlocked) as cm:
                sync.push(1, self.root, token="t")
        req.assert_not_called()
        self.assertTrue(any("Claude" in f.msg for f in cm.exception.findings))

    def test_push_blocked_when_body_starts_with_heading(self):
        self.write_body("# 1. Design Problem\n\n본문 문단\n")
        with mock.patch.object(notion, "_request") as req:
            with self.assertRaises(sync.SyncBlocked) as cm:
                sync.push(1, self.root, token="t")
        req.assert_not_called()
        self.assertIn("첫 블록", cm.exception.findings[0].msg)

    def test_push_happy_path(self):
        uploaded = []
        with mock.patch.object(notion, "_request", side_effect=self.fake_request(uploaded)):
            r = sync.push(1, self.root, token="t", now="2026-10-10 12:00")
        self.assertEqual((r["version"], r["title"]), (1, "전자회로2 설계과제1 보고서 v1"))
        self.assertTrue(r["baseline"].exists())
        self.assertEqual(r["baseline"], self.p.baseline(1))
        self.assertEqual(r["roundtrip"], [])
        self.assertFalse(uploaded[0]["markdown"].startswith("# 설계 과제 1"))
        self.assertEqual(uploaded[0]["properties"]["title"][0]["text"]["content"],
                         "전자회로2 설계과제1 보고서 v1")
        rec = notion.load_records(self.p.notion_dir)
        self.assertEqual(rec[0]["uploaded_at"], "2026-10-10 12:00")
        self.assertEqual(rec[0]["kind"], "보고서")
        self.assertTrue(any("그림" in f.msg for f in r["info"]))

    def test_second_push_is_v2(self):
        uploaded = []
        with mock.patch.object(notion, "_request", side_effect=self.fake_request(uploaded)):
            sync.push(1, self.root, token="t", now="a")
            r = sync.push(1, self.root, token="t", now="b")
        self.assertEqual(r["version"], 2)

    def test_recover_baselines_repulls_missing_only(self):
        notion.append_record(self.p.notion_dir, "보고서", "p1", "u1", "r.md", "a")
        notion.append_record(self.p.notion_dir, "보고서", "p2", "u2", "r.md", "b")
        self.p.baseline(1).write_text("old", encoding="utf-8")
        with mock.patch.object(notion, "_request", return_value={"markdown": "새 본문"}) as req:
            got = sync.recover_baselines(1, self.root, token="t")
        self.assertEqual(got, [self.p.baseline(2)])
        self.assertEqual(req.call_count, 1)
        self.assertIn("p2", req.call_args.args[1])
        self.assertEqual(self.p.baseline(1).read_text(encoding="utf-8"), "old")

    def test_check_images_flags_empty(self):
        notion.append_record(self.p.notion_dir, "보고서", "p1", "u1", "r.md", "a")
        with mock.patch.object(notion, "_request", return_value={"markdown": "![회로도]()\n"}):
            f = sync.check_images(1, self.root, token="t")
        self.assertEqual(len(f), 1)
        self.assertTrue(self.p.pulled(1).exists())

    def test_check_images_without_record(self):
        with mock.patch.object(notion, "_request") as req:
            with self.assertRaises(notion.NotionError):
                sync.check_images(1, self.root, token="t")
        req.assert_not_called()

    def test_cli_blocked_returns_2(self):
        self.write_body(BODY + "\nChatGPT\n")
        with mock.patch.object(sync.config, "find_root", return_value=self.root), \
             mock.patch.object(notion, "_request"):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(sync.main(["push", "--n", "1"]), 2)
        self.assertIn("ChatGPT", out.getvalue())


class NoParentTests(SyncTestBase):
    parent = None

    def test_push_without_parent_id_writes_no_record(self):
        with mock.patch.dict(os.environ, {"NOTION_TOKEN": ""}), \
             mock.patch.object(notion, "_request") as req:
            with self.assertRaisesRegex(notion.NotionError, "notion_parent_page_id"):
                sync.push(1, self.root)
        req.assert_not_called()
        self.assertFalse((self.p.notion_dir / "notion.json").exists())

    def test_cli_no_parent_returns_3(self):
        with mock.patch.object(sync.config, "find_root", return_value=self.root), \
             mock.patch.object(notion, "_request"):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(sync.main(["push", "--n", "1"]), 3)
        self.assertIn("notion_parent_page_id", out.getvalue())


if __name__ == "__main__":
    unittest.main()
