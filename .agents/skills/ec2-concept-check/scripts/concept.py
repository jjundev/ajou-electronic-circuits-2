"""Stage, validate and publish a single EC2 concept check."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
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
from source import RUNTIME, describe_inputs, nfc, read, sha, verify_inputs, write

ASSETS = _paths.SKILL / "assets"
TEMPLATE = ASSETS / "review-template.html"
TEMPLATE_HASH = "b8df4750f44ce1e6e4487133049e480cf1be2236d92bd6d8af8a56df2d400927"
BRAND = '<strong class="brand">복습문제</strong>'
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
    if not pack_flow.current_concept_parent(state):
        raise ValueError("parent_final_check_required")
    if repo is not None and nfc(str(repo)) != nfc(state["repo"]):
        raise ValueError("부모 실행과 저장소 경로가 다릅니다.")
    if range_ is not None and range_ != state["range"]:
        raise ValueError("부모 실행과 날짜 범위가 다릅니다.")
    return state


def prepare(run, repo, range_, parent_run, *, candidate_pack: Path | None = None):
    if parent_run and candidate_pack is None:
        state = parent_state(parent_run, repo, range_)
    data = describe_inputs(repo, range_, parent_run, candidate_pack=candidate_pack)
    if parent_run:
        data['parent_run'] = str(parent_run)
        if candidate_pack is None:
            data['parent_attempt'] = state['actions']['final-check']['attempt']
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
    if data.get('candidate_pack'):
        check_candidate(data)
    else:
        verify_inputs(data)
    if data.get("parent_run") and not data.get("candidate_pack"):
        state = parent_state(Path(data["parent_run"]), Path(data["repo"]), data["range"])
        if state["actions"]["final-check"]["attempt"] != data["parent_attempt"]:
            raise ValueError("부모 최종 검사 회차가 바뀌었습니다. 현재 회차로 다시 준비하세요.")
    return items.load(data, run)


def check_candidate(data):
    current = describe_inputs(Path(data['repo']), data['range'], Path(data['parent_run']),
                              candidate_pack=Path(data['candidate_pack']))
    if dict(current, parent_run=data['parent_run']) != data:
        raise ValueError('quiz_input_changed')


def _bind_parent(run, parent_run):
    data = read(run/'source.json')
    if data.get('parent_run') != str(parent_run):
        raise ValueError('quiz_parent_mismatch')
    repo = Path(data['repo'])
    if data.get('candidate_pack'):
        # A replaced note may already have invalidated the public final receipt.
        from pack_flow import inspect_state
        state = inspect_state(parent_run)
        if state.get('publication', {}).get('status') == 'published':
            current = describe_inputs(repo, data['range'], parent_run)
            if current.get('logical_inputs') != data['logical_inputs']:
                raise ValueError('quiz_input_changed')
    state = parent_state(parent_run, repo, data['range'])
    attempt = state['actions']['final-check']['attempt']
    if data.get('parent_attempt', attempt) != attempt:
        raise ValueError('parent_final_check_required')
    if data.get('candidate_pack'):
        check_candidate(data)
    verify_inputs(data)
    current = describe_inputs(repo, data['range'], parent_run)
    if not data.get('candidate_pack') and dict(current, parent_run=str(parent_run), parent_attempt=attempt) != data:
        raise ValueError('quiz_input_changed')
    if current.get('logical_inputs') != data.get('logical_inputs'):
        raise ValueError('quiz_input_changed')
    return dict(parent_run=str(parent_run), parent_attempt=attempt, logical_inputs=current.get('logical_inputs', {}))


def bind_parent_for_publish(run: Path, parent_run: Path) -> dict:
    data = read(run/'source.json')
    with publication_lock(Path(data['pack'])):
        return _bind_parent(run, parent_run)


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
    path.write_text(page, encoding="utf-8", newline="\n")
    return path


def approved_preview(run, data):
    path = preview_page(run, data)
    if path.read_bytes() != render_page(data).encode("utf-8"):
        raise ValueError("미리보기와 현재 빌드가 다릅니다. build부터 다시 실행하세요.")
    return path


def checked_browser(html, browser, data):
    expected_modes = {f"{w}x{h} {t}" for w, h in browser_check.VIEWPORTS for t in browser_check.THEMES}
    passed_modes = {entry["label"] for entry in browser.get("runs", []) if not entry["failures"]
                    and entry["detail"].get("items_checked") == len(data["items"])
                    and entry["detail"].get("hints_checked") == len(data["items"])}
    if (browser.get("sha256") != sha(html) or browser.get("status") != "pass"
            or browser.get("failures") or passed_modes != expected_modes):
        raise ValueError("현재 HTML의 브라우저 4모드 통과 기록이 필요합니다.")

    return expected_modes


def verify_legacy(pack, slug):
    """Recognize a historical publisher's closed bundle and matching HTML bytes."""
    from pack_paths import checked_file
    if not re.fullmatch(r'[A-Za-z0-9_]+', slug):
        raise ValueError('invalid quiz slug')
    stem = f'확인문제_{pack.name}_{slug}'
    html = checked_file(pack, stem + '.html')
    bundle = checked_file(pack, '.pack/자료_' + stem)
    if {p.name for p in bundle.iterdir()} not in (set(EVIDENCE), {*EVIDENCE, 'binding.json'}):
        raise ValueError('unrecognized legacy evidence')
    for name in EVIDENCE:
        checked_file(bundle, name)
    data = read(bundle/'source.json')
    if (data.get('logical_inputs') or (data.get('range'),data.get('slug')) != (pack.name,slug)
            or nfc(Path(data['note']).name) != f'정리노트_{pack.name}_{slug}.html'
            or nfc(Path(data['note_md']).name) != f'정리노트_{pack.name}_{slug}.md'
            or not all(re.fullmatch(r'[0-9a-f]{64}', data['inputs'].get(path,''))
                       for path in (data['note'],data['note_md'],*data['transcripts'].values()))):
        raise ValueError('unrecognized legacy source')
    if (bundle/'binding.json').exists():
        binding = read(checked_file(bundle, 'binding.json'))
        if not data.get('parent_run') or binding != dict(parent_run=data['parent_run'],
                parent_attempt=data['parent_attempt'], logical_inputs={}):
            raise ValueError('unrecognized legacy binding')
    content = items.load(data, bundle)
    browser = read(bundle/'browser.json')
    ledger = read(bundle/'blind-ledger.json')
    if nfc(browser['html']) != nfc(html.name) or blind.errors(content, ledger):
        raise ValueError('legacy evidence mismatch')
    checked_browser(html, browser, content)
    markup = html.read_text(encoding='utf-8')
    model_tag = re.search(r'<script id="review-interaction-model" type="application/json">(.+?)</script>', markup, re.S)
    model = json.loads(model_tag[1]) if model_tag else {}
    if (model.get('documentId') != stem or interaction.validate_model(markup, model)
            or set(model['cards']) != {item['id'] for item in content['items']}):
        raise ValueError('legacy HTML model mismatch')
    objectives = {o['id']:o for o in content['objectives']}
    for index,item in enumerate(content['items'], 1):
        card = render.card_html(item, objectives[item['objective']], index, Path(data['note']).name)
        if card not in markup:
            raise ValueError('legacy HTML item mismatch')


