"""실제 복습노트/<range>/ 맨 위에는 .pack/·HTML·PDF·.assets/만 있는지 확인한다."""

from pathlib import Path
import tempfile
import unicodedata
import unittest

from _util import REPO

import manifest

NOTES = REPO / "복습노트"


def stray_entries(notes_dir):
    """팩 폴더 맨 위에서 규칙에 맞지 않는 항목(`<range>/<이름>`, NFC) 목록."""
    out = []
    # 맨 위 .assets/는 팩이 아니라 팩들이 함께 쓰는 vendor 폴더다.
    for pack in sorted(p for p in notes_dir.iterdir() if p.is_dir() and p.name != manifest.BUNDLE):
        for entry in sorted(pack.iterdir()):
            name = unicodedata.normalize("NFC", entry.name)
            if name == ".DS_Store":
                continue
            if entry.is_dir() and name in (".pack", manifest.BUNDLE):
                continue
            if entry.is_file() and name.lower().endswith((".html", ".pdf")):
                continue
            out.append(f"{unicodedata.normalize('NFC', pack.name)}/{name}")
    return out


class TestPackLayout(unittest.TestCase):
    @unittest.skipUnless(NOTES.is_dir(), "복습노트 없음")
    def test_real_packs_keep_only_allowed_top_level_entries(self):
        self.assertEqual(stray_entries(NOTES), [])

    def test_detects_stray_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "0101"
            for d in (".pack", ".assets", "figures_0101"):
                (pack / d).mkdir(parents=True)
            for f in ("정리노트_0101_X.html", "복습문제_0101_X-문제.pdf", "정리노트_0101_X.md", "problems.txt"):
                (pack / f).write_text("x", encoding="utf-8")
            self.assertEqual(stray_entries(Path(tmp)), ["0101/figures_0101", "0101/problems.txt", "0101/정리노트_0101_X.md"])


if __name__ == "__main__":
    unittest.main()
