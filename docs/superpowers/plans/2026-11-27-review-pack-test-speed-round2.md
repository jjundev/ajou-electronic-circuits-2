# ec2-review-pack 테스트 단축 2차 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 퀴즈 시나리오의 진짜 Chromium 호출을 대표 1개만 남기고 검사를 통과하는 대체 보고서로 바꾸고, 전체 suite를 pytest-xdist로 병렬 실행해 실행 시간을 줄인다.

**Architecture:** `concept.py browser`를 부를 때만 테스트 helper가 `-c` 래퍼로 `browser_check.check`를 stub으로 바꿔 실행한다. 나머지 concept 명령과 제품 코드는 그대로다. 진짜 브라우저를 쓰는 `zero_problem[None]`이 같은 quiz에 stub을 돌려 보고서 형태가 같은지 단언한다. xdist는 코드 변경 없이 opt-in 명령으로 쓰고, `tests/README.md`에 기록한다.

**Tech Stack:** Python 3.14, pytest 9.1.1, pytest-xdist 3.8.0, Pillow, Playwright 1.63 (Windows)

**Spec:** `docs/superpowers/specs/2026-11-27-review-pack-test-speed-round2-design.md`

## Global Constraints

- 테스트가 검증하는 계약(contract 필드, 채택 게이트, probe 판정, 레거시 RUN 호환)을 약하게 만들지 않는다. 빠르게 하려고 단언을 지우지 않는다.
- 제품 코드(`.claude/skills/*/scripts`, `workbook/`)는 수정하지 않는다.
- 커밋과 push는 사용자가 요청할 때만 한다. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`을 붙인다.
- 전체 실행은 30분 이상 걸릴 수 있으므로 항상 백그라운드(Terminal 패널 탭)에서 돌린다.
- 전체 실행 전에 `EC2_CACHE_ROOT`를 미리 설정하지 않는다. 워커마다 `_util.py`가 따로 만든다.
- 진짜 브라우저 스위치 이름은 `EC2_TEST_BROWSER=real`이다. CLI 스위치 `EC2_TEST_CLI=subprocess`는 그대로 둔다.
- concept 하위 프로세스 출력은 지금처럼 `text=True`(로캘 인코딩)로 읽는다. 자식의 cp949 한글 stderr를 그대로 디코딩하기 위해서다.
- 기준 결과 수는 717 passed / 5 skipped / 357 subtests다. 이 계획에서 새 테스트 4개를 더하므로 완료 후 721 passed / 5 skipped / 357 subtests가 되어야 한다.

## Review Focus

1. **힌트가 없는 문항:** 진짜 브라우저는 `hints_checked`가 문항 수보다 적게 나와 evidence에서 막힌다. stub도 막혀야 하며, 무조건 pass하면 안 된다. Task 1의 `test_stub_report_fails_when_an_item_has_no_hint`가 확인한다.
2. **`browser`가 첫 인자가 아닌 곳에 나올 때**(`--out browser` 같은 값): stub이 걸리면 안 된다. 판단은 `args[0]`만으로 한다. Task 1의 `test_run_concept_wraps_only_the_browser_command`가 확인한다.
3. **`browser_check` 보고서 형태가 바뀔 때**(키 추가, 스크린샷 이름 변경): stub이 따라가지 못하면 바로 실패해야 한다. Task 2의 parity 단언이 확인한다.
4. **stub이 실패 보고서를 낼 때:** 시나리오 테스트가 실패해야 한다. 게이트가 실제로 막는지 보는 것이다. Task 2의 fault injection 단계가 확인한다.
5. **병렬 부하:** Chromium 테스트와 0.3s/2s/5s 대기 테스트가 거짓 실패하지 않아야 한다. Task 3에서 3회 연속 통과로 확인한다.

---

### Task 1: 퀴즈 브라우저 stub과 `run_concept`

**Files:**
- Create: `.claude/skills/ec2-review-pack/tests/quiz_browser_stub.py`
- Modify: `.claude/skills/ec2-review-pack/tests/cli_runner.py` (`run_pack_cli` 아래에 추가하고, 모듈 docstring에 `EC2_TEST_BROWSER` 한 줄을 추가)
- Test: `.claude/skills/ec2-review-pack/tests/test_cli_runner.py`

**Interfaces:**
- Consumes:
  - `browser_check.VIEWPORTS`, `browser_check.THEMES`, `browser_check.sha256`, `concept.shot_names(data)`. 모두 `.claude/skills/ec2-concept-check/scripts`에 있다.
  - `cli_runner.Result`
- Produces:
  - `quiz_browser_stub.check(html, out, shots, *, source, viewports=VIEWPORTS, themes=THEMES) -> dict`
  - `cli_runner.run_concept(cli, *args, real_browser=False) -> Result`

- [ ] **Step 1: Write the failing tests** (`test_cli_runner.py` 끝에 추가)

```python
from pack_parallel import CONCEPT_CLI

