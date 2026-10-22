#!/usr/bin/env python3
"""
workbook 문제 목록 (복습문제 선별용). 문제 md는 workbook/problem.py의 load_problem으로 읽는다.

한 줄에 문제 하나, 탭으로 구분:
  id  kind  secnum  section  difficulty  used  title
- secnum: 교과서는 section 앞 절 번호(예: 9.1.2. 번호가 없으면 section 그대로), 기출은 "ch" + textbook_chapters(예: ch9,10)
- difficulty: 교과서 frontmatter 값, 기출은 "-"
- used: 이전 팩 .assets/problems.txt에 있으면 "USED", 아니면 "-"
CLI: problem_index.py --repo REPO [--used REPO/복습노트] [--chapters 9,10]
JSON: --format json --catalog-out RUN/exam-catalog (전체 소문항·필요 개념·상세 JSON 참조).
읽을 수 없는 md는 stderr에 `ERROR <경로>: <이유>`로 적고 건너뛴다(종료 코드 1).
"""

from __future__ import annotations

import argparse
import json
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


def used_in_ranges(notes_dir: Path | str, exclude: str | None = None) -> dict[str, list[str]]:
    """<notes_dir>/*/.assets/problems.txt 의 id (줄 형식 `id | why`).

    exclude: 이 폴더 이름(NFC로 비교)의 problems.txt는 건너뛴다(같은 range를 다시 돌릴 때
    자기 자신의 이전 결과가 USED로 잡히지 않게 한다).
    """
    notes_dir, ids = Path(notes_dir), {}
    if not notes_dir.is_dir():
        return ids
    exclude_nfc = nfc(exclude) if exclude is not None else None
    for path in notes_dir.glob("*/.assets/problems.txt"):
        if exclude_nfc is not None and nfc(path.parent.parent.name) == exclude_nfc:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            pid = nfc(line.split("|", 1)[0].strip())
            if pid:
                ids.setdefault(pid, []).append(nfc(path.parent.parent.name))
    return ids


def used_ids(notes_dir: Path | str, exclude: str | None = None) -> set[str]:
    return set(used_in_ranges(notes_dir, exclude))


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
          chapters: set[int] | None = None,
          exclude_range: str | None = None) -> tuple[list[list[str]], list[str]]:
    problem = _workbook(Path(repo))
    used = used_ids(used_dir, exclude=exclude_range) if used_dir else set()
    rows, errors = [], []
    for path in md_paths(repo, chapters):
        try:
            # 손으로 쓴 md의 어떤 오류도 목록 전체를 멈추지 않게 넓게 잡는다.
            p = problem.load_problem(path)
            meta, pid = p.meta, nfc(p.id)
            exam = meta.get("kind") == "기출"
            if exam and chapters and not set(meta.get("textbook_chapters") or []) & chapters:
                continue
            rows.append([pid, str(meta["kind"]), secnum(meta), str(meta.get("section", "-")),
                         "-" if exam else str(meta.get("difficulty", "-")),
                         "USED" if pid in used else "-", p.title.replace("\t", " ")])
        except Exception as e:
            errors.append(f"{path}: {e}")
    return rows, errors


def _textbook_inputs(p, repo: Path) -> dict[str, str]:
    from exam_catalog import file_hash, inside
    from crop_figures import figure_filename
    inputs = [p.path]
    figures = _workbook(repo).problem_figures(p)
    if figures:
        inputs.append(p.figures_dir / 'figures.yaml')
    inputs += [p.figures_dir / figure_filename(fig_id, crop) for fig_id, crop in figures]
    return {inside(path, repo).relative_to(repo).as_posix(): file_hash(path) for path in inputs}


