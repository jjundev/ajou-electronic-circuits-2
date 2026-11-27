# ec2-review-pack 테스트 단축 2차 — 퀴즈 브라우저 대체 + xdist

## Intent
`.claude/skills/ec2-review-pack/tests` 전체 실행(현재 직렬 15m19s, 717 passed / 5 skipped / 357 subtests)을 검증 범위를 줄이지 않고 더 줄인다. 퀴즈 시나리오가 `concept.py browser`마다 띄우는 진짜 Chromium(회당 15.6–17.4s)을 대표 1개 테스트만 남기고 대체 보고서로 바꾸고, 그 테스트에서 대체 보고서가 진짜와 같은 형태인지 비교한다. 그다음 pytest-xdist로 병렬 실행한다. 완료 기준: 결과 수 유지(새 테스트만 추가), 직렬 약 12분대, 병렬 실행 3회 연속 통과.
Classification: bounded — 테스트 helper(`cli_runner`)와 퀴즈 시나리오 helper만 바꾸며 제품 코드는 그대로다.

## 측정 근거
- `test_quiz_adoption_rejects_rewritten_existing_sibling_packet`: 72s 중 `concept.py browser` 3회가 52.2s.
- `test_quiz_crash_reuses_only_matching_public_receipt_marker_and_blind_proof`: 53s 중 browser 1회 15.6s.
- `test_zero_problem_cli_publishes_only_after_actual_converter_and_review_receipts` 6개 param 중 browser까지 가는 것은 `None` 하나(15.7s).
- 다른 concept 명령은 회당 약 0.5s.
- 이 브라우저 호출은 공유 시나리오 `exercise_zero_problem_cli`(test_pack_graph.py)의 `review_quiz`/`exercise_sibling_repair`에서 나오고, test_pack_graph와 test_pack_dispatch_resume의 7개 테스트가 이 시나리오를 쓴다.

## Behavior when done
- `python -m pytest .claude/skills/ec2-review-pack/tests -n 8 --dist worksteal`로 병렬 실행한다(opt-in). 직렬 실행도 그대로 된다.
- 퀴즈 시나리오 대부분은 대체 브라우저 보고서를 쓴다. 이 보고서는 evidence/publish의 실제 검사를 통과해야 한다:
  - 4모드 확인(`checked_browser`)
  - HTML sha256 일치
  - 문항 수와 힌트 수 일치
  - 스크린샷 해시 일치
  - PNG 형식과 크기 확인
- `EC2_TEST_BROWSER=real`이면 모든 퀴즈 브라우저 호출이 진짜 Chromium이다. `EC2_TEST_CLI=subprocess`와 함께 쓰면 완전 재현 모드다.
- 대체 보고서와 진짜 `browser_check` 보고서의 형태가 달라지면 `zero_problem[None]`이 실패한다.

## Not in this round
- **concept CLI의 다른 명령을 in-process로 돌리기:** 이득은 직렬 약 90s, 병렬로는 10초 안팎이다. 반면 이름 충돌(concept.py:17-24)과 `sys.path` 삽입(interaction.py:12), `publish`의 잠금 재획득(concept.py:299) 위험이 있다.
- **제품 쪽 `concept_command`(pack_parallel.py:1177)와 `verify-legacy`(pack_publication.py:181):** `browser`를 부르지 않고, 프로세스 경계가 계약의 일부다.
- **제품 action 프로세스(html2md, check_html, assemble):** pid와 `process.json` 기록을 검증하는 테스트가 의존한다.
- **layout_probe, pack_approvals, standalone-svg-qa의 진짜 Chromium:** 브라우저 동작 자체를 검증한다.

