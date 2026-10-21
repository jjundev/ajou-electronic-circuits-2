# EC2 Learning Style Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사용자의 손풀이에 근거한 공통 명세를 두 EC2 스킬에 적용하고, 검토된 핵심 풀이를 HTML·MD·답안 PDF에서 일관되게 제공한다.

**Architecture:** 저장소 공통 MD와 불변 해시 스냅샷을 두 스킬의 생성·검토 입력으로 사용한다. 문제설명은 기존 일곱 구역 앞에 핵심 풀이를 추가하고, 같은 핵심 영역에서 답안 데이터를 추출하여 workbook의 선택적 입력으로 전달한다. 부모 복습팩이 검토된 답안 PDF를 마지막에 교체하며, 자식의 독립 검산 및 발행 경계를 유지한다.

**Tech Stack:** Python 3.10+, 표준 라이브러리, 기존 HTML parser/MD converter, pytest/unittest, 기존 Playwright·Chrome·KaTeX·PyMuPDF. 새 런타임 의존성 없음.

**Spec:** [2026-10-21-ec2-learning-style-design.md](../specs/2026-10-21-ec2-learning-style-design.md). 실행자는 이 계획과 설계를 모두 읽는다. #7·#8은 사용자가 추천안을 명시적으로 확정했다.

## Global Constraints

- Python 3.10 이상. 새 런타임 패키지를 추가하지 않는다.
- HTML: 내 사고 순서의 핵심 풀이를 먼저 보여주고, 필요한 개념·유도를 이어서 자세히 설명.
- 답안 PDF: 핵심 회로·판단·계산·최종 답을 담고, 상세 설명은 HTML에서 제공.
- 원문 조건·회로·문항 ID·소문항·정답의 정확성이 개인 표기 취향보다 우선한다.
- 빈칸·계산 생략을 이해 부족으로 해석하지 않는다. 미관찰 분야를 확인된 성향으로 일반화하지 않는다.
- 생성 PDF는 기존 video-16x9 규격과 1920×1080 기준 하단 180px 자막 여백을 유지한다.
- 원본 문제 MD·원본 PDF·문제 그림·손풀이 PDF는 변경하지 않는다.
- 개인화 필수 입력 누락이나 검토 실패 시 기존 풀이로 조용히 대체하지 않는다.
- 개인 명세의 바이트가 변경되면 이전 개인화 검토를 재사용하지 않는다.
- 과거 발행물은 계속 열 수 있지만, 구버전 검토 기록으로 새 개인화 발행을 승인하지 않는다.
- 실제 수학 검산·원문 대조·내용 검토·화면 검토를 수행하지 않고 pass를 기록하지 않는다.
- 구현 검증은 임시 RUN/fixture에서 수행한다. 기존 복습팩 전체 재생성·커밋·푸시는 이 계획 작성의 범위가 아니다.

## Review Focus

1. 개인 명세가 생성 도중 또는 발행 뒤 변경됨: 내용상 비슷해도 이전 검토·overlay 재사용 금지. Task 1/3/4의 변경·누락 테스트가 담당한다.
2. pN과 workbook ID를 혼동하거나 소문항 하나가 빠짐: 그럴듯한 다른 정답을 붙이지 않고 전체 매핑 검증 실패. Task 2/4가 담당한다.
3. 오래된 팩의 rerender와 참조 이동: 과거 HTML 열람은 유지하지만 개인화 검토가 없으면 새 승인을 상속하지 않음. Task 3이 담당한다.
4. NFC/NFD·공백 경로와 SVG/PNG 상대 경로: 현재 stage와 최종 PDF 모두 그림을 읽으며 외부/탈출 경로는 실패. Task 4가 담당한다.
5. PDF 넘침·렌더 실패·교체 실패와 문제 0개 팩: 기존 자료를 손상시키지 않으며 미완료/skip을 구분. Task 5/6/7이 담당한다.

---

## 실행 범위와 파일 구조

하나의 연속된 기능으로 진행한다. 명세 → 해설 → 검토 → PDF 전달은 서로 의존하므로 별도 독립 프로젝트로 나누지 않는다. 계획 작성 시점에는 다음 두 문서만 저장했으며 코드·스킬·실제 학습 자료를 변경하지 않았다.

실행 시작 시 `using-git-worktrees`를 적용하고 현재 사용자 변경을 확인한다. 이 문서들의 미커밋 상태도 사용자 작업으로 보존해 실행 checkout에 전달한다. 여기의 commit 단계는 실행을 선택한 뒤의 작은 단위 로컬 커밋이며 push 지시가 아니다. 모든 git add는 명시 파일 목록을 사용한다.

