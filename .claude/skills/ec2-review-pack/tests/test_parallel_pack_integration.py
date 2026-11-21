"""Isolated end-to-end trials. All worker judgments in this file are synthetic."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pymupdf

from _util import REPO, SCRIPTS, prepare_mini_run
from pack_support import add_target_judgments, genuine_child_run
from problem_index import record_selection


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False))


def child_fixture(code, *args):
    """The child and parent suites both provide a module named _util."""
    helper = REPO / '.claude/skills/ec2-problem-explain/tests'
    subprocess.run([sys.executable, '-c', 'import sys; from pathlib import Path; '
                    'sys.path.insert(0,sys.argv[1]); ' + code, helper, *args], check=True)


class Trial:
    def __init__(self, root, *, problem=False, existing=False, lab=False):
        self.root, self.repo, self.run = root, root/'repo', root/'run'
        self.public = self.repo/'복습노트/0909'
        self.problem = problem
        self.lab = lab
        for name in ('교과서/마이크로전자회로/_tools', 'from_the_past/md/_tools',
                     'workbook/templates', '.claude/skills/ec2-problem-explain',
                     '.claude/skills/ec2-review-pack/scripts', '복습노트/.assets/vendor'):
            shutil.copytree(REPO/name, self.repo/name)
        for module in (REPO/'workbook').glob('*.py'):
            shutil.copyfile(module, self.repo/'workbook'/module.name)
        profile = Path('.claude/skills/ec2-review-pack/references/solution-style.md')
        (self.repo/profile).parent.mkdir()
        shutil.copyfile(REPO/profile, self.repo/profile)
        self.stt = self.repo/'STT/0909 전회2.md'
        self.stt.parent.mkdir()
        self.stt.write_text('합성 테스트 강의')
        self.pdf = self.repo/'slides.pdf'
        with pymupdf.open() as doc:
            doc.new_page()
            doc.save(self.pdf)
        if problem:
            child_fixture('from _util import _copy_problem; _copy_problem("P10.01", Path(sys.argv[2]))',
                          self.repo)
        if existing:
            self.public.mkdir(parents=True)
            (self.public/'정리노트_0909_Previous.html').write_text('Previous published note')
            (self.public/'personal.txt').write_text('Personal file')
        self.fixture = prepare_mini_run(root/'fixture', self.repo)
        self.manifest = read(self.fixture/'manifest.json')
        self.manifest.update(range='0909', selection_policy='exam-first-v2', problems=[], links=[],
                             link_sections=['s2'])
        self.manifest['sessions'][0].update(date='0909', stt='STT/0909 전회2.md')
        if problem:
            self.manifest['problems'] = [dict(id='P10.01', kind='장말문제', anchor='s1-mean',
                date='0909', why='합성 테스트', priority='core', estimated_minutes=5, learning_goals=['이득'])]
            self.manifest['links'] = [dict(topic='s2-links', href=f'복습문제_0909_Mini_Test-{kind}.pdf')
                                      for kind in ('문제','답안')]
        self.cli('init', '--repo', self.repo, '--range', '0909',
                 '--browser-owner', 'workers', '--pdf-owner', 'workers', '--allow-tmp')

    def cli(self, *args, error=False):
        proc = subprocess.run([sys.executable, SCRIPTS/'pack_cli.py', *args, '--run', self.run],
                              capture_output=True, text=True)
        result = json.loads(proc.stdout)
        assert proc.returncode == int(error), (args, result, proc.stderr)
        return result

    def action(self, name):
        self.cli('run', '--action', name)

    def next(self):
        return self.cli('next', '--slots', '20')['next']

    def report(self):
        return read(self.cli('report')['details_path'])

    def prepare_note(self):
        self.action('candidate-index')
        for tid in ('source-prep', 'stt-0909', 'scope-draft', 'author-why', 'author-s1',
                    'selection', 'scope-final', 'author-s2'):
            self.worker(tid)
        self.action('assemble-note')
        self.action('structural-precheck')
        self.worker('content-review')
        self.worker('style-audit')

    def convert(self):
        self.action('precheck')
        self.action('convert-md')

    def worker(self, tid, *, edit=None):
        claim = self.cli('task', 'claim', '--task', tid)['next']
        brief = read(claim['brief'])
        task = ('--task', tid, '--attempt', claim['attempt'])
        self.cli('task', 'bind', *task, '--agent-id', 'synthetic-' + tid)
        outputs = list(map(Path, brief['required_outputs']))
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        self.produce(tid, brief, outputs)
        report = Path(brief['report'])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('Synthetic integration fixture judgment.')
        submission = dict(status='done', report=str(report), outputs=[str(p) for p in outputs if p.is_file()],
                          reviews=[str(report), *[str(p) for p in outputs if p.name == 'report.json']],
                          counts=dict(targets=brief['targets']), unresolved=[])
        if edit:
            edit(brief, submission)
        if 'approval_plan' in brief:
            add_target_judgments(brief, submission)
        submission_path = Path(brief['run'])/'submission.json'
        write(submission_path, submission)
        self.cli('task', 'build-receipt', *task, '--submission', submission_path)
        self.cli('task', 'check', *task, '--receipt', brief['receipt'])
        self.cli('task', 'accept', *task, '--receipt', brief['receipt'])
        return brief

    def produce(self, tid, brief, outputs):
        if tid == 'child-coordinator':
            genuine_child_run(self.root, existing=(self.repo, self.run), lab=self.lab)
            return
        if tid in ('explain-author', 'explain-blind'):
            question, = read(brief['questions'])['problems']
            if tid == 'explain-author':
                child_fixture('from _util import fragment; from types import SimpleNamespace; import json; '
                              'Path(sys.argv[3]).write_text(fragment(SimpleNamespace(subparts=json.loads(sys.argv[2]))))',
                              json.dumps(question['subparts']), outputs[0])
                if brief.get('repair_findings'):
                    # A synthetic correction: new bytes for the reopened fragment.
                    outputs[0].write_text(outputs[0].read_text() + '\n' * (1 + len(brief['repair_findings'][0]['repairs'])))
            else:
                write(outputs[0], dict(items={f'p1:{key}':dict(reviewer='synthetic-explain-blind',
                    method='exact', conclusion='1=1', evidence='synthetic independent fixture')
                    for key in question['subparts']}))
            return
        for path in outputs:
            if path.name == 'source-map.json':
                write(path, dict(schema_version=1, sessions=[dict(date='0909', stt=str(self.stt),
                     pdfs=[str(self.pdf)], status='ready', missing=[])]))
            elif path.name == 'manifest.json':
                write(path, self.manifest)
            elif path.name in ('selection.json', 'selection-review.json'):
                catalog = read(brief['candidates'])
                review = dict(policy='exam-first-v2', catalog_sha256=catalog['catalog_sha256'],
                              candidates=[], coverage=[])
                if self.problem:
                    review['candidates'] = [dict(id='P10.01', disposition='selected', scope='in_scope', reason='합성 테스트')]
                    review['coverage'] = [dict(goal='이득', problem_ids=['P10.01'])]
                write(path, review if path.name == 'selection-review.json' else record_selection(self.manifest, catalog, review))
            elif path.name == 'display-titles.json':
                write(path, {'P10.01':'Fixture gain'} if self.problem else {})
            elif path.name == 'learning-style-audit-note.json':
                audit = read(self.fixture/'learning-style-audit.json')
                for item in audit['items'].values():
                    item['reviewer'] = 'synthetic-' + tid
                write(path, audit)
            elif path.suffix == '.html':
                raw = (self.fixture/'sections'/path.name).read_text().replace('0101 수업', '0909 수업')
                # No generated SVG in this fixture. The ordinary note UI and topic quizzes still run.
                raw = re.sub(r'<div class="widget" .*?(?=<div class="quiz after">)', '', raw, flags=re.S)
                raw = re.sub(r'<script id="widget-mean-ui">.*?</script>', '', raw, flags=re.S)
                if not self.problem:
                    raw = re.sub(r'<ul><li><a href="{{PROBLEM_PDF}}">.*?</ul>',
                                 '<p>이번 범위에는 복습문제가 없어요.</p>', raw, flags=re.S)
                path.write_text(raw)
            else:
                write(path, {})


def public_files(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_parallel_full_pack_accepts_only_current_evidence(tmp_path):
    trial = Trial(tmp_path, problem=True, lab=True)
    trial.prepare_note()
    trial.action('stage-problem-index')
    trial.worker('explain-author')
    trial.worker('explain-blind')
    trial.worker('child-coordinator')
    trial.action('explain-verify')
    trial.action('render-preflight')
    trial.action('build-problems')
    trial.action('build-answers')
    brief = trial.worker('pdf-qa')
    trial.convert()
    trial.worker('browser-qa')
    state = read(trial.run/'run-status.json')
    independent = state['tasks']['explain-blind']['receipt']['fresh_approvals']
    lost = 'pdf-page:1'
    previous = next(entry for entry in state['approval_ledger']
                    if entry['attempt'] == brief['attempt'] and entry['target'] == lost)
    Path(previous['screen']).unlink()
    assert 'publish-pack' not in trial.next()['actions']
    renewed = trial.worker('pdf-qa')
    assert set(renewed['approval_plan']['pending']) == {lost}
    trial.action('publish-pack')
    final_report = trial.report()
    assert final_report['status'] == 'complete'
    for name in ('정리노트_0909_Mini_Test.html', '.assets/정리노트_0909_Mini_Test.md',
                 '복습문제_0909_Mini_Test-문제.pdf', '복습문제_0909_Mini_Test-답안.pdf',
                 '문제설명_0909_Mini_Test.html'):
        assert (trial.public/name).is_file()
    lab = trial.public / '.assets/자료_문제설명_0909_Mini_Test/labs/P10.01/index.html'
    assert lab.is_file()
    assert 'data-ec2-problem-lab' in (trial.public/'문제설명_0909_Mini_Test.html').read_text()
    tasks = read(trial.run/'run-status.json')['tasks']
    assert tasks['explain-blind']['receipt']['fresh_approvals'] == independent
    accepted = tasks['pdf-qa']['receipt']
    assert lost not in accepted['reused_approvals']
    assert accepted['fresh_approvals'][lost]['attempt'] == renewed['attempt']


def test_zero_problem_pack_still_offers_quiz(tmp_path):
    trial = Trial(tmp_path)
    trial.prepare_note()
    trial.convert()
    trial.action('concept-draft')
    assert 'concept-review' in trial.next()['dispatch']
    brief = read(trial.cli('task', 'claim', '--task', 'concept-review')['next']['brief'])
    assert (Path(brief['quiz_run'])/'source.json').is_file()
    assert 'pdf-qa' not in read(trial.run/'run-status.json')['tasks']


def test_zero_svgs_never_skips_required_html_review(tmp_path):
    trial = Trial(tmp_path)
    trial.prepare_note()
    trial.convert()
    state = read(trial.run/'run-status.json')
    assert state['converted_assets']['svgs'] == []
    ready = trial.next()
    assert 'browser-qa' in ready['dispatch'] and 'standalone-svg-qa' not in state['tasks']
    assert 'publish-pack' not in ready['actions']
    trial.worker('browser-qa')
    assert 'publish-pack' in trial.next()['actions']


def test_regeneration_keeps_public_pack_until_verified_publish(tmp_path):
    trial = Trial(tmp_path, existing=True)
    original = public_files(trial.public)
    trial.prepare_note()
    trial.convert()
    trial.worker('browser-qa')
    assert public_files(trial.public) == original
    state = read(trial.run/'run-status.json')
    md = Path(state['converted_assets']['md']['path'])
    # Moving the physical producer output invalidates the adopted path even with identical bytes.
    moved = md.rename(md.with_suffix('.moved'))
    rejected = trial.cli('run', '--action', 'publish-pack', error=True)
    assert public_files(trial.public) == original
    assert rejected['error_code'] == 'stale_inputs'
    moved.rename(md)
    trial.action('publish-pack')
    assert (trial.public/'정리노트_0909_Mini_Test.html').is_file()
    assert not (trial.public/'정리노트_0909_Previous.html').exists()
    assert (trial.public/'personal.txt').read_bytes() == original['personal.txt']


# Coordinator → explain-author repair route. Every judgment below is synthetic.
COORDINATOR_DEFECT = dict(rule='content/retry', target='P10.01', defect='retry step repeats the solve step',
                          severity='Important', owner_task='explain-author',
                          evidence='synthetic: fragment retry block compared with solve block')


def coordinator_judgment(trial, *, unresolved=(), fix_results=()):
    """Submit a coordinator judgment through the real CLI receipt path."""
    def edit(brief, submission):
        if unresolved:
            Path(submission['report']).write_text('## Important\n' + ''.join(
                f"- [{x['target']}] [{x['rule']}] {x['defect']}\n" for x in unresolved))
            submission.update(status='needs-fix', outputs=[], unresolved=list(unresolved))
        if fix_results:
            pending = brief['recheck_findings']
            submission['fix_results'] = [dict(finding_id=row['id'], request_id=row['pending_request'],
                                              attempt=row['repair_attempt'], outcome=outcome,
                                              evidence='synthetic: corrected fragment re-read')
                                         for row, outcome in zip(pending, fix_results)]
    if unresolved:
        # A negative judgment needs no ready child bucket.
        trial.produce = lambda tid, brief, outputs, original=trial.produce: (
            None if tid == 'child-coordinator' else original(tid, brief, outputs))
    try:
        return trial.worker('child-coordinator', edit=edit)
    finally:
        trial.__dict__.pop('produce', None)


def fix_coordinator_findings(trial, rid):
    rows = [r for r in read(trial.run/'run-status.json')['findings'].values()
            if r['review_id'] == 'child-coordinator' and r['status'] == 'open']
    request = trial.run/(rid + '.json')
    write(request, dict(id=rid, items=[dict(finding_id=r['id'], review_attempt=r['review_attempt'],
                                            input_digest=r['input_digest']) for r in rows]))
    trial.cli('task', 'fix', '--request', request)
    return rows


def coordinator_trial(root):
    trial = Trial(root, problem=True)
    trial.prepare_note()
    trial.action('stage-problem-index')
    trial.worker('explain-author')
    trial.worker('explain-blind')
    return trial


def test_coordinator_findings_reopen_only_explain_author(tmp_path):
    trial = coordinator_trial(tmp_path)
    blind = read(trial.run/'run-status.json')['tasks']['explain-blind']['attempt']
    first = coordinator_judgment(trial, unresolved=[COORDINATOR_DEFECT])
    state = read(trial.run/'run-status.json')
    row, = state['findings'].values()
    assert (row['review_id'], row['owner_task'], row['status']) == ('child-coordinator', 'explain-author', 'open')
    assert row['input_digest'] == first['candidate_digest'] == state['tasks']['child-coordinator']['candidate_digest']
    assert state['tasks']['child-coordinator']['status'] == 'needs_fix'
    assert 'child-coordinator' not in trial.next()['dispatch']
    trial.cli('task', 'claim', '--task', 'child-coordinator', error=True)

    fix_coordinator_findings(trial, 'coordinator-fix-1')
    tasks = read(trial.run/'run-status.json')['tasks']
    assert tasks['explain-author']['status'] == 'stale'
    assert tasks['child-coordinator']['status'] == 'stale'
    assert tasks['explain-blind']['status'] == 'done' and tasks['explain-blind']['attempt'] == blind
    assert trial.next()['dispatch'] == ['explain-author']
    repaired = trial.worker('explain-author')
    assert [r['id'] for r in repaired['repair_findings']] == [row['id']]
    assert set(repaired['previous_outputs']) == {'explanations/p1.html'}

    second = coordinator_judgment(trial, fix_results=['resolved'])
    pending, = second['recheck_findings']
    assert pending['repair_attempt'] == read(trial.run/'run-status.json')['tasks']['explain-author']['attempt']
    assert second['candidate_digest'] != first['candidate_digest']
    state = read(trial.run/'run-status.json')
    assert state['findings'][row['id']]['status'] == 'resolved'
    assert state['tasks']['child-coordinator']['status'] == 'done'
    assert state['tasks']['explain-blind']['attempt'] == blind
    assert 'explain-verify' in trial.next()['actions']


def test_coordinator_finding_unresolved_twice_is_withheld(tmp_path):
    trial = coordinator_trial(tmp_path)
    coordinator_judgment(trial, unresolved=[COORDINATOR_DEFECT])
    for attempt in (1, 2):
        row, = fix_coordinator_findings(trial, f'coordinator-fix-{attempt}')
        trial.worker('explain-author')
        coordinator_judgment(trial, unresolved=[COORDINATOR_DEFECT], fix_results=['unresolved'])
        row = read(trial.run/'run-status.json')['findings'][row['id']]
        assert len(row['unsuccessful_attempts']) == attempt
    assert row['status'] == 'withheld'
    assert 'child-coordinator' not in trial.next()['dispatch']


def test_coordinator_must_not_be_the_explanation_author(tmp_path):
    trial = coordinator_trial(tmp_path)
    claim = trial.cli('task', 'claim', '--task', 'child-coordinator')['next']
    brief = read(claim['brief'])
    task = ('--task', 'child-coordinator', '--attempt', claim['attempt'])
    trial.cli('task', 'bind', *task, '--agent-id', 'synthetic-explain-author')
    report = Path(brief['report'])
    report.write_text('## Important\n- [P10.01] [content/retry] retry step repeats the solve step\n')
    submission = Path(brief['run'])/'submission.json'
    write(submission, dict(status='needs-fix', report=str(report), outputs=[], reviews=[str(report)],
                           counts=dict(targets=brief['targets']), unresolved=[COORDINATOR_DEFECT]))
    rejected = trial.cli('task', 'build-receipt', *task, '--submission', submission, error=True)
    assert 'authored' in rejected['reason']
    assert 'findings' not in read(trial.run/'run-status.json') or not read(trial.run/'run-status.json')['findings']


def test_legacy_coordinator_needs_fix_without_findings_is_redispatched(tmp_path):
    trial = coordinator_trial(tmp_path)
    coordinator_judgment(trial, unresolved=[COORDINATOR_DEFECT])
    # Recreate the state adopted by the earlier runner: needs_fix, no ledger entry, no candidate.
    state = read(trial.run/'run-status.json')
    state['tasks']['child-coordinator'].pop('candidate_digest')
    state['findings'] = {}
    write(trial.run/'run-status.json', state)
    assert 'child-coordinator' in trial.next()['dispatch']
    brief = coordinator_judgment(trial, unresolved=[COORDINATOR_DEFECT])
    assert brief['recheck_findings'] == []
    state = read(trial.run/'run-status.json')
    assert [r['review_id'] for r in state['findings'].values()] == ['child-coordinator']
    # With a ledger finding it waits for task fix instead of looping.
    assert 'child-coordinator' not in trial.next()['dispatch']
