#!/usr/bin/env python3
"""장 폴더 전체의 정합성을 검사한다. check_md.py가 파일 하나씩 보는 것을 장 단위로 보완한다.

사용법: python3 verify_chapter.py <장 폴더> [--recrop]    예) python3 verify_chapter.py ../ch09
"""
import re
import sys
from pathlib import Path

import yaml

from check_md import ID_RE, KIND_BY_PREFIX, md_files, split_frontmatter
from crop_figures import figure_filename

SECTION_ORDER = ["## 조건", "## 구할 것", "## 상속·참조", "## 회로", "## 답"]
REQUIRED = {0: "조건", 1: "구할 것", 3: "회로"}
ANSWER = 4
HEADING_RE = re.compile(r"^## .+$", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def load_docs(ch_dir):
    docs, errors = {}, []
    for path in md_files(ch_dir):
        try:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            docs[str(fm["id"])] = (path, fm, body)
        except Exception as e:  # 깨진 파일 하나가 나머지 검사를 막지 않게
            errors.append(f"{path.name}: frontmatter 읽기 실패 ({e})")
    return docs, errors


def check_numbering(docs):
    errors, infos = [], []
    for prefix, kind in KIND_BY_PREFIX.items():
        ids = [i for i in docs if (m := ID_RE.match(i)) and m.group(1) == prefix]
        if not ids:
            continue
        chapter = ID_RE.match(ids[0]).group(2)
        nums = {int(ID_RE.match(i).group(3)) for i in ids}
        missing = [f"{prefix}{chapter}.{n:02d}" for n in range(1, max(nums) + 1) if n not in nums]
        if missing:
            errors.append(f"{kind} 번호가 빠짐: {', '.join(missing)}")
    for i in sorted(docs):
        if i.startswith("X") and "E" + i[1:] not in docs:
            errors.append(f"{i}: 짝이 되는 예제 E{i[1:]}가 없음")
        if i.startswith("E") and "X" + i[1:] not in docs:
            infos.append(f"{i}: 연습문제 없음 (원문에 연습문제가 없는지 확인)")
    return errors, infos


def check_figures(ch_dir, docs):
    fig_dir = ch_dir / "figures"
    yaml_path = fig_dir / "figures.yaml"
    if not yaml_path.exists():
        return ["figures/figures.yaml 없음"]
    errors = []
    figures = (yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}).get("figures") or {}
    for key in figures:
        if not isinstance(key, str):
            errors.append(f"figures.yaml 그림 id {key!r}는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
    yaml_ids = {str(k) for k in figures}
    used = set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        for fig in fm.get("figures") or []:
            fid = str(fig["id"])
            used.add(fid)
            if figure_filename(fid) not in names:
                errors.append(f"{i}: 그림 {fid} 이미지 링크 없음")
        for link in links:
            if not (path.parent / link).exists():
                errors.append(f"{i}: 깨진 이미지 링크 {link}")
    if yaml_ids - used:
        errors.append(f"figures.yaml에만 있고 md가 쓰지 않는 그림: {', '.join(sorted(yaml_ids - used))}")
    if used - yaml_ids:
        errors.append(f"md가 쓰지만 figures.yaml에 없는 그림: {', '.join(sorted(used - yaml_ids))}")
    pngs = {p.name for p in fig_dir.glob("*.png")}
    expected = {figure_filename(i) for i in yaml_ids}
    if expected - pngs:
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_figures.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    return errors


def check_structure(docs):
    errors = []
    for i, (path, fm, body) in sorted(docs.items()):
        first = next((line for line in body.splitlines() if line.strip()), "")
        if not first.startswith("# "):
            errors.append(f"{i}: 제목 줄(# …)이 없음")
        heads = HEADING_RE.findall(body)
        order = []
        for h in heads:
            k = next((k for k, s in enumerate(SECTION_ORDER) if h.startswith(s)), None)
            if k is None:
                errors.append(f"{i}: 알 수 없는 절 '{h}'")
            else:
                order.append(k)
        if order != sorted(order):
            errors.append(f"{i}: 절 순서가 FORMAT과 다름 ({' → '.join(heads)})")
        for k, name in REQUIRED.items():
            if k not in order:
                errors.append(f"{i}: 필수 절 없음 ({name})")
        has_answer = ANSWER in order
        if i.startswith("E") and not has_answer:
            errors.append(f"{i}: 예제에 '## 답' 절 없음")
        if not i.startswith("E") and has_answer:
            errors.append(f"{i}: 예제가 아닌데 '## 답' 절이 있음")
    return errors


def verify(ch_dir, recrop=False):
    ch_dir = Path(ch_dir)
    docs, errors = load_docs(ch_dir)
    if not docs and not errors:
        return ["문제 md가 없음"], []
    numbering_errors, infos = check_numbering(docs)
    errors += numbering_errors
    errors += check_figures(ch_dir, docs)
    errors += check_structure(docs)
    return errors, infos


def main(argv):
    args = [a for a in argv[1:] if a != "--recrop"]
    if len(args) != 1:
        print("사용법: python3 verify_chapter.py <장 폴더> [--recrop]", file=sys.stderr)
        return 2
    ch_dir = Path(args[0])
    if not ch_dir.is_dir():
        print(f"장 폴더가 없음: {ch_dir}", file=sys.stderr)
        return 2
    errors, infos = verify(ch_dir, recrop="--recrop" in argv[1:])
    for e in errors:
        print(f"ERROR {e}")
    for i in infos:
        print(f"INFO  {i}")
    print(f"{ch_dir}: 오류 {len(errors)}개, 참고 {len(infos)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