def test_run_concept_wraps_only_the_browser_command(monkeypatch, tmp_path):
    seen = []
    monkeypatch.delenv('EC2_TEST_BROWSER', raising=False)
    monkeypatch.setattr(cli_runner.subprocess, 'run',
                        lambda argv, **k: seen.append(argv) or types.SimpleNamespace(returncode=0, stdout='', stderr=''))
    cli_runner.run_concept(CONCEPT_CLI, 'blind-make', '--out', 'browser', '--run', tmp_path)
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path)
    assert seen[0] == [sys.executable, str(CONCEPT_CLI), 'blind-make', '--out', 'browser', '--run', str(tmp_path)]
    assert seen[1][1] == '-c' and seen[1][2:4] == [str(CONCEPT_CLI.parent), str(cli_runner.TESTS)]
    assert seen[1][4:] == ['browser', '--run', str(tmp_path)]

def test_real_browser_runs_concept_unwrapped(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(cli_runner.subprocess, 'run',
                        lambda argv, **k: seen.append(argv) or types.SimpleNamespace(returncode=0, stdout='', stderr=''))
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path, real_browser=True)
    monkeypatch.setenv('EC2_TEST_BROWSER', 'real')
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path)
    assert seen == [[sys.executable, str(CONCEPT_CLI), 'browser', '--run', str(tmp_path)]] * 2
```

The gate tests run in a child process. `import concept` would load concept's `render`/`items`, whose names collide with project modules, into the test process.

```python
STUB_GATE = r'''
import sys
from pathlib import Path
concept_tests, tests, tmp, drop_hint = sys.argv[1:]
sys.path.insert(0, concept_tests); sys.path.append(tests)
from test_browser_transport import synthetic_quiz
import concept, quiz_browser_stub
from PIL import Image
html, data = synthetic_quiz(Path(tmp))
if drop_hint == '1':
    data['items'][0]['hint'] = ''
shots = Path(tmp) / 'shots'
report = quiz_browser_stub.check(html, Path(tmp) / 'browser.json', shots, source=data)
assert report['status'] == 'pass' and report['stub']
concept.checked_browser(html, report, data)
names = concept.shot_names(data)
assert sorted(p.name for p in shots.iterdir()) == sorted(names)
assert len({(shots / n).read_bytes() for n in names}) == len(names)
for name in names:
    with Image.open(shots / name) as frame:
        assert frame.format == 'PNG' and frame.size == tuple(map(int, name.split('-', 1)[0].split('x')))
print('OK')
'''

def stub_gate(tmp_path, drop_hint):
    return subprocess.run([sys.executable, '-c', STUB_GATE, str(CONCEPT_CLI.parents[1] / 'tests'),
                           str(cli_runner.TESTS), str(tmp_path), drop_hint], capture_output=True, text=True)