| 파일/단위 | 책임 |
|---|---|
| `docs/learning/solution-style.md` (신규) | 손풀이 관찰·근거·생성 규칙의 단일 원본 |
| `workbook/learning_style.py` (신규) | 명세 읽기·해시 스냅샷·규칙 ID·적용 감사 형식 검증 |
| `epe_core.py` (신규, 이하 epe 파일은 `.claude/skills/ec2-problem-explain/scripts/`) | 핵심 풀이 마크업 검증과 답안 overlay 생성 |
| `epe_types.py`, `epe_source.py`, `epe_shared.py` | workbook ID와 개인 명세 입력 연결 |
| `epe_contract.py`, `epe_cli.py`, `epe_render.py`, `epe_publish.py`, `epe_review_policy.py`, `epe_rerender.py` | 명세·핵심 풀이·감사·overlay를 기존 발행 경계에 포함 |
| `workbook/answer_overlay.py` (신규) | 발행된 답안 데이터의 출처·선택·해시 검증과 workbook 데이터 적용 |
| `workbook/build_workbook.py`, `workbook/templates/answer.html` | 선택적 개인화 답안과 답안 단독 빌드·SVG 표현 |
| `.claude/skills/ec2-review-pack/scripts/publish_answer.py` (신규) | 검토된 임시 답안 PDF의 백업·원자적 교체 |
| review-pack `manifest.py`, `assemble.py`, `check_html.py` | 부모 명세 스냅샷·감사 및 예비/최종 링크 검사 |
| 두 스킬의 `SKILL.md`와 아래 Task 6의 references | 실제 작성자·리뷰어·부모/자식 실행 순서 |
| 각 영역의 기존 tests + 아래 신규 tests | 행위 검증, 합성 fixture와 실제 화면 검증의 분리 |

`.agents/skills/`는 링크이므로 `.claude/skills/`의 실제 파일만 수정한다. 관련 없는 공유 UI·다른 과목 스킬을 동기화하지 않는다. 모듈 이름 `assemble`과 테스트 helper `_util` 충돌을 피하려고 세 테스트 디렉터리는 별도 Python 프로세스로 실행한다.

## 고정 데이터 계약

### A. 개인 명세와 적용 감사 (Task 1 소유)

`StyleSnapshot`은 `TypedDict`로 `{path: str, sha256: str, rule_ids: list[str]}`. path는 항상 저장소 상대 `docs/learning/solution-style.md`, sha256은 원본 바이트, rule_ids는 `### RULE-01` 형식 제목에서 문서 순서대로 추출한다. 기존 `SourcePack.profile='review'`와 별개의 `learning_style` 필드를 사용한다.

초기 ID: `UNIT-01, CALC-01, CALC-02, CIRCUIT-01, CIRCUIT-02, GAIN-01, DEGEN-01, SCALE-01, BIAS-01, NOTATION-01, EXPLAIN-01, CORRECT-01`.

`StyleAudit`는 `{learning_style: StyleSnapshot, items: dict[str, ItemAudit]}`. ItemAudit는 `{status: 'pass'|'not_run'|'fail', reviewer: str, rules: dict[str, RuleAudit]}`. RuleAudit는 `{disposition: 'applied'|'not_applicable', evidence: str}`. 각 item에 현재 rule_ids 모두가 있어야 하며 evidence는 적용 위치/내용 또는 비적용 이유다. 에이전트가 실제 의미 검토 후 기록하고 프로그램은 형식·집합·해시만 검사한다.

EPE의 item 키는 모든 `pN:subpart`, 부모의 item 키는 manifest의 모든 topic ID. 모든 규칙을 억지로 적용하지 않고 not_applicable 사유를 허용한다.

### B. 핵심 풀이 (Task 2 소유)

새 조각은 기존 일곱 구역보다 앞에 다음 직계 영역 한 개를 둔다. 기존 `data-subpart`는 solve/verify 전용으로 보존한다.

```html
<div class="layer formal solution-route" data-personalization="route">
  <h4>핵심 풀이</h4>
  <div data-core-subpart="main">
    <div data-solution-core="step" data-core-label="회로 판단"><p>판단과 식</p></div>
    <div data-solution-core="answer"><p>단위와 조건을 포함한 최종 답</p></div>
  </div>
</div>
<!-- 기존 understand → recall → start → solve → verify → pitfall → retry → sum -->
```

원문 subparts 순서와 같은 그룹을 정확히 한 번씩 둔다. 그룹마다 비어 있지 않은 step 1개 이상, 마지막에 answer 1개. 중첩/중복 core 표지 금지. step의 label은 비어 있지 않은 일반 텍스트이며 exporter가 escape한다. 회로가 핵심이면 step 안에 기존 SVG 규칙의 figure를 포함한다. 정성 문항도 논증 step과 결론 answer를 사용한다. 모든 조건·근사·부호·최종 답은 뒤 상세 설명과 일치해야 한다.

### C. 답안 overlay (Task 2/3 생성, Task 4 소비)

위치: 발행 자료 폴더 `.assets/자료_문제설명_<range>_<slug>/answer-overlay.json`. schema_version=1. 필드:

```text
schema_version: 1
review_policy_version: 'problem-explain-2026-10-21-learning-style'
range, slug: str
learning_style: StyleSnapshot
input_hash: str                 # EPE payload_hash
source_inputs: dict[str,str]    # repo-relative 입력/그림 경로 → sha256
problems: list[{
  id: str,                     # 실제 workbook ID, 예 E9.05
  explanation_id: str,         # p1
  subparts: list[str],
  steps: list[{subpart: str, label: str, html: str}],
  answers: list[{subpart: str, html: str}]
}]
assets: dict[str,str]           # stage HTML 폴더 상대 그림 경로 → sha256
```

별도 AI 요약 없이 최종 stage DOM의 route를 추출한다. 원시 fragment의 상대 경로가 아니라 resources()가 변환한 경로를 사용한다. overlay를 manifest.files와 review.artifact_hashes에 포함한다. build 시 overlay는 아직 미승인이고, publish가 만드는 같은 폴더의 `validation.json`에 기존 네 검토와 개인화 감사가 실제 pass여야 소비할 수 있다. 별도 서명/권한 시스템은 만들지 않는다. 현재 overlay/manifest의 schema_version 또는 version을 모르면 추정해서 소비하지 않는다.

