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

import pack_flow as f

AUTHOR = 'author-'
WIDTHS = '1280,375'
THEMES = 'light,dark'


def run_layout(preview: Path, out: Path):
    """Run layout_probe on the preview; return (exit_code, report or None)."""
    import layout_probe
    with contextlib.redirect_stdout(io.StringIO()):
        code = layout_probe.main([str(preview), '--widths', WIDTHS, '--themes', THEMES, '--out', str(out)])
    report = json.loads(out.read_text(encoding='utf-8')) if code in (0, 1) and out.is_file() else None
    return code, report


def _defects(report) -> int:
    report = report or {}
    count = sum(len(c.get('overflow', [])) + len(c.get('label_gaps', [])) for c in report.get('checks', []))
    return count + len(report.get('circuits', []))


def _assembly_only_links(manifest: dict, sid: str) -> set[str]:
    """Hrefs that resolve only in the full assembled note, never in a one-section preview."""
    import manifest as manifest_mod
    names = {manifest_mod.problem_pdf_name(manifest), manifest_mod.answer_pdf_name(manifest),
             manifest_mod.note_name(manifest)}
    # In-page anchors to other sections and their topics exist only after assembly.
    anchors = {'#' + x for s in manifest['sections'] if s['id'] != sid
               for x in (s['id'], *(t['id'] for t in s.get('topics', [])))}
    return names | anchors


def _excluded(code: str, detail: str, allowed: set[str]) -> bool:
    return code == 'broken-link' and (detail in allowed or detail.partition('#')[0] in allowed)


def fragment_probe(run: Path, task_id: str, attempt: str, *, layout=None) -> dict:
    from assemble import build_note
    from pack_parallel import common_diagnostics
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
    else:  # 2: no browser or the page could not be measured
        view = dict(status='unavailable', defects=0, report=None)
    result = dict(schema_version=1, task_id=task_id, attempt=attempt, fragment_sha256=fragment_sha,
                  problems=problems, layout=view,
                  status='pass' if not problems and view['status'] in ('pass', 'unavailable') else 'defects')
    if f._sha(fragment) != fragment_sha:
        raise f.FlowError('fragment changed during probe')
    f._atomic_json(details, result)
    return result
