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
from display_titles import DisplayTitlesError, load_display_titles, apply_display_titles, reviewed_title_path
from assemble import MODE_SUFFIX, BuildError, all_selections, build_data, ids_selection, resolve_target, nfc
from answer_overlay import AnswerOverlayError, load_answer_overlay, apply_answer_overlay
from pack_paths import PackPaths
from render import RenderError, inject, load_template, render_pdf, measure_typography
from review_selection import load_selection, apply_selection, reviewed_selection_path


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="build_workbook.py", description="문제 md → 문제지·답안지 PDF")
    ap.add_argument("target", nargs="?", help="ch09 같은 장 폴더 또는 2023-1_기말 같은 기출 폴더")
    ap.add_argument("--ids", help="쉼표로 구분한 문제 id (예: P9.05,E9.01,2023-1_기말-Q1)")
    ap.add_argument("--name", help="--ids 묶음의 이름 (파일 이름과 제목)")
    ap.add_argument("--all", action="store_true", help="모든 장과 기출 회차")
    ap.add_argument("--mode", choices=("both", "problems", "answers"), default="both",
                    help="문제지·답안지 모두 또는 하나만 생성")
    ap.add_argument("--display-titles", type=Path, help="복습팩의 ID별 짧은 표시 제목 JSON")
    ap.add_argument('--public-pack', type=Path)
    ap.add_argument('--candidate-pack', type=Path)
    ap.add_argument("--answer-overlay", type=Path, help="현재 검토를 통과한 발행 답안 overlay")
    ap.add_argument('--selection', type=Path, help='복습팩의 승인 입력에 포함할 selection.json')
    ap.add_argument("--json-only", action="store_true", help="PDF 없이 JSON·HTML만 만든다")
    ap.add_argument("--pdf-dir", type=Path, default=paths.WORKBOOK / "pdf")
    ap.add_argument("--build-dir", type=Path, default=paths.WORKBOOK / "build")
    ap.add_argument("--layout", choices=("a4", "video-16x9"),
                    help="복습노트 출력은 기본 16:9, 그 외 출력은 기본 A4 가로")
    args = ap.parse_args(argv[1:])
    if bool(args.public_pack) != bool(args.candidate_pack):
        ap.error('--public-pack and --candidate-pack must be paired')
    if args.layout is None:
        import unicodedata
        args.layout = "video-16x9" if "복습노트" in [unicodedata.normalize('NFC', p)
            for p in args.pdf_dir.resolve().parts] else "a4"
    if sum([bool(args.target), bool(args.ids), args.all]) != 1:
        ap.error("대상은 target, --ids, --all 중 하나만 준다")
    if args.ids and not args.name:
        ap.error("--ids 에는 --name 이 필요하다")
    if args.answer_overlay and (not args.ids or args.mode == "problems"):
        ap.error("--answer-overlay 는 --ids 및 --mode answers/both 에서만 쓸 수 있다")
    if args.selection and not args.ids:
        ap.error('--selection은 --ids와 함께 써요')
    return args


def selections(args):
    if args.all:
        return all_selections()
    if args.ids:
        return [ids_selection(args.ids.split(","), args.name)]
    return [resolve_target(args.target)]


def root_spelling(overlay_path):
    """paths.ROOT spelled the way the overlay path spells it.

    macOS keeps folder names as NFD on disk, so paths.ROOT (from __file__) can be
    NFD while a caller passes NFC paths. The overlay gate compares path strings,
    so the same folder spelled two ways reads as "outside the repo".
    Only the spelling changes; a path that is really outside keeps paths.ROOT.
    """
    root = Path(paths.ROOT)
    given = Path(overlay_path).absolute()
    head = given.parts[:len(root.parts)]
    if len(given.parts) > len(root.parts) and [nfc(p) for p in head] == [nfc(p) for p in root.parts]:
        return Path(*head)
    return root


def build_one(sel, args):
    """선택 하나를 문제지·답안지로 만든다. 넘친 쪽을 '<파일 이름>: <id>' 목록으로 돌려준다."""
    overflow = []
    overlay = None
    title_path = args.display_titles
    selection_path = args.selection
    view = None
    if args.public_pack:
        root = root_spelling(args.public_pack)
        view = PackPaths(root, args.public_pack, args.candidate_pack)
        if title_path:
            title_path = view.source_file(str(view.logical(title_path)))
        if selection_path:
            selection_path = view.source_file(str(view.logical(selection_path)))
    if args.answer_overlay:
        root = view.repo if view else root_spelling(args.answer_overlay)
        overlay = load_answer_overlay(args.answer_overlay, root,
                                      [nfc(pid.strip()) for pid in args.ids.split(",")], pack_paths=view)
        title_path = reviewed_title_path(overlay, root, title_path, pack_paths=view)
        selection_path = reviewed_selection_path(overlay, root, selection_path, pack_paths=view)
    for mode, suffix in MODE_SUFFIX.items():
        if args.mode != "both" and args.mode != mode:
            continue
        data = build_data(sel, mode)
        if selection_path:
            data = apply_selection(data, load_selection(selection_path, [p['id'] for p in data['problems']]))
        if title_path:
            titles = load_display_titles(title_path, [p['id'] for p in data['problems']])
            data = apply_display_titles(data, titles)
        if mode == 'answers' and overlay is not None:
            data = apply_answer_overlay(data, overlay, html_dir=args.build_dir)
        data['meta']['layout'] = args.layout
        stem = f"{sel.name}-{suffix}"
        args.build_dir.mkdir(parents=True, exist_ok=True)
        if args.layout == 'video-16x9' and not args.json_only:
            baseline = args.build_dir / f"{stem}-typography.html"
            baseline.write_text(inject(load_template(mode), data), encoding="utf-8")
            data['meta']['typography'] = measure_typography(baseline)
        (args.build_dir / f"{stem}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        html_path = args.build_dir / f"{stem}.html"
        html_path.write_text(inject(load_template(mode, args.layout), data), encoding="utf-8")
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
        except (RenderError, AnswerOverlayError, DisplayTitlesError, ValueError, OSError) as e:
            print(f"ERROR {sel.name}: {e}", file=sys.stderr)
            code = 1
    for item in overflow:
        print(f"OVERFLOW {item}", file=sys.stderr)
    return 1 if overflow else code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
