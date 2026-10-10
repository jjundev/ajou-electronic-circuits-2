"""표지 + 노션에서 내보낸 본문 PDF → BB 제출본.

    python3 -m scripts.ec2_report.merge --n 1 [--body P] [--date 2026.10.30] [--keep-body]

본문 원본은 병합 검증이 통과한 뒤 ~/.Trash 로 옮긴다 (--keep-body 면 그대로 둔다).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from . import config
from .check import _IMAGE_LOCAL
from .cover import A4_H_MM, A4_W_MM, make_cover

_VERSION = re.compile(r"(?<![A-Za-z])v(\d+)")
_TITLE_VERSION = re.compile(r"설계과제\s*\d+\s*보고서\s+v\d+")
_OLD_REF = re.compile(r"(?<![\w.])\d\s*-\s*\(\s*[a-z]\s*\)")
TRASH = Path.home() / ".Trash"


@dataclass
class BodySource:
    path: Path
    origin: Path


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _norm(s: str) -> str:
    """노션 내보내기 이름은 공백 대신 밑줄을 쓴다 (`<uuid>_전자회로2_설계과제1_보고서.pdf`)."""
    return _nfc(s).replace("_", " ")


def _default_dirs(n: int, root: Path) -> list[Path]:
    info = config.load_course_info(root)
    return [config.paths(n, root, info).report_md.parent, Path.home() / "Downloads"]


def _zip_pdfs(zf: zipfile.ZipFile) -> list[str]:
    """zip 안 PDF 멤버. Finder 가 붙이는 `__MACOSX/` 와 `._*` 는 뺀다."""
    return [m for m in zf.namelist()
            if m.lower().endswith(".pdf") and not m.startswith("__MACOSX/")
            and not Path(m).name.startswith("._")]


def _zip_inner_name(path: Path) -> str | None:
    """노션 내보내기 zip(`Export-<id>.zip`)은 이름에 제목이 없다 — PDF 가 1개면 그 이름."""
    try:
        with zipfile.ZipFile(path) as zf:
            pdfs = _zip_pdfs(zf)
    except zipfile.BadZipFile:
        return None
    return _norm(Path(pdfs[0]).name) if len(pdfs) == 1 else None


def _open_source(origin: Path) -> BodySource:
    if origin.suffix.lower() != ".zip":
        return BodySource(origin, origin)
    with zipfile.ZipFile(origin) as zf:
        pdfs = _zip_pdfs(zf)
        if len(pdfs) != 1:
            raise ValueError(f"zip 안의 PDF 가 {len(pdfs)}개입니다 (1개여야 함): {origin}")
        out = Path(tempfile.mkdtemp(prefix="ec2_body_")) / "body.pdf"
        out.write_bytes(zf.read(pdfs[0]))
    return BodySource(out, origin)


def find_body(n: int, root: Path, search_dirs: list[Path] | None = None) -> BodySource:
    root = Path(root)
    dirs = search_dirs if search_dirs is not None else _default_dirs(n, root)
    p = config.paths(n, root, config.load_course_info(root))
    excluded = {_norm(p.cover_pdf.name), _norm(p.final_pdf.name)}
    key = f"설계과제{n} 보고서"
    found = []
    for d in dirs:
        if not Path(d).is_dir():
            continue
        for f in Path(d).iterdir():
            name = _norm(f.name)
            if not f.is_file() or f.suffix.lower() not in (".pdf", ".zip") or name in excluded:
                continue
            if key not in name and f.suffix.lower() == ".zip":
                name = _zip_inner_name(f) or ""
            if key in name:
                m = _VERSION.search(name)
                found.append((int(m.group(1)) if m else 0, f.stat().st_mtime, f))
    if not found:
        where = ", ".join(str(d) for d in dirs)
        raise FileNotFoundError(f"'{key}' 이 이름에 든 PDF/zip 을 찾지 못했습니다: {where}")
    found.sort(key=lambda t: (t[0], t[1]))
    return _open_source(found[-1][2])


def lint_body(text: str, images: int, expected_images: int) -> list[str]:
    """노션에서 내보낸 본문 PDF 의 흔적 점검. 경고만 돌려주고 병합은 막지 않는다.

    텍스트 추출은 수식을 깨뜨리므로 오검출이 적은 세 가지만 본다.
    """
    out = []
    m = _TITLE_VERSION.search(text)
    if m:
        out.append(f"본문 제목에 판본 번호가 있다: '{m.group()}' — 노션 페이지 제목에서 vN 을 지운다")
    if images != expected_images:
        out.append(f"본문 PDF 그림이 {images}장인데 md 의 그림 자리는 {expected_images}장이다 — "
                   "노션에 빠진 그림이 없는지 본다")
    refs = sorted({re.sub(r"\s", "", r) for r in _OLD_REF.findall(text)})
    if refs:
        out.append("예전 문항 번호 표기가 남았다: " + ", ".join(refs)
                   + " — 'Spice Problem (a)' 처럼 대절 이름으로 고친다")
    return out


def _body_lint(pdf: Path, report_md: Path) -> list[str]:
    reader = PdfReader(pdf)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    images = sum(len(page.images) for page in reader.pages)
    expected = 0
    if report_md.is_file():
        expected = sum(1 for t in _IMAGE_LOCAL.findall(report_md.read_text(encoding="utf-8"))
                       if not t.startswith(("http://", "https://", "data:")))
    return lint_body(text, images, expected)


def _to_trash(src: Path) -> Path:
    """src 를 휴지통으로 옮기고 새 경로를 돌려준다. 같은 이름이 있으면 ' 2', ' 3' 을 붙인다."""
    if not TRASH.is_dir():
        raise OSError(f"휴지통 폴더가 없습니다: {TRASH}")
    dest, k = TRASH / src.name, 2
    while dest.exists():
        dest = TRASH / f"{src.stem} {k}{src.suffix}"
        k += 1
    shutil.move(str(src), str(dest))
    return dest


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
    warnings = _body_lint(src.path, p.report_md)

    trashed = None
    if not keep_body and src.origin.resolve() != p.final_pdf.resolve():
        try:
            trashed = _to_trash(src.origin)
        except OSError as e:
            warnings.append(f"본문 원본을 휴지통으로 옮기지 못해 그대로 두었다: {e}")
    return {"output": p.final_pdf, "pages": result["pages"], "cover": cover,
            "body_origin": src.origin, "trashed": trashed, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m scripts.ec2_report.merge")
    ap.add_argument("--n", type=int, required=True, help="설계과제 번호")
    ap.add_argument("--body", type=Path, help="본문 PDF 또는 zip (생략하면 자동 탐색)")
    ap.add_argument("--date", help="제출일 (기본: 오늘)")
    ap.add_argument("--keep-body", action="store_true", help="병합 후 본문 원본을 휴지통으로 옮기지 않는다")
    a = ap.parse_args(argv)
    r = merge(a.n, a.body, a.date, a.keep_body)
    print(f"최종본: {r['output']}")
    print(f"쪽수: {r['pages']} (표지 1 + 본문 {r['pages'] - 1})")
    print(f"본문 원본: {r['body_origin']} "
          f"({'휴지통으로 옮김: ' + str(r['trashed']) if r['trashed'] else '그대로 둠'})")
    for w in r["warnings"]:
        print(f"경고: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
