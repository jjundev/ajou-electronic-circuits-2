#!/usr/bin/env python3
"""
workbook 문제 목록 (복습문제 선별용). 문제 md는 workbook/problem.py의 load_problem으로 읽는다.

한 줄에 문제 하나, 탭으로 구분:
  id  kind  secnum  section  difficulty  used  title
- secnum: 교과서는 section 앞 절 번호(예: 9.1.2. 번호가 없으면 section 그대로), 기출은 "ch" + textbook_chapters(예: ch9,10)
- difficulty: 교과서 frontmatter 값, 기출은 "-"
- used: 이전 팩 problems.txt에 있으면 "USED", 아니면 "-"
CLI: problem_index.py --repo REPO [--used REPO/복습노트] [--chapters 9,10]
읽을 수 없는 md는 stderr에 `ERROR <경로>: <이유>`로 적고 건너뛴다(종료 코드 1).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unicodedata

HEADER = "id\tkind\tsecnum\tsection\tdifficulty\tused\ttitle"
KIND_DIRS = ("예제", "연습문제", "장말문제")
SECNUM_RE = re.compile(r"\d+(?:\.\d+)*")
CHAPTER_DIR_RE = re.compile(r"ch(\d{2})")
EXAM_FILE_RE = re.compile(r"Q([1-9]\d*)\.md")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _workbook(repo: Path):
    """REPO/workbook/problem.py 모듈."""
    path = str(Path(repo) / "workbook")
    if path not in sys.path:
        sys.path.insert(0, path)
    import problem  # noqa: E402
    return problem


def secnum(meta: dict) -> str:
    if meta.get("kind") == "기출":
        return "ch" + ",".join(str(c) for c in meta.get("textbook_chapters") or [])
    section = str(meta.get("section", ""))
    m = SECNUM_RE.match(section)
    return m.group(0) if m else section


def used_ids(notes_dir: Path | str) -> set[str]:
    """<notes_dir>/*/problems.txt 의 id (줄 형식 `id | why`)."""
    notes_dir, ids = Path(notes_dir), set()
    if not notes_dir.is_dir():
        return ids
    for path in notes_dir.glob("*/problems.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            pid = nfc(line.split("|", 1)[0].strip())
            if pid:
                ids.add(pid)
    return ids


def _exam_number(path: Path) -> int:
    return int(EXAM_FILE_RE.fullmatch(nfc(path.name)).group(1))


def md_paths(repo: Path | str, chapters: set[int] | None = None) -> list[Path]:
    """교과서(장 순서, 종류 순서, 파일명 순서) 다음 기출(회차 순서, 문항 번호 순서) md 경로."""
    repo, out = Path(repo), []
    textbook = repo / "교과서" / "마이크로전자회로"
    for ch_dir in sorted(textbook.iterdir()) if textbook.is_dir() else []:
        m = CHAPTER_DIR_RE.fullmatch(nfc(ch_dir.name))
        if not m or not ch_dir.is_dir() or (chapters and int(m.group(1)) not in chapters):
            continue
        for kind in KIND_DIRS:
            out += sorted((ch_dir / kind).glob("*.md"))
    exams = repo / "from_the_past" / "md"
    for exam_dir in sorted(p for p in exams.iterdir() if p.is_dir()) if exams.is_dir() else []:
        out += sorted((p for p in exam_dir.glob("*.md") if EXAM_FILE_RE.fullmatch(nfc(p.name))), key=_exam_number)
    return out


def index(repo: Path | str, used_dir: Path | str | None = None,
          chapters: set[int] | None = None) -> tuple[list[list[str]], list[str]]:
    problem = _workbook(Path(repo))
    used = used_ids(used_dir) if used_dir else set()
    rows, errors = [], []
    for path in md_paths(repo, chapters):
        try:
            p = problem.load_problem(path)
        except (problem.ProblemError, OSError, KeyError) as e:
            errors.append(f"{path}: {e}")
            continue
        meta, pid = p.meta, nfc(p.id)
        exam = meta.get("kind") == "기출"
        if exam and chapters and not set(meta.get("textbook_chapters") or []) & chapters:
            continue
        rows.append([pid, str(meta["kind"]), secnum(meta), str(meta.get("section", "-")),
                     "-" if exam else str(meta.get("difficulty", "-")),
                     "USED" if pid in used else "-", p.title.replace("\t", " ")])
    return rows, errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--used", help="이전 팩 폴더들의 부모(보통 REPO/복습노트)")
    ap.add_argument("--chapters", help="쉼표로 구분한 장 번호 (예: 9,10)")
    args = ap.parse_args(argv)
    chapters = {int(c) for c in args.chapters.split(",")} if args.chapters else None
    rows, errors = index(Path(args.repo), args.used, chapters)
    print(HEADER)
    for row in rows:
        print("\t".join(row))
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
