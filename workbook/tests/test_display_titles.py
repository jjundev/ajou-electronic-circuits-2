import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from display_titles import DisplayTitlesError, load_display_titles


class DisplayTitlesTest(unittest.TestCase):
    def test_invalid_or_stale_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'titles.json'
            for value in ({'wrong': '제목'}, {'A': ''}, {'A': 'Fig 10.88 공통 모드'},
                          {'A': 'P1. 제목'}, {'A': '두\n줄'}, {'A': 2}, []):
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding='utf-8')
                    with self.assertRaises(DisplayTitlesError):
                        load_display_titles(path, ['A'])

    def test_missing_and_invalid_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'missing.json'
            with self.assertRaises(DisplayTitlesError):
                load_display_titles(path, ['A'])
            path.write_text('{', encoding='utf-8')
            with self.assertRaises(DisplayTitlesError):
                load_display_titles(path, ['A'])
