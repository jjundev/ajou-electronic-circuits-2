"""The layout probe flags display-math overflow and labels crowding a wire."""
import json
import subprocess
import sys

import pytest
from _util import SCRIPTS

pytest.importorskip('playwright')
PROBE = SCRIPTS / 'layout_probe.py'

WIDE_MATH = '<div class="katex-display"><span style="display:inline-block;width:900px">wide equation</span></div>'
SVG = ('<svg id="amp" width="200" height="100" viewBox="0 0 200 100">'
       '<line x1="0" y1="50" x2="200" y2="50" stroke="black"/>'
       '<text x="80" y="{y}" font-size="13">R1</text></svg>')


def _probe(tmp_path, body, *args):
    html = tmp_path / 'note.html'
    html.write_text('<!doctype html><meta charset="utf-8"><body>' + body + '</body>', encoding='utf-8')
    out = tmp_path / 'probe.json'
    p = subprocess.run([sys.executable, str(PROBE), str(html), '--out', str(out), *args],
                       capture_output=True, text=True, encoding='utf-8')
    assert p.returncode in (0, 1), p.stdout + p.stderr
    return p.returncode, json.loads(out.read_text(encoding='utf-8'))


def test_probe_flags_wide_display_math_at_375(tmp_path):
    code, report = _probe(tmp_path, WIDE_MATH, '--widths', '1280,375', '--themes', 'light')
    by_width = {c['width']: c for c in report['checks']}
    assert code == 1
    assert len(by_width[375]['overflow']) == 1 and by_width[375]['overflow'][0]['excess_px'] > 400
    assert by_width[1280]['overflow'] == []


def test_probe_flags_label_near_wire(tmp_path):
    code, report = _probe(tmp_path, SVG.format(y=45), '--widths', '1280', '--themes', 'light,dark')
    assert code == 1
    for check in report['checks']:
        assert [g['text'] for g in check['label_gaps']] == ['R1']
        assert check['label_gaps'][0]['gap_px'] < 0.6 * 13


def test_probe_clean_fixture_exits_zero(tmp_path):
    code, report = _probe(tmp_path, SVG.format(y=20) + '<div class="katex-display">x = 1</div>')
    assert code == 0 and len(report['checks']) == 4
    assert len(report['html_sha256']) == 64
    assert all(c['overflow'] == [] and c['label_gaps'] == [] for c in report['checks'])


KATEX_PAGE = ('<!doctype html><meta charset="utf-8">'
              '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@{v}/dist/katex.min.css">'
              '<script src="https://cdn.jsdelivr.net/npm/katex@{v}/dist/katex.min.js"></script>'
              '<body><div class="katex-display">x = 1</div></body>')


def _run(tmp_path, html_text):
    html = tmp_path / 'note.html'
    html.write_text(html_text, encoding='utf-8')
    out = tmp_path / 'probe.json'
    p = subprocess.run([sys.executable, str(PROBE), str(html), '--out', str(out), '--widths', '1280', '--themes', 'light'],
                       capture_output=True, text=True, encoding='utf-8')
    return p.returncode, p.stdout


def test_probe_serves_katex_from_repo_copy(tmp_path):
    code, out = _run(tmp_path, KATEX_PAGE.format(v='0.16.11'))
    assert code == 0, out


def test_probe_fails_when_katex_cannot_load(tmp_path):
    code, out = _run(tmp_path, KATEX_PAGE.format(v='0.0.1'))
    assert code == 2
    report = json.loads(out)
    assert report['status'] == 'error' and 'KaTeX not loaded' in report['reason'] and '0.0.1' in report['reason']


def test_probe_measures_with_staged_note_shared_stylesheet(tmp_path):
    notes = tmp_path / 'run' / 'repo' / '복습노트'
    pack = notes / '1118'
    pack.mkdir(parents=True)
    assets = notes / '.assets'
    assets.mkdir()
    (assets / 'layout.css').write_text('.katex-display { width: 300px; }', encoding='utf-8')
    body = ('<link rel="stylesheet" href="../.assets/layout.css">'
            '<a href="https://example.invalid/citation">Reference</a>' + WIDE_MATH)

    code, report = _probe(pack, body, '--widths', '1280', '--themes', 'light')

    assert code == 1
    assert report['checks'][0]['overflow'][0]['excess_px'] == 600


