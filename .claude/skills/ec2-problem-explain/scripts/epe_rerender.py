"""Rebuild a fresh stage from verified published fragments; never publish here."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from epe_source import inside, sha256, existing_path
from epe_shared import parse, STYLE_PATH
from epe_types import ExplainError
from epe_review_policy import carry_reviews, POLICY_VERSION

CODE_RE = re.compile(r'<style\b[^>]*>.*?</style>|<script\b(?![^>]*application/json)[^>]*>.*?</script>',re.S|re.I)

def git_blob(path, digest):
    try:
        commits = subprocess.run(['git','log','--format=%H','--',path.name],cwd=path.parent,capture_output=True,check=True).stdout.decode().split()
        for commit in commits:
            p = subprocess.run(['git','show',f'{commit}:./{path.name}'],cwd=path.parent,capture_output=True)
            if p.returncode:
                continue
            # Windows checkouts may have CRLF although the committed blob uses LF.
            for data in (p.stdout, p.stdout.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')):
                if hashlib.sha256(data).hexdigest() == digest:
                    return data
    except (OSError,subprocess.CalledProcessError):
        pass
    return None

def relocated(path, repo):
    path = inside(path,repo)
    if path.is_file():
        return path
    try:
        normalized=inside(existing_path(path),repo)
        if normalized.is_file():
            return normalized
    except (ExplainError,OSError):
        pass
    candidates = []
    for parent in path.parents:
        if re.fullmatch(r'\d{4}(?:-\d{4})?',parent.name):
            candidates = [parent/side/path.relative_to(parent) for side in ('.pack','.assets')]
            break
    found = [inside(p,repo) for p in candidates if p.is_file()]
    return found[0] if len(found) == 1 else path

def equivalent_text(old, current, old_path, new_path, repo):
    """Accept CSS/code-only changes; resolve URL relocations to verified actual files."""
    decode = lambda data: CODE_RE.sub('',data.decode('utf-8'))
    a,b = decode(old),decode(current)
    if a == b:
        return True
    pattern = re.compile(r'''\b(src|href)=(['"])(.*?)\2''',re.I)
    old_urls,new_urls = list(pattern.finditer(a)),list(pattern.finditer(b))
    if len(old_urls) != len(new_urls):
        return False
    for left,right in zip(old_urls,new_urls):
        if left.group() == right.group():
            continue
        u,v = urlsplit(left[3]),urlsplit(right[3])
        if (left[1] != right[1] or u.scheme or u.netloc or v.scheme or v.netloc
            or not u.path or not v.path or u.query != v.query or u.fragment != v.fragment):
            return False
        p,q = inside(old_path.parent/unquote(u.path),repo),inside(new_path.parent/unquote(v.path),repo)
        if not p.is_file() or not q.is_file() or sha256(p) != sha256(q):
            return False
    return pattern.sub('URL',a) == pattern.sub('URL',b)

def verified_resources(stored, current, repo):
    if not isinstance(stored,dict):
        return False
    mapped={}
    for name,digest in stored.items():
        path=relocated(repo/name,repo)
        if not path.is_file() or sha256(path)!=digest:
            return False
        mapped[inside(path.resolve(), repo).relative_to(repo).as_posix()]=digest
    canonical = {inside((repo / name).resolve(), repo).relative_to(repo).as_posix(): digest
                 for name, digest in current.items()}
    return mapped == canonical

def reference_dependencies(path,repo, *, pack_paths=None):
    if path.suffix.lower() not in ('.html','.md','.svg'):
        return []
    text=path.read_text(encoding='utf-8')
    urls=[]
    if path.suffix.lower()=='.md':
        urls=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
    else:
        for node in parse(text).find_all(lambda n:n.tag in ('img','image')):
            urls.append(node.attrs.get('src',node.attrs.get('href',node.attrs.get('xlink:href',''))))
    result=[]
    for value in urls:
        url=urlsplit(value)
        if url.scheme or url.netloc or not url.path:
            raise ExplainError('참조 그림의 로컬 hash 확인 필요')
        target = (pack_paths.link(path.parent, unquote(url.path)) if pack_paths else
                  inside(existing_path(path.parent/unquote(url.path)),repo))
        result.append(target)
    return result

def verified_references(references, old_repo, repo):
    if not isinstance(references,list):
        return [],False
    carried=[]
    for ref in references:
        if not isinstance(ref,dict) or not isinstance(ref.get('path'),str) or not isinstance(ref.get('sha256'),str):
            return [],False
        path=Path(ref['path'])
        if path.is_relative_to(old_repo):
            path=repo/path.relative_to(old_repo)
        current=relocated(path,repo)
        if not current.is_file():
            print('rerender: 참조 자료 없음: 검토를 다시 하세요: '+path.name)
            return carried,False
        digest=sha256(current)
        if digest != ref['sha256']:
            if current.resolve() == (repo / STYLE_PATH).resolve():
                print('rerender: 개인 명세 바이트 변경: 개인화 검토를 다시 하세요')
                return carried,False
            old=git_blob(path,ref['sha256'])
            if old is None or current.suffix.lower() not in ('.html','.md') or not equivalent_text(old,current.read_bytes(),path,current,repo):
                print('rerender: 참조 자료 변경: 검토를 다시 하세요: '+path.name)
                return carried,False
            print('rerender: 참조 자료는 스타일·스크립트만 바뀌었어요: '+path.name)
        carried.append({**ref,'path':str(current),'sha256':digest})
    recorded={Path(ref['path']).resolve():ref['sha256'] for ref in carried}
    try:
        for ref in carried:
            for dependency in reference_dependencies(Path(ref['path']),repo):
                if recorded.get(dependency.resolve())!=sha256(dependency):
                    print('rerender: 참조 그림 hash 누락/변경: '+dependency.name)
                    return carried,False
    except (ExplainError,OSError,ValueError):
        return carried,False
    return carried,True

def source_resources(pack,repo):
    base=pack.folder
    result={}
    for problem in pack.problems:
        markup=problem.conditions_html+problem.ask_html+problem.original_html+''.join(problem.figures_html)
        for node in parse(markup).find_all(lambda n:n.tag=='img'):
            url=urlsplit(node.attrs.get('src',''))
            if url.scheme or url.netloc or not url.path:
                raise ExplainError('저장소 내부 그림만 허용')
            path=(pack.pack_paths.link(base, unquote(url.path)) if pack.pack_paths else
                  inside(existing_path(base/unquote(url.path)),repo))
            logical = pack.pack_paths.logical(path) if pack.pack_paths else path
            result[logical.relative_to(repo).as_posix()]=sha256(path)
    return result

def published_bundle(pack, repo, *, expected_manifest=None):
    """Check the published bundle and bind every source fragment to its manifest."""
    from epe_render import names
    from epe_types import BUNDLE

    folder = inside(pack.folder, repo)
    data = inside(folder / BUNDLE / names(pack)[2], folder)
    manifest_path = inside(data / 'manifest.json', folder)
    manifest_bytes = manifest_path.read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if expected_manifest is not None and digest != expected_manifest:
        raise ExplainError('재렌더링 원본 manifest가 변경됐어요')
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or (manifest.get('range'), manifest.get('slug')) != (pack.range, pack.slug):
        raise ExplainError('재렌더링 원본 manifest와 대상 팩이 달라요')
    files = manifest.get('files')
    directory = inside(data / 'fragments', folder)
    if not isinstance(files, dict) or not files or not directory.is_dir():
        raise ExplainError('발행된 조각/검산 자료 목록이 없어요: 정상 저작 절차를 쓰세요')
    paths = {p.id: inside(directory / f'{p.id}.html', folder) for p in pack.problems}
    if {p.stem for p in directory.glob('*.html')} != set(paths) or any(
        path.relative_to(folder).as_posix() not in files for path in paths.values()
    ):
        raise ExplainError('발행된 조각 없음/불일치: 정상 저작 절차를 쓰세요')
    for name, expected in files.items():
        source = inside(folder / name, folder)
        if not source.is_file() or sha256(source) != expected:
            raise ExplainError('발행된 조각/검산 자료 변경: 정상 저작 절차를 쓰세요')
    return manifest, digest, paths


def verify_rerender_origin(pack, fragments, repo, manifest_hash, fragment_dir):
    """A stage annotation alone never grants permission to use old authoring."""
    if not isinstance(manifest_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', manifest_hash):
        raise ExplainError('재렌더링 원본 manifest hash가 올바르지 않아요')
    if fragment_dir is None:
        raise ExplainError('재렌더링 원본 조각과 대조할 RUN 경로가 필요해요')
    manifest, _, paths = published_bundle(pack, repo, expected_manifest=manifest_hash)
    for pid, path in paths.items():
        source_hash = manifest['files'][path.relative_to(pack.folder).as_posix()]
        local_bytes = inside(fragment_dir / f'{pid}.html', fragment_dir).read_bytes()
        normalized = local_bytes.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
        if hashlib.sha256(local_bytes).hexdigest() != source_hash or fragments.get(pid) != normalized:
            raise ExplainError(f'{pid}: 재렌더링 원본 조각과 달라요: 새 원고로 build 하세요')


def rerender(repo,target,run):
    from epe_cli import extract,load_run,load_fragments,build,read_json
    from epe_render import names,dump
    from epe_contract import payload_hash, validate_fragment
    from epe_labs import FILES
    repo=Path(repo).resolve()
    failed=bool(extract(repo,target,run))
    errors=[]
    try:
        items=load_run(run,errors=errors)
    except (ExplainError,OSError,ValueError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 1
    for error in errors:
        print(error,file=sys.stderr)
    failed=failed or bool(errors)
    for item in items:
        try:
            pack,folder=item['pack'],item['folder']
            data=pack.folder/'.assets'/names(pack)[2]
            manifest, manifest_hash, published = published_bundle(pack, repo)
            stored=read_json(inside(data/'validation.json',repo))
            if not isinstance(stored, dict):
                raise ExplainError('발행 검토 기록은 JSON 객체여야 해요')
            for pid, source in published.items():
                shutil.copy2(source, folder / 'explanations' / f'{pid}.html')
            evidence=data/'evidence'
            if evidence.is_dir():
                for child in evidence.rglob('*'):
                    inside(child,repo)
                shutil.copytree(evidence,folder/'evidence',dirs_exist_ok=True)
            fragments=load_fragments(item)
            if any(validate_fragment(p, fragments[p.id]) for p in pack.problems):
                raise ExplainError('통합 본문/답안 선택 형식 불일치: 새 저작 필요')
            manifest_key = (data / 'manifest.json').relative_to(pack.folder).as_posix()
            artifact_hashes = {**manifest['files'], manifest_key: manifest_hash}
            same=(stored.get('input_hash')==manifest.get('input_hash')==payload_hash(pack,fragments)
                  and stored.get('artifact_hashes')==artifact_hashes
                  and manifest.get('learning_style')==pack.learning_style
                  and manifest.get('review_policy_version')==POLICY_VERSION
                  and type(manifest.get('version')) is int and manifest['version']==1)
            refs,valid=verified_references(stored.get('references'),Path(manifest.get('repo',str(repo))),repo)
            same=same and valid and verified_resources(manifest.get('source_resources'),source_resources(pack,repo),repo)
            if same and (lab := manifest.get('lab')):
                source = inside(pack.folder / lab['html'], data / 'labs').parent
                destination = folder / 'lab'
                destination.mkdir()
                for name in FILES:
                    path = inside(source / name, source)
                    if path.relative_to(pack.folder).as_posix() not in manifest['files']:
                        raise ExplainError(f'실험 산출 해시 누락: {name}')
                    shutil.copyfile(path, destination / name)
            previous_html = inside(existing_path(pack.folder / (names(pack)[0] + '.html')), repo)
            include_problem_pdf = '원 문제 보기</a>' in previous_html.read_text(encoding='utf-8')
            build(item, fragments, include_problem_pdf=include_problem_pdf, rerender_from=manifest_hash)
            fresh=read_json(folder/'review.json')
            # Keep stale references visible when manual re-review is required; publish will reject them.
            if not valid:
                refs=stored.get('references',[])
            review=carry_reviews(stored,fresh,refs,same)
            dump(folder/'review.json',review)
            reused=review['content']['status']=='pass' and review['independent']['status']=='pass'
            print('rerender: '+('content·independent 재사용, source_visual·browser 재검토 필요' if reused else '입력 변경: 네 검토 모두 다시 필요 (입력·근거·검토 기준을 확인하세요)'))
        except (ExplainError,OSError,ValueError,KeyError,TypeError) as exc:
            failed=True
            print(f'{item["folder"].name}: {exc}',file=sys.stderr)
    return int(failed)
