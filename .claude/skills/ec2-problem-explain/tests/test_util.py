import tempfile
import unittest
import unicodedata
from pathlib import Path

import _util
from epe_shared import load_problem, REPO, compact, parse, TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR


class MakeRepoTests(unittest.TestCase):
    def test_default_repo_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _util.make_repo(Path(tmp))
            self.assertTrue((root / '교과서/마이크로전자회로/ch10/장말문제/P10.02.md').exists())
            self.assertTrue((root / 'from_the_past/md/2023-1_중간/Q4.md').exists())
            self.assertTrue((root / 'from_the_past/md/2023-1_중간/exam.yaml').exists())
            self.assertTrue((root / 'from_the_past/md/2023-1_중간/figures/figures.yaml').exists())
            note = root / '복습노트/1007'
            lines = (note / '.assets' / 'problems.txt').read_text(encoding='utf-8').splitlines()
            self.assertEqual([l.split(' | ')[0] for l in lines], ['P10.02', '2023-1_중간-Q4'])
            self.assertIn('id="s1-diff"', (note / '정리노트_1007_Diff_Amp.html').read_text(encoding='utf-8'))
            self.assertTrue((note / '복습문제_1007_Diff_Amp-문제.pdf').read_bytes())
            self.assertEqual(load_problem(root / 'from_the_past/md/2023-1_중간/Q4.md').id, '2023-1_중간-Q4')

    def test_nfd_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _util.make_repo(Path(tmp), nfd=True, ids=('P10.02',))
            names = {unicodedata.normalize('NFC', p.name) for p in (root / '복습노트/1007').iterdir()}
            self.assertIn('정리노트_1007_Diff_Amp.html', names)

    def test_shared_exports(self):
        self.assertTrue((REPO / 'workbook').is_dir())
        self.assertEqual(compact('<p>a  b\n c</p>'), 'abc')
        self.assertTrue(TEXTBOOK_ID_RE.match('P10.02') and EXAM_ID_RE.match('2023-1_중간-Q4'))
        self.assertEqual(KIND_DIR['P'], '장말문제')
        self.assertEqual(parse('<p>x</p>').children[0].tag, 'p')


if __name__ == '__main__':
    unittest.main()
