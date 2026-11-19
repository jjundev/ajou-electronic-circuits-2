"""Synthetic judgments only. The candidate page images come from a real PDF renderer."""
import json
from pathlib import Path

import pymupdf
import pytest

from test_pack_graph import selected, seed, cli
import pack_flow as flow


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path


def pdf_file(path, label='Vout'):
    with pymupdf.open() as doc:
        for index, text in enumerate([label, 'second'], 1):
            page = doc.new_page()
            page.insert_text((20, 30), f'{index} / 2')
            page.insert_text((40, 100), text)
            page.draw_line((40, 99), (75, 99))
        doc.save(path)


def page_order(pdf):
    return dict(schema_version=1, pdf_sha256=flow._sha(pdf), count=2, browser_version='fixture',
                pages=[dict(id='P1', owner='P1'), dict(id='P2', owner='P2')])


def pdf_run(tmp_path):
    state = selected(tmp_path, ['P1', 'P2'])
    run = Path(state['run'])
    seed(state, ['stage-problem-index', 'explain-author', 'explain-blind', 'child-coordinator',
                 'explain-verify', 'build-answers'])
    pdf = run/'answers.pdf'
    pdf_file(pdf)
    overlay = write(run/'overlay.json', dict(learning_style=flow._read(run/'learning-style.json'),
        problems=[dict(id=x, steps=[x], answers=[x]) for x in ['P1','P2']], assets={}))
    pre = write(run/'preflight.json', dict(browser_version='fixture'))
    state['actions']['render-preflight']['artifacts'] = {'render-preflight.json': str(pre)}
    state['actions']['build-answers']['artifacts'] = {'pdf': str(pdf), 'page-order.json': str(write(run/'page-order.json', page_order(pdf)))}
    state['actions']['explain-verify']['artifacts'] = {'overlay': str(overlay)}
    flow.update_state(run, state['revision'], lambda _: flow.refresh_tasks(state))
    return run, pdf


def test_review_key_survives_order_only_change(tmp_path):
    from pack_approvals import blind_targets
    from display_titles import numbered_title
    titles = {'P1':'Q'}
    q = dict(workbook_id='P1', id='p1', display_title='Q', title=numbered_title(titles,'P1',1), original_html='q', conditions_html='c',
             ask_html='a', subparts=['a'], figures=['p1-img.svg'])
    (tmp_path/'p1-img.svg').write_text('svg')
    before = blind_targets([q], tmp_path, 'profile')
    (tmp_path/'p2-img.svg').write_text('svg')
    after = blind_targets([dict(q, id='p2', title=numbered_title(titles,'P1',2), figures=['p2-img.svg'])], tmp_path, 'profile')
    assert before['independent:P1:a']['key'] == after['independent:P1:a']['key']
    retitled = blind_targets([dict(q,display_title='Different',title=numbered_title({'P1':'Different'},'P1',1))],tmp_path,'profile')
    assert retitled['independent:P1:a']['key'] != before['independent:P1:a']['key']
    # With no approved display-title mapping, a leading Pn belongs to the original text.
    raw = dict(q)
    raw.pop('display_title')
    assert blind_targets([raw],tmp_path,'profile') != blind_targets([dict(raw,title='Q')],tmp_path,'profile')
    changed = blind_targets([dict(q, conditions_html='d')], tmp_path, 'profile')
    assert changed['independent:P1:a']['key'] != before['independent:P1:a']['key']


def test_pdf_label_edit_reuses_only_equal_pages(tmp_path):
    from pack_approvals import pdf_targets
    run, pdf = pdf_run(tmp_path)
    def inventories(tag):
        return pdf_targets(pdf, flow._read(run/'overlay.json'), run/tag, 'renderer', order=page_order(pdf))
    before = inventories('first')
    pdf_file(pdf, 'Vin')
    after = inventories('second')
    assert [n for n in [1, 2] if before[f'pdf-page:{n}']['key'] != after[f'pdf-page:{n}']['key']] == [1]
    assert [n for n in [1, 2] if before[f'pdf-page:{n}']['key'] == after[f'pdf-page:{n}']['key']] == [2]
    assert after['pdf-page:1']['geometry_candidates']
    assert all(Path(row['image']).is_file() for row in after.values())


