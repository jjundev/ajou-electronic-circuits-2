#!/usr/bin/env python3
"""
정리노트 HTML 검사기 (표준 라이브러리만 사용).

- 공통 검사: lang, 중복 id, 외부 리소스 허용 목록, 수식 구분자, 링크(복습문제 PDF 포함), 남은 슬롯, 위젯 정적 대체물
- manifest 검사: 섹션·토픽 id, 필수 용어, 레이어, 보충 배지, 페이지 요약, 예고 밖 금지어, 링크
CLI:
  check_html.py FILE [FILE ...]
  check_html.py --manifest run/manifest.json --note NOTE.html
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifest as manifest_mod  # noqa: E402
from learning_style import validate_style_audit  # noqa: E402
from readability import readability_errors  # noqa: E402
from html2md import Builder, Node  # noqa: E402

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CONTAINER_CLASSES = {"topic", "card"}
# 블록 경계에서 텍스트를 끊어 인접 수식이 "$$"로 붙지 않게 한다.
BLOCK_TAGS = {"p", "div", "li", "ol", "ul", "td", "th", "tr", "table", "h1", "h2", "h3", "h4", "section", "article",
              "details", "summary", "figure", "figcaption", "blockquote", "header", "footer", "label", "br"}
ALLOWED_EXTERNAL_PREFIXES = (
    "https://cdn.jsdelivr.net/npm/katex@0.16.11/",
    "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/",
)
SUPP_LABEL = "보충 · 수업에서 유도하진 않았어요"
# 스킬 템플릿을 바꾸기 전에 만든 팩의 라벨도 받아 준다.
LEGACY_SUPP_LABELS = ("📎 보충 · 수업 미유도",)
SUM_PANEL_ID = "sum-for"
SLOT_RE = re.compile(r"\{\{[A-Z_]+\}\}")
# 조각에 HTML 대신 마크다운으로 쓴 링크: 화면에 [글자](#id)가 그대로 보이고 눌리지 않는다.
MD_LINK_RE = re.compile(r"\[[^\]\n]+\]\((?:#|https?:|\.\./)[^)\s]*\)")
REMOTE_PREFIXES = ("http://", "https://", "//")
# CSS 안의 url(...) 과 @import "..." 대상
CSS_URL_RE = re.compile(r"""url\(\s*['"]?([^'")\s]+)|@import\s+['"]([^'"]+)['"]""", re.IGNORECASE)


def is_remote(url: str) -> bool:
    return url.strip().lower().startswith(REMOTE_PREFIXES)


@dataclass
class Container:
    id: str
    classes: set[str]
    attrs: dict[str, str]
    section: str | None
    text: str = ""
    hrefs: list[str] = field(default_factory=list)
    child_classes: set[str] = field(default_factory=set)


@dataclass
class Doc:
    lang: str | None = None
    ids: set[str] = field(default_factory=set)
    duplicate_ids: set[str] = field(default_factory=set)
    id_section: dict[str, str | None] = field(default_factory=dict)
    hrefs: list[str] = field(default_factory=list)
    local_resources: list[str] = field(default_factory=list)
    external_resources: list[str] = field(default_factory=list)
    section_text: dict[str, str] = field(default_factory=lambda: defaultdict(str))
    containers: dict[str, Container] = field(default_factory=dict)
    widgets: dict[str, set[str]] = field(default_factory=dict)
    scripts_by_id: dict[str, str] = field(default_factory=dict)
    body_text: str = ""


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doc = Doc()
        # (tag, section_id, container_id, widget_id)
        self.stack: list[tuple[str, str | None, str | None, str | None]] = []
        self.raw_tag: str | None = None
        self.script_id: str | None = None

    def _context(self) -> tuple[str | None, str | None, str | None]:
        if not self.stack:
            return None, None, None
        _, sec, con, wid = self.stack[-1]
        return sec, con, wid

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        sec, con, wid = self._context()
        classes = set(a.get("class", "").split())
        if tag == "html":
            self.doc.lang = a.get("lang")
        el_id = a.get("id")
        if el_id:
            if el_id in self.doc.ids:
                self.doc.duplicate_ids.add(el_id)
            self.doc.ids.add(el_id)
        if tag == "section" and el_id:
            sec = el_id
        if el_id:
            self.doc.id_section[el_id] = sec
        if con is not None:
            self.doc.containers[con].child_classes |= classes
        if wid is not None:
            self.doc.widgets[wid] |= classes
        if el_id and classes & CONTAINER_CLASSES:
            self.doc.containers[el_id] = Container(el_id, classes, a, sec)
            con = el_id
        if el_id and "widget" in classes:
            self.doc.widgets[el_id] = set()
            wid = el_id
        if tag == "a" and "href" in a:
            self.doc.hrefs.append(a["href"])
            if con is not None:
                self.doc.containers[con].hrefs.append(a["href"])
        # 원격 리소스: 모든 태그의 src, 모든 <link>의 href (<a href>는 broken_links 담당)
        resource = a.get("src") or (a.get("href") if tag == "link" else None)
        if resource:
            url = urlsplit(resource)
            if url.path and not (url.scheme or url.netloc):
                self.doc.local_resources.append(resource)
        if is_remote(a.get("src", "")):
            self.doc.external_resources.append(a["src"])
        if tag == "link" and is_remote(a.get("href", "")):
            self.doc.external_resources.append(a["href"])
        if tag in ("script", "style"):
            self.raw_tag = tag
            self.script_id = el_id if tag == "script" else None
            if self.script_id:
                self.doc.scripts_by_id[self.script_id] = ""
        if tag in BLOCK_TAGS:
            self._emit("\n")
        if tag not in VOID_TAGS:
            self.stack.append((tag, sec, con, wid))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.raw_tag = None
            self.script_id = None
        if tag in BLOCK_TAGS:
            self._emit("\n")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.raw_tag == "script":
            if self.script_id:
                self.doc.scripts_by_id[self.script_id] += data
            return
        if self.raw_tag == "style":
            for m in CSS_URL_RE.finditer(data):
                url = m.group(1) or m.group(2)
                if is_remote(url):
                    self.doc.external_resources.append(url)
            return
        self._emit(data)

    def _emit(self, data):
        if self.raw_tag:
            return
        sec, con, _ = self._context()
        self.doc.body_text += data
        if sec:
            self.doc.section_text[sec] += data
        if con:
            self.doc.containers[con].text += data


def parse_html(source: str) -> Doc:
    parser = _Parser()
    parser.feed(source)
    parser.close()
    return parser.doc


def parse_file(path: Path | str) -> Doc:
    return parse_html(Path(path).read_text(encoding="utf-8"))


def math_delimiter_errors(text: str) -> list[str]:
    errors: list[str] = []
    t = text.replace("\\$", "")
    if t.count("$$") % 2:
        errors.append("unbalanced $$ (display math)")
    t = re.sub(r"\$\$.*?\$\$", "", t, flags=re.S)
    if t.count("$") % 2:
        errors.append("unbalanced $ (inline math)")
    return errors


def broken_links(doc: Doc, base_dir: Path, *, pack_paths=None) -> list[str]:
    broken: list[str] = []
    cache: dict[Path, Doc] = {}
    for href in doc.hrefs:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        path_part, _, frag = href.partition("#")
        if not path_part:
            if frag not in doc.ids:
                broken.append(href)
            continue
        target = (pack_paths.link(base_dir, unquote(path_part)) if pack_paths else
                  (Path(base_dir) / unquote(path_part)).resolve())
        if not target.exists():
            broken.append(href)
            continue
        if frag and target.suffix == ".html":
            if target not in cache:
                cache[target] = parse_file(target)
            if frag not in cache[target].ids:
                broken.append(href)
    return broken


@dataclass(frozen=True)
class Problem:
    code: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.where}: {self.detail}"


def check_common(doc: Doc, source: str, path: Path, *, pack_paths=None) -> list[Problem]:
    name = Path(path).name
    out: list[Problem] = []
    if doc.lang != "ko":
        out.append(Problem("lang", name, f"<html lang> = {doc.lang!r}"))
    out += [Problem("duplicate-id", name, i) for i in sorted(doc.duplicate_ids)]
    out += [Problem("external", name, u) for u in doc.external_resources if not u.startswith(ALLOWED_EXTERNAL_PREFIXES)]
    out += [Problem("math", name, e) for e in math_delimiter_errors(doc.body_text)]
    out += [Problem("broken-link", name, h) for h in broken_links(doc, Path(path).parent, pack_paths=pack_paths)]
    if pack_paths:
        for resource in doc.local_resources:
            target = pack_paths.link(Path(path).parent, unquote(urlsplit(resource).path))
            if not target.is_file():
                out.append(Problem("missing-resource", name, resource))
    out += [Problem("leftover-slot", name, s) for s in sorted(set(SLOT_RE.findall(source)))]
    out += [Problem("markdown-link", name, s) for s in MD_LINK_RE.findall(doc.body_text)]
    out += [Problem(code, name, detail) for code, detail in readability_errors(source)]
    out += [Problem("widget-static-missing", wid, "위젯에 .widget-static 정적 대체물이 없음")
            for wid, classes in sorted(doc.widgets.items()) if "widget-static" not in classes]
    return out


def check_note(doc: Doc, m: dict) -> list[Problem]:
    out: list[Problem] = []
    preview_section = None
    for sec in m["sections"]:
        if sec["id"] not in doc.ids:
            out.append(Problem("missing-section", sec["id"], "섹션 id 없음"))
        for t in sec["topics"]:
            if t["id"] == m["preview_topic"]:
                preview_section = sec["id"]
            con = doc.containers.get(t["id"])
            if con is None:
                out.append(Problem("missing-topic", t["id"], "토픽 없음"))
                continue
            if con.section != sec["id"]:
                out.append(Problem("wrong-section", t["id"], f"{con.section} 안에 있음 (기대: {sec['id']})"))
            out += [Problem("missing-term", t["id"], term) for term in t["required_terms"] if term not in con.text]
            out += [Problem("missing-layer", t["id"], layer) for layer in t["layers"] if layer not in con.child_classes]
            if t["supp"] and ("supp" not in con.child_classes
                              or not any(label in con.text for label in (SUPP_LABEL, *LEGACY_SUPP_LABELS))):
                out.append(Problem("missing-supp", t["id"], f"layer supp + '{SUPP_LABEL}' 필요"))
            # 페이지 요약 패널(#sum-for)이 있는 템플릿으로 만든 팩만 검사한다.
            if SUM_PANEL_ID in doc.ids and t["layers"] and "sum" not in con.child_classes:
                out.append(Problem("missing-sum", t["id"], '<div class="sum" hidden> 페이지 요약 없음'))
    texts: dict[str, str] = {}
    for sec in m["sections"]:
        if sec["id"] != preview_section:
            texts[sec["id"]] = doc.section_text.get(sec["id"], "")
            continue
        for t in sec["topics"]:
            if t["id"] != m["preview_topic"] and t["id"] in doc.containers:
                texts[t["id"]] = doc.containers[t["id"]].text
    for where, text in texts.items():
        out += [Problem("forbidden-term", where, term) for term in m["forbidden_outside_preview"] if term in text]
    for link in m["links"]:
        con = doc.containers.get(link["topic"])
        if con is None or link["href"] not in con.hrefs:
            out.append(Problem("missing-link", link["topic"], link["href"]))
    return out


# content-rules.md "정확히 말하면의 길잡이": formal 본문 블록이 이만큼 이상이면 소제목이 필요하다.
SUBHEAD_MIN_BLOCKS = 6


def _kids(node: Node) -> list[Node]:
    return [c for c in node.children if isinstance(c, Node)]


def check_guide(source: str, m: dict) -> list[Problem]:
    """길잡이 템플릿(body data-guide)으로 만든 노트만: 끝의 확인 질문, formal 소제목, 본문 접기 금지."""
    builder = Builder()
    builder.feed(source)
    root = builder.root
    body = next(root.find_all(lambda n: n.tag == "body"), None)
    if body is None or "data-guide" not in body.attrs:
        return []
    topics = {n.attrs.get("id"): n for n in root.find_all(lambda n: n.tag == "article" and "topic" in n.classes)}
    out: list[Problem] = []
    for t in (t for s in m["sections"] for t in s["topics"] if t["layers"]):
        art = topics.get(t["id"])
        if art is None:
            continue  # missing-topic이 이미 알린다
        quiz = [q for q in _kids(art) if {"quiz", "after"} <= q.classes]
        if not quiz or not any(c.tag == "p" and "q" in c.classes for c in _kids(quiz[0])) \
                or not any(any(s.tag == "summary" for s in _kids(d)) for d in _kids(quiz[0]) if d.tag == "details"):
            out.append(Problem("missing-check-quiz", t["id"],
                               '토픽 끝에 <div class="quiz after"><p class="q">…</p><details><summary>…</summary>… 필요'))
        # 확인 질문의 답 토글과 위젯 안 조작부만 허용한다. 레이어 밖에서 본문을 접어도 막는다.
        folded = [d for d in art.find_all(lambda n: n.tag == "details")
                  if not any(a.classes & {"quiz", "widget"} for a in _ancestors(d, art))]
        if folded:
            out.append(Problem("folded-body", t["id"], "본문을 <details>로 접지 않아요(확인 질문의 답만 허용)"))
        formal = next((c for c in _kids(art) if {"layer", "formal"} <= c.classes), None)
        if formal is not None:
            blocks = [c for c in _kids(formal) if "layer-title" not in c.classes and c.tag != "h4"]
            has_sub = any(c.tag == "h4" and "sub" in c.classes for c in _kids(formal))
            if len(blocks) >= SUBHEAD_MIN_BLOCKS and not has_sub:
                out.append(Problem("formal-no-subheads", t["id"],
                                   f'정확히 말하면 블록 {len(blocks)}개: <h4 class="sub"> 소제목 필요'))
    return out


def _ancestors(node: Node, stop: Node):
    node = node.parent
    while node is not None and node is not stop:
        yield node
        node = node.parent


def check_file(path: Path | str) -> list[Problem]:
    source = Path(path).read_text(encoding="utf-8")
    return check_common(parse_html(source), source, Path(path))


def check_pack(m: dict, note_path: Path | str, *, repo: Path, style_audit: dict,
               defer_answer_pdf: bool = False, pack_paths=None) -> list[Problem]:
    note_path = Path(note_path)
    validation = manifest_mod.validate(m, repo=repo)
    out = [Problem("learning-style" if "learning_style" in e else "manifest", note_path.name, e)
           for e in validation]
    if not validation:
        topics = [t["id"] for s in m["sections"] for t in s["topics"]]
        out += [Problem("learning-style", note_path.name, e)
                for e in validate_style_audit(style_audit, m["learning_style"], topics)]
    source = note_path.read_text(encoding="utf-8")
    doc = parse_html(source)
    common = check_common(doc, source, note_path, pack_paths=pack_paths)
    # Only the literal expected answer path's missing-file error is deferred.
    # An anchor, different directory/name, or any other check still fails.
    expected = manifest_mod.answer_pdf_name(m)
    if defer_answer_pdf and m["problems"] and not (note_path.parent / expected).exists():
        for index, problem in enumerate(common):
            if problem.code == "broken-link" and problem.detail == expected:
                del common[index]
                break
    if m["problems"]:
        for pdf in (manifest_mod.problem_pdf_name(m), expected):
            target = note_path.parent / pdf
            if target.exists() and not target.is_file():
                common.append(Problem("pdf-file", note_path.name, f"PDF 파일이 아님: {pdf}"))
    return out + common + check_note(doc, m) + check_guide(source, m)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--manifest")
    ap.add_argument("--note")
    ap.add_argument("--repo", type=Path, default=manifest_mod.DEFAULT_REPO)
    ap.add_argument("--defer-answer-pdf", action="store_true")
    args = ap.parse_args(argv)
    if args.defer_answer_pdf and not args.manifest:
        ap.error("--defer-answer-pdf에는 --manifest가 필요")
    problems: list[Problem] = []
    if args.manifest:
        if not args.note:
            ap.error("--manifest에는 --note가 필요")
        try:
            m = manifest_mod.load(args.manifest, repo=args.repo)
            audit = json.loads((Path(args.manifest).parent / "learning-style-audit.json").read_text(encoding="utf-8"))
            problems += check_pack(m, args.note, repo=args.repo, style_audit=audit,
                                   defer_answer_pdf=args.defer_answer_pdf)
        except (manifest_mod.ManifestError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            problems.append(Problem("manifest-or-audit", str(args.manifest), str(exc)))
    for name in args.files:
        problems += check_file(name)
    for p in problems:
        print(p)
    if problems:
        print(f"FAIL ({len(problems)})")
    elif args.defer_answer_pdf:
        print("PRELIMINARY: answer PDF pending")
    else:
        print("OK")
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
