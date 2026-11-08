# 설계과제2: 전류 주입 캐스코드 증폭기 주파수 응답 — 설계

날짜: 2026-11-08 · 상태: 사용자 확정 (#12·#13 추천값)

## Intent
`설계과제/과제2/2026-2_전자회로2_설계과제2_v1.pdf`의 캐스코드 증폭기를 설계하고 검증한다. 회로는 M1 CS(NMOS), M2 CG 캐스코드(NMOS), Y 노드로 전류를 넣는 PMOS 전류원 M3으로 되어 있다. 조건은 VDD = 1 V, RS = 500 Ω, P ≤ 0.5 mW, ID2 = |ID3|, |A0| = 10, 모든 극점 ≥ 1 GHz이다. 과제1과 같은 흐름(`handcalc → params.inc → ngspice → post.py → 보고서 md`)으로 Design Problem (a)–(d)와 Spice Problem (a)–(e)를 푼다. 완료 조건은 보고서 md가 검사기 error 0과 감점 체크를 통과하고, 모든 수치가 `sim/` 산출물에서 나오는 것이다.
분류: bounded. 과제1 흐름을 그대로 쓰고 회로와 해석 종류(AC, pz)만 바뀐다.

## 완료 후 동작
- `cd 설계과제/과제2/sim && python3 handcalc.py && ngspice -b cascode.cir && python3 polemap.py && python3 post.py`를 실행하면 손계산·시뮬레이션·그림·표가 모두 다시 만들어진다.
- 보고서에 들어가는 것:
  - 정확한 Gm 유도, 전력식, 노드 전압 표, W/L 표, saturation 부등식
  - Miller 극점 3개, H(s), Bode 크기 그림
  - 회로도(.op 라벨, 학번·이름), SPICE saturation 표, 크기·위상 Bode
  - 이득·극점·노드 C 비교표(오차 %)
- 극점이 1.5 GHz 미만이거나 포화 여유가 0.1 V 미만이거나 P > 0.5 mW이면 `handcalc.py`가 AssertionError로 멈춘다.

## 이번에 하지 않는 것
- 노션 업로드와 표지 병합(`ec2-sync-notion`, `ec2-merge-report`): 사용자가 그림을 넣은 뒤 따로 한다 (#13).
- 감점체크리스트.md를 과제2에 맞게 일반화하기: 스킬 수정은 범위 밖이다.
- 부하 커패시터 CL: 문제에 없다.

## 구현 사양
폴더 `설계과제/과제2/` (과제1 구조를 따른다)
- `설계과제2.md`: `ajou-bb`로 가져온 BB 공지(마감·첨부)와 문제 원문 전사.
- `figures/fig1_cascode.png`: PDF 1쪽 회로도를 잘라 낸 것. 같은 파일을 `report/figs/01_cascode.png`로 복사한다.
- `sim/MOSFET_model.lib`: 과제1 파일을 수정 없이 복사한다(CMOSN/CMOSP).
- `sim/handcalc.py`:
  - 입력: I1 = 400 µA, Vov1 = Vov2 = 0.15 V, |Vov3| = 0.30 V, VY = 0.30 V
  - λ를 포함한 정확식에서 |A0| = 10.00이 되도록 RL을 반복으로 구한다
  - W는 (1+λVDS) 보정 후 0.01 µm로 반올림한다
  - 과제 표의 C 파라미터로 Miller 극점을 구한다
  - 출력: `params.inc`, `design.json`
- `sim/core.inc`: Vin(DC VIN, AC 1) → RS 500 → M1·M2·M3, RL, Vb1, Vb2. 모든 MOSFET에 AD = AS = XJ·W, PD = PS = W, XJ = 0.49 µm (#12).
- `sim/cascode.cir`: op + `show m`(id vgs vds vdsat gm gds cgs cgd cbd cbs) → `op.txt`, `ac dec 100 1meg 100g` → `ac.txt`, `meas`(A0, f−3dB) → `meas.txt`, `pz in 0 out 0 vol pz` → `pz.txt`.
- `sim/polemap.py`: X·Y·out 노드에 1 fF를 하나씩 더해 pz를 다시 돌리고, 상대 이동이 가장 큰 극점을 그 노드에 대응시킨다 → `polemap.json`.
- `sim/post.py`:
  - 그림: `figs/02_bode_design.png`(H(s) 크기), `figs/04_ac_bode.png`(SPICE 크기·위상)
  - 표: `report/sat_table.md`, `report/compare.md`(이득·극점·C_node = 1/(2π f_p R_node), R_node는 SPICE gm·gds로 구함)
- `sim/ltspice/make_asc.py` → `cascode.asc`(UTF-16LE). 캡처(`figs/03_schematic.png`)는 사용자가 한다.
- `report/설계과제2_보고서.md`: `.claude/skills/ec2-write-design-report/references/양식.md` 순서를 따른다. 그림 번호는 01 회로, 02 설계 Bode, 03 회로도, 04 SPICE Bode.

### 핵심 식
- I1 = ID2 + |ID3| = 2·ID2, P = VDD·I1
- R_in2 = (RL + ro2)/(1 + gm2·ro2), R_Y = ro1 ∥ ro3 ∥ R_in2
- Gm = gm1·(ro1∥ro3)/((ro1∥ro3) + R_in2), Rcas = ro2 + (ro1∥ro3) + gm2·ro2·(ro1∥ro3), Rout = RL ∥ Rcas, A0 = −Gm·Rout
- 강의 근사(1104 노트: A_XY ≈ −gm1/gm2, R_Y ≈ 1/gm2)도 함께 적는다
- 출력 강하 ID2·RL ≈ |A0|·Vov1/4이므로 이득은 Vov1로 정해진다. f_X는 W1에 반비례하고 W1은 I1에 비례한다
- A_XY = −gm1·R_Y
- C_X = CGS1 + (1 − A_XY)·CGD1, R_X = RS
- C_Y = CDB1 + (1 − 1/A_XY)·CGD1 + CGS2 + CSB2 + CDB3 + CGD3
- C_out = CDB2 + CGD2, R_out = Rout
- f_k = 1/(2π R_k C_k), H(s) = A0 / ∏(1 + s/ω_k). RHP 영점 gm1/CGD1(약 45 GHz)은 언급만 한다
- 과제 표 값: Cox = 12 fF/µm², CGS = (2/3)WLCox + 0.3W, CGD = 0.3W, CDB = CSB = 0.4W (fF, W는 µm)

### 타당성 검증 (스크래치패드, 2026-11-08)
- 손계산: RL = 1930 Ω, Vout = 0.614 V, W1/W2/W3 = 62.1/31.0/14.0 µm, A_XY = −2.00, C_X/C_Y/C_out = 164/129/22 fF, Miller 극점 X/Y/out = 1.94/3.28/3.80 GHz
- 바이어스: Vin,DC = 0.55, Vb1 = 0.85, Vb2 = 0.30 V. 포화 여유 M1/M2/M3 = 0.15/0.164/0.40 V
- ngspice(접합 C 포함): A0 = 20.31 dB(10.36), pz 극점 1.55/3.79/7.43 GHz, f−3dB = 1.32 GHz, ID1 = 414.1 µA, ID2 = 207.4 µA, |ID3| = 206.7 µA
- 모델 KP = UO·Cox = 103.6 µA/V²로 주어진 값보다 3.6 % 크다. 이것이 전류·이득 오차의 원인이다
- ngspice Level 1의 `show m`은 cgs·cgd·cbd·cbs를 보고하고, vdsat은 0으로 나올 수 있다

## 결정
| # | 결정 | 답 | 근거 |
|---|---|---|---|
| 1 | 회로 해석 | M2 = NMOS CG, M3 = PMOS 전류원(→Y), I1 = 2·ID2 | 과제 PDF 그림 |
| 2 | 전류 | I1 = 400 µA (P = 0.4 mW) | 전력 여유 20 %. I1을 줄이면 f_X가 오른다 |
| 3 | Vov·노드 | Vov1 = Vov2 = 0.15, \|Vov3\| = 0.30, VY = 0.30 | 헤드룸 3.5·Vov1 + Vov2 ≤ 1, 포화 여유가 고르다 |
| 4 | 이득식 | 정확식으로 \|A0\| = 10.00, 강의 근사 병기 | 감점체크리스트 #1, 1104 노트 §2 |
| 5 | W | (1+λVDS) 보정, 0.01 µm 반올림 | 과제1 handcalc.py:56 |
| 6 | 극점 | Miller, Y에 CDB3·CGD3 포함, CL 없음 | 1104 노트 |
| 7 | SPICE 도구 | 수치는 ngspice, 회로도만 LTspice | 과제1 메모. LTspice에는 pz 해석이 없다 |
| 8 | 극점 추출 | pz + 1 fF 섭동으로 노드 대응 | AC 곡선으로는 비지배 극점을 분리할 수 없다 |
| 9 | SPICE 바이어스 | 손계산 전압 그대로. \|ID2 − \|ID3\|\|/\|ID3\| > 1 %일 때만 Vin을 조정 | KP 차이 3.6 %는 보고서에서 원인으로 설명한다 |
| 10 | 모델 차이 | Cox 8.63 vs 12, CGDO/CGSO 0.4 vs 0.3 fF/µm | MOSFET_model.lib |
| 11 | 설계 여유 | Miller 극점 ≥ 1.5 GHz assert | 결합 시 최저 극점이 약 20 % 낮아진다 |
| 12 | 접합 C | AD = AS = 0.49 µm·W, PD = PS = W | 사용자 확정 (추천값) |
| 13 | 범위 | 보고서 md(검사기 통과) + LTspice .asc까지. 캡처는 사용자, 노션·병합은 따로 | 사용자 확정 (추천값) |
