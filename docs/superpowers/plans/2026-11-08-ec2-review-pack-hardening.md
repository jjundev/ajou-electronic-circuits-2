# ec2-review-pack 재발 방지 강화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1106 세션에서 시간을 잡아먹은 아홉 가지 실패를 실행기(runner) 코드·브리프·문서에서 막는다. 같은 범위를 다시 돌렸을 때 accept 거부와 보류 재실행 없이 끝까지 가는 것이 목표다.

**Architecture:** 기존 `pack_cli → pack_flow / pack_receipts / pack_actions / pack_seed` 흐름은 그대로 두고 검증 지점만 고친다. 경로는 NFC 하나로 맞추고, 작업자가 accept와 같은 검증을 미리 돌리는 명령을 추가하고, 수정 요청이 감사 결함을 빠짐없이 덮는지 실행기가 확인한다. 저장소에 쓰지 않는 답안 빌드는 재시도할 수 있게 하고, 이어받기는 섹션 작성 결과를 늦게라도 가져올 수 있게 한다. 문서와 작업자 지시문은 이 동작에 맞게 갱신한다.

**Tech Stack:** Python 3.14(homebrew), pytest, playwright(Chrome), pymupdf. 대상은 skill `.claude/skills/ec2-review-pack`과 `workbook/`이다.

