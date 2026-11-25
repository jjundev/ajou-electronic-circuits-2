"""보고서 md → 노션 새 페이지 (텍스트만), 되읽기 baseline, 그림 빈자리 검사.

    python3 -m scripts.ec2_report.sync push --n 1
    python3 -m scripts.ec2_report.sync check-images --n 1
    python3 -m scripts.ec2_report.sync diff --n 1
    python3 -m scripts.ec2_report.sync recover --n 1

종료 코드: 0 성공, 1 그림 빈자리 있음(check-images)·노션 수정 있음(diff),
2 md 검사 error 로 막힘, 3 노션·설정·파일 오류.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from datetime import datetime
from pathlib import Path

from . import config, notion
from .check import Finding, check_markdown, check_pulled_images, roundtrip


_SECTION = re.compile(r"^# \d")
_IMAGE_LINE = re.compile(r"^\s*!\[")


def _first_line(text: str) -> str:
    return next((line for line in text.splitlines() if line.strip()), "")


class SyncBlocked(Exception):
    def __init__(self, findings: list[Finding]):
        super().__init__(f"검사 error {len(findings)}건")
        self.findings = findings


def strip_title(text: str, title: str) -> str:
    """앞쪽 빈 줄 다음 첫 줄이 제목 헤딩이면 그 줄과 뒤따르는 빈 줄만 뗀다.

    페이지 제목은 properties 로 따로 주므로 본문의 제목 헤딩은 중복이다.
    `# 1. Design Problem` 처럼 번호로 시작하는 헤딩은 대절이므로 남긴다 (옛 양식 호환).
    """
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i == len(lines) or not lines[i].startswith("# ") or _SECTION.match(lines[i]):
        return text
    i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "".join(lines[i:])


def _context(n: int, root: Path | None):
    root = Path(root) if root else config.find_root()
    info = config.load_course_info(root)
    return root, info, config.paths(n, root, info)


def push(n: int, root: Path | None = None, token: str | None = None,
         now: str | None = None) -> dict:
    root, info, p = _context(n, root)
    findings = check_markdown(p.report_md)
    errors = [f for f in findings if f.level == "error"]
    if errors:
        raise SyncBlocked(errors)
    parent = info.get("notion_parent_page_id")
    if not parent:
        raise notion.NotionError(
            "`.claude/과목정보.md` 의 notion_parent_page_id 가 비어 있습니다. "
            "노션에 전자회로2 페이지를 만들고 integration 을 Connect 한 뒤 그 id 를 적으세요.")
    token = token or notion.load_token()
    unported = _unported_warning(p, token)

    version = notion.next_version(p.notion_dir, config.KIND)
    # 판본 번호는 notion.json·baseline 파일명에만 남긴다. 페이지 제목이 곧 PDF 본문 제목·머리글이 되므로
    # 제목에 vN 을 붙이지 않는다 (2026-10-11 설계과제1 v2 에서 사용자가 노션에서 지웠다).
    title = config.document_title(n)
    body = strip_title(p.report_md.read_text(encoding="utf-8"), title)
    if _first_line(body).startswith("# "):
        # 노션은 본문 첫 블록이 # 헤딩이면 그 헤딩을 지운다 (docs/notion-probe.md 프로브 1).
        raise SyncBlocked([Finding("error", p.report_md.name,
            "본문 첫 블록이 # 헤딩이다 — 노션이 첫 # 헤딩을 지운다. 맨 위에 제목 줄 "
            "'# 설계 과제 N: …' 을 두거나 헤딩 앞에 문단을 둔다")])
    page = notion.push_markdown(body, parent, token, title=title)
    notion.append_record(p.notion_dir, config.KIND, page["page_id"], page["url"],
                         source=p.report_md.name,
                         when=now or datetime.now().strftime("%Y-%m-%d %H:%M"))
    pulled = notion.pull_markdown(page["page_id"], token)
    p.baseline(version).write_text(pulled, encoding="utf-8", newline="\n")
    return {"title": title, "version": version, "url": page["url"],
            "page_id": page["page_id"], "baseline": p.baseline(version),
            "info": [f for f in findings if f.level in ("info", "warn")] + unported,
            "roundtrip": roundtrip(body, pulled)}


def recover_baselines(n: int, root: Path | None = None, token: str | None = None) -> list[Path]:
    """기록은 있는데 baseline 이 없는 판본만 다시 되읽는다. 업로드는 하지 않는다."""
    root, info, p = _context(n, root)
    missing = [r for r in notion.load_records(p.notion_dir)
               if r.get("kind") == config.KIND and not p.baseline(r["version"]).exists()]
    if not missing:
        return []
    token = token or notion.load_token()
    out = []
    for r in missing:
        path = p.baseline(r["version"])
        path.write_text(notion.pull_markdown(r["page_id"], token), encoding="utf-8", newline="\n")
        out.append(path)
    return out


def _latest_record(p) -> dict:
    records = [r for r in notion.load_records(p.notion_dir) if r.get("kind") == config.KIND]
    if not records:
        raise notion.NotionError(f"업로드 기록이 없습니다: {p.notion_dir / notion.RECORD_NAME}")
    return max(records, key=lambda r: r["version"])


def _text_lines(md: str) -> list[str]:
    """그림 줄은 뺀다 — 노션에서 그림을 넣으면 URL 이 바뀌는데 그것은 본문 수정이 아니다."""
    return [line for line in md.splitlines() if not _IMAGE_LINE.match(line)]


def _diff(p, rec: dict, token: str) -> dict:
    v = rec["version"]
    base = p.baseline(v)
    if not base.exists():
        raise notion.NotionError(f"{base.name} 이 없습니다 — 먼저 `sync recover --n <n>` 로 되읽는다")
    pulled = notion.pull_markdown(rec["page_id"], token)
    p.pulled(v).write_text(pulled, encoding="utf-8", newline="\n")
    lines = list(difflib.unified_diff(_text_lines(base.read_text(encoding="utf-8")),
                                      _text_lines(pulled), base.name, p.pulled(v).name,
                                      n=0, lineterm=""))
    changed = sum(1 for line in lines
                  if line[:1] in "+-" and not line.startswith(("+++", "---")))
    return {"version": v, "url": rec.get("url"), "diff": lines, "changed": changed}


def diff(n: int, root: Path | None = None, token: str | None = None) -> dict:
    """최신 판본 페이지를 되읽어, 올렸을 때의 baseline 과 달라진 텍스트 줄을 돌려준다.

    노션에서 사용자가 직접 고친 내용을 md 로 되돌리기 위한 것이다. 되읽은 md 는 형식이
    달라(인라인 수식 백틱, `<table>`) 자동으로 합치지 않고 diff 만 보여 준다.
    """
    root, info, p = _context(n, root)
    rec = _latest_record(p)
    return _diff(p, rec, token or notion.load_token())


def _unported_warning(p, token: str) -> list[Finding]:
    """직전 판본에 md 로 되돌리지 않은 노션 수정이 있으면 경고 한 줄. 업로드는 막지 않는다."""
    try:
        rec = _latest_record(p)
    except notion.NotionError:
        return []
    try:
        d = _diff(p, rec, token)
    except (notion.NotionError, OSError) as e:
        return [Finding("warn", "노션", f"v{rec['version']} 을 되읽지 못해 노션 수정 여부를 확인하지 못했다: {e}")]
    if not d["changed"]:
        return []
    return [Finding("warn", "노션",
        f"v{d['version']} 에 md 로 되돌리지 않은 노션 수정이 {d['changed']}줄 있다 — "
        "`sync diff` 로 확인하고 md 에 반영했는지 본다")]


def check_images(n: int, root: Path | None = None, token: str | None = None) -> list[Finding]:
    root, info, p = _context(n, root)
    latest = _latest_record(p)
    token = token or notion.load_token()
    text = notion.pull_markdown(latest["page_id"], token)
    p.pulled(latest["version"]).write_text(text, encoding="utf-8", newline="\n")
    return check_pulled_images(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m scripts.ec2_report.sync")
    ap.add_argument("command", choices=("push", "check-images", "diff", "recover"))
    ap.add_argument("--n", type=int, required=True, help="설계과제 번호")
    a = ap.parse_args(argv)
    try:
        if a.command == "push":
            r = push(a.n)
            print(f"업로드: {r['title']} (판본 v{r['version']})")
            print(f"URL: {r['url']}")
            print(f"baseline: {r['baseline']}")
            for f in r["info"]:
                print(f)
            for f in r["roundtrip"]:
                print(f)
            print(f"왕복 검사: {'손실 없음' if not r['roundtrip'] else str(len(r['roundtrip'])) + '건'}")
            return 0
        if a.command == "recover":
            got = recover_baselines(a.n)
            print("\n".join(str(x) for x in got) or "되읽을 판본 없음")
            return 0
        if a.command == "diff":
            d = diff(a.n)
            print("\n".join(d["diff"]))
            print(f"v{d['version']} 노션 수정: " + (f"{d['changed']}줄" if d["changed"] else "없음"))
            return 1 if d["changed"] else 0
        findings = check_images(a.n)
        for f in findings:
            print(f"✗ {f.msg}")
        print("그림 빈자리 없음" if not findings else f"그림 빈자리 {len(findings)}곳")
        return 1 if findings else 0
    except SyncBlocked as e:
        for f in e.findings:
            print(f)
        return 2
    except notion.NotionError as e:
        print(f"노션 오류: {e}")
        return 3
    except (OSError, ValueError, KeyError) as e:
        print(f"설정 오류: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
