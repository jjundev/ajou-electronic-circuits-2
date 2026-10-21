"""Synthetic, reviewed v1 publication: every digest comes from real fixture bytes."""
import base64
import hashlib
import json
from pathlib import Path
import unicodedata
from urllib.parse import quote

import paths
from learning_style import read_style, PERSONALIZED_REVIEW_POLICY


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


class OverlayBundle:
    def __init__(self, root):
        self.repo = root.resolve() / 'repo with spaces'
        self.stage = self.repo / '복습노트/1008'
        self.data = self.stage / '.assets/자료_문제설명_1008_샘플'
        self.data.mkdir(parents=True)
        self.build_dir = root / 'moved build'
        self.path = self.data / 'answer-overlay.json'
        self.ids = ['E9.05', 'E9.06']
        profile = self.repo / 'docs/learning/solution-style.md'
        profile.parent.mkdir(parents=True)
        profile.write_text('# Style\n### UNIT-01\nUse units.\n')
        snapshot = read_style(self.repo)
        source = self.stage / '.assets/problems.txt'
        source.write_text('E9.05 | first\nE9.06 | second\n')
        (self.stage / '정리노트_1008_샘플.html').write_text('<p>Note</p>')
        self.source_files = [source]
        for pid, ask in [('E9.05', '- Find ratio.'), ('E9.06', '- (a) Find current.\n- (b) Find gain.')]:
            path = self.repo / f'교과서/마이크로전자회로/ch09/예제/{pid}.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'''---
id: {pid}
kind: 예제
number: "9.{int(pid[-2:])}"
section: "9.1 Test"
book_page: 455
pdf_page: 4
figures: []
depends_on: []
refs: []
---
# 예제 {pid} — Fixture

## 원문
Find the value.

## 조건
- Current is $0.5$ mA.

## 구할 것
{ask}

## 풀이
### Old step
- Old calculation.
### 답
- Old answer.
''', encoding='utf-8')
            self.source_files.append(path)
        self.source_files.append(profile)
        self.asset = self.stage / '.assets' / unicodedata.normalize('NFD', '그림 공백.png')
        self.asset.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='))
        asset_name = quote('.assets/그림 공백.png', safe='/')
        steps = [{'subpart': 'main', 'label': '판단 & 계산', 'html': f'<p>Core calculation.</p><figure><img src="{asset_name}" alt="circuit"></figure><p><a href="elsewhere.html">Details</a></p>'}]
        self.overlay = {'schema_version': 1, 'review_policy_version': PERSONALIZED_REVIEW_POLICY,
            'range': '1008', 'slug': '샘플', 'learning_style': snapshot, 'input_hash': 'a'*64,
            'source_inputs': {p.relative_to(self.repo).as_posix(): digest(p) for p in self.source_files},
            'problems': [
                {'id': 'E9.05', 'explanation_id': 'p1', 'subparts': ['main'], 'steps': steps,
                 'answers': [{'subpart': 'main', 'html': '<p>$W/L=15.625$</p>'}]},
                {'id': 'E9.06', 'explanation_id': 'p2', 'subparts': ['a', 'b'],
                 'steps': [{'subpart': s, 'label': 'Calculate', 'html': '<p>Derive.</p>'} for s in ['a','b']],
                 'answers': [{'subpart': s, 'html': f'<p>Answer {s}</p>'} for s in ['a','b']]}
            ], 'assets': {asset_name: digest(self.asset)}}
        source_hash = hashlib.sha256(''.join(digest(p) for p in self.source_files).encode()).hexdigest()
        self.manifest = {'version': 1, 'profile': 'review', 'range': '1008', 'slug': '샘플',
            'source': str(source), 'source_sha256': source_hash, 'review_policy_version': PERSONALIZED_REVIEW_POLICY,
            'inputs': [str(p) for p in self.source_files], 'input_hash': 'a'*64,
            'destination': str(self.stage), 'repo': str(self.repo), 'source_resources': {}, 'reading_key': '1008',
            'problems': [{'id':'p1', 'subparts':['main']}, {'id':'p2', 'subparts':['a','b']}],
            'learning_style': snapshot, 'answer_overlay': self.path.relative_to(self.stage).as_posix(), 'files': {}}
        passed = {'status': 'pass', 'reviewer': 'synthetic fixture', 'evidence': 'Synthetic test evidence only.'}
        keys = ['p1:main','p2:a','p2:b']
        self.validation = {'review_policy_version': PERSONALIZED_REVIEW_POLICY, 'input_hash':'a'*64,
            'references':[{'path':str(profile),'sha256':digest(profile)}],
            'source_visual':dict(passed), 'browser':dict(passed),
            'content': {**passed, 'items':{k:dict(passed) for k in keys}},
            'independent': {**passed, 'items':{k:{**passed, 'method':'exact', 'conclusion':'Fixture only.'} for k in keys}},
            'learning_style_audit': {'learning_style':snapshot, 'items':{k:{'status':'pass','reviewer':'fixture',
                'rules':{'UNIT-01':{'disposition':'applied','evidence':'Fixture step.'}}} for k in keys}}}
        self.sync()

    def sync(self):
        articles = []
        for p in self.overlay['problems']:
            groups = []
            for s in p['subparts']:
                entries = ''.join(f'<div data-solution-core="step" data-core-label="{st["label"].replace("&", "&amp;")}">{st["html"]}</div>' for st in p['steps'] if st['subpart']==s)
                entries += ''.join(f'<div data-solution-core="answer">{a["html"]}</div>' for a in p['answers'] if a['subpart']==s)
                groups.append(f'<div data-core-subpart="{s}">{entries}</div>')
            articles.append(f'<article id="{p["explanation_id"]}"><div class="layer formal solution-route" data-personalization="route"><h4>Core</h4>{"".join(groups)}</div></article>')
        (self.stage/'문제설명_1008_샘플.html').write_text('<main>'+''.join(articles)+'</main>')
        dump(self.path, self.overlay)
        files = [p for p in self.stage.rglob('*') if p.is_file() and p.name not in ('manifest.json','validation.json','problems.txt') and not p.name.startswith('정리노트_')]
        self.manifest['files'] = {p.relative_to(self.stage).as_posix():digest(p) for p in files}
        dump(self.data/'manifest.json', self.manifest)
        self.validation['artifact_hashes'] = {**self.manifest['files'], (self.data/'manifest.json').relative_to(self.stage).as_posix():digest(self.data/'manifest.json')}
        dump(self.data/'validation.json', self.validation)
