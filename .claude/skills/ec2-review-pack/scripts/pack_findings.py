"""Audit findings and the task that owns each one.

Review reports list findings as `- [<id>] ...` under `## Critical`,
`## Important` and `## Minor`. A content fix is the one content round a RUN
gets, so every finding must reach its owner in that request or be waived.
"""
from __future__ import annotations

from pathlib import Path
import re

SEVERITIES = ('Critical', 'Important', 'Minor')
_HEADING = re.compile(r'^##\s+(.+?)\s*$')
_ITEM = re.compile(r'^\s*[-*]\s+\[([^\]\s]+)\]')


def blocking_findings(report_md: Path) -> list[tuple[str, str]]:
    """(severity, id) for each `- [id]` item under the three severity sections, in order."""
    found, severity = [], None
    for line in Path(report_md).read_text(encoding='utf-8').splitlines():
        heading = _HEADING.match(line)
        if heading:
            name = heading[1].strip().capitalize()
            severity = name if name in SEVERITIES else None
            continue
        item = _ITEM.match(line)
        if severity and item: found.append((severity, item[1]))
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
