# Exam Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 기출 전체를 보존하는 JSON과 수업 범위 선별 메타데이터를 기존 복습팩 흐름에 연결한다.

**Architecture:** MD를 원본으로 두고 목록/상세 JSON을 결정적으로 생성한다. 복습팩은 JSON으로 후보를 검토한 뒤 기존 ID 기반 PDF·해설 생성기를 사용한다. 전체 문항만 채택한다.

**Tech Stack:** Python 3.10+, unittest, 기존 PyYAML/workbook parser.

**Spec:** `docs/superpowers/specs/2026-10-21-exam-catalog-design.md`

## Global Constraints

- MD는 수정 원본이다. JSON은 자동 생성한다.
- PDF에는 문항 전체만 채택한다. 소문항 하나라도 범위 밖이면 제외한다.
- Python 3.10+, 기존 PyYAML과 표준 라이브러리만 사용한다.
- 복습팩 실행 중 저장소에 쓰지 않는다. RUN 아래 생성한다.
- 기존 TSV, manifest, problems.txt와 해설 검산 계약을 유지한다.
- 사용자 요청 범위에 따라 현재의 깨끗한 checkout에서 구현하고 커밋·푸시는 하지 않는다.

## Review Focus

- NFC/NFD 경로·ID: 실제 파일을 찾고 중복 ID를 거부한다(Task 1).
- 수정된 MD·exam.yaml·그림: 저장 JSON과 분류 해시의 오래됨을 검출한다(Task 1).
- 풀이 없는/미분류 문항: 보존하되 풀이 없는 후보는 제외한다(Task 1/2).
- 혼합 장/소문항·의존성: 전체 문항 내용을 제공하고 부분 채택을 허용하지 않는다(Task 2/3).
- 같은 range 재실행·다른 range 사용 이력: USED 계산을 보존한다(Task 2).

---

## File Structure

- `workbook/exam_catalog.py`: 원문 보존·해시·JSON 생성/검사 CLI.
- `workbook/tests/test_exam_catalog.py`: 임시 저장소의 보존·검증 회귀 테스트.
- `.claude/skills/ec2-review-pack/scripts/problem_index.py`: 기존 TSV와 JSON 후보/선택 기록 옵션.
- `.claude/skills/ec2-review-pack/tests/test_problem_index.py`: JSON·사용 이력·오류 회귀 테스트.
- `from_the_past/md/*/Q*.md`: 선택 메타데이터(원문 본문은 유지).
- `from_the_past/json/`: 생성 목록/상세와 사용법.
- 두 스킬 SKILL/references, `workbook/README.md`, `FORMAT-EXAM.md`: 사용 계약.
- `.claude/skills/ec2-problem-explain/tests/test_source.py`: 혼합 ID 입력 연결 확인.

### Task 1: 원문 보존 카탈로그

**Interfaces:** `content_hash(path: Path) -> str`; `build_catalog(repo: Path) -> tuple[dict, dict[str, dict]]`; `write_catalog(repo: Path, out: Path) -> dict`; `check_catalog(repo: Path, out: Path) -> list[str]`; `CatalogError(ValueError)`.

- [x] 보존/중복/경로/그림 누락/입력 변경/분류 변경 테스트를 작성한다. 핵심 assertion: 상세 `raw_md == path.read_text()`, `selection.status == 'stale'` after body change, `check_catalog(...) != []` after image change.
- [x] `python3 -m unittest discover -s workbook/tests -p test_exam_catalog.py`가 미구현 API 때문에 실패함을 확인한다.
- [x] `workbook/exam_catalog.py`에서 기존 parser를 재사용하고 index/detail, 입력 파일 해시, atomic JSON 교체, build/check CLI를 구현한다. index의 content hash는 selection을 제외한 metadata와 본문 기준으로 순환을 피한다.
- [x] 같은 테스트 PASS를 확인한다.

### Task 2: 복습팩 후보와 선택 기록

**Interfaces:** Task 1의 `build_catalog`, `write_catalog`를 소비한다. `candidate_data(repo: Path, used_dir=None, chapters=None, exclude_range=None) -> tuple[dict, list[str]]`; `record_selection(manifest: dict, candidates: dict) -> dict`를 제공한다.

