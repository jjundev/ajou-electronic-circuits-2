"""Offline Playwright layout and multi-state probe tests for ec2-interactive v2."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip('playwright')

SKILL = Path(__file__).resolve().parents[1]
PROBE = SKILL / 'scripts' / 'probe_interactive.py'
BUILD = SKILL / 'scripts' / 'build.cjs'
EXAMPLE = SKILL / 'references' / 'example-lab.js'


def test_probe_passes_example_lab_across_desktop_and_mobile(tmp_path):
    html = tmp_path / 'example.html'
    out = tmp_path / 'probe.json'
    subprocess.run(['node', str(BUILD), str(EXAMPLE), str(html)], check=True)
    res = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            str(html),
            '--widths',
            '1440,375',
            '--themes',
            'light,dark',
            '--out',
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is True
    assert len(data['checks']) >= 4
    assert all(
        c['katex_ok']
        and not c['label_gaps']
        and not c['overflow']
        and c['horizontal_scroll_px'] <= 1
        and not c['console_errors']
        and not c['page_errors']
        for c in data['checks']
    )
    mobile_drawers = {c.get('drawer') for c in data['checks'] if c['width'] == 375}
    assert {'none', 'left', 'right'} <= mobile_drawers


def _replace_once(text: str, old: str, new: str) -> str:
    assert old in text, f'Pattern not found in fixture: {old!r}'
    return text.replace(old, new, 1)


def test_probe_catches_active_badge_wire_collision_and_mobile_overflow(tmp_path):
    """Review Focus #4: 동적 배지가 도선에 0.6em 미만으로 겹치면 exit 1."""
    bad_lab = tmp_path / 'bad-lab.js'
    bad_lab.write_text(
        _replace_once(
            EXAMPLE.read_text(encoding='utf-8'),
            'data-badge-for="out" transform="translate(220, 32)"',
            'data-badge-for="out" transform="translate(150, 80)"',
        ),
        encoding='utf-8',
    )
    html = tmp_path / 'bad.html'
    out = tmp_path / 'bad-probe.json'
    subprocess.run(['node', str(BUILD), str(bad_lab), str(html)], check=True)
    res = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            str(html),
            '--widths',
            '1440,375',
            '--themes',
            'light',
            '--out',
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is False
    assert any(c['label_gaps'] for c in data['checks'])


def test_probe_catches_mobile_overflow_at_375(tmp_path):
    """Review Focus #4: 1440px에서는 통과하지만 375px 모바일에서 넘치는 요소를 exit 1로 검출."""
    html = tmp_path / 'overflow.html'
    out = tmp_path / 'overflow-probe.json'
    subprocess.run(['node', str(BUILD), str(EXAMPLE), str(html)], check=True)
    raw = html.read_text(encoding='utf-8')
    wide_block = '<div class="mobile-overflow-sentinel" style="width:550px;min-width:550px;flex:none">wide mobile overflow</div>'
    html.write_text(_replace_once(raw, '</main>', f'{wide_block}</main>'), encoding='utf-8')

    res = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            str(html),
            '--widths',
            '1440,375',
            '--themes',
            'light',
            '--out',
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is False
    desktop_checks = [c for c in data['checks'] if c['width'] == 1440]
    mobile_checks = [c for c in data['checks'] if c['width'] == 375]
    assert desktop_checks and all(not c['overflow'] and c['horizontal_scroll_px'] <= 1 for c in desktop_checks)
    assert mobile_checks and any(c['overflow'] or c['horizontal_scroll_px'] > 1 for c in mobile_checks)


