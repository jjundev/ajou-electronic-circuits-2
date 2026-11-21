# 노트 리뷰 판정 충돌: 표시 불일치를 작성자 수정에서 떼어 내기 — 설계

날짜: 2026-11-21 · 상태: 확정 (사용자 확인 2026-11-21)

## Intent
1120 실행에서 개인화 감사(`style-audit`)와 내용 리뷰(`content-review`)가 같은 토픽·규칙의 적용 표시(`applied` / `not_applicable`)를 다르게 적었다. 실행기는 이 23건을 Important 결함으로 만들어 작성자 7명에게 보냈다. 그 결과 LLM 시도 12회와 토큰 약 37M이 들었고, s5에는 절차를 통과시키려고 '차원 확인' 문단이 들어갔다.

이 설계는 두 가지를 바꾼다.

1. **판정 충돌을 리뷰어 쪽 문제로 되돌린다.** 표시가 달라도 작성자 수정이나 발행 차단이 생기지 않게 한다.
2. **축을 나눈다.** 적용 표시는 개인화 감사가 확정하고, 내용 리뷰는 결함 주장으로만 막는다. 그리고 두 리뷰어가 같은 표시 정의와 노트 토픽 적용 기준을 읽게 한다.

분류: bounded. 바꾸는 범위는 `join_reviews`, 리뷰어 지시문, 새 참조 문서 하나, 테스트다.

## 왜 안전한가 (핵심 근거)
`pack_findings.join_reviews`는 두 리뷰가 **모두 `done`일 때만** 실행된다(`any(t['status'] != 'done' …) → return`). 따라서 join이 만드는 충돌은 정의상 **두 리뷰어가 모두 "결함 없음"이라고 한 칸**이다. 실제 결함은 이미 각 리뷰의 `unresolved` 목록을 거쳐 작성자에게 간다(1120의 correct-note-1 5건이 그 경로였다). join 충돌은 결함 경로가 아니라 표시 경로이므로, 작성자에게 보낼 근거가 없다.

1120의 23건을 원문으로 확인한 결과는 다음과 같다.
- 23건 모두 양쪽 evidence에 결함 주장이 없다.
- CALC-02 5건은 **같은 사실**("결과가 정수라 반올림 불필요")에 한쪽은 `applied`, 다른 쪽은 `not_applicable`을 붙였다. 규칙 해석이 아니라 **표시의 뜻** 차이다.
  - `applied` = "규칙을 확인했고 지켰다"
  - `not_applicable` = "규칙이 손댈 것이 없었다"
- CORRECT-01 8건은 규칙의 대상 정의가 다르다. 감사는 "조건·≈ 보존"까지 CORRECT-01로 봤고, 내용 리뷰는 "STT·슬라이드 오기 교정"으로 봤다. 그런데 `solution-style.md`의 CORRECT-01 대상은 손풀이 오기 패턴이다.

원래 의도도 같다. `references/review-prompt.md` 3행은 이미 "개인화 감사는 전담 감사자가 수행하며, 내용 리뷰어가 실제 근거를 재검토·보완한다. 실제 감사 결과는 전담 감사자가 기록한다"라고 적고 있다. 2026-11-19 계획(Task 5)도 "Conflicting judgments remain open until reconciled with the source"였다. 대조는 리뷰어 몫이었는데, 구현이 `owner_of(target)`으로 작성자에게 보냈다.

## 완료 후 동작
- 두 노트 리뷰가 `done`이면 표시가 달라도 join이 합친 감사를 바로 발행하고, precheck가 진행된다.
- 표시가 다른 칸은 합친 감사에 `disposition`(감사 쪽 값), 양쪽 evidence, `disagreement: true`로 남는다. RUN 상태 `applicability_disagreements`에도 쌓인다.
- `report.json`에 불일치 개수와 목록이 나온다. 실행이 끝난 뒤 이것을 보고 적용 기준표를 보강한다.
- `review-join` 결함과 그에 따른 작성자 수정 요청은 새 RUN에서 생기지 않는다.
- 내용 리뷰가 규칙 위반을 본다면 표시를 바꾸는 대신 `unresolved` 결함(rule ID 포함)으로 올린다. 이 경로는 지금처럼 막는다.

## 이번에 하지 않는 것
- 내용 리뷰의 13규칙 표를 없애는 일. 표를 없애면 리뷰어 토큰이 줄지만 receipt·brief·`audit_output` 계약이 바뀐다. 2단계 후보로 남긴다.
- `solution-style.md` 수정. 이 파일은 사용자가 확정한 명세이고 snapshot 해시에 들어간다. 적용 기준은 리뷰어 참조 문서에 둔다.
- 이미 진행 중인 RUN의 동작 변경. 계약 버전이 1인 RUN은 기존 동작을 유지한다.

## 구현 사양

### 1. `scripts/pack_findings.py` — `join_reviews`
- 새 상수 `LABEL_ONLY_JOIN = 2`를 둔다. `state.get('join_contract', 1) >= 2`일 때만 새 동작을 쓴다. `init_run`이 새 parallel RUN에 `join_contract = 2`를 기록한다. 기존 `approval_contract`, `concept_contract`와 같은 방식이다.
- 새 동작:
  - 규칙 칸마다 `decision['disposition'] != second['disposition']`이면 결함을 만들지 않는다.
  - 대신 `decision['disagreement'] = True`를 붙이고, 합친 칸의 `disposition`은 **style-audit 값**으로 둔다.
  - evidence는 지금처럼 두 리뷰어 근거를 합친다.
  - `state['applicability_disagreements']`에 `dict(candidate_digest, target, rule, style=…, content=…)`를 추가한다. 같은 후보를 다시 join하면 그 후보의 항목을 교체한다.
