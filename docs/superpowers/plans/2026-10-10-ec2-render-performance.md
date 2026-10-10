# EC2 Render Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 검증된 캡처 작업자 6개 설정을 문제풀이 영상에 적용하고, 성능 옵션 변경 시 음성을 보존하며 렌더부터 재개한다.

**Architecture:** 렌더 옵션의 탐지·검증·읽기를 작은 전용 모듈에 두고 음성 설정과 분리한다. 기존 CLI/상태 지문/미디어 함수를 연결하며 파트·마스터 출력을 검증한 뒤 교체한다. 개념 복습 영상과 글로벌 스케줄러는 변경하지 않는다.

**Tech Stack:** 기존 Python/unittest/PyMuPDF/Pillow, Node/로컬 HyperFrames, Chrome, FFmpeg/ffprobe/libass. 실측 근거 버전은 HyperFrames 0.8.137, FFmpeg 9.0.2이며 설치/업그레이드는 이 계획의 작업이 아니다.

**Spec:** `docs/superpowers/specs/2026-10-10-ec2-render-performance-design.md`. 실행자는 두 문서를 읽는다. 모든 아래 경로는 REPO `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` 기준이다. `SKILL=.agents/skills/ec2-solution-video`. 시작 조사 HEAD는 `345a88e`; 실행 시 실제 체크아웃/사용자 변경을 다시 확인한다. 작업 격리가 필요하면 실행 시 using-git-worktrees로 만든다.

## Global Constraints

- 적용 대상은 ec2-solution-video만이며 ec2-review-video 코드와 출력은 변경하지 않는다.
- 신규 RUN 기본값은 Darwin / Apple M5 / CPU 10코어 / 메모리 16GiB 이상에서 작업자 6개이며, 다른 환경이나 탐지 실패에서는 기존 2개다.
- 렌더 작업자 수는 정수 1–6이며 bool, 실수, 문자열 JSON 값, 범위 밖 값은 거부한다.
- CPU 인코딩과 브라우저 GPU auto를 유지하며 experimental-fast-capture=false를 명시한다.
- 1920×1080, 30fps, 기존 PCM mono 24kHz, 기존 자막 인코딩·폰트·배치 설정을 유지한다.
- 렌더 옵션은 source/render-options.json에 저장하며 source/config.json·대본·음성·타임라인을 변경하지 않는다.
- 파트와 문항은 순차 렌더하며 문항 내부의 캡처 작업자만 늘린다.
- 실패 시 기존 파트·마스터·최종 영상과 검증 영수증을 보존하고, GPU·음성 공급자·작업자 수를 자동 대체하지 않는다.
- 신규 패키지 설치·전역 설정 변경·유료 API 호출·기존 완성 영상 일괄 재생성·자동 게시를 하지 않는다.

## Review Focus

1. 옵션 없는 이전 RUN: resume-set은 파일을 추가하지 않으며 렌더 요청 때만 옵션을 만든다 — Task 1/2.
2. 잘못된 workers/손상 JSON/예상 밖 옵션 키: 실행·기존 옵션 덮어쓰기 전에 실패한다 — Task 1/2.
3. 저장된 수동 옵션과 다른 호스트: 저장값 우선, CLI override 최우선이며 탐지 실패로 값을 지우지 않는다 — Task 1.
4. 렌더 설정 변경: 최초 무효 단계는 render이며 WAV·음성 config·타임라인 바이트와 앞 단계 지문을 보존한다 — Task 1/2.
5. 실패/잘못된 규격/두 번째 파트 실패: 검증된 이전 출력과 영수증을 보존하며 재시도에 성공한 파트를 사용자가 잃지 않는다 — Task 2.

---

## 파일 구조

| 파일 | 책임 |
|---|---|
| Create: `.agents/skills/ec2-solution-video/scripts/solution_video/render_options.py` | 호스트 탐지, 렌더 옵션 기본값/검증/읽기. 상태 쓰기·음성 처리는 하지 않음 |
| Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/state.py:7-29` | render 옵션 파일과 정책 모듈을 render부터 지문에 등록 |
| Modify: `.agents/skills/ec2-solution-video/scripts/video.py:23-44,82-93,162-179` | prepare/render CLI 연결, 옵션 저장, 성공 영수증 등록 |
| Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/media.py:22-48` | 선택된 workers, pending 출력/규격 검사, 실행 기록 |
| Test: `.agents/skills/ec2-solution-video/tests/test_render_options.py` (new), `test_state.py`, `test_cli.py`, `test_media.py` | 정책·재개·오류/파일 보존 회귀 |
| Create: `.agents/skills/ec2-solution-video/tests/test_render_performance_acceptance.py` | 명시적 opt-in의 실제 동결 영상 수용 검사 |
| Modify: `.agents/skills/ec2-solution-video/SKILL.md`, `references/verification.md` | 기본값, 수동 조절, 재개와 검증 범위 |

생산 RUN 데이터는 source/render-options.json과 verification/render-receipt.json을 새로 사용한다. TTS adapter와 defaults.json은 수정하지 않는다. 커밋 체크포인트는 아래에 제시하되, 실제 실행에서 커밋 권한이 없으면 동일한 파일 범위의 diff 체크포인트로 남긴다. 이번 계획 작성 턴은 커밋하지 않는다.

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