- [x] JSON 후보에 미분류·전체 소문항·필요 개념·의존성이 남고 풀이 없는 문항은 빠지며, 사용 이력과 같은 range 제외가 동작하는 테스트를 추가한다. 선택 기록은 없는/USED ID·중복·누락 의존성을 거부한다.
- [x] `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_problem_index.py` RED를 확인한다.
- [x] TSV 기본 동작을 유지하고 `--format json --catalog-out RUN/exam-catalog`, `--selection-manifest ... --candidates-input RUN/candidates.json --selection-out RUN/selection.json`을 구현한다. 출력에는 schema/catalog hash를 넣는다.
- [x] 위 테스트 GREEN 및 기존 manifest 테스트를 확인한다.

### Task 3: 자료와 스킬 연결

**Interfaces:** index/detail schema, 기존 manifest `{id,kind,anchor,date,why}`, 기존 epe_source `load_source`를 사용한다.

- [x] 실제 기출/교과서 혼합 ID가 같은 순서로 해설 추출되는 테스트와 카탈로그 실제 입력 전수 검사 테스트를 추가하고 필요한 RED를 확인한다.
- [x] 기출을 읽어 근거가 있는 선별 메타데이터를 frontmatter에 추가한다. 검토를 과장하지 않고 미확인/미분류 상태를 명시한다. 본문은 변경하지 않는다.
- [x] catalog build로 `from_the_past/json`에 저장한다. 생성물은 손으로 편집하지 않는다.
- [x] 두 스킬 및 관련 reference에 후보 JSON 생성→전체 내용·그림 확인→manifest→selection.json→기존 PDF/설명 절차를 적는다. 정답의 독립 검산은 유지한다.
- [x] workbook, review-pack, problem-explain 테스트를 실행하고 catalog check·본문 불변·git diff --check를 확인한다.

## Execution record

- 계획 자가 검토: 승인 설계의 모든 요구를 Task 1–3에 배정했다. 구현은 직접 수행하고 마지막에 fresh-context 코드 리뷰를 받는다.
- 커밋 단계는 사용자 승인 범위에 맞춰 생략한다. 변경 파일을 그대로 검토 가능하게 남긴다.


## Review and validation record

- 독립 리뷰의 중요 지적 2건을 RED→GREEN으로 수정: 그림 있는 기출의 figures.yaml 필수화; 교과서 후보의 실제 그림/설정 해시 추가.
- 통합 점검에서 발견한 기존 `1)` 소문항 인식 오류도 재현 테스트 후 수정했다. 카탈로그 전체 기출과 해설 추출기의 소문항 표지가 일치하는 전수 테스트를 추가했다.
- 61문항 모두 selection 초안 및 JSON을 생성했다. 본문은 git HEAD와 바이트 대조해 모두 그대로임을 확인했다. 분류는 draft이며 원문 대조·정답 검산 승인을 주장하지 않는다.
- 후보 검토 후 원본/사용 이력이 바뀌면 이전 candidates.json을 선택 기록에서 거부하도록 보강했다.
- 임시 디렉터리에서 실제 혼합 ID 선택 기록→workbook 문제/답안 JSON·HTML 생성 스모크를 통과했다. 새 복습팩이나 해설 발행은 요청 범위에 없으므로 실행하지 않았다.
- `pytest`는 저장소 의존성 변경 없이 `/tmp/ec2-catalog-test-deps`에 준비했다.
- 기존 문제설명 실패 2건은 변경 전 HEAD(ba859fc) 파일을 임시 폴더에 추출해 동일하게 재현했다. `test_summary_preserves_math_when_navigating_after_render`는 이전 제목 복제 동작을 기대하며, `test_canonically_equal_sibling_directory_is_not_inside_repo`는 macOS에서 NFC/NFD 형제 디렉터리 두 개를 만들 수 없어 실패한다. 이번 기능과 무관한 화면 계약/플랫폼 테스트는 수정하지 않았다.

- 최종 검증: workbook unittest 113개 통과; review-pack pytest 142개 통과(175 subtests); problem-explain pytest 122개 통과(92 subtests), 위의 기존 실패 2개; 기출 도구 unittest 98개 통과. catalog check 및 git diff --check 통과.