### Task 1: 근거를 갖춘 개인 명세와 스냅샷

**Files:**
- Create: `docs/learning/solution-style.md`, `workbook/learning_style.py`, `workbook/tests/test_learning_style.py`

**Interfaces:**
- Consumes: 동반 설계의 12개 규칙·근거·확정 선택.
- Produces: `StyleSnapshot`, `StyleAudit`, `LearningStyleError(ValueError)`.
- Produces: `read_style(repo: Path) -> StyleSnapshot`, `check_style(repo: Path, expected: StyleSnapshot) -> None`, `validate_style_audit(audit: dict, snapshot: StyleSnapshot, item_ids: list[str]) -> list[str]`.
- CLI: `python3 workbook/learning_style.py snapshot --repo REPO --out RUN/learning-style.json`; `check --repo REPO --snapshot FILE --audit FILE --items ITEM...`. check는 현재 해시와 전체 감사 일치 때만 exit 0/`style PASS`.

- [ ] **Step 1: 실패 테스트 작성.** 테스트 helper `write_profile(tmp_path, ids)`는 ASCII 경로의 MD에 지정 제목을 쓰고 tmp_path를 repo로 반환한다. 파일명만 바꾼 가짜 분석이 아니라 해시/누락 동작을 검사한다.

```python
def test_snapshot_detects_any_byte_change(tmp_path):
    repo = write_profile(tmp_path, ['UNIT-01', 'EXPLAIN-01'])
    snapshot = read_style(repo)
    assert snapshot['rule_ids'] == ['UNIT-01', 'EXPLAIN-01']
    assert snapshot['path'] == 'docs/learning/solution-style.md'
    (repo / snapshot['path']).write_bytes((repo / snapshot['path']).read_bytes() + b'\n')
    with pytest.raises(LearningStyleError, match='명세 변경'):
        check_style(repo, snapshot)

def test_audit_rejects_missing_rule_or_item(valid_audit, snapshot):
    assert validate_style_audit(valid_audit, snapshot, ['p1:main']) == []
    del valid_audit['items']['p1:main']['rules']['UNIT-01']
    assert validate_style_audit(valid_audit, snapshot, ['p1:main'])
```

`valid_audit/snapshot` fixture는 위 두 ID, p1:main, 비어 있지 않은 reviewer/evidence, pass/applied를 사용한다. 추가: `test_missing_profile_fails`, `test_duplicate_rule_id_fails`, `test_empty_reason_fails`, `test_not_applicable_with_reason_passes`, `test_extra_item_fails`.

- [ ] **Step 2:** `python3 -m pytest workbook/tests/test_learning_style.py -q` 실행. Expected: 새 모듈/함수 부재로 FAIL.
- [ ] **Step 3:** 설계의 근거 표·12규칙·예외·6개 적용 예시·미확인 범위·변경 이력을 MD로 작성하고 세 함수를 구현한다. 단위 예시의 BJT 328.947 kΩ 및 MOS W/L=15.625를 독립 산술로 확인한다. 기존 학습 자료에 쓰지 않는다.
- [ ] **Step 4:** 같은 테스트 실행. Expected: PASS. 작성한 MD를 설계의 관찰 항목과 수동 대조한다. 문장에 특정 문자열이 있다는 것을 분석 정확성 검사로 대체하지 않는다.
- [ ] **Step 5:** `git diff --check`와 staged scope 확인 후 위 세 파일만 커밋한다. 메시지: `feat(ec2): define evidence-based learning style`.

### Task 2: 핵심 풀이 마크업과 안정적인 문항 매핑

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_core.py`, `.claude/skills/ec2-problem-explain/tests/test_core.py`
- Modify: scripts `epe_types.py`(Problem/SourcePack), `epe_source.py`(load_source), `epe_shared.py`, `epe_contract.py`(validate_fragment)
- Modify: `.claude/skills/ec2-problem-explain/tests/_util.py` 및 `Problem`/`SourcePack`를 직접 구성하는 기존 테스트의 fixture

**Interfaces:**
- Consumes: Task 1 `read_style`/`StyleSnapshot`, 기존 Node/parse/inner/outer. epe_shared가 workbook 경로 초기화 후 learning_style의 공개 이름을 재노출하고 epe_types/epe_review_policy는 그 어댑터에서 가져온다. 모듈 로딩 순서에 따라 workbook import가 실패하지 않게 한다.
- Produces: `Problem.workbook_id: str`, `SourcePack.learning_style: StyleSnapshot`. 기본 빈 값으로 필수 검사를 우회하지 않는다.
- Produces: `validate_core(problem: Problem, markup: str) -> list[str]`, `extract_core(problem: Problem, markup: str) -> dict`. 반환은 계약 C problems의 원소다. 추출 실패는 ExplainError.
- Produces: `make_overlay(pack: SourcePack, stage_html: Path, repo: Path) -> dict`. 계약 C 전체 반환. source_inputs/asset 해시는 실제 파일에서 계산한다.

- [ ] **Step 1: 실패 테스트 작성.** `core_fragment(problem)` fixture는 계약 B와 기존 일곱 구역을 합쳐 원문 subparts 순서대로 만든다. 실제 workbook_id는 E9.05, explanation_id는 p1인 사례를 반드시 둔다.

```python
def test_core_maps_stable_id_and_keeps_equations(problem, core_markup):
    result = extract_core(problem, core_markup)
    assert result['id'] == 'E9.05'
    assert result['explanation_id'] == 'p1'
    assert result['answers'] == [{'subpart': 'main', 'html': '<p>$W/L=15.625$</p>'}]

