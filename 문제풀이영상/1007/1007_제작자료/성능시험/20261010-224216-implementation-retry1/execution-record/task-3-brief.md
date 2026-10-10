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
