# 연쇄 블록 곱·테브난 변환·부하 기준 접지 연결 풀이 반영

기록일: 2026-11-26 (Asia/Seoul).
근거 보관용이며 규칙 원본은 [개인 풀이 명세](../../../.claude/skills/ec2-review-pack/references/solution-style.md)다.

## 입력·시작 상태

- 입력 1(시각 자료): 사용자 수업 필기 PDF `2026F_Lec6_Ch12_Feedback_rev3_261125_143026_(1).pdf` 5쪽(Lec6 s57–60, 예제 III C-V 귀환 및 예제 IV C-C 귀환 비이상 입·출력 로딩 효과).
  - p1(s57, Ex. III): $M_2$ 소스 노드를 $V_{out}$으로 두고 $\frac{I_{out}}{V_{in}}=\frac{V_X}{V_{in}}\cdot\frac{V_{out}}{V_X}\cdot\frac{1}{R_L}=(g_{m1}R_D)\cdot\frac{R_L}{1/g_{m2}+R_L}\cdot\frac{1}{R_L}$로 $R_L$ 약분; 로딩 효과는 `$R_L$ 자리에 $(R_L+R_M)$` 치환으로 처리.
  - p2(Ex. III $R_{out,open}$ 손그림): `접지 — 1/g_m2 — [Laser] — R_M — 접지` 세로 배치에 왼쪽 `Connect` 곡선으로 두 교류 접지를 이어 "Laser 입장에서는 $1/g_{m2}$와 $R_M$이 직렬로 보임"으로 판정.
  - p3(s58, Ex. III 폐루프): 개루프 대비 폐루프 이득 $\frac{1}{1+K(I/V)}$배, $R_{in,closed}$·$R_{out,closed}$ 모두 $(1+K(I/V))$배 표기.
  - p4(s59, Ex. IV): 입력 $I_{in}\parallel(R_F+R_M)$을 노턴→테브난 변환해 $(R_F+R_M)\cdot(V_X/V_{in})\cdot(I_{out}/V_X)$로 CG 이득 적용; 둘째 단은 $M_2$ 드레인에서 $I^*=I_{out}+I'$ 전류 분배로 전개(단, 필기 메모에서 PMOS $M_2$의 음수 부호 `-`가 생략됨).
  - p5(s60, Ex. IV $K$): 슬라이드 60의 $I_1, I_2$ 대신 원래 회로의 $I_{out}$(위로 들어감)·$I_F$(오른쪽으로 빠짐) 기호로 직접 $I_F=-\frac{R_M}{R_F+R_M}I_{out}$, $K=\frac{I_F}{I_{out}}=-\frac{R_M}{R_F+R_M}$ 도출.
- 입력 2(사용자 명시적 선호 및 `/grill-yourself` 확정):
  - 사용자 발언: “나는 전류 전압에 대한 연립방정식을 푸는 걸 좋아하지 않고, 내가 편한 풀이대로 풀어. 이 내용을 정리노트 html에 반영하자. ‘내가 필기한 부분’으로 명시하지 말고, 자연스럽게. 설명하는 방식을 바꾸자는 말이야.”
  - 확정 범위: `#1=C`(1125 정리노트 HTML + `.assets` 동기화 + `solution-style.md` 기존 13규칙 확장 + 본 갱신 기록 작성), `#5=A`(`#s2-cc-gain` 제목·도식·링크·치트시트 전면 동기화, `id="s2-cc-gain"` 유지).
- 변경 전 명세 SHA-256: `87746aa5d127893bd5f5ce10a8804d44f3e05bd687c93664e050289b2ff3945a`.
  명세·기록 폴더에 미커밋 변경은 없었다.

## 비교표

