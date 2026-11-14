"""Make an answer-free packet and verify the independent solver's ledger."""
import hashlib
import json
import re

from html2md import Builder
from source import read


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


def record(data, answers, previous, round_):
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
    return {**(read(previous) if previous.exists() else {}), **responses}


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
