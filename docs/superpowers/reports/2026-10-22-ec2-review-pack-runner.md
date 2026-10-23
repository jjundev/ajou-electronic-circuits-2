# 전자회로2 review-pack runner 구현·인수 보고

2026-10-22 실행, 2026-10-23 소스 최종 검토. runner 소스 구현과 독립 검토는 완료했으며, 실제 0909 normal-mode 인수는 **미완료**로 종료 기록한다. 최종 parent browser QA에서 BQA-03 Important 1건이 남았다. 수정 예산(content 1/1, machine/browser 2/2)을 모두 사용했으므로 추가 수정·예산 초기화·새 RUN·승인 우회 없이 실패와 미실시 단계를 보존했다.

- [x] Task 1: 상태·초기화·입력 동결
- [x] Task 2: 최초 백업·파일 준비·복구 API
- [x] Task 3: claim/bind/receipt 검증
- [x] Task 4: 의존성 스케줄·수정 예산
- [x] Task 5: 실제 subprocess gate·발행/복구 통합
- [x] Task 6: 짧은 JSON CLI
- [x] Task 7 소스·문서·회귀 검사와 인수 근거 기록
- [ ] Task 7 실제 전체 인수 성공

계획: [2026-10-22-ec2-review-pack-runner.md](../plans/2026-10-22-ec2-review-pack-runner.md). 브랜치 `codex/ec2-pack-runner`, 기준 `f3d9aafaa255efc515731f836913b991244b6bac`, 실제 인수 시점 소스 `4ee90bedc60fb11f65b08663e95a877a2e4143ac`. 단계별 소스 종료점은 Task1 `9a7f6a9`, Task2 `4d83d13`, Task3 `d8e84bd`, Task4 `ed12715`, Task5 `bc50a95`, Task6 `2d1df98`, Task7 `7bfa5a4`이다. 실사용 중 receipt 타입/coverage 설명만 `df69029`, `d67de20`에서 보완했고, 변환 후 standalone SVG의 실제 검토 담당이 빠진 문제를 `4ee90be`에서 runner·receipt·테스트·문서에 추가했다. 이 추가 gate는 독립 소스 리뷰를 통과했지만 실제 변환 후 QA는 아직 수행하지 않았다.

스킬 진입점은 짧은 runner 호출과 파일 인계 중심으로 바뀌었다. 기존 교육 내용·개인 풀이 명세·원문 대조·독립 검토·실제 브라우저/PDF·최종 검증은 유지한다. immutable producer/audit 버전, 정확한 입력 해시, current evidence, 최초 백업, 외부 변경 보존, main 전용 발행/복구를 적용했다. 합성 workflow 테스트는 실제 정상 인수 근거로 사용하지 않았다.

## 회귀 검증

최종 소스 `75c8470` parent 전체 회귀: **347 passed, 7 failed, 1 skipped, 241 subtests passed**, 513.53초, exit 1. 실패 이름 7개는 아래 최초 기준과 동일하다. 로그는 `final-pack.log`/`final-pack.exit`에 보존했다. 최종 수정은 child runtime/tests를 바꾸지 않았고 관련 실제 action/receipt 검증을 통과했으므로 child 전체 검사는 아래 마지막 실행 결과를 유지한다. 따라서 두 패키지 전체 green을 주장하지 않는다. 최종 독립 소스 재검토는 I1/I2 해결·새 지적 0건으로 승인됐다.

SVG gate 추가 시점 `4ee90be` 전체 parent 패키지: **338 passed, 7 failed, 1 skipped, 241 subtests passed**, 363.96초. child: **213 passed, 1 failed, 93 subtests passed**, 224.67초. 두 명령 모두 실패 종료이며 전체 green으로 표현하지 않는다. 최종 quick_validate는 `Skill is valid!`, diff check는 clean이었다. 로그는 보존된 worktree의 `.superpowers/sdd/2026-10-22-ec2-review-pack-runner/post-svg-pack.log`, `post-svg-child.log` 및 각 `.exit`에 있다.

