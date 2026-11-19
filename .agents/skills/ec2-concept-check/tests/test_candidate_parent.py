"""Small synthetic fixtures for the candidate/publication boundary."""
from pathlib import Path
import json
import shutil
import sys

import pytest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL/'scripts'))
import concept
import source
import pack_flow
import pack_publication as publication
from pack_paths import PackPaths


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


@pytest.fixture
def parent(tmp_path, monkeypatch):
    repo, run = tmp_path/'repo', tmp_path/'parent'
    candidate = run/'converted/복습노트/0909'
    note = put(candidate/'정리노트_0909_Test.html', '<article class="topic" id="gain">Gain</article>')
    md = put(candidate/'.assets/정리노트_0909_Test.md', 'Gain')
    summary = put(run/'adopted/stt.md', 'Synthetic STT summary')
    m = put(run/'adopted/manifest.json', json.dumps(dict(range='0909', slug='Test', problems=[],
                    sections=[dict(topics=[dict(id='gain')])])))
    selection = put(run/'adopted/selection.json', '{"problems":[]}')
    put(repo/'STT/0909 전회2.md', 'Synthetic transcript')
    shutil.copytree(SKILL.parents[2]/'복습노트/.assets/vendor', repo/'복습노트/.assets/vendor')
    audit = put(run/'audit.json', '{}')
    def row(artifacts):
        return dict(status='done', attempt='fixture', artifacts={k:str(p) for k,p in artifacts.items()})
    state = dict(repo=str(repo), range='0909', run=str(run), workflow='parallel', concept_contract=1,
                 status='ready', concept_check_enabled=True, stale_inputs=[], selected_ids=[], active_audit=str(audit),
                 tasks={'scope-final':row({'manifest.json':m}), 'selection':row({'selection.json':selection}),
                        'stt-0909':row({'summaries/stt-0909.md':summary})},
                 actions={'convert-md':dict(row({}), candidate_root=str(candidate)),
                          'assemble-note':row({'note':note}), 'final-check':{'status':'pending'}},
                 converted_assets={'note':dict(path=str(note),sha256=source.sha(note)),
                                   'md':dict(path=str(md),sha256=source.sha(md)), 'svgs':[]})
    monkeypatch.setattr(pack_flow, 'inspect_state', lambda _:state)
    import pack_findings
    monkeypatch.setattr(pack_findings, 'current_audit', lambda s:bool(s.get('active_audit')))
    return repo, run, candidate, state


def finalize(parent, tmp_path):
    repo, run, candidate, state = parent
    paths = PackPaths(repo, repo/'복습노트/0909', candidate)
    import pack_files
    result = publication.publish_pack(paths, tmp_path/'install', expected={},
                candidate_inventory=pack_files.inventory_at(candidate, '0909'), verify=lambda _:None, retire_concept=True)
    state.update(status='complete', publication=result)
    state['actions']['publish-pack'] = dict(status='done', attempt='new-final')
    state['actions']['final-check'].update(status='done', attempt='new-final')
    return paths.public_pack


def test_prepare_before_parent_final_then_publish_after(parent, tmp_path):
    repo, run, candidate, state = parent
    quiz = tmp_path/'quiz'
    assert concept.prepare(quiz, repo, '0909', run, candidate_pack=candidate).is_file()
    assert not (repo/'복습노트/0909/확인문제_0909_Test.html').exists()
    with pytest.raises(ValueError, match='parent_final_check_required'):
        concept.bind_parent_for_publish(quiz, run)
    finalize(parent, tmp_path)
    assert concept.bind_parent_for_publish(quiz, run)['parent_attempt'] == 'new-final'


def test_parent_note_change_refuses_early_quiz(parent, tmp_path):
    repo, run, candidate, state = parent
    quiz = tmp_path/'quiz'
    concept.prepare(quiz, repo, '0909', run, candidate_pack=candidate)
    public = finalize(parent, tmp_path)
    (public/'정리노트_0909_Test.html').write_text('<article class="topic" id="gain">Changed</article>')
    with pytest.raises(ValueError, match='quiz_input_changed'):
        concept.bind_parent_for_publish(quiz, run)


