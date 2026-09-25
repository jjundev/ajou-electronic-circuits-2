"""기출 도구 테스트 공용 픽스처."""
from pathlib import Path

import fitz


def make_pdf(path: Path, pages: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=200, height=100)
    doc.save(str(path))