def test_stub_report_passes_concept_browser_gates(tmp_path):
    proc = stub_gate(tmp_path, '0')
    assert (proc.returncode, proc.stdout.strip()) == (0, 'OK'), proc.stderr

def test_stub_report_fails_when_an_item_has_no_hint(tmp_path):
    proc = stub_gate(tmp_path, '1')
    assert proc.returncode != 0 and '4모드' in proc.stderr
```

Add `import subprocess` to the test file's imports.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest .claude/skills/ec2-review-pack/tests/test_cli_runner.py -q -p no:cacheprovider`
Expected: 4 new tests FAIL. The first two fail with `AttributeError: ... has no attribute 'run_concept'` or `'TESTS'`. The gate tests fail with `ModuleNotFoundError: quiz_browser_stub`. The 12 existing tests PASS.

- [ ] **Step 3: Implement `quiz_browser_stub.check(...) -> dict`**

The module docstring must say that this is a synthetic report that runs no browser, and that `EC2_TEST_BROWSER=real` and `zero_problem[None]` keep the real path.

`check` writes a report with the same key set as the one browser_check.py:345-381 builds:
- `html=html.name`
- `sha256=browser_check.sha256(html)`
- `viewports=[f'{w}x{h}' ...]` and `themes=list(themes)`
- `transport` equal to the real string: `'loopback HTTP, offline=True, local assets fulfilled'`
- `runs`: for each viewport×theme, `{label: f'{w}x{h} {t}', detail: {items_checked: len(items), items: len(items), hints_checked: sum(bool(it.get('hint')) for it in items)}, failures: [], external_blocked: []}`
- `failures: []` and `status: 'pass'`
- marker `stub: 'tests/quiz_browser_stub.py'`

Write `out` the same way as browser_check.py:377-380: `ensure_ascii=False`, `indent=2`, `newline='\n'`.

When `shots` is not None, write one PNG per `concept.shot_names(source)` name with `PIL.Image.new('RGB', (w, h), color)`. Take the size from the name prefix. Derive the color from the first 3 bytes of `sha256(name)` so each name gets different bytes.

Import `concept` and `browser_check` lazily inside the function. The stub runs only in a child process where the concept folder is already on `sys.path`.

- [ ] **Step 4: Implement `run_concept(cli, *args, real_browser=False) -> Result` in `cli_runner.py`**

- Add `TESTS = Path(__file__).resolve().parent`.
- Use the stub only when `args[0] == 'browser'`, `real_browser` is false, and `os.environ.get('EC2_TEST_BROWSER') != 'real'`.
  - In that case run `[sys.executable, '-c', _STUB_BROWSER, str(Path(cli).parent), str(TESTS), *args]`.
  - Otherwise run `[sys.executable, str(cli), *args]`.
- Pass every argument through `str`.
- Call `subprocess.run(argv, capture_output=True, text=True)` and return `Result(proc.returncode, proc.stdout, proc.stderr)`.

`_STUB_BROWSER` follows the same pattern as the race wrapper at test_pack_graph.py:511:

```python
_STUB_BROWSER = """import sys
sys.path.insert(0, sys.argv.pop(1)); sys.path.append(sys.argv.pop(1))
import browser_check, concept, quiz_browser_stub
browser_check.check = quiz_browser_stub.check
sys.exit(concept.main(sys.argv[1:]))"""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest .claude/skills/ec2-review-pack/tests/test_cli_runner.py -q -p no:cacheprovider`
Expected: `16 passed`

- [ ] **Step 6: Commit (only if the user asks)**

```bash
git add .claude/skills/ec2-review-pack/tests/quiz_browser_stub.py .claude/skills/ec2-review-pack/tests/cli_runner.py .claude/skills/ec2-review-pack/tests/test_cli_runner.py
git commit -m "test(review-pack): add synthetic quiz browser report for tests"
```

---

### Task 2: 퀴즈 시나리오 연결과 parity 단언

