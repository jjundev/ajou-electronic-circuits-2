#!/usr/bin/env python3
"""문제 md → 문제지·답안지 PDF.

사용법:
  python3 workbook/build_workbook.py ch09                          # 교과서 장 하나 (책 순서)
  python3 workbook/build_workbook.py 2023-1_기말                   # 기출 회차 하나
  python3 workbook/build_workbook.py --ids P9.05,E9.01 --name 샘플  # 고른 문제 (적은 순서)
  python3 workbook/build_workbook.py --all                         # 모든 장과 기출
  옵션: --json-only (PDF 없이 JSON·HTML만), --pdf-dir, --build-dir

결과: workbook/pdf/<이름>-문제.pdf, <이름>-답안.pdf (커밋 대상)
      workbook/build/<이름>-문제.json, .html … (중간 산출물, git 무시)
종료 코드: 0 성공, 1 md 오류·렌더링 실패·쪽 넘침, 2 사용법·대상 오류
"""
import argparse
import json
import sys
from pathlib import Path

import paths
from assemble import MODE_SUFFIX, BuildError, all_selections, build_data, ids_selection, resolve_target
from render import RenderError, inject, load_template, render_pdf


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="build_workbook.py", description="문제 md → 문제지·답안지 PDF")
    ap.add_argument("target", nargs="?", help="ch09 같은 장 폴더 또는 2023-1_기말 같은 기출 폴더")
    ap.add_argument("--ids", help="쉼표로 구분한 문제 id (예: P9.05,E9.01,2023-1_기말-Q1)")
    ap.add_argument("--name", help="--ids 묶음의 이름 (파일 이름과 제목)")
    ap.add_argument("--all", action="store_true", help="모든 장과 기출 회차")
    ap.add_argument("--json-only", action="store_true", help="PDF 없이 JSON·HTML만 만든다")
    ap.add_argument("--pdf-dir", type=Path, default=paths.WORKBOOK / "pdf")
    ap.add_argument("--build-dir", type=Path, default=paths.WORKBOOK / "build")
    args = ap.parse_args(argv[1:])
    if sum([bool(args.target), bool(args.ids), args.all]) != 1:
        ap.error("대상은 target, --ids, --all 중 하나만 준다")
    if args.ids and not args.name:
        ap.error("--ids 에는 --name 이 필요하다")
    return args


def selections(args):
    if args.all:
        return all_selections()
    if args.ids:
        return [ids_selection(args.ids.split(","), args.name)]
    return [resolve_target(args.target)]


def build_one(sel, args):
    """선택 하나를 문제지·답안지로 만든다. 넘친 쪽을 '<파일 이름>: <id>' 목록으로 돌려준다."""
    overflow = []
    for mode, suffix in MODE_SUFFIX.items():
        data = build_data(sel, mode)
        stem = f"{sel.name}-{suffix}"
        args.build_dir.mkdir(parents=True, exist_ok=True)
        (args.build_dir / f"{stem}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        html_path = args.build_dir / f"{stem}.html"
        html_path.write_text(inject(load_template(mode), data), encoding="utf-8")
        print(html_path)
        if args.json_only:
            continue
        args.pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = args.pdf_dir / f"{stem}.pdf"
        overflow += [f"{stem}: {x}" for x in render_pdf(html_path, pdf_path)]
        print(pdf_path)
    return overflow


def main(argv):
    args = parse_args(argv)
    try:
        sels = selections(args)
    except KeyError as e:
        print(f"ERROR {e.args[0]}", file=sys.stderr)
        return 2
    except BuildError as e:
        for msg in e.errors:
            print(f"ERROR {msg}", file=sys.stderr)
        return 2
    code, overflow = 0, []
    for sel in sels:
        try:
            overflow += build_one(sel, args)
        except BuildError as e:
            for msg in e.errors:
                print(f"ERROR {msg}", file=sys.stderr)
            code = 1
        except RenderError as e:
            print(f"ERROR {sel.name}: {e}", file=sys.stderr)
            code = 1
    for item in overflow:
        print(f"OVERFLOW {item}", file=sys.stderr)
    return 1 if overflow else code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
