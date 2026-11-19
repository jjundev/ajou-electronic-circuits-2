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
    public = repo/'복습노트/0909'
    old = put(public/'확인문제_0909_Old.html', 'obsolete quiz')
    bundle = put(public/'.pack/자료_확인문제_0909_Old/source.json', 'old evidence')
    other = put(public/'.pack/unrelated/source.json', 'sibling')
    put(candidate/'정리노트_0909_Test.html', 'new parent')
    paths = PackPaths(repo, public, candidate)
    opts = dict(expected=publication.publication_inventory(public, '0909'),
                candidate_inventory=publication.publication_inventory(candidate, '0909'),
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
    assert (archive/old.name).read_text() == 'obsolete quiz'
    assert (archive/bundle.relative_to(public)).read_text() == 'old evidence'
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
