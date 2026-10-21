#!/usr/bin/env python3
"""
복습팩 manifest.json 로더·검증기 (표준 라이브러리만 사용).

manifest는 한 번의 실행(기간 하나)에 대한 계약이다. assemble.py와 check_html.py가 읽는다.
CLI: manifest.py RUN/manifest.json [REPO]   (검증만. REPO를 주면 문제 md가 있는지도 본다. 오류가 있으면 목록 출력 후 종료 코드 1)
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unicodedata

DEFAULT_REPO = Path(__file__).resolve().parents[4]
sys.path.append(str(DEFAULT_REPO / "workbook"))
from learning_style import STYLE_PATH, LearningStyleError, check_style  # noqa: E402

LAYER_NAMES = {"eli5", "formal", "prof", "warn"}
TOP_LEVEL_TYPES = {
    "course": str, "range": str, "slug": str,
    "note_title": str, "note_subtitle": str, "footer_note": str,
    "sessions": list, "sections": list, "preview_topic": str, "forbidden_outside_preview": list,
    "problems": list, "links": list, "learning_style": dict,
}
RANGE_RE = re.compile(r"\d{4}(-\d{4})?")
SLUG_RE = re.compile(r"[A-Za-z0-9_]+")
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
DATE_RE = re.compile(r"\d{4}")
# workbook/assemble.py의 TEXTBOOK_ID_RE·EXAM_ID_RE·KIND_DIR와 같은 규칙
TEXTBOOK_ID_RE = re.compile(r"([EXP])(\d+)\.(\d{2})")
EXAM_ID_RE = re.compile(r"(\d{4}-[12]_(?:중간|기말)(?:_[0-9A-Za-z가-힣]+)?)-Q([1-9]\d*)")
KIND_BY_PREFIX = {"E": "예제", "X": "연습문제", "P": "장말문제"}
MAX_PROBLEMS = 12
# 모든 정리노트의 첫 섹션: "왜 이런 회로를 쓸까" 페이지(토픽 1개). 기존 s0… id는 그대로 둔다.
WHY_SECTION_ID = "why"
WHY_TOPIC_ID = "why-circuit"
WHY_TITLE = "들어가며: 왜 이런 회로를 쓸까"
WHY_SHORT = "왜 쓸까"
WHY_TOPIC_TITLE = "왜 이런 회로를 쓸까"
WHY_REQUIRED_LAYERS = ("eli5", "formal")
PROBLEMS_TXT = "problems.txt"
# 팩 폴더 맨 위에는 .pack/·HTML·PDF만 두고, md·그림·problems.txt 등 나머지는 여기 모은다.
BUNDLE = ".assets"


class ManifestError(ValueError):
    pass


def _need(obj: dict, key: str, typ: type, where: str, errors: list[str]) -> bool:
    value = obj.get(key) if isinstance(obj, dict) else None
    # bool은 int의 하위 클래스라 int 자리에 true/false가 들어오지 않게 따로 막는다.
    if not isinstance(value, typ) or (typ is int and isinstance(value, bool)):
        errors.append(f"{where}.{key}: {typ.__name__} 필요")
        return False
    return True


def _strings(items: list, where: str, errors: list[str]) -> None:
    """검사기가 `term in text`로 쓰는 목록: 빈 문자열이 아닌 문자열만 허용한다(숫자는 "0.2"처럼 따옴표)."""
    for i, item in enumerate(items):
        if not isinstance(item, str) or not item:
            errors.append(f"{where}[{i}]: 빈 문자열이 아닌 문자열 필요: {item!r}")


def _objects(items: list, where: str, errors: list[str]):
    """dict 항목만 (i, 항목)으로 돌려준다. dict가 아닌 항목은 오류로 기록하고 건너뛴다."""
    for i, item in enumerate(items):
        if isinstance(item, dict):
            yield i, item
        else:
            errors.append(f"{where}[{i}]: 객체 필요")


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def problem_kind(pid: str) -> str | None:
    """workbook id의 종류(예제/연습문제/장말문제/기출). 형식이 틀리면 None."""
    pid = _nfc(pid)
    if m := TEXTBOOK_ID_RE.fullmatch(pid):
        return KIND_BY_PREFIX[m.group(1)]
    if EXAM_ID_RE.fullmatch(pid):
        return "기출"
    return None


def problem_md_path(repo: Path | str, pid: str) -> Path:
    """workbook id → 문제 md 경로 (workbook/assemble.py ids_selection과 같은 규칙)."""
    repo, pid = Path(repo), _nfc(pid)
    if m := TEXTBOOK_ID_RE.fullmatch(pid):
        return repo / "교과서" / "마이크로전자회로" / f"ch{int(m.group(2)):02d}" / KIND_BY_PREFIX[m.group(1)] / f"{pid}.md"
    if m := EXAM_ID_RE.fullmatch(pid):
        return repo / "from_the_past" / "md" / m.group(1) / f"Q{m.group(2)}.md"
    raise ValueError(f"workbook id 형식 오류: {pid}")


def _check_why(m: dict, errors: list[str]) -> None:
    """첫 섹션이 why 페이지인지 본다. 형식 오류는 validate가 이미 보고했으므로 여기서는 건너뛴다."""
    if m["preview_topic"] == WHY_TOPIC_ID:
        errors.append(f"preview_topic: {WHY_TOPIC_ID}은 예고 토픽이 될 수 없음")
    if not m["sections"] or not isinstance(m["sections"][0], dict):
        return
    sec = m["sections"][0]
    if sec.get("id") != WHY_SECTION_ID:
        errors.append(f"sections[0].id: 첫 섹션은 {WHY_SECTION_ID}여야 함")
        return
    topics = sec.get("topics")
    if not isinstance(topics, list):
        return
    if [t.get("id") if isinstance(t, dict) else None for t in topics] != [WHY_TOPIC_ID]:
        errors.append(f"sections[0].topics: {WHY_SECTION_ID} 섹션의 토픽은 {WHY_TOPIC_ID} 하나여야 함")
    layers = topics[0].get("layers") if topics and isinstance(topics[0], dict) else None
    if isinstance(layers, list) and not all(l in layers for l in WHY_REQUIRED_LAYERS):
        errors.append(f"sections[0].topics[0].layers: {WHY_TOPIC_ID}에는 eli5와 formal이 필요함")


def _check_snapshot(snapshot: dict, errors: list[str]) -> None:
    if set(snapshot) != {"path", "sha256", "rule_ids"}:
        errors.append("manifest.learning_style: path/sha256/rule_ids 필요")
    if snapshot.get("path") != STYLE_PATH:
        errors.append(f"manifest.learning_style.path: {STYLE_PATH} 필요")
    digest = snapshot.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("manifest.learning_style.sha256: SHA-256 필요")
    rules = snapshot.get("rule_ids")
    if (not isinstance(rules, list) or not rules
            or any(not isinstance(r, str) or not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]{2}", r) for r in rules)):
        errors.append("manifest.learning_style.rule_ids: 규칙 ID 목록 필요")
    elif len(rules) != len(set(rules)):
        errors.append("manifest.learning_style.rule_ids: 중복 규칙 ID")


def validate(m: dict, repo: Path | str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(m, dict):
        return ["manifest: JSON 객체 필요"]
    for key, typ in TOP_LEVEL_TYPES.items():
        _need(m, key, typ, "manifest", errors)
    if errors:
        return errors
    _check_snapshot(m["learning_style"], errors)
    if repo is not None and not errors:
        try:
            check_style(Path(repo), m["learning_style"])
        except LearningStyleError as exc:
            errors.append(f"manifest.learning_style: {exc}")
    if not RANGE_RE.fullmatch(m["range"]):
        errors.append(f"manifest.range: MMDD 또는 MMDD-MMDD 형식이어야 함: {m['range']}")
    if not SLUG_RE.fullmatch(m["slug"]):
        errors.append(f"manifest.slug: 영문·숫자·밑줄만: {m['slug']}")

    seen: set[str] = set()

    def new_id(value: str, where: str) -> None:
        if not ID_RE.fullmatch(value):
            errors.append(f"{where}: id 형식 오류: {value}")
        if value in seen:
            errors.append(f"{where}: 중복 id: {value}")
        seen.add(value)

    for i, s in _objects(m["sessions"], "sessions", errors):
        for key in ("date", "stt", "summary", "slides"):
            _need(s, key, str, f"sessions[{i}]", errors)

    topic_ids: set[str] = set()
    for i, sec in _objects(m["sections"], "sections", errors):
        where = f"sections[{i}]"
        if not all([_need(sec, "id", str, where, errors), _need(sec, "title", str, where, errors),
                    _need(sec, "short", str, where, errors), _need(sec, "topics", list, where, errors)]):
            continue
        new_id(sec["id"], where)
        for j, t in _objects(sec["topics"], f"{where}.topics", errors):
            tw = f"{where}.topics[{j}]"
            ok = all([_need(t, "id", str, tw, errors), _need(t, "title", str, tw, errors),
                      _need(t, "required_terms", list, tw, errors), _need(t, "layers", list, tw, errors),
                      _need(t, "supp", bool, tw, errors)])
            if not ok:
                continue
            new_id(t["id"], tw)
            topic_ids.add(t["id"])
            _strings(t["required_terms"], f"{tw}.required_terms", errors)
            if not all(isinstance(x, str) for x in t["layers"]):
                errors.append(f"{tw}.layers: 문자열 목록이어야 함")
                continue
            unknown = set(t["layers"]) - LAYER_NAMES
            if unknown:
                errors.append(f"{tw}.layers: 알 수 없는 레이어 {sorted(unknown)}")

    _check_why(m, errors)
    _strings(m["forbidden_outside_preview"], "forbidden_outside_preview", errors)
    if m["preview_topic"] not in topic_ids:
        errors.append(f"preview_topic: 토픽 id가 아님: {m['preview_topic']}")

    pids: set[str] = set()
    for i, q in _objects(m["problems"], "problems", errors):
        where = f"problems[{i}]"
        if not all([_need(q, key, str, where, errors) for key in ("id", "kind", "anchor", "date", "why")]):
            continue
        pid = _nfc(q["id"])
        kind = problem_kind(pid)
        if kind is None:
            errors.append(f"{where}.id: workbook id 형식 오류: {q['id']}")
        elif q["kind"] != kind:
            errors.append(f"{where}.kind: {pid}는 {kind}")
        elif repo is not None and not problem_md_path(repo, pid).is_file():
            errors.append(f"{where}.id: 문제 파일 없음: {problem_md_path(repo, pid)}")
        if pid in pids:
            errors.append(f"{where}.id: 중복 문제: {pid}")
        pids.add(pid)
        if q["anchor"] not in topic_ids:
            errors.append(f"{where}.anchor: 없는 토픽: {q['anchor']}")
        if not DATE_RE.fullmatch(q["date"]):
            errors.append(f"{where}.date: MMDD 형식이어야 함: {q['date']}")
        if not q["why"].strip():
            errors.append(f"{where}.why: 빈 문자열")
        elif "\n" in q["why"] or "|" in q["why"]:
            errors.append(f"{where}.why: 줄바꿈이나 |를 쓸 수 없음")
    if len(m["problems"]) > MAX_PROBLEMS:
        errors.append(f"problems: 최대 {MAX_PROBLEMS}개 ({len(m['problems'])}개)")

    hrefs: set[str] = set()
    for i, link in _objects(m["links"], "links", errors):
        where = f"links[{i}]"
        if _need(link, "topic", str, where, errors) and link["topic"] not in topic_ids:
            errors.append(f"{where}.topic: 없는 토픽: {link['topic']}")
        if _need(link, "href", str, where, errors):
            hrefs.add(link["href"])
    pdfs = {problem_pdf_name(m), answer_pdf_name(m)}
    if m["problems"]:
        errors += [f"links: 복습문제 PDF 링크 필요: {name}" for name in sorted(pdfs - hrefs)]
    else:
        errors += [f"links: 문제가 0개인데 PDF 링크가 있음: {name}" for name in sorted(pdfs & hrefs)]
    return errors


def load(path: Path | str, repo: Path | str | None = None) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ManifestError(f"{path}: 파일을 읽을 수 없음: {e}") from e
    try:
        m = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestError(f"{path}: JSON 형식 오류: {e}") from e
    errors = validate(m, repo)
    if errors:
        raise ManifestError("\n".join(errors))
    return m


def note_name(m: dict) -> str:
    return f"정리노트_{m['range']}_{m['slug']}.html"


def problem_set_name(m: dict) -> str:
    """build_workbook.py --name 값. PDF는 이 이름 + '-문제.pdf' / '-답안.pdf'."""
    return f"복습문제_{m['range']}_{m['slug']}"


def problem_pdf_name(m: dict) -> str:
    return f"{problem_set_name(m)}-문제.pdf"


def answer_pdf_name(m: dict) -> str:
    return f"{problem_set_name(m)}-답안.pdf"


def fig_dir_name(range_: str) -> str:
    return f"figures_{range_}"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) not in (1, 2):
        print("사용법: manifest.py RUN/manifest.json [REPO]", file=sys.stderr)
        return 2
    try:
        load(argv[0], argv[1] if len(argv) == 2 else None)
    except ManifestError as e:
        print(e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
