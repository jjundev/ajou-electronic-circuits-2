#!/usr/bin/env python3
"""Measure a note's layout before a human browser review.

Reports two machine-checkable defects that cost browser fix rounds:
  overflow    display math, summary panel or table wider than its box
              (scrollWidth - clientWidth > 1 px)
  label_gaps  an SVG text label closer than 0.6 em to a wire (line/path/polyline),
              element symbols (.sym, [data-symbol]) and <defs> excluded

Usage:
  python3 layout_probe.py NOTE.html [--widths 1280,375] [--themes light,dark] --out probe.json
Exit code: 0 no defects, 1 defects found, 2 usage or browser error.
This is evidence for the reviewer, not a substitute for looking at the screen.
KaTeX and Pretendard requests to cdn.jsdelivr.net are answered from the repository copy
(workbook/vendor_route.py), so measurements match with or without network. A page that
loads KaTeX but ends up without it is a browser error (exit 2), not a clean measurement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
GAP_EM = 0.6
# The page asked for KaTeX (a script tag) but the library never arrived.
_KATEX_MISSING = ("() => [...document.scripts].some(s => /katex/i.test(s.src))"
                  " && typeof window.katex === 'undefined'")
OVERFLOW_SELECTOR = ('.katex-display, .page-summary, .panel-right .panel-inner, '
                     '.panel-right .sum, .panel-right .katex-display, table')

_MEASURE = r"""
({selector, gapEm}) => {
  const visible = el => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const name = (el, i) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    (el.classList.length ? '.' + [...el.classList].join('.') : '') + `[${i}]`;
  const overflow = [];
  [...document.querySelectorAll(selector)].forEach((el, i) => {
    if (!visible(el)) return;
    const excess = el.scrollWidth - el.clientWidth;
    if (excess > 1) overflow.push({selector: name(el, i), excess_px: excess});
  });
  const skip = el => el.closest('.sym, [data-symbol], defs, marker, symbol');
  const rectDistance = (r, x, y) => Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
  const label_gaps = [];
  [...document.querySelectorAll('svg')].forEach((svg, si) => {
    if (!visible(svg) || svg.parentElement?.closest('svg')) return;
    const wires = [...svg.querySelectorAll('line, path, polyline')].filter(w => !skip(w) && visible(w) && w.getTotalLength);
    const points = [];
    for (const w of wires) {
      const ctm = w.getScreenCTM(); if (!ctm) continue;
      let length = 0; try { length = w.getTotalLength(); } catch (e) { continue; }
      const n = Math.max(2, Math.min(400, Math.ceil(length * Math.abs(ctm.a) / 2)));
      for (let k = 0; k <= n; k++) {
        const p = w.getPointAtLength(length * k / n);
        points.push(new DOMPoint(p.x, p.y).matrixTransform(ctm));
      }
    }
    [...svg.querySelectorAll('text')].forEach(t => {
      if (skip(t) || !visible(t) || !t.textContent.trim()) return;
      const r = t.getBoundingClientRect();
      const ctm = t.getScreenCTM();
      const font = parseFloat(getComputedStyle(t).fontSize) * (ctm ? Math.hypot(ctm.a, ctm.b) : 1);
      let gap = Infinity;
      for (const p of points) gap = Math.min(gap, rectDistance(r, p.x, p.y));
      if (gap < gapEm * font)
        label_gaps.push({svg_id: svg.id || `svg[${si}]`, text: t.textContent.trim().slice(0, 40),
                         gap_px: Math.round(gap * 10) / 10, min_px: Math.round(gapEm * font * 10) / 10});
    });
  });
  return {overflow, label_gaps};
}
"""


def probe(html: Path, widths: list[int], themes: list[str]) -> dict:
    from playwright.sync_api import sync_playwright
    if str(REPO / 'workbook') not in sys.path:
        sys.path.insert(0, str(REPO / 'workbook'))
    from browser_runtime import install_render_routes, launch_chromium, local_url
    import vendor_route

    html = html.resolve()
    notes_root = REPO / "복습노트"
    local_root = notes_root if html.is_relative_to(notes_root) else html.parent
    url = local_url(html, local_root)
    checks = []
    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        try:
            for width in widths:
                for theme in themes:
                    page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme=theme,
                                            offline=True, service_workers='block')
                    blocked = set()
                    install_render_routes(page, local_roots=(local_root,),
                                          vendor_resolver=vendor_route.resolve_asset, blocked=blocked)
                    response = page.goto(url, wait_until='load')
                    if response is None or not response.ok:
                        raise RuntimeError(f'Local HTML did not load: {html}')
                    if page.evaluate(_KATEX_MISSING):
                        detail = ': ' + '; '.join(sorted(blocked)) if blocked else ''
                        raise RuntimeError('KaTeX not loaded' + detail)
                    page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                    toggle = page.locator('#toggle-right[aria-expanded="false"]')
                    if toggle.count() and toggle.first.is_visible():
                        toggle.first.click()  # measure with the summary panel open
                    page.wait_for_timeout(300)
                    result = page.evaluate(_MEASURE, {'selector': OVERFLOW_SELECTOR, 'gapEm': GAP_EM})
                    checks.append(dict(width=width, theme=theme, **result))
                    page.close()
        finally:
            browser.close()
    return dict(html_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=checks)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('html', type=Path)
    ap.add_argument('--widths', default='1280,375')
    ap.add_argument('--themes', default='light,dark')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        widths = [int(w) for w in a.widths.split(',') if w.strip()]
        themes = [t.strip() for t in a.themes.split(',') if t.strip()]
        if not a.html.is_file() or not widths or not set(themes) <= {'light', 'dark'}:
            raise ValueError('need an existing HTML file, widths, and themes from light,dark')
        report = probe(a.html, widths, themes)
    except Exception as exc:  # browser missing, bad arguments
        print(json.dumps({'status': 'error', 'reason': str(exc)[:240]}, ensure_ascii=False))
        return 2
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    defects = sum(len(c['overflow']) + len(c['label_gaps']) for c in report['checks'])
    print(json.dumps({'status': 'pass' if defects == 0 else 'defects', 'defects': defects, 'out': str(a.out)},
                     ensure_ascii=False))
    return 0 if defects == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