def test_shared_font_invalidates_visual_approvals(tmp_path):
    from pack_approvals import render_fingerprint
    font = tmp_path/'shared.woff2'
    font.write_bytes(b'first')
    before = render_fingerprint('test-browser', [font])
    font.write_bytes(b'second')
    assert before != render_fingerprint('test-browser', [font])


def test_missing_png_reopens_only_own_approval(tmp_path):
    from pack_approvals import collect_current_reviews, approval_key
    from PIL import Image
    required, ledger = {}, []
    for view in ['mobile-dark','desktop-light']:
        target = 'note-visual:feedback:' + view
        key = approval_key('note-visual', target, input_hashes={'render_fingerprint':'a'}, policy_version='test')
        image = tmp_path/(view+'.png')
        Image.new('RGB', (8, 8)).save(image)
        required[target] = key
        ledger.append(dict(target=target, key=key, status='pass', reviewer='fixture', evidence='actual fixture',
                           files=[dict(path=str(image), sha256=flow._sha(image))]))
    (tmp_path/'mobile-dark.png').unlink()
    result = collect_current_reviews(required, ledger, run_root=tmp_path)
    assert set(result['pending']) == {'note-visual:feedback:mobile-dark'}


def test_pdf_brief_contains_only_direct_inputs(tmp_path):
    run, _ = pdf_run(tmp_path)
    claim = flow.claim_task(run, 'pdf-qa')
    brief = flow._read(claim['brief'])
    assert set(brief['input_paths']).isdisjoint(flow.load_state(run)['hashes'].keys() -
        {brief['snapshot'], brief['profile']})
    assert all('synthetic.json' not in p for p in brief['input_paths'])
    assert set(brief['approval_plan']['pending']) == {'pdf-page:1','pdf-page:2'}


def test_pdf_claim_check_accept_next_reuses_only_current_proof(tmp_path):
    run, pdf = pdf_run(tmp_path)
    def review(expected):
        claim = flow.claim_task(run, 'pdf-qa')
        a = claim['attempt']
        flow.bind_task(run, 'pdf-qa', a, 'fixture PDF reviewer')
        brief = flow._read(claim['brief'])
        root = Path(brief['run'])
        plan = brief['approval_plan']
        assert set(plan['pending']) == expected
        Path(brief['report']).write_text('Only fixture inspections.')
        decisions = write(root/'target-reviews.json', {target: dict(status='pass', evidence='fixture page inspected',
            overflow=[], geometry_evidence='synthetic glyph and wire inspection', image=plan['targets'][target]['image']) for target in expected})
        submission = write(root/'submission.json', dict(status='done', report=brief['report'], outputs=[],
            reviews=[str(decisions), brief['report']], counts={'targets': brief['targets']}, unresolved=[]))
        cli('task','build-receipt','--run',run,'--task','pdf-qa','--attempt',a,'--submission',submission)
        cli('task','check','--run',run,'--task','pdf-qa','--attempt',a,'--receipt',brief['receipt'])
        state = flow.accept_task(run,'pdf-qa',a,Path(brief['receipt']))
        assert state['tasks']['pdf-qa']['status'] == 'done'
        assert 'pdf-qa' not in flow.next_work(run, slots=10)['dispatch']
        return state
    old = review({'pdf-page:1','pdf-page:2'})
    previous = Path(old['tasks']['pdf-qa']['artifacts']['answer-review.json'])
    digest = flow._sha(previous)
    pdf_file(pdf, 'Vin')
    write(run/'page-order.json', page_order(pdf))
    assert 'pdf-qa' in flow.next_work(run, slots=20)['dispatch']
    cur = review({'pdf-page:1'})
    assert flow._sha(previous) == digest
    assert set(cur['tasks']['pdf-qa']['receipt']['reused_approvals']) == {'pdf-page:2'}

def test_stale_page_map_cannot_narrow_explanation_proof(tmp_path):
    from pack_approvals import pdf_targets
    run, pdf = pdf_run(tmp_path)
    overlay = flow._read(run/'overlay.json')
    sidecar = page_order(pdf)
    def keys(name, sidecar):
        return [x['key'] for x in pdf_targets(pdf, overlay, run/name, 'browser', order=sidecar).values()]
    original = keys('original', sidecar)
    overlay['problems'][0]['steps'] = ['different']
    changed = keys('changed', sidecar)
    assert original[0] != changed[0] and original[1] == changed[1]
    stale = dict(sidecar, pdf_sha256='older PDF')
    before = keys('stale', stale)
    overlay['problems'][0]['steps'] = ['yet another']
    after = keys('stale-after', stale)
    assert all(a != b for a,b in zip(before, after))


