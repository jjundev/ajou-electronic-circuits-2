### Task 1: 렌더 옵션과 단계 지문 분리

**Files:**
- Create: `.agents/skills/ec2-solution-video/scripts/solution_video/render_options.py`
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/state.py:7-29`
- Test: `.agents/skills/ec2-solution-video/tests/test_render_options.py`, `test_state.py`

**Interfaces:**
- Consumes: 기존 `util.read/write/digest`, `contracts.InputError`, `state.finish_stage/recover_run/stage_fingerprint`.
- Produces: `detect_hardware() -> dict[str, object]`: platform/chip/cpu_cores/memory_bytes; Darwin sysctl 실패는 미확인 필드로 반환.
- Produces: `default_render_options(hardware: dict[str, object] | None = None) -> dict[str, object]`.
- Produces: `validate_render_options(options: dict[str, object]) -> dict[str, object]`: 스펙의 다섯 키/고정값/정수 범위를 검사해 복사본 반환, 오류는 InputError.
- Produces: `load_render_options(run: Path, workers: int | None = None, *, hardware: dict[str, object] | None = None) -> dict[str, object]`: 쓰기 없이 CLI override → 저장값 → 기본값 순으로 선택.

- [ ] **Step 1: Write failing policy tests**

`RenderOptionsTests`에 아래 assertions를 작성한다. fixtures.Sandbox의 임시 RUN과 util.write를 사용한다.

```python
m5 = dict(platform='darwin', chip='Apple M5', cpu_cores=10, memory_bytes=16 * 1024**3)
assert default_render_options(m5) == dict(schema_version=1, workers=6, encoder='cpu', browser_gpu='auto', fast_capture=False)
assert default_render_options(dict(m5, chip='Apple M4'))['workers'] == 2
assert default_render_options(dict(m5, memory_bytes=8 * 1024**3))['workers'] == 2
assert default_render_options(dict(platform='linux'))['workers'] == 2
```

Test names: `test_missing_options_is_read_only`, `test_saved_override_survives_host_change`, `test_invalid_options_fail_without_rewrite`, `test_detection_failure_uses_legacy_workers`. Assert missing file remains absent; saved workers=4 wins over M5 defaults and unavailable hardware; override=2 wins; values `True, 0, -1, 7, 2.5, '6'`, corrupted JSON, unknown keys, schema_version=2/True, encoder='gpu', browser_gpu='hardware', fast_capture=True raise InputError and preserve file bytes. Patch sys.platform and subprocess.run to test failed sysctl without touching the real host.

- [ ] **Step 2: Verify policy tests fail**

Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_render_options.py -v`
Expected: RED because render_options module/functions do not exist; no subprocess renderer/API call.

- [ ] **Step 3: Implement the four Interfaces in render_options.py**

Use sys.platform and Darwin sysctl fields specified in the spec; unknown/failed detection defaults to 2. JSON read errors become InputError. Validate saved values before applying an override so corruption is not hidden. Use type(value) is int for schema_version/workers, and type(value) is bool for fast_capture=False. No file writes or environment credential access.

- [ ] **Step 4: Write the failing render-only invalidation test**

Add `StateTests.test_render_options_change_preserves_voice_and_timeline` using the existing full-stage fixture pattern in test_state.py: create options workers=2; mark all STAGES with existing finish_stage; snapshot fingerprints through composition plus WAV/config/timeline hashes; write workers=6; assert recover_run(run)=='render' and all snapshots unchanged. Also assert deleting/adding the options file affects render only. `test_missing_options_recovery_is_read_only` marks current-stage records without options and verifies recovery does not create the file.

- [ ] **Step 5: Verify the state tests fail**

Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_state.py -v`
Expected RED at render option invalidation.

- [ ] **Step 6: Implement render-only dependency mapping in state.py**

Add source/render-options.json to FACTORS.render and render_options to MODULES.render only. Do not edit util/contracts or earlier-stage factors. Legacy saved tool hashes may legitimately invalidate render; do not restamp old receipts.

- [ ] **Step 7: Verify Task 1 passes**

Run the exact policy and state commands above. Expected: both OK; invalid inputs leave files unchanged and setting changes never invalidate voice/timing/composition.

- [ ] **Step 8: Scoped checkpoint**

Stage only render_options.py, state.py, test_render_options.py, test_state.py; inspect `git diff --cached --check` and file list. If committing is authorized: `git commit -m "feat: isolate EC2 render options from voice state"`.

