import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _util import REPO
from scripts.ec2_report import notion


class NotionTests(unittest.TestCase):
    def test_load_token_missing_mentions_zshenv(self):
        with mock.patch.dict(os.environ, {"NOTION_TOKEN": ""}):
            with self.assertRaisesRegex(notion.NotionError, r"~/\.zshenv"):
                notion.load_token()

    def test_push_markdown_sends_title_property(self):
        with mock.patch.object(notion, "_request", return_value={"id": "p1", "url": "u"}) as req:
            r = notion.push_markdown("본문", "parent", "tok", title="T v1")
        payload = req.call_args.args[3]
        self.assertEqual(payload["properties"]["title"][0]["text"]["content"], "T v1")
        self.assertEqual(payload["parent"], {"page_id": "parent"})
        self.assertEqual(r, {"page_id": "p1", "url": "u"})

    def test_push_markdown_empty_parent_names_course_info(self):
        with mock.patch.object(notion, "_request") as req:
            with self.assertRaisesRegex(notion.NotionError, "과목정보.md"):
                notion.push_markdown("x", "", "tok")
        req.assert_not_called()

    def test_pull_truncated_raises(self):
        with mock.patch.object(notion, "_request", return_value={"truncated": True, "markdown": "x"}):
            with self.assertRaises(notion.NotionError):
                notion.pull_markdown("p1", "tok")

    def test_pull_strips_presigned_query(self):
        md = "![a](https://s3.aws/a.png?X-Amz-Signature=abc&X-Amz-Security-Token=t)"
        with mock.patch.object(notion, "_request", return_value={"markdown": md}):
            self.assertEqual(notion.pull_markdown("p1", "tok"), "![a](https://s3.aws/a.png)")

    def test_versions_count_per_kind(self):
        with tempfile.TemporaryDirectory() as d:
            notion.append_record(d, "보고서", "p1", "u1", "r.md", "2026-10-10 12:00")
            notion.append_record(d, "보고서", "p2", "u2", "r.md", "2026-10-10 13:00")
            self.assertEqual(notion.next_version(d, "보고서"), 3)
            data = json.loads((Path(d) / "notion.json").read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "notion-uploads/v1")
            self.assertEqual([r["version"] for r in data["uploads"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