def test_workbook_print_emits_same_render_page_provenance(tmp_path):
    import sys
    from _util import REPO
    sys.path.insert(0, str(REPO/'workbook'))
    import render
    html = tmp_path/'sample.html'
    html.write_text("""<html data-ready="true"><style>@page {size:200px 100px;margin:0}
    body{margin:0}.page{height:100px;break-after:page}</style><div id="book">
    <div class="page" id="P1">First</div>
    <div class="page" id="P1-solution-1" data-solution-for="P1">Second</div></div></html>""")
    pdf, sidecar = tmp_path/'result.pdf', tmp_path/'page-order.json'
    assert render.render_pdf(html, pdf, order_path=sidecar) == []
    order = flow._read(sidecar)
    assert order['pdf_sha256'] == flow._sha(pdf) and order['count'] == 2
    assert order['pages'] == [dict(id='P1',owner='P1'), dict(id='P1-solution-1',owner='P1')]
    assert order['browser_version']


def blind_run(tmp_path):
    state = selected(tmp_path, ['P1','P2'])
    run = Path(state['run'])
    seed(state, ['stage-problem-index'])
    questions = run/'sealed/questions.json'
    from display_titles import numbered_title
    rows = [dict(workbook_id=pid, id=f'p{i}',display_title=pid, title=numbered_title({pid:pid},pid,i), original_html=pid, conditions_html='conditions',
                 ask_html='question', subparts=['a'], figures=[]) for i,pid in enumerate(['P1','P2'],1)]
    write(questions, dict(problems=rows))
    index = state['actions']['stage-problem-index']
    index.update(questions=[str(questions)], artifacts={'questions.json':str(questions)})
    flow.update_state(run, state['revision'], lambda _: flow.refresh_tasks(state))
    return run, questions


def compact(run, tid, reviewer):
    claim = flow.claim_task(run,tid)
    flow.bind_task(run,tid,claim['attempt'],reviewer)
    brief = flow._read(claim['brief'])
    root = Path(brief['run'])
    report = Path(brief['report'])
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text('Fixture inspection.')
    decisions = root/'target-reviews.json'
    submission = write(root/'worker.json',dict(status='done',report=str(report),outputs=[],
                       reviews=[str(report),str(decisions)],counts={'targets':brief['targets']},unresolved=[]))
    return brief, decisions, submission


def test_blind_reuse_preserves_solver_and_rejects_unchecked_numerical_solution(tmp_path):
    from pack_receipts import build_receipt
    run, questions = blind_run(tmp_path)
    brief,d,s = compact(run,'explain-blind','first solver')
    pending = brief['approval_plan']['pending']
    assert set(pending) == {'independent:P1:a','independent:P2:a'}
    data = {t:dict(status='pass',method='numerical',conclusion=t,evidence='fixture',residual=2,tolerance=1)
            for t in pending}
    write(d,data)
    with pytest.raises(flow.FlowError,match='tolerance|residual'):
        build_receipt(flow.inspect_state(run),'explain-blind',brief['attempt'],s)
    for decision in data.values():
        decision['residual'] = 0
    write(d,data)
    build_receipt(flow.inspect_state(run),'explain-blind',brief['attempt'],s)
    flow.accept_task(run,'explain-blind',brief['attempt'],Path(brief['receipt']))
    rows = flow._read(questions)['problems'][::-1]
    for i,row in enumerate(rows,1):
        row['id'] = f'p{i}'
        from display_titles import numbered_title
        row['title'] = numbered_title({row['workbook_id']:row['workbook_id']},row['workbook_id'],i)
    write(questions,dict(problems=rows))
    brief,d,s = compact(run,'explain-blind','second solver')
    assert not brief['approval_plan']['pending']
    assert 'first solver' not in json.dumps(brief)
    write(d,{})
    build_receipt(flow.inspect_state(run),'explain-blind',brief['attempt'],s)
    assert flow._read(Path(brief['run'])/'independent.json')['items'] == {}
    assert 'first solver' not in Path(brief['receipt']).read_text()
    state = flow.accept_task(run,'explain-blind',brief['attempt'],Path(brief['receipt']))
    items = flow._read(state['tasks']['explain-blind']['artifacts']['independent.json'])['items']
    assert items['p1:a']['conclusion'] == 'independent:P2:a' and items['p1:a']['reviewer']=='first solver'