@pytest.mark.parametrize('mutation', ['missing_b', 'duplicate_a', 'wrong_order', 'empty_answer', 'nested_core', 'route_after_recall'])
def test_invalid_core_is_rejected(two_part_problem, mutation):
    assert validate_core(two_part_problem, mutated_core(two_part_problem, mutation))
```

추가: `test_original_seven_sections_still_required`, `test_core_does_not_count_as_solve_subparts`, `test_scalar_and_qualitative_answers`, `test_overlay_uses_stage_image_paths`. helper `mutated_core`는 이름대로 단 하나의 위반을 만든다.

- [ ] **Step 2:** `python3 -m pytest .claude/skills/ec2-problem-explain/tests/test_core.py -q`. Expected: 새 인터페이스 부재로 FAIL.
- [ ] **Step 3:** load_source에서 표시용 source 문자열을 파싱하지 않고 원래 `p.id`를 workbook_id로 저장한다. 명세 파일을 source inputs 및 snapshot에 포함한다. 핵심 영역은 상세 구역과 독립적으로 검사하며 기존 일곱 구역·sum 검사도 실행한다. exporter는 문장/수식 내용을 고치지 않는다.
- [ ] **Step 4:** 핵심 테스트 및 `test_source.py`, `test_contract.py` 실행. Expected: PASS. 기존 fixture는 유효한 개인 명세와 route를 갖도록 갱신하고 테스트를 삭제/skip해서 맞추지 않는다.
- [ ] **Step 5:** 변경한 위 파일과 fixture 파일을 명시적으로 stage, diff 확인 후 커밋. 메시지: `feat(ec2): add shared core solution markup`.

### Task 3: 개인화 검토와 overlay를 발행 경계에 묶기

**Files:**
- Modify: EPE scripts `epe_cli.py`, `epe_render.py`, `epe_contract.py`, `epe_publish.py`, `epe_review_policy.py`, `epe_rerender.py`
- Modify: `workbook/learning_style.py` (공유 policy 상수), EPE `epe_shared.py`
- Create: `.claude/skills/ec2-problem-explain/tests/test_learning_style_flow.py`
- Modify: EPE tests `_util.py`, `test_cli.py`, `test_render.py`, `test_publish.py`, `test_sync.py`의 승인 fixture

**Interfaces:**
- Consumes: Task 1/2.
- Produces: 공유 `PERSONALIZED_REVIEW_POLICY = 'problem-explain-2026-10-21-learning-style'`; 기존 EPE POLICY_VERSION은 이를 사용한다.
- Produces: review.json의 `learning_style_audit: StyleAudit`, manifest의 `learning_style: StyleSnapshot`, `answer_overlay: str`(stage root 상대 경로).
- Existing functions `build`, `publish_explanation`, `rerender`의 CLI는 유지한다. overlay는 build 때 만들고 publish의 소유 범위인 자료 폴더로 함께 발행한다.

- [ ] **Step 1: 실패 테스트 작성.** 기존 make_repo/fragment/approved를 확장하고 'unit test fixture' 판정을 실제 검토와 혼동하지 않게 유지한다.

```python
def test_personalization_not_run_blocks_publish(bundle):
    bundle.review['learning_style_audit']['items']['p1:main']['status'] = 'not_run'
    with pytest.raises(ExplainError, match='개인화'):
        bundle.publish()

def test_profile_change_after_build_blocks_publish(bundle):
    bundle.profile.write_bytes(bundle.profile.read_bytes() + b'\n')
    with pytest.raises(ExplainError):
        bundle.publish()

def test_overlay_is_bound_to_artifact_hashes(bundle):
    relative = bundle.overlay.relative_to(bundle.artifacts.html.parent).as_posix()
    assert relative in bundle.review['artifact_hashes']
    bundle.overlay.write_text('{}', encoding='utf-8')
    with pytest.raises(ExplainError):
        bundle.publish()
