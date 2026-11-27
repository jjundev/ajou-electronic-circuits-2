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
from note_assemble import note_module  # re-exported for callers

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
        # A single section of a circuit note may draw no figure; the whole note's browser-qa keeps
        # that guard. Every topic screen is still walked, and any figures it has are measured.
        code = layout_probe.main([str(preview), '--widths', WIDTHS, '--themes', THEMES, '--out', str(out),
                                  '--allow-no-figures'])
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

def fragment_probe(run: Path, task_id: str, attempt: str, *, layout=None) -> dict:
    from pack_parallel import common_diagnostics, fragment_owns, metadata_diagnostics
    note_assemble = note_module()
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
    preview_manifest = dict(manifest, sections=sections)
    markup = note_assemble.build_note(preview_manifest, root)
    preview.write_text(markup, encoding='utf-8', newline='\n')
    _, diagnostics = common_diagnostics(markup, preview, None)
    # Charge the author only what machine_report would route to author-<sid>: manifest-field
    # diagnostics belong to scope-draft and template-only ones to assemble-note.
    own = common_diagnostics(note_assemble.read_fragment(fragment, manifest), preview, None)
    metadata = metadata_diagnostics(preview_manifest, preview, None)
    allowed = _assembly_only_links(manifest, sid)
    problems = [dict(code=code, where=sid, detail=detail) for code, detail in sorted(diagnostics)
                if not _excluded(code, detail, allowed) and fragment_owns(code, detail, own, metadata)]
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
