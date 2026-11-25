#!/usr/bin/env python3
"""문제 md의 frontmatter로 장 폴더의 README.md(문제 인덱스)를 만든다.

사용법: python3 make_index.py <장 폴더> [장 제목]
    예) python3 make_index.py ../ch09 "9장 캐스코드 단과 전류 거울"
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from check_md import KIND_BY_PREFIX, md_files, split_frontmatter
from crop_figures import figure_filename

TITLE_RE = re.compile(r"^# .*? — (.+)$", re.M)


def load_docs(ch_dir):
    kind_order = list(KIND_BY_PREFIX.values())
    docs = {}
    for path in sorted(md_files(ch_dir), key=lambda p: (kind_order.index(p.parent.name), p.name)):
        text = path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        m = TITLE_RE.search(body)
        docs[fm["id"]] = {"kind": fm["kind"], "fm": fm, "title": m.group(1).strip() if m else ""}
    return docs


def figure_tag(fig):
    panels = fig.get("panels") or []
    return fig["id"] + (f"({','.join(panels)})" if panels else "")


def build_index(ch_dir, title=None):
    ch_dir = Path(ch_dir)
    docs = load_docs(ch_dir)
    spec = yaml.safe_load((ch_dir / "figures" / "figures.yaml").read_text(encoding="utf-8"))
    chapter = re.sub(r"\D", "", ch_dir.resolve().name).lstrip("0")
    title = title or f"{chapter}장"

    used_by = defaultdict(list)
    fig_use = defaultdict(list)
    for i, d in docs.items():
        for dep in d["fm"].get("depends_on") or []:
            used_by[dep].append(i)
        for fig in d["fm"].get("figures") or []:
            panels = fig.get("panels") or []
            fig_use[fig["id"]].append((i + (f"({','.join(panels)})" if panels else ""), fig["role"]))

    def link(i):
        return f"[{i}]({docs[i]['kind']}/{i}.md)" if i in docs else i

    def links(ids):
        return ", ".join(link(i) for i in ids) or "—"

    def esc(s):
        return str(s).replace("|", "\\|")

    kinds = list(KIND_BY_PREFIX.values())
    lines = [
        f"# {title} — 문제 인덱스",
        "",
        f"{chapter}장 문제를 md로 옮긴 파일의 목록이다. 형식은 [FORMAT.md](../FORMAT.md)를 따른다.",
        f"이 표는 각 파일의 frontmatter에서 `_tools/make_index.py`로 만들었다. 원본은 `{Path(spec['pdf']).name}`이고, "
        "쪽 번호는 교재 쪽, PDF는 PDF 페이지(1부터)다.",
        "",
        "| 종류 | 개수 |",
        "|---|---|",
    ]
    for kind in kinds:
        lines.append(f"| {kind} | {sum(d['kind'] == kind for d in docs.values())} |")
    lines += [f"| 합계 | {len(docs)} |", "",
              "표기: 그림 열의 `답`은 풀이 그림(`role: answer`)이다. 난이도는 원문의 * 개수이고, SOL은 풀이가 제공되는 문제다.",
              ""]

    for kind in kinds:
        is_problem = kind == KIND_BY_PREFIX["P"]
        cols = ["id", "제목", "절", "쪽", "PDF"] + (["난이도", "SOL"] if is_problem else []) + ["그림", "전제", "이어받는 문제"]
        lines += [f"## {kind}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for i, d in docs.items():
            if d["kind"] != kind:
                continue
            fm = d["fm"]
            figs = ", ".join(figure_tag(f) + ("" if f["role"] == "problem" else " 답")
                             for f in fm.get("figures") or []) or "—"
            row = [link(i), esc(d["title"]), esc(fm["section"]), fm["book_page"], fm["pdf_page"]]
            if is_problem:
                row += ["*" * fm["difficulty"] or "—", "SOL" if fm["sol"] else "—"]
            row += [figs, links(fm.get("depends_on") or []), links(sorted(used_by[i]))]
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines.append("")

    lines += ["## 그림별 사용처", "",
              "| 그림 | 문제 그림으로 쓰는 문제 | 풀이 그림으로 쓰는 문제 |",
              "|---|---|---|"]
    for fid in sorted(fig_use, key=lambda s: tuple(int(x) for x in s.split("."))):
        prob = ", ".join(t for t, r in fig_use[fid] if r == "problem") or "—"
        ans = ", ".join(t for t, r in fig_use[fid] if r == "answer") or "—"
        lines.append(f"| [Fig {fid}](figures/{figure_filename(fid)}) | {prob} | {ans} |")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    if len(argv) not in (2, 3):
        print("사용법: python3 make_index.py <장 폴더> [장 제목]", file=sys.stderr)
        return 2
    ch_dir = Path(argv[1])
    if not ch_dir.is_dir():
        print(f"장 폴더가 없음: {ch_dir}", file=sys.stderr)
        return 2
    out = ch_dir / "README.md"
    out.write_text(build_index(ch_dir, argv[2] if len(argv) == 3 else None), encoding="utf-8", newline="\n")
    print(f"{out} 작성")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
