# 1014 정리노트 독립 내용 검토

Reviewer: `/root/note_review`, 2026-10-22. 작성자가 아닌 독립 내용 리뷰어로 본문·수식·그림의 연결 의미·요약과 선발 근거를 읽었다. 아래의 pass는 내용 판정이다. 실제 조립본의 글꼴 face·글리프 간격·좁은 화면·light/dark 및 답안 PDF 발행 승인은 부모의 별도 화면/발행 evidence와 결합한다.

## Critical

- 없음.

## Important

- 없음.

## Minor

- 없음.

## 독립 판정과 범위

정리노트 14개 토픽의 내용 검토는 pass다. 최종 조립본을 다시 읽고 바인딩한 SHA-256은 `3676cf101f3d5a66c4fde57a4f74c9604806f46c252c55155bc528162ce875af`다. 현재 PROFILE의 실제 바이트 SHA-256은 `15dd74dba003093e0a3e627a7531d1b89dbc4b081ebfb2f04245d065758f62fe`로 manifest snapshot 및 12 rule IDs와 일치한다. `learning-style-audit.json`은 14×12=168개 실제 의미 판정으로 갱신했다. 이전 메인 초기 감사는 `work/note-review/main-initial-learning-style-audit.json`에 보존했다. `work/summary-audit-note.json`은 일반·교수님·주의 핵심의 124행 대응/정당한 생략과 실제 토픽/요약 텍스트를 보존한다. 14개 모두 보충 레이어가 없는 manifest 계약을 확인했다. 이 파일과 JSON은 public 학습 파일을 수정하지 않는다. `work/note-review/independent-math.json`은 독립 KCL 네 모델과 수정 graph의 101개 표본을 실행 검증한 내부 evidence다.

읽은 자료: 전체 `review-prompt.md`, `content-rules.md`, 현재 `solution-style.md`와 `problem-selection.md`; manifest, 전체 STT 요약과 범위/말실수 표, L05 s1–11 실제 텍스트 및 예고와 미진행 슬라이드의 경계; why/s0/s1/s2/s3 실제 조각과 조립 HTML의 14개 본문·직계 sum; Razavi 11장 PDF pp1–7 이미지(그중 p7은 11.1.5 도입부터 뒤 공식은 이번 수업 밖임을 확인); 선택한 13개 원본 MD의 원문·조건·모든 요구·회로 넷리스트/그림 설명; P11.01 원문 p33, P11.02/03/06/09/12 원문 p34 그림; 7개 범위 장 기출의 전체 원문과 모든 소문항·참고 풀이, 실제 2021기말 Q1/Q2 및 2023기말 Q1 그림. 이들 기출 중 4개는 서술형으로 원문에 그림이 없다. 내용 검토를 source summary나 자동 checker의 pass만으로 대신하지 않았다.

작성자 보고는 실제 `work/s0/author-report.md`, `work/s1/author-report.md`, `work/s2/author-report.json`, `work/s3/author-report.md`를 읽었다. why에는 별도 작성자 보고 파일이 없어 아래 why 적용 질문은 리뷰어가 실제 첫 설명/4단계 내용에서 만들었다.

## 독립 회로·수학 검산