def reviewed_files(run, data):
    preview = approved_preview(run, data)
    problems = blind.errors(data, read(run / "blind-ledger.json"))
    if problems:
        raise ValueError("\n".join(problems))
    browser = read(run/'browser.json')
    expected_modes = checked_browser(preview, browser, data)
    files = [run/name for name in EVIDENCE]
    if data.get('logical_inputs'):
        if browser.get('logical_inputs') != data['logical_inputs']:
            raise ValueError('quiz_input_changed')
        expected = shot_names(data)
        if browser.get('screenshots') != {name: sha(run/'shots'/name) for name in expected}:
            raise ValueError('quiz_browser_evidence_changed')
        visual = run/'visual-review.json'
        review = read(visual)
        views = review.get('views', {})
        if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or set(views) != expected_modes:
            raise ValueError('visual-review requires a named reviewer and four views')
        for mode, view in views.items():
            prefix = mode.replace(' ', '-') + '-'
            shots = {k:v for k,v in browser['screenshots'].items() if k.startswith(prefix)}
            if (view.get('status') != 'pass' or not isinstance(view.get('observation'), str)
                    or not view['observation'].strip() or view.get('screenshots') != shots):
                raise ValueError('visual-review missing current inspection: ' + mode)
        files.append(visual)
        from PIL import Image
        for name in expected:
            path = run/'shots'/name
            size = tuple(map(int, name.split('-', 1)[0].split('x')))
            with Image.open(path) as frame:
                if frame.format != 'PNG' or frame.size != size:
                    raise ValueError('quiz_browser_evidence_changed')
                frame.verify()
            files.append(path)
        files.extend(blind.evidence(run, data, read(run/'blind-ledger.json')))
    return [preview, *files]


