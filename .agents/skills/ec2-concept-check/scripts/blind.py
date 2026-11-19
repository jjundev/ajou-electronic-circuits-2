"""Make an answer-free packet and verify the independent solver's ledger."""
import hashlib
import json
import re
from pathlib import Path
import shutil
from uuid import uuid4

from html2md import Builder
from source import read, sha, write


def projection(items):
    questions = []
    for item in items:
        question = {k:item[k] for k in ('id','title','format','stem_html','figure_svg') if k in item}
        if item['format'] == 'mcq':
            question['options'] = [{k:opt[k] for k in ('id','text')} for opt in item['options']]
        questions.append(question)
    return questions


def packet_contents(questions):
    result = {}
    lines = ["# 확인문제 독립 풀이", "", "답과 이의를 표로 기록하세요. | ID | 답 | 이의 |", ""]
    for item in questions:
        parser = Builder()
        parser.feed(item["stem_html"])
        lines.extend([f"## {item['id']}. {item['title']}", "", parser.root.text(), ""])
        if item.get("figure_svg"):
            name = f"{item['id']}.svg"
            result[name] = item["figure_svg"].encode()
            lines.extend([f"![문항의 회로도]({name})", ""])
        if item["format"] == "mcq":
            lines.extend(f"{option['id']}. {option['text']}" for option in item["options"])
        lines.append("")
    result['문제.md'] = '\n'.join(lines).encode()
    return result


def packet(data, folder):
    folder.mkdir(exist_ok=True)
    for name, content in packet_contents(projection(data['items'])).items():
        (folder/name).write_bytes(content)


def verified_packet_files(archive, issued):
    """Reconstruct the answer-free files from this issue's own question snapshot."""
    from pack_paths import checked_file
    questions = issued.get('questions', [])
    ids = [q['id'] for q in questions]
    if (not ids or not all(isinstance(cid, str) and re.fullmatch(r'q[1-9][0-9]*', cid) for cid in ids)
            or len(set(ids)) != len(ids) or set(ids) != set(issued['items'])
            or questions != projection(questions)):
        raise ValueError('invalid independent packet projection')
    expected = {name:hashlib.sha256(content).hexdigest() for name,content in packet_contents(questions).items()}
    folder = checked_file(archive, 'packet')
    if (expected != issued.get('files') or not folder.is_dir()
            or set(expected) != {p.name for p in folder.iterdir()}):
        raise ValueError('independent packet files changed')
    paths = set()
    for name, value in expected.items():
        path = checked_file(folder, name)
        if not path.is_file() or sha(path) != value:
            raise ValueError('independent packet files changed')
        paths.add(path)
    return paths


def verify_packet_source(issued, data, targets, *, inherited=False):
    questions = issued['questions']
    stored = {q['id']:q for q in questions}
    current = {item['id']:item for item in data['items']}
    objectives = {o['id']:o for o in data['objectives']}
    if not inherited:
        subset = [item for item in data['items'] if item['id'] in stored]
        full_digests = {i['id']:digest(i, objectives[i['objective']]) for i in subset}
        if issued['items'] != full_digests or questions != projection(subset):
            raise ValueError('independent packet differs from its full current source; reissue it')
    for cid in targets:
        item = current[cid]
        if issued['items'].get(cid) != digest(item, objectives[item['objective']]) or stored.get(cid) != projection([item])[0]:
            raise ValueError('independent packet question changed')


