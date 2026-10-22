# 독립 검산과 workbook 참고 풀이의 대조 (메인 컨트롤러)

각 검산자는 blind/question.md와 실제 회로 그림만 먼저 읽고 답을 확정했다. 작성자와 검산자는 다른 에이전트다. evidence의 pN-blind-verdict는 그 최초 확정 상태이고, 이 문서는 이후 컨트롤러가 source.json reference_steps/reference_answer와 비교한 기록이다. 설명 조각과의 최종 비교·개인화 감사는 마지막 build 뒤 내용 리뷰어가 수행한다.

- p1: 직접 CM half KCL에서 -gm RD/(1+2gm ro3), gm=ISS/Vov 대입 후 (10.224) residual0. md의 합친 두트랜지스터 회로와 동치. 단일종단CM, 차동CM0.
- p2: 정확 CM KCL에서 근사 Gm≈1/(2ro5), Rout≈ro3, ACM_SE≈-ro3/(2ro5). md와 일치. 정확 Rout 식은 evidence에만. 그림의 두출력차와 ACM_SE 정의 구별.
- p3: 입력/부하 ro20kΩ, gm1=10mS, tail gm5=20mS/ro5,6=10kΩ. Ad=-100, RSS≈2MΩ, ACM≈-5×10^-3. 유한ro 정확값 -0.0049256은 내부 대조이며 gmro≫1 근사에서 참고답과 일치.
- p4: 테일 시험원KCL 정확모델을 evidence에서 풀어 주항 [(1+gm3(R1∥rpi3))ro3]와 비교. 입력쌍 큰β·VA∞, 가산항무시조건에서 ΔRC/(1/gm1+2RSS)로 md와 일치. 필요한 근사조건을 본문에 명시해야 함.
- p5: DM/CM KCL의 일반 이득은 (RC+ΔRC/2)를 포함. 작은 미스매치·큰 입력β와 테일 근사에서 md CMRR=(gmRC/ΔRC)(1/gm+2RSS)와 일치. gm3와 입력gm1, beta조건을 구별.
- p6: 정확 부하 평균 RD+ΔRD/2를 유지한 CMRR. 작은 미스매치 극한에 md 식으로 수렴. 소문항 표지 main 안에 실제(a),(b) 모두 설명. 이 차이는 근사차이이며 조건 없이 잘못된 등호를 쓰지 않음.
- p7: 원문 VDD/입력CM 미지정으로 정확 CLM DC 답은 불확정. 참고답의 입력ro 무시 수업 모델에서 O, ADM=-10, ACM=-9.90099e-2, ACM-DM=+9.90099e-4, CMRR10100(80.0864dB), 폭2배 CMRR7171.0678(77.1117dB). md의 반올림 수치와 일치. 유한입력ro 모델과 차이는 evidence에만 비교; 본문 전 구역에 추가근사 명시.
- p8: 실제 I1 아래 화살표와 PMOS 회로 KCL에서 +RL/N. md와 일치.
- p9: mirror비+출력KCL로 (a)0→2ΔIRL, (b)-I0RL/2→(3ΔI-I0)RL/2. md와 일치. 이상전류원과 M4 포화/현실 compliance 조건.
- p10: VT26mV 가정에서 pnpVA=65/12V≈5.42V, 원래 이득100 역대입. md와 일치. 오른쪽 단일출력/vid=vin1-vin2 이득은+이며 원문 목표크기100과 모순없음.

실제 회로 연결·수치 불일치 disputed 없음. 위 모델 차이는 증거의 기호·수치 대조를 충족하는 근사 차이이며, 새 설명이 조건을 공개하는지는 최종 내용 검토에서 판단한다.
