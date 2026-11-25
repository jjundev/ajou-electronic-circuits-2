#!/usr/bin/env python3
"""기출 문제 md 형식 검사기. 규칙은 ../FORMAT-EXAM.md (본문 절은 교과서 FORMAT.md).

사용법: python3 check_exam.py <시험 폴더>    예) python3 check_exam.py ../2021-1_중간
오류가 하나라도 있으면 종료 코드 1.
"""
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf as fitz
import yaml

TEXTBOOK_TOOLS = Path(__file__).resolve().parents[3] / "교과서" / "마이크로전자회로" / "_tools"
sys.path.insert(0, str(TEXTBOOK_TOOLS))
from check_md import check_body, split_frontmatter  # noqa: E402,F401  (split_frontmatter 재노출)
from crop_exam import FIG_ID_RE, figure_filename  # noqa: E402

KIND = "기출"
REQUIRED_KEYS = ["id", "kind", "exam", "number", "points", "source", "pdf_page", "source_lang",
                 "figures", "textbook_chapters", "depends_on", "refs"]
EXAM_DIR_RE = re.compile(r"^(\d{4})-([12])_(중간|기말)(?:_([0-9A-Za-z가-힣]+))?$")   # 끝 _<분반>은 같은 학기 시험이 둘일 때만
ID_RE = re.compile(r"^(\d{4}-[12]_(?:중간|기말)(?:_[0-9A-Za-z가-힣]+)?)-Q([1-9]\d*)$")
FILE_RE = re.compile(r"^Q([1-9]\d*)\.md$")
SOURCE_LANGS = {"ko", "en"}
ANSWER_RE = re.compile(r"^## 답", re.M)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def nfc(s):
    """macOS 경로의 한글은 NFD(자모 분리)로 올 수 있어 NFC로 맞춘다."""
    return unicodedata.normalize("NFC", s)


def exam_title(dir_name):
    dir_name = nfc(dir_name)
    m = EXAM_DIR_RE.match(dir_name)
    if not m:
        raise ValueError(f"시험 폴더 이름 형식 오류: {dir_name!r} (예: 2021-1_중간, 2017-1_중간_D반)")
    title = f"{m.group(1)}-{m.group(2)} {m.group(3)}고사"
    return f"{title} ({m.group(4)})" if m.group(4) else title


def md_files(exam_dir):
    return sorted((p for p in exam_dir.glob("Q*.md") if FILE_RE.match(p.name)),
                  key=lambda p: int(FILE_RE.match(p.name).group(1)))


def stray_md(exam_dir):
    """Q<번호>.md와 README.md가 아닌 md 파일 이름 (md_files가 건너뛰는 파일)."""
    return sorted(p.name for p in exam_dir.glob("*.md") if p.name != "README.md" and not FILE_RE.match(p.name))


def check_source(path, meta):
    source, pdf_page = meta["source"], meta["pdf_page"]
    if not isinstance(source, str) or not source.endswith(".pdf"):
        return [f"source {source!r} 는 md 기준 상대 경로의 .pdf"]
    pdf = (path.parent / source).resolve()
    if not pdf.is_file():
        return [f"source PDF 없음: {source}"]
    if not is_int(pdf_page):
        return [f"pdf_page {pdf_page!r} 는 정수"]
    with fitz.open(pdf) as doc:
        if not 1 <= pdf_page <= len(doc):
            return [f"pdf_page {pdf_page} 가 {Path(source).name} 의 1..{len(doc)} 범위 밖"]
    return []


def check_figures_meta(figures, exam_dir):
    figures = figures or []
    if not isinstance(figures, list):
        return [f"figures 는 목록이어야 함: {figures!r}"]
    errors = []
    for fig in figures:
        if not isinstance(fig, dict):
            errors.append(f"figures 항목은 {{id: ..., role: ...}} 형태여야 함: {fig!r}")
            continue
        fig_id = fig.get("id")
        if not isinstance(fig_id, str) or not FIG_ID_RE.match(fig_id):
            errors.append(f'그림 id {fig_id!r} 형식 오류 (따옴표로 감싼 "Q2" 또는 "Q2-2")')
            continue
        if fig.get("role") != "problem":
            errors.append(f"그림 {fig_id} role 은 problem (기출은 답 그림을 싣지 않음)")
        if not (exam_dir / "figures" / figure_filename(fig_id)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id)}")
    return errors


