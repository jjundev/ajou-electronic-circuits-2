#!/usr/bin/env python3
"""시험 폴더 전체의 정합성을 검사한다. check_exam.py가 파일 하나씩 보는 것을 시험 단위로 보완한다.

사용법: python3 verify_exam.py <시험 폴더> [--recrop]    예) python3 verify_exam.py ../2021-1_중간 --recrop
"""
import re
import sys
import tempfile
from pathlib import Path

import fitz
import yaml

from check_exam import FILE_RE, ID_RE, exam_title, md_files, split_frontmatter
from crop_exam import FIG_ID_RE, crop_all, figure_filename, valid_bbox
from make_exam_index import build_exam_index
from verify_chapter import check_structure  # check_exam이 교과서 _tools를 sys.path에 넣음

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def load_docs(exam_dir):
    docs, errors = {}, []
    for path in md_files(exam_dir):
        try:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            docs[str(fm["id"])] = (path, fm, body)
        except Exception as e:  # 깨진 파일 하나가 나머지 검사를 막지 않게
            errors.append(f"{path.name}: frontmatter 읽기 실패 ({e})")
    return docs, errors


def check_stray_files(exam_dir):
    return [f"알 수 없는 md 파일: {p.name} (Q<번호>.md와 README.md만 둠)"
            for p in sorted(exam_dir.glob("*.md")) if p.name != "README.md" and not FILE_RE.match(p.name)]


def check_numbering(docs):
    nums = {int(m.group(2)) for i in docs if (m := ID_RE.match(i))}
    if not nums:
        return []
    missing = [f"Q{n}" for n in range(1, max(nums) + 1) if n not in nums]
    return [f"문제 번호가 빠짐: {', '.join(missing)}"] if missing else []


def check_figures(exam_dir, docs):
    fig_dir = exam_dir / "figures"
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
        return ['figures.yaml의 figures가 매핑("Q2": {...})이 아님']
    errors, yaml_ids = [], set()
    for key, fig in figures.items():
        if not isinstance(key, str) or not FIG_ID_RE.match(key):
            errors.append(f'figures.yaml 그림 id {key!r} 형식 오류 (따옴표로 감싼 "Q2" 또는 "Q2-2")')
            continue
        yaml_ids.add(key)
        if not isinstance(fig, dict) or "pdf" not in fig:
            errors.append(f"figures.yaml {key}: pdf 경로가 없음")
        elif not valid_bbox(fig.get("bbox")):
            errors.append(f"figures.yaml {key}: bbox 는 [x0, y0, x1, y1] 숫자 4개")
    used = set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        figs = fm.get("figures") or []
        if not isinstance(figs, list):
            errors.append(f"{i}: frontmatter figures가 목록이 아님")
            figs = []
        for fig in figs:
            fid = fig.get("id") if isinstance(fig, dict) else None
            if not isinstance(fid, str) or not FIG_ID_RE.match(fid):
                errors.append(f"{i}: figures 항목 {fig!r}에 올바른 id가 없음")
                continue
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
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_exam.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    return errors


def check_exam_yaml(exam_dir):
    path = exam_dir / "exam.yaml"
    if not path.exists():
        return ["exam.yaml 없음"]
    meta = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = []
    title = exam_title(exam_dir.name)
    if meta.get("exam") != title:
        errors.append(f"exam.yaml exam {meta.get('exam')!r} 가 폴더와 안 맞음 (기대: \"{title}\")")
    if not isinstance(meta.get("header"), str) or not meta["header"]:
        errors.append("exam.yaml header(시험지 머리 문구) 없음")
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("exam.yaml sources 는 원본 PDF 경로 목록")
        sources = []
    for s in sources + list(meta.get("aux_sources") or []):
        if not (exam_dir / s).is_file():
            errors.append(f"exam.yaml 원본 없음: {s}")
    return errors


def check_readme(exam_dir):
    readme = exam_dir / "README.md"
    if not readme.exists():
        return ["README.md 없음 (make_exam_index.py 실행)"]
    try:
        fresh = build_exam_index(exam_dir)
    except Exception as e:  # 깨진 md나 exam.yaml — 그 원인은 다른 검사가 보고
        return [f"README.md 비교 실패 ({e})"]
    return [] if fresh == readme.read_text(encoding="utf-8") else ["README.md가 최신이 아님 (make_exam_index.py 다시 실행)"]


def check_recrop(exam_dir):
    fig_dir = exam_dir / "figures"
    errors = []
    try:
        spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
        for fig in (spec.get("figures") or {}).values():
            fig["pdf"] = str((fig_dir / fig["pdf"]).resolve())
        with tempfile.TemporaryDirectory() as t:
            tmp_exam = Path(t) / exam_dir.name
            (tmp_exam / "figures").mkdir(parents=True)
            (tmp_exam / "figures" / "figures.yaml").write_text(
                yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            for out in crop_all(tmp_exam):
                current = fig_dir / out.name
                if not current.exists():
                    continue  # PNG 없음은 check_figures가 보고
                a, b = fitz.Pixmap(str(current)), fitz.Pixmap(str(out))
                if (a.width, a.height, a.samples) != (b.width, b.height, b.samples):
                    errors.append(f"{out.name}: figures.yaml로 다시 자른 결과와 다름 (crop_exam.py 다시 실행)")
    except Exception as e:  # PDF 없음, bbox 오류, pdf 키 누락
        errors.append(f"다시 자르기 실패 ({e})")
    return errors


def verify(exam_dir, recrop=False):
    exam_dir = Path(exam_dir).resolve()
    docs, errors = load_docs(exam_dir)
    if not docs and not errors:
        return ["문제 md가 없음"]
    checks = [("check_stray_files", lambda: check_stray_files(exam_dir)),
              ("check_numbering", lambda: check_numbering(docs)),
              ("check_figures", lambda: check_figures(exam_dir, docs)),
              ("check_structure", lambda: check_structure(docs)),
              ("check_exam_yaml", lambda: check_exam_yaml(exam_dir)),
              ("check_readme", lambda: check_readme(exam_dir))]
    if recrop:
        checks.append(("check_recrop", lambda: check_recrop(exam_dir)))
    for name, run in checks:
        try:  # 예상 못 한 입력 하나가 traceback으로 나머지 보고를 막지 않게
            errors += run()
        except Exception as e:
            errors.append(f"{name} 실패 ({e!r})")
    return errors


def main(argv):
    args = [a for a in argv[1:] if a != "--recrop"]
    if len(args) != 1:
        print("사용법: python3 verify_exam.py <시험 폴더> [--recrop]", file=sys.stderr)
        return 2
    exam_dir = Path(args[0])
    if not exam_dir.is_dir():
        print(f"시험 폴더가 없음: {exam_dir}", file=sys.stderr)
        return 2
    errors = verify(exam_dir, recrop="--recrop" in argv[1:])
    for e in errors:
        print(f"ERROR {e}")
    print(f"{exam_dir}: 오류 {len(errors)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