최초 baseline parent는 8 failed / 201 passed / 1 skipped / 241 subtests였다. NFC/NFD 백업 실패 1건은 Task2에서 해결했다. 최종 남은 7건은 최초부터 있던 `test_publish_answer.py`의 다음 실패와 정확히 같다.

- `test_success_keeps_verified_backup`
- `test_missing_old_pdf_installs_and_records_receipt`
- `test_preparation_failure_preserves_old_pdf[backup]`
- `test_preparation_failure_preserves_old_pdf[receipt]`
- `test_preparation_failure_preserves_old_pdf[temp]`
- `test_all_required_writes_finish_before_replacement`
- `test_cli_publishes_with_real_loader`

원인은 기존 PyMuPDF deprecated fitz 경고가 stdout 앞에 붙는데 legacy 테스트가 전체 stdout을 JSON/path로 읽는 것이다. 원 publisher/tests를 바꾸어 숨기지 않았다. skip은 `test_assemble.py::test_template_preserves_shared_panel_contract`의 upstream ML template 부재이며 브라우저 능력 부족으로 건너뛴 검사는 아니다.

최초 child baseline도 1 failed / 213 passed / 93 subtests였다. 남은 실패는 `test_learning_style_flow.py::test_build_records_unapproved_style_audit_and_required_reference`이며 profile이 review.references에 있어야 한다는 기존 fixture 기대와 실제 `[]`가 다르다. child runtime은 변경하지 않았다. Task2 이후 누적된 `test_personalized_pipeline.py::test_parent_failure_restores_coherent_pack`의 removed-heredoc 추출 실패는 최초 baseline 실패로 재분류하지 않았다. Task7 승인 범위에서 실제 prepare/inventory/recover API 및 coherent-pack 바이트·답안 소비자·양쪽 백업 receipt 검증으로 이관했고, 실제 RED→focused GREEN→전체 child 재실행으로 해결했다. 최종 소스에서 추가 미해결 회귀는 없다.

## 실제 인수와 보존 상태

worktree: `C:/Users/Hyunjun/.codex/worktrees/ec2-pack-runner/ajou-electronic-circuits-2`.
RUN: `C:/Users/Hyunjun/.codex/worktrees/ec2-pack-runner/acceptance-0909-20261022-e4cwyv`.
상세 current gate·파일 SHA256·복구·측정 근거: RUN의 `runner-acceptance.md`, `run-status.json`, `report.json`, `controller-metrics.json`.

현재 phase 7 / needs_fix / partial=1, publication `{}`. prepare/assemble/build-problems/precheck는 실제 실행 완료했다. 원문·선정·저자 작업 후 독립 style/content 검토는 현재 12 topics × 12 rules = 144를 통과했다. 선정은 P9.12/P9.15/P9.56이며 미학습 하위 문항을 포함한 미사용 기출 27개를 통째로 보류했고 문항 수를 억지로 채우지 않았다. 선정 근거 5행 수정, 접점 dot, 모바일 작은 글자와 동일 노드 blue 수정은 실제 반영·재검토했다.

최종 browser attempt `fd9ff244-54c9-4612-85eb-f1ed9681afef`는 needs-fix로 정직하게 수락했다. 실제 48 topic/width/theme 조합, SVG 10개, 현행 문제 PDF 3/3 페이지를 확인했다. BQA-03은 375×812 light/dark에서 여섯 s0 스크롤 영역과 s1-current 그림에 focus 후 ArrowRight를 누르면 내부 그림 대신 다음 topic으로 이동하고 scrollLeft가 0에 남는 문제다. pointer pan은 가능하나 키보드로 숨은 필수 label에 접근하지 못해 Important로 판정했다. 과거 tiny-label/blue 문제가 해결되었다는 사실과 이 잔여 실패를 구분했다. 실패별 report·receipt·screens/측정은 RUN/work 아래에 그대로 보존한다.

남은 단계는 **MD conversion → standalone SVG QA → child independent 4-review workflow(독립 검산 포함) → answer PDF QA → publish → final-check**이다. parent browser gate도 미해결이다. 현재 문제 PDF 검토를 답안 PDF나 child 검토 승인으로 사용하지 않는다. 추가 수정 없이 이번 인수를 미완료로 마친다.

