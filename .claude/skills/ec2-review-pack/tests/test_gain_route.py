"""Structural Gm/Rout route regressions; semantic equations still require review."""
import unittest
from _util import SCRIPTS
from readability import readability_errors


def route(stages=('gm', 'rout', 'gain')):
    formula = {'gm': r'$$G_m=i_{sc}/v_{in}$$',
               'rout': r'$$R_{out}\approx R_L\parallel R_{amp}$$',
               'gain': r'$$A_v\approx-G_mR_{out}$$'}
    return '<div data-gain-route="gm-rout">' + ''.join(
        f'<div data-gain-stage="{s}"><h5>{s}</h5><p>{formula[s]}</p></div>'
        for s in stages) + '</div>'


class GainRouteTests(unittest.TestCase):
    def errors(self, markup):
        return [e for e in readability_errors(markup) if e[0] == 'gain-route']

    def test_visible_ordered_route_is_valid(self):
        self.assertEqual(self.errors(route()), [])

    def test_missing_reordered_duplicate_stages_rejected(self):
        for stages in [('gm', 'gain'), ('rout', 'gm', 'gain'), ('gm', 'rout', 'gain', 'gain')]:
            self.assertTrue(self.errors(route(stages)), stages)

    def test_hidden_stage_or_math_rejected(self):
        for attr in ['hidden', 'aria-hidden="true"', 'style="display:none"',
                     'style="visibility: hidden"', 'class="visually-hidden"']:
            self.assertTrue(self.errors(route().replace('data-gain-stage="gm"',
                f'data-gain-stage="gm" {attr}')), attr)
            self.assertTrue(self.errors(route().replace('<p>$$G_m', f'<p {attr}>$$G_m')), attr)
        self.assertTrue(self.errors('<div hidden>' + route() + '</div>'))

    def test_empty_formula_or_heading_only_stage_rejected(self):
        for replacement in ['', '<h5>$$G_m=i/v$$</h5>', '<p>공식을 떠올려요</p>', '<p>$$$$</p>']:
            before = '<h5>gm</h5><p>$$G_m=i_{sc}/v_{in}$$</p>'
            self.assertTrue(self.errors(route().replace(before, replacement)), replacement)

    def test_invalid_or_orphan_markers_rejected(self):
        self.assertTrue(self.errors(route().replace('gm-rout', 'other')))
        self.assertTrue(self.errors('<p data-gain-stage="gm">$$G_m=1$$</p>'))
        self.assertTrue(self.errors(route().replace('data-gain-stage="gm"', 'data-gain-stage="unknown"')))
        self.assertTrue(self.errors('<div data-gain-route="gm-rout">' + route() + '</div>'))

    def test_unmarked_legacy_is_not_inferred_or_rewritten(self):
        self.assertEqual(self.errors('<p>$$A_v=-R_C/(2R_{SS})$$</p>'), [])


if __name__ == '__main__':
    unittest.main()