@pytest.mark.parametrize('stylesheet', ['missing.css', 'https://example.invalid/layout.css'])
def test_probe_rejects_failed_resource_loads(tmp_path, stylesheet):
    code, out = _run(tmp_path, f'<link rel="stylesheet" href="{stylesheet}">{WIDE_MATH}')

    assert code == 2, out
    report = json.loads(out)
    assert report['status'] == 'error'
    assert stylesheet in report['reason']
    assert not (tmp_path / 'probe.json').exists()


def test_candidate_probe_reads_shared_course_css_and_ignores_stale_pack_css(tmp_path):
    repo = tmp_path/'repo'
    public = repo/'복습노트/1118'
    public.mkdir(parents=True)
    shared = public.parent/'.assets'
    shared.mkdir()
    (shared/'layout.css').write_text('.katex-display { width: 300px; }')
    (public/'stale.css').touch()
    candidate = tmp_path/'outside'
    candidate.mkdir()
    options = ('--repo', str(repo), '--public-pack', str(public), '--candidate-pack', str(candidate),
               '--widths', '1280', '--themes', 'light')
    code, report = _probe(candidate, '<link rel="stylesheet" href="../.assets/layout.css">'+WIDE_MATH, *options)
    assert code == 1 and report['checks'][0]['overflow'][0]['excess_px'] == 600
    note = candidate/'note.html'
    note.write_text('<link rel="stylesheet" href="stale.css">'+WIDE_MATH)
    proc = subprocess.run([sys.executable, str(PROBE), str(note), '--out', str(tmp_path/'bad.json'), *options],
                          capture_output=True, text=True)
    assert proc.returncode == 2 and 'stale.css' in proc.stdout


# ---- circuit notes: real template, every topic ----
CIRCUIT = ('<figure class="figure circuit"><svg id="fig-circuit-{name}" viewBox="0 0 320 200" role="img" aria-label="c">'
           '<path class="fig-ink" d="M20 100H300"/><g data-symbol="r"><path class="fig-ink" d="M100 60H200"/></g>'
           '<text class="fig-text" x="150" y="{y}">R</text><text class="fig-text" x="150" y="58">S</text>'
           '<text class="fig-text fig-loc" style="font-size:17px" x="60" y="60">㉠</text></svg><figcaption>c</figcaption></figure>')
STEPS = '<p>step</p><p style="height:40px"></p>$$x=1$$' * 12


def _note(tmp_path, *, y=40, css='', steps=STEPS):
    import json as _json
    import shutil
    import assemble
    from _util import MINI_RUN
    run = tmp_path / 'run'
    shutil.copytree(MINI_RUN, run)
    m = _json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    m['sections'][1]['topics'][1]['circuits'] = [{'id': 'fig-circuit-v', 'source': 'L01 s1'}]
    (run / 'manifest.json').write_text(_json.dumps(m), encoding='utf-8')
    path = run / 'sections/s1.html'
    text = path.read_text(encoding='utf-8')
    old = '<span class="layer-title">정확히 말하면</span><p>$\\sigma'
    assert text.count(old) == 1
    path.write_text(text.replace(old, '<span class="layer-title">정확히 말하면</span>' + CIRCUIT.format(name='v', y=y)
                                 + steps + '<p>$\\sigma'), encoding='utf-8')
    note = assemble.assemble(run, tmp_path / 'out')
    if css:
        note.write_text(note.read_text(encoding='utf-8').replace('</head>', f'<style>{css}</style></head>'), encoding='utf-8')
    return note


def _probe_note(tmp_path, note):
    out = tmp_path / 'probe.json'
    p = subprocess.run([sys.executable, str(PROBE), str(note), '--out', str(out), '--widths', '1280', '--themes', 'light'],
                       capture_output=True, text=True, encoding='utf-8')
    return p.returncode, p.stdout, json.loads(out.read_text(encoding='utf-8')) if out.exists() else None


