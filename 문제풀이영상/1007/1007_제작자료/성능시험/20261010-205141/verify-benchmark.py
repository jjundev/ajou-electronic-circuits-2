from pathlib import Path
import subprocess,json,hashlib,re,statistics,concurrent.futures,sys
P=Path(sys.argv[1]).resolve();FF='/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg';results=json.loads((P/'results.json').read_text());out=P/'verification';out.mkdir(exist_ok=True)
progress=P/'verification-progress.json'
def note(s):progress.write_text(json.dumps({'state':s}));print(s,flush=True)
def run(args):return subprocess.run([FF,'-v','error',*map(str,args)],capture_output=True,check=True)
def digests(row):
 name=row['case'];f=P/row['output'];note('frame decode: '+name)
 r=run(['-threads','2','-i',f,'-map','0:v:0','-an','-f','framemd5','-'])
 (out/(name+'-framemd5.txt')).write_bytes(r.stdout)
 h=[l.split(',')[-1].strip() for l in r.stdout.decode().splitlines() if l and not l.startswith('#')]
 assert len(h)==7220
 return name,h
render=[r for r in results if r['case'].startswith('w')]
checks={'frame_count':7220,'full_decoded_frames':{},'pixel_comparisons':{},'cross_codec_metrics':{},'resources_bound':'One-second sampled sum of process RSS; may double-count shared pages. Swap is system-wide.'}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 frames=dict(pool.map(digests,render))
reference=frames['w2-cpu-r1']
for name,h in frames.items():
 diff=[i for i,(a,b) in enumerate(zip(reference,h)) if a!=b]
 checks['full_decoded_frames'][name]=len(h)
 checks['pixel_comparisons'][name]={'differing_frames':len(diff),'first_differences':diff[:20]}
 # Encoded pixels across codecs can differ even with identical source capture.
for case1,case2,crop in [('w2-cpu-r1','w4-gpu-r1',None),('captions-current','captions-fast',None),('captions-current','captions-hardware',None),('captions-current','captions-hardware','crop=1920:180:0:900')]:
 a=next(r for r in results if r['case']==case1);b=next(r for r in results if r['case']==case2)
 label=case1+'-vs-'+case2+('-caption-crop' if crop else '')
 note('SSIM comparison: '+label)
 filt='fps=3'+(','+crop if crop else '')
 r=subprocess.run([FF,'-hide_banner','-threads','2','-i',str(P/a['output']),'-threads','2','-i',str(P/b['output']),'-filter_complex_threads','1','-filter_complex',f'[0:v]{filt}[a];[1:v]{filt}[b];[a][b]ssim','-an','-f','null','-'],capture_output=True,text=True,check=True)
 (out/(label+'-ssim.log')).write_text(r.stderr)
 m=re.findall(r'All:([0-9.]+)',r.stderr);checks['cross_codec_metrics'][label]={'ssim_all':float(m[-1]) if m else None,'fps':3,'description':'Decoded output similarity to current encoder; not a lossless quality reference.'}
checks['audio_copy_hashes']={}
for case in ['captions-current','captions-fast','captions-hardware']:
 row=next(r for r in results if r['case']==case);f=P/row['output'];note('full final decode: '+case)
 run(['-threads','2','-i',f,'-f','null','-'])
 r=run(['-i',f,'-map','0:a:0','-c:a','copy','-f','adts','-'])
 checks['audio_copy_hashes'][case]=hashlib.sha256(r.stdout).hexdigest()
checks['audio_unchanged_between_caption_trials']=len(set(checks['audio_copy_hashes'].values()))==1
checks['source_inventory_unchanged']=json.loads((P/'source-hashes-before.json').read_text())==json.loads((P/'source-hashes-after.json').read_text())
book=json.loads((P/'delivered-hashes-before.json').read_text());checks['delivered_inventory_unchanged']=all(hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()==h for path,h in book.items());checks['delivered_inventory_count']=len(book)
# Visual samples at every stage area are saved for direct review.
from PIL import Image,ImageDraw
sample_times=[5,35,65,95,125,155,185,215]
for name in ['captions-current','captions-hardware']:
 row=next(r for r in results if r['case']==name);sheet=Image.new('RGB',(1280,4*390),'#e5e5e5');draw=ImageDraw.Draw(sheet)
 for i,t in enumerate(sample_times):
  b=run(['-ss',t,'-i',P/row['output'],'-frames:v','1','-f','image2pipe','-vcodec','png','-']).stdout
  f=out/f'{name}-{t}s.png';f.write_bytes(b);im=Image.open(f).convert('RGB');im.thumbnail((640,360));x=(i%2)*640;y=(i//2)*390;sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f'{name} {t}s',fill='#111')
 sheet.save(out/(name+'-contact.png'))
checks['visual_review']='pending direct inspection';(out/'report.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False));note('verification automated checks complete; direct visual review pending')
print(json.dumps(checks,ensure_ascii=False),flush=True)
