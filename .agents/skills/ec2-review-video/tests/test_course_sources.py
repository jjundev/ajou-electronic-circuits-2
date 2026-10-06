import json, tempfile, unittest, unicodedata
from pathlib import Path
from _util import ROOT
from lib.sources import discover, SourceError

class CourseSourcesTest(unittest.TestCase):
 def fixture(self,r):
  n=r/'복습노트/1002';n.mkdir(parents=True)
  (n/'정리노트_1002_DM.md').write_text('note')
  (n/'복습문제_1002.pdf').write_bytes(b'%PDF questions')
  (n/'답안_1002.pdf').write_bytes(b'%PDF answers')
  (n/'problems.txt').write_text('E10.11 | gain\nP10.66 | CM\n2021-1_중간-Q3 | exam\nP10.99 | missing')
  p=r/'교과서/책/ch10/예제';p.mkdir(parents=True)
  self.md(p/'E10.11.md','E10.11','[E10.10]','![fig](../figures/f.png)')
  self.md(p/'E10.10.md','E10.10')
  self.md(p/'P10.66.md','P10.66')
  f=p.parent/'figures/f.png';f.parent.mkdir();f.write_bytes(b'png')
  e=r/'from_the_past/md/2021-1_중간';e.mkdir(parents=True)
  self.md(e/'Q3.md','2021-1_중간-Q3')
  return p,n
 def md(self,p,id,deps='[]',body=''):
  p.write_text(f'---\nid: {id}\ndepends_on: {deps}\nrefs: []\n---\n{body}')
 def test_discovers_pdf_list_and_problem_closure(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);out=discover(r,'1002')
   kinds=[x['kind'] for x in out['files']]
   self.assertIn('problem-list',kinds);self.assertIn('questions-pdf',kinds);self.assertIn('answers-pdf',kinds)
   self.assertEqual(kinds.count('problem-md'),4);self.assertEqual(kinds.count('figure'),1)
   self.assertEqual(out['missing_problem_ids'],['P10.99'])
   ids={x['id'] for x in out['files']}
   for link in out['relations']: self.assertIn(link['from_id'],ids);self.assertIn(link['to_id'],ids)
   self.assertEqual({x['role'] for x in out['relations']},{'depends_on','figure'})
 def test_absent_problem_list_is_optional(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);n=r/'복습노트/0902';n.mkdir(parents=True);(n/'정리노트_0902_intro.md').write_text('note')
   self.assertEqual(discover(r,'0902')['missing_problem_ids'],[])
 def test_duplicate_cycle_and_escape_rejected(self):
  for mode in ['duplicate','cycle','escape']:
   with self.subTest(mode=mode), tempfile.TemporaryDirectory() as d:
    r=Path(d);p,n=self.fixture(r)
    if mode=='duplicate':self.md(p/'dup.md','E10.11')
    if mode=='cycle':self.md(p/'E10.10.md','E10.10','[E10.11]')
    if mode=='escape':self.md(p/'E10.11.md','E10.11',body='![bad](../../../../../../escape.png)')
    with self.assertRaises(SourceError):discover(r,'1002')
 def test_explicit_sources_freeze_and_reject_outside_repo(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);f=r/'STT/강의.md';f.parent.mkdir();f.write_text('transcript')
   out=discover(r,'1002',extra_sources=(str(f),))
   rec=next(x for x in out['files'] if x['kind']=='supplemental-md')
   from lib.batch import _snapshot
   frozen=_snapshot(out,r/'run');snap=next(x for x in frozen['files'] if x['id']==rec['id'])
   f.write_text('changed');self.assertEqual((r/'run'/snap['snapshot']).read_text(),'transcript')
   with self.assertRaises(SourceError):discover(r,'1002',extra_sources=('../outside.md',))
