# ec2-review-pack 병렬 RUN 재설계

2026-11-26 대화에서 확정한 설계. 구현 계획은 `docs/superpowers/plans/2026-11-26-ec2-review-pack-unbounded-parallel.md`.

## 의도

병렬 RUN이 에이전트를 "4칸 배급" 대신 가장 작은 검증 대상 단위로 띄우게 한다. 완료 기준은 다음과 같다.

- 슬롯 인자 없이 준비된 작업이 모두 한 번에 배정된다.
- 문항별 작성자·풀이자가 동시에 진행된다.
- 맨 앞의 LLM 원문 준비 단계가 기계 작업이 된다.
- 작업자는 역할에 필요한 문서 절만 읽는다.
- 작성자는 조각 결함을 넘기기 전에 실행기 명령으로 잡는다.

분류: architectural. 접근은 A(기존 실행기를 유지하고 그래프 작업 단위만 쪼갬)를 택했다. 승인 장부가 이미 소문항 단위이기 때문이다.

## 완료 후 동작

- `next --run <RUN>`은 `--slots`를 생략하면 준비된 작업자를 모두 `dispatch`에 낸다. 값을 주면 지금처럼 그 수만큼만 낸다.
- 선발 뒤 `explain-author-pN`·`explain-blind-pN`이 문항마다 동시에 열린다. 같은 N의 작성자와 풀이자가 같은 에이전트면 채택이 거부된다.
- `source-prep`는 기계 작업이다. 모든 `강의노트/2026F_Lec*_*.pdf`를 `slides.txt`로 뽑고 날짜별 대조는 요약자가 한다.
- 작성자는 `task probe`로 한 섹션짜리 미리보기의 구조·화면 결함을 확인한다. 결함이 남은 작성자 receipt는 `task check`에서 거부된다.
- 작업자 명령은 브리프의 `python` 경로를 쓴다.
- 이미 시작한 RUN과 레거시 RUN은 저장된 계약대로 돈다.

## 범위 밖

Workflow 스크립트 배치, 레거시 workflow 변경, browser-qa와 감사의 동시 실행, 두 감사 합치기, CLI 중복 해시 정리, 레거시/병렬 문서 분리.

## 확정 결정

| # | 결정 | 값 |
|---|---|---|
| 1 | 기존 RUN 호환 | 새 계약 필드로 분기. 필드가 없는 RUN은 현재 동작 |
| 2 | 문항 작업 단위 | 문항(소문항 아님) |
| 3 | 역할 이름 | `explain-author`/`explain-blind` 유지, 작업 ID만 `-pN` |
| 4 | 독립성 | 같은 문항의 작성자 ≠ 풀이자, 조정자는 어떤 문항 작성자와도 다름 |
| 5 | `--slots` | 선택 인자, 생략 시 무제한 |
| 6 | 절 지정 | 새 브리프 필드 `reference_sections` |
| 7 | 파이썬 명령 | 브리프의 `python` = 실행기의 `sys.executable` |
| 8 | `source-prep` ID | 유지, 종류만 action |
| 9 | 레거시 | 변경 없음 |
| 10 | Workflow 스크립트 | 제외 |
| 11 | PROFILE 면제 역할 | `stt`, `selection`, `scope-final` |
| 12 | browser/pdf owner 기본값 | `workers` |
| 13 | PR 구성 | 네 개: (슬롯+읽을거리) → 원문 준비 → 문항 단위 → 조각 사전 검사 |

계획 단계에서 결정 1을 구체화했다. PR마다 독립된 계약 필드(`source_contract`, `problem_contract`, `probe_contract`)를 둔다. 하나의 `graph_contract: 2`로 묶으면 PR 사이에 시작한 RUN의 의미가 바뀐다.
