"""보고서 md → 노션 새 페이지 (텍스트만), 되읽기 baseline, 그림 빈자리 검사.

    python3 -m scripts.ec2_report.sync push --n 1
    python3 -m scripts.ec2_report.sync check-images --n 1
    python3 -m scripts.ec2_report.sync recover --n 1

종료 코드: 0 성공, 1 그림 빈자리 있음, 2 md 검사 error 로 막힘, 3 노션·설정 오류.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import config, notion
from .check import Finding, check_markdown, check_pulled_images, roundtrip


class SyncBlocked(Exception):
    def __init__(self, findings: list[Finding]):
        super().__init__(f"검사 error {len(findings)}건")
        self.findings = findings


def strip_title(text: str, title: str) -> str:
    """앞쪽 빈 줄 다음 첫 줄이 `# ` 헤딩이면 그 줄과 뒤따르는 빈 줄만 뗀다.

    페이지 제목은 properties 로 따로 주므로 본문의 제목 헤딩은 중복이다.
    """
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i == len(lines) or not lines[i].startswith("# "):
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

    version = notion.next_version(p.notion_dir, config.KIND)
    title = f"{config.document_title(n)} v{version}"
    body = strip_title(p.report_md.read_text(encoding="utf-8"), title)
    page = notion.push_markdown(body, parent, token, title=title)
    notion.append_record(p.notion_dir, config.KIND, page["page_id"], page["url"],
                         source=p.report_md.name,
                         when=now or datetime.now().strftime("%Y-%m-%d %H:%M"))
    pulled = notion.pull_markdown(page["page_id"], token)
    p.baseline(version).write_text(pulled, encoding="utf-8")
    return {"title": title, "version": version, "url": page["url"],
            "page_id": page["page_id"], "baseline": p.baseline(version),
            "info": [f for f in findings if f.level == "info"],
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
        path.write_text(notion.pull_markdown(r["page_id"], token), encoding="utf-8")
        out.append(path)
    return out


def check_images(n: int, root: Path | None = None, token: str | None = None) -> list[Finding]:
    root, info, p = _context(n, root)
    records = [r for r in notion.load_records(p.notion_dir) if r.get("kind") == config.KIND]
    if not records:
        raise notion.NotionError(f"업로드 기록이 없습니다: {p.notion_dir / notion.RECORD_NAME}")
    latest = max(records, key=lambda r: r["version"])
    token = token or notion.load_token()
    text = notion.pull_markdown(latest["page_id"], token)
    p.pulled(latest["version"]).write_text(text, encoding="utf-8")
    return check_pulled_images(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m scripts.ec2_report.sync")
    ap.add_argument("command", choices=("push", "check-images", "recover"))
    ap.add_argument("--n", type=int, required=True, help="설계과제 번호")
    a = ap.parse_args(argv)
    try:
        if a.command == "push":
            r = push(a.n)
            print(f"업로드: {r['title']}")
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


if __name__ == "__main__":
    sys.exit(main())