### Task 2: CLI 연결과 안전한 실제 렌더

**Files:**
- Modify: `.agents/skills/ec2-solution-video/scripts/video.py:23-44,82-93,162-179`
- Modify: `.agents/skills/ec2-solution-video/scripts/solution_video/media.py:22-48`
- Test: `.agents/skills/ec2-solution-video/tests/test_cli.py`, `test_media.py`
- Modify: `.agents/skills/ec2-solution-video/SKILL.md`, `references/verification.md`

**Interfaces:**
- Consumes: Task 1 load_render_options/default_render_options/validate_render_options; existing util.write, media.probe/command, state.recover_run/finish_stage.
- Produces: `render_master(parts: list[dict], timeline: dict, audio: list[dict], run: Path, hyperframes_entry: Path, *, render_options: dict[str, object] | None = None) -> Path`. Existing five-position calls remain valid.
- Produces: CLI render `--render-workers N` (optional). Successful render JSON adds render_options and render_receipt path; paid_requests stays 0.
- Produces: verification/render-receipt.json schema_version/options/parts/master_sha256; parts rows have key, command:list[str], elapsed_seconds:float, output_sha256:str, frames:int.
- Produces (internal): `_commit_master_and_receipt(master_pending: Path, receipt_data: dict, master: Path, receipt: Path) -> None`; prepares receipt pending, preserves old files, commits the pair, and rolls back on write/replace exceptions.

- [ ] **Step 1: Write failing CLI behavior tests**

Add `test_prepare_keeps_render_options_out_of_voice_config`, `test_render_override_precedes_recovery`, `test_resume_set_does_not_initialize_legacy_options`, `test_invalid_render_options_do_not_launch_renderer` to CLITests. Use existing sandbox/content fixture and mocked gate/renderer; prepare mocks source discovery/export as needed. Assert new options are separate, voice config unchanged, workers=6 override is saved before recover_run sees it, resume writes nothing, invalid N/JSON retains options bytes and never calls render_master/generate_voice. Simulate successful renderer producing master+receipt and assert finish_stage receives both output files. Existing namespace callers without render_workers must work via getattr.

- [ ] **Step 2: Verify CLI tests fail**

Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_cli.py -v`
Expected RED on missing behavior/CLI option; no paid request.

- [ ] **Step 3: Wire CLI options**

prepare_batch writes default_render_options to source/render-options.json separately. In render action, validate/load and atomic-write options after the existing required-file check and before recover_run. Pass options by keyword to render_master. Add argparse integer 1–6 validation for render only; register master and receipt on successful finish_stage. Non-render commands do not initialize options or accept the new flag.

- [ ] **Step 4: Write failing atomic-output tests**

Extend MediaTests with `test_render_failure_preserves_previous_outputs`, `test_wrong_dimensions_or_fps_or_frames_cannot_replace_part`, `test_later_part_failure_preserves_master_and_completed_part`, `test_invalid_master_cannot_replace_previous_master`, `test_receipt_write_or_replace_failure_rolls_back_master`, `test_saved_render_options_drive_execution_and_receipt`. Use mocked command/probe plus dummy previous byte files. Simulate nonzero exit, timeout, malformed probe, 1280×720, 24/1 fps, missing expected frame, wrong master audio rate/channels, receipt write failure and failure at the second commit replace. Assert old target/receipt bytes preserved, pending removed, failed log retained, no substitute attempt, parts executed sequentially. On success assert command workers=6, quality=delivery, explicit fast=false, no encoder --gpu, recorded args match execution, receipt hashes match files, PCM starts remain correct. Update the existing padded PCM mock to return full valid media metadata; do not change its timing assertions.

- [ ] **Step 5: Verify media tests fail**

Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_media.py -v`
Expected RED on direct-overwrite or absent option behavior.

- [ ] **Step 6: Implement render_master and the commit helper in media.py**

Implement the Task 2 signatures; source_checks remains mandatory. Use Task 1 loader if no options supplied; otherwise validate. Render part pending, probe exact video contract, then os.replace. Validate pending master video contract and mono 24kHz audio. Prepare receipt pending before committing the master/receipt pair; keep old-file backups until both replacements succeed and restore them on exceptions. Remove failed pending output while retaining a log, including partial stdout/stderr from TimeoutExpired. Preserve existing PCM construction, mux codec settings, captions and verify logic.

- [ ] **Step 7: Update usage documentation**

Document current-M5 default 6, other/unknown-host default 2, stored-option precedence, explicit workers=2/4/6 examples, sequential document processing, no automatic GPU/fast capture, render-only recovery and manual low-worker retry.

- [ ] **Step 8: Verify Task 2 passes**

Run the exact CLI/media commands above, then policy/state commands from Task 1. Expected all OK; snapshot TTS config/voice/timeline unchanged.

- [ ] **Step 9: Scoped checkpoint**

Stage only Task 2 files; inspect cached diff/check. If committing is authorized: `git commit -m "feat: apply verified workers to EC2 solution rendering"`.