def test_added_shared_resource_reopens_visual_approval_at_next(tmp_path):
    from pack_receipts import build_receipt
    run, _ = pdf_run(tmp_path)
    brief,d,s = compact(run,'pdf-qa','fixture PDF reviewer')
    write(d,{t:dict(status='pass',image=r['image'],overflow=[],geometry_evidence='synthetic glyph and wire inspection',evidence='fixture render')
             for t,r in brief['approval_plan']['targets'].items()})
    build_receipt(flow.inspect_state(run),'pdf-qa',brief['attempt'],s)
    state = flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    font = Path(state['repo'])/'.claude/skills/ec2-problem-explain/assets/vendor/fallback.woff2'
    font.parent.mkdir(parents=True,exist_ok=True)
    font.write_bytes(b'changed font inventory')
    assert 'pdf-qa' in flow.next_work(run,slots=20)['dispatch']
    brief,_,_ = compact(run,'pdf-qa','fixture PDF reviewer')
    assert set(brief['approval_plan']['pending']) == {'pdf-page:1','pdf-page:2'}


def test_real_browser_claim_loses_one_topic_view_and_rejects_cross_attempt_screen(tmp_path):
    from PIL import Image
    from pack_receipts import build_receipt
    state = selected(tmp_path, [])
    run = Path(state['run'])
    seed(state,['scope-final','author-why','assemble-note','structural-precheck','style-audit','content-review','precheck'])
    note = run/'candidate/note.html'
    note.parent.mkdir()
    state['scope_sections'][0]['topics'].append(dict(id='second-topic'))
    note.write_text('<style>article{height:1500px}</style><article id="why-topic"><p>Fixture topic</p></article>'
                    '<article id="second-topic"><img src="detail.png"></article>')
    detail = note.parent/'detail.png'
    Image.new('RGB',(40,40),'blue').save(detail)
    original_detail = detail.read_bytes()
    m = write(run/'manifest.json',dict(sections=state['scope_sections']))
    state['actions']['assemble-note']['artifacts'] = {'note':str(note)}
    state['tasks']['scope-final']['artifacts'] = {'manifest.json':str(m)}
    state['actions']['precheck']['candidate_root'] = str(note.parent)
    flow.update_state(run,state['revision'],lambda _: flow.refresh_tasks(state))
    brief,d,s = compact(run,'browser-qa','browser fixture')
    rows = {}
    for target in brief['approval_plan']['pending']:
        img = Path(brief['run'])/(target.split(':')[-1]+'.png')
        Image.new('RGB',(32,32)).save(img)
        rows[target] = dict(status='pass',image=str(img),evidence='fixture inspection')
    write(d,rows)
    report = write(Path(brief['required_outputs'][0]),dict(fixture=True))
    write(s,dict(flow._read(s),outputs=[str(report)],reviews=[str(d),str(report),brief['report']]))
    with pytest.raises(flow.FlowError, match='renderer'):
        build_receipt(flow.inspect_state(run),'browser-qa',brief['attempt'],s)
    for row in rows.values():
        row['renderer'] = brief['render_context']
    write(d,rows)
    with pytest.raises(flow.FlowError, match='capture|viewport'):
        build_receipt(flow.inspect_state(run),'browser-qa',brief['attempt'],s)
    for t,row in rows.items():
        row['image'] = brief['approval_plan']['targets'][t]['image']
    write(d,rows)
    with pytest.raises(flow.FlowError, match='interaction'):
        build_receipt(flow.inspect_state(run),'browser-qa',brief['attempt'],s)
    from pack_support import browser_interactions
    browser_interactions(brief)
    specimen = Path(next(iter(rows.values()))['image'])
    original = specimen.read_bytes()
    # A correctly sized replacement at the actual expected path still fails.
    Image.new('RGB',(1280,900),'green').save(specimen)
    with pytest.raises(flow.FlowError, match='capture'):
        build_receipt(flow.inspect_state(run),'browser-qa',brief['attempt'],s)
    specimen.write_bytes(original)
    build_receipt(flow.inspect_state(run),'browser-qa',brief['attempt'],s)
    accepted = flow.accept_task(run,'browser-qa',brief['attempt'],Path(brief['receipt']))
    Image.new('RGB',(40,40),'orange').save(detail)
    assert 'browser-qa' in flow.next_work(run,slots=20)['dispatch']
    changed = flow.claim_task(run,'browser-qa')
    plan = flow._read(changed['brief'])['approval_plan']
    assert set(plan['pending']) == {k for k in rows if ':second-topic:' in k}
    assert set(plan['reusable']) == {k for k in rows if ':why-topic:' in k}
    flow.release_task(run,'browser-qa',changed['attempt'],'fixture finished inspecting the delta')
    detail.write_bytes(original_detail)
    lost = 'note-visual:why-topic:mobile-dark'
    item, = [a for a in accepted['approval_ledger'] if a['target']==lost]
    Path(item['screen']).unlink()
    assert 'browser-qa' in flow.next_work(run,slots=8)['dispatch']
    replacement,d,s = compact(run,'browser-qa','another browser fixture')
    assert set(replacement['approval_plan']['pending']) == {lost}
    write(d,{lost:rows[lost]})
    with pytest.raises(flow.FlowError, match='outside'):
        build_receipt(flow.inspect_state(run),'browser-qa',replacement['attempt'],s)


