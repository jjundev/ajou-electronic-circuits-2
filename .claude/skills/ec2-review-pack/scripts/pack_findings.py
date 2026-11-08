"""Audit findings and the task that owns each one.

Review reports list findings as `- [<id>] ...` under `## Critical`,
`## Important` and `## Minor`. A content fix is the one content round a RUN
gets, so every finding must reach its owner in that request or be waived.
"""
from __future__ import annotations

from pathlib import Path
import re

SEVERITIES = ('Critical', 'Important', 'Minor')
_HEADING = re.compile(r'^(#{2,4})\s+(.+?)\s*$')
_ITEM = re.compile(r'^\s*[-*]\s+\[([^\]]+)\]')


def blocking_findings(report_md: Path) -> list[tuple[str, str]]:
    """(severity, id) for each `- [id]` item under the three severity sections, in order."""
    found, severity = [], None
    for line in Path(report_md).read_text(encoding='utf-8').splitlines():
        heading = _HEADING.match(line)
        if heading:
            # '## Important (2)' and '### Critical' open a section; another '##' heading closes it,
            # while a deeper non-severity subheading stays inside the current section.
            word = re.match(r'[A-Za-z]+', heading[2])
            name = word[0].capitalize() if word else ''
            if name in SEVERITIES: severity = name
            elif len(heading[1]) == 2: severity = None
            continue
        item = _ITEM.match(line)
        if severity and item:
            found += [(severity, x.strip()) for x in item[1].split(',') if x.strip()]
    return found


def owner_of(item_id: str, manifest: dict) -> str:
    """Topic or section ID → author-<section>; problem ID → selection; else scope-final."""
    if item_id in {p.get('id') for p in manifest.get('problems', []) if isinstance(p, dict)}:
        return 'selection'
    for section in manifest.get('sections', []):
        if not isinstance(section, dict): continue
        topics = {t.get('id') for t in section.get('topics', []) if isinstance(t, dict)}
        if item_id == section.get('id') or item_id in topics:
            return 'author-' + section['id']
    return 'scope-final'
