from pathlib import Path
import json,re,subprocess
from solution_video.util import read,write,file_hash
from solution_video.subtitles import caption_srt_matches
r=Path(Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap/run-path').read_text());p=r/'verification/caption-wrap-before-after.json';b=read(p);old=Path(b['source_run'])
assert len(b['wav_hashes'])==66
for n,h in b['wav_hashes'].items():assert file_hash(r/n)==h==file_hash(old/n),n
for n,h in b['preserved_hashes'].items():assert file_hash(r/n)==h==file_hash(old/n),n
assert file_hash(old/'renders/final.mp4')==b['original_final_sha256']
a=(old/'renders/captions.srt').read_text().strip().split('\n\n');c=(r/'renders/captions.srt').read_text().strip().split('\n\n');assert len(a)==len(c)==47
for x,y in zip(a,c):
 xx,yy=x.splitlines(),y.splitlines();assert xx[:2]==yy[:2]
 assert ' '.join(' '.join(xx[2:]).split())==' '.join(' '.join(yy[2:]).split())
assert sum(x!=y for x,y in zip(a,c))==4
assert c[24].splitlines()[2:]==['저항으로 흐르는 전류는','(I₀ + ΔI) − (I₀ − ΔI)입니다.']
assert caption_srt_matches(read(r/'source/timeline.json'),r/'renders/captions.srt')
video=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(r/'renders/final.mp4')]))
v=next(s for s in video['streams'] if s['codec_type']=='video');assert (int(v['nb_frames']),v['width'],v['height'],v['r_frame_rate'])==(7220,1920,1080,'30/1')
audio_hashes={str(p):subprocess.check_output(['/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg','-v','error','-i',str(p),'-map','0:a','-c','copy','-f','hash','-hash','sha256','-']).decode().strip() for p in [old/'renders/final.mp4',r/'renders/final.mp4',r/'renders/master.mp4']}
assert len(set(audio_hashes.values()))==1
b['after']=dict(final_sha256=file_hash(r/'renders/final.mp4'),srt_sha256=file_hash(r/'renders/captions.srt'),total_frames=7220,changed_cues=4,cue_count=47,audio_stream_hashes=audio_hashes,paid_requests=0)
write(p,b)
rows=read(r/'verification/caption-wrap-changes.json')
text=['# 자막 줄바꿈 검토','', '기존 47개 청크 중 4개의 줄바꿈만 변경했습니다. 문구·교체 시간·음성·7,220프레임·회로 필기를 유지했습니다.','', '| cue | 시각 | 이전 | 수정 |','|---|---|---|---|']
for row in rows:text.append('| '+str(row['cue'])+' | '+row['time']+' | '+' / '.join(row['before'])+' | '+' / '.join(row['after'])+' |')
text+=['','수식 전체를 한 줄에 놓을 수 있으면 설명과 수식을 나눕니다. 중첩 괄호·분수·식별자는 보호하고 연산자는 다음 항에 붙입니다. 긴 식이 안전하게 두 줄에 들어가지 않으면 자동 축약이나 시간 분할 대신 저작 오류로 알립니다.','', '## 실제 영상 화면','']
for row in rows:text+=['![cue '+str(row['cue'])+']('+row['frame']+')','']
text+=['## 보존 및 검증','', '- 원본 실행과 최종 영상은 보존했습니다.','- WAV 66개, narration.wav, master, manifest, timeline, 회로 필기 파일 SHA256이 모두 동일합니다.','- 기존 final·새 final·master의 오디오 스트림 SHA256이 동일합니다.','- 원본 렌더링 입력은 재조립해 비교했습니다. 복사된 이미지/회로 SVG 경로와 해당 metadata 해시만 바뀌었고 실제 영상 내용은 동일합니다.','- 추가 유료 TTS 요청은 0입니다.','- 실제 음성 의미 청취는 이번 작업에서 수행하지 않았습니다. 기존 unverified를 유지합니다.','- 커밋·푸시·publish·latest 변경은 수행하지 않았습니다.','', '최종 SHA256: `'+b['after']['final_sha256']+'`','']
(r/'verification/자막 줄바꿈 검토.md').write_text('\n'.join(text),encoding='utf-8')
print('PASS: 66 WAVs+mixed PCM/master/manifest/timeline/ink preserved; 47 cue times unchanged; 4 layouts changed; 7220 frames; final audio stream exact; paid0')

from solution_video.verify import verification_fingerprint
report=read(r/'verification/report.json')
assert report['input_hash']==verification_fingerprint(r)
assert report['final_sha256']==file_hash(r/'renders/final.mp4')
assert {k:v['status'] for k,v in report['checks'].items() if v['status']!='passed'}=={'audio_meaning':'unverified'}
assert sum(v['status']=='passed' for v in report['checks'].values())==12
assert not report['complete'] and report['live_audio']=='unverified'
review=read(r/'verification/visual-review.json')
assert all(file_hash(r/n)==sha for n,sha in review['evidence'].items())
w=Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap');suite=(w/'full-suite-reviewed.log').read_text()
assert re.search(r'^Ran 250 tests ',suite,re.M) and re.search(r'^OK \(skipped=2\)$',suite,re.M)
print('PASS: current report fingerprint/12 checks; visual evidence hashes; final 250 suite; audio unverified')
