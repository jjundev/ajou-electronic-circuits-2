"""Select and stage one independently verified optional circuit experiment."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil

from epe_contract import payload_hash
from epe_shared import parse
from epe_source import sha256

CANDIDATES = 'lab-candidates.json'
FILES = ('brief.json', 'lab.js', 'index.html', 'lab-validation.json')
GATES = ('machine', 'numeric_independent', 'probe', 'browser')
SECTIONS = ('start', 'solve', 'retry')
TEXT_FIELDS = ('decision', 'action', 'observation', 'return_to', 'label')


@dataclass(frozen=True)
class Lab:
    directory: Path
    problem_id: str
    workbook_id: str
    section: str
    subpart: str
    decision: str
    label: str

    def copy_to(self, directory):
        directory.mkdir(parents=True)
        for name in FILES:
            shutil.copyfile(self.directory / name, directory / name)


def find_section(root, section):
    return next(root.find_all(lambda node: node.attrs.get('data-explanation') == section), None)


def _read(path):
    if path.is_symlink():
        raise ValueError(f'심볼릭 링크: {path.name}')
    return json.loads(path.read_text(encoding='utf-8'))


def _matches(candidate, problem, fragments, *, allow_legacy=False):
    workbook_id = candidate.get('workbook_id')
    section = candidate.get('section')
    subpart = candidate.get('subpart')
    sections = SECTIONS if allow_legacy else ('solve',)
    return (isinstance(workbook_id, str) and workbook_id == problem.workbook_id
            and re.fullmatch(r'[\w][\w.-]*', workbook_id)
            and section in sections and subpart in problem.subparts
            and all(isinstance(candidate.get(key), str) and candidate[key].strip() for key in TEXT_FIELDS)
            and find_section(parse(fragments[problem.id]), section) is not None)


def select_lab(bucket, pack, fragments):
    """Choose from educational proposals. No acceptable proposal means no lab."""
    brief = bucket / 'lab' / 'brief.json'
    try:
        candidates = _read(bucket / CANDIDATES)
        if not isinstance(candidates, list):
            raise ValueError('후보는 JSON 배열이어야 해요')
    except FileNotFoundError:
        candidates = []
    except (OSError, ValueError) as exc:
        print(f'{pack.range}: 실험 후보 보류 ({exc})')
        candidates = []

    selected = next((item for problem in sorted(pack.problems, key=lambda p: p.number)
                     for item in candidates
                     if isinstance(item, dict) and _matches(item, problem, fragments)), None)
    if selected is not None:
        keys = ('workbook_id', 'section', 'subpart', *TEXT_FIELDS)
        selected = {**{key: selected[key] for key in keys}, 'schema_version': 1, 'range': pack.range,
                    'input_hash': payload_hash(pack, fragments)}
    if brief.parent.is_symlink() or brief.is_symlink():
        raise ValueError('실험 브리프 경로에 심볼릭 링크가 있어요')
    if selected is not None or brief.exists():
        brief.parent.mkdir(exist_ok=True)
        brief.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return selected


def load_lab(bucket, pack, fragments, *, allow_legacy=False):
    """Return a current lab and a diagnostic for an optional failed experiment."""
    directory = bucket / 'lab'
    brief_path = directory / FILES[0]
    try:
        if directory.is_symlink():
            raise ValueError('실험 폴더에 심볼릭 링크가 있어요')
        if not brief_path.exists() and not brief_path.is_symlink():
            return None, None

        brief = _read(brief_path)
        if brief is None:
            return None, None
        if (not isinstance(brief, dict) or brief.get('schema_version') != 1
                or brief.get('range') != pack.range or brief.get('input_hash') != payload_hash(pack, fragments)):
            raise ValueError('실험 브리프와 현재 해설 입력이 달라요')
        problem = next((p for p in pack.problems if _matches(brief, p, fragments, allow_legacy=allow_legacy)), None)
        if problem is None:
            raise ValueError('실험에 맞는 문항이나 해설 구역이 없어요')

        verify_lab(directory)
        return Lab(directory, problem.id, problem.workbook_id, brief['section'], brief['subpart'],
                   brief['decision'], brief['label']), None
    except (OSError, ValueError) as exc:
        return None, str(exc)


def verify_lab(directory):
    """Validate the lab files again after copying into the reviewed stage."""
    if directory.is_symlink():
        raise ValueError('실험 폴더에 심볼릭 링크가 있어요')
    for name in FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'실험 파일 누락 또는 부적합: {name}')
    review = _read(directory / FILES[-1])
    if not isinstance(review, dict):
        raise ValueError('실험 검증 기록이 올바르지 않아요')
    gates = review.get('gates')
    if not isinstance(gates, dict) or any(gates.get(key) != 'pass' for key in GATES):
        raise ValueError('실험 검증 4개가 모두 통과해야 해요')
    if any(review.get(key) != sha256(directory / name) for key, name in
           zip(('brief_sha256', 'source_sha256', 'html_sha256'), FILES[:3])):
        raise ValueError('검증 이후 실험 파일이 바뀌었어요')
    return _read(directory / FILES[0])