**Files:**
- Modify: `.claude/skills/ec2-review-pack/tests/test_pack_graph.py`
  - :234-236 (`test_zero_problem_cli_publishes_only_after_actual_converter_and_review_receipts`)
  - :251 (`exercise_zero_problem_cli` signature)
  - :348-353 (`review_quiz.call`)
  - :371 (right after `call('browser')`)
  - :599-604 (`exercise_sibling_repair.call`)

**Interfaces:**
- Consumes: `cli_runner.run_concept(cli, *args, real_browser=False) -> Result` from Task 1
- Produces:
  - `exercise_zero_problem_cli(tmp_path, monkeypatch, scope_change, *, quiz_repair=None, real_browser=False)`. The four calls in test_pack_dispatch_resume.py (:288, :400, :470, :511) keep using the default `False`.
  - `browser_shape(quiz: Path) -> dict`

- [ ] **Step 1: Add the parity assertion and the `real_browser` path (the test itself)**

Add a module-level helper:

```python
def browser_shape(quiz):
    """The form of browser.json, with each screenshot replaced by its PNG size; the stub marker is dropped."""
```

It returns `flow._read(quiz/'browser.json')` with `stub` popped and `screenshots` rewritten to `{name: Image.open(quiz/'shots'/name).size}`. Open each image with a `with` block.

In `review_quiz`, right after `call('browser')`, add:

```python
        if real_browser:
            twin = tmp_path/'stub-quiz'
            shutil.copytree(quiz, twin)
            stubbed = run_concept(brief['concept_cli'], 'browser', '--run', twin)
            assert stubbed.returncode == 0, stubbed.stderr
            assert 'stub' in flow._read(twin/'browser.json') and 'stub' not in flow._read(quiz/'browser.json')
            assert browser_shape(twin) == browser_shape(quiz)
```

