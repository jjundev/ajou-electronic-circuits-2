"""Measure final gaps, including collapsed margins and the 1024px boundary."""
import re
import unittest
from pathlib import Path
from _util import SKILL

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "playwright unavailable")
class ReadabilityBrowserTest(unittest.TestCase):
    def test_measured_gaps_and_hidden_summary_in_both_templates(self):
        body = '''<div class="layer" data-explanation="solve"><span class="layer-title">이렇게 풀어요</span>
          <div data-subpart="1"><h4>(1) 입력 범위</h4><p>첫 문장</p><p>다음 문장</p></div>
          <div data-subpart="2"><h4>(2) 이득</h4><p>본문</p></div></div>
          <div class="sum" hidden><p class="sum-lead">핵심 한 문장</p>
          <div class="summary-group"><h4>첫 식</h4><p>하나예요.</p><p>둘이에요.</p></div>
          <div class="summary-group"><h4>판단</h4><p>조건이에요.</p></div></div>'''
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                for name in ("ec2-review-pack", "ec2-problem-explain"):
                    text = (SKILL.parent / name / "assets/note-template.html").read_text(encoding="utf-8")
                    css = re.search(r"<style>([\s\S]*?)</style>", text).group(1)
                    for width, section in ((w, s) for w in (1280, 1024, 1023, 375) for s in ('solve', 'verify')):
                        with self.subTest(template=name, width=width, section=section):
                            page = browser.new_page(viewport={"width":width,"height":900})
                            page.set_content("<style>" + css + "</style>" + body.replace('data-explanation="solve"', f'data-explanation="{section}"'))
                            self.assertEqual(page.locator(".sum").evaluate("e=>getComputedStyle(e).display"), "none")
                            values = page.evaluate('''() => {
                              const gap=(a,b)=>b.getBoundingClientRect().top-a.getBoundingClientRect().bottom;
                              const sum=document.querySelector('.sum');sum.hidden=false;
                              const groups=sum.querySelectorAll('.summary-group');
                              const ps=groups[0].querySelectorAll('p');
                              const parts=document.querySelectorAll('[data-subpart]');
                              return {group:gap(groups[0],groups[1]),lead:gap(sum.firstElementChild,groups[0]),
                                sentence:gap(ps[0],ps[1]),label:gap(groups[0].querySelector('h4'),ps[0]),
                                part:gap(parts[0],parts[1]),first:gap(document.querySelector('.layer-title'),parts[0]),
                                heading:gap(parts[0].querySelector('h4'),parts[0].querySelector('p')),
                                paragraph:gap(parts[0].querySelectorAll('p')[0],parts[0].querySelectorAll('p')[1])};
                            }''')
                            for key,wanted in {"group":24,"lead":24,"sentence":8,"label":12}.items():
                                self.assertAlmostEqual(values[key],wanted,delta=.1,msg=(key,values))
                            if name=="ec2-problem-explain":
                                for key,wanted in {"part":32 if width>=1024 else 24,"first":24,"heading":12,"paragraph":12}.items():
                                    self.assertAlmostEqual(values[key],wanted,delta=.1,msg=(key,values))
                            page.close()
            finally:
                browser.close()


    def test_real_summary_labels_equation_tail_and_math_before_subpart(self):
        # Regression: reset selectors used to win over universal sibling selectors.
        body = """<div class="sum"><p class="sum-lead">요약</p><p>첫 판단</p><p>둘째 판단</p>
          <p class="panel-label">최종 답</p><p class="answer">답이에요.</p><ul class="eq-list"><li><span class="eq-name">공통 크기</span><span class="math-row">x = 33.28</span></li></ul><p class="tail">조건을 유지해요.</p></div>
          <div class="layer" data-explanation="solve"><h4>이렇게 풀어요</h4><p>공통 계산</p>
          <span class="math-row">r = 5 kΩ</span><div data-subpart="1"><h4>(1) 차동 이득</h4><p>설명</p></div></div>"""
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                for name in ("ec2-review-pack", "ec2-problem-explain"):
                    text = (SKILL.parent / name / "assets/note-template.html").read_text(encoding="utf-8")
                    css = re.search(r"<style>([\s\S]*?)</style>", text).group(1)
                    for width in (1280, 1024, 1023, 375):
                        with self.subTest(template=name, width=width):
                            page = browser.new_page(viewport={"width":width,"height":900})
                            page.set_content("<style>"+css+"</style>"+body)
                            values = page.evaluate("""() => {
                              const q=s=>document.querySelector(s),gap=(a,b)=>q(b).getBoundingClientRect().top-q(a).getBoundingClientRect().bottom;
                              return {label:gap('.sum > p:nth-child(3)', '.panel-label'),
                                formula:gap('.panel-label','.answer'),lead:gap('.sum-lead','.sum > p:nth-child(2)'),tail:gap('.eq-list','.tail'),
                                part:gap('.layer > .math-row','[data-subpart]')};
                            }""")
                            for key,wanted in {'label':24,'formula':12,'tail':24,'lead':24}.items():
                                self.assertAlmostEqual(values[key],wanted,delta=.1,msg=(key,values))
                            if name == 'ec2-problem-explain':
                                self.assertAlmostEqual(values['part'],32 if width>=1024 else 24,delta=.1,msg=values)
                            page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
