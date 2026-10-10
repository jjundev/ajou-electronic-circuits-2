"""표지 + 노션에서 내보낸 본문 PDF → BB 제출본.

    python3 -m scripts.ec2_report.merge --n 1 [--body P] [--date 2026.10.30] [--keep-body]
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from . import config
from .cover import A4_H_MM, A4_W_MM, make_cover

_VERSION = re.compile(r"(?<![A-Za-z])v(\d+)")


@dataclass
class BodySource:
    path: Path
    origin: Path


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _default_dirs(n: int, root: Path) -> list[Path]:
    info = config.load_course_info(root)
    return [config.paths(n, root, info).report_md.parent, Path.home() / "Downloads"]


def _open_source(origin: Path) -> BodySource:
    if origin.suffix.lower() != ".zip":
        return BodySource(origin, origin)
    with zipfile.ZipFile(origin) as zf:
        pdfs = [m for m in zf.namelist() if m.lower().endswith(".pdf") and not m.endswith("/")]
        if len(pdfs) != 1:
            raise ValueError(f"zip 안의 PDF 가 {len(pdfs)}개입니다 (1개여야 함): {origin}")
        out = Path(tempfile.mkdtemp(prefix="ec2_body_")) / "body.pdf"
        out.write_bytes(zf.read(pdfs[0]))
    return BodySource(out, origin)


def find_body(n: int, root: Path, search_dirs: list[Path] | None = None) -> BodySource:
    root = Path(root)
    dirs = search_dirs if search_dirs is not None else _default_dirs(n, root)
    p = config.paths(n, root, config.load_course_info(root))
    excluded = {_nfc(p.cover_pdf.name), _nfc(p.final_pdf.name)}
    key = f"설계과제{n} 보고서"
    found = []
    for d in dirs:
        if not Path(d).is_dir():
            continue
        for f in Path(d).iterdir():
            name = _nfc(f.name)
            if (f.is_file() and f.suffix.lower() in (".pdf", ".zip")
                    and key in name and name not in excluded):
                m = _VERSION.search(name)
                found.append((int(m.group(1)) if m else 0, f.stat().st_mtime, f))
    if not found:
        where = ", ".join(str(d) for d in dirs)
        raise FileNotFoundError(f"'{key}' 이 이름에 든 PDF/zip 을 찾지 못했습니다: {where}")
    found.sort(key=lambda t: (t[0], t[1]))
    return _open_source(found[-1][2])


def verify_merged(pdf: Path, expected_pages: int) -> dict:
    reader = PdfReader(pdf)
    pages = len(reader.pages)
    if pages != expected_pages:
        raise ValueError(f"쪽수 불일치: 기대 {expected_pages}쪽, 실제 {pages}쪽")
    box = reader.pages[0].mediabox
    w, h = float(box.width) * 25.4 / 72, float(box.height) * 25.4 / 72
    if not (A4_W_MM[0] <= w <= A4_W_MM[1] and A4_H_MM[0] <= h <= A4_H_MM[1]):
        raise ValueError(f"1쪽이 A4 가 아닙니다: {w:.1f} x {h:.1f} mm")
    return {"pages": pages, "page1_mm": (round(w, 1), round(h, 1))}


def merge(n: int, body: Path | None = None, date: str | None = None,
          keep_body: bool = False, root: Path | None = None) -> dict:
    root = Path(root) if root else config.find_root()
    info = config.load_course_info(root)
    p = config.paths(n, root, info)
    src = _open_source(Path(body)) if body else find_body(n, root, _default_dirs(n, root))
    cover = make_cover(n, date, root)

    body_pages = len(PdfReader(src.path).pages)
    writer = PdfWriter()
    writer.append(str(cover))
    writer.append(str(src.path))
    writer.metadata = {"/Title": config.document_title(n), "/Author": info["student_name"]}
    p.final_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(p.final_pdf, "wb") as f:
        writer.write(f)
    result = verify_merged(p.final_pdf, 1 + body_pages)

    deleted = False
    if not keep_body and src.origin.resolve() != p.final_pdf.resolve():
        try:
            src.origin.unlink()
            deleted = True
        except OSError:
            print("경고: 본문 원본을 지우지 못했습니다", file=sys.stderr)
    return {"output": p.final_pdf, "pages": result["pages"], "cover": cover,
            "body_origin": src.origin, "deleted": deleted}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m scripts.ec2_report.merge")
    ap.add_argument("--n", type=int, required=True, help="설계과제 번호")
    ap.add_argument("--body", type=Path, help="본문 PDF 또는 zip (생략하면 자동 탐색)")
    ap.add_argument("--date", help="제출일 (기본: 오늘)")
    ap.add_argument("--keep-body", action="store_true", help="병합 후 본문 원본을 지우지 않는다")
    a = ap.parse_args(argv)
    r = merge(a.n, a.body, a.date, a.keep_body)
    print(f"최종본: {r['output']}")
    print(f"쪽수: {r['pages']} (표지 1 + 본문 {r['pages'] - 1})")
    print(f"본문 원본: {r['body_origin']} ({'삭제함' if r['deleted'] else '보존'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