@pytest.mark.parametrize('interrupted', [False, True])
def test_old_quiz_not_visible_after_changed_parent(tmp_path, monkeypatch, interrupted):
    repo, run, candidate = tmp_path/'repo', tmp_path/'install', tmp_path/'candidate'
    date = '1118'
    slug = 'Feedback_Loading'
    public = repo/'복습노트'/date
    public.mkdir(parents=True)
    legacy = SKILL.parents[2]/'복습노트'/date
    stem = '확인문제_' + date + '_' + slug
    old = public/(stem+'.html')
    shutil.copyfile(legacy/old.name, old)
    bundle = public/'.pack'/('자료_'+stem)/'source.json'
    shutil.copytree(legacy/'.pack'/('자료_'+stem), bundle.parent)
    before = (old.read_bytes(), bundle.read_bytes())
    other = put(public/'.pack/unrelated/source.json', 'sibling')
    put(candidate/'정리노트_1118_Test.html', 'new parent')
    paths = PackPaths(repo, public, candidate)
    opts = dict(expected=publication.publication_inventory(public, date),
                candidate_inventory=publication.publication_inventory(candidate, date),
                verify=lambda _:None, retire_concept=True)
    if interrupted:
        original = publication._mutate
        def stop(*args):
            original(*args)
            raise OSError('fixture interruption')
        with monkeypatch.context() as m:
            m.setattr(publication, '_mutate', stop)
            result = publication.publish_pack(paths, run, **opts)
        assert result['status'] == 'recovery_required'
        result = publication.reconcile_publication(paths, Path(result['journal']), verify=opts['verify'])
        assert result['status'] == 'restored'
        assert old.is_file() and bundle.is_file()
        run = tmp_path/'retry'
    result = publication.publish_pack(paths, run, **opts)
    assert result['status'] == 'published'
    assert not old.exists() and not bundle.exists()
    archive = Path(result['journal']).parent/'before'
    assert (archive/old.name).read_bytes() == before[0]
    assert (archive/bundle.relative_to(public)).read_bytes() == before[1]
    assert other.read_text() == 'sibling'


def test_candidate_rejects_forged_copy_and_lost_review(parent, tmp_path):
    repo, run, candidate, state = parent
    duplicate = tmp_path/'duplicate'
    shutil.copytree(candidate, duplicate)
    with pytest.raises(ValueError, match='quiz_candidate_required'):
        concept.prepare(tmp_path/'quiz', repo, '0909', run, candidate_pack=duplicate)
    state.pop('active_audit')
    with pytest.raises(ValueError, match='quiz_candidate_required'):
        concept.prepare(tmp_path/'quiz', repo, '0909', run, candidate_pack=candidate)


def test_quiz_cannot_bind_an_earlier_parent_with_identical_bytes(parent, tmp_path):
    repo, run, candidate, state = parent
    quiz = tmp_path/'quiz'
    concept.prepare(quiz, repo, '0909', run, candidate_pack=candidate)
    public = finalize(parent, tmp_path)
    paths = PackPaths(repo, public, candidate)
    inventory = publication.publication_inventory(public, '0909')
    result = publication.publish_pack(paths, tmp_path/'another-parent', expected=inventory,
            candidate_inventory=inventory, verify=lambda _:None, retire_concept=True)
    assert result['status'] == 'published'
    with pytest.raises(ValueError, match='parent_final_check_required'):
        concept.bind_parent_for_publish(quiz, run)


def test_independent_response_needs_current_question_packet(tmp_path):
    import blind
    quiz = tmp_path/'quiz'
    quiz.mkdir()
    item = dict(id='q1', title='Test', objective='o1', stem_html='<p>2+2?</p>', format='short',
                answer={'canonical':'4'},hint='add')
    data = dict(logical_inputs={'note':'fixture'}, items=[item], objectives=[{'id':'o1'}])
    packet = tmp_path/'sealed'
    blind.issue(data, quiz, packet)
    answers = put(tmp_path/'answers.md', '| q1 | 4 | |')
    ledger = quiz/'blind-ledger.json'
    with pytest.raises(ValueError, match='independent'):
        blind.record(data, answers, ledger, 1, packet_dir=packet, author='writer', solver='writer')
    item['stem_html'] = '<p>3+1?</p>'
    with pytest.raises(ValueError, match='packet'):
        blind.record(data, answers, ledger, 1, packet_dir=packet, author='writer', solver='solver')


def test_accepted_worker_withholding_reports_reason_for_current_parent(parent, tmp_path):
    repo, run, candidate, state = parent
    finalize(parent, tmp_path)
    report = put(run/'quiz-worker/report.md', 'fixture review has an unresolved independent answer')
    proof = dict(status='withheld', unresolved=['q2 has an unresolved independent answer'],
                 verified_files=[dict(path=str(report),sha256=source.sha(report))])
    state['tasks']['concept-review'] = dict(status='blocked', attempt='review', receipt=proof,
                                           dependencies=['concept-draft'],input_version={'concept-draft':'draft'})
    state['actions']['concept-draft'] = dict(status='done', attempt='draft')
    result = pack_flow.concept_check_result(state)
    assert result and result['status'] == 'withheld' and 'q2' in result['reason']
    assert pack_flow.concept_progress(state)['attempt'] == 'new-final'
    state['actions']['concept-draft']['attempt'] = 'new-draft'
    assert pack_flow.concept_check_result(state) is None


