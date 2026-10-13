"""Gate publication on reviews, then reuse locks, backups and rollback."""
import json
from pathlib import Path
from epe_contract import validate_fragment, validate_reviews, payload_hash
from epe_files import publish_files
from epe_render import artifact_hashes, check_artifacts, dump, names
from epe_source import sha256, inside, load_source
from epe_types import BUNDLE, ExplainError


def publish_explanation(pack, artifacts, fragments, reviews, destination, backup_dir, repo):
    try:
        repo = Path(repo)
        if load_source(pack.path, repo) != pack:
            raise ExplainError('입력 변경: 설명을 다시 검증하세요')
        destination = Path(destination).absolute()
        if destination != pack.folder.absolute():
            raise ExplainError('발행 위치는 입력 카드의 디렉터리여야 해요')
        errors = check_artifacts(pack, artifacts) + validate_reviews(pack, fragments, reviews)
        errors += [e for p in pack.problems for e in validate_fragment(p, fragments.get(p.id, ''))]
        if errors:
            raise ExplainError('발행 보류: ' + ' / '.join(errors))
        manifest = json.loads(artifacts.manifest.read_text(encoding='utf-8'))
        if manifest['input_hash'] != payload_hash(pack, fragments):
            raise ExplainError('stage와 현재 조각 불일치')
        if not isinstance(reviews.get('artifact_hashes'), dict) or reviews['artifact_hashes'] != artifact_hashes(artifacts):
            raise ExplainError('검토 후 생성 파일 변경: 다시 화면·내용을 검토하세요')
        references = reviews.get('references')
        if not isinstance(references, list):
            raise ExplainError('참조 자료 hash 목록 필요')
        for reference in references:
            path = inside(Path(reference['path']), repo)
            if not path.is_file() or sha256(path) != reference['sha256']:
                raise ExplainError('참조 자료 변경: ' + str(path))
        stage_root = artifacts.html.parent.resolve()
        stem, fig_name, data_name = names(pack)
        allowed_roots = {fig_name, data_name}
        protected = {Path(item).resolve() for item in pack.inputs}
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
            dst = inside(destination / relative, repo)
            if dst.resolve() in protected:
                raise ExplainError('원본 덮어쓰기 금지')
            mapping[dst] = src
        # Report is deliberately outside the reviewed hash set (avoids self-hashing).
        report = stage_root / BUNDLE / data_name / 'validation.json'
        dump(report, reviews)
        report_dst = inside(destination / report.relative_to(stage_root), repo)
        if report_dst.resolve() in protected:
            raise ExplainError('원본 덮어쓰기 금지')
        mapping[report_dst] = report
        publish_files(mapping, Path(backup_dir))
        return tuple(mapping)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, ExplainError):
            raise
        raise ExplainError(str(exc)) from exc
