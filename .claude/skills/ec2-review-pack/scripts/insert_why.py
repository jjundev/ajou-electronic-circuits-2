#!/usr/bin/env python3
"""
이미 만든 정리노트에 "왜 이런 회로를 쓸까" 섹션을 끼워넣는다 (표준 라이브러리만 사용).

조각은 assemble.py의 섹션 조각과 같은 형식이다: <article class="topic" id="why-circuit"> 하나,
레이어 eli5·formal과 <div class="sum" hidden> 포함, <section>·<h2>·<script> 없음.
why 섹션은 첫 <section> 앞에, 목차 링크는 목차 맨 앞에 들어간다. 이미 있으면 교체한다(다시 실행해도 결과가 같다).
CLI: insert_why.py --note 복습노트/<range>/정리노트_….html --fragment why.html [--title T] [--short S]
      (노트를 그 자리에서 고친다. 실패하면 파일은 그대로 두고 종료 코드 1)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble import esc  # noqa: E402
from check_html import MD_LINK_RE  # noqa: E402
from manifest import WHY_REQUIRED_LAYERS, WHY_SECTION_ID, WHY_SHORT, WHY_TITLE, WHY_TOPIC_ID  # noqa: E402

TOC_OPEN = '<nav class="toc" aria-label="목차">'
SECTION_OPEN = '<section id="'
OLD_SECTION_RE = re.compile(rf'<section id="{WHY_SECTION_ID}">.*?</section>\s*', re.S)
OLD_TOC_LINK = re.compile(rf'<a href="#{WHY_SECTION_ID}">[^<]*</a>')


class InsertError(RuntimeError):
    pass


def fragment_errors(fragment: str) -> list[str]:
    errors = [f"조각에 {tag}를 쓸 수 없음" for tag in ("<section", "</section", "<h2", "<script") if tag in fragment.lower()]
    errors += [f"조각에 마크다운 링크가 있음(<a href>로): {s}" for s in MD_LINK_RE.findall(fragment)]
    needed = [f'<article class="topic" id="{WHY_TOPIC_ID}">',
              *(f'class="layer {layer}"' for layer in WHY_REQUIRED_LAYERS), '<div class="sum" hidden>']
    errors += [f"조각에 {s} 없음" for s in needed if s not in fragment]
    return errors


def insert_why(note_html: str, fragment: str, title: str = WHY_TITLE, short: str = WHY_SHORT) -> str:
    if errors := fragment_errors(fragment):
        raise InsertError("; ".join(errors))
    note = OLD_SECTION_RE.sub("", note_html, count=1)
    toc = note.find(TOC_OPEN)
    if toc < 0:
        raise InsertError(f"노트에 목차({TOC_OPEN})가 없음")
    toc += len(TOC_OPEN)
    toc_end = note.find("</nav>", toc)
    if toc_end < 0:
        raise InsertError("노트의 목차가 </nav>로 닫히지 않음")
    # 목차 안의 why 링크만 지운다(본문의 #why 링크는 그대로 둔다).
    note = note[:toc] + OLD_TOC_LINK.sub("", note[toc:toc_end], count=1) + note[toc_end:]
    at = note.find(SECTION_OPEN)
    if at < 0:
        raise InsertError(f"노트에 {SECTION_OPEN}… 섹션이 없음")
    # 원래 들여쓰기는 첫 섹션 앞에 남아 있으므로 why 뒤에 같은 들여쓰기를 붙인다.
    section = f'<section id="{WHY_SECTION_ID}"><h2>{esc(title)}</h2>\n{fragment.strip()}\n    </section>\n    '
    note = note[:at] + section + note[at:]
    toc = note.find(TOC_OPEN) + len(TOC_OPEN)  # 섹션이 목차 앞에 들어갔을 때를 위해 다시 찾는다
    return note[:toc] + f'<a href="#{WHY_SECTION_ID}">{esc(short)}</a>' + note[toc:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--note", required=True)
    ap.add_argument("--fragment", required=True)
    ap.add_argument("--title", default=WHY_TITLE)
    ap.add_argument("--short", default=WHY_SHORT)
    args = ap.parse_args(argv)
    note = Path(args.note)
    try:
        try:
            note_html = note.read_text(encoding="utf-8")
            fragment = Path(args.fragment).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise InsertError(f"파일을 읽을 수 없음: {e}") from e
        out = insert_why(note_html, fragment, args.title, args.short)  # 다 만든 뒤에만 쓴다
    except InsertError as e:
        print(f"insert_why 실패: {e}", file=sys.stderr)
        return 1
    # 쓰다가 멈춰도 노트가 잘리지 않게 같은 폴더의 임시 파일에 쓴 뒤 바꿔 끼운다.
    fd, tmp = tempfile.mkstemp(dir=note.parent, prefix=".insert_why-", suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, note)
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