def test_replaced_final_attempt_cannot_bind_without_new_publication(parent, tmp_path):
    repo, run, candidate, state = parent
    quiz = tmp_path/'quiz'
    concept.prepare(quiz, repo, '0909', run, candidate_pack=candidate)
    finalize(parent, tmp_path)
    state['actions']['final-check']['attempt'] = 'different'
    with pytest.raises(ValueError, match='parent_final_check_required'):
        concept.bind_parent_for_publish(quiz, run)


def test_only_read_vendor_resources_invalidate_quiz(parent, tmp_path):
    repo, run, candidate, state = parent
    quiz = tmp_path/'quiz'
    concept.prepare(quiz, repo, '0909', run, candidate_pack=candidate)
    put(repo/'복습노트/.assets/vendor/unrelated/notes.txt', 'a different course asset')
    public = finalize(parent, tmp_path)
    assert concept.bind_parent_for_publish(quiz, run)['parent_attempt'] == 'new-final'
    put(public.parent/'.assets/vendor/pretendard/woff2/Pretendard-Regular.woff2', 'changed font')
    with pytest.raises(ValueError, match='quiz_input_changed'):
        concept.bind_parent_for_publish(quiz, run)


@pytest.mark.parametrize('damage', ['empty', 'injected', 'figure', 'wrong-question', 'extra-item'])
def test_exact_sealed_packet_projection(tmp_path, damage):
    import blind
    quiz = tmp_path/'quiz'
    quiz.mkdir()
    item = dict(id='q1', title='Question', objective='o1', stem_html='<p>2+2?</p>', format='short',
                figure_svg='<svg>fixture</svg>', answer={'canonical':'4'}, hint='add')
    data = dict(logical_inputs={'note':'fixture'}, items=[item], objectives=[{'id':'o1'}])
    packet = tmp_path/'sealed'
    blind.issue(data, quiz, packet)
    answers = put(tmp_path/'answers.md', '| q1 | 4 | |')
    ledger = blind.record(data, answers, quiz/'blind-ledger.json', 1, packet_dir=packet, author='a', solver='s')
    archive = blind.issued_path(quiz, packet)
    issued = source.read(archive/'issued.json')
    if damage == 'empty':
        issued['files'] = {}
    elif damage == 'figure':
        issued['files'].pop('q1.svg')
    elif damage == 'extra-item':
        issued['questions'].append(dict(id='q99', title='Answer is four', format='short', stem_html='<p>4</p>'))
        issued['items']['q99'] = 'fabricated'
        for name,content in blind.packet_contents(issued['questions']).items():
            (archive/'packet'/name).write_bytes(content)
        issued['files'] = {p.name:source.sha(p) for p in (archive/'packet').iterdir()}
    else:
        target = archive/'packet'/('answer.txt' if damage == 'injected' else '문제.md')
        put(target, 'answer is four')
        issued['files'][target.name] = source.sha(target)
    source.write(archive/'issued.json', issued)
    ledger['q1']['issued_sha256'] = source.sha(archive/'issued.json')
    with pytest.raises(ValueError, match='packet'):
        blind.evidence(quiz, data, ledger)


def test_pin_the_actual_interaction_assets(parent):
    import interaction
    repo, run, candidate, state = parent
    data = source.describe_inputs(repo, '0909', run, candidate_pack=candidate)
    for name in ('review-interaction.css', 'review-prompt.js', 'review-interaction.js'):
        assert data['logical_inputs'].get('interaction/'+name) == source.sha(interaction.SKILL/'assets'/name)


def test_manual_quiz_and_unpaired_evidence_survive_parent(tmp_path):
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    manual = put(public/'확인문제_0909_Manual.html', 'manual notes')
    orphan = put(public/'.pack/자료_확인문제_0909_Orphan/custom.txt', 'private notes')
    candidate = tmp_path/'candidate'
    put(candidate/'정리노트_0909_New.html', 'new note')
    paths = PackPaths(repo, public, candidate)
    result = publication.publish_pack(paths, tmp_path/'install', expected=publication.publication_inventory(public,'0909'),
               candidate_inventory=publication.publication_inventory(candidate,'0909'), verify=lambda _:None, retire_concept=True)
    assert result['status'] == 'published'
    assert manual.read_text() == 'manual notes' and orphan.read_text() == 'private notes'

