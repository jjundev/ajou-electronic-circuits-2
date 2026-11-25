"""기출 MD → AI 선별용 목록/원문 보존 JSON. 출력용 workbook JSON과 별개다."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

import yaml

from problem import ProblemError, load_problem, problem_figures
from check_md import split_frontmatter
from crop_exam import figure_filename

SCHEMA_VERSION = 2
EXAM_ID = re.compile(r'\d{4}-[12]_(?:중간|기말)(?:_[0-9A-Za-z가-힣]+)?-Q[1-9]\d*')
PART = re.compile(r'^\s*-\s+(?:\((\d+|[a-z])\)|(\d+|[a-z])\))\s+(.*)$')
SELECTION_LISTS = ('topics', 'circuit_types', 'required_concepts', 'learning_goals', 'evidence_sections')


class CatalogError(ValueError):
    pass


def nfc(value: str) -> str:
    return unicodedata.normalize('NFC', value)


def encoded(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'


def digest(value) -> str:
    return hashlib.sha256(encoded(value).encode('utf-8')).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(path: Path, root: Path) -> Path:
    if not path.resolve().is_relative_to(root.resolve()):
        raise CatalogError(f'저장소 밖 경로: {path}')
    return path


def relative(path: Path, repo: Path) -> str:
    return inside(path, repo).relative_to(repo).as_posix()


def read_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    if not isinstance(value, dict):
        raise CatalogError(f'YAML 객체가 필요해요: {path}')
    return value


def assets(path: Path) -> tuple[list[dict], list[Path]]:
    p = load_problem(path)
    folder = path.parent
    inputs = [folder / 'exam.yaml']
    if problem_figures(p) and not (folder / 'figures/figures.yaml').is_file():
        raise CatalogError(f'그림 설정 figures.yaml 없음: {folder}')
    if (folder / 'figures/figures.yaml').exists():
        inputs.append(folder / 'figures/figures.yaml')
    figures = []
    for fig_id, crop in problem_figures(p):
        if crop is not None:
            raise CatalogError(f'기출 그림은 crop을 지원하지 않아요: {path}')
        name = figure_filename(fig_id)
        original = folder / 'figures' / name
        redrawn = folder / 'figures/redrawn' / name
        if not original.is_file():
            raise CatalogError(f'그림 없음: {original}')
        display = redrawn if redrawn.is_file() else original
        inputs += [original] + ([redrawn] if display == redrawn else [])
        figures.append(dict(id=fig_id, original=original, display=display))
    return figures, list(dict.fromkeys(inputs))


def content_hash(path: Path) -> str:
    """selection 자체를 제외한 내용과 회로/시험 입력의 해시(자기 참조 없음)."""
    path = Path(path)
    meta, body = split_frontmatter(path.read_text(encoding='utf-8'))
    meta = {k: v for k, v in meta.items() if k != 'selection'}
    _, inputs = assets(path)
    # 경로 이전과 NFD 표기를 구분하지 않되 실제 파일 바이트는 구분한다.
    hashes = {nfc(os.path.relpath(p, path.parent)): file_hash(p) for p in inputs}
    return digest(dict(metadata=meta, body_md=body, assets=hashes))


def selection_data(p, content_sha: str) -> dict:
    value = p.meta.get('selection')
    if value is None:
        return dict(status='unclassified', **{k: [] for k in SELECTION_LISTS})
    if not isinstance(value, dict):
        raise CatalogError(f'selection 객체가 필요해요: {p.path}')
    for key in SELECTION_LISTS:
        if not isinstance(value.get(key), list) or any(not isinstance(x, str) or not x.strip() for x in value[key]):
            raise CatalogError(f'selection.{key}: 문자열 목록이 필요해요: {p.path}')
    headings = {h for h, _ in p.sections}
    if not set(value['evidence_sections']) <= headings:
        raise CatalogError(f'selection 근거 절 없음: {p.path}')
    status = value.get('review_status', 'draft')
    if status not in ('draft', 'reviewed'):
        raise CatalogError(f'selection.review_status: draft/reviewed 필요: {p.path}')
    if status == 'reviewed' and (not value['required_concepts'] or not value['evidence_sections']):
        raise CatalogError(f'검토 분류에 필요 개념과 근거가 필요해요: {p.path}')
    requirements = value.get('subpart_requirements', [])
    labels = {s['label'] for s in question_parts(p)}
    seen = set()
    if not isinstance(requirements, list):
        raise CatalogError(f'selection 소문항 목록 필요: {p.path}')
    for part in requirements:
        if not isinstance(part, dict):
            raise CatalogError(f'selection 소문항 객체 필요: {p.path}')
        label, concepts = part.get('label'), part.get('required_concepts')
        if (label not in labels or label in seen or not isinstance(concepts, list)
                or any(not isinstance(c, str) or not c.strip() for c in concepts)):
            raise CatalogError(f'selection 소문항 표지/개념 오류: {p.path}')
        seen.add(label)
    current = value.get('reviewed_content_sha256') == content_sha
    return {**value, 'status': status if current else 'stale'}


def question_parts(p) -> list[dict]:
    parts = []
    for line in (p.section('구할 것') or '').splitlines():
        if m := PART.match(line):
            parts.append(dict(label=m[1] or m[2], ask_md=m[3]))
    if len({v['label'] for v in parts}) != len(parts):
        raise CatalogError(f'소문항 표지 중복: {p.path}')
    return parts or [dict(label='main', ask_md=p.section('구할 것') or '')]


def build_catalog(repo: Path) -> tuple[dict, dict[str, dict]]:
    repo = Path(repo).absolute()
    folder = repo / 'from_the_past/md'
    if not folder.is_dir():
        raise CatalogError(f'기출 폴더 없음: {folder}')
    details, rows, errors = {}, [], []
    for path in sorted(folder.glob('*/Q*.md'), key=lambda p: nfc(str(p))):
        try:
            inside(path, repo)
            p = load_problem(path)
            pid = nfc(p.id)
            if not EXAM_ID.fullmatch(pid) or pid != nfc(f'{path.parent.name}-{path.stem}') or not p.is_exam:
                raise CatalogError(f'기출 경로/ID 불일치: {path}: {pid}')
            if pid in details:
                raise CatalogError(f'중복 ID: {pid}')
            figures, inputs = assets(path)
            for item in inputs:
                inside(item, repo)
            source_sha = content_hash(path)
            selection = selection_data(p, source_sha)
            subparts = question_parts(p)
            requirements = {s['label']: s['required_concepts'] for s in selection.get('subpart_requirements', [])}
            for part in subparts:
                part['required_concepts'] = requirements.get(part['label'], [])
            raw = path.read_text(encoding='utf-8')
            _, body = split_frontmatter(raw)
            detail = dict(schema_version=SCHEMA_VERSION, id=pid, title=p.title,
                          md_path=relative(path, repo), metadata=p.meta, raw_md=raw, body_md=body,
                          sections=[dict(heading=h, markdown=c) for h, c in p.sections],
                          exam=read_yaml(path.parent / 'exam.yaml'),
                          figures=[dict(id=f['id'], original_path=relative(f['original'], repo),
                                        display_path=relative(f['display'], repo)) for f in figures],
                          subparts=subparts, selection=selection, content_sha256=source_sha,
                          input_hashes={relative(f, repo): file_hash(f) for f in [path, *inputs]})
            deps = p.meta.get('depends_on') or []
            if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
                raise CatalogError(f'의존성 문자열 목록 필요: {path}')
            details[pid] = detail
            rows.append(dict(id=pid, kind='기출', title=p.title, md_path=detail['md_path'],
                             detail_path=f'problems/{pid}.json', textbook_chapters=p.meta.get('textbook_chapters') or [],
                             depends_on=[nfc(d) for d in deps], refs=p.meta.get('refs') or [],
                             points=p.meta.get('points'), eligible=True,
                             reference_solution='solution' if (p.section('풀이') or '').strip() else 'none',
                             adoption_unit='whole', subparts=subparts, selection=selection,
                             content_sha256=source_sha, detail_sha256=digest(detail)))
        except (ProblemError, ValueError, OSError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
            errors.append(f'{path}: {exc}')
    for row in rows:
        missing = set(row['depends_on']) - details.keys()
        if missing:
            errors.append(f"{row['id']}: 의존 문항 없음: {sorted(missing)}")
    if errors:
        raise CatalogError('\n'.join(errors))
    index = dict(schema_version=SCHEMA_VERSION, adoption_unit='whole', total=len(rows), problems=rows)
    index['catalog_sha256'] = digest(index)
    return index, details


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False, newline='\n') as f:
            tmp = Path(f.name)
            f.write(encoded(value))
        tmp.replace(path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def output_files(index: dict, details: dict) -> dict:
    return {'index.json': index, **{f'problems/{pid}.json': d for pid, d in details.items()}}


def write_catalog(repo: Path, out: Path) -> dict:
    out, repo = Path(out).absolute(), Path(repo).absolute()
    if out.resolve() == repo.resolve() or out.resolve().is_relative_to((repo / 'from_the_past/md').resolve()):
        raise CatalogError('원본 폴더에 JSON을 생성할 수 없어요')
    index, details = build_catalog(repo)
    files = output_files(index, details)
    # index를 마지막에 교체한다. 실패한 혼합 세대는 check에서 검출된다.
    for name in sorted(files, key=lambda n: n == 'index.json'):
        atomic_json(out / name, files[name])
    for stale in (out / 'problems').glob('*.json'):
        if f'problems/{stale.name}' not in files:
            stale.unlink()
    return index


def check_catalog(repo: Path, out: Path) -> list[str]:
    index, details = build_catalog(repo)
    files = output_files(index, details)
    errors = []
    for name, value in files.items():
        path = Path(out) / name
        if not path.is_file() or path.read_text(encoding='utf-8') != encoded(value):
            errors.append(f'오래됨/누락/변경: {path}')
    errors += [f'불필요 상세: {p}' for p in (Path(out) / 'problems').glob('*.json')
               if f'problems/{p.name}' not in files]
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=('build', 'check'))
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--out', type=Path)
    args = ap.parse_args(argv)
    out = args.out or args.repo / 'from_the_past/json'
    try:
        if args.command == 'build':
            result = write_catalog(args.repo, out)
            print(f"catalog: {result['total']} problems → {out / 'index.json'}")
            return 0
        errors = check_catalog(args.repo, out)
        if errors:
            raise CatalogError('\n'.join(errors))
        print('catalog: PASS')
        return 0
    except (CatalogError, OSError) as exc:
        print(f'ERROR {exc}', file=__import__('sys').stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