def check_file(path, exam_dir):
    errors, warnings = [], []
    try:
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError) as e:
        return [str(e)], warnings

    missing = [k for k in REQUIRED_KEYS if k not in meta]
    if missing:
        return [f"frontmatter 키 누락: {', '.join(missing)}"], warnings

    m = ID_RE.match(str(meta["id"]))
    if not m:
        return [f"id 형식 오류: {meta['id']!r} (예: 2021-1_중간-Q2)"], warnings
    exam, n = m.group(1), m.group(2)
    if exam != nfc(exam_dir.name):
        errors.append(f"id {meta['id']} 의 시험 {exam} 이 폴더 {nfc(exam_dir.name)} 와 다름")
    if path.name != f"Q{n}.md":
        errors.append(f"파일명 {path.name} 이 id {meta['id']} 와 다름 (기대: Q{n}.md)")
    if not isinstance(meta["number"], str):
        errors.append(f'number {meta["number"]!r} 는 따옴표로 감싼 문자열이어야 함 (예: "{n}")')
    elif meta["number"] != n:
        errors.append(f"number {meta['number']!r} 가 id {meta['id']} 와 안 맞음 (기대: \"{n}\")")
    if meta["kind"] != KIND:
        errors.append(f"kind {meta['kind']!r} 는 {KIND} 이어야 함")
    try:
        title = exam_title(exam_dir.name)
        if meta["exam"] != title:
            errors.append(f"exam {meta['exam']!r} 가 폴더와 안 맞음 (기대: \"{title}\")")
    except ValueError as e:
        errors.append(str(e))
    if not is_int(meta["points"]) or meta["points"] <= 0:
        errors.append(f"points {meta['points']!r} 는 양의 정수 (원문 배점)")
    if meta["source_lang"] not in SOURCE_LANGS:
        errors.append(f"source_lang {meta['source_lang']!r} 는 ko 또는 en")
    errors += check_source(path, meta)
    chapters = meta["textbook_chapters"]
    if not isinstance(chapters, list) or not all(is_int(c) for c in chapters):
        errors.append(f"textbook_chapters {chapters!r} 는 정수 목록 (예: [9, 10])")
    errors += check_figures_meta(meta["figures"], exam_dir)

    for dep in meta["depends_on"] or []:
        dm = ID_RE.match(str(dep))
        if not dm:
            errors.append(f"depends_on id 형식 오류: {dep!r}")
        elif dm.group(1) != nfc(exam_dir.name):
            errors.append(f"depends_on {dep} 는 다른 시험 (같은 시험 id만 적고, 다른 시험은 refs에 적음)")
        elif not (exam_dir / f"Q{dm.group(2)}.md").exists():
            warnings.append(f"depends_on {dep} 파일이 아직 없음")

    errors += check_body(body, path, KIND)
    if ANSWER_RE.search(body):
        errors.append("기출에는 답 절을 두지 않음 (풀이와 답은 ## 풀이에 씀, FORMAT-EXAM.md)")
    return errors, warnings


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 check_exam.py <시험 폴더>", file=sys.stderr)
        return 2
    exam_dir = Path(argv[1]).resolve()   # "check_exam.py ." 로 불러도 폴더 이름이 나오게
    if not exam_dir.is_dir():
        print(f"시험 폴더가 없음: {exam_dir}", file=sys.stderr)
        return 2
    try:
        exam_title(exam_dir.name)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    files = md_files(exam_dir)
    n_err = 0
    for path in files:
        try:
            errors, warnings = check_file(path, exam_dir)
        except Exception as e:  # 파일 하나가 깨져도 나머지는 계속 검사
            errors, warnings = [f"검사 중 예외 {e!r}"], []
        for e in errors:
            print(f"ERROR {path}: {e}")
        for w in warnings:
            print(f"WARN  {path}: {w}")
        n_err += len(errors)
    for name in stray_md(exam_dir):
        print(f"WARN  {exam_dir / name}: 알 수 없는 md 파일: {name} (Q<번호>.md 형식이 아니라 검사하지 않음)")
    print(f"{len(files)}개 파일, 오류 {n_err}개")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