- 계약 2에서는 `adjudicate(state, CONFLICT, …)`를 부르지 않는다. 계약은 RUN을 만들 때만 정해지므로 계약 2 RUN에는 `review-join` 결함이 생길 수 없다. 그래도 하나라도 남아 있으면 `FlowError('label-only join cannot carry review-join findings')`로 멈춘다(불변식 검사).
- `validate_style_audit`(`workbook/learning_style.py`)는 `disposition`과 `evidence`만 검사하므로 추가 키 `disagreement`를 허용한다. 따라서 바꾸지 않는다.

### 2. `scripts/pack_findings.py` — `apply_request`
- 노트 리뷰 결함을 모두 묶어 보내라는 조건에서 `CONFLICT`는 계약 2에서 생기지 않는다. 코드는 그대로 둬도 된다. 정리할 때 `(*NOTE_REVIEWS, CONFLICT)`를 `NOTE_REVIEWS`로 좁히는 것은 선택 사항이다.

### 3. 보고
- 최종 `report.json`을 만드는 곳(`pack_publication.py` 쪽)에 `applicability_disagreements`의 개수와 규칙별 집계를 넣는다.
- 집계 예: 1120 기준 `CORRECT-01: 8, CALC-02: 5, SCALE-01: 3, …`, 전체 208칸 중 23칸(11%).

### 4. `references/review-prompt.md` — 병렬 RUN 절
"같은 토픽·규칙의 적용 여부가 엇갈리면 두 보고의 원문 근거를 다시 대조한다"를 다음으로 바꾼다.

> 적용 표시는 개인화 감사가 확정한다. 내용 리뷰의 표시가 다르면 실행기가 기록만 남기고 발행을 막지 않는다. 규칙 위반이라고 판단하면 표시를 바꾸지 말고 해당 rule ID로 `unresolved` 결함을 올린다. 표시의 뜻과 노트 토픽 기준은 [note-rule-applicability.md](note-rule-applicability.md)를 따른다.

### 5. 새 문서 `references/note-rule-applicability.md`
두 노트 리뷰어 brief에 같이 넣는다(`pack_flow.py`의 references 표 737–738행에 두 역할 모두 추가). 내용은 다음과 같다.

**표시의 뜻(공통)**
- `applied`: 토픽 안에 규칙이 다루는 **대상**이 있고, 그 대상이 규칙을 따른다. "고칠 것이 없었다"도 대상이 있으면 `applied`이다.
- `not_applicable`: 규칙이 다루는 대상이 토픽에 **없다**. 이유로 그 부재를 적는다.
- 대상이 있는데 규칙을 어겼다면 표시가 아니라 결함이다.

**노트 토픽에서의 대상** (1120의 불일치에서 뽑은 초안 — 사용자 확인 필요)

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

### 6. 테스트 (`tests/test_pack_findings.py`)
- 계약 2: 두 리뷰가 `done`이고 한 칸 표시가 다르면 → `review-join` 결함 0개, `active_audit` 발행, 그 칸에 `disagreement: true`, `applicability_disagreements` 1건, precheck가 ready.
- 계약 2: 같은 후보를 두 번 join하면 `applicability_disagreements`가 중복되지 않는다.
- 계약 2: 상태에 `review-join` 결함이 남아 있으면 join이 `FlowError`로 멈춘다.
- 계약 2: 한 리뷰가 `needs-fix`이면 join이 돌지 않고, 불일치도 기록되지 않는다.
- 계약 1: 기존 동작(불일치 → Important 결함) 유지.
- `validate_style_audit`가 `disagreement` 키가 있는 감사를 통과시킨다.

## 1120 재연 추정
| 항목 | 실제 | 새 설계 |
|---|---|---|
| 00:27 join 결과 | 23건 결함 → 작성자 7명 | 감사 발행, 불일치 23건 기록 |
| review-join-1·2에 쓴 LLM 시도 | 12회 | 0회 |
| 그 구간 토큰(재개 구간 합) | 약 37M (작성자 25.4M + 리뷰 11.5M) | 0 |
| precheck 시작 | 00:43 | 약 00:27 |
| s5 '차원 확인' 문단 | 절차 때문에 추가 | 추가 안 됨 |

뒤의 화면·SVG·PDF 사슬은 그대로라서 svg-fix-1과 browser-fix-1 비용은 남는다. 다만 16분 일찍 진행되므로 00:57 사용 한도 전에 더 멀리 갔을 가능성이 있다(추정).

## 위험과 대응
- **감사자가 대충 `not_applicable`을 붙이는 경우**: 결함이 있으면 내용 리뷰가 rule ID로 결함을 올려 막는다. 규칙별 불일치율을 report에 남기므로, 특정 규칙의 불일치가 반복되면 기준표를 보강한다.
- **내용 리뷰어가 위반을 보고도 표시만 바꾸는 경우**: 지시문 4번에서 "위반은 결함으로"를 명시한다. 1120에서는 23건 모두 evidence에 위반 주장이 없어 이 경우가 없었다.
- **기준표가 사용자 명세를 잘못 해석하는 경우**: 기준표는 리뷰어 참조 문서이고 `solution-style.md`를 바꾸지 않는다. 초안 표는 사용자가 확인한 뒤 적용한다.
