# EC2 Review Render Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Apply approved rendering policy to review videos and validate real output before a scoped commit and main merge.
**Architecture:** Independent read-only lib/render_options.py follows solution renderer policy. CLI persists policy before recover, render_parts consumes it with sequential scenes and internal capture workers. Existing audio and mux remain.
**Tech Stack:** Python unittest, local HyperFrames 0.8.137, FFmpeg 9.0.2.
**Spec:** docs/superpowers/specs/2026-10-10-ec2-review-render-performance.md

## Global Constraints
- Apple M5 physical10 RAM>=16GiB workers6; unknown host2; override1..6.
- CPU encode, browser GPU auto, fast capture false, delivery1080p30.
- No paid TTS, source content edits, dependency upgrades, push, other-user-file staging.
- Commit only after actual render verification; merge main locally.

## Review Focus
- Saved malformed policy must fail even with override.
- Cache hits after unchanged settings must avoid render; changed workers invalidate render only.
- Nonzero/timeout/stale pending must preserve previous MP4/receipt and log errors.
- revoice rebuilt scenes must use policy without enabling scene-level oversubscription.
- Legacy RUN without settings remains readable; resume does not write new policy.

### Task 1: Policy, CLI and rendering
**Files:** lib/render_options.py, lib/render.py, lib/composition.py, lib/state.py, scripts/video.py, tests/test_render_options.py, tests/test_render.py, tests/test_cli.py, tests/test_state.py, tests/test_composition.py (under .agents/skills/ec2-review-video), SKILL.md, references/rendering-and-verification.md.
**Interfaces:** Produces load_render_options(run, workers=None, *, hardware=None) -> dict; render_parts(parts, run, backend) -> list[Path], backend contains render_options. CLI render/revoice consumes these.
- [x] Write failing tests for policy validation/precedence, command settings/sequential/cache/failure/timeout, CLI flags/defaults, render-only invalidation.
- [x] Run unittest targeted files. Expected: new feature tests FAIL.
- [x] Implement exact policy and integrate render/revoice; preserve probe_backends public helper for older callers. Validate settings before subprocess, include settings in cache and state; log actual commands.
- [x] Run full unittest discover. Expected: all pass. Commit deferred until Task 2 acceptance by user instruction.

### Task 2: Real acceptance and local integration
**Files:** tests/render_performance_acceptance.py; plan/spec; results in 복습영상/1002/1002_제작자료/성능시험/<timestamp> (untracked).
**Interfaces:** Consumes Task1 render_parts and CLI CPU backend, uses unchanged mux plus subtitles helper.
- [x] Build 2 scene60s fixture; run workers1/2/6 sequentially with real Node/Chrome/FFmpeg. Expected: 1800frames each, frame hashes/PCM/AAC equal; source hashes unchanged. Compare original0.6s motion and extended24s stress motion separately; report measured speed without asserting all workloads get faster. Inspect representative frames.
- [x] Test fonts-ready registration with deferred Promise in a Node VM (RED→GREEN); test composition-code drift invalidates composition but preserves voice. Re-run real static and dynamic acceptance after fix.
- [x] Full suite and skill validation. Expected: exit0.
- [x] Dispatch one fresh final code reviewer; fix Important/Critical via failing tests then full suite.
- [x] Stage only requested files, inspect cached diff; commit. Merge main locally and run merged tests; no push.