| 후보 ID | 파일·쪽수/영역 | 관찰 | 기존 규칙 ID | 분류 | 해석·범위 | 제안·근거 |
|---|---|---|---|---|---|---|
| B1 | 1125 필기 p1(s57) | $V_X, V_{out}$ 중간 노드로 $\frac{V_X}{V_{in}}\cdot\frac{V_{out}}{V_X}\cdot\frac{1}{R_L}$ 연쇄 곱 후 $R_L$ 약분, 로딩은 $R_L\to(R_L+R_M)$ 치환 | GAIN-01, DEGEN-01 | 확장·경계 명확화 | 다단 트랜스컨덕턴스·전류 이득에서 연립방정식($I_{out}=g_{m2}(V_X-I_{out}R_L)$)보다 블록 연쇄 곱·로딩 치환을 우선 | 우선순위 6·GAIN-01 확장, DEGEN-01 예외에 우선 경계 명시 |
| B2 | 1125 필기 p2 | `접지 — 1/g_m2 — [Laser] — R_M — 접지`의 위·아래 접지를 `Connect`로 연결해 직렬 판정 | CIRCUIT-01, CIRCUIT-02 | 확장 | 두 노드 사이 부하 포트의 $R_{out,open}$은 시험원 노드 방정식 대신 위·아래 접지 연결로 직렬 합 판정(Ex. III·IV 공통) | CIRCUIT-01 생성 규칙 1·CIRCUIT-02 시험원 생략 조건 추가 |
| B3 | 1125 필기 p3(s58) | 폐루프 이득 $\frac{1}{1+KA_0}$배, $R_{in}, R_{out}$ $(1+KA_0)$배 병렬 정리 | GAIN-01 | 보강 | 귀환 폐루프 단계에서 개루프 대비 배율 관점을 일관되게 제시 | GAIN-01 다단·귀환 절에 배율 정리 반영 |
| B4 | 1125 필기 p4(s59) | $I_{in}\parallel(R_F+R_M)$을 테브난 $V_{in}=I_{in}(R_F+R_M)$+직렬 $(R_F+R_M)$로 변환해 CG 단 이득 적용, 둘째 단은 $I^*=I_{out}+I'$ 전류 분배 | CIRCUIT-01, CIRCUIT-02, GAIN-01 | 확장 | 전류 입력이 익숙한 전압 입력 단을 구동할 때 노턴→테브난 변환으로 기본 단 블록을 재사용 | 우선순위 6·CIRCUIT-01 생성 규칙 2·CIRCUIT-02·GAIN-01 반영 |
| B5 | 1125 필기 p4(s59) | PMOS $M_2$ 드레인 전류 $I^*=g_{m2}V_X$로 적어 `-` 부호 생략 | CORRECT-01 | 정확성 보완 | 음수 부호를 생략하면 $A_{I,open}\gt0$이 되어 $K\lt0$인 음의 귀환($KA_{I,open}\gt0$)과 모순 | 선호로 채택하지 않고 $I^*=-g_{m2}V_X$ 보정 기준을 CORRECT-01 10번에 기록 |
| B6 | 1125 필기 p5(s60) | $K$ 유도에서 $I_1, I_2, I_{R_F}$ 대신 원 회로 기호 $I_{out}$(위로 들어감)·$I_F$(오른쪽) 직접 사용 | NOTATION-01 | 확장 | 불필요한 임시 포트 변수를 줄이되, 원문 그림 화살표와 다를 때는 방향 정의를 병기 | NOTATION-01 생성 규칙에 귀환 계수 직접 기호 규칙 추가 |

미응답·보류 후보는 없다.

## 내부 검산 (SymPy)

- Ex. III 이상적 개루프 연쇄 곱 vs 연립방정식:
  $$(g_{m1}R_D)\cdot\frac{R_L}{1/g_{m2}+R_L}\cdot\frac{1}{R_L}-\frac{g_{m1}R_D}{1/g_{m2}+R_L}=0.$$
- Ex. III 로딩 치환($R_L\to R_L+R_M$) vs 연립방정식:
  $$(g_{m1}R_D)\cdot\frac{R_L+R_M}{1/g_{m2}+R_L+R_M}\cdot\frac{1}{R_L+R_M}-\frac{g_{m1}R_D}{1/g_{m2}+R_L+R_M}=0.$$
- Ex. IV 첫 단 노턴→테브난 변환 + CG 이득 vs 입력 노드 전류 분배:
  $$(R_F+R_M)\cdot\frac{R_D}{1/g_{m1}+R_F+R_M}-\frac{R_F+R_M}{R_F+R_M+1/g_{m1}}\cdot R_D=0.$$
- Ex. IV 둘째 단 부호 검산: PMOS $M_2$의 $V_{SG2}=V_{DD}-V_X$에서 소신호 $\Delta v_{sg2}=-v_X$, 아래 방향 드레인 전류 $I^*=-g_{m2}V_X$, 따라서 $\frac{I_{out}}{V_X}=\frac{-g_{m2}r_{O2}}{r_{O2}+R_L+R_M\parallel R_F}\lt0$, $A_{I,open}\approx-46.07\lt0$, $K=-1/11\lt0\Rightarrow KA_{I,open}\approx4.19\gt0$(음의 귀환 일치).

## 반영 내용

- `.claude/skills/ec2-review-pack/references/solution-style.md`의 버전 기준일, `간결한 풀이의 우선순위`, `CIRCUIT-01`, `CIRCUIT-02`, `GAIN-01`, `DEGEN-01`, `NOTATION-01`, `CORRECT-01`, `변경 이력`을 갱신했다.
- 기존 13규칙 ID(`UNIT-01`~`FREQ-01`)를 그대로 유지했고 신규 규칙 ID를 추가하지 않았다.
- 과거 산출물(`확인문제_1125_Analog_Filters.html`, `문제설명_1125_Analog_Filters.html`, 복습문제 PDF, 이전 검토 해시·기록)은 수정하지 않았다.

## 검증

- 변경 후 명세 SHA-256: `824109c2d41910f5e6a3433c128b01ba05e936bc1e37946199791cad496109e0`.
- `workbook.learning_style.read_style(Path('.'))`: 13규칙 ID(`UNIT-01`, `CALC-01`, `CALC-02`, `CIRCUIT-01`, `CIRCUIT-02`, `GAIN-01`, `DEGEN-01`, `SCALE-01`, `BIAS-01`, `NOTATION-01`, `EXPLAIN-01`, `CORRECT-01`, `FREQ-01`) 확인.
- `pytest workbook/tests/test_learning_style.py -q`: 29 passed.
- 상대 링크(`../../../../docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md`) 실존 확인 및 `git diff --check` 통과.
명세 바이트 변경으로 이전 개인화 검토는 새 발행에 재사용할 수 없다.
