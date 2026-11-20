"""Extract → agent-authored fragments → build/check → reviewed publication."""
import argparse
from dataclasses import asdict
import json
import re
from pathlib import Path
import shutil
import sys
import uuid
from epe_contract import initial_reviews, payload_hash, validate_fragment
from epe_source import inside, load_source, resolve_sources, sha256
from epe_render import build_explanation, check_artifacts, artifact_hashes, dump
from epe_publish import build_explanation_candidate, publish_explanation
from epe_shared import REPO
from pack_paths import PackPaths
from epe_types import Artifacts, ExplainError

def serialized(pack):
    value = asdict(pack)
    value.pop('pack_paths')
    value['path'] = str(pack.path)
    # JSON normalizes tuples to lists; compare canonical serialization on import.
    return json.loads(json.dumps(value, ensure_ascii=False))

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def extract(repo, target, run, *, pack_paths=None, slug=None):
    repo = pack_paths.repo if pack_paths else Path(repo).resolve()
    run = Path(run).absolute()
    if run.exists() and (run.is_symlink() or not run.is_dir() or any(run.iterdir())):
        raise ExplainError('RUN은 비어 있어야 해요')
    if pack_paths:
        if not slug or target != pack_paths.public_pack.name:
            raise ExplainError('후보 팩 날짜와 승인된 slug 필요')
        sources = (pack_paths.work_file('.assets/problems.txt'),)
    else:
        sources = resolve_sources(repo, target)
    run.mkdir(parents=True, exist_ok=True)
    buckets = []
    failed = False
    for source in sources:
        try:
            pack = load_source(source, repo, pack_paths=pack_paths, slug=slug)
            name = f'review-{pack.range}-{pack.slug}'
            folder = run / name
            folder.mkdir()
            (folder / 'explanations').mkdir()
            (folder / 'evidence').mkdir()
            dump(folder / 'source.json', serialized(pack))
            for problem in pack.problems:
                if getattr(problem,'choice',None) is None and re.search(r'class=[\"\'][^\"\']*\bchoices\b',problem.conditions_html+problem.ask_html):
                    print(f'{problem.id}: 보기 모델 없음/불일치 — 정적 표시',file=sys.stderr)
            buckets.append(name)
            print('extract:', folder / 'source.json')
        except ExplainError as exc:
            failed = True
            print(f'{source}: {exc}', file=sys.stderr)
    index = {'version': 1, 'repo': str(repo), 'targets': buckets}
    if pack_paths:
        index.update(public_pack=str(pack_paths.public_pack), candidate_pack=str(pack_paths.work_pack), slug=slug,
                     private_roots=[str(path) for path in pack_paths.private_roots])
    dump(run / 'run.json', index)
    return int(failed)

def load_run(run, errors=None, *, pack_paths=None):
    run = Path(run).absolute()
    index = read_json(inside(run / 'run.json', run))
    repo = Path(index['repo'])
    if not repo.is_absolute() or not repo.is_dir():
        raise ExplainError('저장소 절대 경로 필요')
    if 'candidate_pack' in index:
        stored = PackPaths(repo, Path(index['public_pack']), Path(index['candidate_pack']))
        if pack_paths and stored.public_pack != pack_paths.public_pack:
            raise ExplainError('후보 팩 입력 경로 불일치')
        # Reviews must survive deletion of the child RUN and the original producer,
        # even when the bound source bytes now come from an adopted consumer.
        pack_paths = (pack_paths or stored).excluding(
            stored.work_pack, run, *(Path(p) for p in index.get('private_roots', ())))
    items = []
    if not isinstance(index['targets'], list) or not index['targets']:
        raise ExplainError('추출 대상 없음')
    for name in index['targets']:
        try:
            folder = inside(run / name, run)
            value = read_json(inside(folder / 'source.json', run))
            source = Path(value['path'])
            if not source.is_absolute():
                raise ExplainError('추출 입력은 절대 경로여야 해요')
            pack = load_source(inside(source, repo), repo, pack_paths=pack_paths, slug=index.get('slug'))
            if value != serialized(pack):
                raise ExplainError('추출 데이터 또는 원본 변경: extract부터 다시 실행하세요')
            items.append({'pack': pack, 'folder': folder, 'repo': repo, 'run': run})
        except (ExplainError, OSError, ValueError, KeyError, TypeError) as exc:
            if errors is None:
                raise
            errors.append(f'{name}: {exc}')
    return items

def load_fragments(item):
    folder = item['folder']
    actual = {p.stem for p in (folder / 'explanations').glob('*.html')}
    if actual != {p.id for p in item['pack'].problems}:
        raise ExplainError('모든 문항의 explanations/pN.html을 먼저 저작하세요')
    return {p.id: inside(folder / 'explanations' / f'{p.id}.html', item['run']).read_text(encoding='utf-8') for p in item['pack'].problems}

def load_artifacts(item):
    value = read_json(inside(item['folder'] / 'stage.json', item['run']))
    stage = inside(item['folder'] / value['stage'], item['run'])
    paths = [inside(stage / value[key], stage) for key in ('html', 'md', 'manifest')]
    manifest = read_json(paths[2])
    files = tuple(inside(stage / name, stage) for name in manifest['files']) + (paths[2],)
    return Artifacts(*paths, files)