```

`bundle` fixture는 일시 repo의 E9.05 한 문항에 extract/build를 실제 호출하고 합성 승인 기록을 준비하며 publish wrapper를 제공한다. 추가: `test_profile_missing_before_extract`, `test_old_policy_rerender_does_not_inherit`, `test_current_profile_change_never_uses_html_equivalence`, `test_missing_style_reference_rejected`, `test_final_core_and_details_are_both_in_md`.

- [ ] **Step 2:** 새 flow 테스트 실행. Expected: 기존 경로가 개인화 실패를 거부하지 못해 FAIL.
- [ ] **Step 3:** build_explanation의 stage DOM 생성 후 make_overlay를 호출하고 파일 해시 확정 전에 저장한다. initial_reviews는 개인화 감사도 not_run으로 초기화하고 명세 reference만 자동 기입한다. publish는 현재 snapshot·필수 reference·감사 전체·overlay 해시를 검사한다. make_overlay를 export하는 별도 승인 우회 CLI는 만들지 않는다.
- [ ] **Step 4:** rerender에서 새 snapshot과 저장 snapshot이 다르면 재사용을 금지한다. 옛 fragment에 route가 없으면 '새 저작 필요'로 종료하고 기존 발행물을 유지한다. 구버전 policy나 명세 변경에서 approval을 새 hash로 옮겨 쓰지 않는다.
- [ ] **Step 5:** `python3 -m pytest .claude/skills/ec2-problem-explain/tests -q`. Expected: PASS 또는 환경 의존 browser skip의 구체적 사유. 스킵은 화면 검토 완료가 아니다.
- [ ] **Step 6:** 해당 파일만 stage/diff 확인 후 커밋. 메시지: `feat(ec2): gate personalized explanations and answer data`.

### Task 4: 검토된 overlay를 사용하는 답안 PDF 빌드

**Files:**
- Create: `workbook/answer_overlay.py`, `workbook/tests/test_answer_overlay.py`, `workbook/tests/overlay_fixture.py`
- Modify: `workbook/build_workbook.py:25`(인자), `:56`(build_one), `workbook/templates/answer.html`(핵심 그림 스타일)
- Modify: `workbook/tests/test_build.py`, `workbook/tests/test_video_layout.py`, `workbook/README.md`

**Interfaces:**
- Consumes: 계약 C, Task 1 snapshot/policy.
- Produces: `AnswerOverlayError(ValueError)`, `load_answer_overlay(path: Path, repo: Path, expected_ids: list[str]) -> dict`, `apply_answer_overlay(data: dict, overlay: dict, *, html_dir: Path) -> dict`.
- CLI adds `--mode both|problems|answers` (default both), `--answer-overlay PATH` (optional). overlay는 `--ids` 및 answers/both에서만 허용한다. repo는 기존 `paths.REPO`를 사용한다. legacy 호출은 기존 동작 그대로다.

- [ ] **Step 1: 실패 테스트 작성.** `overlay_fixture.py`는 schema C와 EPE가 발행하는 manifest/validation의 최소한 유효한 합성 bundle을 만든다. 그림과 명세·원문 해시는 실제 fixture 바이트로 계산한다.

```python
def test_applies_only_answer_fields(overlay_bundle, answer_data):
    overlay = load_answer_overlay(overlay_bundle.path, overlay_bundle.repo, ['E9.05'])
    out = apply_answer_overlay(answer_data, overlay, html_dir=overlay_bundle.build_dir)
    assert out['problems'][0]['html'] == answer_data['problems'][0]['html']
    assert out['problems'][0]['solution']['answer'] == '<p>$W/L=15.625$</p>'
    assert answer_data['problems'][0]['solution'] != out['problems'][0]['solution']

@pytest.mark.parametrize('mutation', ['missing_id', 'duplicate_id', 'reordered_ids', 'missing_subpart', 'modified_profile', 'modified_source', 'modified_asset', 'missing_validation', 'not_run_review'])
def test_invalid_overlay_fails_without_fallback(overlay_bundle, mutation):
    overlay_bundle.mutate(mutation)
    with pytest.raises(AnswerOverlayError):
        load_answer_overlay(overlay_bundle.path, overlay_bundle.repo, overlay_bundle.ids)
```

추가: `test_answers_mode_leaves_problem_pdf_untouched`, `test_legacy_without_overlay_preserves_json`, `test_profile_missing_fails_personalized_only`, `test_nfd_and_spaces_resolve_images`, `test_external_or_escaping_asset_rejected`, `test_invalid_overlay_writes_no_outputs`.

- [ ] **Step 2:** `python3 -m pytest workbook/tests/test_answer_overlay.py -q`. Expected: 새 모듈/CLI 부재로 FAIL.
- [ ] **Step 3:** load_answer_overlay는 sibling manifest.json/validation.json을 확인한다. 현재 policy, 네 검토와 전체 소문항 판정 및 개인화 감사 pass, manifest/input_hash 일치, validation.artifact_hashes의 실제 파일 전부, profile 및 source_inputs, references와 assets의 해시, 정확한 ID 순서·소문항 집합을 검증한다. validation.json은 기존 방식대로 자기 자신을 해시하지 않는다. 반환 dict에는 디스크 스키마 외의 내부 값 `_asset_data: dict[str,str]`를 추가해 검증된 asset 상대경로를 해당 바이트의 data URI에 대응시킨다. 이 내부 값은 파일로 다시 저장하지 않는다. manifest의 data 폴더 구조로 stage root를 정하며 입력 path가 그 root 밖으로 나가면 거부한다.
- [ ] **Step 4:** apply_answer_overlay는 입력 복사본의 solution만 변경한다. subpart가 main이면 표지 없음, 그 외 '(a)' 등을 기존 순서대로 붙여 기존 steps/answer 스키마로 합친다. 그림은 load_answer_overlay가 제공한 `_asset_data`의 data URI로 바꿔 PDF 빌드 폴더 이동에 독립적으로 만든다. 링크는 텍스트만 유지한다. SVG는 기존 클래스에 대응하는 답안 템플릿 스타일을 추가하고 fill/선/화살표가 보이도록 한다. AI 재작성은 없다.
- [ ] **Step 5:** 빌드 전에 overlay 전체를 검증하고 `--mode answers`는 문제지 JSON/HTML/PDF를 생성·교체하지 않는다. legacy/default both는 유지한다. 검증 오류는 exit 1, 사용법 오류는 argparse exit 2.
- [ ] **Step 6:** `python3 -m pytest workbook/tests -q`. Expected: PASS. Playwright가 필요한 기존 테스트의 미실행은 별도 보고한다.
- [ ] **Step 7:** 해당 파일만 stage/diff 확인 후 커밋. 메시지: `feat(workbook): render reviewed personalized answers`.

### Task 5: 임시 답안 PDF의 검토와 안전한 교체

**Files:**
- Create: `.claude/skills/ec2-review-pack/scripts/publish_answer.py`, `.claude/skills/ec2-review-pack/tests/test_publish_answer.py`

**Interfaces:**
- Consumes: Task 4 load_answer_overlay, 최종 RUN PDF, 실제 화면 검토 JSON.
- Produces: `publish_answer(repo: Path, overlay_path: Path, pdf_path: Path, review_path: Path, destination: Path, backup_dir: Path) -> Path` (백업 PDF 경로 반환; 기존 파일이 없으면 backup_dir의 receipt.json 경로).
- CLI: `publish_answer.py --repo REPO --overlay PATH --pdf PATH --review PATH --destination PATH --backup-dir PATH`.
- review JSON: `{schema_version:1, pdf_sha256, overlay_sha256, learning_style_sha256, status:'pass', reviewer, evidence:[{path,sha256}], overflow:[]}`. evidence는 실제 렌더 페이지 PNG 및 검토 보고서 경로. 경로 기준은 review JSON 폴더다.

- [ ] **Step 1: 실패 테스트 작성.** fixture의 기존 답안은 `b'old-pdf'`; 검토 JSON은 합성 테스트 전용으로 표기한다.

```python
@pytest.mark.parametrize('failure', ['pdf_changed', 'overlay_changed', 'overflow', 'not_run', 'missing_evidence', 'outside_destination', 'replace_error'])
def test_failed_publish_preserves_existing_pdf(publish_fixture, failure):
    publish_fixture.inject(failure)
    with pytest.raises((ValueError, OSError)):
        publish_fixture.publish()
    assert publish_fixture.destination.read_bytes() == b'old-pdf'