def test_manual_overlap_conflicts_before_parent_write(tmp_path):
    repo = tmp_path/'repo'
    public = repo/'복습노트/0909'
    orphan = put(public/'확인문제_0909_Test.html', 'manual')
    candidate = tmp_path/'candidate'
    put(candidate/'정리노트_0909_Test.html', 'new note')
    result = publication.publish_pack(PackPaths(repo, public, candidate), tmp_path/'install',
                        expected=publication.publication_inventory(public,'0909'),
                        candidate_inventory=publication.publication_inventory(candidate,'0909'),
                        verify=lambda _:None, retire_concept=True)
    assert result['status'] == 'conflict' and orphan.read_text() == 'manual'
    assert not (public/'정리노트_0909_Test.html').exists()

def test_rewritten_legacy_html_is_not_a_managed_quiz(tmp_path):
    date, slug = '1118', 'Feedback_Loading'
    fixture = SKILL.parents[2]/'복습노트'/date
    public = tmp_path/'repo/복습노트'/date
    stem = f'확인문제_{date}_{slug}'
    html = put(public/(stem+'.html'), 'my personal quiz')
    bundle = public/'.pack'/('자료_'+stem)
    shutil.copytree(fixture/'.pack'/('자료_'+stem), bundle)
    browser = source.read(bundle/'browser.json')
    browser['sha256'] = source.sha(html)
    source.write(bundle/'browser.json', browser)
    assert publication.publication_inventory(public,date) == {}


def test_interaction_change_invalidates_prepared_render(parent, tmp_path, monkeypatch):
    import interaction
    repo, run, candidate, state = parent
    renderer = tmp_path/'renderer'
    shutil.copytree(interaction.SKILL/'assets', renderer/'assets')
    monkeypatch.setattr(interaction, 'SKILL', renderer)
    quiz = tmp_path/'quiz'
    draft = concept.prepare(quiz,repo,'0909',run,candidate_pack=candidate)
    script = renderer/'assets/review-prompt.js'
    script.write_bytes(script.read_bytes()+b'\n// changed\n')
    with pytest.raises(ValueError, match='quiz_input_changed'):
        concept.check_candidate(source.read(draft))


def test_standalone_can_replace_its_own_verified_publication(parent, tmp_path):
    repo, _, candidate, _ = parent
    shutil.copytree(candidate, repo/'복습노트/0909')
    quiz = tmp_path/'standalone'
    concept.prepare(quiz,repo,'0909',None)
    objective = dict(id='o1',topic_id='gain',concept='fixture',source=dict(date='0909',stt='line 1',slide='s1'))
    source.write(quiz/'objectives.json', dict(range='0909',slug='Test', objectives=[objective]))
    item = dict(id='q1',objective='o1',format='short',title='합성 문제',stem_html='<p>1+1은?</p>',
                hint='하나를 더하세요.',answer=dict(canonical='2',accepted=[]),solution=['1에 1을 더하면 2예요.'])
    source.write(quiz/'items.json',dict(items=[item]))
    answer = put(tmp_path/'answer.md','| q1 | 2 | |')
    for command in (['blind-record','--answers',str(answer),'--round','1'], ['build'], ['browser'], ['publish'], ['publish']):
        assert concept.main([*command,'--run',str(quiz)]) == 0
    assert (repo/'복습노트/0909/확인문제_0909_Test.html').is_file()


@pytest.mark.parametrize('change', ['revised', 'removed'])
def test_unaccepted_multi_item_packet_must_be_reissued_after_sibling_change(tmp_path, change):
    import blind
    quiz, packet = tmp_path/'quiz', tmp_path/'packet'
    quiz.mkdir()
    first = dict(id='q1',title='First',objective='o1',stem_html='<p>1+1?</p>',format='short',
                 answer={'canonical':'2'},hint='add')
    second = dict(first,id='q2',title='Second',stem_html='<p>2+2?</p>',answer={'canonical':'4'})
    data = dict(logical_inputs={'note':'fixture'}, items=[first,second], objectives=[{'id':'o1'}])
    blind.issue(data,quiz,packet)
    answers = put(tmp_path/'answers.md','| q1 | 2 | |\n| q2 | 4 | |')
    ledger = blind.record(data,answers,quiz/'blind-ledger.json',1,packet_dir=packet,author='author',solver='solver')
    if change == 'revised':
        second['stem_html'] = '<p>2+3?</p>'
    else:
        data['items'].pop()
    # q1 alone still has a matching item digest; its recipient saw the combined sheet.
    assert not blind.errors(dict(data,items=[first]), ledger)
    with pytest.raises(ValueError, match='full current source'):
        blind.evidence(quiz,data,ledger)