def shot_names(data):
    first = data['items'][0]['id']
    return [f'{w}x{h}-{t}-{label}.png' for w,h in browser_check.VIEWPORTS for t in browser_check.THEMES
            for label in ('review', first, first + '-hint', 'last')]


def publish(run, data, *, review_attempt=None, action_attempt=None):
    import pack_flow
    pack = Path(data["pack"])
    parent = Path(data['parent_run']) if data.get('parent_run') else None
    from pack_publication import parent_marker, registered_quiz_inventory, register_attached_quiz
    with (pack_flow._locked(parent) if parent else nullcontext()), publication_lock(pack):
        owner = parent_marker(pack)
        strict = owner.get('strict', False)
        if strict and not (parent and action_attempt and review_attempt):
            raise ValueError('quiz_publish_attempt_changed')
        binding = _bind_parent(run, parent) if parent else None
        state = parent_state(parent) if parent else {}
        review_root = state.get('tasks', {}).get('concept-review', {}).get('attempt_dir')
        if strict or review_attempt or action_attempt or (review_root and run == Path(review_root)/'quiz'):
            from pack_parallel import same_attempt
            claim = state['actions'].get('concept-publish', {})
            if (not strict or not state.get('concept_contract') or state['publication'].get('journal') != owner['journal']
                    or not action_attempt or claim.get('attempt') != action_attempt or claim.get('status') != 'running'
                    or claim.get('input_version', {}).get('final-check') != binding['parent_attempt']):
                raise ValueError('quiz_publish_attempt_changed')
            same_attempt(state, 'concept-publish', action_attempt)
            worker = state['tasks']['concept-review']
            if (worker['status'] != 'done' or worker['attempt'] != review_attempt
                    or Path(worker['attempt_dir'])/'quiz' != run):
                raise ValueError('quiz_review_changed')
        data = load(run)
        reviewed = reviewed_files(run, data)
        if strict:
            accepted = worker['receipt'].get('quiz_files', {})
            if set(accepted) != {nfc(p.relative_to(run).as_posix()) for p in reviewed}:
                raise ValueError('quiz_review_changed')
            original = {str(p):accepted[nfc(p.relative_to(run).as_posix())] for p in reviewed}
        else:
            original = {str(p): sha(p) for p in reviewed}
        preview = reviewed[0]
        browser = read(run/'browser.json')
        from pack_paths import checked_file
        html = checked_file(pack, filename(data))
        bundle = checked_file(pack, '.pack/자료_' + html.stem)
        bundle.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".ec2-concept-", dir=pack) as stage:
            stage = Path(stage)
            staged_bundle = stage / "evidence"
            staged_bundle.mkdir()
            for source_file in reviewed[1:]:
                destination = staged_bundle/source_file.relative_to(run)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, destination)
                if sha(destination) != original[str(source_file)]:
                    raise ValueError('quiz_review_changed')
            files = {str(bundle/p.relative_to(run)): original[str(p)] for p in reviewed[1:]}
            files[str(html)] = original[str(preview)]
            if binding:
                write(staged_bundle/'binding.json', binding)
                files[str(bundle/'binding.json')] = sha(staged_bundle/'binding.json')
            staged_html = stage / html.name
            shutil.copyfile(preview, staged_html)
            if sha(staged_html) != original[str(preview)] or sha(staged_html) != browser["sha256"]:
                raise ValueError("발행 후보 HTML이 브라우저 검사 후 바뀌었습니다.")
            backup = run / "previous" / uuid4().hex
            if html.exists() or bundle.exists():
                if strict:
                    if not registered_quiz_inventory(pack, html, bundle):
                        raise ValueError('unowned_quiz_overlap')
                else:
                    verify_legacy(pack, data['slug'])
                backup.mkdir(parents=True)
                if html.exists():
                    shutil.copy2(html, backup / html.name)
                if bundle.exists():
                    shutil.copytree(bundle, backup / bundle.name)
            displaced = stage / "previous"
            if any(sha(Path(path)) != digest for path,digest in original.items()):
                raise ValueError('quiz_review_changed')
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
            "range": data["range"], "status": "published", "attempt": binding["parent_attempt"] if binding else None,
            "run": str(run), "backup": str(backup) if backup.exists() else None,
            "files": files,
            "items": len(data["items"]),
            "reviewed_files": original, "review_attempt": review_attempt, "action_attempt": action_attempt,
        }
        if strict:
            from pack_publication import quiz_inventory
            installed = quiz_inventory(pack, [html.name, bundle.relative_to(pack).as_posix()])
            observed = {str(pack/name):value for name,value in installed.items() if not name.endswith('/')}
            if observed != files:
                raise ValueError('installed quiz differs from the approved staged bytes')
            register_attached_quiz(pack, receipt, owner['journal'], installed)
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
    start.add_argument("--candidate-pack", type=Path)
    start.add_argument("--run", required=True, type=Path)
    for name in ("check", "build", "blind-make", "blind-record", "blind-status", "browser", "evidence", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--run", required=True, type=Path)
        if name == "publish":
            command.add_argument("--review-attempt")
            command.add_argument("--action-attempt")
        if name == "blind-make":
            command.add_argument("--out", required=True, type=Path)
            command.add_argument("--only", nargs="+")
        if name == "blind-record":
            command.add_argument("--packet", type=Path)
            command.add_argument("--author")
            command.add_argument("--solver")
            command.add_argument("--answers", required=True, type=Path)
            command.add_argument("--round", required=True, type=int, choices=(1, 2, 3))
    legacy = commands.add_parser('verify-legacy')
    legacy.add_argument('--pack', required=True, type=Path)
    legacy.add_argument('--slug', required=True)
    withheld = commands.add_parser("withhold")
    withheld.add_argument("--parent-run", required=True, type=Path)
    withheld.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify-legacy":
            verify_legacy(args.pack, args.slug)
            return 0
        if args.command == "withhold":
            parent_run = args.parent_run.resolve()
            import pack_flow
            state = pack_flow.load_state(parent_run)
            public = Path(state['repo'])/'복습노트'/state['range']
            with pack_flow._locked(parent_run), publication_lock(public):
                state = parent_state(parent_run)
                if not args.reason.strip():
                    raise ValueError('quiz withholding reason required')
                record_parent(parent_run, {"range": state["range"], "status": "withheld", "reason": args.reason,
                                           "attempt": state["actions"]["final-check"]["attempt"]})
            return 0
        run = args.run.resolve()
        if args.command == "prepare":
            print(prepare(run, args.repo.resolve(), args.range, args.parent_run.resolve() if args.parent_run else None,
                          candidate_pack=args.candidate_pack.resolve() if args.candidate_pack else None))
            return 0
        if args.command == 'publish':
            print(publish(run, read(run/'source.json'), review_attempt=args.review_attempt, action_attempt=args.action_attempt))
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
            if data.get('logical_inputs'):
                blind.issue(data, run, args.out)
            else:
                blind.packet(data, args.out)
            print(args.out / "문제.md")
        elif args.command == "blind-record":
            write(ledger, blind.record(data, args.answers, ledger, args.round, packet_dir=args.packet,
                                       author=args.author, solver=args.solver))
        elif args.command == "blind-status":
            records = read(ledger)
            problems = blind.errors(data, records)
            if problems:
                raise ValueError("\n".join(problems))
            if data.get('logical_inputs'):
                blind.evidence(run, data, records)
            print("OK")
        elif args.command == "browser":
            path = approved_preview(run, data)
            report = browser_check.check(path, run / "browser.json", run / "shots", source=data)
            if report['status'] == 'pass' and data.get('logical_inputs'):
                report['logical_inputs'] = data['logical_inputs']
                report['screenshots'] = {name: sha(run/'shots'/name) for name in shot_names(data)}
                write(run/'browser.json', report)
            print("browser:", report["status"])
            for failure in report["failures"]:
                print(failure, file=sys.stderr)
            return int(report["status"] != "pass")
        elif args.command == "evidence":
            print(json.dumps([str(p) for p in reviewed_files(run, data)]))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ParseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