def candidate_data(repo: Path, used_dir=None, chapters=None, exclude_range=None) -> tuple[dict, list[str]]:
    """기출은 상세 JSON 참조와 전체 소문항을, 교과서는 기존 선별 정보를 제공한다."""
    repo = Path(repo)
    problem = _workbook(repo)
    from exam_catalog import build_catalog, CatalogError, digest, question_parts
    rows, errors = index(repo, used_dir, chapters, exclude_range)
    try:
        catalog, _ = build_catalog(repo)
    except CatalogError as exc:
        # 불완전한 기출 JSON을 성공한 카탈로그로 취급하지 않는다.
        return {}, [*errors, str(exc)]
    exams = {p['id']: p for p in catalog['problems']}
    textbook_paths = {nfc(p.stem): p for p in md_paths(repo, chapters) if not p.stem.startswith('Q')}
    items = []
    history = used_in_ranges(used_dir, exclude_range) if used_dir else {}
    for pid, kind, secnum_, section, difficulty, used, title in rows:
        if kind == '기출':
            item = dict(exams[pid])
        else:
            # 기존 index가 검증한 교과서 MD에서 의존성도 가져온다.
            path = textbook_paths[pid]
            try:
                p = problem.load_problem(path)
                inputs = _textbook_inputs(p, repo)
            except (ValueError, OSError, problem.ProblemError) as exc:
                errors.append(f'{path}: {exc}')
                continue
            item = dict(id=pid, kind=kind, title=title, secnum=secnum_, section=section,
                        difficulty=difficulty, depends_on=p.meta.get('depends_on') or [],
                        md_path=path.relative_to(repo).as_posix(), content_sha256=digest(inputs),
                        input_hashes=inputs, subparts=question_parts(p),
                        reference_solution=('solution' if (p.section('풀이') or '').strip()
                                            else 'answer_only' if problem.solution(p) else 'none'),
                        adoption_unit='whole')
        items.append({**item, 'used': used == 'USED', 'used_in_ranges': sorted(history.get(pid, []))})
    return dict(schema_version=2, adoption_unit='whole', catalog_sha256=catalog['catalog_sha256'],
                catalog_root=None, problems=items), errors


