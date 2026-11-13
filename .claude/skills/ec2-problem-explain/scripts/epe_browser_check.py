"""Headless browser check for a staged explanation note (see references/verification.md "browser").

Needs the python `playwright` package and its chromium:
    pip3 install --user --break-system-packages playwright
    python3 -m playwright install chromium

Usage:
    python3 epe_browser_check.py --url http://127.0.0.1:<port>/문제설명_<range>_<slug>.html [--shots DIR] [--topics N]

Prints one JSON object (per-combo measurements plus `failures`) and exits 1 when any of the
four combos (1280x900 / 375x812 x light / dark) fails the pass criteria, 2 when playwright is missing.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

COMBOS = [(1280, 900, 'light'), (1280, 900, 'dark'), (375, 812, 'light'), (375, 812, 'dark')]
TOPIC_WAIT_MS = 700
ASSETS = Path(__file__).resolve().parents[1] / 'assets'
WORKBOOK = Path(__file__).resolve().parents[4] / 'workbook'

MEASURE_JS = r"""async (topicWait) => {
await new Promise((r) => setTimeout(r, 1500));
await document.fonts.ready;
const allowedExternal = [
  'https://cdn.jsdelivr.net/npm/katex@0.16.11/',
  'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/',
];
const textNodes = Array.from(document.querySelectorAll('main *, #panel-right *')).filter((e) => !['SCRIPT', 'STYLE'].includes(e.tagName) && !e.closest('[hidden]'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const summaryToggle=document.querySelector('#toggle-right');
if (summaryToggle?.getAttribute('aria-expanded')==='false') {summaryToggle.click(); await wait(300);}
const scroller = document.querySelector('.content') || document.documentElement;
const over = [], panelOver = [], spacingErrors = [];
const gap = (a,b) => b.getBoundingClientRect().top-a.getBoundingClientRect().bottom;
function checkGap(a,b,min,kind,id) {
  if (a && b && a.getClientRects().length && b.getClientRects().length && gap(a,b)<min-.5)
    spacingErrors.push({topic:id,kind,actual:gap(a,b),minimum:min});
}
for (const t of document.querySelectorAll('main article.topic')) {
  location.hash = '#' + t.id; await wait(topicWait);
  document.getAnimations().forEach((a) => a.finish());
  await wait(100);
  const sum = document.querySelector('#sum-for .sum:not([hidden])');
  for (const label of sum?.querySelectorAll(':scope > .panel-label') || []) {
    checkGap(label.previousElementSibling,label,24,'summary-label-top',t.id);
    checkGap(label,label.nextElementSibling,12,'summary-label-bottom',t.id);
  }
  for (const list of sum?.querySelectorAll(':scope > .eq-list') || [])
    checkGap(list,list.nextElementSibling,24,'summary-equations-bottom',t.id);
  for (const part of t.querySelectorAll('.layer:is([data-explanation="solve"],[data-explanation="verify"]) > [data-subpart]')) {
    const prev=part.previousElementSibling;
    const min=prev?.matches('h4,.layer-title') ? 24 : (innerWidth>=1024 ? 32 : 24);
    checkGap(prev,part,min,'subpart-top',t.id);
    const heading=part.firstElementChild;
    if (heading?.matches('h4')) checkGap(heading,heading.nextElementSibling,12,'subpart-heading-bottom',t.id);
  }
  if (scroller.scrollWidth > scroller.clientWidth + 1 || document.documentElement.scrollWidth > window.innerWidth + 1) over.push(t.id + ':' + scroller.scrollWidth);
  for (const d of document.querySelectorAll('#panel-right .sum .katex-display')) {
    if (d.offsetParent !== null && d.scrollWidth > d.clientWidth + 1) panelOver.push(t.id);
  }
}
location.hash = '';
return {
  visibility: document.visibilityState,
  topics: document.querySelectorAll('main article.topic').length,
  topicIds: Array.from(document.querySelectorAll('main article.topic')).map((t) => t.id),
  katex: document.querySelectorAll('.katex').length,
  katexErrors: document.querySelectorAll('.katex-error').length,
  rawDollar: textNodes.some((e) => Array.from(e.childNodes).some((n) => n.nodeType === 3 && n.textContent.includes('$'))),
  sumsInPanel: document.querySelectorAll('#panel-right .sum').length,
  sumsLeftInMain: document.querySelectorAll('main .sum').length,
  brokenImages: Array.from(document.images).filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.getAttribute('src')),
  external: performance.getEntriesByType('resource').map((e) => e.name).filter((u) => !u.startsWith(location.origin) && !allowedExternal.some((p) => u.startsWith(p))),
  mathPan: document.querySelectorAll('.math-pan').length,
  hScroll: over,
  panelOverflow: panelOver,
  spacingErrors,
  bg: getComputedStyle(document.body).backgroundColor,
};}"""


def evaluate(result, expected_topics=None):
    """Return the list of pass-criteria failures for one combo's measurement (empty = pass)."""
    failures = []
    if result.get('visibility') != 'visible':
        failures.append(f"visibility={result.get('visibility')!r} (측정 무효)")
    topics = result.get('topics', 0)
    if not topics:
        failures.append('topics=0')
    if expected_topics is not None and topics != expected_topics:
        failures.append(f'topics={topics} (기대 {expected_topics})')
    if result.get('sumsInPanel') != topics:
        failures.append(f"sumsInPanel={result.get('sumsInPanel')} != topics={topics}")
    if result.get('katexErrors', 1):
        failures.append(f"katexErrors={result.get('katexErrors')}")
    if result.get('rawDollar', True):
        failures.append('rawDollar')
    if result.get('sumsLeftInMain', 1):
        failures.append(f"sumsLeftInMain={result.get('sumsLeftInMain')}")
    for key in ('brokenImages', 'external', 'hScroll', 'panelOverflow', 'consoleErrors', 'spacingErrors'):
        value = result.get(key, ['(없음)'])
        if value:
            failures.append(f'{key}={value}')
    return failures


async def _goto(page, url, tries=3):
    for attempt in range(tries):
        try:
            await page.goto(url)
            return
        except Exception as exc:  # playwright.Error; flaky local server resets are retried
            if 'ERR_CONNECTION' not in str(exc) or attempt == tries - 1:
                raise
            await asyncio.sleep(1)


async def run(url, shots=None):
    from playwright.async_api import async_playwright
    if str(WORKBOOK) not in sys.path:
        sys.path.insert(0, str(WORKBOOK))
    import vendor_route
    out = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            for width, height, scheme in COMBOS:
                mobile = width < 768
                ctx = await browser.new_context(viewport={'width': width, 'height': height},
                                                color_scheme=scheme, is_mobile=mobile, has_touch=mobile)
                page = await ctx.new_page()
                misses = await vendor_route.install_async(page, vendor=ASSETS / 'vendor')
                errors = []
                page.on('console', lambda m, errors=errors: errors.append(m.text) if m.type == 'error' else None)
                page.on('pageerror', lambda e, errors=errors: errors.append(str(e)))
                await _goto(page, url)
                result = await page.evaluate(MEASURE_JS, TOPIC_WAIT_MS)
                if misses:
                    result['external'] = [*result.get('external', []), *misses]
                result['consoleErrors'] = errors
                combo = f'{width}x{height}-{scheme}'
                if shots:
                    for topic in result['topicIds']:
                        await page.evaluate('(id) => { location.hash = "#" + id; }', topic)
                        await page.wait_for_timeout(TOPIC_WAIT_MS)
                        await page.screenshot(path=str(Path(shots) / f'shot-{combo}-{topic}.png'))
                out[combo] = result
                await ctx.close()
        finally:
            await browser.close()
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description='stage 문제설명 HTML 헤드리스 화면 검사')
    parser.add_argument('--url', required=True, help='http.server로 연 stage HTML URL')
    parser.add_argument('--shots', help='문항별 스크린샷을 저장할 폴더(선택)')
    parser.add_argument('--topics', type=int, help='기대 문항 수(선택)')
    args = parser.parse_args(argv)
    try:
        import playwright  # noqa: F401
    except ImportError:
        print('playwright가 없어요: pip3 install --user --break-system-packages playwright && '
              'python3 -m playwright install chromium', file=sys.stderr)
        return 2
    if args.shots:
        Path(args.shots).mkdir(parents=True, exist_ok=True)
    results = asyncio.run(run(args.url, args.shots))
    failures = {combo: evaluate(r, args.topics) for combo, r in results.items()}
    failures = {k: v for k, v in failures.items() if v}
    # A local http.server reset is a flake, not a page defect: re-run instead of failing the review.
    flaky = [k for k, r in results.items()
             if any('ERR_CONNECTION' in e or 'ERR_SOCKET' in e for e in r['consoleErrors'])]
    print(json.dumps({'route': 'playwright-headless', 'url': args.url, 'results': results,
                      'failures': failures, 'flaky_rerun': flaky, 'pass': not failures},
                     ensure_ascii=False, indent=1))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