The test passes `real_browser=(scope_change is None)`. Add the `real_browser=False` keyword to `exercise_zero_problem_cli`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest ".claude/skills/ec2-review-pack/tests/test_pack_graph.py::test_zero_problem_cli_publishes_only_after_actual_converter_and_review_receipts[None]" -q -p no:cacheprovider`
Expected: FAIL with `NameError: run_concept` (`call` is not switched yet).

- [ ] **Step 3: Switch the two `call` helpers to `run_concept`**

- Add `from cli_runner import run_concept` to the imports.
- `review_quiz.call(*args)` becomes `proc = run_concept(brief['concept_cli'], *args, '--run', quiz, real_browser=real_browser)`. Keep the assertion as it is.
- `exercise_sibling_repair.call(*args, expected=True)` becomes `proc = run_concept(brief['concept_cli'], *args, '--run', quiz)`. Keep the assertion as it is.
- Leave the other direct `subprocess.run` calls on concept (`missing`, `early`, :485, :501, :522, :585, :588) unchanged. None of them is `browser`.

- [ ] **Step 4: Run the affected tests and the runner tests to verify they pass**

Run: `python -m pytest .claude/skills/ec2-review-pack/tests/test_pack_graph.py .claude/skills/ec2-review-pack/tests/test_pack_dispatch_resume.py .claude/skills/ec2-review-pack/tests/test_cli_runner.py -q -p no:cacheprovider --durations=10`
Expected:
- All pass. The pass count equals the current counts for these three files plus 4.
- `test_quiz_adoption_rejects_rewritten_existing_sibling_packet` takes under about 25s (it was 66s).
- `zero_problem[None]` alone keeps a real browser and takes about 45–50s.

- [ ] **Step 5: Fault injection — confirm the gates still bite (revert each change right after)**

1. Change the stub's `status` to `'fail'`. Run `test_quiz_adoption_keeps_approved_answer_after_sibling_removed`. Expected: FAIL (`call('browser')` returns nonzero). Revert.
2. Make the stub's PNG width 1 pixel too small. Run the same test. Expected: FAIL, with `quiz_browser_evidence_changed` somewhere in the failure output (it may come out through the FlowError or assertion message from `evidence` or the worker's acceptance). Revert.
3. Add a `'probe': 1` key to the stub report. Run `zero_problem[None]`. Expected: FAIL on the `browser_shape` assertion. Revert.

After reverting, `git diff --stat` must show changes in only the three test files from Task 1 and `test_pack_graph.py`.

- [ ] **Step 6: Commit (only if the user asks)**

```bash
git add .claude/skills/ec2-review-pack/tests/test_pack_graph.py
git commit -m "test(review-pack): stub the quiz browser outside the zero-problem path"
```

---

### Task 3: 직렬 기준 측정, xdist 워커 수 결정, README

**Files:**
- Create: `.claude/skills/ec2-review-pack/tests/README.md`
- Scratch (not committed): `<scratchpad>/measure_round2.ps1`, logs, `summary.txt`

**Interfaces:**
- Consumes: the full suite after Tasks 1–2
- Produces: the chosen worker count `N` and the measured times, recorded in the README

- [ ] **Step 1: Write the measurement script**

`measure_round2.ps1` runs from the repository root, in this order:
1. Serial: `python -m pytest .claude/skills/ec2-review-pack/tests -q -p no:cacheprovider --durations=25`
2. `-n 4 --dist worksteal`
3. `-n 8 --dist worksteal`
4. `-n 12 --dist worksteal`

For each run, write the stdout/stderr logs and append a `<label> exit=<code> wall=<s>s` line to `summary.txt`. Clear `EC2_TEST_CLI`, `EC2_TEST_BROWSER` and `EC2_CACHE_ROOT` before each run. The structure is the same as `run_both_modes.ps1` from the previous round.

- [ ] **Step 2: Run it in a Terminal panel tab in the background and wait for the summary**

Expected:
- All four runs show `exit=0`, and each log ends with `721 passed, 5 skipped, ... 357 subtests passed`.
- Serial takes about 12–13 minutes.
- If any run fails, fix the cause first (follow systematic-debugging) and do not record a time.

- [ ] **Step 3: Choose N**

Pick the run with the shortest wall time among `exit=0` runs. On a tie (difference within 10%), pick the smaller N.

- [ ] **Step 4: Run the chosen N three more times in a row, then once in full-fidelity mode**

1. Run `-n N --dist worksteal` three times.
2. Run once with `EC2_TEST_CLI=subprocess` and `EC2_TEST_BROWSER=real` under `-n N --dist worksteal`.

Expected: all four runs show `exit=0` with 721 passed / 5 skipped / 357 subtests.

A failure that happens only under parallel load is a real issue. Find the cause and do not increase the retry count. If you need to change a test, only lengthen a harness wait that exists for completion. Do not lengthen or remove a "still blocked" check such as `future.result(timeout=0.3)` or `p2.join(0.3)`.

- [ ] **Step 5: Write `tests/README.md`**

Write it in Korean, about 15 lines. Include:
- The full parallel command: `python -m pytest .claude/skills/ec2-review-pack/tests -n <N> --dist worksteal -p no:cacheprovider`
- The serial command
- How to run a single test (no `-n`)
- The full-fidelity mode `EC2_TEST_CLI=subprocess` + `EC2_TEST_BROWSER=real`, and when to use it: before committing changes to the pack_cli/pack_flow entry points or to concept `browser_check`
- That `EC2_CACHE_ROOT` must not be preset
- The measured serial and parallel times (as measured in Steps 2–4)
- Where the real browser still runs: `zero_problem[None]`, layout_probe, pack_approvals real-browser tests, standalone-svg-qa, `real_probe=True` integration

- [ ] **Step 6: Commit (only if the user asks)**

```bash
git add .claude/skills/ec2-review-pack/tests/README.md
git commit -m "docs(review-pack): document parallel and full-fidelity test runs"
```
