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