def test_uncertified_local_solver_history_requires_recorded_responses(tmp_path):
    import blind
    quiz = tmp_path/'quiz'
    quiz.mkdir()
    item = dict(id='q1',title='First',objective='o1',stem_html='<p>1+1?</p>',format='short',
                answer={'canonical':'2'},hint='add')
    data = dict(logical_inputs={'note':'fixture'}, items=[item], objectives=[{'id':'o1'}])
    answers = put(tmp_path/'answers.md','| q1 | 2 | |')
    ledger = quiz/'blind-ledger.json'
    for number,solver in enumerate(('A','B','C'),1):
        packet = tmp_path/f'packet-{number}'
        blind.issue(data,quiz,packet)
        rows = blind.record(data,answers,ledger,number,packet_dir=packet,author='writer',solver=solver)
        source.write(ledger, rows)
        assert rows['q1']['solvers'] == list('ABC'[:number])
        blind.evidence(quiz,data,rows)
        for malformed in ([], [solver,solver], ['invented',solver], ['   ',solver], ['wrong-final']):
            with pytest.raises(ValueError,match='solver history'):
                blind.evidence(quiz,data,{'q1':dict(rows['q1'], solvers=malformed)})
    with pytest.raises(ValueError,match='solver history'):
        blind.evidence(quiz,data,{'q1':dict(rows['q1'], solvers=['C'])})


@pytest.mark.parametrize('certified_first', [False, True])
@pytest.mark.parametrize('damage', ['missing', 'modified', 'resealed', 'intact'])
def test_solver_can_correct_unsuccessful_second_round_before_third_approval(tmp_path, monkeypatch, certified_first, damage):
    import blind
    quiz = tmp_path/'quiz'
    quiz.mkdir()
    item = dict(id='q1',title='First',objective='o1',stem_html='<p>1+1?</p>',format='short',
                answer={'canonical':'2'},hint='add')
    data = dict(logical_inputs={'note':'fixture'}, items=[item], objectives=[{'id':'o1'}])
    ledger = quiz/'blind-ledger.json'
    archives = []
    for number,solver,answer in ((1,'A','2'),(2,'B','5'),(3,'C','4')):
        item.update(stem_html=f'<p>{number}+1?</p>', figure_svg=f'<svg><text>{number}</text></svg>',
                    answer={'canonical':str(number + 1)})
        packet = tmp_path/f'packet-{number}'
        blind.issue(data,quiz,packet)
        archives.append(blind.issued_path(quiz,packet)/'packet')
        answers = put(tmp_path/'answers.md',f'| q1 | {answer} | |')
        rows = blind.record(data,answers,ledger,number,packet_dir=packet,author='writer',solver=solver)
        source.write(ledger,rows)
        if certified_first and number == 1:
            monkeypatch.setattr(blind,'inherited_rows',lambda *_args, approved=rows:approved)
    assert rows['q1']['solvers'] == ['A','B','C'] and not blind.errors(data,rows)
    if damage == 'intact':
        evidence = set(blind.evidence(quiz,data,rows))
        for archive in archives[1:] if certified_first else archives:
            assert {archive/'문제.md', archive/'q1.svg'} <= evidence
    else:
        if damage == 'missing':
            (archives[1]/'문제.md').unlink()
        else:
            (archives[1]/'q1.svg').write_text('<svg>changed</svg>')
        if damage == 'resealed':
            # Even a consistent chain of file receipts must reproduce B's own questions.
            issue = archives[1].parent/'issued.json'
            issued = source.read(issue)
            issued['files']['q1.svg'] = source.sha(archives[1]/'q1.svg')
            source.write(issue,issued)
            latest = (quiz/rows['q1']['proof']).with_name('submission.json')
            event = source.read(latest)
            ref = event['previous']['q1']
            previous = (quiz/ref['proof']).with_name('submission.json')
            source.write(previous,dict(source.read(previous),issued_sha256=source.sha(issue)))
            ref['sha256'] = source.sha(previous)
            source.write(latest,event)
            rows['q1']['submission_sha256'] = source.sha(latest)
        with pytest.raises(ValueError,match='packet'):
            blind.evidence(quiz,data,rows)
