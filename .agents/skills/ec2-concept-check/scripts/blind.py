"""Make an answer-free packet and verify the independent solver's ledger."""
import hashlib
import json
import re
from pathlib import Path
import shutil
from uuid import uuid4

from html2md import Builder
from source import read, sha, write


def packet(data, folder):
    folder.mkdir(exist_ok=True)
    lines = ["# 확인문제 독립 풀이", "", "답과 이의를 표로 기록하세요. | ID | 답 | 이의 |", ""]
    for item in data["items"]:
        parser = Builder()
        parser.feed(item["stem_html"])
        lines.extend([f"## {item['id']}. {item['title']}", "", parser.root.text(), ""])
        if item.get("figure_svg"):
            path = folder / f"{item['id']}.svg"
            path.write_text(item["figure_svg"], encoding="utf-8")
            lines.extend([f"![문항의 회로도]({path.name})", ""])
        if item["format"] == "mcq":
            lines.extend(f"{option['id']}. {option['text']}" for option in item["options"])
        lines.append("")
    (folder / "문제.md").write_text("\n".join(lines), encoding="utf-8")


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
    write(archive/'issued.json', dict(items={i['id']:digest(i,objectives[i['objective']]) for i in data['items']},
          files={p.name:sha(p) for p in (archive/'packet').iterdir()}))


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
        if packet_dir is None:
            raise ValueError('issued packet required')
        archive = issued_path(previous.parent, packet_dir)
        issued = read(archive/'issued.json')
        if (set(responses) != set(issued['items']) or
                {p.name:sha(p) for p in packet_dir.iterdir()} != issued['files']):
            raise ValueError('independent packet or response set changed')
        for cid, row in responses.items():
            old = prior.get(cid, {})
            if issued['items'][cid] != row['sha256']:
                raise ValueError('independent packet changed')
            if round_ <= old.get('round', 0) or solver in old.get('solvers', []):
                raise ValueError('new round and independent solver required')
            row.update(author=author, solver=solver, solvers=[*old.get('solvers', []), solver])
        saved = archive/str(uuid4())
        saved.mkdir()
        shutil.copyfile(answers, saved/'answers.md')
        for row in responses.values():
            row.update(proof=str((saved/'answers.md').relative_to(previous.parent)), answers_sha256=sha(saved/'answers.md'))
    return {**prior, **responses}


def evidence(run, data, ledger):
    """Verify source answers and answer-free originals for each accepted item."""
    from pack_paths import checked_file
    paths = set()
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
        rows = [line.strip().strip('|').split('|', 2) for line in answer.read_text(encoding='utf-8').splitlines()]
        if (issued['items'].get(cid) != row['sha256'] or
                [cid, row['answer'], row['objection']] not in [[v.strip() for v in parts] for parts in rows]):
            raise ValueError('independent packet or answer changed')
        paths.update((answer, original))
        for name, digest_ in issued['files'].items():
            file = checked_file(original.parent/'packet', name)
            if sha(file) != digest_:
                raise ValueError('independent packet changed')
            paths.add(file)
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
