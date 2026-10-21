"""Select a review pack's problems.txt and read the workbook problems it lists."""
import hashlib
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from epe_types import BUNDLE, ExplainError, Problem, SourcePack
from epe_shared import (load_problem, html_fields, problem_figures, solution, ProblemError,
                        TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR, textbook_figure_filename,
                        exam_figure_filename, parse)

REVIEW_DIR = '복습노트'
PACK_RE = re.compile(r'\d{4}(?:-\d{4})?')
LINE_RE = re.compile(r'^\s*(\S+)\s*\|\s*(.*\S)\s*$')
LABEL_RE = re.compile(r'^\s*\(?(\d+|[a-z])\)\s')


def nfc(value):
    return unicodedata.normalize('NFC', str(value))


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(path: Path, repo: Path) -> Path:
    path, repo = Path(path).absolute(), Path(repo).absolute()
    # Normalize unresolved spellings only; two existing NFC/NFD sibling directories are distinct.
    if not repo.exists():
        repo = existing_path(repo)
    try:
        path.resolve().relative_to(repo.resolve())
    except ValueError:
        try:
            if not path.exists():
                path = existing_path(path)
            path.resolve().relative_to(repo.resolve())
        except (ValueError, OSError) as exc:
            raise ExplainError(f'저장소 밖 경로: {path}') from exc
    current = path
    while current != repo and current != current.parent:
        if current.is_symlink():
            raise ExplainError(f'심볼릭 링크 입력 금지: {current}')
        current = current.parent
    return path

def existing_path(path: Path) -> Path:
    """Resolve encoded/Unicode-normalized paths component by component."""
    path = path.absolute()
    current = Path(path.anchor)
    for part in path.parts[1:]:
        candidate = current / part
        if candidate.exists():
            current = candidate
        elif current.is_dir():
            matches = [p for p in current.iterdir() if nfc(p.name) == nfc(part)]
            if len(matches) != 1:
                raise ExplainError(f'경로 없음 또는 모호함: {path}')
            current = matches[0]
        else:
            raise ExplainError(f'경로 없음: {path}')
    return current


def date_key(value):
    try:
        datetime.strptime('2000' + value, '%Y%m%d')
    except ValueError as exc:
        raise ExplainError(f'잘못된 날짜: {value}') from exc
    return value


def _folders(repo: Path) -> dict:
    """NFC folder name -> (path, has problems.txt) for pack-named folders under 복습노트."""
    try:
        root = existing_path(repo / REVIEW_DIR)
    except ExplainError:
        return {}
    out = {}
    for path in sorted(root.iterdir()):
        name = nfc(path.name)
        if path.is_dir() and PACK_RE.fullmatch(name):
            out[name] = (path, (path / BUNDLE / 'problems.txt').is_file())
    return out


def resolve_sources(repo: Path, target: str | None) -> tuple[Path, ...]:
    repo = Path(repo).absolute()
    folders = _folders(repo)
    ready = {n: p for n, (p, ok) in folders.items() if ok}
    if target == 'all':
        chosen = [p for n,p in sorted(ready.items(),key=lambda pair:(pair[0].split('-')[-1],pair[0]),reverse=True)]
        if not chosen:
            raise ExplainError('대상 없음: problems.txt가 있는 복습 팩이 없습니다')
    elif target is None:
        if not ready:
            raise ExplainError('대상 없음: problems.txt가 있는 복습 팩이 없습니다')
        latest = max(n.split('-')[-1] for n in ready)
        found = {n: p for n, p in ready.items() if n.split('-')[-1] == latest}
        if len(found) > 1:
            raise ExplainError('여러 후보 (최신 날짜의 통합/개별):\n' + '\n'.join(str(p) for p in found.values()))
        chosen = list(found.values())
    else:
        target = nfc(target).strip()
        if not PACK_RE.fullmatch(target):
            raise ExplainError('대상 없음 또는 잘못된 대상: ' + target)
        bounds = target.split('-')
        for date in bounds:
            date_key(date)
        if len(bounds) == 1:
            if target not in folders:
                raise ExplainError('대상 없음: ' + target)
            if target not in ready:
                raise ExplainError(f'문제 없는 팩: {target} (problems.txt 없음)')
            chosen = [ready[target]]
        else:
            if bounds[0] > bounds[1]:
                raise ExplainError('날짜 범위 순서 오류')
            individual = {n: p for n, p in ready.items() if '-' not in n and bounds[0] <= n <= bounds[1]}
            if target in ready and individual:
                raise ExplainError('여러 후보 (통합/개별):\n'
                                   + '\n'.join(str(p) for p in [ready[target], *individual.values()]))
            chosen = [ready[target]] if target in ready else [individual[n] for n in sorted(individual)]
            if not chosen:
                raise ExplainError(f'문제 없는 팩: {target} (범위 안에 problems.txt가 있는 팩 없음)')
    return tuple(inside(p / BUNDLE / 'problems.txt', repo) for p in chosen)


