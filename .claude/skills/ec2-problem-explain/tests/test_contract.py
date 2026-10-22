from epe_review_policy import POLICY_VERSION
import unittest
from copy import deepcopy
from dataclasses import replace

import _util
from _util import problem, fragment, pack
from epe_contract import validate_fragment, validate_reviews, payload_hash
from epe_shared import parse, outer

RECALL = ('<div class="layer formal" data-explanation="recall">'
          '<h4>이 개념과 공식을 떠올려요</h4>'
          '<p>제곱을 구하라는 단서에서 같은 수의 곱을 떠올려요. '
          '$A^2=A\\cdot A$이며 A는 주어진 스칼라예요.</p></div>')


def with_recall():
    text = fragment()
    if 'data-explanation="recall"' not in text:
        text = text.replace('<div class="layer formal" data-explanation="start">',
                            RECALL + '<div class="layer formal" data-explanation="start">')
    return text


def recall_block(text):
    return outer(next(parse(text).find_all(lambda n: n.attrs.get('data-explanation') == 'recall')))


def reviews():
    base = {'status': 'pass', 'reviewer': '검토자', 'evidence': '근거: Razavi p.1'}
    items = {f'p1:{s}': dict(base) for s in ('a', 'b')}
    result = _util.approved(pack(), {'p1': fragment()})
    result.update(source_visual=base, browser=base, content={**base, 'items': items},
                  independent={**base, 'items': {k: {**v, 'method': 'exact', 'conclusion': '1=1'}
                                              for k, v in items.items()}})
    return result