### Task 3: 실제 동결 영상 수용 검증

**Files:**
- Create: `.agents/skills/ec2-solution-video/tests/test_render_performance_acceptance.py`
- Modify: `.agents/skills/ec2-solution-video/references/verification.md`

**Interfaces:**
- Consumes: Task 1 options, Task 2 render_master/receipt and CLI regression behavior; frozen benchmark metadata.json.source_run.
- Produces: unittest RenderPerformanceAcceptance gated by EC2_RENDER_ACCEPTANCE=1; writes metrics/hash/frame evidence under EC2_RENDER_ACCEPTANCE_DEST. EC2_RENDER_FIXTURE names the original frozen RUN; EC2_HYPERFRAMES_ENTRY names the pinned local CLI. No API calls/production publish.

- [ ] **Step 1: Write the opt-in acceptance contract**

`test_p1072_worker_change_preserves_every_frame_and_pcm`: default skips without explicit opt-in. With opt-in, missing fixture/destination/CLI or fixture frame count other than 7,220 is a failure, not an unnoticed skip. Copy composition, parts/timeline/audio JSON and the referenced cached WAVs into two scratch RUNs. Preserve source-file hashes before/after. Call production render_master with workers=2 and workers=6 (other fixed options identical), time each, and record metrics. Assert both video streams are 1920×1080/30fps/7,220 frames, narration.wav/encoded AAC hashes match, all decoded video framemd5 entries match, receipts agree with chosen options and actual outputs, and original files are untouched. Record elapsed ratio rather than enforce a brittle exact 52% threshold. Assert no paid transport/publish is invoked.

- [ ] **Step 2: Verify the harness default and explicit-input behavior**

Run: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_render_performance_acceptance.py -v`
Expected: explicit skip explaining opt-in; separately exercise missing-input assertions with mocked opt-in to prove they fail before rendering. This is not the real-video PASS. Task 1/2 provided behavior RED/GREEN; do not break correct code just to force this acceptance test RED.

- [ ] **Step 3: Run full current-checkout regression once**

Run: `PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`
Run: `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs .agents/skills/ec2-solution-video/tests/test_teaching_runtime.cjs`
Expected: OK / zero failures. Explain any opt-in skips; repair regressions before real rendering. Existing real-media acceptance tests may require dependencies; absence is explicit and never reported as pass.

- [ ] **Step 4: Run the actual acceptance outside original RUNs**

Use REPO cwd and verified local paths; create a new scratch destination via mktemp. HYPERFRAMES_FFMPEG_PATH must point to the same /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg for both cases.

```bash
EC2_RENDER_ACCEPTANCE=1 EC2_RENDER_FIXTURE="$REPO/문제풀이영상/1007/1007_제작자료/실행/20261010-124459-semantic-caption-wrap/videos/problem-d885c8738da3" EC2_RENDER_ACCEPTANCE_DEST="$EC2_ACCEPTANCE_DEST" EC2_HYPERFRAMES_ENTRY="$EC2_HF_ENTRY" HYPERFRAMES_FFMPEG_PATH=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_render_performance_acceptance.py -v
```

Set REPO to the absolute root from the header; EC2_ACCEPTANCE_DEST to a fresh scratch directory; EC2_HF_ENTRY to `/Users/hyunjun_macbook_pro/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/cli.js` only after confirming version 0.8.137 exists. Missing pinned tools: report unavailable without install/version substitution. Expected actual PASS with 7,220 equal frames and preserved audio/source. Do not copy old state/review approvals to satisfy current CLI prerequisites; CLI wiring was exercised in Task 2, and this test measures the production renderer on frozen visual/PCM data. It is technical acceptance, not new educational/audio approval.

- [ ] **Step 5: Inspect evidence and complete the documentation**

Inspect actual capture mode/effective workers in both logs, receipts and representative beginning/annotation/writing/final frames. Compare measured 6/2 time ratio to the prior 0.482 result; if 6 no longer improves speed, record the condition and withhold the default-profile performance claim pending diagnosis. Document test command, real outcome, full-frame/audio checks and any limitations in references/verification.md. Do not add output binaries or cached WAVs to Git.

- [ ] **Step 6: Final scoped checkpoint**

Run `git diff --check` and inspect only this feature's changes; preserve unrelated untracked performance samples/design-assignment work. Stage test_render_performance_acceptance.py, references/verification.md and these design/plan documents only. If committing is authorized: `git commit -m "test: verify EC2 multicore render acceptance"`. No push or PR is part of this plan.

## Self-review record

Scope/default/manual override/recovery/failure preservation/recording/docs/real acceptance are mapped to Tasks 1–3. Review Focus 1–5 have named tests in their owning tasks. Task 2 consumes the same four option signatures produced by Task 1; Task 3 consumes the unchanged five-position media interface plus keyword-only options. Shared util/TTS modules and ec2-review-video remain outside edits. Real acceptance deliberately separates frozen-media rendering from the current CLI's semantic-state checks rather than falsifying old reviews. Implementation bodies are left to the executor; this plan fixes interfaces, values, evidence and boundaries.
