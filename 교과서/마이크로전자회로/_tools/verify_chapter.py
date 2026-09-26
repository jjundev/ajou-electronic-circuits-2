#!/usr/bin/env python3
"""장 폴더 전체의 정합성을 검사한다. check_md.py가 파일 하나씩 보는 것을 장 단위로 보완한다.

사용법: python3 verify_chapter.py <장 폴더> [--recrop]    예) python3 verify_chapter.py ../ch09
"""
import re
import sys
import tempfile
from pathlib import Path

import fitz
import yaml

from check_md import ID_RE, KIND_BY_PREFIX, md_files, split_frontmatter
from crop_figures import crop_all, figure_filename
from make_index import build_index

# 문제집용 절(## 원문, ## 힌트, ## 풀이)은 선택이다. 모양은 check_md.check_workbook_sections가 본다.
SECTION_ORDER = ["## 원문", "## 조건", "## 구할 것", "## 상속·참조", "## 회로", "## 답", "## 힌트", "## 풀이"]
REQUIRED = {1: "조건", 2: "구할 것", 4: "회로"}
ANSWER = 5
HEADING_RE = re.compile(r"^## .+$", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
FIG_ID_RE = re.compile(r"^\d+\.\d+$")
H1_RE = re.compile(r"^# (.+) — 문제 인덱스$", re.M)


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
    try:
        spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"figures.yaml 읽기 실패 ({e})"]
    if not isinstance(spec, dict):
        return ["figures.yaml 최상위가 매핑(키: 값)이 아님"]
    figures = spec.get("figures") or {}
    if not isinstance(figures, dict):
        return ['figures.yaml의 figures가 매핑("id": {...})이 아님']
    errors = []
    yaml_ids, yaml_crops = set(), {}
    for key, fig in figures.items():
        if not isinstance(key, str):
            errors.append(f"figures.yaml 그림 id {key!r}는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
        elif not FIG_ID_RE.match(key):
            errors.append(f"figures.yaml 그림 id {key!r} 형식 오류 (예: \"9.30\")")
        else:
            yaml_ids.add(key)
            crops = fig.get("crops") if isinstance(fig, dict) else None
            yaml_crops[key] = {str(n) for n in crops} if isinstance(crops, dict) else set()
    used, used_crops = set(), set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        figs = fm.get("figures") or []
        if not isinstance(figs, list):
            errors.append(f"{i}: frontmatter figures가 목록이 아님")
            figs = []
        for fig in figs:
            fid = fig.get("id") if isinstance(fig, dict) else None
            if fid is None or not FIG_ID_RE.match(str(fid)):
                errors.append(f"{i}: figures 항목 {fig!r}에 올바른 id가 없음")
                continue
            fid = str(fid)
            used.add(fid)
            crop = fig.get("crop")
            crop = None if crop is None else str(crop)
            if crop is not None:
                used_crops.add((fid, crop))
                if fid in yaml_crops and crop not in yaml_crops[fid]:
                    errors.append(f"{i}: 그림 {fid} 크롭 {crop}이 figures.yaml에 없음")
            expected_link = figure_filename(fid, crop)
            if expected_link not in names:
                errors.append(f"{i}: 그림 {fid} 이미지 링크 없음 ({expected_link})")
        for link in links:
            if not (path.parent / link).exists():
                errors.append(f"{i}: 깨진 이미지 링크 {link}")
    if yaml_ids - used:
        errors.append(f"figures.yaml에만 있고 md가 쓰지 않는 그림: {', '.join(sorted(yaml_ids - used))}")
    if used - yaml_ids:
        errors.append(f"md가 쓰지만 figures.yaml에 없는 그림: {', '.join(sorted(used - yaml_ids))}")
    unused_crops = {(f, n) for f, ns in yaml_crops.items() for n in ns} - used_crops
    if unused_crops:
        errors.append("figures.yaml에만 있고 md가 쓰지 않는 크롭: "
                      + ", ".join(f"{f} {n}" for f, n in sorted(unused_crops)))
    pngs = {p.name for p in fig_dir.glob("*.png")}
    expected = {figure_filename(i) for i in yaml_ids}
    expected |= {figure_filename(f, n) for f, ns in yaml_crops.items() for n in ns}
    if expected - pngs:
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_figures.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    answer_panels = {}
    for _, fm, _ in docs.values():
        for fig in fm.get("figures") or []:
            if isinstance(fig, dict) and fig.get("role") == "answer" and isinstance(fig.get("panels"), list):
                answer_panels.setdefault(str(fig.get("id")), set()).update(map(str, fig["panels"]))
    for i, (_, fm, _) in sorted(docs.items()):
        for fig in fm.get("figures") or []:
            if not isinstance(fig, dict) or fig.get("role") != "problem" or fig.get("crop") is not None:
                continue
            panels = fig.get("panels") if isinstance(fig.get("panels"), list) else []
            leak = answer_panels.get(str(fig.get("id")), set()) - set(map(str, panels))
            if leak:
                errors.append(f"{i}: 그림 {fig.get('id')} 문제 이미지에 풀이 패널 {', '.join(sorted(leak))}이 보임 (crop 필요)")
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


def check_readme(ch_dir):
    readme = ch_dir / "README.md"
    if not readme.exists():
        return ["README.md 없음 (make_index.py 실행)"]
    text = readme.read_text(encoding="utf-8")
    m = H1_RE.match(text)
    if not m:
        return ["README.md 첫 줄이 '# <제목> — 문제 인덱스' 형식이 아님"]
    try:
        fresh = build_index(ch_dir, m.group(1))
    except Exception as e:  # 깨진 md가 있으면 인덱스를 만들 수 없음 — 그 원인은 다른 검사가 보고
        return [f"README.md 비교 실패 ({e})"]
    return [] if fresh == text else ["README.md가 최신이 아님 (make_index.py 다시 실행)"]


def check_recrop(ch_dir):
    fig_dir = ch_dir / "figures"
    errors = []
    try:
        spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8"))
        spec["pdf"] = str((fig_dir / spec["pdf"]).resolve())
        with tempfile.TemporaryDirectory() as t:
            tmp_ch = Path(t) / ch_dir.name
            (tmp_ch / "figures").mkdir(parents=True)
            (tmp_ch / "figures" / "figures.yaml").write_text(
                yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            for out in crop_all(tmp_ch):
                current = fig_dir / out.name
                if not current.exists():
                    continue  # PNG 없음은 check_figures가 보고
                a, b = fitz.Pixmap(str(current)), fitz.Pixmap(str(out))
                if (a.width, a.height, a.samples) != (b.width, b.height, b.samples):
                    errors.append(f"{out.name}: figures.yaml로 다시 자른 결과와 다름 (crop_figures.py 다시 실행)")
    except Exception as e:  # PDF 없음(worktree 심볼릭 링크 누락 등), bbox 오류
        errors.append(f"다시 자르기 실패 ({e})")
    return errors


def verify(ch_dir, recrop=False):
    ch_dir = Path(ch_dir)
    docs, errors = load_docs(ch_dir)
    if not docs and not errors:
        return ["문제 md가 없음"], []
    infos = []
    checks = [("check_numbering", lambda: check_numbering(docs)),
              ("check_figures", lambda: (check_figures(ch_dir, docs), [])),
              ("check_structure", lambda: (check_structure(docs), [])),
              ("check_readme", lambda: (check_readme(ch_dir), []))]
    if recrop:
        checks.append(("check_recrop", lambda: (check_recrop(ch_dir), [])))
    for name, run in checks:
        try:  # 예상 못 한 입력 하나가 traceback으로 나머지 보고를 막지 않게
            found_errors, found_infos = run()
        except Exception as e:
            found_errors, found_infos = [f"{name} 실패 ({e!r})"], []
        errors += found_errors
        infos += found_infos
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
