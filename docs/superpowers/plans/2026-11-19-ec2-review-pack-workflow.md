# EC2 Review Pack Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 전자회로2 복습팩에서 독립 작업을 앞당기고, 승인된 결과를 재사용하며, 중단 후 같은 RUN을 복구할 수 있게 한다.

**Architecture:** 기존 Python 실행기의 revision, 시도 ID, 검증기를 재사용한다. 신규 흐름은 직접 입력과 필수 승인으로 작업을 배정하고 RUN 안에서 후보를 만든다. 공개 경로는 날짜별 잠금과 복구 기록을 사용하는 발행 작업에서만 갱신한다.

**Tech Stack:** Python, pytest, Playwright Chromium, PyMuPDF, 기존 workbook·문제설명·확인문제 CLI, JSON 상태 및 증거 파일.

**Spec:** [이 문서에 보관한 설계 계약](#design-contract). 1118 실행 분석과 뒤이은 수정 설계를 실행자가 채팅 없이 읽을 수 있도록 정리했다.

## Global Constraints

- 기존 공개 URL, 날짜 폴더, 파일명과 `/ec2-review-pack` 인자를 유지한다. 원문·강의자료·PROFILE은 읽기 전용이다.
- 기존 RUN은 생성 당시 계약을 사용한다. 신규 흐름은 우선 `pack_cli init --workflow parallel`로 선택한다. 1118 재현과 다음 실제 강의 검증을 모두 통과한 뒤 신규 RUN의 기본값을 변경한다. `--workflow legacy`로 새 레거시 RUN을 선택할 수 있다.
- 기존 교육 기준, 독립 풀이의 답안 비공개, 필수 실제 화면 검사, SVG WOFF2, 16:9 PDF의 1920×1080 기준 하단 180px 자막 여백, 최종 무유예 검사를 유지한다.
- 기능 분기는 원래 리뷰 기준을 모두 적용한다. 문제 0개인 팩은 문제지·답안·문제설명 작업을 건너뛰고 노트와 확인문제를 진행한다. 확인문제 보류 시 부모 팩은 완료로 유지한다.
- 상태·발행 변경은 입력 버전과 시도 ID 검증을 통과해야 한다. 기한 경과만으로 실행 중 시도를 회수하거나 소유권이 불명확한 공개 파일을 덮어쓰지 않는다.
- 저장소에서 사용 중인 Python 및 Playwright 의존성을 사용한다. 작업 큐 서비스, 신규 DB, 호스트 자동 재시작, 다른 과목 이식은 범위 밖이다.
- 테스트의 합성 판정은 fixture 한정이다. 1118 및 다음 회차 실사용 인수에는 실제 독립 풀이, SVG·브라우저·PDF 리뷰 기록을 남긴다.

## Review Focus

1. **같은 날짜에 외부 편집 또는 두 RUN이 발행을 시도**하면 한 RUN만 진행하고 다른 쪽의 변경을 보존한다. Task 3의 `test_publish_rejects_changed_baseline`.
2. **프로세스가 파일 교체 직후 죽으면** 실행기가 기록된 쓰기를 판별하고 검증된 이전 세트로 복구할 수 있다. Task 3의 `test_reconcile_after_replace_before_checkpoint`.
3. **선발 순서만 바뀌면** 독립 풀이가 숫자 순번을 따라 다른 문항에 붙지 않는다. Task 6의 `test_review_key_survives_order_only_change`.
4. **이전 작업자가 종료 후 제출하면** 기존 시도의 쓰기와 receipt가 후임의 결과를 바꾸지 않는다. Task 8의 `test_late_receipt_cannot_replace_new_attempt`.
5. **새 팩에서 확인문제가 보류됐는데 예전 확인문제가 남아 있으면** 현재 확인문제로 노출되지 않는다. Task 7의 `test_old_quiz_not_visible_after_changed_parent`.

---

## Design Contract

1118은 약 4시간 40분이 걸렸으며 중단과 재개 사이의 약 100분은 호스트 공백이다. 개선 대상은 나머지 실행 중 대기·재작업·복구와 메인 컨텍스트다. 1118의 알려진 재작업 사례는 Chromium의 `file://` 차단에 따른 첫 PDF 실패, 초기 감사 수정 후 발견한 안정성 설명 누락, SVG WOFF2 재변환, 답안 1쪽 라벨 접촉, 작업자 소실 후 인계다.

작업 가능 여부는 직접 입력과 필요한 승인을 기준으로 계산한다. 문제 목록 확정 뒤 문제지 빌드·설명 작성·블라인드 풀이를 노트 작성과 겹친다. 같은 노트 후보에서 개인화 감사와 내용 리뷰를 실시하고 지적을 모아 수정한다. 화면 검토와 MD·SVG 변환은 동일한 고정 HTML을 읽는다. 확인문제 초안은 검토된 노트·MD·문제 목록을 사용해 일찍 만들고, 공개는 부모 최종 검사와 실제 입력 일치 뒤에 한다. 답안은 검토된 후보 overlay로 만들고 부모 팩을 발행할 때 설명과 다시 대조한다.

수정과 재개가 새 RUN을 강제하는 범위를 줄인다. 내용·시각 승인 유효성, 작업자에게 제공할 자료, 전체 증거 보관을 구분한다. 작업자가 낸 내용·시각 판정을 실행기가 만들어 내지 않는다. 설명 문단 하나나 PDF 한 페이지를 고치면 변경된 대상과 관련 참조만 다시 검토하되, 공통 렌더 자원·템플릿·교육 기준이 바뀌면 영향받는 전체 묶음을 검토한다. 효과는 중단 공백과 실제 실행·대기·재작업을 분리해서 기록한다.

## File Structure

| 책임 | 파일 |
|---|---|
| 브라우저 선택, 오프라인 자원 경로, 렌더 사전 검사 | `workbook/browser_runtime.py`, `workbook/render.py`, `workbook/vendor_route.py`, 리뷰팩 `scripts/layout_probe.py`, 확인문제 `scripts/browser_check.py` |
| 실제 repo·후보 팩·공개 팩 경로와 선택 목록 | `workbook/pack_paths.py`, `workbook/answer_overlay.py`, `workbook/build_workbook.py`, 리뷰팩 `scripts/assemble.py`, `scripts/check_html.py`, `scripts/html2md.py`, `scripts/pack_actions.py`, 문제설명 `scripts/epe_source.py`, `scripts/epe_cli.py`, `scripts/epe_publish.py` |
| 날짜 잠금, 공개본 반영·대조·복구 | 리뷰팩 `scripts/pack_publication.py`, `scripts/pack_files.py`, `scripts/pack_actions.py`, 확인문제 `scripts/concept.py`, 문제설명 `scripts/epe_files.py` |
| 작업 그래프와 RUN 상태 | 리뷰팩 `scripts/pack_graph.py`, `scripts/pack_flow.py`, `scripts/pack_cli.py`, `scripts/pack_actions.py` |
| 지적, 대상별 승인·브리프·증거 | 리뷰팩 `scripts/pack_findings.py`, `scripts/pack_approvals.py`, `scripts/pack_receipts.py`, `scripts/pack_flow.py`, 문제설명 `scripts/epe_contract.py` |
| 확인문제의 조기 제작·부모 결속 | 확인문제 `scripts/source.py`, `scripts/concept.py`, `scripts/blind.py`, 리뷰팩 `scripts/pack_graph.py`, `scripts/pack_flow.py` |
| 일괄 인계·재개·관측·운영 계약 | 리뷰팩 `scripts/pack_cli.py`, `scripts/pack_flow.py`, `scripts/pack_actions.py`, `SKILL.md`, `references/{runner-contract,delegation,worker-prompt,execution-guide,problem-explain-integration}.md`, 문제설명·확인문제 `SKILL.md` |

아래에서 **리뷰팩**, **문제설명**, **확인문제**는 각각 `.claude/skills/ec2-review-pack`, `.claude/skills/ec2-problem-explain`, `.claude/skills/ec2-concept-check`이다. 명령은 저장소 루트에서 실행한다. `dict`로 넘기는 필드와 오류 코드는 명시한 계약을 따른다. 각 자동 테스트는 해당 스킬이나 workbook의 임시 fixture를 사용한다. 리뷰팩에서는 `tests/pack_support.py`의 `make_run`, `install_task`, `receipt_for`를 시작점으로 써서 실제 날짜 폴더를 건드리지 않는다.

**의존 순서**는 `1 → 2 → 3 → 4 → 5 → 6`, `3 + 4 + 6 → 7`, `4 + 5 + 6 + 7 → 8`, `1–8 → 9`이다. 작업마다 명시된 테스트를 red/green으로 확인한 뒤 해당 변경만 커밋한다. 기본값 전환은 Task 9의 실제 인수 뒤 별도 커밋이다.

### Task 1. 공통 렌더 세션과 실제 PDF 사전 검사

**Files** — Create `workbook/browser_runtime.py`, `workbook/tests/test_browser_runtime.py`. Modify `workbook/render.py:50`, `workbook/vendor_route.py:48`, `.claude/skills/ec2-review-pack/scripts/layout_probe.py:85`, `.claude/skills/ec2-concept-check/scripts/browser_check.py:34`.

**Interfaces** — `launch_chromium(playwright, *, executable: Path | None = None) -> Browser`; `install_render_routes(page, *, local_roots: tuple[Path, ...], vendor_resolver: Callable[[str], Path | None] | None = None, blocked: set[str]) -> None`; `local_url(path: Path, root: Path) -> str`; `render_preflight(output_dir: Path) -> dict` in `workbook/render.py` returns `status`, `browser_version`, `pdf`, `page_count`, `error_code`. Existing `render_pdf` and `measure_typography` signatures stay available.

- [ ] Add `test_preflight_writes_real_pdf_without_file_urls` using a request observer rejecting `file:` and a real browser. Add `test_local_routes_block_escape_and_unknown_origin` covering encoded traversal, symlink escape and unexpected remote assets. Assert:

  ```python
  assert result['status'] == 'pass'
  assert result['page_count'] == 1
  assert result['pdf'].read_bytes().startswith(b'%PDF-')
  assert not any(url.startswith('file:') for url in requested_urls)
  assert {escaped_path_url, symlink_url, remote_url} <= blocked
  ```

- [ ] Run `python3 -m pytest workbook/tests/test_browser_runtime.py -q`. Expect missing shared entry points on baseline. Use the repo's verified Playwright environment with real Chromium for the green run.
- [ ] Implement `launch_chromium`, `local_url` and `install_render_routes`. Use an explicit executable when supplied, then try Playwright Chromium and the existing Chrome fallback. Use synthetic loopback origin fulfilled by Playwright, without a listening server. Canonicalize and check roots before reading and whitelist exact vendor resolutions. The browser's real navigation and all renderer readiness checks use this same route.
- [ ] Implement `render_preflight(output_dir)` using the existing render entry for a one-page 16:9 template fixture with local SVG, KaTeX and Pretendard. Check `data-ready`, rendered formula, `document.fonts` and referenced resources, then open the PDF with PyMuPDF. Report a specific failure for launch, transport, readiness, font or PDF. Apply the shared transport to the three call sites while preserving their existing expected render conditions.
- [ ] Run `python3 -m pytest workbook/tests/test_browser_runtime.py workbook/tests/test_video_layout.py workbook/tests/test_solution_pagination.py -q` and `python3 -m pytest .claude/skills/ec2-concept-check/tests/test_browser_transport.py -q`. Expect passing real render/transport cases.
- [ ] Commit the task files with `fix(review): share browser transport and verify real PDF rendering`.

### Task 2. 후보 경로와 승인 overlay 입력

**Files** — Create `workbook/pack_paths.py`, `workbook/tests/test_candidate_overlay.py`. Modify `workbook/{answer_overlay,build_workbook}.py`, `.claude/skills/ec2-review-pack/scripts/{assemble,check_html,html2md,pack_actions}.py`, `.claude/skills/ec2-problem-explain/scripts/{epe_source,epe_cli,epe_publish}.py`. Test also `workbook/tests/test_answer_overlay.py` and `.claude/skills/ec2-review-pack/tests/test_deferred_conversion.py`.

**Interfaces** — `PackPaths(repo: Path, public_pack: Path, candidate_pack: Path | None = None)` in `workbook/pack_paths.py`; `work_pack: Path`, `source_file(logical_repo_path: str) -> Path`, `work_file(relative: str) -> Path`. `load_source(path: Path, repo: Path, *, pack_paths: PackPaths | None = None, slug: str | None = None) -> SourcePack`; `load_answer_overlay(path: Path, repo: Path, expected_ids: list[str], *, pack_paths: PackPaths | None = None) -> dict`; workbook CLI `--candidate-pack PATH` and `--public-pack PATH` are paired. `stage_problem_index(paths: PackPaths, manifest: dict, selection: Path, titles: Path) -> dict[str, Path]` in `assemble.py` writes `problems.txt`, `selection.json`, `display-titles.json` and `selection-review.json` to a candidate. `build_explanation_candidate` in `epe_publish.py` takes the same `pack`, `artifacts`, `fragments`, `reviews`, `destination`, `repo` arguments as existing `publish_explanation` minus `backup_dir`, and returns the verified candidate file list as `list[Path]`.

- [ ] Add `test_candidate_overlay_matches_public_contract`, `test_changed_candidate_reference_is_rejected` and `test_problem_index_exists_without_note`. Use a reviewed-proof fixture and a candidate outside repo. Assert:

  ```python
  assert candidate_core == public_core
  assert not public_pack.exists()
  assert index['problems.txt'].is_file()
  assert not list(candidate_pack.glob('정리노트_*.html'))
  with pytest.raises(AnswerOverlayError, match='hash|변경'):
      load_answer_overlay(overlay, repo, ids, pack_paths=paths_after_tamper)
  ```

- [ ] Run `python3 -m pytest workbook/tests/test_candidate_overlay.py -q`. Expect rejection of candidate outside repo or missing candidate inputs on baseline.
- [ ] Implement `PackPaths` and wire the explicit map into source, overlay, link and workbook lookup. Map logical paths under the exact public pack prefix to the candidate root, and resolve source paths elsewhere only from repo. Validate resolved containment and reject traversal, symlink escape and NFC-colliding paths. A missing candidate file under that prefix fails proof and never falls back to a stale public file. Keep emitted paths and HTML links in public layout. Preview resolution maps them to the candidate when testing.
- [ ] Split the problem index from section assembly. Use the accepted manifest slug for early problem extraction instead of discovering it by scanning assembled HTML. Reuse explanation stage validation for both candidate materialization and legacy publication, and run answer builds against the candidate overlay. Keep legacy default call paths. Compose each consumer's pack view from adopted immutable output files under its attempt root, with one producer per logical output. Assemble/convert/final-check pass that view explicitly. Continue deferring only the exact answer link during preliminary validation and resolve all actual assembled files and PDF links at final-check.
- [ ] Run `python3 -m pytest workbook/tests/test_candidate_overlay.py workbook/tests/test_answer_overlay.py -q`, `python3 -m pytest .claude/skills/ec2-problem-explain/tests -q` and `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_assemble.py .claude/skills/ec2-review-pack/tests/test_deferred_conversion.py -q`. Expect verified candidates and preserved legacy behavior.
- [ ] Commit the task files with `refactor(review): build validated pack candidates outside public folders`.

### Task 3. 날짜 단위 발행과 중단 복구

**Files** — Create `.claude/skills/ec2-review-pack/scripts/pack_publication.py`, `.claude/skills/ec2-review-pack/tests/test_pack_publication.py`. Modify `.claude/skills/ec2-review-pack/scripts/{pack_files,pack_actions}.py`, `.claude/skills/ec2-concept-check/scripts/concept.py`, `.claude/skills/ec2-problem-explain/scripts/epe_files.py`.

**Interfaces** — `publication_lock(public_pack: Path) -> ContextManager[None]`; `publish_pack(paths: PackPaths, run: Path, *, expected: dict[str, str], candidate_inventory: dict[str, str], verify: Callable[[Path], None]) -> dict`; `reconcile_publication(paths: PackPaths, journal: Path, *, verify: Callable[[Path], None]) -> dict`. Parent publication record has `status`, `before`, `after`, and `journal`. Candidate validation is repeated inside the lock before copying. All overlapping publishers use the same date lock without nesting it.

- [ ] Add `test_publish_rejects_changed_baseline`, `test_same_date_publishers_serialize`, `test_reconcile_after_replace_before_checkpoint`, `test_reconcile_preserves_unexpected_bytes`, and `test_zero_problem_replacement_retains_unowned_files`. Use two processes for the same-date case and inject failure immediately after replacing the first owned file, before checkpointing. Assert:

  ```python
  assert conflict['error_code'] == 'publication_conflict'
  assert second_publisher_replacements_while_first_holds_lock == 0
  assert external_file.read_bytes() == user_bytes
  assert recovered['status'] == 'restored'
  assert inventory_pack(repo, range_) == before
  assert not stale_owned_answer.exists()
  assert unowned_file.read_bytes() == original_unowned
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_publication.py -q`. Expect missing shared publication entry and journal recovery on baseline.
- [ ] Implement the range lock and a durable publication journal. Under lock, compare the current owned inventory to the expected baseline. Capture verified backups and the exact before/after file sets before the first public write; stage each replacement on the publication filesystem. Record intent before each mutation, check per-path hashes, and record completion after verification. Reconcile against journaled before/after states and owned operation order. Complete a fully verified publication; restore an interrupted known partial publication; return `recovery_required` for any unexplained bytes. Retain non-owned files and avoid claiming simultaneous visibility for multiple file replacements.
- [ ] Wire parent final validation under the lock and share the lock with legacy review-pack live actions, standalone explanation and standalone concept publication. Derive the lock key from the canonical NFC-normalized public pack path and reuse the repository's OS file-lock approach. Lock order is RUN action lock, then publication lock, then short RUN state update. Keep all judgment calls and worker runs outside the publication lock. Final success requires strict HTML, MD, links, current overlay/PDF proof and inventory on the actual public paths.
- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_publication.py .claude/skills/ec2-review-pack/tests/test_pack_files.py .claude/skills/ec2-review-pack/tests/test_pack_actions.py -q`. Also run the relevant publish suites via `python3 -m pytest .claude/skills/ec2-problem-explain/tests -q` and `python3 -m pytest .claude/skills/ec2-concept-check/tests -q`. Expect crash recovery, concurrent conflict rejection and legacy regression coverage.
- [ ] Commit the task files with `feat(review): publish pack candidates with recoverable date-scoped writes`.

### Task 4. 작업 의존성 그래프와 RUN 선택

**Files** — Create `.claude/skills/ec2-review-pack/scripts/pack_graph.py`, `.claude/skills/ec2-review-pack/tests/test_pack_graph.py`. Modify `.claude/skills/ec2-review-pack/scripts/{pack_flow,pack_cli,pack_actions}.py`, `.claude/skills/ec2-review-pack/tests/pack_support.py`.

**Interfaces** — `TaskSpec(id: str, kind: Literal['worker','action'], direct_inputs: tuple[str, ...], required_approvals: tuple[str, ...], outputs: tuple[str, ...])`; `task_specs(state: dict) -> tuple[TaskSpec, ...]`; `ready_work(state: dict, *, slots: int) -> dict` returns `actions`, `dispatch`, `blocked`, `waiting` as lists of task IDs or task/reason pairs, plus `revision`. `init_run(..., workflow: Literal['legacy','parallel'] = 'legacy')` stores `workflow`; absent means legacy. Legacy `next` shape stays supported for legacy RUNs. Each candidate-side machine action runs in its own attempt root and holds only its task lock during work.

| 작업 ID | 착수 조건 | 채택하는 결과 |
|---|---|---|
| `render-preflight`, `source-prep`, `candidate-index` | 독립적으로 RUN 초기화 직후 | 렌더 사전 검사 기록, 원문 지도, workbook 후보·사용 이력 |
| `selection`, `author-<section>` | 선발은 범위와 후보 색인, 링크 없이 가능한 섹션은 고정 범위·토픽 브리프 | 확정 선발과 표시 순서, 섹션 조각 |
| `stage-problem-index`, `explain-author`, `explain-blind`, `build-problems` | index는 확정 선발, 작성·독립 풀이는 index와 문제 원문·그림, PDF 빌드는 index와 사전 검사 | 후보 목록, 원고, 가린 입력의 독립 풀이, 문제지 PDF |
| `assemble-note`, `style-audit`, `content-review`, `precheck` | 조립은 섹션과 확정 링크, 두 리뷰는 같은 조립본, 예비 검사는 현재 합류 감사 기록 | HTML·리뷰·예비 검사 기록 |
| `browser-qa`, `convert-md`, `standalone-svg-qa` | 앞 두 작업은 같은 고정 HTML과 문제지 후보(문제가 있을 때), SVG 검토는 실제 변환 목록 | 브라우저 승인, MD와 SVG, SVG 승인. 실제 0개이면 변환 증거로 SVG 검토 생략 |
| `explain-verify`, `build-answers`, `pdf-qa` | 설명 검토는 원고·블라인드 풀이와 필요한 원문·렌더, 답안 빌드는 설명의 승인 overlay와 사전 검사 | 필수 설명 승인 묶음, 답안 PDF, 페이지별 승인 |
| `publish-pack`, `final-check`, `concept-draft`, `concept-publish` | 부모 발행과 공개본 최종 검사는 하나의 잠금 구간에서 완료. 확인문제 준비는 검토된 HTML·MD와 선발, 발행은 현재 부모 최종 검사와 확인문제 자체 승인 | 최종 발행 증거와 현재 부모 회차에 결속된 확인문제 결과 |

- [ ] Add `test_source_and_render_preflight_are_independent`, `test_selection_unlocks_pdf_and_blind_before_note_qa`, `test_fixed_html_unlocks_browser_and_svg_conversion`, `test_zero_problems_omits_every_workbook_action` and `test_existing_state_uses_legacy_scheduler`. Seed tasks by accepted output/approval and assert:

  ```python
  assert 'render-preflight' in initial['actions'] and 'source-prep' in initial['dispatch']
  assert 'build-problems' in selected['actions'] and 'explain-blind' in selected['dispatch']
  assert 'browser-qa' in assembled['dispatch'] and 'convert-md' in assembled['actions']
  assert {'build-problems', 'build-answers', 'explain-blind'}.isdisjoint(zero_problem_graph_ids)
  assert legacy_next['kind'] == 'dispatch'
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_graph.py -q`. Expect the old first-incomplete stage to hide at least one independent task.
- [ ] Implement `task_specs` and `ready_work` for `parallel`. Register the table's machine IDs in the CLI and action dispatcher as they are enabled, so each ready action can run by ID. Use Task 1 preflight and Task 2 candidate outputs. Materialize task IDs only after the input that defines them is accepted. Split `scope-draft` into stable scope/topic identities and later final problem-link assembly. Allow authoring of sections whose brief is final except for those links. Define distinct `explain-author` and `explain-blind` tasks on the selected inputs; join at explanation verification. Keep the correct note and SVG approvals on the final paths, independently of their earlier builds. Defer the `concept-draft` feature to Task 7 and the merged review barrier to Task 5.
- [ ] Preserve lock/revision checks for claim, result adoption and publication. Capture the initial public inventory under the short date lock at parallel RUN start and use it as Task 3's expected baseline. Order ready tasks deterministically by downstream work unlocked, then task ID, with machine actions counted separately from agent slots. Use explicit ownership and attempt roots for concurrently writable files. Maintain legacy schema semantics including seed/resume and `next` for mid-flight records. Keep the trial workflow behind explicit selection until Task 9's acceptance.
- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_graph.py .claude/skills/ec2-review-pack/tests/test_pack_cli.py .claude/skills/ec2-review-pack/tests/test_pack_flow.py .claude/skills/ec2-review-pack/tests/test_pack_seed.py -q`.
- [ ] Commit the task files with `feat(review): schedule pack work from explicit dependencies`.

### Task 5. 병렬 내용 검토와 동일 RUN 수정

**Files** — Create `.claude/skills/ec2-review-pack/scripts/pack_findings.py`. Modify `.claude/skills/ec2-review-pack/scripts/{pack_graph,pack_flow,pack_receipts}.py`, `.claude/skills/ec2-review-pack/tests/test_pack_findings.py`, `.claude/skills/ec2-review-pack/references/{review-prompt,runner-contract}.md`.

**Interfaces** — `record_findings(state: dict, *, review_id: str, input_digest: str, findings: list[dict]) -> dict`; `fixable_findings(state: dict, *, candidate_digest: str) -> list[dict]`; `record_fix_result(state: dict, *, finding_id: str, request_id: str, attempt: str, outcome: Literal['resolved','unresolved']) -> dict`. Finding key is `review kind + rule + stable target + specific defect`; record includes `severity`, `owner_task`, `evidence`, `status` and unsuccessful repair attempt IDs. Independent `style-audit` and `content-review` approvals feed a join that records `active_audit` only for the current corrected candidate.

- [ ] Add `test_two_review_findings_are_batched`, `test_late_new_finding_accepts_fix_in_same_run`, and `test_two_failed_repairs_block_only_same_finding`. Assert:

  ```python
  assert first_review_only == []
  assert {row['id'] for row in both} == {widget_id, circuit_id}
  assert result['run_id'] == original_run_id
  assert findings[late_id]['status'] == 'open'
  assert findings[repeat_id]['status'] == 'withheld'
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_findings.py -q`. Expect the current serial review or shared repair budget to block these new assertions.
- [ ] Implement both independent reviews on the same HTML digest with distinct output ownership. The structural precheck can run with them; the existing precheck requiring an audit runs after their join. Separate each reviewer's report from the final joined audit. Conflicting judgments remain open until reconciled with the source, and provisional old-review outcomes never resolve a new candidate.
- [ ] Replace v2 shared content and machine/browser repair counters with per-finding repair state. Count only distinct accepted attempts that leave the same finding unresolved. Duplicate requests and unfinished/interrupted attempts do not consume a repair. After two unsuccessful corrections of one finding, withhold its dependent publication and report the evidence. A new finding uses the same RUN. Preserve existing legacy authorization and `waived` semantics for legacy runs; v2 cannot silently waive a blocking finding.
- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_findings.py .claude/skills/ec2-review-pack/tests/test_pack_authorization.py .claude/skills/ec2-review-pack/tests/test_learning_style_flow.py -q`.
- [ ] Commit the task files with `feat(review): consolidate independent review findings before repair`.

### Task 6. 대상별 승인과 작은 브리프

**Files** — Create `.claude/skills/ec2-review-pack/scripts/pack_approvals.py`, `.claude/skills/ec2-review-pack/tests/test_pack_approvals.py`. Modify `.claude/skills/ec2-review-pack/scripts/{pack_receipts,pack_flow,pack_actions}.py`, `.claude/skills/ec2-problem-explain/scripts/epe_contract.py`, `.claude/skills/ec2-review-pack/references/worker-prompt.md`.

**Interfaces** — `approval_key(kind: str, target: str, *, input_hashes: dict[str, str], policy_version: str) -> str`; `select_approval(ledger: list[dict], *, key: str, run_root: Path) -> dict | None`; `collect_current_reviews(required: dict[str, str], ledger: list[dict], *, run_root: Path) -> dict`; `build_receipt(state: dict, task_id: str, attempt: str, submission: Path) -> dict` validates worker decisions and writes machine-owned file records. Worker submission fields `status`, `report`, `outputs`, `reviews`, `counts`, `unresolved`; identity and actual hashes come from the claimed attempt. Keep independent physical proof for each review kind, with `render_fingerprint` in visual inputs.

- [ ] Add `test_review_key_survives_order_only_change`, `test_pdf_label_edit_reuses_only_equal_pages`, `test_shared_font_invalidates_visual_approvals`, `test_missing_png_reopens_only_own_approval`, and `test_pdf_brief_contains_only_direct_inputs`. Use a two-page PDF and real fixture renders for the visual test. Assert:

  ```python
  assert blind_key_old_order == blind_key_new_order
  assert changed_pdf_pages == [1] and reusable_pdf_pages == [2]
  assert reusable_after_shared_font_change == []
  assert stale_after_missing_png == {'note-visual:feedback:mobile-dark'}
  assert parent_note_screenshot not in pdf_brief['input_paths']
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_approvals.py -q`. Expect absent approval API or broad invalidation on baseline.
- [ ] Implement deterministic approval keys. Independent work uses workbook ID + subpart and condition/question/figure/required-profile digests; the current explanation-to-solution comparison remains separate. PDF visual approvals bind ordered page identity, page count, candidate rendered page image, corresponding approved explanation slice, renderer/platform/font and policy. Compare complete regenerated page inventories before any page reuse. Note/SVG approvals bind target, directly referenced material and relevant shared styles/scripts/fonts and renderer; use whole affected review when dependencies are uncertain. Validate evidence on reuse and aggregate all required current judgments before the existing explanation/overlay validation.
- [ ] Switch v2 briefs to direct role inputs and compute the evidence manifest and receipt fields inside the runner. Use file hashes at claim, adoption and publication boundaries, and local deduplication where the same file is hashed twice in one operation. Preserve all original evidence and record why an approval was invalidated or reused. Add print-space glyph/geometry overlap reporting for circuit label candidates in the PDF review step, with human adjudication rather than automated approval.
- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_approvals.py .claude/skills/ec2-review-pack/tests/test_pack_receipts.py .claude/skills/ec2-review-pack/tests/test_pack_standalone_svg.py -q` and `python3 -m pytest .claude/skills/ec2-problem-explain/tests -q`.
- [ ] Commit the task files with `feat(review): bind reusable approvals to reviewed targets`.

### Task 7. 확인문제 조기 준비와 발행 결속

**Files** — Modify `.claude/skills/ec2-concept-check/scripts/{source,concept,blind}.py`, `.claude/skills/ec2-review-pack/scripts/{pack_graph,pack_flow,pack_publication}.py`, `.claude/skills/ec2-concept-check/SKILL.md`. Create `.claude/skills/ec2-concept-check/tests/test_candidate_parent.py`.

**Interfaces** — `describe_inputs(repo, range_, parent_run=None, *, candidate_pack: Path | None = None) -> dict`; `prepare(run, repo, range_, parent_run, *, candidate_pack: Path | None = None) -> Path`; `bind_parent_for_publish(run: Path, parent_run: Path) -> dict` returns `parent_run`, `parent_attempt`, and current logical input hashes after matching candidate and public input identity. CLI `prepare ... --parent-run RUN --candidate-pack PATH` enables the early path only for parallel parent runs. Existing standalone and legacy parent behavior remains valid.

- [ ] Add `test_prepare_before_parent_final_then_publish_after`, `test_parent_note_change_refuses_early_quiz`, and `test_old_quiz_not_visible_after_changed_parent`. Assert:

  ```python
  assert draft_source.is_file() and not public_quiz.exists()
  assert initial_publish_error == 'parent_final_check_required'
  assert final_receipt['attempt'] == current_final_attempt
  assert changed_source_error == 'quiz_input_changed'
  assert not obsolete_public_quiz.exists() and archived_quiz.is_file()
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-concept-check/tests/test_candidate_parent.py -q`. Expect old `prepare` to reject a parent without final-check.
- [ ] Implement early `prepare/load` over an accepted immutable note HTML/MD and selection snapshot. Use logical input identity across candidate and public paths; STT, manifest, summaries and any read resources remain pinned. Author, independently solve and browser-review the candidate normally. Upon binding under the date lock, recheck the parent final attempt, the input hashes and all blind/browser evidence. Mismatches block publication and schedule only affected work. Keep the existing item-specific blind workflow.
- [ ] Include old quiz HTML and its evidence in the parent publication inventory. When replacing a parent, retain an old quiz only if evidence proves it is current for the new input and is validly bound; otherwise archive it as part of the journaled parent publication. When a new quiz is withheld, report its reason and keep the parent complete. Allow standalone `concept.py` to reuse the shared lock without holding it during review.
- [ ] Run `python3 -m pytest .claude/skills/ec2-concept-check/tests -q` and `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_graph.py .claude/skills/ec2-review-pack/tests/test_pack_publication.py -q`.
- [ ] Commit the task files with `feat(review): prepare concept quizzes while the parent pack finishes`.

### Task 8. 일괄 인계, 중단 복구, 시간 기록

**Files** — Modify `.claude/skills/ec2-review-pack/scripts/{pack_cli,pack_flow,pack_actions}.py`, `.claude/skills/ec2-review-pack/references/{runner-contract,delegation,worker-prompt,execution-guide,problem-explain-integration}.md`, `.claude/skills/ec2-review-pack/SKILL.md`, `.claude/skills/ec2-problem-explain/SKILL.md`. Create `.claude/skills/ec2-review-pack/tests/test_pack_dispatch_resume.py`.

**Interfaces** — `accept_batch(run: Path, submissions: list[dict]) -> dict` consumes `task_id`, `attempt`, `receipt` for each entry and returns per-item `accepted`, `already_accepted`, or `rejected` plus next status. `advance_actions(run: Path, *, max_actions: int) -> dict` stops at human work, a blocker, no ready actions or the count bound. `resume_run(run: Path, *, stopped_attempts: dict[str, str]) -> dict` consumes `attempt_id -> stop evidence path`; completed attempts can be adopted from verified journals/artifacts. Expose `task accept-batch --submissions PATH`, `advance --max-actions N`, `resume --stopped-attempts PATH`. `report --run` remains the report entry.

- [ ] Add `test_late_receipt_cannot_replace_new_attempt`, `test_batch_duplicate_is_idempotent`, `test_resume_reuses_completed_child_and_marks_gap`, and `test_advance_stops_at_review_gate`. Use test timestamps with 100 minutes between confirmed interruption and resume. Assert:

  ```python
  assert late['error_code'] == 'inactive_attempt'
  assert new_output.read_bytes() == successor_bytes
  assert replay['items'][0]['status'] == 'already_accepted'
  assert resumed['reused'] == ['explain-blind']
  assert metrics['confirmed_host_gap_seconds'] == 6000
  assert advanced['waiting_for'] == ['pdf-qa']
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_dispatch_resume.py -q`. Expect independent submit and resume commands to be missing on baseline.
- [ ] Implement batch acceptance in a short revisioned transaction, with per-item duplicate and stale-result checks. Move expensive work outside the state lock, then revalidate identity and input digest at adoption. Drive machine actions while prerequisites permit and stop at verified review gates. Resume completed immutable outputs and reconcile stopped machine attempts; release worker attempts only with confirmed stop. V2 worker output ownership is attempt-scoped, and a late result cannot mutate the adopted snapshot. Keep single-item diagnosis commands and legacy behavior.
- [ ] Persist UTC event times for `ready`, `claimed`, `completed`, `accepted`, `invalidated`, `reused`, `interrupted`, and `resumed`. Report per-task ready-to-claim and claim-to-complete, known host gaps separately, overlapping intervals explicitly, CLI counts and brief bytes. Record model usage and host-side tool counts only when supplied. Report the exact blocker ID and avoid inferring absent usage or downtime from filesystem timestamps. Update the skill runbook with batching, slot allocation, selective evidence inspection, and state-change-only progress updates.
- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_pack_dispatch_resume.py .claude/skills/ec2-review-pack/tests/test_pack_cli.py .claude/skills/ec2-review-pack/tests/test_pack_actions.py .claude/skills/ec2-review-pack/tests/test_skill_files.py -q`.
- [ ] Commit the task files with `feat(review): batch dispatch handoffs and resume verified work`.

### Task 9. 통합 재현과 기본값 전환

**Files** — Create `.claude/skills/ec2-review-pack/tests/test_parallel_pack_integration.py`. Modify `.claude/skills/ec2-review-pack/scripts/{pack_cli,pack_flow}.py` and `.claude/skills/ec2-review-pack/{SKILL.md,references/runner-contract.md}` when switching the default. Preserve real verification reports in the relevant RUNs.

**Interfaces** — Use the existing `init`, `next`, `report` plus Task 8 commands. `init --workflow parallel` is the explicit trial entry; `init --workflow legacy` remains the fallback for new runs. A release record points to verified 1118 and next-course RUN reports and records the source commits, runtime environment, pre-existing test failures and actual review coverage.

- [ ] Add `test_parallel_full_pack_accepts_only_current_evidence`, `test_zero_problem_pack_still_offers_quiz`, `test_zero_svgs_never_skips_required_html_review`, and `test_regeneration_keeps_public_pack_until_verified_publish` to the integration fixture. Cover moves between producer and consumer and disallow stale approval. Assert:

  ```python
  assert unrelated_approval_id in final_report['reused_approvals']
  assert invalidated_approval_id not in final_report['current_approvals']
  assert candidate_only_public_delta == {}
  assert zero_problem_next_accepts_quiz
  assert 'browser-qa' in zero_svg_review_ids and 'standalone-svg-qa' not in zero_svg_review_ids
  assert stale_candidate_publication_error == 'stale_inputs'
  ```

- [ ] Run `python3 -m pytest .claude/skills/ec2-review-pack/tests/test_parallel_pack_integration.py -q`. Expect the unpinned integration path, if any, to surface before rollout. Correct the owning task and rerun its regression tests together with the integration test.
- [ ] Run component suites separately with `python3 -m pytest .claude/skills/ec2-review-pack/tests -q`, `python3 -m pytest .claude/skills/ec2-problem-explain/tests -q`, `python3 -m pytest .claude/skills/ec2-concept-check/tests -q`, and `python3 -m pytest workbook/tests -q`. Use a short OS temp root for Chromium and compare any existing failures on the same host and dependency versions, before classifying them as pre-existing.
- [ ] Commit the task files with `test(review): verify parallel pack integration and recovery`.
- [ ] Recreate 1118 in an isolated checkout and RUN with the actual 1118 STT, lesson materials, workbook, and profile; record their digests and the choice of original or current selection rules. If matching historical timing or problem IDs requires the original input snapshot, report dataset differences and compare only compatible measurements. Complete actual independent and visual reviews. In isolated repeat runs, reproduce late content finding, one-page label correction, common font change, and worker interruption after an accepted independent proof. Verify graph order, final evidence, unchanged-page reuse, wider font invalidation and continued same-RUN review. Include final-link and 16:9/180px checks and note any host gap separately.
- [ ] Run the next actual lecture using explicit `--workflow parallel`. Capture true review coverage, `ready/claimed/completed/accepted` times, invalidated and reused targets, brief sizes, and CLI count. Confirm the two runs satisfy the [design contract](#design-contract). If installation or real review blocks either run, document the blocker and retain the trial default. Use the new workflow's observed counts and timestamps, with the old 1118 run as historical context rather than a controlled A/B run.
- [ ] After both real runs pass, add `test_new_init_defaults_to_parallel_after_rollout` in the integration test, assert `new['workflow'] == 'parallel'`, `old_without_workflow == 'legacy'`, and `explicit_legacy['workflow'] == 'legacy'`. Run it and observe the old trial default fail. Change the new `init` default and docs, rerun integration, CLI and legacy seed suites, then commit `feat(review): default new packs to the verified parallel workflow`.

## Final Verification Checklist

- [ ] `git diff --check` and the four component suites checked with fresh output. Record baseline-only failures by test node and host.
- [ ] Review of all parallel edge conditions covers zero problems, no exported SVG, changed selection and slug, existing pack regeneration, private source/proof path changes, and partial publication failure.
- [ ] Full runs produce public HTML/MD, current figures, expected problem/answer PDFs, explanation and quiz or explicit quiz withholding, with actual review evidence and no loose stale links.
- [ ] 1118 and the next real course session report distinguish actual concurrency, rework, host interruption, and replay cost. Record both RUN references in the default-switch commit or its review record.