def record_selection(manifest: dict, candidates: dict, review: dict | None = None) -> dict:
    """확정 manifest의 순서와 근거를 저장한다. 수업 범위의 의미 판단은 AI 몫이다."""
    from review_selection import POLICY, MAX_PROBLEMS, validate_review
    policy = manifest.get('selection_policy')
    if policy is not None and policy != POLICY:
        raise ValueError(f'알 수 없는 선발 정책: {policy}')
    modern = policy == POLICY
    if modern:
        validate_review(manifest, candidates, review)
    table = {p['id']: p for p in candidates['problems']}
    selected = manifest['problems']
    ids = [q['id'] for q in selected]
    if len(ids) != len(set(ids)):
        raise ValueError('선택 ID 중복')
    if len(ids) > MAX_PROBLEMS:
        raise ValueError(f'최대 {MAX_PROBLEMS}문항')
    output = []
    for q in selected:
        pid = q['id']
        if pid not in table:
            raise ValueError(f'후보에 없는 ID: {pid}')
        item = table[pid]
        if item['used']:
            raise ValueError(f'이전 팩에서 사용한 ID: {pid}')
        if q.get('kind') != item['kind'] or not q.get('why', '').strip():
            raise ValueError(f'종류/선택 이유 오류: {pid}')
        if 'subparts' in q or q.get('adoption_unit', 'whole') != 'whole':
            raise ValueError(f'문항 전체만 채택할 수 있어요: {pid}')
        missing = set(item['depends_on']) - set(ids)
        if missing or any(ids.index(d) >= ids.index(pid) for d in item['depends_on'] if d in ids):
            raise ValueError(f'의존 문항을 먼저 선택해야 해요: {pid}: {sorted(missing)}')
        if modern and q['priority'] == 'core' and any(selected[ids.index(d)]['priority'] != 'core' for d in item['depends_on']):
            raise ValueError(f'핵심 문항의 전제 문항도 핵심이어야 합니다: {pid}')
        output.append(dict(id=pid, kind=item['kind'], why=q['why'], adoption_unit='whole',
                           subparts=item.get('subparts', []), depends_on=item['depends_on'],
                           content_sha256=item.get('content_sha256'),
                           classification_status=item.get('selection', {}).get('status')))
        if modern:
            output[-1].update(priority=q['priority'], learning_goals=q['learning_goals'],
                estimated_minutes=q['estimated_minutes'], subpart_count=max(1, len(item.get('subparts', []))),
                reference_solution=item.get('reference_solution', 'none'))
    result = dict(schema_version=2 if modern else 1, range=manifest['range'], adoption_unit='whole',
                catalog_sha256=candidates['catalog_sha256'],
                scope_check='AI must verify every subpart and figure against the taught scope',
                problems=output)
    if modern:
        from exam_catalog import digest
        result.update(policy=POLICY, review=review, workload=dict(
            estimated_minutes=sum(q['estimated_minutes'] for q in output),
            core_estimated_minutes=sum(q['estimated_minutes'] for q in output if q['priority'] == 'core'),
            subpart_count=sum(q['subpart_count'] for q in output), estimates_only=True))
        result['candidates_sha256'] = digest(candidates['problems'])
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--used", help="이전 팩 폴더들의 부모(보통 REPO/복습노트)")
    ap.add_argument("--chapters", help="쉼표로 구분한 장 번호 (예: 9,10)")
    ap.add_argument("--exclude-range", help="이 range의 problems.txt는 USED 집계에서 뺀다(같은 range 재실행용)")
    ap.add_argument('--format', choices=('tsv', 'json'), default='tsv')
    ap.add_argument('--catalog-out', type=Path, help='JSON 모드의 상세 카탈로그 생성 위치(RUN 아래)')
    ap.add_argument('--selection-manifest', type=Path, help='확정 manifest의 전체 문항 채택 기록')
    ap.add_argument('--selection-out', type=Path, help='RUN/selection.json')
    ap.add_argument('--candidates-input', type=Path, help='선별 때 읽은 RUN/candidates.json (변경 감지)')
    ap.add_argument('--selection-review', type=Path, help='exam-first-v2의 후보 판정/학습 목표 검토 JSON')
    args = ap.parse_args(argv)
    if args.selection_review and not args.selection_manifest:
        ap.error('--selection-review는 --selection-manifest와 함께 써요')
    chapters = {int(c) for c in args.chapters.split(",")} if args.chapters else None
    if args.format == 'json':
        if not args.catalog_out:
            ap.error('--format json에는 --catalog-out이 필요해요')
        if bool(args.selection_manifest) != bool(args.selection_out):
            ap.error('--selection-manifest와 --selection-out은 함께 써요')
        if bool(args.selection_manifest) != bool(args.candidates_input):
            ap.error('선택 기록에는 --candidates-input이 필요해요')
        _workbook(Path(args.repo))
        from exam_catalog import atomic_json, write_catalog, CatalogError
        try:
            data, errors = candidate_data(Path(args.repo), args.used, chapters, args.exclude_range)
            if not data:
                raise CatalogError('\n'.join(errors))
            catalog = write_catalog(Path(args.repo), args.catalog_out)
            if catalog['catalog_sha256'] != data['catalog_sha256']:
                raise CatalogError('선별 중 원본이 변경됐어요. 다시 실행해 주세요')
            data['catalog_root'] = str(args.catalog_out.absolute())
            if args.selection_manifest:
                manifest = json.loads(args.selection_manifest.read_text(encoding='utf-8'))
                if manifest.get('selection_policy') == 'exam-first-v2' and (
                        not args.used or args.exclude_range != manifest['range']):
                    raise CatalogError('새 선발에는 --used 및 manifest range와 같은 --exclude-range가 필요합니다')
                previous = json.loads(args.candidates_input.read_text(encoding='utf-8'))
                old = {q['id']: q for q in previous['problems']}
                current = {q['id']: q for q in data['problems']}
                if (previous['catalog_sha256'] != data['catalog_sha256']
                        or previous.get('schema_version') != data['schema_version']
                        or old != current
                        or any(old.get(q['id']) != current.get(q['id']) for q in manifest['problems'])):
                    raise CatalogError('후보/사용 이력/원본이 변경됐어요. 후보를 다시 검토해 주세요')
                review = json.loads(args.selection_review.read_text(encoding='utf-8')) if args.selection_review else None
                atomic_json(args.selection_out, record_selection(manifest, data, review))
            print(json.dumps(data, ensure_ascii=False, indent=2))
            for error in errors:
                print(f'ERROR {error}', file=sys.stderr)
            return int(bool(errors))
        except (ValueError, OSError, KeyError) as exc:
            print(f'ERROR {exc}', file=sys.stderr)
            return 1
    if args.catalog_out or args.selection_manifest or args.selection_out or args.candidates_input:
        ap.error('카탈로그/선택 기록 옵션은 --format json과 함께 써요')
    rows, errors = index(Path(args.repo), args.used, chapters, args.exclude_range)
    print(HEADER)
    for row in rows:
        print("\t".join(row))
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
