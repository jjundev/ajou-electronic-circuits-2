"""A reviewed route continues at step boundaries instead of clipping equations."""
import sys
from pathlib import Path
from copy import deepcopy
import fitz
import pytest
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from assemble import build_data,ids_selection
from render import inject,load_template,render_pdf


def test_long_answer_route_keeps_every_step_and_final_on_visible_pages(tmp_path):
    data=build_data(ids_selection(['E9.05'],'pagination'),'answers')
    p=data['problems'][0];p['hints']=[]
    p['solution']={'paginate':True,'steps':[{'label':f'RouteStep{i:02d}','html':f'<p>계산 조건 {i}</p>$$x_{{{i}}}={i}$$'} for i in range(26)],'answer':'<p>FinalResult729</p>'}
    file=tmp_path/'answer.html';file.write_text(inject(load_template('answers','video-16x9'),data));pdf=tmp_path/'answer.pdf'
    assert render_pdf(file,pdf)==[]
    with fitz.open(pdf) as doc:
        assert len(doc)>1
        text=''.join(page.get_text() for page in doc)
        for i in range(26):assert text.count(f'RouteStep{i:02d}')==1
        assert text.count('FinalResult729')==1
        for page in doc:assert not page.get_text(clip=fitz.Rect(0,675,1440,810)).strip()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome');page=browser.new_page();page.goto(file.as_uri());page.wait_for_selector('html[data-ready="true"]')
        assert page.locator('[data-solution-for="E9.05"]').count()>0
        assert page.locator('.sol-step').count()==26
        assert page.locator('.katex-error').count()==0
        browser.close()


@pytest.mark.parametrize('lines', [31, 150])
def test_oversized_final_answer_is_reported_instead_of_silently_clipped(tmp_path, lines):
    data=build_data(ids_selection(['E9.05'],'oversized'),'answers')
    data['problems'][0]['hints']=[]
    data['problems'][0]['solution']={'paginate':True,'steps':[{'label':'short','html':'<p>short</p>'}],'answer':'<p>'+('<br>'.join(['Final line']*lines))+'</p>'}
    file=tmp_path/'oversized.html';file.write_text(inject(load_template('answers','video-16x9'),data))
    assert render_pdf(file,tmp_path/'oversized.pdf')


def test_paginated_routes_keep_baseline_type_size(tmp_path):
    data=build_data(ids_selection(['E9.05'],'type'),'answers')
    data['problems'][0]['hints']=[]
    data['problems'][0]['solution']={'paginate':True,'steps':[{'label':f'Step{i}','html':'<p>계산</p>$$x=1$$'} for i in range(28)],'answer':'<p>Final</p>'}
    file=tmp_path/'type.html';file.write_text(inject(load_template('answers','a4'),data))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome');page=browser.new_page();page.goto(file.as_uri());page.wait_for_selector('html[data-ready="true"]')
        assert page.locator('.work').evaluate_all('(nodes)=>nodes.every(n=>(parseFloat(getComputedStyle(n).getPropertyValue("--sfs"))||1)>=1)')
        browser.close()


def test_existing_unpaginated_answer_can_still_use_its_font_fit(tmp_path):
    data=build_data(ids_selection(['E9.05'],'legacy-fit'),'answers')
    data['problems'][0]['hints']=[]
    data['problems'][0]['solution']={'steps':[{'label':'short','html':'<p>short</p>'}],'answer':'<p>'+('<br>'.join(['AnswerLine']*24))+'</p>'}
    file=tmp_path/'legacy.html';file.write_text(inject(load_template('answers','a4'),data))
    assert render_pdf(file,tmp_path/'legacy.pdf')==[]