def test_distinct_standalone_proof_cannot_reuse_note_image(tmp_path):
    from pack_approvals import select_approval
    report = tmp_path/'report.md'
    report.write_text('No SVG screenshot.')
    ledger = [dict(target='standalone-svg:fig.svg',key='fixture',status='pass',reviewer='fixture',
                   evidence='fixture',files=[dict(path=str(report),sha256=flow._sha(report))])]
    assert select_approval(ledger,key='fixture',run_root=tmp_path) is None


def test_prior_solver_cannot_author_reused_independent_answer(tmp_path):
    from pack_receipts import build_receipt
    run, questions = blind_run(tmp_path)
    brief,decisions,submission = compact(run,'explain-blind','original solver')
    write(decisions,{target:dict(status='pass',method='exact',conclusion='1',evidence='fixture inspection')
         for target in brief['approval_plan']['pending']})
    build_receipt(flow.inspect_state(run),'explain-blind',brief['attempt'],submission)
    flow.accept_task(run,'explain-blind',brief['attempt'],Path(brief['receipt']))
    # Re-aggregate the same stable decisions under a new claim coordinator.
    payload = flow._read(questions)
    questions.write_text(json.dumps(payload, indent=2))
    brief,decisions,submission = compact(run,'explain-blind','coordinator')
    assert not brief['approval_plan']['pending']
    write(decisions,{})
    build_receipt(flow.inspect_state(run),'explain-blind',brief['attempt'],submission)
    flow.accept_task(run,'explain-blind',brief['attempt'],Path(brief['receipt']))
    brief,_,submission = compact(run,'explain-author','original solver')
    for name in brief['required_outputs']:
        p = Path(name)
        p.parent.mkdir(exist_ok=True)
        p.write_text('fixture fragment')
    write(submission,dict(flow._read(submission),reviews=[brief['report']],outputs=brief['required_outputs']))
    with pytest.raises(flow.FlowError, match='independent|author'):
        build_receipt(flow.inspect_state(run),'explain-author',brief['attempt'],submission)


def test_static_note_review_tracks_visible_target_and_shared_styles(tmp_path):
    from pack_approvals import _visual_targets
    note = tmp_path/'note.html'
    def inventory(change, style=''):
        note.write_text('<html><head><style>article{height:1400px}'+style+'</style></head><body>'
                        '<article id="one">First</article><article id="two">'+change+'</article></body></html>')
        brief = dict(role='browser-qa', run=str(tmp_path.parent/(tmp_path.name+'-capture')), note=str(note), candidate_pack=str(tmp_path),
                     targets=['one','two'],attempt='test')
        return {k:v['key'] for k,v in _visual_targets({},brief,'fixture').items()}
    old = inventory('unchanged')
    new = inventory('edited')
    assert old['note-visual:one:desktop-light'] == new['note-visual:one:desktop-light']
    assert old['note-visual:two:mobile-dark'] != new['note-visual:two:mobile-dark']
    restyled = inventory('edited','body{color:blue}')
    assert all(key != restyled[k] for k,key in new.items())


