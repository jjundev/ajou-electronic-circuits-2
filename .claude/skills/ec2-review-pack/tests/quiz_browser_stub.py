"""A synthetic `browser_check.check` report for quiz scenario tests. It runs no browser.

The real check starts Chromium four times (about 16 s per call). The scenarios test
what pack and concept do with the report, so they get a report with the same keys,
counts, hashes and PNG screenshots. `EC2_TEST_BROWSER=real` runs the real check
everywhere, and `zero_problem[None]` always runs it and compares the two reports' shape.
"""
import hashlib
import json
from pathlib import Path

TRANSPORT = 'loopback HTTP, offline=True, local assets fulfilled'


def check(html, out, shots, *, source, viewports=None, themes=None):
    # Imported here: only the child process that runs concept has its folder on sys.path.
    import browser_check
    import concept
    from PIL import Image
    viewports = browser_check.VIEWPORTS if viewports is None else viewports
    themes = browser_check.THEMES if themes is None else themes
    html = Path(html).resolve()
    # The same reads as the real check, so a source.json it would reject (KeyError) fails here too.
    topics = {o['id']: o['topic_id'] for o in source['objectives']}
    items = [dict(it, topic_id=topics[it['objective']]) for it in source['items']]
    Path(source['repo']), Path(source['note'])
    detail = {'items_checked': len(items), 'items': len(items),
              'hints_checked': sum(bool(it.get('hint')) for it in items)}
    report = {'html': html.name, 'sha256': browser_check.sha256(html),
              'viewports': [f'{w}x{h}' for w, h in viewports], 'themes': list(themes),
              'runs': [], 'failures': [], 'transport': TRANSPORT}
    for w, h in viewports:
        for t in themes:
            report['runs'].append({'label': f'{w}x{h} {t}', 'detail': dict(detail),
                                   'failures': [], 'external_blocked': []})
    if shots is not None:
        shots = Path(shots)
        shots.mkdir(parents=True, exist_ok=True)
        for name in concept.shot_names(source):
            size = tuple(map(int, name.split('-', 1)[0].split('x')))
            color = tuple(hashlib.sha256(name.encode()).digest()[:3])
            Image.new('RGB', size, color).save(shots / name, format='PNG')
    report['status'] = 'fail' if report['failures'] else 'pass'
    report['stub'] = 'tests/quiz_browser_stub.py'
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    return report