- **[s0-rc-lowpass]** 출력이 C 양단이므로 `vout/vin = ZC/(R+ZC) = 1/(1+sRC)`. 낮은 주파수에서 1, 높은 주파수에서 0이다. `|ZC|=1/(omega C)`이므로 omega만 20배일 때 임피던스 크기는 1/20이지만 회로 전달비가 모든 주파수에서 정확히 1/20이라는 결론은 나오지 않는다. 본문은 둘을 혼동하지 않는다.
- **[s0-cs-cl]** 선택 모델은 포화, source AC 접지, 채널 변조/몸체효과 무시, 외부 CL만이다. 오른쪽에서 회로로 들어오는 단락전류를 양으로 정하면 출력 단락에서 `iout,sc=gm vin`, `Gm=gm`. 입력0이면 `vgs=0`이고 출력에 남는 admittance는 `1/RD+sCL`. 직접 합성으로 `Rout≈RD`부터 쓰고 `Zout=RD/(1+sRDCL)`를 얻는다. 출력 KCL `(1/RD+sCL)vout+gm vin=0`로 `Av=-Gm Zout` 음부호와 독립 대조했다. 유한 rO 대안에서는 같은 출력–접지 두 노드의 `RD||rO`를 먼저 합성한다. `Zout(s)`의 RC 모델 내 동치 전개는 금지된 전체 transistor 정확 Rout 유도가 아니다.
- **[s0-3db]** 정규화 크기 `1/sqrt(1+x²)=1/sqrt2`에서 양의 x=1. 따라서 omega3dB=1/(RDCL), f3dB=1/(2piRDCL). 상대 손실은 `20log10(1/sqrt2)=-3.010299… dB`, 진폭비는 0.707106…이다. gm,CL 고정 때 저주파 이득과 대역폭의 RD 배율이 서로 역수다. 수정된 graph path는 큰 RD 이득이 유한 주파수에서 작은 RD 이득보다 항상 크고 두 곡선이 같은 고주파 점근선에 접근한다. RD 증가로 corner가 낮아진다는 사실이 두 크기 곡선의 교차를 뜻하지 않는다.
- **[s1-transfer]** 분모근 `s=-1/(RDCL)`와 양의 corner를 구분했다. 분자 상수이므로 유한 zero는 없다. `arg H=-180°-atan(omega RDCL)`은 -180°에서 시작한 연속 branch로 올바르며 주값과 360° 차이를 허용한다. 반전 factor와 pole의 추가 위상 지연, 진폭 크기를 구별했다. proper(차수)만으로 안정성을 결정할 수 없고 약분 후 남는 pole 실수부 조건이 필요하다는 교정도 맞다.
- **[s1-bode]** `-20log10 sqrt(1+(omega/omega_p)²)`는 고주파에서 `-20log10(omega/omega_p)`로 접근한다. pole마다 기울기 -20, zero마다 +20이며 pole 세 개 후 -60 dB/dec다. 코너에서 이득이 수직으로 20 dB 뛰는 해석을 하지 않는다. 원점/복소근을 1차 양의 corner 표준꼴에 무단 적용하지 않는다.
- **[s2-cs-two-poles]** 독립 KCL은 `(vin-vX)/RS=sCin vX`, `(1/RD+sCL)vout+gm vX=0`. 두 식은 출력에서 입력으로 되먹임이 없는 삼각 구조이므로 분모 `(1+sRSCin)(1+sRDCL)`와 음의 분자 gmRD가 나온다. Gm는 gate vX 기준임이 보이고 저주파 vX=vin도 먼저 설명했다. 이후 vX/vin을 곱하므로 고주파 전체 입력 기준 Gm와 혼동하지 않는다. 같은 pole 두 개도 2차이며 총 -3 dB는 개별 corner보다 낮다.
- **[s2-node-rule]** 유입 it에 대한 KCL `it=vX/Req+sCeq vX`에서 노드 임피던스와 corner가 나온다. 1 kΩ×1 pF=1 ns, 역수는 10^9 rad/s다. 동일 node–ground의 R/C 병렬과 독립원 영점/종속원 유지가 맞다. 노드마다 서로 다른 pole가 무조건 생긴다는 보편 명제로 확대하지 않는다.
- **[s2-cg-poles]** lambda0/no-body, gate AC접지에서 `vgs=-vX`; drain→source 전류는 -gm vX이고 source 유입 전류는 +gm vX다. 따라서 source input block=1/gm. 입력0 뒤 RS와 같은 X–ground 두 노드이므로 병렬이다. 독립 input KCL `(1/RS+gm+sCin)vX=vin/RS`; output KCL `(1/RD+sCL)vout-gm vX=0`의 두 인자가 본문의 두 pole와 일치한다. RS는 앞단 출력저항이고 gate 구동의 외부축퇴 Re가 아니므로 gmRS≫1을 강제해 1을 없애지 않는다. input corner가 CS보다 높아도 전체 두 corner의 순서는 값 없이 정할 수 없다.
- **[s2-floating]** CF의 실제 양단은 gate X와 drain output으로 어느 쪽도 AC ground가 아니다. 임의 절반 배분이나 각 접지 RC인자 분리 불가의 문제 제기까지만 있다. 밀러 공식/배율·실제 소자 고주파 커패시턴스 모델/fT 계산이 본문으로 새어 나오지 않는다.

