"""Read-only self-check for one `author-<sid>` fragment before handoff.

The fragment is assembled alone into `<attempt>/probe/preview.html` with the
regular note template, checked with the same structural diagnostics as the
assembled note, and measured with the layout probe. The result is written to
`<attempt>/probe/probe.json`. RUN state is never written.
"""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import re

import pack_flow as f

AUTHOR = 'author-'
WIDTHS = '1280,375'
THEMES = 'light,dark'


# layout_probe exits 2 for any exception. Only these reasons mean no browser could run:
# the Playwright import, and browser_runtime.launch_chromium's per-candidate failures.
_UNAVAILABLE = re.compile(r"^(No module named '(playwright|browser_runtime|vendor_route)\b"
                          r"|Playwright Chromium: |Google Chrome: )")


def run_layout(preview: Path, out: Path):
    """Run layout_probe on the preview; return (exit_code, report), report={'error': reason} on exit 2."""
    import layout_probe
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        code = layout_probe.main([str(preview), '--widths', WIDTHS, '--themes', THEMES, '--out', str(out)])
    if code in (0, 1):
        return code, json.loads(out.read_text(encoding='utf-8')) if out.is_file() else None
    reason = None
    for line in reversed(printed.getvalue().splitlines()):
        try:
            reason = json.loads(line).get('reason')
            break
        except (ValueError, AttributeError):
            continue
    return code, {'error': reason or printed.getvalue().strip()[:240] or 'layout probe failed'}


def browser_unavailable(reason) -> bool:
    return isinstance(reason, str) and bool(_UNAVAILABLE.match(reason))


def _defects(report) -> int:
    report = report or {}
    count = sum(len(c.get('overflow', [])) + len(c.get('label_gaps', [])) for c in report.get('checks', []))
    return count + len(report.get('circuits', []))


def _assembly_only_links(manifest: dict, sid: str) -> set[str]:
    """Hrefs that resolve only in the full assembled note, never in a one-section preview."""
    import manifest as manifest_mod
    names = {manifest_mod.problem_pdf_name(manifest), manifest_mod.answer_pdf_name(manifest),
             manifest_mod.note_name(manifest)}
    # Manifest links (cross-note, workbook PDFs) are relative to the published pack and are
    # owned by scope-draft/scope-final, as in pack_parallel.machine_report.
    names |= {link['href'] for link in manifest.get('links', [])}
    # In-page anchors to other sections and their topics exist only after assembly.
    anchors = {'#' + x for s in manifest['sections'] if s['id'] != sid
               for x in (s['id'], *(t['id'] for t in s.get('topics', [])))}
    return names | anchors


def _excluded(code: str, detail: str, allowed: set[str]) -> bool:
    return code == 'broken-link' and (detail in allowed or detail.partition('#')[0] in allowed)


def _note_builder():
    """This skill's assemble.build_note; workbook/assemble.py shares the module name."""
    import importlib.util
    import sys
    path = Path(__file__).resolve().with_name('assemble.py')
    loaded = sys.modules.get('assemble')
    if loaded is not None and Path(getattr(loaded, '__file__', '') or '.').resolve() == path:
        return loaded.build_note
    spec = importlib.util.spec_from_file_location('ec2_review_pack_assemble', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_note


def fragment_probe(run: Path, task_id: str, attempt: str, *, layout=None) -> dict:
    from pack_parallel import common_diagnostics
    build_note = _note_builder()
    run = Path(run)
    state = f.load_state(run)
    task = state['tasks'].get(task_id)
    if task is None or not task_id.startswith(AUTHOR) or task.get('role') != 'author':
        raise f.FlowError('probe is only for author-<section> tasks: ' + task_id)
    f._attempt(task, attempt)
    sid = task_id[len(AUTHOR):]
    root = Path(task['attempt_dir'])
    fragment = root / 'sections' / (sid + '.html')
    if not fragment.is_file():
        raise f.FlowError('fragment missing: ' + str(fragment))
    manifest = f._read(f._read(task['brief'])['manifest'])
    sections = [s for s in manifest['sections'] if s['id'] == sid]
    if len(sections) != 1:
        raise f.FlowError('section not in the brief manifest: ' + sid)
    folder = root / 'probe'
    folder.mkdir(exist_ok=True)
    details, preview, out = folder / 'probe.json', folder / 'preview.html', folder / 'layout.json'
    for stale in (details, out):
        stale.unlink(missing_ok=True)
    fragment_sha = f._sha(fragment)
    markup = build_note(dict(manifest, sections=sections), root)
    preview.write_text(markup, encoding='utf-8', newline='\n')
    _, diagnostics = common_diagnostics(markup, preview, None)
    if not re.search(r'<svg\b', fragment.read_text(encoding='utf-8'), re.I):
        # The circuit walk requires at least one topic figure, which a whole note always has
        # somewhere; a figure-free section alone is measured as an ordinary page instead.
        markup = re.sub(r'(<body\b[^>]*?)\s+data-circuits="[^"]*"', r'\1', markup, count=1)
    preview.write_text(markup, encoding='utf-8', newline='\n')
    allowed = _assembly_only_links(manifest, sid)
    problems = [dict(code=code, where=sid, detail=detail) for code, detail in sorted(diagnostics)
                if not _excluded(code, detail, allowed)]
    code, report = (layout or run_layout)(preview, out)
    if code in (0, 1):
        if report is not None and not out.is_file():
            f._atomic_json(out, report)
        defects = _defects(report)
        status = 'defects' if code == 1 or defects else 'pass'
        view = dict(status=status, defects=defects, report=str(out) if out.is_file() else None)
    else:  # 2: no browser, or the page could not be loaded or measured
        reason = (report or {}).get('error')
        if reason is None:  # a layout runner that reported nothing: no browser evidence either way
            view = dict(status='unavailable', defects=0, report=None)
        else:
            f._atomic_json(out, dict(error=reason))
            missing = browser_unavailable(reason)
            view = dict(status='unavailable' if missing else 'defects', defects=0 if missing else 1,
                        report=str(out))
    result = dict(schema_version=1, task_id=task_id, attempt=attempt, fragment_sha256=fragment_sha,
                  problems=problems, layout=view,
                  status='pass' if not problems and view['status'] in ('pass', 'unavailable') else 'defects')
    if f._sha(fragment) != fragment_sha:
        raise f.FlowError('fragment changed during probe')
    f._atomic_json(details, result)
    return result
