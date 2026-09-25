#!/usr/bin/env python3
"""시험 폴더의 figures/figures.yaml에 적힌 bbox로 기출 PDF에서 그림을 잘라 PNG로 저장한다.

교과서 crop_figures.py와 달리 한 시험이 여러 PDF에 나뉘어 있어서 그림마다 pdf 경로를 적는다
(figures 폴더 기준 상대 경로).

사용법: python3 crop_exam.py <시험 폴더>    예) python3 crop_exam.py ../2021-1_중간
"""
import re
import sys
from pathlib import Path

import fitz
import yaml

FIG_ID_RE = re.compile(r"^Q[1-9]\d*(-[2-9]|-[1-9]\d+)?$")


def figure_filename(fig_id: str) -> str:
    return f"fig-{fig_id}.png"


def crop_all(exam_dir: Path) -> list[Path]:
    fig_dir = exam_dir / "figures"
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
    dpi = spec.get("dpi", 144)
    written = []
    for fig_id, fig in (spec.get("figures") or {}).items():
        if not isinstance(fig_id, str) or not FIG_ID_RE.match(fig_id):
            raise ValueError(f'그림 id {fig_id!r} 형식 오류: 따옴표로 감싼 "Q<번호>" 또는 "Q<번호>-<n>" (예: "Q2")')
        if not isinstance(fig, dict) or "pdf" not in fig:
            raise ValueError(f"{fig_id}: pdf 경로가 없음 (figures 폴더 기준 상대 경로로 적음)")
        pdf_path = (fig_dir / fig["pdf"]).resolve()
        if not pdf_path.is_file():
            raise ValueError(f"{fig_id}: PDF 없음 ({fig['pdf']})")
        with fitz.open(pdf_path) as doc:
            pdf_page = fig.get("pdf_page")
            if not isinstance(pdf_page, int) or not 1 <= pdf_page <= len(doc):
                raise ValueError(f"{fig_id}: pdf_page {pdf_page!r} 가 1..{len(doc)} 범위 밖")
            page = doc[pdf_page - 1]
            rect = fitz.Rect(*fig["bbox"])
            if not page.rect.contains(rect):
                raise ValueError(f"{fig_id}: bbox {fig['bbox']} 가 {pdf_page}쪽 범위 {tuple(page.rect)} 밖")
            out = fig_dir / figure_filename(fig_id)
            page.get_pixmap(dpi=dpi, clip=rect).save(out)
        written.append(out)
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("사용법: python3 crop_exam.py <시험 폴더>", file=sys.stderr)
        return 2
    try:
        paths = crop_all(Path(argv[1]))
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
