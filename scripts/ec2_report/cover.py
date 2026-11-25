"""설계과제 보고서 표지 (한글 IEEE 윤리강령 포함 A4 1장)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import config
from .html2pdf import html_to_pdf

TEMPLATE = Path(__file__).parent / "templates" / "cover.html"
PLACEHOLDERS = ("TITLE", "COURSE", "CLASS_SECTION", "DEPARTMENT", "SUBMIT_DATE",
                "PROFESSOR", "STUDENT_ID", "STUDENT_NAME")
A4_W_MM = (205, 215)
A4_H_MM = (290, 302)


def cover_title(n: int) -> str:
    return f"설계과제 {n} 보고서"


def render_cover_html(title: str, info: dict, submit_date: str) -> str:
    values = {
        "TITLE": title,
        "COURSE": info["course"],
        "CLASS_SECTION": info["class_section"],
        "DEPARTMENT": info["department"],
        "SUBMIT_DATE": submit_date,
        "PROFESSOR": info["professor"],
        "STUDENT_ID": info["student_id"],
        "STUDENT_NAME": info["student_name"],
    }
    html = TEMPLATE.read_text(encoding="utf-8")
    for key in PLACEHOLDERS:
        html = html.replace("{{" + key + "}}", str(values[key]))
    if "{{" in html:
        raise ValueError("표지 템플릿에 채우지 못한 자리표시자가 남았습니다")
    return html


def _page_mm(pdf: Path) -> tuple[int, float, float]:
    from pypdf import PdfReader
    reader = PdfReader(pdf)
    box = reader.pages[0].mediabox
    return len(reader.pages), float(box.width) * 25.4 / 72, float(box.height) * 25.4 / 72


def make_cover(n: int, submit_date: str | None = None, root: Path | None = None) -> Path:
    root = Path(root) if root else config.find_root()
    info = config.load_course_info(root)
    missing = config.missing_identity(info)
    if missing:
        raise ValueError("과목정보.md 신원 미확정: " + ", ".join(missing))
    p = config.paths(n, root, info)
    date = submit_date or datetime.now().strftime(info["date_format"])
    p.cover_html.parent.mkdir(parents=True, exist_ok=True)
    p.cover_html.write_text(render_cover_html(cover_title(n), info, date), encoding="utf-8", newline="\n")
    html_to_pdf(p.cover_html, p.cover_pdf, chrome=info["chrome"])
    pages, w, h = _page_mm(p.cover_pdf)
    if pages != 1 or not (A4_W_MM[0] <= w <= A4_W_MM[1] and A4_H_MM[0] <= h <= A4_H_MM[1]):
        raise ValueError(f"표지가 A4 1쪽이 아닙니다: {pages}쪽, {w:.1f}x{h:.1f}mm")
    return p.cover_pdf
