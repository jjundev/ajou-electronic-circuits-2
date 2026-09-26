#!/usr/bin/env python3
"""figures.yaml에 적힌 bbox로 PDF에서 그림을 잘라 PNG로 저장한다.

사용법: python3 crop_figures.py <장 폴더>    예) python3 crop_figures.py ../ch09

그림 항목에 crops: {이름: bbox}가 있으면 같은 쪽에서 잘라 fig<장>-<NN>-<이름>.png로도 저장한다.
"""
import re
import sys
from pathlib import Path

import fitz
import yaml

CROP_NAME_RE = re.compile(r"^[a-z0-9]+$")


def figure_filename(fig_id: str, crop: str | None = None) -> str:
    chapter, number = fig_id.split(".")
    suffix = f"-{crop}" if crop else ""
    return f"fig{chapter}-{int(number):02d}{suffix}.png"


def _clip(page, bbox, where):
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError(f"{where}: bbox {bbox!r} 는 [x0, y0, x1, y1] 네 값이어야 함")
    for v in bbox:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"{where}: bbox {bbox!r} 에 숫자가 아닌 값 {v!r} 이 있음")
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"{where}: bbox {bbox!r} 가 뒤집혔거나 넓이 0 (x1<=x0 또는 y1<=y0)")
    rect = fitz.Rect(*bbox)
    if not page.rect.contains(rect):
        raise ValueError(f"{where}: bbox {bbox} 가 쪽 범위 밖 (쪽 크기 {tuple(page.rect)})")
    return rect


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
            pdf_page = fig["pdf_page"]
            if not isinstance(pdf_page, int) or not 1 <= pdf_page <= len(doc):
                raise ValueError(f"{fig_id}: pdf_page {pdf_page!r} 가 1..{len(doc)} 범위 밖")
            page = doc[pdf_page - 1]
            crops = fig.get("crops") or {}
            if not isinstance(crops, dict):
                raise ValueError(f"{fig_id}: crops 는 매핑(이름: bbox)이어야 함, 받은 값 {crops!r}")
            jobs = [(None, fig["bbox"])] + list(crops.items())
            for name, bbox in jobs:
                if name is not None and not (isinstance(name, str) and CROP_NAME_RE.fullmatch(name)):
                    raise ValueError(f"{fig_id}: 크롭 이름 {name!r} 형식 오류 (소문자·숫자만, 예: a, abc, ce)")
                where = fig_id if name is None else f"{fig_id} 크롭 {name}"
                rect = _clip(page, bbox, where)
                out = fig_dir / figure_filename(fig_id, name)
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
