"""Explicit dependency graph for opt-in parallel review packs."""
from dataclasses import dataclass
import copy
from typing import Literal

import pack_flow as f
from pack_findings import blocked_reason


@dataclass(frozen=True)
class TaskSpec:
    id: str
    kind: Literal['worker', 'action']
    direct_inputs: tuple[str, ...]
    required_approvals: tuple[str, ...]
    outputs: tuple[str, ...]

    @property
    def dependencies(self):
        return tuple(dict.fromkeys((*self.direct_inputs, *self.required_approvals)))


def task_specs(state: dict) -> tuple[TaskSpec, ...]:
    specs = []

    def worker(name, inputs=(), outputs=(), approvals=()):
        specs.append(TaskSpec(name, 'worker', tuple(inputs), tuple(approvals), tuple(outputs)))

    def action(name, inputs=(), outputs=(), approvals=()):
        specs.append(TaskSpec(name, 'action', tuple(inputs), tuple(approvals), tuple(outputs)))

    worker('source-prep', outputs=('source-map.json', 'slides.txt'))
    action('candidate-index', outputs=('candidates.json', 'catalog/index.json'))
    action('render-preflight', outputs=('render-preflight.json', 'render-preflight.pdf'))
    if not f._done(state, 'source-prep'):
        return tuple(specs)
    summaries = []
    for date in state['sessions']:
        summaries.append('stt-' + date)
        worker(summaries[-1], ('source-prep',), (f'summaries/stt-{date}.md',))
    worker('scope-draft', summaries, ('scope.json', 'manifest.json'))
    if not f._done(state, 'scope-draft'):
        return tuple(specs)
    sections = state['scope_sections']
    authors = []
    for section in sections:
        sid = section['id']
        authors.append('author-' + sid)
        if sid not in state.get('link_sections', []):
            worker(authors[-1], ('scope-draft',), (f'sections/{sid}.html',))
    worker('selection', ('scope-draft', 'candidate-index'),
           ('manifest.json', 'selection.json', 'selection-review.json', 'display-titles.json'))
    if not f._done(state, 'selection'):
        return tuple(specs)
    ids = state['selected_ids']
    worker('scope-final', ('scope-draft', 'selection'), ('manifest.json',))
    for sid in state.get('link_sections', []):
        worker('author-' + sid, ('scope-draft', 'scope-final'), (f'sections/{sid}.html',))
    action('assemble-note', ('scope-final', *authors), ('note HTML',))
    action('structural-precheck', ('assemble-note',), ('check-findings.json',))
    worker('style-audit', ('assemble-note',), ('learning-style-audit-note.json',))
    worker('content-review', ('assemble-note',), ('learning-style-audit-note.json',))
    problem_pdf = ()
    pdf_qa = ()
    if ids:
        action('stage-problem-index', ('selection',), ('problem index', 'questions.json'))
        worker('explain-author', ('stage-problem-index',),
               tuple(f'explanations/p{i}.html' for i in range(1, len(ids) + 1)))
        worker('explain-blind', ('stage-problem-index',), ('independent.json',))
        worker('child-coordinator', ('stage-problem-index', 'explain-author', 'explain-blind'),
               ('child/child-receipt.json',))
        action('explain-verify', ('stage-problem-index',), ('explanation bundle',), ('child-coordinator',))
        action('build-problems', ('stage-problem-index', 'render-preflight'), ('problem PDF',))
        action('build-answers', ('stage-problem-index', 'explain-verify', 'render-preflight'), ('answer PDF',))
        worker('pdf-qa', ('build-answers',), ('answer-review.json', 'answer-review.md'))
        problem_pdf, pdf_qa = ('build-problems',), ('pdf-qa',)
    action('precheck', ('assemble-note', 'structural-precheck', *problem_pdf), approvals=('style-audit', 'content-review'))
    worker('browser-qa', ('assemble-note', *problem_pdf, 'precheck'), ('work/browser/report.json',))
    action('convert-md', ('assemble-note', *problem_pdf, 'precheck'), ('note MD', 'emitted SVGs'))
    svg = ()
    if f._done(state, 'convert-md') and state['converted_assets']['svgs']:
        worker('standalone-svg-qa', ('assemble-note', 'convert-md'),
               ('work/standalone-svg-qa/report.json', 'work/standalone-svg-qa/report.md'))
        svg = ('standalone-svg-qa',)
    action('publish-pack', ('convert-md',), ('publication journal',), ('browser-qa', *svg, *pdf_qa))
    action('final-check', ('publish-pack',), ('current public proof',))
    return tuple(specs)