def test_probe_catches_katex_error_and_console_error(tmp_path):
    """KaTeX 렌더 오류(.katex-error) 및 런타임 console.error를 결함(exit 1)으로 검출."""
    bad_math_lab = tmp_path / 'bad-math-lab.js'
    bad_math_lab.write_text(
        _replace_once(
            EXAMPLE.read_text(encoding='utf-8'),
            r"formula: '$$v_{\\text{out}} = \\frac{R_{\\text{eq}}}{R_1 + R_{\\text{eq}}} v_{\\text{in}}$$'",
            r"formula: '$$\\unknownkatexmacroxyz{1}$$'",
        ),
        encoding='utf-8',
    )
    html = tmp_path / 'bad-math.html'
    out = tmp_path / 'bad-math-probe.json'
    subprocess.run(['node', str(BUILD), str(bad_math_lab), str(html)], check=True)
    res = subprocess.run(
        [sys.executable, str(PROBE), str(html), '--widths', '1440', '--themes', 'light', '--out', str(out)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is False
    assert any(not c['katex_ok'] for c in data['checks'])

    err_lab = tmp_path / 'err-lab.js'
    err_lab.write_text(
        _replace_once(
            EXAMPLE.read_text(encoding='utf-8'),
            'evaluate(state, mna) {',
            'evaluate(state, mna) {\n    if (state.causalStep === 3) throw new Error("intentional eval failure");',
        ),
        encoding='utf-8',
    )
    err_html = tmp_path / 'err.html'
    err_out = tmp_path / 'err-probe.json'
    subprocess.run(['node', str(BUILD), str(err_lab), str(err_html)], check=True)
    res2 = subprocess.run(
        [sys.executable, str(PROBE), str(err_html), '--widths', '1440', '--themes', 'light', '--out', str(err_out)],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 1, res2.stdout + res2.stderr
    data2 = json.loads(err_out.read_text(encoding='utf-8'))
    assert data2['ok'] is False
    assert any(c['console_errors'] or c['page_errors'] for c in data2['checks'])


def test_probe_flags_disallowed_external_url_and_exits_2_on_bad_usage(tmp_path):
    """미등록 외부 요청은 blocked_requests 결함(exit 1 + --out 기록), 사용법/런타임 오류는 exit 2."""
    html = tmp_path / 'ext.html'
    out = tmp_path / 'ext-probe.json'
    subprocess.run(['node', str(BUILD), str(EXAMPLE), str(html)], check=True)
    html.write_text(
        _replace_once(
            html.read_text(encoding='utf-8'),
            '</head>',
            '<link rel="stylesheet" href="https://example.invalid/blocked.css"></head>',
        ),
        encoding='utf-8',
    )
    res = subprocess.run(
        [sys.executable, str(PROBE), str(html), '--widths', '1440', '--themes', 'light', '--out', str(out)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, res.stdout + res.stderr
    assert out.is_file()
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is False
    assert 'https://example.invalid/blocked.css' in data['blocked_requests']
    assert any('https://example.invalid/blocked.css' in c['blocked_requests'] for c in data['checks'])

    res_missing = subprocess.run(
        [sys.executable, str(PROBE), str(tmp_path / 'missing.html'), '--out', str(tmp_path / 'missing.json')],
        capture_output=True,
        text=True,
    )
    assert res_missing.returncode == 2
    assert json.loads(res_missing.stdout)['status'] == 'error'
    assert not (tmp_path / 'missing.json').exists()

    no_runtime = tmp_path / 'plain.html'
    no_runtime_out = tmp_path / 'plain.json'
    no_runtime.write_text('<!doctype html><html><body><p>no lab runtime</p></body></html>', encoding='utf-8')
    res_plain = subprocess.run(
        [sys.executable, str(PROBE), str(no_runtime), '--widths', '1440', '--themes', 'light', '--out', str(no_runtime_out)],
        capture_output=True,
        text=True,
    )
    assert res_plain.returncode == 2
    assert json.loads(res_plain.stdout)['status'] == 'error'
    assert not no_runtime_out.exists()


def test_probe_ignores_fig_dot_and_enclosing_block_rect(tmp_path):
    """노드 점(.fig-dot)과 텍스트를 감싸는 블록 <rect>는 label_gaps 오탐을 내지 않는다."""
    extra_svg = (
        "  '  <line class=\"fig-ink\" x1=\"100\" y1=\"190\" x2=\"155\" y2=\"190\"/>',\n"
        "  '  <circle class=\"fig-dot\" cx=\"128\" cy=\"190\" r=\"4\"/>',\n"
        "  '  <text class=\"fig-text\" x=\"128\" y=\"177\" text-anchor=\"middle\">Vx</text>',\n"
        "  '  <rect class=\"fig-ink\" x=\"120\" y=\"20\" width=\"44\" height=\"24\" rx=\"3\"/>',\n"
        "  '  <text class=\"fig-text\" x=\"142\" y=\"36\" text-anchor=\"middle\">A</text>',\n"
        "  '  <g data-badges>',"
    )
    lab = tmp_path / 'dot-rect-lab.js'
    lab.write_text(
        _replace_once(EXAMPLE.read_text(encoding='utf-8'), "  '  <g data-badges>',", extra_svg),
        encoding='utf-8',
    )
    html = tmp_path / 'dot-rect.html'
    out = tmp_path / 'dot-rect-probe.json'
    subprocess.run(['node', str(BUILD), str(lab), str(html)], check=True)
    res = subprocess.run(
        [sys.executable, str(PROBE), str(html), '--widths', '1440,375', '--themes', 'light', '--out', str(out)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is True
    assert all(not c['label_gaps'] for c in data['checks'])
