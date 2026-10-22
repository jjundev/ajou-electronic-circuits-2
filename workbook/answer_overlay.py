"""Consume only intact, currently reviewed EPE answer bundles; never rewrite answers."""
from base64 import b64encode
from copy import deepcopy
import html
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


# Workbook modules are already loaded first. EPE's adapter appends review-pack
# helpers, whose assemble.py must never shadow workbook/assemble.py.
_EPE = Path(__file__).resolve().parents[1] / '.claude/skills/ec2-problem-explain/scripts'
if str(_EPE) not in sys.path:
    sys.path.append(str(_EPE))
from epe_contract import validate_review_records  # noqa: E402
from epe_core import make_overlay  # noqa: E402
from epe_render import names  # noqa: E402
from epe_rerender import reference_dependencies  # noqa: E402
from epe_shared import parse, inner, Node  # noqa: E402
from epe_source import existing_path, inside, load_source, sha256  # noqa: E402
from learning_style import PERSONALIZED_REVIEW_POLICY  # noqa: E402


class AnswerOverlayError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise AnswerOverlayError(message)


def _json(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    _require(isinstance(value, dict), f'JSON 객체 필요: {path}')
    return value


def _relative_file(root, name):
    _require(isinstance(name, str) and bool(name), '상대 파일 경로 필요')
    path = Path(name)
    _require(not path.is_absolute(), f'절대 산출 경로 금지: {name}')
    return inside(existing_path(root / path), root)


def _hash_files(root, mapping):
    _require(isinstance(mapping, dict) and bool(mapping), '파일 hash 목록 필요')
    actual = {}
    for name, digest in mapping.items():
        _require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest), 'sha256 형식 오류')
        file = _relative_file(root, name)
        _require(file.is_file() and sha256(file) == digest, f'파일 변경/누락: {name}')
        _require(not any(file.samefile(other) for other in actual), f'중복 파일 경로: {name}')
        actual[file.resolve()] = digest
    return actual


def _check_core_resources(problems):
    # Only <img src> participates in the overlay asset map. Inline SVG may use
    # its own local definitions, but must not fetch an unreviewed second file.
    for problem in problems:
        for item in (*problem['steps'], *problem['answers']):
            for node in parse(item['html']).find_all(lambda n: True):
                _require('srcset' not in node.attrs, '검증되지 않은 srcset 그림 금지')
                for key, value in node.attrs.items():
                    if key == 'src':
                        _require(node.tag == 'img', '검증되지 않은 자원 src 금지')
                    if key in ('href', 'xlink:href') and node.tag != 'a':
                        _require(value.startswith('#'), 'SVG 자원은 내부 정의만 참조할 수 있어요')
                    for target in re.findall(r'url\((.*?)\)', value, re.I):
                        _require(target.strip().strip('\"\'').startswith('#'), 'SVG 외부 자원 금지')


