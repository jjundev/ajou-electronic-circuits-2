from epe_rerender import verified_references, reference_dependencies
from epe_review_policy import POLICY_VERSION
"""Gate publication on reviews, then reuse locks, backups and rollback."""
import json
import shutil
from pathlib import Path
from epe_contract import validate_fragment, validate_reviews, payload_hash
from epe_files import _install_locked, publication_lock
from epe_render import artifact_hashes, check_artifacts, dump, names
from epe_source import sha256, inside, load_source
from pack_paths import PackPaths
from epe_types import BUNDLE, ExplainError
from epe_shared import check_style
from epe_core import make_overlay


def _verified_mapping(pack, artifacts, fragments, reviews, destination, repo, *, candidate):
    view = pack.pack_paths
    if view and view.candidate_pack and not candidate:
        raise ExplainError('후보 원본으로 직접 발행할 수 없습니다')
    try:
        repo = Path(repo)
        check_style(repo, pack.learning_style)
        current = (load_source(pack.path, repo, pack_paths=view, slug=pack.slug) if view else
                   load_source(pack.path, repo))
        if candidate and not (view and view.candidate_pack):
            for name in ('display-titles.json', 'selection.json'):
                if str(pack.path.with_name(name)) not in current.inputs:
                    raise ExplainError(f'후보 승인 입력 누락: {name}')
        if current != pack:
            raise ExplainError('입력 변경: 설명을 다시 검증하세요')
        destination = Path(destination).absolute()
        output = PackPaths(repo, pack.folder, destination) if candidate else None
        if not candidate and destination != pack.folder.absolute():
            raise ExplainError('발행 위치는 입력 카드의 디렉터리여야 해요')
        errors = check_artifacts(pack, artifacts) + validate_reviews(pack, fragments, reviews)
        errors += [e for p in pack.problems for e in validate_fragment(p, fragments.get(p.id, ''))]
        if errors:
            raise ExplainError('발행 보류: ' + ' / '.join(errors))
        manifest = json.loads(artifacts.manifest.read_text(encoding='utf-8'))
        if manifest.get('review_policy_version') != POLICY_VERSION:
            raise ExplainError('발행 보류: manifest 검토 기준 불일치')
        if manifest['input_hash'] != payload_hash(pack, fragments):
            raise ExplainError('stage와 현재 조각 불일치')
        if not isinstance(reviews.get('artifact_hashes'), dict) or reviews['artifact_hashes'] != artifact_hashes(artifacts):
            raise ExplainError('검토 후 생성 파일 변경: 다시 화면·내용을 검토하세요')
        references = reviews.get('references')
        if not isinstance(references, list):
            raise ExplainError('참조 자료 hash 목록 필요')
        style_path = inside(repo / pack.learning_style['path'], repo)
        if not any(isinstance(ref, dict) and isinstance(ref.get('path'), str)
                   and Path(ref['path']).resolve() == style_path.resolve()
                   and ref.get('sha256') == pack.learning_style['sha256'] for ref in references):
            raise ExplainError('개인 명세 참조 hash 누락/불일치')
        recorded = {}
        for reference in references:
            if output and output != view:
                # The output attempt can also live under repo. Its physical names cannot be published.
                output.source_file(reference['path'])
            path = view.source_file(reference['path']) if view else inside(Path(reference['path']), repo)
            if not path.is_file() or sha256(path) != reference['sha256']:
                raise ExplainError('참조 자료 변경: ' + str(path))
            recorded[path.resolve()] = reference['sha256']
        if view:
            for path in recorded:
                for dep in reference_dependencies(path, repo, pack_paths=view):
                    if recorded.get(dep.resolve()) != sha256(dep):
                        raise ExplainError('참조 그림 hash 누락/변경')
        elif not verified_references(references,repo,repo)[1]:
            raise ExplainError('발행 보류: 참조 그림을 포함한 모든 참조 hash 필요')
        overlay = json.loads((artifacts.html.parent / manifest['answer_overlay']).read_text(encoding='utf-8'))
        if overlay != make_overlay(pack, artifacts.html, repo):
            raise ExplainError('답안 overlay와 최종 stage/입력 불일치')
        stage_root = artifacts.html.parent.resolve()
        stem, fig_name, data_name = names(pack)
        allowed_roots = {fig_name, data_name}
        protected = {(view.source_file(item) if view else Path(item)).resolve() for item in pack.inputs}
        mapping = {}
        for src in artifacts.files:
            src = Path(src).absolute()
            inside(src, stage_root)
            relative = src.relative_to(stage_root)
            parts = relative.parts
            owned = parts == (stem + '.html',) or parts == (BUNDLE, stem + '.md') \
                or (len(parts) > 2 and parts[0] == BUNDLE and parts[1] in allowed_roots)
            if not owned or relative.name == 'validation.json':
                raise ExplainError('소유하지 않은 산출 경로: ' + str(relative))
            dst = output.work_file(str(relative)) if output else inside(destination / relative, repo)
            if dst.resolve() in protected:
                raise ExplainError('원본 덮어쓰기 금지')
            mapping[dst] = src
        # Report is deliberately outside the reviewed hash set (avoids self-hashing).
        report = stage_root / BUNDLE / data_name / 'validation.json'
        if not candidate:
            dump(report, reviews)
        report_dst = (output.work_file(str(report.relative_to(stage_root))) if output else
                      inside(destination / report.relative_to(stage_root), repo))
        if report_dst.resolve() in protected:
            raise ExplainError('원본 덮어쓰기 금지')
        mapping[report_dst] = None if candidate else report
        return mapping
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, ExplainError):
            raise
        raise ExplainError(str(exc)) from exc


def publish_explanation(pack, artifacts, fragments, reviews, destination, backup_dir, repo):
    try:
        with publication_lock([pack.folder / artifacts.html.name]):
            mapping = _verified_mapping(pack, artifacts, fragments, reviews, destination, repo, candidate=False)
            _install_locked(mapping, Path(backup_dir))
    except OSError as exc:
        raise ExplainError(str(exc)) from exc
    return tuple(mapping)


def build_explanation_candidate(pack, artifacts, fragments, reviews, destination, repo) -> list[Path]:
    mapping = _verified_mapping(pack, artifacts, fragments, reviews, destination, repo, candidate=True)
    if any(dst.exists() for dst in mapping):
        raise ExplainError('후보 설명 산출 파일 중복')
    for dst, src in mapping.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open('xb') as out:
            if src is None:
                out.write((json.dumps(reviews, ensure_ascii=False, indent=2) + '\n').encode())
            else:
                with src.open('rb') as incoming:
                    shutil.copyfileobj(incoming, out)
    return list(mapping)
