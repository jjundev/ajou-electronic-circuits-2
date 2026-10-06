import importlib, json, pathlib, subprocess, sys, unittest
S=pathlib.Path(__file__).resolve().parents[1]
class PortabilityTests(unittest.TestCase):
 def test_standalone_cli_and_modules(self):
  p=subprocess.run([sys.executable,str(S/'scripts/video.py'),'--help'],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr)
  sys.path.insert(0,str(S/'scripts'))
  for name in ['lib.sources','lib.manifest','lib.state','lib.composition','lib.vertex_tts']:
   self.assertTrue(pathlib.Path(importlib.import_module(name).__file__).is_relative_to(S/'scripts'))
 def test_defaults(self):
  d=json.loads((S/'assets/defaults.json').read_text())
  self.assertEqual([d[k] for k in ['voice','width','height','fps','sample_rate','budget_usd']],['Aoede',1920,1080,30,24000,None])
