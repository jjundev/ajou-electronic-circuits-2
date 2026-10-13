"""The headless browser check's pass/fail evaluator (pure; no browser needed)."""
import unittest

import _util  # noqa: F401  (puts scripts/ on sys.path)
from epe_browser_check import evaluate


def good(**overrides):
    result = {'visibility': 'visible', 'topics': 3, 'sumsInPanel': 3, 'katex': 40, 'katexErrors': 0,
              'rawDollar': False, 'sumsLeftInMain': 0, 'brokenImages': [], 'external': [],
              'hScroll': [], 'panelOverflow': [], 'consoleErrors': []}
    result.update(overrides)
    return result


class EvaluateTests(unittest.TestCase):
    def test_clean_result_passes(self):
        self.assertEqual(evaluate(good()), [])
        self.assertEqual(evaluate(good(), expected_topics=3), [])

    def test_each_criterion_flags_failure(self):
        cases = {'visibility': {'visibility': 'hidden'}, 'topics=0': {'topics': 0, 'sumsInPanel': 0},
                 'sumsInPanel': {'sumsInPanel': 2}, 'katexErrors': {'katexErrors': 1},
                 'rawDollar': {'rawDollar': True}, 'sumsLeftInMain': {'sumsLeftInMain': 1},
                 'brokenImages': {'brokenImages': ['a.png']}, 'external': {'external': ['https://x']},
                 'hScroll': {'hScroll': ['p1:900']}, 'panelOverflow': {'panelOverflow': ['p2']},
                 'consoleErrors': {'consoleErrors': ['boom']}}
        for needle, overrides in cases.items():
            with self.subTest(needle=needle):
                failures = evaluate(good(**overrides))
                self.assertTrue(any(needle in f for f in failures), failures)

    def test_expected_topic_count_and_missing_keys_fail(self):
        self.assertTrue(evaluate(good(), expected_topics=4))
        self.assertTrue(evaluate({'visibility': 'visible', 'topics': 1, 'sumsInPanel': 1}))


if __name__ == '__main__':
    unittest.main()
