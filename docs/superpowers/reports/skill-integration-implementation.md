# Task 1 — 복습팩 문제설명 통합 구현

2026-10-15. 범위는 `2026-10-15-review-pack-problem-explanations.md`의 Task 1과 고정 설계다. Task 2/3의 실제 팩 감사·설명 저작은 수행하지 않았다.

## 변경

- `.claude/skills/ec2-review-pack/SKILL.md`: 설명 산출물과 발견 설명 추가, MD 뒤 9단계 전체 자식 호출, 10단계 병합 보고, lite에서도 자식 검토 유지, 첫 입력 변경 전 기존 설명 백업·정리 연결, 팩별 보류 처리.
- `.claude/skills/ec2-review-pack/references/problem-explain-integration.md`: 명시적 range·새 빈 자식 RUN·문항 순서 계약, 전체 저작/독립 검산/네 검토/publish, 보고 상태, 기존 팩 보충, SHA-256 검증 백업과 복원 순서.
- `.claude/skills/ec2-problem-explain/SKILL.md`: 부모/단독 호출 모드 구분, 부모 RUN 하위 새 실행 디렉터리, 부모 최종 보고 병합. 원래 CLI 옵션과 발행 게이트 유지.

원본 `.claude/skills/`만 수정했다. `.agents/skills/`는 이중 편집하지 않았다. 실제 복습노트·원본 문제·그림·목록·PDF는 수정하지 않았으며 새 실행기도 만들지 않았다. 커밋하지 않았다.

## 읽은 지침과 변경 전 확인

`skill-creator/SKILL.md`, `writing-skills/SKILL.md`의 점진적 상세 공개·조건별 계약·검증 원칙을 적용했다. 이 작업의 명시적 계획에 따라 새 문자열 검사 테스트나 하위 에이전트 압박 테스트는 만들지 않고, 기존 회귀 테스트와 임시 폴더 파일 작업으로 검증했다. 변경 전 부모는 9단계 보고로 종료되어 설명 호출이 없었고, 부모 백업 대상에 설명이 없었다. 문제 0개/slug 변경 후 옛 설명이 남는 계약상 누락을 확인한 뒤 수정했다.

## 회귀 테스트

두 suite는 `_util` 충돌을 피하도록 별도 Python 프로세스로 실행했다.

```powershell
python -m unittest discover -s .claude/skills/ec2-review-pack/tests -v
python -m unittest discover -s .claude/skills/ec2-problem-explain/tests -v
```

| Suite | 변경 전 | 변경 후 |
|---|---|---|
| ec2-review-pack | 132 tests, OK (1 skip) | 132 tests, OK (1 skip) |
| ec2-problem-explain | 93 tests, failures=2, errors=1 | 93 tests, failures=2, errors=1 (같은 기존 실패) |

변경 전후 자식 실패는 `test_long_formula_overflow_is_accessible_after_layout`(행 선택 결과 0), `test_vendor_files_and_hashes_present`(vendor 해시 불일치), `test_nfd_names`(Windows NFC/NFD 경로 FileNotFoundError)였다. 이번 문서 통합 범위에서는 기존 렌더러·템플릿·경로 구현을 변경하지 않았다.

## 임시 팩 수명주기 실험

명령: `python $env:TEMP/ec2-integration-scenarios.py`. `TemporaryDirectory` 안에서 기존 `make_repo` fixture로 실제 원본 문제 복사본을 만들고 실제 `epe_cli.py`를 subprocess로 호출했다. 성공 검토 값을 주입하거나 실제 팩을 발행하지 않았다. 수동 백업 계약과 같은 파일 작업을 수행했다: 정확한 NFC 접두사 대상 목록 → 팩 내부 절대 경로 확인 → 상대 경로 복사 → 모든 파일 SHA-256 대조 → 대상만 제거. 임시 폴더는 종료 시 정리했다.

| 시나리오 | 실제 관찰 |
|---|---|
| 문제 1개 → 0개 | 기존 HTML·MD·그림·자료 4파일을 검증 백업 후 제거. problems.txt 제거 후 자식 호출을 생략하는 상태 `skipped-no-problems` 확인. 다른 날짜 설명과 인터랙티브 sentinel 보존. |
| 같은 날짜 slug 변경 | 옛 4파일은 백업에만 존재. 기본 노트 slug를 New로 바꾼 뒤 실제 extract exit 0, 추출 pack.slug == New. 옛 이름은 발행 경로에 없음. |
| 같은 날짜 문항 순서 변경 | 기존 RUN 추출 후 problems.txt 두 줄 역순 변경. 기존 RUN check exit 1. 새 RUN extract exit 0, source hash 변경 및 첫 문항이 기출로 변경됨. |
| 통합/개별 팩 공존 | 0909-0911과 0909 동시 존재 시 명시적 통합 range extract exit 1, `여러 후보` 오류. 임의 선택 없음. |
| 자식 not_run/disputed | 실제 build 후 검토를 not_run/disputed로 유지해 각각 publish exit 1. 기본 팩 전체 파일 SHA-256 맵이 전후 동일. 뒤이어 1014 새 RUN extract exit 0. |

이 실험은 문서의 수명주기 계약과 기존 CLI 게이트를 검증한다. 새 설명의 실제 수학·내용·브라우저 검토를 수행했다는 뜻은 아니다.

## Diff 검토

`git diff --check` 통과. 계획 파일은 기존 미추적 파일이며 이 작업에서 수정하지 않았다. 제안 커밋 메시지는 `feat(skills): include problem explanations in review packs`이며 실제 커밋은 하지 않았다.
