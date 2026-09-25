"""대상(교과서 장, 기출 회차, id 목록) → 문제 md 목록 → 문제집 JSON ({"meta", "problems"}).

JSON 모양은 workbook/templates/*.html 의 #workbook-data 계약(샘플: templates/sample-*.json)을 따른다.
"""
import re
import unicodedata
from dataclasses import dataclass

from paths import EXAMS, TEXTBOOK
from problem import ProblemError, exam_info, figures, hints, html_fields, load_problem, solution

TEXTBOOK_ID_RE = re.compile(r"^([EXP])(\d+)\.(\d{2})$")
EXAM_ID_RE = re.compile(r"^(\d{4}-[12]_(?:중간|기말))-Q([1-9]\d*)$")
EXAM_DIR_RE = re.compile(r"^\d{4}-[12]_(?:중간|기말)$")
EXAM_FILE_RE = re.compile(r"^Q([1-9]\d*)\.md$")
CHAPTER_RE = re.compile(r"^ch(\d{2})$")
KIND_DIR = {"E": "예제", "X": "연습문제", "P": "장말문제"}
MODE_SUFFIX = {"problems": "문제", "answers": "답안"}


class BuildError(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass
class Selection:
    name: str        # 파일 이름 앞부분 (ch09, 2023-1_기말, --name 값)
    title: str       # 문제지 meta.title (답안지는 뒤에 " 답안")
    chapter: int     # 장 번호, 장이 아니면 0
    paths: list


def nfc(s):
    return unicodedata.normalize("NFC", s)


def _book_order(path):
    """예제·연습문제를 번호순으로 섞고(E9.01, X9.01, E9.02 …) 장말문제를 뒤에 둔다."""
    m = TEXTBOOK_ID_RE.match(path.stem)
    kind, number = m.group(1), int(m.group(3))
    return (1, number, 0) if kind == "P" else (0, number, 0 if kind == "E" else 1)


def chapter_selection(ch):
    ch_dir = TEXTBOOK / f"ch{ch:02d}"
    if not ch_dir.is_dir():
        raise KeyError(f"장 폴더 없음: {ch_dir}")
    md_paths = sorted((p for kind in KIND_DIR.values() for p in (ch_dir / kind).glob("*.md")), key=_book_order)
    first = (ch_dir / "README.md").read_text(encoding="utf-8").splitlines()[0]
    title = first.removeprefix("# ").removesuffix(" — 문제 인덱스")
    return Selection(f"ch{ch:02d}", title, ch, md_paths)


def exam_selection(dir_name):
    name = nfc(dir_name)
    exam_dir = EXAMS / name
    if not EXAM_DIR_RE.match(name) or not exam_dir.is_dir():
        raise KeyError(f"기출 폴더 없음: {exam_dir}")
    numbered = [(int(m.group(1)), p) for p in exam_dir.glob("*.md") if (m := EXAM_FILE_RE.match(nfc(p.name)))]
    return Selection(name, exam_info(exam_dir)["exam"], 0, [p for _, p in sorted(numbered)])


def ids_selection(ids, name):
    md_paths, errors = [], []
    for raw in ids:
        pid = nfc(raw.strip())
        if m := TEXTBOOK_ID_RE.match(pid):
            path = TEXTBOOK / f"ch{int(m.group(2)):02d}" / KIND_DIR[m.group(1)] / f"{pid}.md"
        elif m := EXAM_ID_RE.match(pid):
            path = EXAMS / m.group(1) / f"Q{m.group(2)}.md"
        else:
            errors.append(f"id 형식 오류: {pid!r} (예: P9.05, 2023-1_기말-Q1)")
            continue
        if path.exists():
            md_paths.append(path)
        else:
            errors.append(f"문제 파일 없음: {path}")
    if errors:
        raise BuildError(errors)
    return Selection(name, name, 0, md_paths)


def resolve_target(target):
    target = nfc(target)
    if m := CHAPTER_RE.match(target):
        return chapter_selection(int(m.group(1)))
    return exam_selection(target)


def all_selections():
    chapters = sorted(int(m.group(1)) for d in TEXTBOOK.iterdir() if d.is_dir() and (m := CHAPTER_RE.match(d.name)))
    exams = sorted(nfc(d.name) for d in EXAMS.iterdir() if d.is_dir() and EXAM_DIR_RE.match(nfc(d.name)))
    return [chapter_selection(c) for c in chapters] + [exam_selection(e) for e in exams]


def entry(p, in_file, mode):
    m = p.meta
    chapter_end = m["kind"] == "장말문제"
    e = {
        "id": p.id,
        "kind": m["kind"],
        "number": str(m["number"]),
        "title": p.title,
        "section": f'{exam_info(p.path.parent)["exam"]} · {m["points"]}점' if p.is_exam else m["section"],
        "book_page": None if p.is_exam else m["book_page"],
        "difficulty": m.get("difficulty") if chapter_end else None,
        "sol": m.get("sol") if chapter_end else None,
        "original_lang": m.get("source_lang", "en"),
        "depends_on": [{"id": str(d), "in_file": str(d) in in_file} for d in m.get("depends_on") or []],
        "html": html_fields(p),
        "figures": figures(p),
        "hints": hints(p),
    }
    if mode == "answers":
        e["html"].pop("original", None)
        sol = solution(p)
        if sol is not None:
            e["solution"] = sol
    return e


def build_data(sel, mode):
    if mode not in MODE_SUFFIX:
        raise ValueError(f"mode 는 {list(MODE_SUFFIX)} 중 하나: {mode!r}")
    problems, errors = [], []
    for path in sel.paths:
        try:
            problems.append(load_problem(path))
        except ProblemError as e:
            errors.append(f"{path}: {e}")
    in_file = {p.id for p in problems}
    entries = []
    for p in problems:
        try:
            entries.append(entry(p, in_file, mode))
        except ProblemError as e:
            errors.append(f"{p.path}: {e}")
        except KeyError as e:
            errors.append(f"{p.path}: frontmatter 키 누락: {e.args[0]}")
    if errors:
        raise BuildError(errors)
    title = sel.title + (" 답안" if mode == "answers" else "")
    return {"meta": {"mode": mode, "title": title, "chapter": sel.chapter, "total": len(entries)},
            "problems": entries}
