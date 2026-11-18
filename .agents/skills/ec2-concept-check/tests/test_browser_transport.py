"""Synthetic content tests offline browser mechanics, never learning approval."""
from pathlib import Path
import sys

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))

import browser_check
import concept
import _paths


def synthetic_quiz(tmp_path):
    note = tmp_path / 'note.html'
    note.write_text('<article id="synthetic">Synthetic test only</article>')
    data = {
        'repo': str(_paths.REPO), 'pack': str(_paths.REPO / '복습노트/0000'),
        'range': '0000', 'slug': 'Synthetic', 'note': str(note),
        'objectives': [{'id': 'o1', 'topic_id': 'synthetic'}],
        'items': [{
            'id': 'q1', 'objective': 'o1', 'format': 'mcq', 'title': '합성 검사',
            'stem_html': '<p>$1+1$의 값은 무엇인가요?</p>', 'hint': '하나에 하나를 더해요.',
            'answer': 'B',
            'options': [
                {'id': 'A', 'text': '1', 'why': '더한 하나가 빠졌어요.', 'misconception': '더하기를 생략함'},
                {'id': 'B', 'text': '2', 'why': '하나에 하나를 더하면 둘이에요.'},
                {'id': 'C', 'text': '3', 'why': '하나를 더 세었어요.', 'misconception': '중복 계산함'},
                {'id': 'D', 'text': '4', 'why': '두 번씩 세었어요.', 'misconception': '두 배로 셈'},
            ],
        }],
    }
    html = concept.build(tmp_path / 'run', data)
    return html, data


def test_offline_local_assets_work_without_file_navigation(tmp_path):
    html, data = synthetic_quiz(tmp_path)
    report = browser_check.check(html, tmp_path / 'browser.json', None, source=data,
                                 viewports=[(375, 812)], themes=['light'])
    assert report['status'] == 'pass', report['failures']
    assert report['transport'] == 'loopback HTTP, offline=True, local assets fulfilled'
    assert report['runs'][0]['external_blocked'] == []


def test_offline_local_asset_transport_still_blocks_external_http(tmp_path):
    html, data = synthetic_quiz(tmp_path)
    external = 'https://example.invalid/ec2-gate-test'
    html.write_text(html.read_text().replace('</body>',
        f'<script>fetch("{external}").catch(() => {{}});</script></body>'))
    report = browser_check.check(html, tmp_path / 'browser.json', None, source=data,
                                 viewports=[(375, 812)], themes=['light'])
    assert report['status'] == 'fail'
    assert external in report['runs'][0]['external_blocked']
