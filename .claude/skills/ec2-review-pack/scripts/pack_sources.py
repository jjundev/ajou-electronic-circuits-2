"""Machine source-prep: map each session's STT and extract every lecture PDF."""
from pathlib import Path
import re

import pack_flow as f

LECTURE = re.compile(r'2026F_Lec(\d+)_')


def lecture_pdfs(repo: Path) -> list[tuple[int, Path]]:
    found = []
    for path in sorted(Path(repo).glob('강의노트/2026F_Lec*_*.pdf')):
        if match := LECTURE.match(f.nfc_path(path.name).name):
            found.append((int(match[1]), path))
    return sorted(found, key=lambda item: (item[0], f.nfc_path(item[1].name).name))


def read_pages(path: Path) -> list[str] | None:
    import pymupdf
    try:
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                return None
            return [page.get_text() for page in doc]
    except Exception:
        # A damaged lecture PDF is recorded as missing; it never fails the RUN.
        return None


def prepare_sources(repo: Path, sessions: list[str], stt: dict[str, Path], root: Path) -> dict[str, Path]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    pdfs, missing, chunks = [], [], []
    for number, path in lecture_pdfs(repo):
        name = f.nfc_path(path.name).name
        pages = read_pages(path)
        if pages is None:
            missing.append(f'{name}: unreadable')
            continue
        pdfs.append(str(f.nfc_path(path)))
        for index, text in enumerate(pages, 1):
            chunks.append(f'=== L{number:02d} s{index} ===\n{text.rstrip()}\n')
    if not pdfs and not missing:
        missing.append('강의노트 PDF 없음')
    source_map = root/'source-map.json'
    slides = root/'slides.txt'
    f._atomic_json(source_map, dict(schema_version=1, sessions=[
        dict(date=date, stt=str(f.nfc_path(stt[date])), pdfs=list(pdfs), status='ready', missing=list(missing))
        for date in sessions]))
    with open(slides, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(''.join(chunks))
    return {'source-map.json': source_map, 'slides.txt': slides}
