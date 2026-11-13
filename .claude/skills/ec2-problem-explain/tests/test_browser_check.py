"""The headless browser check's pass/fail evaluator (pure; no browser needed)."""
import unittest
from pathlib import Path

import _util  # noqa: F401  (puts scripts/ and workbook/ on sys.path)
import vendor_route
from epe_browser_check import evaluate, ASSETS


def good(**overrides):
    result = {'visibility': 'visible', 'topics': 3, 'sumsInPanel': 3, 'katex': 40, 'katexErrors': 0,
              'rawDollar': False, 'sumsLeftInMain': 0, 'brokenImages': [], 'external': [],
              'hScroll': [], 'panelOverflow': [], 'consoleErrors': [], 'spacingErrors': []}
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
                 'spacingErrors': {'spacingErrors': [{'kind':'summary-label-top','actual':0,'minimum':24}]},
                 'consoleErrors': {'consoleErrors': ['boom']}}
        for needle, overrides in cases.items():
            with self.subTest(needle=needle):
                failures = evaluate(good(**overrides))
                self.assertTrue(any(needle in f for f in failures), failures)

    def test_expected_topic_count_and_missing_keys_fail(self):
        self.assertTrue(evaluate(good(), expected_topics=4))
        missing=good(); del missing['spacingErrors']; self.assertTrue(evaluate(missing))
        self.assertTrue(evaluate({'visibility': 'visible', 'topics': 1, 'sumsInPanel': 1}))

    def test_template_cdn_urls_resolve_to_local_vendor(self):
        template = (ASSETS / 'note-template.html').read_text(encoding='utf-8')
        urls = [
            'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
            'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
            'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
            'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
        ]
        for url in urls:
            self.assertIn(url, template)
            target, reason = vendor_route.resolve(url, vendor=ASSETS / 'vendor')
            self.assertIsNone(reason)
            self.assertTrue(Path(target).is_file())

    def test_install_async_fulfills_valid_and_aborts_unknown_cdn(self):
        import asyncio
        from types import SimpleNamespace

        class FakePage:
            def __init__(self):
                self.pattern = None
                self.handler = None
            async def route(self, pattern, handler):
                self.pattern = pattern
                self.handler = handler

        class FakeRoute:
            def __init__(self, url):
                self.request = SimpleNamespace(url=url)
                self.fulfilled = None
                self.aborted = False
            async def fulfill(self, **kwargs):
                self.fulfilled = kwargs
            async def abort(self):
                self.aborted = True

        async def scenario():
            page = FakePage()
            misses = await vendor_route.install_async(page, vendor=ASSETS / 'vendor')
            good_route = FakeRoute('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css')
            bad_route = FakeRoute('https://cdn.jsdelivr.net/npm/evil@1.0.0/x.js')
            await page.handler(good_route)
            await page.handler(bad_route)
            return page.pattern, good_route, bad_route, misses

        pattern, good_route, bad_route, misses = asyncio.run(scenario())
        self.assertEqual(pattern, vendor_route.CDN_PATTERN)
        self.assertIsNotNone(good_route.fulfilled)
        self.assertFalse(good_route.aborted)
        self.assertTrue(bad_route.aborted)
        self.assertEqual(len(misses), 1)


if __name__ == '__main__':
    unittest.main()