**Spec:** 이 대화의 grill-yourself 설계 "ec2-review-pack: 1106 세션의 실수가 재발하지 않게 고치기"(결정 #1–#12). 사용자 결정 필요 항목은 기본값으로 확정됐다: #10 `~/.cache/ec2-review-pack/`, #11 이번에 포함, #12 동시 작업자 5.

## Global Constraints

- 테스트 실행 명령(`$PYTEST`): `uv run --no-project --python /opt/homebrew/opt/python@3.14/bin/python3.14 --with pytest --with pyyaml --with pymupdf --with playwright python -m pytest`
- 스킬 테스트 폴더: `.claude/skills/ec2-review-pack/tests/`(공통 도우미는 `tests/_util.py`, `tests/pack_support.py`). workbook 테스트 폴더: `workbook/tests/`.
- 경로 정책: 저장소와 작업자가 쓰는 경로는 모두 Unicode NFC 문자열이다. 비교는 `unicodedata.normalize('NFC', str(path))` 기준이다.
- RUN 기본 위치: `~/.cache/ec2-review-pack/<range>-<YYYYmmdd-HHMMSS>`. `/tmp`, `/private/tmp`, `/var/folders` 아래 경로는 `--allow-tmp` 없이는 거부한다.
- 동시 작업자 기본값: 5(문서 기본값; `next --slots`는 그대로 인자로 받는다).
- 화면 기준: 1920×1080 16:9, 하단 180px 자막 여백. SVG 라벨과 도선 간격 ≥ 0.6em(13px 글꼴에서 7.8px). 375px과 1280px, 라이트·다크에서 수식 가로 넘침 0.
- CLI 응답은 JSON 한 개, 2,000자 이하(기존 계약). 작업자 반환은 800자 이하(기존 계약).
- 기존 품질 계약(내용 수정 1회, 기계/브라우저 수정 2회, 독립 검산, 실제 화면 검토)은 완화하지 않는다.
- 커밋 메시지는 Conventional Commits이고, 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`을 붙인다.

## Review Focus

1. 저장소 폴더가 NFD이고 RUN과 작업자 경로가 NFC인 경우: accept, build-answers, final-check가 모두 통과해야 한다. Task 1과 Task 0에서 테스트한다.
2. 진짜 저장소 밖 경로(형제 폴더 `전자회로2-copy/...`)를 NFC 비교로 잘못 통과시키지 않아야 한다. Task 1에 테스트를 둔다.
3. content fix 요청에서 노트 밖 문제 ID 결함(`[P12.04]`)이 selection 담당으로 대응돼야 하고, 빠지면 거부돼야 한다. Task 5에 테스트를 둔다.
4. build-answers가 실패한 뒤 재시도할 때, 저장소 inventory가 바뀌었다면 재시도하지 말고 recovery_required를 유지해야 한다. Task 6에 테스트를 둔다.
5. 이어받기에서 섹션 브리프의 RUN 경로만 다르면 author를 carried로 가져오고, 메모 한 줄이라도 다르면 가져오지 않아야 한다. Task 7에 테스트를 둔다.

---

### Task 0: 테스트 실행기 준비와 workbook 수정 커밋

**Files:**
- Modify: `workbook/build_workbook.py`(이미 수정됨: `root_spelling`)
- Modify: `workbook/templates/answer.html`(이미 수정됨: `DENSE_FIG_AREA_MM2`, `--w-min`, 그림 쪽 첫 단계 이동)
- Test: `workbook/tests/test_build.py`, `workbook/tests/test_video_layout.py`

**Interfaces:**
- Produces: `build_workbook.root_spelling(overlay_path: str | Path) -> Path`. overlay 경로의 표기를 따르는 저장소 루트이고, 저장소 밖이면 `paths.ROOT`를 그대로 돌려준다.

- [ ] **Step 1: `$PYTEST --version`이 동작하는지 확인한다.** 기대 결과: `pytest 8.x`. 실패하면 Global Constraints의 명령을 고친 뒤 이 문서를 수정한다.
- [ ] **Step 2: 실패하는 테스트를 `workbook/tests/test_build.py`에 추가한다.**

```python
def test_root_spelling_matches_nfc_argument_under_nfd_root(monkeypatch, tmp_path):
    nfd = tmp_path / unicodedata.normalize("NFD", "전자회로2")
    (nfd / "복습노트").mkdir(parents=True)
    monkeypatch.setattr(build_workbook.paths, "ROOT", nfd)
    arg = unicodedata.normalize("NFC", str(nfd / "복습노트/x/.assets/a/answer-overlay.json"))
    root = build_workbook.root_spelling(arg)
    assert str(root) == unicodedata.normalize("NFC", str(nfd))

def test_root_spelling_keeps_root_for_outside_path(monkeypatch, tmp_path):
    monkeypatch.setattr(build_workbook.paths, "ROOT", tmp_path / "repo")
    assert build_workbook.root_spelling(tmp_path / "repo-copy/a.json") == tmp_path / "repo"
```

- [ ] **Step 3: `$PYTEST workbook/tests/test_build.py -k root_spelling -v`를 실행한다.** 기대 결과: PASS(구현은 이미 있다). FAIL이면 `root_spelling`을 고친다.
- [ ] **Step 4: 실패하는 테스트를 `workbook/tests/test_video_layout.py`에 추가한다.** 이름은 `test_dense_figure_keeps_cap_width_and_paginates`. `w_mm=84.7, h_mm=71.6` 그림 하나와 풀이 단계 8개짜리 합성 문항으로 답안 PDF를 렌더한다. 다음을 assert한다.
  - 그림 쪽의 `img.fig` 렌더 폭이 `84.7*1.5mm`(≈480px)의 98% 이상이다.
  - `[data-overflow]`인 page가 0개다.
  - 쪽 수가 2 이상이다.
- [ ] **Step 5: `$PYTEST workbook/tests/test_video_layout.py -v`를 실행한다.** 기대 결과: 모두 PASS.
- [ ] **Step 6: 커밋한다.**

```bash
git add workbook/build_workbook.py workbook/templates/answer.html workbook/tests/test_build.py workbook/tests/test_video_layout.py
git commit -m "fix(workbook): match repo spelling for answer overlay and keep dense figures readable"
```

### Task 1: 저장소 경로 NFC 고정

**Files:**
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_flow.py:179`(`init_run`)
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_receipts.py:80-96`(`_source`)와 receipt의 inputs/outputs 경로를 검사하는 모든 `is_relative_to`
- Test: `.claude/skills/ec2-review-pack/tests/test_pack_receipts.py`, `tests/test_pack_flow.py`

**Interfaces:**
- Produces: `pack_flow.nfc_path(p: str | Path) -> Path`. NFC 문자열로 만든 Path이며 resolve는 하지 않는다. `pack_receipts`가 import해서 쓴다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_init_stores_nfc_repo`: NFD 이름의 repo로 init하면 `state['repo'] == unicodedata.normalize('NFC', ...)`.
  - `test_source_map_accepts_mixed_nfd_component`: source-map pdfs 경로의 `강의노트` 성분만 NFD여도 source-prep accept가 통과한다.
  - `test_source_map_rejects_sibling_outside_repo`: `<repo>-copy/강의노트/x.pdf`이면 `'source material missing/outside REPO'`.
- [ ] **Step 2: `$PYTEST .claude/skills/ec2-review-pack/tests/test_pack_receipts.py -k "nfd or nfc or sibling" -v`를 실행한다.** 기대 결과: 앞의 두 테스트는 FAIL, 마지막은 PASS.
- [ ] **Step 3: 구현한다.** `init_run`에서 `repo = nfc_path(Path(repo).resolve())`로 고정한다. `_source`와 receipt 경로 검사는 `nfc_path(path).is_relative_to(nfc_path(repo))`로 바꾼다. 파일 존재 확인은 원래 경로로 한다(APFS는 표기에 무관하다).
- [ ] **Step 4: 같은 테스트를 다시 실행하고, 전체 `$PYTEST .claude/skills/ec2-review-pack/tests -q`도 실행한다.** 기대 결과: 모두 PASS.
- [ ] **Step 5: 커밋한다.** `fix(review-pack): store NFC repo path and compare paths in NFC`

### Task 2: RUN 기본 위치와 임시 폴더 거부

**Files:**
- Modify: `scripts/pack_cli.py:56-62`(init 파서: `--run` 선택, `--allow-tmp`)
- Modify: `scripts/pack_flow.py:175`(`init_run(..., allow_tmp: bool = False)`)
- Test: `tests/test_pack_cli.py`

**Interfaces:**
- Produces: `pack_flow.default_run_dir(range_: str, now: datetime) -> Path` → `~/.cache/ec2-review-pack/<range>-<YYYYmmdd-HHMMSS>`. `pack_flow.TEMP_ROOTS = ('/tmp', '/private/tmp', '/var/folders', '/private/var/folders')`.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_init_rejects_tmp_run`: `--run /tmp/x`이면 `error_code == 'validation_failed'`이고 reason에 `'temporary'`가 들어 있다.
  - `test_init_allows_tmp_with_flag`
  - `test_init_without_run_uses_cache_dir`: HOME을 tmp_path로 monkeypatch한다. 응답의 `details_path`가 `tmp_path/.cache/ec2-review-pack/`로 시작한다.
- [ ] **Step 2: `$PYTEST tests/test_pack_cli.py -k init -v`를 실행한다.** 기대 결과: 새 테스트 FAIL.
- [ ] **Step 3: 구현한다.** 기존 테스트가 tmp_path(macOS에서 `/private/var/folders/...`)를 RUN으로 쓴다. 그래서 `tests/pack_support.py`의 init 도우미가 `allow_tmp=True`를 넘기도록 같이 고친다.
- [ ] **Step 4: 전체 스킬 테스트를 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): default RUN to ~/.cache and refuse temp dirs`

### Task 3: 브리프에 신원과 receipt 규칙 넣기

**Files:**
- Modify: `scripts/pack_flow.py:552-560`(brief `data`, `constraints`)
- Test: `tests/test_pack_flow.py`

**Interfaces:**
- Produces: brief.json에 `run_id: str`, `attempt: str | None`(claim 뒤 값)이 들어간다. `constraints`에 다음 세 문자열을 덧붙인다.
  - `'done/ready-for-publish receipt는 unresolved=[]; 비차단 메모는 report에만'`
  - `'모든 경로 문자열은 NFC; run_id·attempt는 이 브리프 값만 사용'`
  - `'Write 도구가 막히면 Bash heredoc으로 report 작성; 반환 전 task check 실행'`

- [ ] **Step 1: 실패하는 테스트 `test_claimed_brief_carries_run_id_attempt_and_rules`를 작성한다.** claim 뒤 brief의 `run_id == state['run_id']`, `attempt == claim 응답 attempt`이고 위 세 문자열이 constraints에 들어 있다.
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 구현한다.** claim이 이미 `write_briefs`를 부르는지 확인하고, 부르지 않으면 claim 경로에서 해당 brief만 다시 쓴다.
- [ ] **Step 4: 전체 테스트를 실행한다.** 기대 결과: PASS. 기존 brief 스냅샷 테스트가 있으면 갱신한다.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): put run_id, attempt and receipt rules in briefs`

### Task 4: `task check` 사전 검증 명령

**Files:**
- Modify: `scripts/pack_cli.py:63-70`(`task check --run --task --attempt --receipt`)
- Modify: `scripts/pack_flow.py:accept_task` 주변에 `check_task(run, task_id, attempt, receipt_path) -> dict` 추가
- Test: `tests/test_pack_cli.py`, `tests/test_pack_receipts.py`

**Interfaces:**
- Consumes: `pack_receipts.validate_receipt(state, task, receipt_path)`(자식 receipt면 내부에서 `_child`)
- Produces: CLI 응답 `{"status":"ok"|"failed","error_code":null|"validation_failed","reason":...}`. run-status.json의 바이트는 바뀌지 않는다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_task_check_passes_valid_receipt_without_state_change`: 실행 전후 run-status.json의 sha가 같고 status가 ok다.
  - `test_task_check_reports_unresolved`: reason이 `'unresolved successful receipt'`다.
  - `test_task_check_reports_identity_mismatch`: run_id가 틀리면 reason이 `'receipt identity mismatch'`다.
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL(unknown command).
- [ ] **Step 3: 구현한다.** state를 `copy.deepcopy`로 읽어 validate만 하고 `update_state`는 부르지 않는다. lock은 읽기 lock만 잡거나 잡지 않는다.
- [ ] **Step 4: 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): add read-only task check for receipts`

### Task 5: content fix가 감사 결함을 모두 덮는지 강제

**Files:**
- Create: `scripts/pack_findings.py`
- Modify: `scripts/pack_flow.py:639`(`request_fixes`)
- Test: `tests/test_pack_findings.py`, `tests/test_pack_flow.py`

**Interfaces:**
- Produces:
  - `pack_findings.blocking_findings(report_md: Path) -> list[tuple[str, str]]`: `## Critical`, `## Important`, `## Minor` 절의 `- [<id>]` 항목을 `(severity, id)`로 돌려준다.
  - `pack_findings.owner_of(item_id: str, manifest: dict) -> str`: 토픽 ID는 그 토픽이 속한 섹션의 `author-<sid>`, 문제 ID(manifest problems의 id)는 `selection`, 그 밖은 `scope-final`.
  - fix request JSON에 선택 필드 `waived: [{"id": str, "reason": str}]`를 추가한다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_blocking_findings_parses_three_sections`: `[s4-cheatsheet]`(Important)와 `[P12.04]`(Important)가 모두 나온다.
  - `test_owner_maps_problem_to_selection`
  - `test_content_fix_rejects_missing_owner`: 직전 style-audit report에 `[P12.04]`가 있는데 items에 selection이 없으면 `FlowError('content fix misses findings: P12.04→selection')`.
  - `test_content_fix_accepts_waived`
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 구현한다.** `request_fixes`는 `category == 'content'`일 때만 검사한다. 대상 report는 needs_fix 상태인 style-audit와 content-review task의 receipt.report다. machine_browser는 검사하지 않는다.
- [ ] **Step 4: 전체 테스트를 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): require content fixes to cover every audit finding`

