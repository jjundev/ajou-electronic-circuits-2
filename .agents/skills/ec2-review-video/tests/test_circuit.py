import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from _util import minimal_manifest
from lib.cache import atomic_json,file_hash
from lib.circuit import circuit_fingerprint,validate_circuit_review,require_circuit_review,DOMAINS

def review(run,m):
 return {'schema_version':1,'input_hash':circuit_fingerprint(run,m),'scenes':[{'scene_id':s['id'],'checks':[{'domain':d,'status':'passed','reason':'Fixture semantic comparison only','source_ids':['src-note'],'locators':['#respiration']} for d in DOMAINS]} for s in m['scenes']]}

class CircuitTest(unittest.TestCase):
 def test_report_not_in_own_fingerprint(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();before=circuit_fingerprint(r,m)
   atomic_json(r/'source/circuit-review.json',review(r,m))
   self.assertEqual(circuit_fingerprint(r,m),before);self.assertEqual(validate_circuit_review(r,m),[])
 def test_every_scene_and_domain_required(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();good=review(r,m)
   for mode in ['missing-scene','missing-domain','duplicate','unknown-source','no-locator','all-na','bad-type']:
    bad=copy.deepcopy(good);checks=bad['scenes'][0]['checks']
    if mode=='missing-scene':bad['scenes']=[]
    if mode=='missing-domain':checks.pop()
    if mode=='duplicate':checks.append(checks[0])
    if mode=='unknown-source':checks[0]['source_ids']=['unknown']
    if mode=='no-locator':checks[0]['locators']=[]
    if mode=='all-na':
     for c in checks:c['status']='not-applicable'
    if mode=='bad-type':bad['scenes']={}
    atomic_json(r/'source/circuit-review.json',bad)
    with self.subTest(mode=mode):self.assertTrue(validate_circuit_review(r,m))
 def test_modified_fragment_and_evidence_invalidates_review(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();p=r/'source/scene-fragments/scene-atp.html';p.parent.mkdir(parents=True);p.write_text('32')
   good=review(r,m);e=r/'source/numeric.json';e.write_text('32');good['evidence']=[{'path':'source/numeric.json','sha256':file_hash(e)}]
   atomic_json(r/'source/circuit-review.json',good);require_circuit_review(r,m)
   e.write_text('wrong');self.assertTrue(validate_circuit_review(r,m));e.write_text('32')
   p.write_text('64');self.assertTrue(validate_circuit_review(r,m))
   p.write_text('32');m['segments'][0]['text']='wrong';self.assertTrue(validate_circuit_review(r,m))
 def test_missing_or_stale_review_blocks_tts(self):
  from video import main,finish
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();atomic_json(r/'manifest.json',m)
   for stage in ['inputs','coverage','script']:finish(r,stage,[r/'manifest.json'])
   with patch('video.load_key',side_effect=AssertionError('must not load credentials')),patch('video.live_transport',side_effect=AssertionError('must not call API')):
    self.assertEqual(main(['tts','--run',str(r)]),1)
 def test_verified_media_does_not_override_failed_circuit_review(self):
  from lib.verify import verify_run,review_fingerprint,DOMAINS as VDOMAINS
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();p=r/'verification/e.txt';p.parent.mkdir();p.write_text('evidence')
   reports={k:{'status':'passed','input_hash':review_fingerprint(r,m),'evidence':['verification/e.txt']} for k in VDOMAINS}
   result=verify_run(r,m,reports);self.assertFalse(result['complete']);self.assertEqual(result['content']['status'],'failed')
 def test_report_or_evidence_changes_resume_from_coverage(self):
  from video import finish
  from lib.state import RunStore
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();atomic_json(r/'manifest.json',m);atomic_json(r/'source/circuit-review.json',review(r,m))
   e=r/'source/numeric.json';e.write_text('numeric')
   data=review(r,m);data['evidence']=[{'path':'source/numeric.json','sha256':file_hash(e)}];atomic_json(r/'source/circuit-review.json',data)
   for stage in ['inputs','coverage','script']:finish(r,stage,[r/'manifest.json'])
   e.write_text('changed');self.assertEqual(RunStore(r).recover(),'coverage')
 def test_changed_linked_circuit_image_invalidates_review_and_resume(self):
  from video import finish
  from lib.state import RunStore
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=minimal_manifest();atomic_json(r/'manifest.json',m)
   image=r/'assets/circuit.svg';image.parent.mkdir();image.write_text('<svg><path d="M0 0L10 10"/></svg>')
   f=r/'source/scene-fragments/scene-atp.html';f.parent.mkdir(parents=True);f.write_text('<section class="topic"><img src="assets/circuit.svg"/></section>')
   atomic_json(r/'source/circuit-review.json',review(r,m));require_circuit_review(r,m)
   for stage in ['inputs','coverage','script']:finish(r,stage,[r/'manifest.json'])
   image.write_text('<svg><path d="M0 0L20 0"/></svg>')
   self.assertTrue(validate_circuit_review(r,m))
   self.assertEqual(RunStore(r).recover(),'coverage')
   from video import main
   with patch('video.load_key',side_effect=AssertionError('stale image must not load key')):
    self.assertEqual(main(['tts','--run',str(r)]),1)
   image.unlink();self.assertTrue(validate_circuit_review(r,m))