def test_success_keeps_verified_backup(publish_fixture):
    backup = publish_fixture.publish()
    assert backup.read_bytes() == b'old-pdf'
    assert publish_fixture.destination.read_bytes() == publish_fixture.new_pdf.read_bytes()
```

추가: `test_missing_old_pdf_installs_and_records_receipt`, `test_publication_rechecks_source_after_review`. source 변경은 Task 4 검증을 재호출해 차단한다.
- [ ] **Step 2:** `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_publish_answer.py -q`. Expected: 모듈 부재로 FAIL.
- [ ] **Step 3:** destination은 overlay.range/slug로 계산한 해당 팩의 `복습문제_<range>_<slug>-답안.pdf`와 정확히 일치해야 한다. 검증을 먼저 끝내고 기존 파일을 고유 backup_dir에 복사·해시 대조한다. 같은 destination 디렉터리에 새 임시 파일을 준비해 receipt에 새 PDF·overlay·명세·검토 해시와 백업 위치를 준비한 뒤 최종 os.replace로 교체한다. 검증·백업·receipt 준비·교체 실패 시 임시 파일만 정리하고 원본을 유지한다. os.replace 이후 실패할 수 있는 추가 필수 쓰기 작업을 두지 않는다.
- [ ] **Step 4:** 같은 테스트 실행. Expected: PASS. 함수는 실제 화면 검토를 자동으로 대신하지 않으며 검토 증거 결속만 확인한다.
- [ ] **Step 5:** 두 파일만 stage/diff 확인 후 커밋. 메시지: `feat(ec2): publish reviewed answer PDFs safely`.

### Task 6: 두 스킬의 실제 저작·부모 실행 흐름 연결

**Files:**
- Modify: `.claude/skills/ec2-review-pack/SKILL.md`
- Modify: review-pack references `content-rules.md`, `review-prompt.md`, `manifest-guide.md`, `problem-selection.md`, `problem-explain-integration.md`
- Modify: review-pack scripts `manifest.py`, `assemble.py`, `check_html.py`
- Modify: `.claude/skills/ec2-problem-explain/SKILL.md`, references `authoring.md`, `verification.md`
- Create: `.claude/skills/ec2-review-pack/tests/test_learning_style_flow.py`
- Modify: review-pack tests `_util.py`, `test_manifest.py`, `test_check_html.py`, `test_assemble.py` 및 fixtures/mini-run/manifest.json
- Modify: 두 스킬의 `tests/test_skill_files.py` (실제 브리프 연결 확인)

**Interfaces:**
- Consumes: Task 1~5.
- Produces: 부모 manifest 필수 `learning_style: StyleSnapshot`; `RUN/learning-style-audit.json`는 모든 topic ID 대상.
- `manifest.validate(m, repo=None)`는 snapshot 형식을 검사하고 repo가 있으면 check_style도 수행한다. assemble/check CLI에 `--repo`를 추가하고 제공되지 않으면 현재 실행 파일 기준 repo를 사용한다. 명시 repo가 없다고 검사를 생략하지 않는다. assemble(run_dir, out_dir, *, repo: Path | None=None)도 쓰기 전에 현재 snapshot을 검증한다. 테스트 _util은 tracked mini-run을 임시 폴더로 복사한 뒤 유효한 snapshot/audit를 준비한다. tracked fixture에 환경별 hash를 하드코딩하지 않는다.
- `check_pack(m, note_path, *, repo: Path, style_audit: dict, defer_answer_pdf: bool=False) -> list[Problem]` 및 CLI `--defer-answer-pdf`. CLI의 manifest 모드는 manifest.json과 같은 RUN의 learning-style-audit.json을 필수로 읽고, 현재 snapshot과 모든 topic ID에 대해 validate_style_audit를 호출한다. 유예는 정확한 manifest answer_pdf 경로의 '파일 없음' 한 건만 해당하며 path 문자열 전체를 비교한다. 그 외 링크/앵커/내용/명세 검사는 유지한다. 유예 실행은 `PRELIMINARY: answer PDF pending`으로 출력하고 최종 pass로 기록하지 않는다.

- [ ] **Step 1: 실패 테스트 작성.** 임시 mini-run에 명세·snapshot·audit를 만들고 기존 정리노트 조립으로 실제 링크를 검사한다.

```python
def test_preliminary_defers_only_expected_answer(note_fixture):
    assert note_fixture.check(defer_answer_pdf=True) == []
    assert note_fixture.check(defer_answer_pdf=False)
    note_fixture.break_unrelated_link()
    assert note_fixture.check(defer_answer_pdf=True)

