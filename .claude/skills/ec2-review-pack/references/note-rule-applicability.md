# 노트 토픽의 규칙 적용 표시

사용자 확인 (2026-11-21).

## 표시의 뜻
- `applied`: 토픽 안에 규칙이 다루는 **대상**이 있고, 그 대상이 규칙을 따른다. "고칠 것이 없었다"도 대상이 있으면 `applied`이다.
- `not_applicable`: 규칙이 다루는 대상이 토픽에 **없다**. 이유로 그 부재를 적는다.
- 대상이 있는데 규칙을 어겼다면 표시가 아니라 결함이다.

## 노트 토픽에서의 대상

| 규칙 | 노트 토픽에서의 대상 | 1120 사례와 이 기준의 판정 |
|---|---|---|
| CALC-02 | 수치를 대입한 결과(예시·확인 질문 포함) | s0 "5, 8 kΩ 정수라 반올림 불필요" → 대상 있음 → `applied` |
| CALC-01 | 중간값을 조립하거나 제약에서 역산하는 계산 | s1-k-rules 관계식을 행으로 나눈 것만으로는 대상 아님 → `not_applicable` |
| CORRECT-01 | `solution-style.md` CORRECT-01에 적힌 손풀이 오기 패턴(단위 생략, $V_{DD}$ 누락, 근사 생략 등)을 토픽이 직접 다룰 때 | STT·슬라이드 오기 교정은 content-rules 소관이므로 대상 아님. "≈와 조건 유지"는 해당 규칙(예: CALC·CIRCUIT)에서 판정 |
| SCALE-01 | 고정 인자 대비 배율·비 비교, 변화량 $\Delta X$ | why-circuit "A_0 20% 변화 → 폐루프 1.5%" → 배율 비교 → `applied` |
| CIRCUIT-01 | 저항 합성(병렬·연쇄)이나 알려진 블록 치환이 본문에 있을 때 | s3-vc-closed의 $(1/g_{m1})\parallel R_F$ → 대상 있음 → `applied` |
| CIRCUIT-02 | 회로 그림, 측정 조건이 있는 회로 | 단계 흐름도만 있으면 `not_applicable` |
| UNIT-01 | 단위가 있는 수치 계산·환산 | 기호식 치트시트의 차원 라벨만이면 `not_applicable` |
| NOTATION-01 | 풀이·회로·식 표기 | 예고 제목 목록이면 `not_applicable` |

나머지 규칙(GAIN-01, DEGEN-01, BIAS-01, EXPLAIN-01, FREQ-01)은 1120에서 불일치가 없었다. 처음 불일치가 생기면 그 실행의 `applicability_disagreements`를 보고 행을 추가한다.
