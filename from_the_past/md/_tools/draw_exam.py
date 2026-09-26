#!/usr/bin/env python3
"""시험 폴더의 figures/redrawn/fig-Q<n>.py를 실행해 다시 그린 회로도 PNG를 만든다.

그림 코드는 `def draw() -> schemdraw.Drawing` 하나를 둔다. 규칙은 FORMAT-EXAM.md '다시 그린 그림'.

사용법: python3 draw_exam.py <시험 폴더> [--compare <out.png>]
"""
import importlib.util
import struct
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from schem_style import DPI, FONT_SIZE, save_png

REDRAWN = "redrawn"
FONT_PT_RANGE = (7.0, 11.0)   # 문제집에 찍힐 라벨 글자 크기(pt) 허용 범위
HEIGHT_TOLERANCE = 0.15       # 크롭 폭 기준 인쇄 높이가 크롭 높이와 벌어져도 되는 비율
SHEET_WIDTH = 1200            # 대조 시트 폭(px)
USAGE = "사용법: python3 draw_exam.py <시험 폴더> [--compare <out.png>]"


def png_size(path):
    return struct.unpack(">II", Path(path).read_bytes()[16:24])


def sources(exam_dir):
    return sorted((Path(exam_dir) / "figures" / REDRAWN).glob("fig-*.py"))


def load_draw(py):
    spec = importlib.util.spec_from_file_location("redrawn_" + py.stem.replace("-", "_"), py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    draw = getattr(mod, "draw", None)
    if not callable(draw):
        raise ValueError("draw() 없음")
    return draw


def printed_font_pt(crop_w_px, crop_dpi, redrawn_w_px, dpi=DPI):
    """문제집은 다시 그린 그림을 크롭과 같은 폭으로 찍는다. 그때의 라벨 글자 크기(pt)."""
    return FONT_SIZE * (crop_w_px / crop_dpi) / (redrawn_w_px / dpi)


def printed_height_mm(crop_w_px, crop_h_px, dpi, redrawn_w_px, redrawn_h_px):
    """문제집이 다시 그린 그림을 크롭 폭으로 찍을 때의 인쇄 높이(mm)와 크롭의 인쇄 높이(mm)."""
    crop_w_mm = crop_w_px / dpi * 25.4
    crop_h_mm = crop_h_px / dpi * 25.4
    printed_h_mm = crop_w_mm * redrawn_h_px / redrawn_w_px
    return printed_h_mm, crop_h_mm


def crop_dpi(exam_dir):
    spec = yaml.safe_load((Path(exam_dir) / "figures" / "figures.yaml").read_text(encoding="utf-8")) or {}
    return spec.get("dpi", 144)


def draw_all(exam_dir, out_dir=None):
    """(쓴 PNG 목록, 오류 줄, 경고 줄). out_dir를 주면 PNG를 거기에 쓴다(verify_exam --redraw용)."""
    exam_dir = Path(exam_dir)
    fig_dir = exam_dir / "figures"
    written, errors, warnings = [], [], []
    for py in sources(exam_dir):
        out = Path(out_dir or py.parent) / (py.stem + ".png")
        try:
            save_png(load_draw(py)(), out)
        except Exception as e:  # 그림 하나가 틀려도 나머지는 그린다
            errors.append(f"{py.name}: {e}")
            continue
        written.append(out)
        crop = fig_dir / (py.stem + ".png")
        if crop.exists():
            crop_w, crop_h = png_size(crop)
            dpi_ = crop_dpi(exam_dir)
            out_w, out_h = png_size(out)
            pt = printed_font_pt(crop_w, dpi_, out_w)
            lo, hi = FONT_PT_RANGE
            if not lo <= pt <= hi:
                warnings.append(f"{out.name}: 인쇄 글자 {pt:.1f}pt (허용 {lo:g}–{hi:g}pt). 그림 폭을 조정")
            printed_h_mm, crop_h_mm = printed_height_mm(crop_w, crop_h, dpi_, out_w, out_h)
            if abs(printed_h_mm - crop_h_mm) > HEIGHT_TOLERANCE * crop_h_mm:
                warnings.append(
                    f"{out.name}: 인쇄 높이 {printed_h_mm:.1f}mm (크롭 {crop_h_mm:.1f}mm, "
                    f"허용 ±15%). 배치를 조정")
    return written, errors, warnings


def compare_sheet(exam_dir, out):
    """크롭(위)과 다시 그린 그림(아래)을 같은 폭으로 쌓은 대조 시트."""
    fig_dir = Path(exam_dir) / "figures"
    tiles = []
    for png in sorted((fig_dir / REDRAWN).glob("fig-*.png")):
        for tag, path in (("crop", fig_dir / png.name), ("redrawn", png)):
            if not path.exists():
                continue
            img = Image.open(path).convert("RGB")
            img = img.resize((SHEET_WIDTH, round(img.height * SHEET_WIDTH / img.width)))
            label = Image.new("RGB", (SHEET_WIDTH, 28), "white")
            ImageDraw.Draw(label).text((6, 6), f"{png.stem} {tag}", fill="red")
            tiles += [label, img]
    if not tiles:
        raise ValueError("다시 그린 그림이 없음")
    sheet = Image.new("RGB", (SHEET_WIDTH, sum(t.height for t in tiles)), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(out)
    return Path(out)


def main(argv):
    args = argv[1:]
    compare = None
    if "--compare" in args:
        i = args.index("--compare")
        if i + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 2
        compare = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) != 1 or not Path(args[0]).is_dir():
        print(USAGE, file=sys.stderr)
        return 2
    exam_dir = Path(args[0])
    written, errors, warnings = draw_all(exam_dir)
    for path in written:
        print(path)
    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(f"ERROR {e}")
    if compare and not errors:
        try:
            print(compare_sheet(exam_dir, compare))
        except ValueError:
            print("ERROR 다시 그린 그림이 없음")
            return 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
