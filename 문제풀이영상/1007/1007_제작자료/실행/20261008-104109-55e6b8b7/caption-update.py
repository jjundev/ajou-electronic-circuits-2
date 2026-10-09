from pathlib import Path
import sys,shutil,copy
sys.path.insert(0,'.agents/skills/ec2-solution-video/scripts')
from solution_video.util import read,write,file_hash
from solution_video.manifest import content_fingerprint,validate_manifest
from solution_video.subtitles import caption_text,split_caption
r=next(Path('문제풀이영상/1007').glob('*제작자료/실행/*/videos/*')).resolve();b=r.parents[1];backup=b/'caption-original';backup.mkdir(exist_ok=True)
for name in ['source/manifest.json','source/timeline.json','source/audio.json','renders/final.mp4','renders/captions.srt','verification/report.json','state.json']:
 p=r/name;dst=backup/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
m=read(r/'source/manifest.json');old=copy.deepcopy(m)
updates={
'intro':'문제 10.72입니다. I₁은 I₀에서 I₀ + ΔI로 증가합니다. I₂는 I₀에서 I₀ − ΔI로 감소합니다. 2가지 소자 크기에서 변화 전후의 출력 전압을 구합니다.',
'write_part_0_2':'출력 노드에 들어오는 I_D4는 I₂와 저항 전류로 나뉩니다. 따라서 V_out = R_L × (I_D4 − I₂)입니다.',
'write_part_1_0':'(a)에서는 2개 소자의 폭 대 길이 비가 같습니다.',
'reason_1':'같은 크기의 M₃와 M₄를 생각합니다. I₁이 증가하면 거울을 통해 출력으로 들어오는 전류도 같은 양만큼 증가합니다. 동시에 I₂는 감소합니다. 저항으로 흐르는 전류에는 2개 변화가 같은 방향으로 더해집니다.',
'write_part_1_1':'변화 전에는 거울 전류가 I₀입니다. 출력에서 빠져나가는 I₂도 I₀이므로 차이가 0입니다. 따라서 출력 전압도 0입니다.',
'write_part_1_2':'변화 후 거울 전류는 I₀ + ΔI가 됩니다.',
'write_part_1_3':'저항으로 흐르는 전류는 (I₀ + ΔI) − (I₀ − ΔI)입니다. 증가한 전류와 감소한 전류의 효과가 함께 더해집니다.',
'write_part_1_4':'I₀끼리는 없어지고 ΔI 2개가 남습니다. 출력 전압은 2ΔI R_L입니다.',
'write_part_2_0':'(b)에서는 M₃의 폭 대 길이 비가 M₄의 2배입니다.',
'reason_2':'이번에는 M₃의 크기가 M₄의 2배입니다. 같은 게이트 전압에서 M₄의 전류는 I₁/2가 됩니다. 출력에서는 이 전류에서 I₂를 빼야 합니다. I₂의 감소량 자체는 여전히 ΔI입니다.',
'write_part_2_1':'거울 전류는 I₁/2입니다. 변화 전에는 I₀/2 − I₀이므로 출력 전압은 −I₀ R_L / 2입니다.',
'write_part_2_2':'변화 후 거울 전류는 (I₀ + ΔI)/2입니다.',
'write_part_2_3':'출력 전압은 R_L에 괄호 안 전류 차이를 곱합니다. 거울 전류 (I₀ + ΔI)/2에서 (I₀ − ΔI)를 뺍니다.',
'write_part_2_4':'이를 정리하면 ΔI의 계수는 3/2입니다. I₀의 계수는 −1/2입니다. 따라서 원문에 있는 이 두 항의 차이에 R_L을 곱합니다.',
'write_part_2_5':'변화량은 1.5ΔI R_L입니다. 같은 크기인 (a)의 2ΔI R_L보다 작습니다.',
'write_part_3_0':'답을 원본과 함께 확인합니다. (a)는 변화 전 0이고 변화 후 2ΔI R_L입니다. (b)는 변화 전 −I₀ R_L / 2이고, 변화 후 R_L × (3ΔI − I₀)/2입니다.'}
for s in m['segments']:
 if s['id'] in updates:s['caption_text']=updates[s['id']]
 caption_text(s);split_caption(s['caption_text'])
assert [s['text'] for s in old['segments']]==[s['text'] for s in m['segments']]
l=read(r/'layers/layers.json');c=read(r/'source/coverage.json');rev=read(r/'source/circuit-review.json');h=content_fingerprint(m,l,c);c['input_hash']=rev['input_hash']=h
validate_manifest(m,l,c,rev)
for name,d in [('manifest',m),('coverage',c),('circuit-review',rev)]:write(r/'source'/(name+'.json'),d)
print('updated',len(updates),'segments; speech text unchanged')