### Task 6: build-answers 재시도와 pdf-qa 수정 시 재빌드

**Files:**
- Modify: `scripts/pack_actions.py:20`(`RUN_ONLY = frozenset(('build-answers',))`), `:442`(실패 status 판정)
- Modify: `scripts/pack_flow.py:639`(`request_fixes`: items에 `pdf-qa`가 있으면 `state['actions']['build-answers']`를 `status='stale'`로 바꾸고 history에 남긴다)
- Test: `tests/test_pack_actions.py`, `tests/test_pack_flow.py`

**Interfaces:**
- Produces: build-answers가 실패하고 inventory 변화가 없으면 `status='needs_fix'`이고 `next.kind == 'run'`, `action == 'build-answers'`로 같은 action을 다시 요청한다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_build_answers_failure_is_retryable`: 가짜 명령 exit 1이면 상태가 needs_fix이고 next가 build-answers를 다시 요청한다.
  - `test_build_answers_failure_with_repo_write_stays_recovery_required`: 실행 중 pack inventory가 바뀌면 recovery_required다.
  - `test_pdf_qa_fix_restales_build_answers`
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 구현한다.** 판정식은 `mutation_started and action not in READ_ONLY | RUN_ONLY or inventory changed` → recovery_required이고, 그 밖은 needs_fix다.
- [ ] **Step 4: 전체 테스트를 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `fix(review-pack): retry RUN-only answer builds and rebuild after pdf-qa fixes`

### Task 7: 이어받기에서 섹션 작성 결과를 늦게 가져오기

**Files:**
- Modify: `scripts/pack_seed.py`(`seed_state`, 새 함수 `carry_deferred(state: dict) -> list[str]`)
- Modify: `scripts/pack_flow.py`(scope-final accept 직후 `carry_deferred` 호출)
- Test: `tests/test_pack_seed.py`

**Interfaces:**
- Produces: `state['seeded_from']['deferred'] = [task_id...]`(init 때 의존이 아직 끝나지 않아 보류된 author 후보). 반환값은 새로 carried된 id 목록이다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_author_carried_after_scope_final_when_brief_matches`: 이전 RUN과 새 RUN의 `briefs/s0.json`이 RUN 경로 치환 뒤 같고 `sections/s0.html` 해시가 receipt와 같으면 scope-final accept 뒤 author-s0이 done, carried다.
  - `test_author_not_carried_when_brief_note_changed`: notes 한 줄이 다르면 pending이다.
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 구현한다.** 비교는 `_Copier.value`로 이전 brief의 경로를 치환한 dict와 새 brief dict의 동등 비교다. carry 절차는 `seed_state`의 기존 루프 본문을 함수로 뽑아 같이 쓴다.
- [ ] **Step 4: 전체 테스트를 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): carry unchanged section authors after scope-final`

### Task 8: 화면 탐침 스크립트

**Files:**
- Create: `scripts/layout_probe.py`
- Test: `tests/test_layout_probe.py`(fixture HTML은 테스트 안에서 생성)

**Interfaces:**
- Produces: CLI `python3 layout_probe.py <html> [--widths 1280,375] [--themes light,dark] --out <json>`. 종료 코드는 결함 0이면 0, 결함이 있으면 1이다. JSON은 `{"html_sha256", "checks":[{"width","theme","overflow":[{"selector","excess_px"}],"label_gaps":[{"svg_id","text","gap_px"}]}]}`. 라벨 간격 기준은 `0.6 * font_size_px`이다.
- 측정 대상: `.katex-display`, 요약 패널(`.page-summary` 계열), `table`의 `scrollWidth - clientWidth > 1`. 각 `svg text` bbox와 같은 svg 안 `line`, `path`, `polyline` 사이의 최소 거리. 소자 기호(`.sym`, `[data-symbol]`)는 제외한다. 기본 모드에서는 요약 패널을 연 상태로 잰다.

- [ ] **Step 1: 실패하는 테스트를 작성한다.**
  - `test_probe_flags_wide_display_math_at_375`: 폭 900px 수식이면 overflow 1건이다.
  - `test_probe_flags_label_near_wire`: text가 선에서 5px이면 gap 1건이다.
  - `test_probe_clean_fixture_exits_zero`
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 구현한다.** playwright `chromium.launch(channel='chrome')`를 쓰고, 측정은 `page.evaluate` 한 번으로 한다.
- [ ] **Step 4: 실행한다.** 기대 결과: PASS.
- [ ] **Step 5: 커밋한다.** `feat(review-pack): add layout probe for overflow and label gaps`

### Task 9: 문서와 작업자 지시문

**Files:**
- Create: `references/worker-prompt.md`
- Modify: `SKILL.md`(1단계, 2단계, 5단계), `references/runner-contract.md`(시작 절, 배치 절, 수정 절, 기계 작업 절), `references/delegation.md`(인계 전 묶음 점검), `references/problem-explain-integration.md:30`(child-receipt), `references/execution-guide.md`(`0. 준비`, `3. 작성`)
- Test: `tests/test_skill_files.py`

**Interfaces:**
- Consumes: Task 2 `--allow-tmp`·기본 RUN, Task 4 `task check`, Task 5 `waived`, Task 6 재시도, Task 7 deferred carry, Task 8 `layout_probe.py`

- [ ] **Step 1: 실패하는 테스트를 `test_skill_files.py`에 추가한다.**
  - `test_worker_prompt_has_placeholders`: `{role}`, `{brief}`, `{attempt}`, `{run_id}`, `task check`, `800자`가 들어 있다.
  - `test_docs_mention_new_contracts`: SKILL.md에 `~/.cache/ec2-review-pack`, `NFC`가 있다. runner-contract.md에 `task check`, `--allow-tmp`, `waived`가 있다. delegation.md에 `layout_probe.py`가 있다. integration 문서에 `bucket`(폴더 이름)과 `SVG`(references) 문구가 있다.
- [ ] **Step 2: 실행한다.** 기대 결과: FAIL.
- [ ] **Step 3: 문서를 작성한다.**
  - **worker-prompt.md:** 역할, 브리프 경로, attempt, run_id 자리표시자와 공통 규칙(브리프 직접 읽기, receipt 형식 절 참조, NFC, RUN 밖 쓰기 금지, 다른 에이전트 금지, 상태 명령 금지, 반환 전 `task check`, 800자)을 15줄 안에 담는다. 재개용 짧은 변형(수정·재검토)도 하나 둔다.
  - **SKILL.md:**
    - 1단계: RUN 기본 위치와 NFC 규칙.
    - 2단계: 동시 작업자 기본 5, 작업자 호출은 worker-prompt 템플릿 사용.
    - 5단계: content fix는 감사·리뷰 결함 전체(노트 밖 문제 ID 포함)를 한 요청에 담고, 의도적으로 뺀 항목은 `waived`로 적는다.
  - **delegation.md:** 작성자 인계 전 점검에 `layout_probe.py`의 1280/375 × 라이트/다크 결함 0을 넣는다. 모든 역할에 반환 전 `task check`를 넣는다.
  - **integration 문서:** child-receipt의 `bucket`은 bucket 폴더 이름이고 `stage`는 현재 승인 HTML의 부모 폴더다. review.json references에는 부모 MD가 참조하는 SVG를 전부 넣는다. 반환 전 `task check`를 실행한다.
  - **execution-guide `0. 준비`:** RUN 생성 예시를 기본 위치로 바꾸고, `/tmp` 금지 이유(재부팅 시 손실)를 한 줄 적는다.
- [ ] **Step 4: 전체 스킬 테스트와 workbook 테스트를 실행한다.** 기대 결과: 모두 PASS.
- [ ] **Step 5: 커밋한다.** `docs(review-pack): document hardened runner contracts and worker prompt`
