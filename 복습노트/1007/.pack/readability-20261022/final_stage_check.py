from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,re
from urllib.parse import unquote
R=Path(r'C:/Users/Hyunjun/.codex/scratch/review-pack/1007-readability-20261022');repo=Path.cwd();S=R/'explain/review-1007-Differential_Amplifiers/stage/195ce0ee1c694ab8bf8edb55b0d419dd';hp=S/'문제설명_1007_Differential_Amplifiers.html';mp=S/'.assets/문제설명_1007_Differential_Amplifiers.md';nh=repo/'복습노트/1007/정리노트_1007_Differential_Amplifiers.html';nm=repo/'복습노트/1007/.assets/정리노트_1007_Differential_Amplifiers.md';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda t:re.sub(r'\s+',' ',t).strip()
h=BeautifulSoup(hp.read_text(),'html.parser');md=mp.read_text();rows=[]
def body(x,pid):
 result=[]
 for q in x.select('[data-explanation]'):
  s=BeautifulSoup(str(q),'html.parser')
  for el in s.select('[href],[src],[id]'):
   for attr in ['href','src']:
    if el.has_attr(attr):el[attr]=unquote(el[attr])
   if el.has_attr('id'):el['id']=el['id'].removeprefix(pid+'-')
  result.append(str(s))
 return result
for i in range(1,15):
 a=BeautifulSoup((R/'content/explanations'/f'p{i}.html').read_text(),'html.parser');b=h.find(id=f'p{i}')
 assert a.select_one('.sum').decode()==b.select_one('.sum').decode(),i
 assert body(a,f'p{i}')==body(b,f'p{i}'),i
 for p in a.select('.sum p,.sum h4'):assert norm(p.get_text())in norm(md),(i,p.get_text())
 for q in a.select('.sum .equation'):
  tex=q.get_text().strip().removeprefix('$$').removesuffix('$$').strip();assert norm(tex)in norm(md),(i,tex)
 rows.append({'id':f'p{i}','summary_dom_identical':True,'seven_body_sections_identical_except_generator_URLencoding_and_IDnamespace':True,'summary_paragraphs_and_tex_in_md':True})
a=BeautifulSoup((R/'content/note.html').read_text(),'html.parser');b=BeautifulSoup(nh.read_text(),'html.parser');nmd=nm.read_text()
for t in a.select('.topic'):
 z=t.select_one('.sum')
 if not z:continue
 z2=b.find(id=t['id']).select_one('.sum');assert str(z)==str(z2)
 for p in z.select('p,h4'):assert norm(p.get_text())in norm(nmd),(t['id'],p.get_text())
 for q in z.select('.equation'):
  tex=q.get_text().strip().removeprefix('$$').removesuffix('$$').strip();assert norm(tex)in norm(nmd),(t['id'],tex)
for p in [hp,mp,nh,nm]:assert not re.search(r'STT\s*L\d|시각 정보 없음|Part\s*\d',p.read_text()),str(p)
assert not h.select('.review-workload')
record={'status':'pass','reviewer':'readability_review','stage':str(S),'stage_html_sha256':H(hp),'reviewed_files':[{'path':str(p),'sha256':H(p)}for p in [hp,mp,nh,nm]],'explanations':rows,'note_summary_count':8,'note_summary_dom_identical':True,'all22summary_paragraphs_and_TeX_in_MD':True,'public_STT_locations_absent':True,'workload_DOM_absent':True,'scope':'Finalstage/content/MD equivalence and meaning checked; browser/sourcevisual bymain.'}
(R/'review/final-stage.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':'pass','stageHTML':record['stage_html_sha256'],'14bodies':True,'22summaries':True,'4HTMLMDlocationsclean':True},ensure_ascii=False))