최초 basic 백업은 31 files/1 directory, explanation 백업은 133 files/11 directories 모두 읽기 전용 SHA256/디렉터리 확인에서 일치했다. 현행 recovery.last_inventory 34항목도 실제 파일과 일치했다. 복구 실행·rollback은 수행하지 않았다. 최초 backup/inventory와 후속 last inventory를 구분하며 첫 백업은 덮어쓰지 않았다. 0909 생성물은 소스와 별도로 uncommitted 상태로 남겨 두었고 원 primary checkout의 기존 dirty 1014 작업은 건드리지 않았다. worktree와 RUN을 보존하며 merge/push하지 않는다.

controller-metrics 기준 captured CLI 120개 최대 868자, 2000자 초과 0개이며 이전 accept 1개의 stdout은 unavailable이다. 역할 final 30개 최대 599자, 800자 초과 0개; browser helper 4개 637/509/623/537자, 800자 초과 0개다. 입력/cache telemetry는 unavailable이며 절감률·동일조건 A/B를 주장하지 않는다. 실제 acceptance에서 main이 original STT/PDF/full HTML/SVG/script/example 전문을 읽지 않았다는 범위와 진단 출력 규율은 구분한다. controller가 report.json을 직접 직렬화한 큰 진단 출력 1회, 문서 closeout worker가 중첩 receipt/파일 해시 목록을 출력한 큰 진단 출력 1회가 잘려 반환되었다. 후자는 metadata이며 원문 본문 반입은 아니지만 두 건 모두 context 규율 실수로 기록한다. CLI bounded JSON 성공이 전체 context 절감의 증명은 아니다.

## 구현 중 결정 원문

다음은 progress.md의 모든 `Ruling:` 행을 원문 그대로 보존한 것이다. 각 행에 선택 이유와 비용/위험이 들어 있다. scratch 정리 후에도 결정 근거를 검토할 수 있게 남긴다.

Ruling: Roles without an existing machine approval schema use explicit receipt status, empty unresolved on done, and current hashed genuine reports/required evidence/coverage; no prose pass parser or invented replacement legacy approval — browser/content existing contracts are evidence files, not JSON approvals — if insufficient coverage slips through, real QA could be overstated and must be corrected before publication. Child identity adapter must compare existing real review identities; nested runner reviewers map is not a new approval.

Ruling: Use immutable per-role producer versions for draft/selected manifests and audit supplementation; final scope emits RUN/manifest.json, actions stage the currently approved audit to legacy canonical path — strict current-file hashes otherwise make legitimate overwrites invalidate their own input and predecessor proofs — if compatibility is wrong, brief/action adapters need rework; frozen-input checks must not be weakened. Task4 consumes versioned outputs/active audit, Task5 stages audit and reruns precheck after supplementation.

Ruling: Extend Task4 narrowly into pack_receipts.py/tests for controller-frozen audit_output under role-owned audits/UUID/learning-style-audit-note.json, disjoint from inputs; correction/stale revisions use distinct paths, legacy fixed briefs still validate — immutable producer handoffs also need revision separation within a role — if wrong, receipt/brief compatibility needs rework; strict input/output hash checks remain unchanged. Approved no user pause.

Ruling: Add accepted selection-owned RUN/display-titles.json to receipt and scheduler contracts, validate exact selected IDs/nonempty strings and copy in prepare — existing execution-guide129 requires human-quality chosen titles but no accepted producer existed — if wrong, selector/renderer adapters need rework; runner must not invent titles. Narrow Task5 receipt/test edit approved.

Ruling: Allow main-only stopped-confirmation.json (schema1, attempt, confirmed_by,reason,exact process,inventory) to resolve interrupted process-tree uncertainty; runner never creates it — needs usable manual reconciliation without automatic orphan replay — wrong stop confirmation could race a live writer. Inventory in that marker is not a new trusted recovery baseline; only durable expected inventory or independently verified completion can authorize mutation, otherwise remain recovery_required and preserve external edits.

