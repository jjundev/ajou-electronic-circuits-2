#!/usr/bin/env python3
"""figures.yaml에 적힌 bbox로 PDF에서 그림을 잘라 PNG로 저장한다.

사용법: python3 crop_figures.py <장 폴더>    예) python3 crop_figures.py ../ch09
"""
import sys
from pathlib import Path

import fitz
import yaml


def figure_filename(fig_id: str) -> str:
    chapter, number = fig_id.split(".")
    return f"fig{chapter}-{int(number):02d}.png"


def crop_all(ch_dir: Path) -> list[Path]:
    fig_dir = ch_dir / "figures"
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8"))
    pdf_path = (fig_dir / spec["pdf"]).resolve()
    dpi = spec.get("dpi", 144)
    written = []
    with fitz.open(pdf_path) as doc:
        for fig_id, fig in spec["figures"].items():
            if not isinstance(fig_id, str):
                raise ValueError(f"그림 id {fig_id!r} 는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
            page = doc[fig["pdf_page"] - 1]
            rect = fitz.Rect(*fig["bbox"])
            if not page.rect.contains(rect):
                raise ValueError(f"{fig_id}: bbox {fig['bbox']} 가 {fig['pdf_page']}쪽 범위 {tuple(page.rect)} 밖")
            out = fig_dir / figure_filename(fig_id)
            page.get_pixmap(dpi=dpi, clip=rect).save(out)
            written.append(out)
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("사용법: python3 crop_figures.py <장 폴더>", file=sys.stderr)
        return 2
    for path in crop_all(Path(argv[1])):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
