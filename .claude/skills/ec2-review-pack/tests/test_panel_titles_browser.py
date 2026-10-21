"""Generated single-note contract; no course fixture mutation."""
import functools
import http.server
import threading
import shutil
import re
import json
import pytest
from playwright.sync_api import sync_playwright, expect
from pathlib import Path
import importlib.util
import sys
SKILL=Path(__file__).resolve().parents[1]
from _util import MINI_RUN
sys.path.append(str(SKILL/'scripts'))
spec=importlib.util.spec_from_file_location('ec2_note_assemble',SKILL/'scripts/assemble.py')
assemble=importlib.util.module_from_spec(spec);spec.loader.exec_module(assemble)
sys.path.insert(0,str(SKILL.parents[2]/'workbook'))

@pytest.mark.parametrize('width,height', [(1280,900),(375,812)])
@pytest.mark.parametrize('theme', ['light','dark'])
def test_note_panel_copy(tmp_path,width,height,theme):
    run=tmp_path/'run';shutil.copytree(MINI_RUN,run)
    section=run/'sections/s1.html'
    labels=iter(['첫 토픽 요약','둘째 토픽 요약'])
    section.write_text(re.sub(r'<div class="sum" hidden>.*?</article>',lambda m:'<div class="sum" hidden><p>'+next(labels)+'</p></div></article>',section.read_text(),flags=re.S))
    note=assemble.assemble(run,tmp_path)
    # A long transfer function is authored across short lines, as the skill requires.
    section.write_text(section.read_text().replace('첫 토픽 요약</p>',r'첫 토픽 요약</p><p>$$A_v(s)=A_0 H_1(s)H_2(s)$$</p><p>$$H_1(s)=\frac{1}{1+s/\omega_1}$$</p><p>$$H_2(s)=\frac{1}{1+s/\omega_2}$$</p>'))
    math_note=assemble.assemble(run,tmp_path/'math')
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(tmp_path)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            try:
                context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme)
                page=context.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                vendor=SKILL.parent/'ec2-problem-explain/assets/vendor'
                def local_resource(route):
                    url=route.request.url
                    rel=url.split('/dist/',1)[-1]
                    target=vendor/'katex'/rel
                    if 'pretendard@' in url:
                        route.fulfill(status=200,body='');return
                    route.fulfill(path=str(target))
                page.route('https://cdn.jsdelivr.net/**',local_resource)
                page.goto(f'http://127.0.0.1:{server.server_port}/{note.name}',wait_until='networkidle')
                if not page.locator('#panel-right').is_visible(): page.locator('#toggle-right').click()
                expect(page.locator('#sum-empty')).to_be_visible()
                for topic,label in [('s1-mean','첫 토픽 요약'),('s1-var','둘째 토픽 요약')]:
                    page.evaluate('(id)=>{location.hash=id}',topic)
                    expect(page.locator(f'main #{topic}')).to_be_visible()
                    title=page.locator(f'main #{topic} h3').inner_text()
                    assert page.locator('main h3',has_text=title).is_visible()
                    assert page.locator('#panel-right').get_by_text(title,exact=True).count()==0
                    assert page.locator('#sum-for.sums').count()==1
                    assert page.locator('[id="sum-for"]').count()==1
                    assert page.locator('#panel-right .sum:not([hidden])').count()==1
                    assert page.locator('#panel-right .sum:not([hidden])').inner_text()==label
                    assert page.locator('#sum-for').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
                key='od-note-read:0101-0102'
                saved=page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',key)
                assert {'s1-mean','s1-var'}<=set(saved)
                page.reload(wait_until='networkidle')
                assert page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))',key)==saved
                page.goto(f'http://127.0.0.1:{server.server_port}/math/{math_note.name}#s1-mean',wait_until='networkidle')
                if not page.locator('#panel-right').is_visible():page.locator('#toggle-right').click()
                expect(page.locator('#sum-for .sum:not([hidden]) .katex-display')).to_have_count(3)
                assert page.locator('#sum-for .sum:not([hidden]) .katex-display').evaluate_all('(els)=>els.every(e=>e.scrollWidth<=e.clientWidth+1)')
                assert page.locator('.katex-error').count()==0
                assert errors==[]
                context.close()
            finally: browser.close()
    finally:
        server.shutdown();thread.join();server.server_close()