def load_answer_overlay(path: Path, repo: Path, expected_ids: list[str]) -> dict:
    """Validate disk schema, reviews, all hashes and current source/route identity.

    Review records attest to human/agent checks; this validates their format and
    binding, and does not itself establish mathematical or semantic correctness.
    """
    try:
        repo = existing_path(Path(repo)).resolve()
        path = inside(existing_path(Path(path)), repo)
        overlay = _json(path)
        _require(type(overlay.get('schema_version')) is int and overlay['schema_version'] == 1,
                 '지원하지 않는 overlay schema_version')
        _require(overlay.get('review_policy_version') == PERSONALIZED_REVIEW_POLICY, '현재 검토 기준 필요')
        _require(path.name == 'answer-overlay.json' and path.parent.parent.name == '.assets', '발행 자료 폴더 경로 필요')
        stage = path.parent.parent.parent.resolve()
        manifest_path = inside(path.parent / 'manifest.json', stage)
        manifest = _json(manifest_path)
        validation_path = inside(path.parent / 'validation.json', stage)
        validation = _json(validation_path)
        _require(type(manifest.get('version')) is int and manifest['version'] == 1, '지원하지 않는 manifest version')
        _require(manifest.get('review_policy_version') == PERSONALIZED_REVIEW_POLICY, 'manifest 검토 기준 불일치')
        _require(isinstance(overlay.get('input_hash'), str) and re.fullmatch(r'[0-9a-f]{64}', overlay['input_hash']), 'input_hash 형식 오류')
        for key in ('range', 'slug', 'input_hash', 'learning_style'):
            _require(manifest.get(key) == overlay.get(key), f'manifest {key} 불일치')
        _require(manifest.get('answer_overlay') == path.relative_to(stage).as_posix(), 'manifest overlay 경로 불일치')
        files = manifest.get('files')
        reviewed_files = _hash_files(stage, files)
        expected_artifacts = {**files, manifest_path.relative_to(stage).as_posix(): sha256(manifest_path)}
        _require(validation.get('artifact_hashes') == expected_artifacts, '검토 산출 파일 hash 집합 불일치')
        _hash_files(stage, validation['artifact_hashes'])
        _require(path.relative_to(stage).as_posix() in files, 'overlay 파일 hash 누락')
        _require(manifest_path.relative_to(stage).as_posix() not in files
                 and validation_path.relative_to(stage).as_posix() not in files, 'manifest/validation 자기 hash 금지')

        source = Path(manifest['source'])
        if not source.is_absolute():
            source = repo / source
        pack = load_source(inside(existing_path(source), repo), repo)
        _require(pack.learning_style == overlay['learning_style'], '개인 명세 변경: 다시 검토 필요')
        _require(manifest.get('source_sha256') == pack.sha256, '현재 원문 hash 불일치')
        _require(manifest.get('inputs') == list(pack.inputs), '현재 입력 집합 불일치')
        _require((pack.range, pack.slug) == (overlay['range'], overlay['slug']), '팩 range/slug 불일치')
        _require(pack.folder.resolve() == stage, '발행 폴더와 원문 팩 불일치')
        problems = overlay['problems']
        _require(isinstance(problems, list) and bool(problems), 'overlay 문항 목록 필요')
        ids = [p['id'] for p in problems]
        _require(ids == expected_ids and len(set(ids)) == len(ids), '정확한 문항 ID 순서 필요')
        _require(ids == [p.workbook_id for p in pack.problems], '현재 원문 문항 ID 불일치')
        _require(manifest.get('problems') == [{'id': p.id, 'subparts': list(p.subparts)} for p in pack.problems], 'manifest 소문항 불일치')
        items = [f'{p.id}:{s}' for p in pack.problems for s in p.subparts]
        errors = validate_review_records(pack.learning_style, items, validation, input_hash=overlay['input_hash'])
        _require(not errors, ' / '.join(errors))

        source_inputs = overlay['source_inputs']
        _hash_files(repo, source_inputs)
        references = validation['references']
        _require(isinstance(references, list) and bool(references), '참조 자료 hash 필요')
        recorded = {}
        for reference in references:
            ref = Path(reference['path'])
            ref = inside(existing_path(ref if ref.is_absolute() else repo / ref), repo)
            _require(ref.is_file() and sha256(ref) == reference['sha256'], f'참조 자료 변경: {ref}')
            recorded[ref.resolve()] = reference['sha256']
        style = (repo / pack.learning_style['path']).resolve()
        _require(recorded.get(style) == pack.learning_style['sha256'], '개인 명세 참조 hash 누락')
        for ref in recorded:
            for dependency in reference_dependencies(ref, repo):
                _require(recorded.get(dependency.resolve()) == sha256(dependency), '참조 그림 hash 누락/변경')

        stem, _, data_name = names(pack)
        _require(path.parent.name == data_name, '발행 자료 폴더 이름 불일치')
        html_path = _relative_file(stage, stem + '.html')
        _require(stem + '.html' in files, '발행 HTML hash 누락')
        _require(overlay == make_overlay(pack, html_path, repo), 'overlay와 현재 원문/최종 DOM 불일치')
        _check_core_resources(problems)
        asset_data = {}
        _require(isinstance(overlay['assets'], dict), 'assets hash 객체 필요')
        for name, digest in overlay['assets'].items():
            url = urlsplit(name)
            _require(not url.scheme and not url.netloc and bool(url.path) and not url.query and not url.fragment,
                     f'그림은 stage 상대 경로여야 해요: {name}')
            file = _relative_file(stage, unquote(url.path))
            data = file.read_bytes()
            _require(hashlib.sha256(data).hexdigest() == digest, f'그림 변경: {name}')
            _require(any(file.samefile(reviewed) and value == digest for reviewed, value in reviewed_files.items()), '그림의 발행 hash 누락')
            mime = mimetypes.guess_type(file.name)[0]
            _require(mime is not None and mime.startswith('image/'), '그림 파일 형식 필요')
            asset_data[name] = f'data:{mime};base64,' + b64encode(data).decode('ascii')
        return {**overlay, '_asset_data': asset_data}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        if isinstance(exc, AnswerOverlayError):
            raise
        raise AnswerOverlayError(f'답안 overlay 검증 실패: {exc}') from exc


def _answer_html(markup, asset_data):
    root = parse(markup)
    for node in list(root.find_all(lambda n: True)):
        if node.tag == 'img':
            src = node.attrs.get('src', '')
            _require(src in asset_data, f'검증되지 않은 그림: {src}')
            node.attrs['src'] = asset_data[src]
        elif node.tag == 'a':
            # Preserve visible text/children while dropping the interactive link.
            parent = node.parent
            index = parent.children.index(node)
            parent.children[index:index+1] = node.children
            for child in node.children:
                if isinstance(child, Node):
                    child.parent = parent
    return inner(root)


def apply_answer_overlay(data: dict, overlay: dict, *, html_dir: Path) -> dict:
    """Copy workbook data and replace solutions only, with self-contained images."""
    result = deepcopy(data)
    _require([p['id'] for p in result['problems']] == [p['id'] for p in overlay['problems']], '답안 데이터 문항 순서 불일치')
    assets = overlay['_asset_data']
    for problem, core in zip(result['problems'], overlay['problems']):
        steps, answers = [], []
        for subpart in core['subparts']:
            prefix = '' if subpart == 'main' else f'({subpart}) '
            for step in core['steps']:
                if step['subpart'] == subpart:
                    steps.append({'label': html.escape(prefix + step['label']), 'html': _answer_html(step['html'], assets)})
            for answer in core['answers']:
                if answer['subpart'] == subpart:
                    body = _answer_html(answer['html'], assets)
                    answers.append((f'<p><strong>{html.escape(prefix.strip())}</strong></p>' if prefix else '') + body)
        problem['solution'] = {'steps': steps, 'answer': ''.join(answers), 'paginate': True}
    return result
