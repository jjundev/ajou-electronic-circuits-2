#!/usr/bin/env python3
"""
manifest + 섹션 조각 → 정리노트 HTML (표준 라이브러리만 사용).

실행 폴더 구조:
  RUN/manifest.json
  RUN/sections/<section-id>.html   (섹션 안쪽: <article class="topic"> 들, <script> 가능)
조각 안의 {{NOTE_HREF}} / {{PROBLEM_PDF}} / {{ANSWER_PDF}} 는 실제 파일명으로 바뀐다.
<script> 블록은 조각에서 빼서 </body> 앞({{SCRIPTS}})으로 모은다.
문제가 있으면 같은 폴더에 problems.txt(`id | why` 한 줄씩)를 쓰고, 없으면 예전 problems.txt를 지운다.
CLI: assemble.py --run RUN --out 복습노트/<range>
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifest as manifest_mod  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SLOT_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)


class AssembleError(RuntimeError):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def fill(template: str, values: dict[str, str]) -> str:
    missing = sorted(set(SLOT_RE.findall(template)) - values.keys())
    if missing:
        raise AssembleError(f"템플릿 슬롯 값 없음: {missing}")
    return SLOT_RE.sub(lambda mo: values[mo.group(1)], template)


def split_scripts(fragment: str) -> tuple[str, list[str]]:
    scripts = SCRIPT_RE.findall(fragment)
    return SCRIPT_RE.sub("", fragment), scripts


def read_fragment(path: Path, m: dict) -> str:
    if not path.exists():
        raise AssembleError(f"조각 파일 없음: {path}")
    text = path.read_text(encoding="utf-8")
    for token, value in (("{{NOTE_HREF}}", manifest_mod.note_name(m)),
                         ("{{PROBLEM_PDF}}", manifest_mod.problem_pdf_name(m)),
                         ("{{ANSWER_PDF}}", manifest_mod.answer_pdf_name(m))):
        text = text.replace(token, value)
    return text


def build_note(m: dict, run_dir: Path) -> str:
    sections, scripts = [], []
    for sec in m["sections"]:
        body, found = split_scripts(read_fragment(run_dir / "sections" / f"{sec['id']}.html", m))
        scripts += found
        sections.append(f'    <section id="{sec["id"]}"><h2>{esc(sec["title"])}</h2>\n{body.strip()}\n    </section>')
    return fill((ASSETS / "note-template.html").read_text(encoding="utf-8"), {
        "PAGE_TITLE": esc(f"전자회로2 정리노트 {m['range']}"),
        "DESCRIPTION": esc(m["note_subtitle"]),
        "TOC": "".join(f'<a href="#{s["id"]}">{esc(s["short"])}</a>' for s in m["sections"]),
        "TITLE": esc(m["note_title"]),
        "SUBTITLE": esc(m["note_subtitle"]),
        "SECTIONS": "\n".join(sections),
        "FOOTER": m["footer_note"],
        "SCRIPTS": "\n".join(f"  {s}" for s in scripts),
        "RANGE": m["range"],
    })


def problems_txt(m: dict) -> str:
    return "".join(f"{q['id']} | {q['why']}\n" for q in m["problems"])


def assemble(run_dir: Path | str, out_dir: Path | str) -> Path:
    run_dir, out_dir = Path(run_dir), Path(out_dir)
    m = manifest_mod.load(run_dir / "manifest.json")
    note_html = build_note(m, run_dir)  # 조각이 하나라도 없으면 아무것도 쓰지 않는다
    out_dir.mkdir(parents=True, exist_ok=True)
    note_path = out_dir / manifest_mod.note_name(m)
    note_path.write_text(note_html, encoding="utf-8")
    listing = out_dir / manifest_mod.PROBLEMS_TXT
    if m["problems"]:
        listing.write_text(problems_txt(m), encoding="utf-8")
    elif listing.exists():
        listing.unlink()
    return note_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        print(assemble(args.run, args.out))
    except (AssembleError, manifest_mod.ManifestError) as e:
        print(f"assemble 실패: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