def md_path(repo: Path, pid: str) -> Path:
    repo = Path(repo).absolute()
    if m := TEXTBOOK_ID_RE.match(pid):
        path = repo / '교과서/마이크로전자회로' / f'ch{int(m.group(2)):02d}' / KIND_DIR[m.group(1)] / f'{pid}.md'
    elif m := EXAM_ID_RE.match(pid):
        path = repo / 'from_the_past/md' / m.group(1) / f'Q{m.group(2)}.md'
    else:
        raise ExplainError(f'문항 id 형식 오류: {pid}')
    try:
        path = existing_path(path)
    except ExplainError as exc:
        raise ExplainError(f'md 파일 없음: {path}') from exc
    if not path.is_file():
        raise ExplainError(f'md 파일 없음: {path}')
    return inside(path, repo)


def figure_paths(p) -> list[Path]:
    out = []
    for fig_id, crop in problem_figures(p):
        if p.is_exam:
            if crop is not None:
                raise ExplainError(f'기출 그림 {fig_id}에는 crop을 쓸 수 없음')
            name = exam_figure_filename(fig_id)
            redrawn = p.figures_dir / 'redrawn' / name
            out.append(redrawn if redrawn.is_file() else p.figures_dir / name)
        else:
            out.append(p.figures_dir / textbook_figure_filename(fig_id, crop))
    return out


def subparts(ask_html: str) -> tuple[str, ...]:
    root = parse(ask_html)
    items = []
    for lst in root.children:
        if not isinstance(lst, str) and lst.tag in ('ul', 'ol'):
            items += [n for n in lst.children if not isinstance(n, str) and n.tag == 'li']
    labels = [m[1] for n in items if (m := LABEL_RE.match(n.text()))]
    if not labels:
        return ('main',)
    if len(set(labels)) != len(labels):
        raise ExplainError('소문항 표지 중복: ' + ', '.join(labels))
    return tuple(labels)


def _entries(text: str) -> list[str]:
    ids = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        m = LINE_RE.match(line)
        if not m:
            raise ExplainError(f'problems.txt {n}행 형식 오류')
        ids.append(m[1])
    return ids


def _slug(folder: Path, range_: str) -> str:
    pattern = re.compile(rf'정리노트_{re.escape(range_)}_(.+)\.html')
    slugs = [m[1] for p in folder.iterdir() if (m := pattern.fullmatch(nfc(p.name)))]
    if len(slugs) != 1:
        raise ExplainError(f'정리노트_{range_}_*.html은 정확히 하나여야 합니다 ({len(slugs)}개)')
    return slugs[0]


def load_source(path: Path, repo: Path) -> SourcePack:
    repo = Path(repo).absolute()
    path = inside(Path(path), repo)
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise ExplainError(f'problems.txt 읽기 실패: {exc}') from exc
    ids = _entries(text)
    if not ids:
        raise ExplainError('problems.txt에 문항이 없습니다')
    if nfc(path.parent.name) != BUNDLE:
        raise ExplainError(f'problems.txt는 팩 폴더의 {BUNDLE}/ 안에 있어야 합니다: {path}')
    folder = path.parent.parent
    range_ = nfc(folder.name)
    slug = _slug(folder, range_)
    problems, mds, figs = [], [], []
    for i, pid in enumerate(ids, 1):
        try:
            md = md_path(repo, pid)
            p = load_problem(md)
            fields = html_fields(p)
            paths = figure_paths(p)
            for fig in paths:
                if not fig.is_file():
                    raise ExplainError(f'그림 파일 없음: {fig}')
                inside(fig, repo)
            sol = solution(p)
        except ExplainError as exc:
            raise ExplainError(f'문항 {pid}: {exc}') from exc
        except (ProblemError, OSError) as exc:
            raise ExplainError(f'문항 {pid}: {exc}') from exc
        rels = [quote(os.path.relpath(fig, folder).replace(os.sep, '/'), safe='/') for fig in paths]
        steps, answer = ((), '') if sol is None else (tuple(s['html'] for s in sol['steps']), sol['answer'])
        try:
            subs = subparts(fields['ask'])
        except ExplainError as exc:
            raise ExplainError(f'문항 {pid}: {exc}') from exc
        problems.append(Problem(
            id=f'p{i}', number=i, title=p.title, source=f"{p.id} · {p.meta['kind']} {p.meta['number']}",
            original_html=fields.get('original', ''), conditions_html=fields['conditions'],
            ask_html=fields['ask'],
            figures_html=tuple(f'<figure><img src="{rel}" alt="그림 {p.id}"></figure>' for rel in rels),
            reference_steps=steps, reference_answer=answer, subparts=subs))
        mds.append(md)
        figs += [f for f in paths if f not in figs]
    inputs = [path, *mds, *figs]
    digest = hashlib.sha256()
    for item in inputs:
        digest.update(sha256(item).encode())
    return SourcePack('review', range_, slug, path, digest.hexdigest(), tuple(problems),
                      tuple(str(item) for item in inputs))
