"""Resolve actual EC2 note files and freeze lecture evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unicodedata

from interaction import Builder

RANGE = re.compile(r"[0-9]{4}(?:-[0-9]{4})?")
STT = re.compile(r"([0-9]{4}) 전회2\.md")
TOPIC = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def nfc(text):
    return unicodedata.normalize("NFC", text)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"JSON 객체가 필요합니다: {path}")
    return value


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def one_file(folder, pattern):
    files = [path for path in folder.iterdir() if path.is_file() and pattern.fullmatch(nfc(path.name))]
    if len(files) != 1:
        raise ValueError(f"파일 하나가 필요합니다: {folder} / {pattern.pattern} (찾은 수 {len(files)})")
    return files[0]


def load_topics(note):
    parser = Builder()
    parser.feed(note.read_text(encoding="utf-8"))
    topics = {}
    all_ids = set()
    for article in parser.root.find_all(lambda node: node.tag == "article" and "topic" in node.classes):
        topic = article.attrs.get("id", "")
        if not TOPIC.fullmatch(topic) or topic in all_ids:
            raise ValueError(f"정리노트 토픽 ID가 비어 있거나 중복됩니다: {topic!r}")
        all_ids.add(topic)
        if topic == "why-circuit" or topic.endswith(("-next", "-links", "-cheatsheet", "-preview", "-summary")):
            continue
        tags = {kind: [node.text().strip() for node in article.find_all(
            lambda node: {"tag", kind} <= node.classes)] for kind in ("date", "slide", "supp")}
        if not tags["supp"]:
            topics[topic] = {"date": tags["date"], "slides": tags["slide"]}
    if not topics:
        raise ValueError(f"출제할 정리노트 토픽이 없습니다: {note}")
    return topics


RUNTIME = ("pretendard/pretendard.css", "katex/katex.min.css", "katex/katex.min.js",
           "katex/contrib/auto-render.min.js")


def runtime_resources(repo):
    """Pin the quiz runtime and the local fonts named by its vendored stylesheets."""
    from pack_paths import checked_file
    vendor = repo/'복습노트/.assets/vendor'
    files = {checked_file(vendor, name) for name in (*RUNTIME, 'pretendard/LICENSE', 'katex/LICENSE')}
    for sheet in [p for p in files if p.suffix == '.css']:
        for ref in re.findall(r'url\(\s*([^)]*?)\s*\)', sheet.read_text(encoding='utf-8'), re.I):
            relative = (sheet.parent/ref.strip(chr(34) + chr(39))).resolve().relative_to(vendor.resolve())
            files.add(checked_file(vendor, relative))
    return {'vendor/' + p.relative_to(vendor).as_posix(): p for p in files}


def parallel_parent(parent_run, repo, range_):
    from pack_flow import inspect_state
    state = inspect_state(parent_run)
    if nfc(state['repo']) != nfc(str(repo)) or state['range'] != range_ or not state.get('concept_check_enabled'):
        raise ValueError('quiz_parent_mismatch')
    return state


def accepted_sources(state, root, paths):
    from pack_findings import current_audit
    from pack_flow import _done
    from pack_paths import checked_file
    from pack_parallel import output
    if (state.get('workflow') != 'parallel' or state.get('stale_inputs')
            or state['status'] in ('blocked', 'withheld', 'recovery_required')
            or not current_audit(state) or not all(_done(state, task) for task in
                ('assemble-note', 'scope-final', 'selection', 'convert-md'))):
        raise ValueError('quiz_candidate_required')
    converted = state['converted_assets']
    note, md = (Path(converted[k]['path']) for k in ('note', 'md'))
    if output(state, 'assemble-note', 'note') != note:
        raise ValueError('quiz_input_changed')
    expected = {note.name: converted['note']['sha256'],
                '.assets/' + md.name: converted['md']['sha256']}
    candidate = Path(state['actions']['convert-md']['candidate_root'])
    for record in converted['svgs']:
        expected[Path(record['path']).relative_to(candidate).as_posix()] = record['sha256']
    if state['selected_ids']:
        if not _done(state, 'stage-problem-index'):
            raise ValueError('quiz_candidate_required')
        expected.update(state['actions']['stage-problem-index']['pack']['files'])
    for relative, digest in expected.items():
        path = checked_file(root, relative)
        if not path.is_file() or sha(path) != digest:
            raise ValueError('quiz_input_changed')
        paths['pack/' + nfc(relative)] = path
    if not state['selected_ids'] and (root/'.assets/problems.txt').exists():
        raise ValueError('quiz_input_changed')


def describe_inputs(repo, range_, parent_run=None, *, candidate_pack: Path | None = None):
    if not RANGE.fullmatch(range_):
        raise ValueError(f"날짜 범위 형식은 MMDD 또는 MMDD-MMDD입니다: {range_}")
    first, _, last = range_.partition("-")
    last = last or first
    if first > last:
        raise ValueError(f"날짜 범위 순서를 확인하세요: {range_}")
    pack = repo / "복습노트" / range_
    public_pack = pack
    state = parallel_parent(parent_run, repo, range_) if parent_run else None
    parallel = state and state.get('workflow') == 'parallel'
    logical = {}
    if candidate_pack is not None:
        if not parallel or not state.get('concept_contract'):
            raise ValueError('quiz_candidate_required')
        pack = Path(candidate_pack)
        if pack != Path(state['actions'].get('convert-md', {}).get('candidate_root', '')):
            raise ValueError('quiz_candidate_required')
    strict = parallel and state.get('concept_contract')
    if strict:
        accepted_sources(state, pack, logical)
    note_pattern = re.compile(rf"정리노트_{range_}_([A-Za-z0-9_]+)\.html")
    note = one_file(pack, note_pattern)
    slug = note_pattern.fullmatch(nfc(note.name))[1]
    md = one_file(pack / ".assets", re.compile(re.escape(nfc(note.stem)) + r"\.md"))
    transcripts = {}
    for path in sorted((repo / "STT").iterdir()):
        match = STT.fullmatch(nfc(path.name))
        if match and path.is_file() and first <= match[1] <= last:
            if match[1] in transcripts:
                raise ValueError(f"중복 STT: {path}")
            transcripts[match[1]] = str(path)
    if not {first, last} <= transcripts.keys():
        raise ValueError(f"범위 양끝 날짜의 STT를 확인하세요: {range_}")

    topics = load_topics(note)
    loaded = {
        "repo": str(repo), "range": range_, "slug": slug, "pack": str(public_pack),
        "note": str(note), "note_md": str(md), "transcripts": transcripts,
        "topics": topics, "forbidden": [],
    }
    inputs = [note, md, *map(Path, transcripts.values())]
    problems = pack / ".assets/problems.txt"
    if problems.is_file():
        loaded["problem_list"] = str(problems)
        inputs.append(problems)
    if parent_run is not None:
        from pack_parallel import output
        manifest_path = output(state, 'scope-final', 'manifest.json') if parallel else parent_run / "manifest.json"
        manifest = read(manifest_path)
        if (manifest.get("range"), manifest.get("slug")) != (range_, slug):
            raise ValueError(f"정리노트와 부모 manifest 범위·주제가 다릅니다: {manifest_path}")
        reviewed = {topic["id"] for section in manifest["sections"] for topic in section["topics"]
                    if not topic.get("supp") and topic["id"] != manifest.get("preview_topic")}
        loaded["topics"] = {key: value for key, value in topics.items() if key in reviewed}
        if not loaded["topics"]:
            raise ValueError("부모 manifest에 출제할 토픽이 없습니다.")
        summaries = {date: str(parent_run / f"summaries/stt-{date}.md") for date in transcripts}
        if parallel:
            summaries = {date: str(output(state, 'stt-' + date, 'summaries/stt-' + date + '.md')) for date in transcripts}
        if strict:
            selection = output(state, 'selection', 'selection.json')
            loaded['selection'] = str(selection)
            logical.update(manifest=manifest_path, selection=selection)
            logical.update({'stt/' + d: Path(p) for d,p in transcripts.items()})
            logical.update({'summary/' + d: Path(p) for d,p in summaries.items()})
            logical.update(runtime_resources(repo))
            if candidate_pack is not None:
                loaded['candidate_pack'] = str(pack)
            if not {nfc(str(note)), nfc(str(md))} <= {nfc(str(p)) for p in logical.values()}:
                raise ValueError('quiz_input_changed')
            inputs.extend(logical.values())
            loaded['logical_inputs'] = {key: sha(path) for key, path in logical.items()}
        loaded.update(manifest=str(manifest_path), summaries=summaries,
                      forbidden=manifest.get("forbidden_outside_preview", []))
        inputs.extend([manifest_path, *map(Path, summaries.values())])
    loaded["inputs"] = {str(path): sha(path) for path in inputs}
    return loaded


def verify_inputs(data):
    for path, digest in data["inputs"].items():
        if sha(Path(path)) != digest:
            raise ValueError(f"확인문제 작성 중 입력이 바뀌었습니다: {path}")
