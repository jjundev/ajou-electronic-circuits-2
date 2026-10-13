import re
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'assets' / 'note-template.html'
LIGHT = '--scroll: #c9d0db; --scroll-hover: #9aa3b2;'
DARK = '--scroll: #3f414b; --scroll-hover: #5b5e6a;'


class TestScrollbarTheme(unittest.TestCase):
    def setUp(self):
        self.text = TEMPLATE.read_text(encoding='utf-8')

    def test_tokens_in_every_theme_block(self):
        self.assertEqual(len(re.findall(r'--scroll: #[0-9a-f]{6}; --scroll-hover: #[0-9a-f]{6};', self.text)), 3)
        self.assertEqual(self.text.count(LIGHT), 1)
        self.assertEqual(self.text.count(DARK), 2)

    def test_rules_cover_both_scroll_containers(self):
        for rule in (
            '.content::-webkit-scrollbar, .panel-inner::-webkit-scrollbar { width: 8px; }',
            '.content::-webkit-scrollbar-thumb, .panel-inner::-webkit-scrollbar-thumb { background: var(--scroll);',
            '.content::-webkit-scrollbar-thumb:hover, .panel-inner::-webkit-scrollbar-thumb:hover { background: var(--scroll-hover); }',
            'scrollbar-color: var(--scroll) transparent;',
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.text)

    def test_panel_width_variable_kept(self):
        self.assertIn('--scrollbar: 16px;', self.text)

    def test_math_pan_still_hidden(self):
        self.assertIn('.math-row.math-pan::-webkit-scrollbar { display:none; }', self.text)