원 회로·알려진 블록을 우선한 점을 실제 그림과 식에서 확인했다. CS Gm 그림에는 오른쪽 출력의 실제 접지 단락선이 있고, Rout 그림에는 입력의 실제 접지 연결과 끝 Vt점·왼쪽 유입 전류가 있다. source는 접지, RD/CL은 같은 output–ACground 부하이며 input은 왼쪽/output은 오른쪽이다. 제어 전류원까지 펼친 그림이 없으므로 controlled-source/ro 쌍의 좌우 배치 규칙을 불필요한 그림 추가 사유로 적용하지 않았다. 같은 노드의 점/이름 데이터가 같은 색으로 묶였고 원문 연결과 첫 식이 대응한다. 실제 색·font face·최소 glyph 간격은 부모 브라우저 검토에 맡긴다.

## 작성자 적용 질문의 독립 답

| 토픽 | 실제 질문의 요지 | 독립 답과 이유 | 판정 |
|---|---|---|---|
| why-circuit | 리뷰어 생성: gm,CL 고정, RD만 두 배면? | 저주파 이득 크기 2배, omega3dB 절반. gmRD와 1/(RDCL)의 고정인자 조건이 같음. | pass |
| s0-speed-bandwidth | 동일 입력의 저주파10배·고주파5배 중 어느 변화를 덜 잘 따라가나? | 고주파. 같은 입력 크기에서 출력/입력 비가 더 작음. | pass |
| s0-rc-lowpass | C 고정, 주파수20배면 ZC의 크기는? | 1/20배. 1/(omega C)의 역비례이며 출력 전달비 전체와 구분. | pass |
| s0-cs-cl | 출력 임피던스 측정에서 gate/source를 접지했는데 gmvin가 여전히 구동전류인가? | 아니다. 선택 모델 vgs=0이라 제어 전류가0; RD와CL 부하가 남음. 별도 입력유지/출력단락 Gm 측정에서는 gm를 얻음. | pass |
| s0-3db | gm,CL 고정 RD3배면 저주파 이득/3dB는? | 이득 크기3배, 경계1/3배. CL만 바꾸면 저주파 이득은 불변. | pass |
| s1-transfer | CS의 주파수를 올릴 때 크기와 뒤집힘은? | 크기는 감소하고 음의 반전 인자는 유지. 정확 위상에는 pole의 추가 지연도 있어 모든 주파수에서 정확180° 반대라는 뜻은 아님. 본문이 그 차이를 명시함. | pass |
| s1-bode | 평평하게 시작/zero영향없음, 두pole후-40이면 세번째뒤? | -60 dB/dec. 기존기울기에 -20을 추가하며 순간이득20dB하락이 아님. | pass |
| s2-cs-two-poles | 다른값고정 Cin만4배면 input/outputcorner는? | input1/4배, output불변. RS Cin만4배이고 RDCL은 고정. | pass |
| s2-node-rule | 분리접지RC, C고정 R절반이면? | corner2배. RC가절반이라 역수2배. | pass |
| s2-cg-poles | lambda0/no-body/gateAC접지, RS=1/gm이면 같은RS,Cin CS와비교? | CG inputcorner2배. RS||1/gm=RS/2. outputcorner 순서는 아직모름. | pass |
| s2-floating | gate/drainCF의 어느단자가 접지C의 접지단자에 해당? | 어느쪽도 아님. 둘다 움직이는 신호node이며 임의반분불가. | pass |
| s3-cheatsheet | RS/Cin 입력CS의 inputpole는? | 1/(RS Cin). RS가앞단출력저항이고 Cin이접지연결인 수업 모델. | pass |
| s3-next | 부유C 계산식이 이번 요약표에 있나? | 없다. 이번에는 문제제기, 예고는 제목만. | pass |
| s3-links | 현재 선택한 문제수는? | 13개. manifest/selection ID순서와 링크문구 일치. | pass |

## 문제 선발의 독립 검토

