import json
import re
import tempfile
from urllib.parse import unquote
import unittest
from dataclasses import replace
from pathlib import Path

from _util import make_repo, fragment
from epe_contract import payload_hash
from epe_render import build_explanation, check_artifacts, artifact_hashes, names, dump
from epe_shared import parse, compact
from epe_source import load_source, sha256
from epe_types import ExplainError


class RenderTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def build(self, ids=('P10.02', '2023-1_중간-Q4'), take=None, name='stage', **kw):
        self.repo = make_repo(self.tmp / 'repo', ids=ids, **kw)
        self.src = self.repo / '복습노트' / '1007' / '.assets' / 'problems.txt'
        pack = load_source(self.src, self.repo)
        if take is not None:
            pack = replace(pack, problems=pack.problems[take])
        self.pack = pack
        fragments = {p.id: fragment(p) for p in pack.problems}
        result = build_explanation(pack, fragments, self.tmp / name, self.repo)
        return pack, fragments, result

    def test_output_names_and_reading_key(self):
        pack, _, result = self.build()
        self.assertEqual(names(pack), ('문제설명_1007_Diff_Amp', 'figures_문제설명_1007_Diff_Amp',
                                       '자료_문제설명_1007_Diff_Amp'))
        self.assertEqual(result.html.name, '문제설명_1007_Diff_Amp.html')
        self.assertEqual(result.md.name, '문제설명_1007_Diff_Amp.md')
        self.assertIn('ec2-problem-explain-review-1007-Diff_Amp', result.html.read_text(encoding='utf-8'))
        self.assertIn('전자회로2 복습 1007 문제설명', result.html.read_text(encoding='utf-8'))

    def test_figures_copied_into_owned_dir(self):
        pack, _, result = self.build()
        document = parse(result.html.read_text(encoding='utf-8'))
        main = next(document.find_all(lambda n: n.tag == 'main'))
        srcs = [n.attrs['src'] for n in main.find_all(lambda n: n.tag == 'img')]
        self.assertTrue(srcs)
        root = result.html.parent
        for src in srcs:
            self.assertTrue(src.startswith('.assets/figures_문제설명_1007_Diff_Amp/'), src)
            self.assertTrue((root / src).is_file(), src)
        self.assertEqual(check_artifacts(pack, result), [])

    def test_render_preserves_questions_and_math_offline(self):
        pack, _, result = self.build()
        text = result.html.read_text(encoding='utf-8')
        md = result.md.read_text(encoding='utf-8')
        root = parse(text)
        for p in pack.problems:
            reading = next(root.find_all(lambda n: n.attrs.get('data-source-problem') == p.id))
            fields = {n.attrs['data-source-field']: compact(n.text())
                      for n in reading.find_all(lambda n: 'data-source-field' in n.attrs)}
            self.assertEqual(fields, {'conditions': compact(p.conditions_html), 'ask': compact(p.ask_html)})
            self.assertIn(f'<a id="{p.id}"></a>', md)
        self.assertNotIn('https://cdn.', text)
        self.assertFalse(list(root.find_all(lambda n: n.tag == 'details' and 'original' not in n.classes)))
        self.assertEqual(set(artifact_hashes(result)),
                         {p.relative_to(result.html.parent).as_posix() for p in result.files})
        self.assertEqual(check_artifacts(pack, result), [])

    def test_recall_and_summary_survive_html_and_markdown(self):
        pack, _, _ = self.build(take=slice(0, 1))
        p = pack.problems[0]
        text = fragment(p).replace('<div class="sum" hidden>',
            '<div class="sum" hidden><div class="summary-group">'
            '<h4>떠올릴 개념·공식</h4><p>전치의 크기는 $n\\times m$이에요.</p></div>')
        result = build_explanation(pack, {p.id: text}, self.tmp / 'stage2', self.repo)
        self.assertEqual(check_artifacts(pack, result), [])
        html = result.html.read_text(encoding='utf-8')
        md = result.md.read_text(encoding='utf-8')
        node = next(parse(html).find_all(lambda n: n.attrs.get('data-explanation') == 'recall'))
        self.assertNotIn('hidden', node.attrs)
        for output in (html, md):
            self.assertIn('이 개념과 공식을 떠올려요', output)
            self.assertIn('떠올릴 개념·공식', output)
            self.assertIn('$n\\times m$', output)
        self.assertIn('A\\cdot A', md)

    def test_exam_without_original_builds(self):
        # Every committed exam md has an 원문 section today; an empty one must still build.
        pack, _, _ = self.build(ids=('2023-1_중간-Q4',))
        self.assertTrue(pack.problems[0].original_html.strip())
        p = replace(pack.problems[0], original_html='')
        pack = replace(pack, problems=(p,))
        result = build_explanation(pack, {p.id: fragment(p)}, self.tmp / 'stage-noorig', self.repo)
        self.assertEqual(check_artifacts(pack, result), [])
        root = parse(result.html.read_text(encoding='utf-8'))
        self.assertFalse(list(root.find_all(lambda n: 'data-original-problem' in n.attrs)))

    def test_exam_original_is_preserved(self):
        pack, _, result = self.build(ids=('2023-1_중간-Q4',))
        self.assertEqual(check_artifacts(pack, result), [])
        root = parse(result.html.read_text(encoding='utf-8'))
        self.assertEqual(len(list(root.find_all(lambda n: 'data-original-problem' in n.attrs))), 1)

    def test_original_block_before_conditions_when_present(self):
        pack, _, _ = self.build(ids=('P10.02',))
        p = replace(pack.problems[0], original_html='<p>Original English text.</p>')
        pack = replace(pack, problems=(p,))
        result = build_explanation(pack, {p.id: fragment(p)}, self.tmp / 'stage3', self.repo)
        self.assertEqual(check_artifacts(pack, result), [])
        text = result.html.read_text(encoding='utf-8')
        self.assertIn('class="original" data-original-problem', text)
        self.assertIn('<summary>원문 보기</summary>', text)
        # Dropping the preserved original is detected.
        result.html.write_text(text.replace('Original English text.', 'changed'), encoding='utf-8')
        self.assertTrue(any('원문 보존 실패' in e for e in check_artifacts(pack, result)))

    def test_problem_pdf_link_when_present(self):
        pack, _, result = self.build(take=slice(0, 1))
        anchors = list(parse(result.html.read_text(encoding='utf-8')).find_all(lambda n: n.tag == 'a'))
        hrefs = [unquote(n.attrs.get('href', '')) for n in anchors]
        self.assertTrue(any(h.endswith('복습문제_1007_Diff_Amp-문제.pdf') for h in hrefs), hrefs)
        self.assertFalse(any('원 문제 보기' in n.text() and '#' in n.attrs.get('href', '') for n in anchors))
        self.assertEqual(check_artifacts(pack, result), [])

    def test_markdown_lives_in_assets_with_rebased_links(self):
        pack, _, result = self.build(take=slice(0, 1))
        stage = result.html.parent
        self.assertEqual(result.md, stage / '.assets' / '문제설명_1007_Diff_Amp.md')
        self.assertEqual(sorted(p.name for p in stage.iterdir()), ['.assets', '문제설명_1007_Diff_Amp.html'])
        md = unquote(result.md.read_text(encoding='utf-8'))
        self.assertIn('](../복습문제_1007_Diff_Amp-문제.pdf)', md)
        self.assertEqual(check_artifacts(pack, result), [])

    def test_no_link_when_problem_pdf_missing(self):
        repo = make_repo(self.tmp / 'repo2')
        folder = repo / '복습노트' / '1007'
        for f in folder.glob('*-문제.pdf'):
            f.unlink()
        pack = load_source(folder / '.assets' / 'problems.txt', repo)
        result = build_explanation(pack, {p.id: fragment(p) for p in pack.problems}, self.tmp / 'stage4', repo)
        self.assertNotIn('원 문제 보기', result.html.read_text(encoding='utf-8'))
        self.assertEqual(check_artifacts(pack, result), [])

    def test_tampered_conditions_detected(self):
        pack, _, result = self.build(take=slice(0, 1))
        text = result.html.read_text(encoding='utf-8')
        marker = 'data-source-field="conditions">'
        end = text.index(marker) + len(marker)
        changed = text[:end] + '변조된 조건 ' + text[end:]
        result.html.write_text(changed, encoding='utf-8')
        errors = check_artifacts(pack, result)
        self.assertTrue(any('conditions 원문 보존 실패' in e for e in errors), errors)

    def test_tampered_output_detected(self):
        pack, _, result = self.build(take=slice(0, 1))
        result.html.write_text(result.html.read_text(encoding='utf-8') + '변경', encoding='utf-8')
        self.assertTrue(check_artifacts(pack, result))

    def test_manifest_records_inputs_and_bundle_hash(self):
        pack, fragments, result = self.build()
        manifest = json.loads(result.manifest.read_text(encoding='utf-8'))
        self.assertEqual(manifest['inputs'], list(pack.inputs))
        self.assertEqual(manifest['source_sha256'], pack.sha256)
        self.assertEqual(manifest['input_hash'], payload_hash(pack, fragments))
        manifest['inputs'] = manifest['inputs'][:-1]
        dump(result.manifest, manifest)
        self.assertTrue(check_artifacts(pack, result))

    def test_missing_images_and_duplicate_svg_ids_refused(self):
        pack, _, _ = self.build(take=slice(0, 1))
        p = pack.problems[0]
        with self.assertRaisesRegex(ExplainError, '경로|그림'):
            build_explanation(pack, {p.id: fragment(p).replace('<p>$A=1$부터 써요.</p>', '<p>$A=1$부터 써요.</p><img src="missing.png">')}, self.tmp / 'missing', self.repo)
        with self.assertRaisesRegex(ExplainError, '중복.*ID'):
            build_explanation(pack, {p.id: fragment(p).replace('<p>$A=1$부터 써요.</p>', '<p>$A=1$부터 써요.</p><svg><g id="a"></g><g id="a"></g></svg>')},
                              self.tmp / 'dup', self.repo)

    def test_inline_svg_ids_rewritten_per_problem(self):
        pack, _, _ = self.build()
        svg = ('<svg viewBox="0 0 10 10"><defs><clipPath id="clip"><rect width="5" height="5"/></clipPath></defs>'
               '<rect clip-path="url(#clip)" width="10" height="10"/></svg>')
        result = build_explanation(pack, {p.id: fragment(p).replace('<p>$A=1$부터 써요.</p>', '<p>$A=1$부터 써요.</p>'+svg) for p in pack.problems},
                                   self.tmp / 'stage5', self.repo)
        self.assertEqual(check_artifacts(pack, result), [])
        text = result.html.read_text(encoding='utf-8')
        self.assertIn('url(#p1-clip)', text)
        self.assertIn('url(#p2-clip)', text)

    def test_stage_must_be_empty(self):
        pack, fragments, result = self.build(take=slice(0, 1))
        with self.assertRaises(ExplainError):
            build_explanation(pack, fragments, result.html.parent, self.repo)

    def test_vendor_files_and_hashes_present(self):
        vendor = Path(__file__).resolve().parents[1] / 'assets/vendor'
        manifest = json.loads((vendor / 'provenance.json').read_text(encoding='utf-8'))
        for name, digest in manifest['files'].items():
            self.assertEqual(sha256(vendor / name), digest)
        for css in vendor.rglob('*.css'):
            for href in re.findall(r'url\([\'"]?([^\)\'"\s]+)', css.read_text(encoding='utf-8')):
                self.assertTrue((css.parent / href).is_file(), href)

    def test_raster_image_survives_markdown_and_loss_detected(self):
        pack, _, result = self.build(ids=('2023-1_중간-Q4',))
        md = result.md.read_text(encoding='utf-8')
        self.assertTrue(re.search(r'!\[[^\]]*\]\(figures_[^)]+\.png\)', md), md[:400])
        self.assertEqual(check_artifacts(pack, result), [])
        result.md.write_text(re.sub(r'!\[[^\]]*\]\([^)]+\)', '', md), encoding='utf-8')
        manifest = json.loads(result.manifest.read_text(encoding='utf-8'))
        manifest['files'][result.md.name] = sha256(result.md)
        result.manifest.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        self.assertTrue(any('래스터 그림 누락' in e for e in check_artifacts(pack, result)))

    def test_approved_fixture_artifact_hashes(self):
        from _util import approved
        pack, fragments, result = self.build(take=slice(0, 1))
        self.assertEqual(approved(pack, fragments, result)['artifact_hashes'], artifact_hashes(result))


if __name__ == '__main__':
    unittest.main()