def test_previous_parallel_run_keeps_full_receipt_and_original_brief(tmp_path):
    run, _ = pdf_run(tmp_path)
    state = flow.load_state(run)
    state.pop('approval_contract',None)
    flow.update_state(run,state['revision'],lambda _: state)
    brief = flow._read(flow.claim_task(run,'pdf-qa')['brief'])
    assert 'approval_plan' not in brief
    assert any(Path(r['path']).parent.name=='STT' for r in brief['inputs'])
    flow.bind_task(run,'pdf-qa',brief['attempt'],'legacy reviewer')
    root = Path(brief['run'])
    report = Path(brief['report'])
    report.write_text('legacy physical review fixture')
    pages = root/'answer-pages'
    pages.mkdir()
    with pymupdf.open(brief['pdf']) as doc:
        for i,page in enumerate(doc,1):
            page.get_pixmap().save(pages/f'page-{i}.png')
    evidence = [report,*sorted(pages.iterdir())]
    overlay = flow._read(brief['overlay'])
    summary = write(root/'answer-review.json',dict(schema_version=1,status='pass',reviewer='legacy reviewer',
        overflow=[],pdf_sha256=flow._sha(Path(brief['pdf'])),overlay_sha256=flow._sha(Path(brief['overlay'])),
        learning_style_sha256=overlay['learning_style']['sha256'],
        evidence=[dict(path=p.relative_to(root).as_posix(),sha256=flow._sha(p)) for p in evidence]))
    receipt = write(Path(brief['receipt']),dict(schema_version=1,run_id=brief['run_id'],task_id='pdf-qa',
        attempt=brief['attempt'],status='done',inputs=brief['inputs'],outputs=[dict(path=str(p),sha256=flow._sha(p))
        for p in [*evidence,summary]],report=str(report),reviews=[str(report)],counts={'targets':brief['targets']},unresolved=[]))
    assert flow.check_task(run,'pdf-qa',brief['attempt'],receipt)['status']=='ok'
    assert flow.accept_task(run,'pdf-qa',brief['attempt'],receipt)['tasks']['pdf-qa']['status']=='done'



def test_compact_receipt_freezes_original_submission_and_rejects_changed_decision(tmp_path):
    from pack_receipts import build_receipt
    run, _ = pdf_run(tmp_path)
    brief,d,s = compact(run,'pdf-qa','fixture')
    write(d,{t:dict(status='pass',image=r['image'],overflow=[],geometry_evidence='synthetic glyph and wire inspection',evidence='fixture') for t,r in brief['approval_plan']['targets'].items()})
    build_receipt(flow.inspect_state(run),'pdf-qa',brief['attempt'],s)
    original = s.read_bytes()
    write(s,dict(flow._read(s),status='withheld'))
    res = flow.check_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    assert res['status']=='failed'
    s.write_bytes(original)
    accepted = flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    assert Path(accepted['tasks']['pdf-qa']['artifacts'][s.name]).read_bytes() == original