class ContractTests(unittest.TestCase):
    def test_declared_gain_route_is_allowed_and_enforced(self):
        route = ('<div data-gain-route="gm-rout">'
                 '<p data-gain-stage="gm">$$G_m=i_{sc}/v_{in}$$</p>'
                 '<p data-gain-stage="rout">$$R_{out}\\approx R_L$$</p>'
                 '<p data-gain-stage="gain">$$A_v=-G_mR_{out}$$</p></div>')
        text = with_recall().replace('<h4>이렇게 풀어요</h4>', '<h4>이렇게 풀어요</h4>' + route)
        self.assertEqual(validate_fragment(problem(), text), [])
        bad = text.replace('<p data-gain-stage="rout">$$R_{out}\\approx R_L$$</p>', '')
        self.assertTrue(any('gain-route' in e for e in validate_fragment(problem(), bad)))

    def test_public_source_locator_and_multi_sentence_summary_refused(self):
        text = fragment()
        bad = text.replace('<div class="sum" hidden>',
            '<div class="sum" hidden><p>테일 저항을 구해요. 반회로로 풀어요.</p>')
        self.assertTrue(any('summary-sentence' in e for e in validate_fragment(problem(), bad)))
        self.assertTrue(any('public-source-location' in e for e in
            validate_fragment(problem(), text + '<p title="STT L182–186">설명</p>')))

    def test_recall_required_and_legacy_fragment_refused(self):
        text = with_recall()
        self.assertEqual(validate_fragment(problem(), text), [])
        self.assertTrue(validate_fragment(problem(), text.replace(recall_block(text), '')))

    def test_recall_duplicate_empty_and_wrong_order_refused(self):
        text = with_recall()
        block = recall_block(text)
        self.assertTrue(validate_fragment(problem(), text + block))
        empty = '<div class="layer formal" data-explanation="recall"><h4>개념</h4></div>'
        self.assertTrue(any('recall' in e for e in validate_fragment(problem(), text.replace(block, empty))))
        wrong = text.replace(block, '').replace(
            '<div class="layer formal" data-explanation="solve">',
            block + '<div class="layer formal" data-explanation="solve">')
        self.assertTrue(any('순서' in e for e in validate_fragment(problem(), wrong)))

    def test_recall_edit_invalidates_approval(self):
        before = fragment()
        changed = before.replace('제곱을 구하라는 단서', '곱셈을 요구하는 단서')
        self.assertNotEqual(changed, before)
        self.assertTrue(validate_reviews(pack(), {'p1': changed}, reviews()))

    def test_nested_heading_only_recall_refused(self):
        text = with_recall()
        nested = ('<div class="layer formal" data-explanation="recall">'
                  '<div><h4>제목뿐인 개념 구역</h4></div></div>')
        self.assertTrue(any('recall' in e for e in
                            validate_fragment(problem(), text.replace(recall_block(text), nested))))

    def test_all_subparts_must_be_solved_and_verified(self):
        self.assertEqual(validate_fragment(problem(), fragment()), [])
        broken = fragment().replace('data-subpart="b"', 'data-subpart="a"', 1)
        self.assertTrue(any('소문항' in e for e in validate_fragment(problem(), broken)))

    def test_numeric_subparts_required_in_solve_and_verify(self):
        p = replace(problem(), subparts=('1', '2'))
        self.assertEqual(validate_fragment(p, fragment(p)), [])
        broken = fragment(p).replace('data-subpart="2"', 'data-subpart="3"', 1)
        self.assertTrue(any('모든 소문항' in e for e in validate_fragment(p, broken)))

    def test_hidden_or_active_explanation_refused(self):
        for markup in ['<details>답</details>', '<p hidden>답</p>', '<script>alert(1)</script>',
                       '<img src="x" onerror="x">', '<a href="javascript:alert(1)">x</a>',
                       '<p style="display:none">답</p>', '<iframe src="x"></iframe>']:
            with self.subTest(markup=markup):
                self.assertTrue(validate_fragment(problem(), fragment() + markup))

    def test_math_delimiters_checked_per_text_node(self):
        pitfall = '<p>행과 열을 바꾸지 않아요.</p>'
        adjacent = with_recall().replace(pitfall, pitfall + '<p>$a$</p><p>$b$</p>')
        self.assertEqual(validate_fragment(problem(), adjacent), [])
        split = with_recall().replace(pitfall, pitfall + '<p>$a</p><p>b$</p>')
        errors = validate_fragment(problem(), split)
        self.assertTrue(any('unbalanced $' in e for e in errors), errors)
        self.assertEqual(len(errors), len(set(errors)))

    def test_retry_and_missing_sections_refused(self):
        self.assertTrue(validate_fragment(
            problem(), fragment().replace('data-explanation="start"', 'data-explanation="solve"')))
        self.assertTrue(validate_fragment(problem(), fragment().replace('<li>다시 계산해요.</li>', '')))

    def test_unreviewed_or_stale_or_incomplete_reports_refused(self):
        self.assertTrue(validate_reviews(pack(), {'p1': fragment()}, {}))
        good = reviews()
        self.assertEqual(validate_reviews(pack(), {'p1': fragment()}, good), [])
        self.assertTrue(validate_reviews(pack(), {'p1': fragment() + '변경'}, good))
        for kind in ('source_visual', 'browser', 'content', 'independent'):
            bad = deepcopy(good)
            bad[kind]['status'] = 'not_run'
            self.assertTrue(validate_reviews(pack(), {'p1': fragment()}, bad), kind)
        bad = deepcopy(good)
        del bad['independent']['items']['p1:b']
        self.assertTrue(validate_reviews(pack(), {'p1': fragment()}, bad))

    def test_numerical_residual_requires_real_bounds(self):
        good = reviews()
        item = good['independent']['items']['p1:a']
        item.update(method='numerical', tolerance=1e-8, residual=1e-9)
        self.assertEqual(validate_reviews(pack(), {'p1': fragment()}, good), [])
        item['residual'] = 1
        self.assertTrue(validate_reviews(pack(), {'p1': fragment()}, good))
        item['residual'] = float('nan')
        self.assertTrue(validate_reviews(pack(), {'p1': fragment()}, good))

    def test_approved_helper_passes_validate_reviews(self):
        self.assertEqual(validate_reviews(pack(), {'p1': fragment()},
                                          _util.approved(pack(), {'p1': fragment()})), [])


if __name__ == '__main__':
    unittest.main()