## Implementation spec
1. **`tests/quiz_browser_stub.py`:** `check(html, out, shots, *, source, viewports=VIEWPORTS, themes=THEMES)`는 `browser_check.check`와 시그니처가 같다.
   - 보고서 키: `html`, `sha256`, `viewports`, `themes`, `transport`(진짜와 같은 문자열), `runs`, `failures`, `status`, 표식 `stub`.
   - `runs` 각 항목: `label`, `detail{items_checked, items, hints_checked}`(모두 문항 수), `failures:[]`, `external_blocked:[]`.
   - `concept.shot_names(source)`의 각 이름으로 viewport 크기의 진짜 PNG를 쓴다. 이름마다 바이트가 달라야 한다.
2. **`tests/cli_runner.py`:** `run_concept(cli, *args, real_browser=False)`.
   - `args[0] == 'browser'`이고 real이 아닐 때만 `-c` 래퍼로 실행한다. 래퍼는 `browser_check.check`를 stub으로 바꾸고 `concept.main`을 부른다.
   - 그 밖에는 `python <cli> ...`를 그대로 실행한다.
3. **`tests/test_pack_graph.py`:**
   - 시나리오의 concept 호출을 `run_concept`로 바꾼다.
   - `exercise_zero_problem_cli(..., real_browser=False)`를 추가하고, `zero_problem` 테스트는 `real_browser=(scope_change is None)`를 넘긴다.
   - 진짜 browser 직후에 parity 단언을 둔다.
4. **`tests/test_cli_runner.py`:** argv 선택 2개, stub 보고서의 concept 게이트 통과 1개를 추가한다.
5. **xdist:** `--dist worksteal`. 4/8/12 워커를 측정해 N을 정하고, 3회 연속 통과시킨 뒤 완전 재현 모드로 1회 돌린다. 명령은 `tests/README.md`에 적는다.
6. **fault injection:** stub `status:'fail'`이나 틀린 PNG 크기가 시나리오 테스트를 실패시키는지 확인하고 되돌린다.

## Decisions
### Confident
| # | Decision | Answer | Rationale |
|---|---|---|---|
| 1 | 순서 | 브라우저 대체 → xdist | 병렬 실행 시간은 가장 긴 테스트보다 짧아질 수 없다. 72s 중 52s가 브라우저다. |
| 2 | 넣는 방식 | `browser` 명령만 `-c` 래퍼 | 프로세스 경계를 유지한다. 같은 선례가 test_pack_graph.py:511에 있다. |
| 3 | stub 출력 | 진짜 PNG, 같은 키와 개수, sha 일치 | concept.py:194-201, :261-282의 검사를 통과해야 한다. |
| 4 | 형태 어긋남 방지 | 진짜 browser 테스트 안에서 parity 단언 | `browser_check`가 바뀌면 바로 잡힌다. |
| 5 | 완전 재현 스위치 | `EC2_TEST_BROWSER=real` | `EC2_TEST_CLI=subprocess`와 같은 규칙이다. |
| 6 | 분배 방식 | `--dist worksteal` | 시간 차이가 크다. `loadfile`이면 test_pack_graph(224s)가 워커 하나에 묶인다. |
| 7 | 워커 간 충돌 | 없음 | date lock은 public 경로 해시를 키로 쓴다(pack_publication.py:52-56). cache root는 프로세스마다 따로다(_util.py:33-36). 렌더 origin은 소켓이 아니라 route 가로채기다(browser_runtime.py:12, :39-73). `EC2_CACHE_ROOT`를 미리 설정하지 않는다(pack_flow.py:52). |
| 8 | subtest 집계 | xdist에서도 정상 | 직렬과 `-n 2` 모두 277 subtests로 같았다. |
| 9 | 시간에 민감한 테스트 | 그대로 두고 3회 연속 실행으로 확인 | 0.3s 막힘 검사는 부하에서 거짓 실패하지 않는다. |
| 10 | 워커 수 | 측정, 가정값 8 | 물리 코어 8개, RAM 31GB. |

### Needs you
| # | Decision | Answer |
|---|---|---|
| 11 | xdist 기본 활성화 | opt-in 명령, `tests/README.md`에 기록 **[confirmed by default]** |
| 12 | 진짜 퀴즈 브라우저를 남길 테스트 | `zero_problem[None]` 하나 **[confirmed by default]** |