def build(item, fragments):
    folder = item['folder']
    stage = folder / 'stage' / uuid.uuid4().hex
    artifacts = build_explanation(item['pack'], fragments, stage, item['repo'])
    # Evidence is copied before binding the artifact hashes; review approval comes later.
    evidence = inside(folder / 'evidence', item['run'])
    if evidence.is_dir():
        for source in evidence.rglob('*'):
            inside(source, item['run'])
            if source.is_file():
                dest = artifacts.manifest.parent / 'evidence' / source.relative_to(evidence)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
    manifest = read_json(artifacts.manifest)
    files = tuple(sorted(p for p in stage.rglob('*') if p.is_file() and p != artifacts.manifest))
    manifest['files'] = {p.relative_to(stage).as_posix(): sha256(p) for p in files}
    dump(artifacts.manifest, manifest)
    artifacts = Artifacts(artifacts.html, artifacts.md, artifacts.manifest, files + (artifacts.manifest,))
    dump(folder / 'stage.json', {'stage': stage.relative_to(folder).as_posix(),
                               'html': artifacts.html.name, 'md': artifacts.md.relative_to(stage).as_posix(),
                               'manifest': artifacts.manifest.relative_to(stage).as_posix()})
    review = initial_reviews(item['pack'], fragments)
    review['artifact_hashes'] = artifact_hashes(artifacts)
    dump(folder / 'review.json', review)
    print('build:', artifacts.html)

def rerender(repo,target,run):
    from epe_rerender import rerender as rebuild
    return rebuild(repo,target,run)

def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    extraction = commands.add_parser('extract')
    extraction.add_argument('--repo', type=Path, default=REPO)
    extraction.add_argument('--target')
    extraction.add_argument('--public-pack', type=Path)
    extraction.add_argument('--candidate-pack', type=Path)
    extraction.add_argument('--slug')
    extraction.add_argument('--run', type=Path, required=True)
    rendering = commands.add_parser('rerender')
    rendering.add_argument('--repo',type=Path,required=True)
    rendering.add_argument('--target',required=True)
    rendering.add_argument('--run',type=Path,required=True)
    for name in ('build', 'check', 'publish'):
        command = commands.add_parser(name)
        command.add_argument('--run', type=Path, required=True)
        if name == 'publish':
            command.add_argument('--repo', type=Path, default=REPO)
            command.add_argument('--public-pack', type=Path)
            command.add_argument('--candidate-pack', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'rerender':
            return rerender(args.repo,args.target,args.run)
        if args.command == 'extract':
            if bool(args.public_pack) != bool(args.candidate_pack) or bool(args.slug) != bool(args.public_pack):
                raise ExplainError('--candidate-pack, --public-pack, --slug must be supplied together')
            view = PackPaths(args.repo, args.public_pack, args.candidate_pack) if args.public_pack else None
            return extract(args.repo, args.target, args.run, pack_paths=view, slug=args.slug)
        load_errors = []
        view = None
        if args.command == 'publish' and (args.public_pack or args.candidate_pack):
            if not (args.public_pack and args.candidate_pack):
                raise ExplainError('--public-pack and --candidate-pack must be paired')
            view = PackPaths(args.repo, args.public_pack, args.candidate_pack)
        items = load_run(args.run, errors=load_errors, pack_paths=view)
        failed = bool(load_errors)
        for error in load_errors:
            print(error, file=sys.stderr)
        for item in items:
            try:
                fragments = load_fragments(item)
                if args.command == 'build':
                    build(item, fragments)
                else:
                    artifacts = load_artifacts(item)
                    if args.command == 'check':
                        errors = check_artifacts(item['pack'], artifacts)
                        errors += [e for p in item['pack'].problems for e in validate_fragment(p, fragments[p.id])]
                        if read_json(artifacts.manifest).get('input_hash') != payload_hash(item['pack'], fragments):
                            errors.append('설명 조각 변경: build부터 다시 실행하세요')
                        dump(item['folder'] / 'machine.json', {'status': 'fail' if errors else 'pass', 'errors': errors,
                                                              'artifact_hashes': artifact_hashes(artifacts)})
                        if errors:
                            raise ExplainError(' / '.join(errors))
                        print('check: machine PASS (수학·화면 검토는 별도)', artifacts.html)
                    else:
                        review = read_json(inside(item['folder'] / 'review.json', item['run']))
                        if view:
                            outputs = build_explanation_candidate(item['pack'], artifacts, fragments, review,
                                                                  view.work_pack, item['repo'])
                            print(json.dumps([str(p) for p in outputs], ensure_ascii=False))
                            continue
                        published = publish_explanation(item['pack'], artifacts, fragments, review,
                                                        item['pack'].folder, item['folder'] / 'backups',
                                                        item['repo'])
                        print('publish:', published[0], 'backup:', item['folder'] / 'backups')
            except (ExplainError, OSError, ValueError, KeyError, TypeError) as exc:
                failed = True
                print(f'{item["folder"].name}: {exc}', file=sys.stderr)
        return int(failed)
    except (ExplainError, OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