def test_circuit_note_passes_and_counts_topic_figures(tmp_path):
    code, out, report = _probe_note(tmp_path, _note(tmp_path))
    assert code == 0, out + json.dumps(report, ensure_ascii=False)
    assert report['circuits'] == [] and report['checks'][0]['topic_svgs'] >= 1


def test_label_gap_is_found_on_a_hidden_topic(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(tmp_path, y=97))
    assert code == 1
    assert [(g['topic'], g['text']) for g in report['checks'][0]['label_gaps']] == [('s1-var', 'R')]


def test_overflow_is_found_on_a_hidden_topic(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(tmp_path, steps='<div class="table-wrap"></div>$$' + 'abcdefghij+' * 30 + 'x$$'))
    assert code == 1
    assert {o['topic'] for o in report['checks'][0]['overflow']} == {'s1-var'}


def test_circuit_that_scrolls_away_is_reported(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(tmp_path, css='.js .layer .circuit{position:static!important}'))
    assert code == 1
    problems = {(c['view'], c['panel'], c['problem']) for c in report['circuits']}
    assert ('1280x720', 'closed', 'circuit not fully visible') in problems
    assert ('375x667', 'closed', 'circuit not fully visible') in problems
    assert ('1280x720', 'open', 'circuit not fully visible') in problems


def test_circuit_taller_than_the_body_is_reported(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(tmp_path, css='.js .layer .circuit svg{height:1400px!important;max-height:none!important}'))
    assert code == 1
    assert {c['panel'] for c in report['circuits'] if c['problem'] == 'circuit not fully visible'} == {'open', 'closed'}


TWO = STEPS + '<h4 class="sub">next</h4>' + CIRCUIT.format(name='w', y=40) + STEPS


def test_two_circuits_hand_over_cleanly(tmp_path):
    code, out, report = _probe_note(tmp_path, _note(tmp_path, steps=TWO))
    assert code == 0, out + json.dumps(report['circuits'], ensure_ascii=False)


def test_earlier_circuit_showing_below_is_reported(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(
        tmp_path, steps=TWO, css='.js .layer .circuit:has(#fig-circuit-v){padding-bottom:40px!important}'))
    assert code == 1
    assert {(c['circuit'], c['problem']) for c in report['circuits']} == {('fig-circuit-w', 'earlier circuit shows below')}


def test_circuit_covering_its_equation_is_reported(tmp_path):
    code, _, report = _probe_note(tmp_path, _note(
        tmp_path, css='.js .layer .circuit{min-height:100dvh}'))
    assert code == 1
    assert 'circuit covers the equation' in {c['problem'] for c in report['circuits']}


def test_circuit_note_without_any_topic_figure_is_an_error(tmp_path):
    note = _note(tmp_path, css='article.topic svg{display:none!important}')
    code, out, report = _probe_note(tmp_path, note)
    assert code == 2 and 'no topic figure' in out and report is None


def test_circuit_stays_pinned_in_the_body(tmp_path):
    from playwright.sync_api import sync_playwright
    note = _note(tmp_path)
    place = ("() => { const f = document.querySelector('figure.circuit'); return [document.querySelectorAll('figure.circuit').length,"
             " !!f.closest('main .layer.formal'), f.hidden, getComputedStyle(f).position]; }")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 720}, offline=True)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(note.as_uri() + '#s1-var')
            page.wait_for_timeout(300)
            assert page.get_attribute('#toggle-right', 'aria-expanded') == 'true'
            assert page.evaluate(place) == [1, True, False, 'sticky']
            page.click('#toggle-right')
            page.wait_for_timeout(300)
            assert page.evaluate(place) == [1, True, False, 'sticky']
            page.emulate_media(media='print')
            assert page.evaluate(place) == [1, True, False, 'static']
            page.emulate_media(media='screen')
            for size, position in (((900, 720), 'sticky'), ((375, 667), 'sticky'), ((667, 375), 'static')):
                page.set_viewport_size({'width': size[0], 'height': size[1]})
                page.wait_for_timeout(200)
                assert page.evaluate(place) == [1, True, False, position]
            assert not [e for e in errors if 'renderMathInElement' not in e and 'katex' not in e.lower()]
        finally:
            browser.close()