def digest(item, objective):
    content = {key: value for key, value in item.items() if key != "hint"}
    payload = json.dumps([content, objective], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def issued_path(run, folder):
    key = hashlib.sha256(str(folder.resolve()).encode()).hexdigest()
    return run/'blind-issued'/key


def issue(data, run, folder):
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('empty independent packet directory required')
    packet(data, folder)
    archive = issued_path(run, folder)
    archive.mkdir(parents=True, exist_ok=False)
    shutil.copytree(folder, archive/'packet')
    objectives = {o['id']:o for o in data['objectives']}
    write(archive/'issued.json', dict(questions=projection(data['items']), items={i['id']:digest(i,objectives[i['objective']]) for i in data['items']},
          files={p.name:sha(p) for p in (archive/'packet').iterdir()}))


def response_ref(row):
    if not isinstance(row.get('proof'),str) or not isinstance(row.get('submission_sha256'),str):
        raise ValueError('missing independent solver history response')
    return {'proof':row['proof'], 'sha256':row['submission_sha256'], 'solvers':row['solvers']}


def solver_history(run, cid, row, approved):
    """Verify unaccepted rounds from their response records, stopping at a certified prefix."""
    from pack_paths import checked_file
    def require(valid):
        if not valid:
            raise ValueError('invalid independent solver history: ' + cid)
    history, number = row.get('solvers'), row.get('round')
    require(type(number) is int and 1 <= number <= 3 and isinstance(history, list) and 1 <= len(history) <= number)
    require(all(isinstance(name,str) and name and name == name.strip() for name in history))
    require(len(set(history)) == len(history) and history[-1] == row.get('solver'))
    prefix = approved['solvers'] if approved is not None else []
    if row != approved:
        require(history[:len(prefix)] == prefix and len(history) > len(prefix))
        require(approved is None or number > approved['round'])
    # The exact inherited row already has the runner's prior attestation. New
    # submissions must link their actual answer/issue records to that original.
    ref = response_ref(row)
    paths = set()
    next_round = 4
    length = len(history)
    for name in reversed(history[-1:] if row == approved else history[len(prefix):]):
        require(isinstance(ref,dict) and isinstance(ref.get('proof'),str))
        answer = checked_file(run,ref['proof'])
        require(answer.is_relative_to(run/'blind-issued') and answer.name == 'answers.md')
        record = checked_file(run,answer.with_name('submission.json').relative_to(run))
        issue = checked_file(run,(answer.parent.parent/'issued.json').relative_to(run))
        require(record.is_file() and sha(record) == ref.get('sha256'))
        event = read(record)
        require(event.get('solver') == name and type(event.get('round')) is int and 1 <= event['round'] < next_round)
        author = event.get('author')
        require(isinstance(author,str) and author.strip() and author == author.strip() and author != name)
        issued = read(issue)
        packet_files = verified_packet_files(issue.parent, issued)
        require(event.get('answers_sha256') == sha(answer) and event.get('issued_sha256') == sha(issue))
        require(cid in event.get('previous', {}) and cid in issued['items'])
        require(any(parts[0].strip() == cid and len(parts) == 3 and parts[1].strip() for parts in
                    (line.strip().strip('|').split('|', 2) for line in answer.read_text(encoding='utf-8').splitlines())))
        if not paths:
            require((event['round'],event['author']) == (number,row['author']))
        paths.update((answer,record,issue))
        paths.update(packet_files)
        next_round = event['round']
        ref = event['previous'][cid]
        if row != approved:
            require(ref is None or isinstance(ref,dict) and isinstance(ref.get('solvers'),list))
            predecessor = ref['solvers'] if ref is not None else []
            require(history[:length] == [*predecessor, name])
        length -= 1
    if row != approved:
        require(ref == (response_ref(approved) if approved is not None else None))
        require(approved is None or next_round > approved['round'])
    return paths


def record(data, answers, previous, round_, *, packet_dir=None, author=None, solver=None):
    prior = read(previous) if previous.exists() else {}
    responses = {}
    objectives = {o["id"]: o for o in data["objectives"]}
    items = {item["id"]: item for item in data["items"]}
    for line in answers.read_text(encoding="utf-8").splitlines():
        parts = [value.strip() for value in line.strip().strip("|").split("|", 2)]
        if not re.fullmatch(r"q[1-9][0-9]*", parts[0]):
            continue
        if len(parts) != 3 or parts[0] not in items or parts[0] in responses or not parts[1]:
            raise ValueError(f"독립 풀이 답안표 행을 확인하세요: {line}")
        cid, answer, objection = parts
        item = items[cid]
        responses[cid] = {"answer": answer, "objection": objection, "round": round_,
                          "sha256": digest(item, objectives[item["objective"]])}
    if not responses:
        raise ValueError("독립 풀이 답안표에 문항 행이 없습니다.")
    if data.get('logical_inputs'):
        if not author or not solver or not author.strip() or not solver.strip() or author.strip() == solver.strip():
            raise ValueError('independent author and solver identities required')
        author, solver = author.strip(), solver.strip()
        if type(round_) is not int or not 1 <= round_ <= 3:
            raise ValueError('invalid independent solver history round')
        if packet_dir is None:
            raise ValueError('issued packet required')
        archive = issued_path(previous.parent, packet_dir)
        issued = read(archive/'issued.json')
        verified_packet_files(archive, issued)
        verify_packet_source(issued, data, responses)
        if (set(responses) != set(issued['items']) or
                {p.name:sha(p) for p in packet_dir.iterdir()} != issued['files']):
            raise ValueError('independent packet or response set changed')
        certified = inherited_rows(previous.parent, data)
        predecessors = {}
        for cid, row in responses.items():
            original = certified.get(cid)
            old = prior.get(cid) or original
            if old is not None and old != original:
                solver_history(previous.parent,cid,old,original)
            predecessors[cid] = response_ref(old) if old else None
            old = old or {}
            if issued['items'][cid] != row['sha256']:
                raise ValueError('independent packet changed')
            if round_ <= old.get('round', 0) or solver in old.get('solvers', []):
                raise ValueError('new round and independent solver required')
            row.update(author=author, solver=solver, solvers=[*old.get('solvers', []), solver])
        saved = archive/str(uuid4())
        saved.mkdir()
        shutil.copyfile(answers, saved/'answers.md')
        metadata = saved/'submission.json'
        digests = dict(issued_sha256=sha(archive/'issued.json'), answers_sha256=sha(saved/'answers.md'))
        write(metadata, dict(author=author, solver=solver, round=round_, previous=predecessors, **digests))
        proof = dict(proof=str((saved/'answers.md').relative_to(previous.parent)), submission_sha256=sha(metadata), **digests)
        for row in responses.values():
            row.update(proof)
    return {**prior, **responses}


def inherited_rows(run, data):
    from pack_flow import load_state
    from pack_parallel import prior_blind_approval
    if not data.get('parent_run'):
        return {}
    parent = Path(data['parent_run'])
    state = load_state(parent)
    worker = state['tasks'].get('concept-review', {})
    origin = worker.get('blind_origin', {})
    if (not origin or origin['recipient_attempt'] != worker.get('attempt')
            or Path(worker['attempt_dir'])/'quiz' != run):
        return {}
    return prior_blind_approval(parent, state['run_id'], origin['previous_attempt'], origin['file'], data['logical_inputs'])


def evidence(run, data, ledger):
    """Verify source answers and answer-free originals for each accepted item."""
    from pack_paths import checked_file
    paths = set()
    prior = inherited_rows(run, data)
    prior_issues = {Path(row['proof']).parent.parent for row in prior.values()}
    for item in data['items']:
        cid = item['id']
        row = ledger[cid]
        answer = checked_file(run, row.get('proof', ''))
        if (not row.get('author') or not row.get('solver') or row['author'] == row['solver']
                or not answer.is_relative_to(run/'blind-issued') or answer.name != 'answers.md'
                or sha(answer) != row.get('answers_sha256')):
            raise ValueError('independent response evidence changed')
        original = answer.parent.parent/'issued.json'
        issued = read(original)
        if sha(original) != row.get('issued_sha256'):
            raise ValueError('independent packet receipt changed')
        previous = prior.get(cid)
        inherited = row == previous
        if not inherited:
            if original.parent.relative_to(run) in prior_issues or (previous and (
                    row['round'] <= previous['round'] or row['solver'] in previous['solvers'])):
                raise ValueError('independent packet or recipient differs from the accepted approval; reissue it')
        verify_packet_source(issued, data, [cid], inherited=inherited)
        rows = [line.strip().strip('|').split('|', 2) for line in answer.read_text(encoding='utf-8').splitlines()]
        if (issued['items'].get(cid) != row['sha256'] or
                [cid, row['answer'], row['objection']] not in [[v.strip() for v in parts] for parts in rows]):
            raise ValueError('independent packet or answer changed')
        paths.update(solver_history(run, cid, row, previous))
    return sorted(paths)


def errors(data, ledger):
    from source import nfc

    objectives = {o["id"]: o for o in data["objectives"]}
    errors = []
    for item in data["items"]:
        cid = item["id"]
        row = ledger.get(cid, {})
        if row.get("sha256") != digest(item, objectives[item["objective"]]):
            errors.append(f"{cid}: 독립 풀이가 없거나 문항이 바뀌었습니다.")
            continue
        if item["format"] == "mcq":
            matched = row["answer"].upper() == item["answer"]
        else:
            answer = item["answer"]
            accepted = [answer["canonical"], *answer.get("accepted", [])]
            matched = nfc(row["answer"].strip()) in {nfc(value.strip()) for value in accepted}
        if not matched:
            errors.append(f"{cid}: 독립 풀이 답 불일치 ({row['answer']})")
        if row["objection"]:
            errors.append(f"{cid}: 이의 ({row['objection']})")
    return errors