def test_embedded_svg_keeps_key_but_script_and_remote_resources_do_not(tmp_path):
    from pack_approvals import _visual_targets
    path = tmp_path/'diagram.svg'
    md = tmp_path/'notes.md'
    def keys(markup):
        path.write_text(markup)
        r = dict(path=str(path),sha256=flow._sha(path))
        brief = dict(role='standalone-svg-qa',note=str(tmp_path/'note.html'),
                     converted_assets=dict(md={'path':str(md)},svgs=[r]),
                     svg_screenshots={str(path):str(tmp_path/'screen.png')})
        return [next(iter(_visual_targets({},dict(brief,attempt=a),'renderer').values()))['key'] for a in ['old','new']]
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><style>@font-face{src:url(\'data:font/woff2;base64,AAAA\')}</style></svg>'
    assert len(set(keys(svg))) == 1
    assert len(set(keys('<svg><image href="https://example.test/x"/></svg>'))) == 2
    assert len(set(keys('<svg><rect onload="change()"/></svg>'))) == 2


def test_flagged_pdf_geometry_requires_human_disposition(tmp_path):
    from pack_receipts import build_receipt
    run, _ = pdf_run(tmp_path)
    brief,d,s = compact(run,'pdf-qa','fixture')
    assert flow._read(brief['geometry_hints']['path'])['pdf-page:1']
    write(d,{t:dict(status='pass',image=r['image'],overflow=[],evidence='overall fixture pass')
             for t,r in brief['approval_plan']['targets'].items()})
    with pytest.raises(flow.FlowError, match='geometry'):
        build_receipt(flow.inspect_state(run),'pdf-qa',brief['attempt'],s)


def test_partial_repair_requires_current_judgment_for_affected_pdf_pages(tmp_path):
    from pack_approvals import make_plan
    from pack_receipts import build_receipt
    run, _ = pdf_run(tmp_path)
    brief,d,s = compact(run,'pdf-qa','fixture')
    write(d,{t:dict(status='pass',image=r['image'],overflow=[],geometry_evidence='fixture glyph',evidence='fixture')
             for t,r in brief['approval_plan']['targets'].items()})
    build_receipt(flow.inspect_state(run),'pdf-qa',brief['attempt'],s)
    state = flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    again = dict(brief, recheck_findings=[{'target':'P1'}], run=str(run/'recheck'))
    Path(again['run']).mkdir()
    make_plan(state,again)
    assert set(again['approval_plan']['pending']) == {'pdf-page:1'}
    assert set(again['approval_plan']['reusable']) == {'pdf-page:2'}


def test_new_negative_judgment_blocks_an_older_pass_with_same_key(tmp_path):
    from pack_approvals import collect_current_reviews, select_approval
    proof = tmp_path/'solver.json'
    proof.write_text('original proof')
    good = dict(target='independent:P1:a',key='fixture-key',reviewer='one',evidence='actual fixture',status='pass',
                files=[dict(path=str(proof),sha256=flow._sha(proof))])
    rows = [good,dict(target=good['target'],key=good['key'],status='invalidated',reason='later human finding')]
    assert select_approval(rows,key=good['key'],run_root=tmp_path) is None
    assert collect_current_reviews({good['target']:good['key']},rows,run_root=tmp_path)['pending']


def submit_pdf(run):
    from pack_receipts import build_receipt
    brief,d,s = compact(run,'pdf-qa','fixture')
    write(d,{t:dict(status='pass',image=r['image'],overflow=[],geometry_evidence='fixture glyph inspection',evidence='fixture')
             for t,r in brief['approval_plan']['targets'].items() if t in brief['approval_plan']['pending']})
    build_receipt(flow.inspect_state(run),'pdf-qa',brief['attempt'],s)
    return brief


def test_claimed_pdf_cannot_drop_target_proof(tmp_path):
    run, _ = pdf_run(tmp_path)
    brief = submit_pdf(run)
    receipt = Path(brief['receipt'])
    raw = flow._read(receipt)
    raw.pop('target_reviews')
    raw.pop('worker_submission')
    write(receipt,raw)
    assert flow.check_task(run,'pdf-qa',brief['attempt'],receipt)['status']=='failed'
    with pytest.raises(flow.FlowError):
        flow.accept_task(run,'pdf-qa',brief['attempt'],receipt)


def test_policy_only_change_reopens_adopted_and_active_reviews(tmp_path,monkeypatch):
    import pack_approvals as approvals
    run, _ = pdf_run(tmp_path)
    brief = submit_pdf(run)
    policy = approvals.POLICY
    monkeypatch.setattr(approvals,'POLICY',policy+'-changed')
    assert flow.check_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))['status']=='failed'
    monkeypatch.setattr(approvals,'POLICY',policy)
    flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    monkeypatch.setattr(approvals,'POLICY',policy+'-changed')
    assert flow.inspect_state(run)['tasks']['pdf-qa']['status']=='stale'
    assert 'explain-blind' in flow.next_work(run,slots=20)['dispatch']
    assert 'publish-pack' not in flow.next_work(run,slots=20)['actions']