후보 JSON의 관련 장 기출은 7개 전부이며 모두 미사용이다. 2019-1중간Q5의 (1)바이어스, (2)CM제거, (3)CMRR은 선행 범위지만 (4)가 CF의 양단 Miller 변환을 요구하므로 전체 보류가 맞다. 2023-1중간Q1도 (1)은 선행 범위지만 (2)가 Miller 입력임피던스/대역폭 감소라 전체 보류다. 2021-1기말Q1은 실제 M3가 Y에 연결된 전류원 캐스코드에서 CGD1의 X/Y분할 및 각 소자 커패시턴스가 필요하다. Q2는 CE와pnp부하의 Cpi/Cmu/CCS 및 Miller가 필요하다. 2023-1기말Q1은 원문이 Miller 사용을 명시하고 (a)와(b)의 모든 pole를 묻는다. 실제(a)M3는 source가 내부node인 NMOS, M4는다이오드이고, (b)는차동쌍이며 두회로모두 미학습소자C/변환이 필요하다. 2021-1기말Q7과2023-1기말Q6은 단락전류이득1의 fT정의부터 CGS=(2/3)WLCox를 사용한 유도 전체가 목표라 이번범위 밖이다. 단순 저항블록 선행지식이 있다는 이유로 이 7개를 부분 채택할 수 없다.

13개 교과서 선발은 이 공백을 채운다. 원문 전체 요구가 기초 주파수/접지RC·선행 저주파블록으로 해결된다. 순서상 E11.04→X11.04, E11.08→X11.08, E11.09→X11.09 전제가 함께 들어가고 앞선다. E11.03은 영상의 경계 흐림 정성, E11.04는CS 단일인자, X11.04는finite rO 병렬 대안, P11.01은10% 역산, P11.02는CE 전력/대역폭 최대이득, P11.03은네가지부하의저항블록, P11.06은pole/zero기울기, P11.09는두CS의곱/겹친pole, E/X11.08은두접지RC 및중복pole의실제대역폭, E/X11.09는CGsource병렬과10배pole분리 설계, P11.12는Cin앞node와MOSsource사이RP의직렬효과를 연습한다. P11.03의 네회로가 원문 한요구로 묶인 subpart_count1이라는 metadata는 허용된 묶음기준이며, 예상22분으로 실제4회로부담을 반영한다. 핵심73분/전체157분은 추정치로만 보존되어 있다. 참고풀이가 없다는 이유의 불이익 선발은 보이지 않는다.

선발 가능성을 확인하는 독립 결과: P11.01에서 0.9=1/sqrt(1+x²)이므로 x=sqrt19/9, `omega≈4.84×10^8 rad/s`, `f≈77.08MHz`. P11.02는 주어진 전력상한에서 IC≈P/VCC, 필요한 R1=1/(2pi f CL), |A0|=IC R1/VT로 역산할 수 있다(VT의수치관례는해설에서밝혀야함). P11.03은(a) emitter-side1/gm2[finitebeta라면rpi/(beta+1)], (b) (1/gm2+RB/beta2)의knownblock, (c)ro1||ro2, (d)(1/gm2)||ro2||ro1의부하와CL로해결된다. P11.06기울기는0→-20→0→-20이며, P11.09는positive DC분자와겹친2pole의-40기울기다. X11.08의 half-power경계는 omega=omega_p sqrt(sqrt2-1), X11.09는 RD=(RS||1/gm)Cin/(10CL). P11.12는 R_eq,in=RS||(RP+1/gm), 출력RDCL은유지된다. 이 확인은 선발범위 검토이며 자식 해설의 독립 정답·PDF 화면 승인 게이트를 대체하지 않는다.

사용자의 중복 override를 우선했다. `used-policy/1002/.assets/problems.txt`와 `used-policy/1007/.assets/problems.txt`의 실제 ID 집합과 선택13ID의 교집합은 공집합이다. 다른 회차 재사용은 명시적으로 허용되었으므로 중복 결함으로 재분류하지 않았다. 보류 기출은 이후 Miller/highfrequency/fT 회차에서 재검토할 공백으로 기록되어 있다. 다른 학습팩을 자동수정하지 않는다.

## 잔여 게이트

내용 미해결은 없다. s3 모바일 표의 긴 같은-양 H식을 줄바꾼 최종 조립본을 실제 다시 읽었고, 변경된 토픽 텍스트는 그 한 식뿐임을 이전 snapshot과 대조했다. 수정된 두줄 곱 H식은 원래 두분모 곱과 대수적으로 같다. 두 감사 JSON과 review-bindings를 최종 SHA-256 `3676cf101f3d5a66c4fde57a4f74c9604806f46c252c55155bc528162ce875af`에 갱신했다. 부모의 최종 브라우저/PDF 발행 판정은 별도다. 독립 audit를 자동승인이나 PDF완료로 해석하지 않는다.
