"""Per-review-pack display titles; source problem titles remain untouched."""
import json
import hashlib
import re
from pathlib import Path


class DisplayTitlesError(ValueError):
    pass


def load_display_titles(path, ids):
    """Read an exact ID-to-unnumbered-title map; fail closed on stale selections."""
    try:
        titles = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise DisplayTitlesError(f'표시 제목 파일 읽기 실패: {exc}') from exc
    if not isinstance(titles, dict) or set(titles) != set(ids):
        raise DisplayTitlesError('표시 제목의 문항 집합이 선택 목록과 다릅니다')
    for title in titles.values():
        if (not isinstance(title, str) or not title.strip() or title != title.strip()
                or '\n' in title or '\r' in title or re.search(r'\bFig(?:ure)?\.?\s*\d|^P\d+\.', title, re.I)):
            raise DisplayTitlesError('표시 제목은 Fig 번호와 P번호 접두사 없는 한 줄이어야 합니다')
    return titles


def numbered_title(titles, pid, number):
    return f'P{number}. {titles[pid]}'


def apply_display_titles(data, titles):
    for number, problem in enumerate(data['problems'], 1):
        problem['source_title'] = problem['title']
        problem['title'] = numbered_title(titles, problem['id'], number)
    return data


def reviewed_title_path(overlay, repo, explicit=None):
    """Use the title map bound by the approved overlay, including when flag omitted."""
    bound = [(name, digest) for name, digest in overlay['source_inputs'].items()
             if Path(name).name == 'display-titles.json' and Path(name).parent.name == '.assets']
    if not bound:
        if explicit is not None:
            raise DisplayTitlesError('표시 제목은 승인된 답안 입력에 포함되어야 합니다: 다시 검토 필요')
        return None  # Older reviewed packs retain their source titles.
    if len(bound) != 1:
        raise DisplayTitlesError('승인된 표시 제목 파일은 정확히 하나여야 합니다')
    name, digest = bound[0]
    title_path = Path(repo) / name
    try:
        if hashlib.sha256(title_path.read_bytes()).hexdigest() != digest:
            raise DisplayTitlesError('승인된 표시 제목 파일이 변경되었습니다')
        if explicit is not None and hashlib.sha256(Path(explicit).read_bytes()).hexdigest() != digest:
            raise DisplayTitlesError('표시 제목이 승인된 답안 입력과 다릅니다: 다시 검토 필요')
    except OSError as exc:
        raise DisplayTitlesError(f'승인된 표시 제목 읽기 실패: {exc}') from exc
    return title_path