def test_note_style_audit_covers_all_topics(note_fixture):
    note_fixture.remove_audit_topic('why-circuit')
    assert note_fixture.check_final_style()

def test_zero_problem_pack_skips_pdf_without_skipping_style(note_fixture):
    note_fixture.set_zero_problems()
    assert note_fixture.requires_pdf is False
    note_fixture.change_profile()
    assert note_fixture.check(defer_answer_pdf=False)
```

추가: `test_manifest_missing_snapshot_fails`, `test_assembly_rejects_stale_profile_before_writes`, `test_final_links_pass_only_with_real_answer`, `test_parent_briefs_include_profile_and_audit`, `test_child_briefs_include_profile_and_core_contract`. fixture의 requires_pdf는 manifest.problems의 참/거짓에 대응하는 테스트용 속성이며 새 production API가 아니다.
- [ ] **Step 2:** 새 flow 테스트 실행. Expected: 필수 snapshot/예비 검사 미구현으로 FAIL.
- [ ] **Step 3:** 부모 작성자·리뷰어의 읽기 목록에 명세 절대 경로와 snapshot을 추가한다. 개념 토픽은 첫 설명에서 회로 역할/핵심 관계를 먼저 보여주고 formal에서 상세 유도를 잇는다. 기존 why·eli5·formal·보충·summary 계약은 보존한다. lite는 부모가 실제 개인화 감사를 수행하고 기록한다.
- [ ] **Step 4:** 자식 작성자는 핵심 route를 먼저 저작하고 상세 일곱 구역과 연결한다. 리뷰어는 핵심과 상세의 답·단위·근사·그림을 대조하고 전체 StyleAudit를 작성한다. 독립 검산은 이전처럼 원문에서 먼저 답을 구한다. 자식은 PDF를 직접 교체하지 않는다.
- [ ] **Step 5:** 부모 실행 순서를 아래로 바꾼다. 초기 문제지 빌드는 `--mode problems`; legacy 답안 선행 빌드 지시를 제거한다. 추출 이후 정리노트 바이트를 바꾸지 않는다.

```text
명세 snapshot → 범위/manifest → 작성/조립 → 문제지만 빌드
→ 부모 내용/화면/MD/개인화 감사 + 답안 링크만 예비 검사
→ 자식 extract/저작/독립 검산/build/check/네 검토/개인화 감사/publish
→ 발행된 overlay로 RUN에 --mode answers --answer-overlay 빌드
→ PDF 실제 렌더 페이지 검토와 answer-review.json 기록
→ publish_answer.py → 유예 없는 정리노트 링크/명세/감사 최종 검사
```

이전 답안의 문제 목록과 새 목록이 다르면 기존 백업 계약에 따라 이전 답안을 보관하고 최신 산출로 취급하지 않는다. 자식/PDF 실패 시 전체 완료를 보고하지 않는다. 기존 팩이면 부모와 자식의 이번 실행 전 백업으로 노트·목록·PDF·설명 소유 파일을 서로 맞는 이전 상태로 복구하고, 실패한 새 산출은 RUN에 보관한다. 새 팩이면 이번 실행이 만든 파일만 RUN의 withheld 영역에 보관하고 발행 경로에 미완성 팩을 남기지 않는다. 복구는 기존 통합 계약의 경로 allowlist·백업 해시 확인을 사용하며 다른 날짜 파일은 건드리지 않는다. 문제 0개는 자식·PDF 없이 개념 명세/감사와 최종 노트 검사만 수행한다.
- [ ] **Step 6:** `python3 -m pytest .claude/skills/ec2-review-pack/tests -q`, 별도 프로세스에서 EPE tests 실행. Expected: PASS. 문서 읽기 의무의 문자열 테스트만으로 실제 적용을 증명했다고 보고하지 않는다.
- [ ] **Step 7:** 위 파일을 명시적으로 stage/diff 확인 후 커밋. 메시지: `feat(ec2): integrate personal style into review workflows`.

### Task 7: 대표 회로의 실제 통합·화면 검증

**Files:**
- Create: `.claude/skills/ec2-problem-explain/tests/test_personalized_pipeline.py`
- Create after real checks: `docs/superpowers/reviews/2026-10-21-ec2-learning-style.md`
- 임시 산출물: RUN 안에만. 기존 복습노트 날짜 폴더를 재생성하지 않는다.

**Interfaces:**
- Consumes: Task 1~6, 설계의 여섯 대표 문항 E9.05/E9.06/E9.01/P9.23/E9.11/P9.30.
- Produces: 합성 lifecycle 회귀 테스트와 실제 내용/화면 검토 보고. 실제 수학 검토는 합성 승인 fixture와 분리한다.

- [ ] **Step 1: end-to-end 실패 테스트 작성.** 기존 make_repo 기반 임시 repo에서 extract→작성 fixture→build→합성 검토→publish→workbook answers subprocess를 연결한다. 새로운 정상 통합 기대값과 실패 조건을 먼저 작성한다.

```python
def test_published_core_drives_pdf_data(pipeline):
    result = pipeline.run_json_only()
    assert result.returncode == 0
    assert pipeline.answer_json['problems'][0]['solution']['answer'] == pipeline.expected_core_answer
    assert pipeline.original_problem_md_bytes == pipeline.current_problem_md_bytes

