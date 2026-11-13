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
