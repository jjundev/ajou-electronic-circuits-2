"""Public study text and authored sentence blocks, without splitting TeX at runtime."""
import unittest
import tempfile
from _util import SCRIPTS
from check_html import check_common, parse_html
from pathlib import Path


class ReadabilityTest(unittest.TestCase):
    def errors(self, body):
        source = '<html lang="ko"><body>' + body + '</body></html>'
        return [str(e) for e in check_common(parse_html(source), source, Path('note.html'))]

    def test_public_stt_citation_in_text_or_tooltip_is_rejected(self):
        for text in ['(1007 STT L182–186, Part 04; 시각 정보 없음)',
                     '(0914 26:00)', 'STT 12:30', 'Part 04', '시각 정보 없음']:
            for body in [f'<p>{text}</p>', f'<p title="{text}">설명</p>']:
                self.assertTrue(any('public-source-location' in e for e in self.errors(body)), body)

    def test_circuit_time_and_part_symbols_are_not_source_locations(self):
        self.assertEqual(self.errors('<p>시간 상수는 $\\tau=0.5\\,\\mathrm{ms}$예요. 시각 12:30의 파형을 읽어요. Part 번호는 소자 이름이에요.</p>'), [])

    def test_long_summary_paragraph_is_rejected(self):
        errors = self.errors('<div class="sum" hidden><p>테일 저항을 구해요. 반회로를 사용해요.</p></div>')
        self.assertTrue(any('summary-sentence' in e for e in errors), errors)

    def test_sentence_blocks_keep_decimals_math_and_block_formulas(self):
        self.assertEqual(self.errors('<div class="sum" hidden><p class="sum-lead">반회로로 풀어요.</p>'
            '<div class="summary-group"><h4>이득</h4><p>$A_v=-4.76$이에요.</p>'
            '<p>동작 범위는 1.8–2.9 V예요.</p><p>$$x=0.5\\quad y=1.0$$</p></div></div>'), [])

    def test_empty_paragraph_and_br_spacing_are_rejected(self):
        for body in ['<div class="sum" hidden><p> </p></div>',
                     '<div class="sum" hidden><p>첫 식<br><br>답</p></div>']:
            self.assertTrue(any('summary-spacing' in e for e in self.errors(body)), body)

    def test_generated_workload_row_is_rejected(self):
        self.assertTrue(any('review-workload' in e for e in self.errors('<p class="review-workload">추가 연습 · 소문항 6묶음 · 예상 30분(추정)</p>')))

    def test_companion_markdown_check_rejects_public_source_locator(self):
        from html2md import check_md
        with tempfile.TemporaryDirectory() as tmp:
            html = Path(tmp) / 'note.html'
            md = Path(tmp) / 'note.md'
            html.write_text('<html><body><main><p>핵심</p></main></body></html>', encoding='utf-8')
            md.write_text('핵심\n\n(1007 STT L182–186, Part 04)', encoding='utf-8')
            self.assertTrue(any('public-source-location' in e for e in check_md(html, md)))


if __name__ == '__main__':
    unittest.main()
