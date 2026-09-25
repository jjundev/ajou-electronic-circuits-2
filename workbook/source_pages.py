#!/usr/bin/env python3
"""원문 옮기기용 원본 페이지 도구. md frontmatter의 pdf_page로 원본 PDF 쪽을 찾는다.

사용법:
  python3 workbook/source_pages.py next <폴더> [--size 10]   원문 없는 md를 (원본, pdf_page, id) 순으로 N개
  python3 workbook/source_pages.py missing <폴더>            원문 없는 md 목록. 하나라도 있으면 종료 코드 1
  python3 workbook/source_pages.py render <md…> --out <폴더> [--dpi 200]
      pdf_page와 다음 쪽을 <id>-p<쪽>.png로. 글자 층이 있으면 <id>-p<쪽>.txt도.
<폴더>는 장 폴더(교과서/마이크로전자회로/ch09)나 시험 폴더(from_the_past/md/2023-1_기말).
원본 PDF: 교과서는 장 폴더 옆 <장 번호>장.pdf, 기출은 frontmatter source(md 기준 상대 경로).
"""
import argparse
import re
import sys
from pathlib import Path

import fitz

import paths  # noqa: F401  (기존 도구 import 경로 설정)
from check_md import split_frontmatter, split_sections

CHAPTER_RE = re.compile(r"^ch(\d+)$")
TEXT_MIN = 20       # 이보다 짧은 글자 층은 스캔 잡음으로 보고 버린다


class SourceError(Exception):
    pass


def problem_mds(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise SourceError(f"폴더 없음: {folder}")
    return sorted(p for p in folder.rglob("*.md") if p.name != "README.md")


def read_md(md):
    try:
        return split_frontmatter(Path(md).read_text(encoding="utf-8"))
    except ValueError as e:
        raise SourceError(f"{md}: {e}") from e


def pending(folder):
    """원문이 없는 md를 (source, pdf_page, id) 순으로. 같은 쪽의 예제·연습문제가 이어진다."""
    keyed = []
    for md in problem_mds(folder):
        meta, body = read_md(md)
        if any(title == "원문" for title, _ in split_sections(body)):
            continue
        keyed.append(((str(meta.get("source", "")), int(meta["pdf_page"]), str(meta["id"])), md))
    return [md for _, md in sorted(keyed)]


def source_pdf(md, meta):
    md = Path(md)
    if meta.get("kind") == "기출":
        return md.parent / str(meta["source"])
    chapter = md.parent.parent
    m = CHAPTER_RE.match(chapter.name)
    if not m:
        raise SourceError(f"장 폴더를 알 수 없음: {md}")
    return chapter.parent / f"{int(m.group(1))}장.pdf"


def render(mds, out, dpi=200):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for md in mds:
        meta, _ = read_md(md)
        pdf = source_pdf(md, meta)
        if not pdf.exists():
            raise SourceError(f"원본 PDF 없음: {pdf}")
        first = int(meta["pdf_page"])
        with fitz.open(pdf) as doc:
            for page_no in (first, first + 1):
                if page_no > doc.page_count:
                    continue
                page = doc[page_no - 1]
                stem = out / f"{meta['id']}-p{page_no}"
                png = stem.with_name(stem.name + ".png")
                page.get_pixmap(dpi=dpi).save(str(png))
                written.append(png)
                text = page.get_text().strip()
                if len(text) >= TEXT_MIN:
                    txt = stem.with_name(stem.name + ".txt")
                    txt.write_text(text + "\n", encoding="utf-8")
                    written.append(txt)
    return written


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="source_pages.py", description="원문 옮기기용 원본 페이지 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    nxt = sub.add_parser("next", help="원문 없는 md를 N개")
    nxt.add_argument("folder", type=Path)
    nxt.add_argument("--size", type=int, default=10)
    mis = sub.add_parser("missing", help="원문 없는 md 전부 (있으면 종료 코드 1)")
    mis.add_argument("folder", type=Path)
    ren = sub.add_parser("render", help="pdf_page와 다음 쪽을 PNG로")
    ren.add_argument("mds", nargs="+", type=Path)
    ren.add_argument("--out", type=Path, required=True)
    ren.add_argument("--dpi", type=int, default=200)
    return ap.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)
    try:
        if args.cmd == "next":
            for md in pending(args.folder)[:args.size]:
                print(md)
        elif args.cmd == "missing":
            left = pending(args.folder)
            for md in left:
                print(md)
            print(f"원문 없음: {len(left)}개", file=sys.stderr)
            return 1 if left else 0
        else:
            for f in render(args.mds, args.out, args.dpi):
                print(f)
    except (SourceError, KeyError, OSError) as e:
        msg = e.args[0] if isinstance(e, SourceError) else f"{type(e).__name__}: {e}"
        print(f"ERROR {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