def targets(state, tid):
    if tid.startswith('stt-'): return [tid[4:]]
    if tid.startswith('author-'): return [tid[7:]]
    if tid in ('style-audit', 'content-review', 'browser-qa'):
        return [topic['id'] for section in state['scope_sections'] for topic in section['topics']]
    if tid == 'standalone-svg-qa':
        return [item['path'] for item in state['converted_assets']['svgs']]
    if tid in ('explain-author', 'explain-blind', 'child-coordinator', 'pdf-qa'):
        return state['selected_ids']
    if tid == 'scope-final': return [section['id'] for section in state['scope_sections']]
    return state['sessions']


def refresh(state):
    for spec in task_specs(state):
        group = state['tasks' if spec.kind == 'worker' else 'actions']
        row = group.setdefault(spec.id, dict(id=spec.id, status='pending'))
        dependencies = list(spec.dependencies)
        if row.get('dependencies', dependencies) != dependencies and row['status'] == 'done':
            row['status'] = 'stale'
        row['dependencies'] = dependencies
        if spec.kind == 'worker':
            role = 'author' if spec.id.startswith('author-') else 'stt' if spec.id.startswith('stt-') else spec.id
            row.update(role=role, targets=targets(state, spec.id))
            row.setdefault('brief', None)
            row.setdefault('attempt', None)
            row.setdefault('receipt', None)
    return state


def ready_work(state: dict, *, slots: int) -> dict:
    if type(slots) is not int or slots < 0:
        raise f.FlowError('slots must be a nonnegative integer')
    state = f._current(copy.deepcopy(state))
    specs = task_specs(state)
    descendants = {spec.id: set() for spec in specs}
    for spec in reversed(specs):
        for dep in spec.dependencies:
            descendants[dep].update((spec.id, *descendants[spec.id]))
    result = dict(kind='parallel', actions=[], dispatch=[], blocked=[], waiting=[], revision=state['revision'])
    for spec in sorted(specs, key=lambda s: (-len(descendants[s.id]), s.id)):
        record = f._record(state, spec.id)
        status = record.get('status', 'pending')
        if status == 'done': continue
        if state.get('stale_inputs') or state['status'] in ('withheld', 'recovery_required', 'blocked'):
            result['blocked'].append((spec.id, 'RUN requires attention'))
        elif status == 'recovery_required':
            result['blocked'].append((spec.id, 'reconcile this attempt'))
        elif status in ('blocked', 'needs_fix') or (record and spec.kind == 'worker' and f._owner(state, record) == 'unavailable'):
            result['blocked'].append((spec.id, status if status in ('blocked', 'needs_fix') else 'inspection unavailable'))
        elif status in ('running', 'claimed') or record.get('invalidated_active'):
            result['waiting'].append((spec.id, 'active attempt'))
        elif pending := [dep for dep in spec.dependencies if not f._done(state, dep)]:
            result['waiting'].append((spec.id, pending))
        elif reason := blocked_reason(state, spec.id):
            result['blocked'].append((spec.id, reason))
        elif spec.id == 'final-check':
            result['waiting'].append((spec.id, 'grouped with publish-pack'))
        elif spec.kind == 'action':
            result['actions'].append(spec.id)
        elif record and f._owner(state, record) == 'main':
            result.setdefault('review_locally', []).append(spec.id)
        elif len(result['dispatch']) < slots:
            result['dispatch'].append(spec.id)
        else:
            result['waiting'].append((spec.id, 'worker slots'))
    return result
