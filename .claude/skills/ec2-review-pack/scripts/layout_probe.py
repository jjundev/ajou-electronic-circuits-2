#!/usr/bin/env python3
"""Measure a note's layout before a human browser review.

Reports two machine-checkable defects that cost browser fix rounds:
  overflow    display math, summary panel or table wider than its box
              (scrollWidth - clientWidth > 1 px)
  label_gaps  an SVG text label closer than 0.6 em to a wire (line/path/polyline),
              element symbols (.sym, [data-symbol]) and <defs> excluded
Notes built from the circuit template (body data-circuits) are also walked topic by topic:
  overflow    the same boxes on every topic screen
  label_gaps  labels of every figure.circuit (location marks .fig-loc: 0.25 em)
  circuits    the circuit preceding each formal equation must be fully visible and must not
              cover that equation (1280x720 with the panel closed and open, 375x667)

Usage:
  python3 layout_probe.py NOTE.html [--widths 1280,375] [--themes light,dark] --out probe.json
Exit code: 0 no defects, 1 defects found, 2 usage or browser error.
This is evidence for the reviewer, not a substitute for looking at the screen.
KaTeX and Pretendard requests to cdn.jsdelivr.net are answered from the repository copy
(workbook/vendor_route.py), so measurements match with or without network.
A missing page resource or an unloaded KaTeX script yields a browser error (exit 2).
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
LOC_GAP_EM = 0.25
CIRCUIT_VIEWS = ((1280, 720), (375, 667))
# The page asked for KaTeX (a script tag) but the library never arrived.
_KATEX_MISSING = ("() => [...document.scripts].some(s => /katex/i.test(s.src))"
                  " && typeof window.katex === 'undefined'")
OVERFLOW_SELECTOR = ('.katex-display, .page-summary, .panel-right .panel-inner, '
                     '.panel-right .sum, .panel-right .katex-display, table')

_MEASURE = r"""
({selector, gapEm, locGapEm, scope}) => {
  const inScope = el => !scope || el.closest(scope);
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
    if (!visible(svg) || svg.parentElement?.closest('svg') || !inScope(svg)) return;
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
      const need = (svg.closest('figure.circuit') && t.classList.contains('fig-loc') ? locGapEm : gapEm) * font;
      if (gap < need)
        label_gaps.push({svg_id: svg.id || `svg[${si}]`, text: t.textContent.trim().slice(0, 40),
                         gap_px: Math.round(gap * 10) / 10, min_px: Math.round(need * 10) / 10});
    });
  });
  return {overflow, label_gaps};
}
"""
_SHOW_TOPIC = r"""
id => new Promise(done => {
  location.hash = '#' + id;
  requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(done, 60)));
})
"""
_TOPIC_IDS = "() => [...document.querySelectorAll('article.topic')].map(t => t.id)"
_TOPIC_SVGS = ("() => [...document.querySelectorAll('article.topic svg, .circuits svg')]"
               ".filter(s => s.getClientRects().length).length")
# Run while every circuit is at its place in the body: [equation index -> svg id].
_PAIR_CIRCUITS = r"""
id => {
  const formal = document.querySelector(`#${CSS.escape(id)} > .layer.formal`);
  const figures = formal ? [...formal.querySelectorAll('figure.circuit')] : [];
  if (!figures.length) return [];
  const equations = [...formal.querySelectorAll('.katex-display')];
  const items = equations.length ? equations : [formal.lastElementChild];
  return items.map(e => {
    const before = figures.filter(f => f === e || f.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING);
    return (before.at(-1) ?? figures[0]).querySelector('svg').id;
  });
}
"""
_CIRCUITS_VISIBLE = r"""
({id, pairs}) => {
  const formal = document.querySelector(`#${CSS.escape(id)} > .layer.formal`);
  const equations = [...formal.querySelectorAll('.katex-display')];
  const items = equations.length ? equations : [formal.lastElementChild];
  const out = [];
  items.forEach((e, i) => {
    e.scrollIntoView({block: 'end', behavior: 'instant'});
    const svg = document.getElementById(pairs[i]);
    const figure = svg.closest('figure.circuit');
    const port = (svg.closest('.panel-inner') ?? svg.closest('.content') ?? document.documentElement).getBoundingClientRect();
    const r = svg.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    const shown = r.height > 0 && r.top >= port.top - 2 && r.bottom <= Math.min(port.bottom, innerHeight) + 2
      && r.left >= port.left - 2 && r.right <= port.right + 2 && top && figure.contains(top);
    if (!shown) out.push({topic: id, equation: i + 1, circuit: svg.id, problem: 'circuit not fully visible'});
    const f = figure.getBoundingClientRect(), q = e.getBoundingClientRect();
    if (!figure.contains(e) && q.top < f.bottom - 1 && q.bottom > f.top + 1 && q.left < f.right - 1 && q.right > f.left + 1)
      out.push({topic: id, equation: i + 1, circuit: svg.id, problem: 'circuit covers the equation'});
  });
  return out;
}
"""


def _set_panel(page, open_: bool) -> None:
    toggle = page.locator('#toggle-right')
    if toggle.count() and toggle.first.is_visible() and (toggle.first.get_attribute('aria-expanded') == 'true') != open_:
        toggle.first.click()
        page.wait_for_timeout(300)


def _walk_topics(page, result: dict) -> int:
    """Add the defects of every topic screen to `result`; return how many topic SVGs were measured."""
    svgs = 0
    for topic in page.evaluate(_TOPIC_IDS):
        page.evaluate(_SHOW_TOPIC, topic)
        svgs += page.evaluate(_TOPIC_SVGS)
        found = page.evaluate(_MEASURE, {'selector': OVERFLOW_SELECTOR, 'gapEm': GAP_EM, 'locGapEm': LOC_GAP_EM,
                                         'scope': 'figure.circuit'})
        for key, items in found.items():
            result[key] += [dict(item, topic=topic) for item in items]
    return svgs


def _circuit_visibility(page, size: tuple[int, int]) -> list[dict]:
    page.set_viewport_size({'width': size[0], 'height': size[1]})
    page.wait_for_timeout(200)
    _set_panel(page, False)
    pairs = {}
    for topic in page.evaluate(_TOPIC_IDS):
        page.evaluate(_SHOW_TOPIC, topic)
        if found := page.evaluate(_PAIR_CIRCUITS, topic):
            pairs[topic] = found
    out = []
    for panel in ((False, True) if size[0] >= 1024 else (False,)):
        _set_panel(page, panel)
        for topic, pair in pairs.items():
            page.evaluate(_SHOW_TOPIC, topic)
            out += [dict(view=f'{size[0]}x{size[1]}', panel='open' if panel else 'closed', **item)
                    for item in page.evaluate(_CIRCUITS_VISIBLE, {'id': topic, 'pairs': pair})]
    return out


def probe(html: Path, widths: list[int], themes: list[str], *, pack_paths=None) -> dict:
    from playwright.sync_api import sync_playwright
    if str(REPO / 'workbook') not in sys.path:
        sys.path.insert(0, str(REPO / 'workbook'))
    from browser_runtime import install_render_routes, launch_chromium, local_url
    import vendor_route

    html = html.resolve()
    local_root = next((parent for parent in html.parents if normalize("NFC", parent.name) == "복습노트"),
                      html.parent)
    if pack_paths:
        logical = pack_paths.logical(html)
        if pack_paths.source_file(str(logical)).resolve() != html:
            raise ValueError('preview HTML must come from the candidate')
        roots = (pack_paths.repo, pack_paths.work_pack)
        url = local_url(logical, pack_paths.repo)
    else:
        roots = (local_root,)
        url = local_url(html, local_root)
    checks, circuits, walked = [], [], False
    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        try:
            for width in widths:
                for theme in themes:
                    page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme=theme,
                                            offline=True, service_workers='block')
                    failed_resources = set()
                    page.on('requestfailed', lambda request: failed_resources.add(request.url))
                    page.on('response', lambda response: failed_resources.add(response.url)
                            if response.status >= 400 else None)
                    install_render_routes(page, local_roots=roots,
                                          local_resolver=pack_paths.source_file if pack_paths else None,
                                          vendor_resolver=vendor_route.resolve_asset, blocked=failed_resources)
                    response = page.goto(url, wait_until='load')
                    if response is None or not response.ok:
                        raise RuntimeError(f'Local HTML did not load: {html}')
                    if page.evaluate(_KATEX_MISSING):
                        detail = ': ' + ', '.join(sorted(failed_resources)) if failed_resources else ''
                        raise RuntimeError('KaTeX not loaded' + detail)
                    page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
                    toggle = page.locator('#toggle-right[aria-expanded="false"]')
                    if toggle.count() and toggle.first.is_visible():
                        toggle.first.click()  # measure with the summary panel open
                    page.wait_for_timeout(300)
                    page.evaluate("document.fonts.ready.then(() => null)")
                    if failed_resources:
                        raise RuntimeError('Page resource failed to load: ' + ', '.join(sorted(failed_resources)))
                    result = page.evaluate(_MEASURE, {'selector': OVERFLOW_SELECTOR, 'gapEm': GAP_EM,
                                                      'locGapEm': LOC_GAP_EM, 'scope': None})
                    if page.evaluate("() => 'circuits' in document.body.dataset"):
                        if not (svgs := _walk_topics(page, result)):
                            raise RuntimeError('circuit note: no topic figure was measured')
                        result['topic_svgs'] = svgs
                        if not walked:
                            walked = True
                            for size in CIRCUIT_VIEWS:
                                circuits += _circuit_visibility(page, size)
                    checks.append(dict(width=width, theme=theme, **result))
                    page.close()
        finally:
            browser.close()
    report = dict(html_sha256=hashlib.sha256(html.read_bytes()).hexdigest(), checks=checks)
    return dict(report, circuits=circuits) if walked else report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('html', type=Path)
    ap.add_argument('--repo', type=Path, default=REPO)
    ap.add_argument('--public-pack', type=Path)
    ap.add_argument('--candidate-pack', type=Path)
    ap.add_argument('--widths', default='1280,375')
    ap.add_argument('--themes', default='light,dark')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        widths = [int(w) for w in a.widths.split(',') if w.strip()]
        themes = [t.strip() for t in a.themes.split(',') if t.strip()]
        if not a.html.is_file() or not widths or not set(themes) <= {'light', 'dark'}:
            raise ValueError('need an existing HTML file, widths, and themes from light,dark')
        view = None
        if a.public_pack or a.candidate_pack:
            if not (a.public_pack and a.candidate_pack):
                raise ValueError('--public-pack and --candidate-pack must be paired')
            sys.path.append(str(REPO / 'workbook'))
            from pack_paths import PackPaths
            view = PackPaths(a.repo, a.public_pack, a.candidate_pack)
        report = probe(a.html, widths, themes, pack_paths=view)
    except Exception as exc:  # browser missing, bad arguments
        print(json.dumps({'status': 'error', 'reason': str(exc)[:240]}, ensure_ascii=False))
        return 2
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    defects = sum(len(c['overflow']) + len(c['label_gaps']) for c in report['checks'])
    defects += len(report.get('circuits', []))
    print(json.dumps({'status': 'pass' if defects == 0 else 'defects', 'defects': defects, 'out': str(a.out)},
                     ensure_ascii=False))
    return 0 if defects == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