Ruling: Extend Task7 into child test_personalized_pipeline.py only to migrate removed-heredoc recovery test to actual pack_files APIs while preserving coherent-pack behavior assertions — full regression revealed Task2 missed this consumer, an accumulated new failure relative to initial baseline — if wrong, recovery coverage could weaken and must be repaired. Child runtime remains unchanged. Initial full child2fail212pass93subtests225.47s; baseline reference failure plus new extraction failure. Require focused GREEN and justified full child rerun after migration.

Ruling: Add mandatory browser-owner standalone-SVG QA AFTER actual MD conversion and BEFORE child/final, including zero-problem notes with SVGs — actual acceptance found existing PROFILE/execution-guide requires standalone font/MD checks but fixed graph had no owner after conversion — if wrong, adds extra queue or stale propagation/revalidation regressions; keep phase8 and original gates, no legacy runtime/template changes. Narrow runner+receipt+tests/docs extension authorized, no user pause. Current phase7 browser needs-fix accepted; sourceactormayfix mobile/blue separately in machine2 while one code implementer adds missing gate.


## 최종 소스 통합 수정 (I1/I2)

최종 전체 브랜치 검토의 Important 소스 발견 2건을 `75c8470` (`fix(review-pack): expose reconciliation and align PDF reports`)에서 수정했다. I1은 기존 reconcile_action을 재실행 없이 호출하는 `reconcile --run <RUN> --action <action>` CLI와 중단 후 next/wait 운영 절차를 추가했다. 기존 stop·입력·inventory·발행 검증과 action lock을 유지한다. I2는 PDF brief/receipt/기존 소비자의 실제 보고서를 `RUN/answer-review.md`로 통일하고 동일 보고서의 현재 evidence를 요구한다. dummy 허용 출력 사전생성 없이 실제 fixture PDF 전 페이지를 렌더해 문서에 지정된 산출만 제출하는 회귀를 추가했다.

TDD: corrected RED 8 failed / 45 deselected (55.65s), PDF report-binding RED 1 failed / 29 deselected (14.42s). 최종 covering focused CLI/flow/receipts/actions/standalone-SVG/skill-files 147 passed / 189 subtests passed (274.92s), 최종 보고서 연결 변경은 별도 PDF consumer/producer 검증 5 passed / 25 deselected (42.78s). 초기 fixture 폴더 누락과 슬롯 0에서 정상 wait를 금지한 테스트 기대값 오류는 보정했으며 원래 로그를 보존했다. quick_validate는 Skill is valid!, git diff --check는 exit 0/출력 없음이다. 기존 시스템 임시 재현 fixture도 지원 CLI exit 0/빈 stderr로 재검증했으며 실제 인수 승인이 아니다. 상세 RED/GREEN 명령·로그·한계는 `.superpowers/sdd/2026-10-22-ec2-review-pack-runner/final-fix-report.md`다.

실제 acceptance의 역사적 source는 `4ee90be` 그대로다. phase 7/needs_fix, BQA-03 Important 1건, content 1/1·machine/browser 2/2, publication empty 및 미수행 MD/SVG/자식/답안/최종 검사를 유지한다. A1 인수 제한을 완료로 바꾸지 않았다. 실제 RUN·생성물·수정 예산은 변경하지 않았다. `75c8470`에 대한 한 번의 독립 scoped 재검토에서 I1/I2 모두 ADDRESSED, 새 지적 0건으로 소스 수정이 승인됐다. 근거는 보존된 `final-fix-review.md`다. 최종 parent 전체 회귀는 347 통과·기존 실패 7건으로 끝났고 새 미해결 회귀는 없다. 계획과 이 보고서는 생성물과 분리한 문서 커밋으로 보존한다.

Ruling: Extend the enumerated CLI with a thin guarded reconciliation route for completed interrupted actions, reusing reconcile_action without replay or state edits — final review reproduced a fully provable completed action that neither documented run nor recover could resume, so the command table omitted a required recovery behavior — if wrong, CLI compatibility/documentation requires rework or unsafe adoption could occur; retain process-stop, exact hashes/inventory and all publication evidence guards. This source repair does not waive artifact repair budgets.
