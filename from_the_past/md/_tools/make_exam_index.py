#!/usr/bin/env python3
"""시험 폴더의 문제 md frontmatter와 exam.yaml로 README.md(문제 인덱스)를 만든다.

사용법: python3 make_exam_index.py <시험 폴더>    예) python3 make_exam_index.py ../2021-1_중간
"""
import re
import sys
from pathlib import Path

import yaml

from check_exam import TEXTBOOK_TOOLS, md_files, split_frontmatter

TITLE_RE = re.compile(r"^# .*? — (.+)$", re.M)
TEXTBOOK_DIR = TEXTBOOK_TOOLS.parent
TEXTBOOK_LINK = "../../../교과서/마이크로전자회로"   # from_the_past/md/<시험>/ 기준


def esc(s):
    return str(s).replace("|", "\\|")


def figure_tag(fig):
    panels = fig.get("panels") or []
    return fig["id"] + (f"({','.join(panels)})" if panels else "")


def chapter_link(n):
    name = f"ch{n:02d}"
    if (TEXTBOOK_DIR / name / "README.md").exists():
        return f"[{n}장]({TEXTBOOK_LINK}/{name}/README.md)"
    return f"{n}장"


def build_exam_index(exam_dir):
    exam_dir = Path(exam_dir)
    meta = yaml.safe_load((exam_dir / "exam.yaml").read_text(encoding="utf-8")) or {}
    rows, total = [], 0
    for path in md_files(exam_dir):
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        m = TITLE_RE.search(body)
        q = path.stem
        total += fm["points"]
        figs = ", ".join(figure_tag(f) for f in fm.get("figures") or []) or "—"
        chapters = ", ".join(chapter_link(n) for n in fm.get("textbook_chapters") or []) or "—"
        deps = ", ".join(f"[{d.rsplit('-', 1)[1]}]({d.rsplit('-', 1)[1]}.md)"
                         for d in fm.get("depends_on") or []) or "—"
        row = [f"[{q}]({q}.md)", esc(m.group(1).strip() if m else ""), fm["points"],
               Path(fm["source"]).name, fm["pdf_page"], figs, chapters, deps]
        rows.append("| " + " | ".join(str(c) for c in row) + " |")

    exam = meta["exam"]
    lines = [
        f"# {exam} — 문제 인덱스",
        "",
        f"{exam} 문제를 md로 옮긴 파일의 목록이다. 형식은 [FORMAT-EXAM.md](../FORMAT-EXAM.md)를 따른다.",
        "이 표는 각 파일의 frontmatter와 `exam.yaml`에서 `_tools/make_exam_index.py`로 만들었다. "
        "PDF 열은 원본 PDF의 페이지(1부터)다.",
        "",
        f"- 시험지 머리: {meta['header']}",
        "- 원본: " + ", ".join(f"`{Path(s).name}`" for s in meta["sources"]),
    ]
    if meta.get("aux_sources"):
        lines.append("- 보조 원본: " + ", ".join(f"`{Path(s).name}`" for s in meta["aux_sources"]))
    lines.append(f"- 문제 {len(rows)}개, 배점 합계 {total}점")
    lines += [f"- {n}" for n in meta.get("notes") or []]
    lines += ["", "| 문제 | 제목 | 배점 | 원본 | PDF | 그림 | 교과서 | 전제 |",
              "|---|---|---|---|---|---|---|---|"]
    lines += rows
    lines.append("")
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 make_exam_index.py <시험 폴더>", file=sys.stderr)
        return 2
    exam_dir = Path(argv[1])
    if not (exam_dir / "exam.yaml").is_file():
        print(f"exam.yaml 없음: {exam_dir}", file=sys.stderr)
        return 2
    out = exam_dir / "README.md"
    out.write_text(build_exam_index(exam_dir), encoding="utf-8")
    print(f"{out} 작성")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
