"""Stage, validate and publish a single EC2 concept check."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import quote
from uuid import uuid4
from xml.etree.ElementTree import ParseError

import _paths
import browser_check
import interaction
import blind
import items
import render
from pack_publication import publication_lock
from source import describe_inputs, nfc, read, sha, verify_inputs, write

ASSETS = _paths.SKILL / "assets"
TEMPLATE = ASSETS / "review-template.html"
TEMPLATE_HASH = "b8df4750f44ce1e6e4487133049e480cf1be2236d92bd6d8af8a56df2d400927"
BRAND = '<strong class="brand">복습문제</strong>'
RUNTIME = ("pretendard/pretendard.css", "katex/katex.min.css", "katex/katex.min.js",
           "katex/contrib/auto-render.min.js")
EVIDENCE = ("source.json", "objectives.json", "items.json", "blind-ledger.json", "browser.json")


def filename(data):
    return f"확인문제_{data['range']}_{data['slug']}.html"


def preview_page(run, data):
    return run / "preview" / "복습노트" / data["range"] / filename(data)


def vendor_path(data):
    return Path(data["repo"]) / _paths.VENDOR_REL


def parent_state(parent_run, repo=None, range_=None):
    import pack_flow
    state = pack_flow.inspect_state(parent_run)
    if (state["status"] != "complete" or state["actions"].get("final-check", {}).get("status") != "done"
            or not state.get("concept_check_enabled")):
        raise ValueError("신규 복습팩의 현재 final-check 성공 기록이 필요합니다.")
    if repo is not None and nfc(str(repo)) != nfc(state["repo"]):
        raise ValueError("부모 실행과 저장소 경로가 다릅니다.")
    if range_ is not None and range_ != state["range"]:
        raise ValueError("부모 실행과 날짜 범위가 다릅니다.")
    return state


def prepare(run, repo, range_, parent_run):
    if parent_run:
        state = parent_state(parent_run, repo, range_)
    data = describe_inputs(repo, range_, parent_run)
    if parent_run:
        data.update(parent_run=str(parent_run), parent_attempt=state["actions"]["final-check"]["attempt"])
    run.mkdir(parents=True, exist_ok=True)
    source_file = run / "source.json"
    # Resuming uses the original snapshot so a changed note cannot inherit an earlier review.
    if source_file.exists():
        if read(source_file) != data:
            raise ValueError(f"RUN의 원래 근거가 현재 입력과 다릅니다. 새 RUN을 사용하세요: {run}")
    else:
        if any(run.iterdir()):
            raise ValueError(f"비어 있는 RUN이 필요합니다: {run}")
        write(source_file, data)
    return source_file


def load(run):
    data = read(run / "source.json")
    verify_inputs(data)
    if data.get("parent_run"):
        state = parent_state(Path(data["parent_run"]), Path(data["repo"]), data["range"])
        if state["actions"]["final-check"]["attempt"] != data["parent_attempt"]:
            raise ValueError("부모 최종 검사 회차가 바뀌었습니다. 현재 회차로 다시 준비하세요.")
    return items.load(data, run)


def render_page(data):
    if sha(TEMPLATE) != TEMPLATE_HASH:
        raise ValueError("자구알 원본 HTML 템플릿 해시가 다릅니다.")
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count(BRAND) != 1:
        raise ValueError("원본 템플릿의 상단 제목 위치를 확인하세요.")
    vendor = vendor_path(data)
    for asset in RUNTIME:
        if not (vendor / asset).is_file():
            raise ValueError(f"로컬 자원 누락: {vendor / asset}")
    note = Path(data["note"]).name
    by_id = {obj["id"]: obj for obj in data["objectives"]}
    cards = "".join(render.card_html(it, by_id[it["objective"]], index, note)
                    for index, it in enumerate(data["items"], 1))
    range_ = data["range"]
    title = f"{range_} 확인문제 — 이번 수업 개념 확인"
    asset_root = quote(Path(os.path.relpath(vendor, data["pack"])).as_posix(), safe="/")
    slots = {
        "ASSET_ROOT": asset_root,
        "PAGE_TITLE": render.esc(f"전자회로2 확인문제 {range_}"),
        "DESCRIPTION": render.esc(title),
        "TITLE": render.esc(title),
        "NOTE_HREF": render.esc(note),
        "TOC": '<a href="#check">확인</a>',
        "INTRO": f"이번 수업에서 처음 배운 개념을 {len(data['items'])}문항으로 확인해요. 보기를 고르면 바로 채점돼요. 숫자 답은 입력한 뒤 ‘답 확인’을 눌러요.",
        "PARTS": f'<section id="check"><h2>확인문제</h2>{cards}</section>',
        "FOOTER": ("<p>AI가 강의자료와 수업 전사를 바탕으로 만든 문항이에요.</p>"
                   f'<p>라이선스 <a href="{asset_root}/pretendard/LICENSE" download="Pretendard-LICENSE.txt">Pretendard</a> · '
                   f'<a href="{asset_root}/katex/LICENSE" download="KaTeX-LICENSE.txt">KaTeX</a></p>'),
        "SCRIPTS": "",
        "RANGE": render.esc(f"{range_}-확인"),
    }
    page = re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: slots[match[1]], template)
    page = page.replace(BRAND, '<strong class="brand">확인문제</strong>')
    return interaction.install(page, filename(data).removesuffix(".html"))


def link(source, target):
    if target.is_symlink() and target.resolve() == source.resolve():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source.resolve(), target_is_directory=source.is_dir())


def build(run, data):
    page = render_page(data)
    path = preview_page(run, data)
    path.parent.mkdir(parents=True, exist_ok=True)
    link(vendor_path(data), run / "preview" / _paths.VENDOR_REL)
    note = Path(data["note"])
    link(note, path.parent / note.name)
    path.write_text(page, encoding="utf-8")
    return path


def approved_preview(run, data):
    path = preview_page(run, data)
    if path.read_bytes() != render_page(data).encode("utf-8"):
        raise ValueError("미리보기와 현재 빌드가 다릅니다. build부터 다시 실행하세요.")
    return path


def publish(run, data):
    pack = Path(data["pack"])
    with publication_lock(pack):
        data = load(run)
        preview = approved_preview(run, data)
        problems = blind.errors(data, read(run / "blind-ledger.json"))
        if problems:
            raise ValueError("\n".join(problems))
        browser = read(run / "browser.json")
        expected_modes = {f"{w}x{h} {t}" for w, h in browser_check.VIEWPORTS for t in browser_check.THEMES}
        passed_modes = {entry["label"] for entry in browser.get("runs", []) if not entry["failures"]
                        and entry["detail"].get("items_checked") == len(data["items"])
                        and entry["detail"].get("hints_checked") == len(data["items"])}
        if (browser.get("sha256") != sha(preview) or browser.get("status") != "pass"
                or browser.get("failures") or passed_modes != expected_modes):
            raise ValueError("현재 HTML의 브라우저 4모드 통과 기록이 필요합니다.")

        html = pack / filename(data)
        bundle = pack / ".pack" / f"자료_{html.stem}"
        bundle.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".ec2-concept-", dir=pack) as stage:
            stage = Path(stage)
            staged_bundle = stage / "evidence"
            staged_bundle.mkdir()
            for name in EVIDENCE:
                shutil.copyfile(run / name, staged_bundle / name)
            staged_html = stage / html.name
            shutil.copyfile(preview, staged_html)
            if sha(staged_html) != browser["sha256"]:
                raise ValueError("발행 후보 HTML이 브라우저 검사 후 바뀌었습니다.")
            backup = run / "previous" / uuid4().hex
            if html.exists() or bundle.exists():
                backup.mkdir(parents=True)
                if html.exists():
                    shutil.copy2(html, backup / html.name)
                if bundle.exists():
                    shutil.copytree(bundle, backup / bundle.name)
            displaced = stage / "previous"
            verify_inputs(data)
            if bundle.exists():
                bundle.rename(displaced)
            try:
                staged_bundle.rename(bundle)
                os.replace(staged_html, html)
            except BaseException:
                if bundle.exists():
                    shutil.rmtree(bundle)
                if displaced.exists():
                    displaced.rename(bundle)
                raise
        receipt = {
            "range": data["range"], "status": "published", "attempt": data.get("parent_attempt"),
            "run": str(run), "backup": str(backup) if backup.exists() else None,
            "files": {str(p): sha(p) for p in [html, *(bundle / name for name in EVIDENCE)]},
            "items": len(data["items"]),
        }
        if data.get("parent_run"):
            record_parent(Path(data["parent_run"]), receipt)
        return html


def record_parent(parent_run, receipt):
    state = parent_state(parent_run, range_=receipt["range"])
    if receipt["attempt"] != state["actions"]["final-check"]["attempt"]:
        raise ValueError("부모 최종 검사 회차가 바뀌었습니다.")
    import pack_flow
    pack_flow._atomic_json(parent_run / "concept-check-result.json", receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("prepare")
    start.add_argument("range")
    start.add_argument("--repo", type=Path, default=_paths.REPO)
    start.add_argument("--parent-run", type=Path)
    start.add_argument("--run", required=True, type=Path)
    for name in ("check", "build", "blind-make", "blind-record", "blind-status", "browser", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True, type=Path)
        if name == "blind-make":
            command.add_argument("--out", required=True, type=Path)
            command.add_argument("--only", nargs="+")
        if name == "blind-record":
            command.add_argument("--answers", required=True, type=Path)
            command.add_argument("--round", required=True, type=int, choices=(1, 2, 3))
    withheld = commands.add_parser("withhold")
    withheld.add_argument("--parent-run", required=True, type=Path)
    withheld.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "withhold":
            parent_run = args.parent_run.resolve()
            state = parent_state(parent_run)
            record_parent(parent_run, {"range": state["range"], "status": "withheld", "reason": args.reason,
                                       "attempt": state["actions"]["final-check"]["attempt"]})
            return 0
        run = args.run.resolve()
        if args.command == "prepare":
            print(prepare(run, args.repo.resolve(), args.range, args.parent_run.resolve() if args.parent_run else None))
            return 0
        data = load(run)
        ledger = run / "blind-ledger.json"
        if args.command == "check":
            print("OK")
        elif args.command == "build":
            print(build(run, data))
        elif args.command == "blind-make":
            if args.only:
                selected = set(args.only)
                data["items"] = [it for it in data["items"] if it["id"] in selected]
                if {it["id"] for it in data["items"]} != selected:
                    raise ValueError("블라인드 재검토 문항 ID를 확인하세요.")
            blind.packet(data, args.out)
            print(args.out / "문제.md")
        elif args.command == "blind-record":
            write(ledger, blind.record(data, args.answers, ledger, args.round))
        elif args.command == "blind-status":
            problems = blind.errors(data, read(ledger))
            if problems:
                raise ValueError("\n".join(problems))
            print("OK")
        elif args.command == "browser":
            path = approved_preview(run, data)
            report = browser_check.check(path, run / "browser.json", run / "shots", source=data)
            print("browser:", report["status"])
            for failure in report["failures"]:
                print(failure, file=sys.stderr)
            return int(report["status"] != "pass")
        elif args.command == "publish":
            print(publish(run, data))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ParseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
