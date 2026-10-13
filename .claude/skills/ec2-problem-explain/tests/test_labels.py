import unittest

import _util  # noqa: F401
from epe_labels import normalize_subpart_labels
from epe_shared import parse


def paragraphs(markup, subpart):
    root = parse(markup)
    block = next(root.find_all(lambda n: n.attrs.get('data-subpart') == subpart))
    return [n.text() for n in block.find_all(lambda n: n.tag == 'p')]


def wrap(label, body, heading=True):
    h = f'<h4>({label})</h4>' if heading else ''
    return f'<div data-explanation="solve"><div data-subpart="{label}">{h}{body}</div></div>'


class LabelTests(unittest.TestCase):
    def test_removes_repeated_labels_and_preserves_references(self):
        body = ('<p>(a) 전개해요. $A^2=1$</p><p><strong>(a) </strong>미분해요.</p>'
                '<p>(a)에서 구한 결과예요.</p><p>(b) 다른 소문항을 참조해요.</p>')
        got = paragraphs(normalize_subpart_labels(wrap('a', body)), 'a')
        self.assertIn('전개해요. $A^2=1$', got)
        self.assertIn('미분해요.', got)
        self.assertIn('(a)에서 구한 결과예요.', got)
        self.assertIn('(b) 다른 소문항을 참조해요.', got)

    def test_keeps_labels_without_a_subpart_heading(self):
        src = wrap('a', '<p>(a) 첫 식에서 계산해요.</p>', heading=False)
        self.assertEqual(normalize_subpart_labels(src), src)

    def test_numeric_label_prefix_removed_under_heading(self):
        src = ('<div data-explanation="solve"><div data-subpart="1"><h4>(1)</h4>'
               '<p>(1) 이득을 구해요.</p></div></div>')
        self.assertIn('<p>이득을 구해요.</p>', normalize_subpart_labels(src))

    def test_multi_digit_numeric_label(self):
        src = wrap('10', '<p>(10) 값을 구해요.</p>')
        self.assertIn('<p>값을 구해요.</p>', normalize_subpart_labels(src))

    def test_numeric_reference_to_other_subpart_kept(self):
        src = wrap('1', '<p>(2)번 결과를 써요.</p>')
        self.assertIn('(2)번 결과를 써요.', normalize_subpart_labels(src))

    def test_non_label_names_ignored(self):
        src = wrap('main', '<p>(main) 그대로예요.</p>')
        self.assertEqual(normalize_subpart_labels(src), src)


if __name__ == '__main__':
    unittest.main()
