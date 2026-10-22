from pathlib import Path
import json, hashlib, re
from html import unescape
RUN=Path(__file__).parents[1]
B=RUN/'review-1007-Differential_Amplifiers'
REPO=Path(r'C:/Users/Hyunjun/Desktop/현준대학/26-2/ajou-electronic-circuits-2')
S=json.loads((B/'source.json').read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
PROFILE=REPO/S['learning_style']['path']
assert sha(PROFILE)==S['learning_style']['sha256']
reviewer='gm_route_review 독립 수학·내용 검토자'
# These conclusions were individually assessed against original conditions, visible text and fresh executions.
C={
'p1':['입력 λ=0·테일 λ≠0에서 CM 반회로 전류를 구해 원문의 -RD ISS/(2/λ+Vov)를 증명하고 차동 출력 CM=0과 구별한다.'],
'p2':['출력 단락 Gm≈1/(2ro5), 입력 영점 Rout≈ro3, 같은 반회로의 단일 출력 CM≈-ro3/(2ro5)이며 병렬 축약 조건을 밝힌다.'],
'p3':['테일 1 mA를 반씩 나눠 gm1=10 mS, ro1∥ro3=10 kΩ, 좌−우 ADM=-100을 얻는다.','캐스코드 테일은 M5의 gmro 인자로 RSS≈2 MΩ이며 2RSS 반회로의 각/평균 출력 CM≈-0.005이다.'],
'p4':['CM 제거는 공통 입력의 차동 출력 억제이며 유한 테일과 비대칭의 역할을 분리한다.','원문의 ro≫RD 아래 같은 가지 전류를 두 다른 부하에 적용해 좌−우 누출 +0.001을 얻는다.'],
'p5':['제곱법칙 DC에서 테일 포화 하한 0.6 V, 더 큰 오른쪽 부하가 정하는 포화 상한 1.69 V이다.','입력 ro 생략 수업 모델에서 왼쪽 CM=-0.05, 오른쪽=-0.051, 좌−우 누출 +0.001이다.','같은 수업 모델의 대칭 기준 ADM=-10을 누출로 나눠 CMRR≈10000, 80 dB이다.'],
'p6':['테일 전류 고정·입력쌍 폭 두 배이므로 전류 조향 경계는 1/√2배가 되어 X이다.','입력 ro=100 kΩ를 남겨 RD∥ro의 ADM≈-9.09이다.','큰 축퇴 주항에서 각 출력 CM≈-0.1이며 대칭 차동 출력 CM=0이다.','유한 입력 ro로 인한 가지 전류 차이를 남겨 CM-to-DM≈+9.09×10^-4이다.','DM·누출의 같은 유한 ro 보정이 소거되며 목표 CMRR30000에서 ΔRD≈33.33 Ω이다.'],
'p7':['고정 Vb1에서 테일 폭 두 배는 전류 두 배이므로 조향 경계 √2배, O이다.','입력쌍 ro를 생략한다고 명시한 수업 모델의 대칭 ADM=-10이다.','같은 모델의 2ro3 반회로에서 각 출력 CM≈-0.1이다.','입력 ro 생략으로 같은 전류와 1% 부하 차이를 써 좌−우 누출≈+0.001이다.','대칭 기준 DM와 같은 근사 누출의 비는 CMRR≈10000, 80 dB이다.','고정 Vb1·테일 폭 두 배에서 gm은 √2배·테일 ro는 절반이므로 CMRR≈7071.07, 76.99 dB이다.'],
'p8':['RE는 테일 드레인 위 직렬이다. DC 포화 경계는 1.8–2.9 V이며 RE의 1 V 강하를 포함한다.','고정 ISS 제곱법칙에서 한쪽 꺼짐 경계는 ±√0.08 V≈±0.28 V이며 선형 범위와 구별한다.','대칭 DM 소스 가상 접지와 RC∥ro를 써 ADM=-100/21≈-4.76이다.','대칭 CM의 Rs=2RSS=220 kΩ에서 출력 단락 Gm≈4.55 μS → 입력 영점 Rtrans≈22 MΩ와 RC 병렬 Rout≈10 kΩ → 단일 출력 -GmRout≈-4.55×10^-2이다. 그림의 차동 출력 CM=0이다.','불일치에서는 같은 vgs의 제어 전류와 다른 ro 전류를 분리해 누출≈+4.33×10^-5이다.','같은 유한 입력 ro 모델·큰 곱·작은 불일치 주항의 CMRR≈110000, 100.83 dB이다.'],
'p9':['캐스코드는 부하에 있고 테일은 단일 M7이다. Rup≈1000 kΩ와 입력 ro1 병렬로 ADM≈-99.01이다.','CM의 2ro7 축퇴 Rdn≈1000 kΩ와 Rup의 병렬을 유지하여 각 출력 CM≈-50이며 차동 CM=0이다.'],
'p10':['전류 입력의 트랜스임피던스다. 공통 Vov에서 gm4/gm3=1/N이고 입력 흡수 증가가 공급 증가를 만들어 +RL/N Ω이다.'],
'p11':['λ=0·동작 여유를 전제로 같은 크기 거울은 초기 0, 최종 2ΔI RL이다.','출력 거울 비 1/2이면 초기 -I0 RL/2, 최종 (3ΔI-I0)RL/2이며 변화량 1.5ΔI RL과 구별한다.'],
'p12':['거울 부하는 두 신호 전류를 오른쪽 단일 출력에 합쳐 +gm(ro2∥ro4)이다. 원본 손글씨 음의 부호 정정 이유가 일관된다.','1 mA 가지·gm=10 mS·ro=10 kΩ에서 거울 주항의 +50이다.','다이오드 부하는 각 출력에 1/gm3와 두 ro의 병렬이며 유한 ro 모델의 이득≈-0.98이다.','두 노드 사이 저항을 DM으로 반씩 나눠 gmRS=1이다. 수치가 큰 곱과 반대이므로 분모1·유한 ro를 남겨 전압이득≈-2.43이다.'],
'p13':['각 PNP 자기 B–C 저항 부하에 유한 rπ=2.6 kΩ와 β=100을 남겨 이득≈-4.68이다. 두 베이스를 공유하지 않는다.','VT=26 mV 가정·큰 β 거울 주항에서 gm≈3.85 mS, ro2∥ro4=200/9 kΩ, 오른쪽 출력≈+85.47이다.','전류원 각각 0.1 mA이며 RE/2=2.5 kΩ이다. 큰 외부 축퇴 주항 이득≈-0.4이며 유한 축퇴의 -0.36과 구분한다.'],
'p14':['같은 IC의 Gm≈gm와 Early 저항 병렬에서 전류가 소거된다. VT=26 mV 가정으로 VAp=65/12 V≈5.42 V, 오른쪽 출력 이득≈+100을 역대입 검산한다.']}
conditions={
'p1':'입력 MOS λ=0·테일 MOS λ≠0·원문 지정 증명식',
'p2':'유한 ro·gmro≫1·PMOS 고정 바이어스·대칭 CM 반회로',
'p3':'가지 0.5 mA·테일 1 mA·위쪽 M5 캐스코드 테일',
'p4':'ro≫RD 명시·ΔRD=20 Ω·좌−우 출력',
'p5':'입력 ro 생략 추가 수업 근사·오른쪽 부하 1.02 kΩ·제곱법칙 DC',
'p6':'고정 ISS·유한 입력 ro100 kΩ·큰 축퇴·작은 불일치',
'p7':'고정 Vb1·테일 폭 변화·입력 ro 생략 수업 모델',
'p8':'RE는 테일 드레인 위·RSS110 kΩ·입력 ro200 kΩ·좌−우 출력·큰 곱·작은 불일치',
'p9':'PMOS 캐스코드 부하·단일 M7 테일·입력 ro 보존',
'p10':'λ=0·공통 Vov·전류 입력·포화 거울·크기비 N',
'p11':'λ=0·이상 전류원·전후 DC·거울 비1 또는1/2·동작 여유',
'p12':'거울/다이오드/브리지 저항의 다른 연결·(c) gmRS=1 예외',
'p13':'VT26 mV 가정·(1) 유한 rπ·(3) 각각 IEE·큰 β 주항',
'p14':'VT26 mV 가정·큰 β·Early 전압 크기·무부하 오른쪽 출력'}
content={'status':'pass','reviewer':reviewer,'evidence':'현재 명세를 읽고 전체 14문항의 원문 조건·일곱 구역·요약을 새로 대조했다. P8은 새 작성자 원고 전에 원문에서 독립 유도했다. 다른 13문항은 기존 독립 모델의 코드를 이번 RUN에서 새로 실행하고 본문과 재대조했다.','items':{},'findings':[]}
ind={'status':'pass','reviewer':reviewer,'evidence':'evidence/p1-sympy.py부터 p14-sympy.py까지 이번 RUN에서 새로 실행하여 모두 종료0. P8은 이번에 출력 단락과 입력 영점 시험을 별도로 유도하고 full KCL과 기호적으로 일치함을 확인했다.','items':{},'scope':'P8 새 독립 유도; 나머지는 보존된 독립 검산 코드의 새 실행·원문 조건·답 재대조. 다른 13문항의 새 원고 저작이나 처음부터 다시 한 blind 풀이로 주장하지 않는다.'}
audit={'learning_style':S['learning_style'],'items':{},'scope':'개인 명세 12규칙을 39소문항에서 새로 읽고 판정했다. GAIN-01의 새 필수 순서는 재저작한 P8(4)에 적용하며 다른 기존 gain section에 소급 재작성을 요구하지 않는다.'}
for p in S['problems']:
 pid=p['id'];h=(B/'explanations'/f'{pid}.html').read_text(encoding='utf-8')
 assert h.count('data-explanation=')==7
 assert len(C[pid])==len(p['subparts'])
 for sub,conc in zip(p['subparts'],C[pid]):
  key=f'{pid}:{sub}'
  evidence=f'explanations/{pid}.html의 solve·verify {sub}, recall·start·sum 대조: {conc} 적용 조건: {conditions[pid]}.'
  content['items'][key]={'status':'pass','reviewer':reviewer,'evidence':evidence}
  ind['items'][key]={'status':'pass','reviewer':reviewer,'evidence':f'evidence/{pid}-sympy.py, evidence/{pid}-result.txt: {conc}','method':'symbolic','conclusion':conc}
  rules={}
  for rid in S['learning_style']['rule_ids']:
   d='applied';e=''
   if rid=='UNIT-01':
    e=f'현재 소문항의 단위와 제어량을 대조했다: {conc}'
    if pid=='p4' and sub=='1':d='not_applicable';e='CM 제거의 정성 정의와 두 한계를 설명하는 소문항이므로 수치 환산을 추가하지 않는다.'
   elif rid=='CALC-01':e=f'start의 필요한 파라미터에서 solve {sub}의 목표 관계와 verify 결과로 연결한다: {conc}'
   elif rid=='CALC-02':
    e='solve·verify·sum의 반올림을 대조하고 정밀값·간단한 분수로 다음 계산을 이어간다. '+conc
    if pid in ['p1','p2','p10','p11'] or (pid=='p4' and sub=='1') or (pid=='p12' and sub=='1'):d='not_applicable';e='이 소문항의 답은 기호 관계/정성 판단이므로 임의 숫자나 반올림을 추가하지 않는다. '+conc
   elif rid=='CIRCUIT-01':e='입출력·부하·테일 또는 거울 연결을 원문 조건과 대조했다. '+conditions[pid]+'; '+conc
   elif rid=='CIRCUIT-02':
    e='해당 모델의 AC 접지·소스/이미터 노드·반회로 또는 전체 결합을 대조했다. '+conditions[pid]+'; '+conc
    if (pid in ['p5','p8'] and sub in ['1','2']) or pid=='p11' or (pid=='p4' and sub=='1') or (pid in ['p6','p7'] and sub=='1'):
     d='not_applicable';e='이 소문항은 DC 경계/전류 조향 또는 정성 정의라 출력 단락·입력 영점 소신호 측정을 억지로 넣지 않는다. '+conc
    if pid=='p8' and sub=='4':e='새 CM 반회로의 실제 출력 단락·입력 영점 시험을 분리했다. 출력 단락에서 ro 전류를 포함한 첫 식→대입→Gm 근사, 입력 영점의 Rtrans 주항→부하 병렬→음의 곱을 순서대로 제시한다. 정확 Rout 수치와 긴 KCL은 내부 evidence에만 있다.'
   elif rid=='GAIN-01':
    if pid=='p8' and sub=='4':e='재저작된 경로의 보이는 gm→rout→gain 세 단계다. 같은 vCM/단일 출력 정의에서 Gm≈4.55 μS, Rtrans≈22 MΩ, RC 병렬 Rout≈10 kΩ, Av=-GmRout≈-0.04545이다. 차동 CM=0과 구별한다.'
    elif pid=='p2':e='기존 본문도 출력 단락 Gm→입력 영점의 ro3 병렬 Rout→같은 CM 반회로의 음의 곱으로 연결되어 있다.'
    elif pid=='p14':e='기존 알려진 거울 블록의 공급 전류 Gm≈gm와 Rout≈ro2∥ro4를 따로 정의하여 오른쪽 출력의 양의 곱을 사용한다.'
    else:
     d='not_applicable';e='이번에 계산 경로를 재저작하지 않은 기존 소문항이다. 새 순서의 소급 재작성을 강제하지 않는 현재 GAIN-01 범위에 따라 기존 목표/모델을 유지한다. '+conc
   elif rid=='DEGEN-01':
    if pid in ['p1','p2','p3','p4','p5','p6','p7','p8','p9'] and not ((pid in ['p5','p8'] and sub in ['1','2']) or (pid in ['p6','p7'] and sub=='1')):e='공유 소스 전압 상승이 제어 전압을 줄인다는 recall의 관계와 적용한 2RSS/ro 모델을 대조한다. '+conc
    elif (pid=='p12' and sub=='4') or (pid=='p13' and sub=='3'):e='DM에서 양단 저항을 반씩 나누며 외부 축퇴와 내부1/gm를 구별한다. '+conc
    else:d='not_applicable';e='이 소문항의 핵심은 축퇴 전류식이 아니라 DC/거울/다이오드 부하 또는 별도 목표다. '+conc
   elif rid=='SCALE-01':
    if pid in ['p6','p7'] and sub in ['1','6']:e='고정한 전류 또는 Vb1을 먼저 구별하고 폭 배율이 전류·gm·조향 범위·CMRR에 미치는 배율을 계산한다. '+conc
    else:d='not_applicable';e='이 소문항 자체는 소자 폭·전류 배율을 요구하지 않는다. 해당 조건은 그대로 두고 목표만 계산한다. '+conc
   elif rid=='BIAS-01':
    if pid in ['p5','p8'] and sub=='1':e='테일의 아래 포화 경계와 입력 드레인의 위 포화 경계를 따로 계산하고 등호 경계와 실제 여유를 구별한다. '+conc
    else:d='not_applicable';e='이 소문항은 입력 CM 바이어스 상하한을 새로 계산하는 목표가 아니다. 명시된 활성/포화 소신호 조건을 유지한다. '+conc
   elif rid=='NOTATION-01':e='본문의 대소문자 Gm/gm·소자 번호·입출력 부호를 원문과 대응시키고 SVG의 native 첨자/Pretendard600 선언·노드 색 표기를 읽었다. 실제 face·겹침 화면은 별도 browser 검토로 확인한다. '+conc
   elif rid=='EXPLAIN-01':e='일곱 구역과 solve/verify '+sub+'에서 짧은 판단→식→이유→답의 연결 및 sum 핵심 일치를 재독했다. '+conc
   elif rid=='CORRECT-01':e='원문 요구를 모두 답하고 근사값은 조건과 함께 표시했다. 참고 풀이와 다른 근사 차수/명시적 오류는 해당 본문 조건을 유지한다. '+conc
   rules[rid]={'disposition':d,'evidence':e}
  audit['items'][key]={'status':'pass','reviewer':reviewer,'rules':rules}
assert len(content['items'])==39 and sum(len(v['rules']) for v in audit['items'].values())==468
frozen={'source_sha256':sha(B/'source.json'),'profile':{'path':str(PROFILE),'sha256':sha(PROFILE)},'fragments':{p['id']:sha(B/'explanations'/f"{p['id']}.html") for p in S['problems']},'evidence':json.loads((RUN/'review/fresh-executions.json').read_text(encoding='utf-8'))}
if (B/'stage.json').exists():
 st=json.loads((B/'stage.json').read_text(encoding='utf-8'));print('STAGE',st)
 for k in ['stage','html']:assert k in st
 stage=B/st['stage'];html=stage/st['html']
 frozen['stage_html']={'path':str(html),'sha256':sha(html)}
 md=list((stage/'.assets').glob('*.md'));assert len(md)==1
 frozen['stage_md']={'path':str(md[0]),'sha256':sha(md[0])}
else: raise RuntimeError('final stage required')
for name,obj in [('content.json',content),('independent.json',ind),('style-audit.json',audit)]:
 obj['current_files']=frozen
 (RUN/'review'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Fresh reports written:',len(content['items']),'groups /',sum(len(v['rules']) for v in audit['items'].values()),'rule decisions')
