"""Check the quiz contract before rendering and blind review."""
from __future__ import annotations

from collections import Counter
import re
import xml.etree.ElementTree as ET

from interaction import Builder
from source import read

LETTERS = list("ABCD")
SVG_TAGS = {"svg", "title", "desc", "g", "path", "line", "polyline", "polygon", "rect", "circle", "ellipse", "text", "tspan"}
SVG_ATTRS = {
    "viewBox", "width", "height", "role", "aria-label", "x", "y", "x1", "y1", "x2", "y2", "dx", "dy",
    "cx", "cy", "r", "rx", "ry", "d", "points", "fill", "stroke", "stroke-width", "stroke-linecap",
    "stroke-linejoin", "stroke-dasharray", "transform", "font-size", "font-weight", "text-anchor",
    "dominant-baseline", "baseline-shift",
}


def require(ok, location, message):
    if not ok:
        raise ValueError(f"{location}: {message}")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def texts(values):
    return isinstance(values, list) and all(text(value) for value in values)


def visible_text(fragment):
    parser = Builder()
    parser.feed(fragment)
    for node in parser.root.find_all(lambda n: True):
        require(node.tag in {"p", "strong", "em", "code", "br", "ul", "ol", "li"} and not node.attrs,
                "stem_html", f"허용되지 않은 태그 또는 속성: {node.tag}")
    rendered = parser.root.text().strip()
    require(rendered, "stem_html", "발문 본문이 비어 있습니다.")
    return rendered


def validate_svg(svg, item_id):
    root = ET.fromstring(svg)
    require(root.tag == "{http://www.w3.org/2000/svg}svg" and root.get("viewBox") and root.get("aria-label"),
            item_id, "회로도 SVG에 xmlns, viewBox, aria-label이 필요합니다.")
    for el in root.iter():
        require(el.tag.startswith("{http://www.w3.org/2000/svg}") and el.tag.split("}", 1)[1] in SVG_TAGS,
                item_id, f"허용되지 않은 회로도 요소: {el.tag}")
        for attr, value in el.attrib.items():
            require(attr in SVG_ATTRS and "url(" not in value.lower(), item_id, f"허용되지 않은 회로도 속성: {attr}")
    for el in root.iter():
        el.tag = el.tag.split("}", 1)[1]
    root.set("xmlns", "http://www.w3.org/2000/svg")
    return ET.tostring(root, encoding="unicode")


def load(source, run):
    obj_doc, item_doc = (read(run / f"{name}.json") for name in ("objectives", "items"))
    require((obj_doc.get("range"), obj_doc.get("slug")) == (source["range"], source["slug"]),
            "objectives.json", "정리노트 범위·주제와 다릅니다.")
    objectives, items = obj_doc["objectives"], item_doc["items"]
    require(isinstance(objectives, list) and isinstance(items, list) and 1 <= len(items) <= 16,
            "items.json", "1~16문항과 목표 목록이 필요합니다.")

    known = {}
    for objective in objectives:
        oid = objective["id"]
        require(isinstance(oid, str) and re.fullmatch(r"o[1-9][0-9]*", oid) and oid not in known,
                oid, "목표 ID가 잘못되었거나 중복됩니다.")
        require(objective.get("topic_id") in source["topics"], oid, "정리노트 토픽 근거를 확인하세요.")
        require(text(objective.get("concept")), oid, "개념 이름이 필요합니다.")
        evidence = objective.get("source", {})
        require(evidence.get("date") in source["transcripts"] and text(evidence.get("stt"))
                and text(evidence.get("slide")), oid, "날짜·STT 위치·강의 슬라이드 근거가 필요합니다.")
        topic = source["topics"][objective["topic_id"]]
        require(not topic["date"] or any(evidence["date"] in label for label in topic["date"]),
                oid, "목표 날짜와 토픽 날짜가 다릅니다.")
        require(not topic["slides"] or evidence["slide"] in topic["slides"],
                oid, "정리노트의 슬라이드 태그를 그대로 기록하세요.")
        known[oid] = objective

    used, seen, stems = Counter(), set(), set()
    for item in items:
        iid = item["id"]
        require(isinstance(iid, str) and re.fullmatch(r"q[1-9][0-9]*", iid) and iid not in seen,
                iid, "문항 ID가 잘못되었거나 중복됩니다.")
        seen.add(iid)
        oid = item["objective"]
        require(oid in known, iid, "목표 ID가 없습니다.")
        used[oid] += 1
        require(all(text(item.get(key)) for key in ("title", "stem_html", "hint")),
                iid, "제목·발문·첫 행동 힌트가 필요합니다.")
        stem = visible_text(item["stem_html"])
        require(stem not in stems or item.get("figure_svg"), iid, "발문이 중복됩니다.")
        stems.add(stem)
        if item.get("figure_svg"):
            item["figure_svg"] = validate_svg(item["figure_svg"], iid)
        format_ = item.get("format")
        require(format_ in ("mcq", "short"), iid, "형식은 mcq 또는 short입니다.")
        visible = [stem, item["title"], item["hint"], item.get("figure_svg", "")]
        if format_ == "mcq":
            options = item["options"]
            require([o["id"] for o in options] == LETTERS and item["answer"] in LETTERS, iid, "A~D 보기·정답을 확인하세요.")
            require(len({o["text"].strip() for o in options}) == 4, iid, "보기가 중복됩니다.")
            for o in options:
                keys = ("text", "why") if o["id"] == item["answer"] else ("text", "why", "misconception")
                require(all(text(o.get(key)) for key in keys), iid, "보기별 설명 및 오답의 오개념이 필요합니다.")
                visible.extend(o[key] for key in keys)
        else:
            answer, solution = item["answer"], item["solution"]
            require(text(answer.get("canonical")) and texts(answer.get("accepted", [])) and texts(solution) and solution,
                    iid, "정규 답안·허용 표기 목록·풀이 단계가 필요합니다.")
            visible.extend(solution)
        require(not any(term.casefold() in "\n".join(visible).casefold() for term in source["forbidden"]),
                iid, "신규 팩의 예고 범위 밖 금지어가 문항에 들어갔습니다.")
    for oid in known:
        require(1 <= used[oid] <= 2, oid, "목표당 1~2문항이 필요합니다.")
    return dict(source, objectives=objectives, items=items)
