#!/usr/bin/env python3
"""Offline Playwright layout and multi-state probe for ec2-interactive v2 labs.

Loads a built interactive HTML file under Playwright's offline mode using
workbook/browser_runtime.py and workbook/vendor_route.py (serving only local
files and the 4 vendored KaTeX/Pretendard CDN URLs). Walks all representative
states returned by window.__EC2_LAB__.listProbeStates() across the requested
viewport widths and color themes, plus mobile drawer open/Escape flows at
widths < 1024px.

Exit codes:
  0  No layout, KaTeX, SVG label-gap, drawer, or runtime console/page defects.
  1  One or more defects found.
  2  CLI usage error, missing/unmapped network resource, missing runtime API,
     or Chromium launch failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from unicodedata import normalize

REPO = Path(__file__).resolve().parents[4]
GAP_EM = 0.6
OVERFLOW_SELECTOR = (
    '.katex-display, .page-summary, .panel-left, .panel-left .panel-inner, '
    '.panel-right, .panel-right .panel-inner, .panel-right .sum, '
    '.stage, .lab-stage-wrap, .lab-stage, .predict-card, .plot-wrap, '
    '.diagnosis, .formula-box, .summary-box, .topbar, .seg, table'
)

_KATEX_MISSING = """
() => {
  const scripts = [...document.scripts];
  const needsKatex = scripts.some(s => /katex(?:\\.min)?\\.js/i.test(s.src) || /\\/katex@/i.test(s.src));
  const needsAuto = scripts.some(s => /auto-render/i.test(s.src));
  if (needsKatex && typeof window.katex === 'undefined') return 'katex';
  if (needsAuto && typeof window.renderMathInElement !== 'function') return 'auto-render';
  return null;
}
"""

_CHECK_CONTROLLER = """
() => {
  const api = window.__EC2_LAB__;
  if (!api) return { present: false, valid: false };
  const valid = (
    typeof api.listProbeStates === 'function' &&
    typeof api.applyProbeState === 'function' &&
    typeof api.setTheme === 'function'
  );
  return { present: true, valid };
}
"""

_MEASURE = r"""
({selector, gapEm}) => {
  const isDisplayed = el => {
    if (!el || el.closest('[hidden], [display="none"]')) return false;
    if (el.getClientRects().length === 0) return false;
    let cur = el;
    while (cur && cur.nodeType === 1) {
      if (getComputedStyle(cur).display === 'none') return false;
      cur = cur.parentElement;
    }
    return true;
  };
  const visible = el => {
    if (!isDisplayed(el)) return false;
    let cur = el;
    while (cur && cur.nodeType === 1) {
      if (getComputedStyle(cur).visibility === 'hidden') return false;
      cur = cur.parentElement;
    }
    return true;
  };
  const overflowMeasurable = el => {
    if (!isDisplayed(el)) return false;
    const panel = el.closest('.panel');
    if (panel) {
      // Closed desktop panels collapse to width: 0 with visibility: hidden;
      // closed mobile panels keep full drawer width offscreen and can still
      // reveal text/formula overflow across all probe states.
      if (parseFloat(getComputedStyle(panel).width || '0') <= 1) return false;
      return true;
    }
    return visible(el);
  };
  const name = (el, i) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    (el.classList.length ? '.' + [...el.classList].join('.') : '') + `[${i}]`;

  const rootEl = document.getElementById('ec2-lab-root');
  const docEl = document.documentElement;
  const horizontal_scroll_px = Math.max(
    0,
    Math.round(docEl.scrollWidth - docEl.clientWidth),
    document.body ? Math.round(document.body.scrollWidth - document.body.clientWidth) : 0,
    rootEl ? Math.round(rootEl.scrollWidth - rootEl.clientWidth) : 0
  );

  const overflow = [];
  [...document.querySelectorAll(selector)].forEach((el, i) => {
    if (!overflowMeasurable(el)) return;
    const excess = Math.round((el.scrollWidth - el.clientWidth) * 10) / 10;
    if (excess > 1) overflow.push({selector: name(el, i), excess_px: excess});
  });

  const stageEl = document.querySelector('.stage');
  const stageRect = stageEl ? stageEl.getBoundingClientRect() : null;
  document.querySelectorAll('.lab-stage svg').forEach((svg, si) => {
    if (!visible(svg)) return;
    const svgRect = svg.getBoundingClientRect();
    svg.querySelectorAll('text, rect, circle, line, path, polyline').forEach(el => {
      if (!visible(el) || el.closest('defs, marker, symbol')) return;
      const r = el.getBoundingClientRect();
      if (r.width <= 0 && r.height <= 0) return;
      const stageClip = stageRect ? Math.max(0, stageRect.left - r.left, r.right - stageRect.right) : 0;
      const svgClip = Math.max(0, svgRect.left - r.left, r.right - svgRect.right);
      const svgExcess = Math.max(stageClip > 1 ? stageClip : 0, svgClip > 3 ? svgClip : 0);
      if (svgExcess > 1) {
        overflow.push({
          selector: `${svg.id || `svg[${si}]`} ${el.tagName.toLowerCase()}`,
          excess_px: Math.round(svgExcess * 10) / 10,
        });
      }
    });
  });

  const skipSymbol = el => Boolean(el.closest('.sym, [data-symbol], defs, marker, symbol'));
  const skipUiSvg = svg => Boolean(
    svg.closest('.topbar, .plot-wrap, button, [aria-hidden="true"]') ||
    svg.getAttribute('aria-hidden') === 'true'
  );
  const skipWire = w => {
    if (skipSymbol(w)) return true;
    if (w.matches('.lab-badge-bg, [data-badge-bg], .port-chip-bg') || w.closest('.plot-wrap')) return true;
    const st = getComputedStyle(w);
    const tag = w.tagName.toLowerCase();
    if (tag === 'rect' && (st.stroke === 'none' || parseFloat(st.strokeWidth || '0') <= 0)) return true;
    if (st.stroke === 'none' && st.fill === 'none') return true;
    return false;
  };
  const rectDistance = (r, x, y) => Math.hypot(
    Math.max(r.left - x, 0, x - r.right),
    Math.max(r.top - y, 0, y - r.bottom)
  );

  const label_gaps = [];
  [...document.querySelectorAll('svg')].forEach((svg, si) => {
    if (!visible(svg) || svg.parentElement?.closest('svg') || skipUiSvg(svg)) return;
    const wires = [...svg.querySelectorAll('line, path, polyline, rect, circle')]
      .filter(w => !skipWire(w) && visible(w) && typeof w.getTotalLength === 'function');
    const points = [];
    for (const w of wires) {
      const ctm = w.getScreenCTM();
      if (!ctm) continue;
      let length = 0;
      try { length = w.getTotalLength(); } catch (e) { continue; }
      if (!(length > 0)) continue;
      const scale = Math.hypot(ctm.a, ctm.b) || Math.hypot(ctm.c, ctm.d) || 1;
      const n = Math.max(2, Math.min(400, Math.ceil(length * scale / 2)));
      for (let k = 0; k <= n; k++) {
        const p = w.getPointAtLength(length * k / n);
        points.push(new DOMPoint(p.x, p.y).matrixTransform(ctm));
      }
    }
    [...svg.querySelectorAll('text')].forEach(t => {
      if (skipSymbol(t) || !visible(t) || !t.textContent.trim()) return;
      const r = t.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return;
      const ctm = t.getScreenCTM();
      const font = parseFloat(getComputedStyle(t).fontSize) * (ctm ? Math.hypot(ctm.a, ctm.b) : 1);
      let gap = Infinity;
      for (const p of points) gap = Math.min(gap, rectDistance(r, p.x, p.y));
      if (gap < gapEm * font) {
        const badgeEl = t.closest('[data-badge-for]');
        const entry = {
          svg_id: svg.id || `svg[${si}]`,
          text: t.textContent.trim().slice(0, 40),
          gap_px: Math.round(gap * 10) / 10,
          min_px: Math.round(gapEm * font * 10) / 10,
        };
        if (badgeEl) entry.badge_for = badgeEl.getAttribute('data-badge-for');
        label_gaps.push(entry);
      }
    });
  });

  const katexErrors = [
    ...document.querySelectorAll('.katex-error, .katex [mathcolor="#cc0000"], .katex [style*="rgb(204, 0, 0)"], .katex [style*="#cc0000"]'),
  ];
  const katexNodes = [...document.querySelectorAll('.katex')];
  const zeroMetricKatex = [];
  for (const k of katexNodes) {
    if (!isDisplayed(k)) continue;
    const kr = k.getBoundingClientRect();
    if (kr.width <= 0 || kr.height <= 0) {
      zeroMetricKatex.push(k.textContent.trim().slice(0, 40));
    }
  }
  const unrendered = [];
  const mathRoots = [
    document.querySelector('.panel-right .panel-inner'),
    document.querySelector('.predict-slot'),
  ].filter(Boolean);
  const mathRegex = /\$\$[\s\S]+?\$\$|\$[^$\n]+?\$/;
  for (const root of mathRoots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent || !isDisplayed(parent)) continue;
      if (parent.closest('.katex, script, style, noscript, textarea, pre, code, svg')) continue;
      const text = node.nodeValue || '';
      if (mathRegex.test(text) || (parent.closest('.formula-box') && text.includes('$'))) {
        unrendered.push(text.trim().slice(0, 60));
      }
    }
  }
  const formulaBoxes = [...document.querySelectorAll('.formula-box')].filter(fb => isDisplayed(fb) && fb.textContent.trim().length > 0);
  const missingFormulaKatex = formulaBoxes.some(fb => {
    const txt = fb.textContent;
    return (txt.includes('$') || txt.includes('\\')) && fb.querySelectorAll('.katex').length === 0;
  });
  const katex_ok = katexErrors.length === 0 && zeroMetricKatex.length === 0 && unrendered.length === 0 && !missingFormulaKatex;
  const drawer = rootEl ? (rootEl.getAttribute('data-drawer') || 'none') : 'none';

  return {
    drawer,
    horizontal_scroll_px,
    overflow,
    label_gaps,
    katex_ok,
    katex_details: {
      count: katexNodes.length,
      errors: katexErrors.length,
      zero_metrics: zeroMetricKatex,
      unrendered,
      missing_formula_katex: missingFormulaKatex,
    },
  };
}
"""


def _ensure_page_resources(page, failed_resources: set[str]) -> None:
    if failed_resources:
        raise RuntimeError('Page resource failed to load: ' + ', '.join(sorted(failed_resources)))


def _drain_check(
    page,
    *,
    width: int,
    theme: str,
    state_label: str,
    console_errors: list[str],
    page_errors: list[str],
    drawer_ok: bool = True,
    drawer_error: str | None = None,
) -> dict:
    measured = page.evaluate(_MEASURE, {'selector': OVERFLOW_SELECTOR, 'gapEm': GAP_EM})
    errs = list(console_errors)
    perrs = list(page_errors)
    console_errors.clear()
    page_errors.clear()
    if drawer_error:
        perrs.append(drawer_error)
    return {
        'width': width,
        'theme': theme,
        'state': state_label,
        'drawer': measured['drawer'],
        'console_errors': errs,
        'page_errors': perrs,
        'horizontal_scroll_px': measured['horizontal_scroll_px'],
        'overflow': measured['overflow'],
        'label_gaps': measured['label_gaps'],
        'katex_ok': measured['katex_ok'],
        'katex_details': measured['katex_details'],
        'drawer_ok': drawer_ok,
    }


def _probe_mobile_drawers(
    page,
    *,
    width: int,
    theme: str,
    base_state: dict | None,
    console_errors: list[str],
    page_errors: list[str],
    failed_resources: set[str],
) -> list[dict]:
    results = []
    if base_state is not None:
        page.evaluate('st => window.__EC2_LAB__.applyProbeState(st)', base_state)
        page.wait_for_timeout(80)
        _ensure_page_resources(page, failed_resources)

    for side in ('left', 'right'):
        btn = page.locator(f'[data-drawer-btn="{side}"]')
        if btn.count() == 0 or not btn.first.is_visible():
            results.append(
                _drain_check(
                    page,
                    width=width,
                    theme=theme,
                    state_label=f'서랍: {side}',
                    console_errors=console_errors,
                    page_errors=page_errors,
                    drawer_ok=False,
                    drawer_error=f'Drawer button [data-drawer-btn="{side}"] missing or hidden at {width}px',
                )
            )
            continue

        btn.first.click()
        page.wait_for_timeout(280)
        _ensure_page_resources(page, failed_resources)

        opened_attr = page.evaluate("() => document.getElementById('ec2-lab-root')?.getAttribute('data-drawer')")
        open_err = None if opened_attr == side else f'Expected data-drawer="{side}", got "{opened_attr}"'
        check = _drain_check(
            page,
            width=width,
            theme=theme,
            state_label=f'서랍: {side}',
            console_errors=console_errors,
            page_errors=page_errors,
            drawer_ok=(open_err is None),
            drawer_error=open_err,
        )

        page.keyboard.press('Escape')
        page.wait_for_timeout(220)
        closed_attr = page.evaluate("() => document.getElementById('ec2-lab-root')?.getAttribute('data-drawer')")
        if closed_attr != 'none':
            check['drawer_ok'] = False
            check['page_errors'].append(f'Escape failed to close {side} drawer (data-drawer="{closed_attr}")')
        results.append(check)

    return results


def _count_defects(checks: list[dict]) -> int:
    total = 0
    for c in checks:
        total += len(c['console_errors'])
        total += len(c['page_errors'])
        if c['horizontal_scroll_px'] > 1:
            total += 1
        total += len(c['overflow'])
        total += len(c['label_gaps'])
        if not c['katex_ok']:
            total += 1
        if not c.get('drawer_ok', True):
            total += 1
    return total


def probe(html: Path, widths: list[int], themes: list[str]) -> dict:
    """Run offline Playwright checks across all probe states, widths, and themes."""
    from playwright.sync_api import sync_playwright

    workbook_dir = str(REPO / 'workbook')
    if workbook_dir not in sys.path:
        sys.path.insert(0, workbook_dir)
    from browser_runtime import install_render_routes, launch_chromium, local_url
    import vendor_route

    html = html.resolve()
    local_root = next((p for p in html.parents if normalize('NFC', p.name) == '복습노트'), html.parent)
    url = local_url(html, local_root)
    checks: list[dict] = []

    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        try:
            for width in widths:
                height = 812 if width < 1024 else 900
                for theme in themes:
                    page = browser.new_page(
                        viewport={'width': width, 'height': height},
                        color_scheme=theme,
                        offline=True,
                        service_workers='block',
                    )
                    try:
                        console_errors: list[str] = []
                        page_errors: list[str] = []
                        failed_resources: set[str] = set()
                        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
                        page.on('pageerror', lambda err: page_errors.append(str(err)))
                        page.on('requestfailed', lambda req: failed_resources.add(req.url))
                        page.on('response', lambda resp: failed_resources.add(resp.url) if resp.status >= 400 else None)
                        install_render_routes(
                            page,
                            local_roots=(local_root,),
                            vendor_resolver=vendor_route.resolve_asset,
                            blocked=failed_resources,
                        )

                        response = page.goto(url, wait_until='load')
                        if response is None or not response.ok:
                            raise RuntimeError(f'Local HTML did not load: {html}')

                        _ensure_page_resources(page, failed_resources)
                        missing_katex = page.evaluate(_KATEX_MISSING)
                        if missing_katex:
                            raise RuntimeError(f'KaTeX not loaded ({missing_katex})')

                        ctrl = page.evaluate(_CHECK_CONTROLLER)
                        if not ctrl['present']:
                            if console_errors or page_errors:
                                checks.append(
                                    _drain_check(
                                        page,
                                        width=width,
                                        theme=theme,
                                        state_label='__boot__',
                                        console_errors=console_errors,
                                        page_errors=page_errors,
                                    )
                                )
                                continue
                            raise RuntimeError('window.__EC2_LAB__ is missing on this page')
                        if not ctrl['valid']:
                            raise RuntimeError('window.__EC2_LAB__ is missing listProbeStates/applyProbeState/setTheme')

                        page.evaluate('t => window.__EC2_LAB__.setTheme(t)', theme)
                        page.evaluate('() => document.fonts.ready.then(() => null)')
                        page.wait_for_timeout(120)
                        _ensure_page_resources(page, failed_resources)

                        states = page.evaluate('() => window.__EC2_LAB__.listProbeStates()')
                        if not isinstance(states, list) or not states:
                            raise RuntimeError('window.__EC2_LAB__.listProbeStates() returned no states')

                        for entry in states:
                            label = str(entry.get('label') or 'state')
                            page.evaluate('st => window.__EC2_LAB__.applyProbeState(st)', entry.get('state'))
                            page.evaluate('() => document.fonts.ready.then(() => null)')
                            page.wait_for_timeout(40)
                            _ensure_page_resources(page, failed_resources)
                            checks.append(
                                _drain_check(
                                    page,
                                    width=width,
                                    theme=theme,
                                    state_label=label,
                                    console_errors=console_errors,
                                    page_errors=page_errors,
                                )
                            )

                        if width < 1024:
                            checks.extend(
                                _probe_mobile_drawers(
                                    page,
                                    width=width,
                                    theme=theme,
                                    base_state=states[0].get('state'),
                                    console_errors=console_errors,
                                    page_errors=page_errors,
                                    failed_resources=failed_resources,
                                )
                            )
                    finally:
                        page.close()
        finally:
            browser.close()

    defect_count = _count_defects(checks)
    return {
        'ok': defect_count == 0,
        'html': str(html),
        'html_sha256': hashlib.sha256(html.read_bytes()).hexdigest(),
        'defect_count': defect_count,
        'checks': checks,
    }


def _parse_widths(raw: str) -> list[int]:
    widths = [int(w.strip()) for w in raw.split(',') if w.strip()]
    if not widths or any(w <= 0 for w in widths):
        raise ValueError('widths must be positive integers')
    return widths


def _parse_themes(raw: str) -> list[str]:
    themes = [t.strip() for t in raw.split(',') if t.strip()]
    if not themes or not set(themes) <= {'light', 'dark'}:
        raise ValueError('themes must be chosen from light,dark')
    return themes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('html', type=Path)
    ap.add_argument('--widths', default='1440,375')
    ap.add_argument('--themes', default='light,dark')
    ap.add_argument('--out', type=Path, default=None)
    args = ap.parse_args(argv)

    try:
        if not args.html.is_file():
            raise ValueError(f'HTML file not found: {args.html}')
        widths = _parse_widths(args.widths)
        themes = _parse_themes(args.themes)
        report = probe(args.html, widths, themes)
    except Exception as exc:
        print(json.dumps({'status': 'error', 'reason': str(exc)[:300]}, ensure_ascii=False))
        return 2

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(
            json.dumps(
                {
                    'status': 'pass' if report['ok'] else 'defects',
                    'defects': report['defect_count'],
                    'checks': len(report['checks']),
                    'out': str(args.out),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=1))

    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