def test_pdf_claim_scopes_an_owner_asset_change(tmp_path):
    run, _ = pdf_run(tmp_path)
    overlay = flow._read(run/'overlay.json')
    for problem in overlay['problems']:
        name = 'images/'+problem['id']+'.svg'
        problem.update(steps=[{'html':f'<img src="{name}">'}],answers=[{'html':'answer'}])
        overlay['assets'][name] = 'original'
    write(run/'overlay.json',overlay)
    brief=submit_pdf(run)
    flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    overlay['assets']['images/P1.svg']='updated'
    write(run/'overlay.json',overlay)
    assert 'pdf-qa' in flow.next_work(run,slots=20)['dispatch']
    again=flow._read(flow.claim_task(run,'pdf-qa')['brief'])
    assert set(again['approval_plan']['pending'])=={'pdf-page:1'}


def test_static_topic_assets_do_not_invalidate_unrelated_topic(tmp_path):
    from pack_approvals import _visual_targets
    from PIL import Image
    root = tmp_path/'candidate'
    root.mkdir()
    note=root/'note.html'
    note.write_text('<style>article{height:1400px}</style><article id="one"><img src="one.png"></article>'
                    '<article id="two"><img src="two.png"></article>')
    for name in ('one','two'):
        Image.new('RGB',(32,32),'red').save(root/(name+'.png'))
    def keys(tag):
        out=tmp_path/tag
        out.mkdir()
        b=dict(role='browser-qa',run=str(out),note=str(note),candidate_pack=str(root),targets=['one','two'],attempt=tag)
        return {t:r['key'] for t,r in _visual_targets({},b,'renderer').items()}
    old=keys('first')
    Image.new('RGB',(32,32),'blue').save(root/'one.png')
    current=keys('second')
    assert current['note-visual:one:desktop-light']!=old['note-visual:one:desktop-light']
    assert current['note-visual:two:desktop-light']==old['note-visual:two:desktop-light']


def test_content_claim_freezes_summary_catalog_and_selection_evidence(tmp_path):
    from pack_graph import refresh
    state=selected(tmp_path,[])
    run=Path(state['run'])
    seed(state,['scope-final','author-why','assemble-note'])
    note=run/'fixture-note.html'
    note.write_text('fixture note')
    state['actions']['assemble-note']['artifacts']={'note':str(note)}
    state['tasks']['scope-final']['artifacts']={'manifest.json':str(write(run/'fixture-manifest.json',{}))}
    direct={}
    for tid, names in [('stt-0909',['summaries/stt-0909.md']),('candidate-index',['candidates.json','catalog/index.json','catalog/detail.json']),
                        ('selection',['selection-review.json','selection.json'])]:
        row=flow._record(state,tid)
        files=row.setdefault('artifacts',{})
        for name in names:
            files[name]=str(write(run/'producer'/name,{}))
            direct[name]=files[name]
    source = Path(state['repo'])/'from_the_past/md/mock.md'
    source.parent.mkdir(parents=True)
    source.write_text('fixture unused exam original')
    write(Path(direct['catalog/detail.json']),dict(input_hashes={'from_the_past/md/mock.md':flow._sha(source)}))
    write(Path(direct['candidates.json']),dict(problems=[dict(id='Q-test',kind='기출',used=False,detail_path='detail.json')]))
    direct['exam_source']=str(source)
    unrelated=write(run/'unrelated.png',{})
    state['actions']['candidate-index']['artifacts']['unrelated.png']=str(unrelated)
    flow.update_state(run,state['revision'],lambda _: refresh(state))
    brief=flow._read(flow.claim_task(run,'content-review')['brief'])
    hashes={r['path']:r['sha256'] for r in brief['inputs']}
    assert all(hashes.get(p)==flow._sha(Path(p)) for p in direct.values())
    assert str(unrelated) not in brief['input_paths']
    assert brief['selection_review']==direct['selection-review.json'] and brief['summaries']==[direct['summaries/stt-0909.md']]

def test_current_policy_stamp_alone_cannot_revive_an_aggregate_approval(tmp_path):
    run,_=pdf_run(tmp_path)
    brief=submit_pdf(run)
    accepted=flow.accept_task(run,'pdf-qa',brief['attempt'],Path(brief['receipt']))
    # An imported pre-fix trial could have supplied arbitrary extra fields.
    def old(state):
        receipt=state['tasks']['pdf-qa']['receipt']
        receipt.pop('target_reviews')
        receipt.pop('fresh_approvals')
        receipt.pop('reused_approvals')
        return state
    flow.update_state(run,accepted['revision'],old)
    assert 'pdf-qa' in flow.next_work(run,slots=20)['dispatch']
