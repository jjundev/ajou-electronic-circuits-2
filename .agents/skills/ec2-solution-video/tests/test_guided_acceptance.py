from fixtures import *
import importlib
from solution_video.util import read,write
class GuidedAcceptanceTests(Sandbox):
 def guided(self):
  try:from guided_acceptance import author_guided
  except ImportError:self.fail('guided author missing')
  import video
  from solution_video.sources import discover
  from unittest.mock import patch
  pairs=discover(REPO,'1002',['E10.13'])
  with patch.object(video,'discover',return_value=pairs):batch=video.prepare_batch(self.run,'1002',['E10.13'],False)
  run=batch/read(batch/'batch.json')['items'][0]['run'];result=author_guided(run)
  return run,result
 def test_four_core_connections_and_exact_source_preservation(self):
  run,result=self.guided()
  self.assertEqual(len(result['core_step_ids']),4)
  lesson=read(run/'source/lesson.json');m=read(run/'source/manifest.json');l=read(run/'layers/layers.json')
  self.assertEqual([r['step_id'] for r in lesson['steps'] if r['mode']=='circuit'],result['core_step_ids'])
  for key,objects in [('glyph_ids',l['glyphs']),('shape_ids',l['shapes'])]:
   ids=[v for s in l['map']['steps'] for v in s[key]]
   self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),{o['id'] for o in objects})
  self.assertTrue(all(s['text'].strip() and s['caption_text'].strip() for s in m['segments']))
  self.assertIn('알 오 원',' '.join(s['text'] for s in m['segments']));self.assertIn('r_O1',' '.join(s['caption_text'] for s in m['segments']))
  self.assertNotIn('알 오 원',' '.join(s['caption_text'] for s in m['segments']))
  from solution_video.annotations import load_teaching
  from solution_video.lesson import load_lesson
  self.assertIsNotNone(load_lesson(run,m,l,load_teaching(run,m,l)))

 def test_fake_audio_never_approves(self):
  run,_=self.guided();m=read(run/'source/manifest.json');l=read(run/'layers/layers.json')
  from solution_video.annotations import load_teaching
  from solution_video.teaching import build_teaching_timeline
  from solution_video.writing import default_writing
  from solution_video.review_adapter import default_config
  from solution_video.narration_pacing import analyze_narration_pacing
  audio=[make_audio(s['id'],24000,run) for s in m['segments']]
  t=build_teaching_timeline(m,l,audio,default_config(),default_writing(),load_teaching(run,m,l))
  self.assertEqual(analyze_narration_pacing(t,audio,run)['status'],'review-required')
  self.assertFalse((run/'verification/audio-review.json').exists())
 def test_guided_caption_semantic_coverage(self):
  from solution_video.subtitles import split_caption,caption_units
  run,_=self.guided();segments=read(run/'source/manifest.json')['segments']
  self.assertEqual(len(segments),20)
  output=[]
  for seg in segments:
   with self.subTest(segment=seg['id']):
    text=seg['caption_text'];chunks=split_caption(text)
    self.assertEqual(' '.join(' '.join(c.split()) for c in chunks),text)
    self.assertTrue(all(len(c.splitlines())<=2 and all(len(line)<=34 for line in c.splitlines()) for c in chunks))
    self.assertEqual(len(chunks),len(caption_units(text)))
    self.assertTrue(all(c.endswith((',', '.')) for c in chunks))
    output.extend(chunks)
  for symbol in ['r_O1','r_O3','g_m1']:self.assertIn(symbol,' '.join(output))

 def test_repeated_original_svg_gate_stays_exact(self):
  # Rebuilding identical static SVG must not capture compositor intermediate frames.
  for attempt in range(8):
   with self.subTest(attempt=attempt):
    run,_=self.guided();gate=read(run/'verification/gate.json')
    self.assertEqual([gate[k] for k in ['pixel_diff','non_target_diff','hidden_leaks']],[0,0,0])