def test_unreviewed_or_changed_bundle_never_replaces_answer(pipeline):
    pipeline.stop_before_review()
    assert pipeline.run_answers().returncode != 0
    assert pipeline.destination_bytes == pipeline.previous_answer_bytes
```

pipeline helper는 위 테스트 파일에서 정의하며 실제 CLI를 별도 프로세스로 실행한다. test_parent_failure_restores_coherent_pack을 추가해 부모 계약의 백업·복구 순서를 fixture에서 실행하고 기존 노트·problems.txt·PDF·설명 파일의 바이트가 모두 돌아오는지 확인한다. 그림이 있는 a/b 문항과 기존 답안 sentinel을 포함한다. 이미 정상 통과하는 경로는 억지로 코드를 깨서 red를 만들지 말고 회귀 검증임을 기록한다.
- [ ] **Step 2:** `python3 -m pytest .claude/skills/ec2-problem-explain/tests/test_personalized_pipeline.py -q`. 통합 누락이 있으면 해당 소유 Task의 코드를 수정한 뒤 PASS를 확인한다.
- [ ] **Step 3:** 임시 repo/RUN에 여섯 대표 문항을 실제로 저작한다. 현재 source의 조건·그림·참고 풀이를 다시 읽는다. 스킬의 작성/독립 검산 역할 분리와 검토 기준을 적용한다. 원문과 불일치하면 원문 MD를 고치지 않고 disputed로 보고한다.
- [ ] **Step 4:** 실제 HTML의 데스크톱/모바일·light/dark 네 조합에서 기존 epe_browser_check.py를 실행하고 스크린샷을 확인한다. 핵심 풀이가 상세 설명보다 먼저 보이고, 그림의 화살표·제어 전압·단위·첨자 및 MD/요약이 일치하는지 확인한다.
- [ ] **Step 5:** 검토된 overlay로 video-16x9 답안 PDF를 RUN에 렌더한다. 모든 페이지를 PNG로 열어 선·그림·식의 잘림, 소문항 누락, 하단 180px 여백과 가독성을 확인한다. 넘침이 있으면 핵심 원고를 수정하고 해당 EPE 검토부터 다시 수행한다. 폰트를 추가로 무리하게 줄이거나 상세 PDF를 새로 만들지 않는다.
- [ ] **Step 6:** 세 테스트 suite를 별도 프로세스로 한 번씩 실행하고 git diff --check를 실행한다. 새 실패·변경이 없으면 같은 검사를 불필요하게 반복하지 않는다.
- [ ] **Step 7:** 리뷰 보고서에 규칙 적용 사례, 실제 명령·결과·증거 경로, 여섯 문항 판정, 단위/부호 보완, PDF 화면 검토, 미실행/환경 제한을 구분해 기록한다. 검증 상태를 과장하지 않는다.
- [ ] **Step 8:** 새 통합 테스트와 실제 리뷰 보고서 및 확인된 수정만 명시 stage/diff 확인 후 커밋. 메시지: `test(ec2): verify personalized learning pipeline`.

## 실행 전후 확인과 인계

- 실행 전: `git status --short`, 현재 브랜치·worktree 확인, 사용자가 고른 실행 방식 확인. 계획 작성만으로 구현에 착수하지 않는다.
- 실행 후: 변경 파일 목록, 세 suite 결과, 실제 HTML/PDF 검토 범위, 개인 명세 경로, 원본 보존과 대표 검증만 수행했다는 범위를 보고한다.
- 실행 방식 추천: Subagent-driven. 7개 작업이 공통 스냅샷·소문항·검토·PDF 경계를 공유하므로 작업마다 새로운 리뷰어가 계약 누락을 확인하는 편이 적합하다. Native를 고르면 같은 계획을 직접 구현하고 마지막 독립 전체 리뷰를 수행한다.

## 계획 자체 검토 기록

- Spec coverage: 근거/12규칙(Task 1), 핵심 먼저/상세 유지(Task 2/6), 필수 읽기/감사(Task 3/6), PDF 공유(Task 4), 실패 보존(Task 5), 실제 사례 검증(Task 7).
- Step scan: 코드 단계에 파일·함수·입출력·실패 기준을 지정했다. 문서·fixture는 소유 작업에 포함했고 별도 scaffolding 작업을 만들지 않았다.
- Type consistency: learning_style와 기존 profile을 구별하고, workbook_id/pN 및 data-core-subpart/data-subpart를 구별했다. 계약 A/B/C를 후속 작업이 재사용한다.
- Review Focus: 다섯 항목 모두 소유 작업의 명명된 테스트로 연결했다.
- Proportion: 구현 함수 본문을 작성하지 않고 데이터 계약과 확인할 행위를 결정했다. 실제 테스트·브라우저·PDF 검토는 구현 단계의 할 일이며 계획 작성 단계에서 실행했다고 주장하지 않는다.
