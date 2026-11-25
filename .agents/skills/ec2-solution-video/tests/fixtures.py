from pathlib import Path
import os,shutil,sys,tempfile,unittest,json,wave,hashlib
S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S/'scripts'))
REPO=S.parents[2]
# The 1002 pack and its problems as published just before commit f67ec5fa, which replaced its problem set.
FROZEN_1002=S/'tests/frozen/1002-before-f67ec5fa'
def _missing_browser():
    from solution_video.util import browser_config
    from solution_video.contracts import InputError
    if shutil.which('node') is None: return 'node missing'
    try: browser_config()
    except InputError as ex: return str(ex)
# EC2_REQUIRE_TOOLS=1 runs these tests anyway, so a missing tool fails instead of skipping.
_browser_reason=None if os.environ.get('EC2_REQUIRE_TOOLS')=='1' else _missing_browser()
needs_browser=unittest.skipIf(_browser_reason,_browser_reason or '')
# These tests require two differently built screens to match byte for byte. On Windows a few antialiased edge pixels
# differ: CPU raster fails four of them, GPU and SwiftShader fail the fifth, and WARP failed the fifth in 7 of 8 runs.
# macOS runs them all.
exact_pixels=unittest.skipIf(os.name=='nt','exact-pixel comparison depends on the Chrome rasterizer on Windows')
class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.run=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
def math_pdf(dest):
    import pymupdf as fitz
    doc=fitz.open(); p=doc.new_page(width=400,height=300)
    p.insert_text((10,30),'P10.1'); p.insert_text((110,120),'x + y = 2',fontsize=14)
    p.insert_text((130,128),'1',fontsize=8); p.draw_line((150,140),(180,140)); p.draw_rect((105,180,290,220),color=(0,0,1))
    doc.save(dest); return dest
def mapping(page):
    glyphs=[g['id'] for g in page['glyphs'] if g['bbox'][0]>=100]
    shapes=[s['id'] for s in page['shapes'] if s['bbox'][0]>=100]
    return {'work_bbox':[100,80,300,240],'steps':[{'id':'solution','glyph_ids':glyphs,'shape_ids':shapes}], 'answer_step_id':'solution'}
def make_audio(segment_id,samples,run):
    p=run/(segment_id+'.wav'); p.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(p),'wb') as w: w.setparams((1,2,24000,0,'NONE','')); w.writeframes(b'\0\0'*samples)
    return dict(id=segment_id,path=p.relative_to(run).as_posix(),samples=samples,rate=24000,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
