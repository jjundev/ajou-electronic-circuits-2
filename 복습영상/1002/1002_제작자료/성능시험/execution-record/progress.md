# SDD ledger — plan: docs/superpowers/plans/2026-10-10-ec2-review-render-performance.md

Baseline: 81 tests passed (4.714s).
Pre-flight: Task1 produces read-only options and renderer; Task2 consumes exactly these. No conflict.
Ruling: existing explicit user request approves same settings and Native execution; no repeat approval gate. Cost if wrong: unwanted same-policy implementation.
Ruling: no EC2 production review RUN found; use existing circuit fixture with synthetic PCM, report limited benchmark scope. Cost if wrong: fixture speed may not generalize to full lectures.
Ruling: pin HF/FFmpeg for measured comparison; no upgrade. Cost if wrong: newer tool improvements omitted.
Task 1: feature tests RED (10 failures, CLI parser failure then assertion RED); GREEN full 91, then cache code invalidation RED→GREEN full 93 (3.810s).
Task 2: first real 60s static fixture: 1/2/6 =15.666/14.728/16.871s, frame/PCM/AAC/master all identical. Speed expectation disproved; retained failed attempt.
Ruling: performance is measured and reported, never forced as a success assertion. Compare extended motion fixture as separate workload, retain static regression. Cost if wrong: dynamic result may not generalize.
Task 2: dynamic first pass 1/2/6=65.036/47.037/28.011s. 6 faster but 250 decoded frames differ in first GOP of scene2; fail strict equality, not accepted. PNG comparison localized first-frame difference to math glyphs.
Ruling: add fonts-ready registration to composition and require legacy RUN reassemble via composition-code fingerprint. Probe same scene at2/6 produced identical video/frame hashes after fonts-ready wait; no two-RAF wait (that stalls pinned runtime). Cost if wrong: one local reassemble and font initialization overhead; TTS remains cached.
Readiness test RED immediate timeline construction before deferred fonts; composition invalidation test RED missing code factor.
Task 1: complete implementation, full 97 tests (6.733s), skill valid. Commit deferred until acceptance.
Ruling: one final read-only review may run while final performance/source checks finish, using staged snapshot (uncommitted due conditional commit instruction). Measurements remain a merge gate. Cost if wrong: later fix requires fresh tests, no second reviewer.
Static final: real acceptance exit0; 1800frames, 110 frozen files unchanged, master/frame/PCM/AAC exact equal for1/2/6. Source checks passed, burned captions/full decode passed. Times 25.547/26.734/28.797s;6 is7.7% slower than2. Directly inspected frame1/59: readable dark math and captions, no clipping.
Final review: two Important, no Critical. Fixed transactional part/master receipt publication with rollback retention; part-write/master-write/replace/interrupt/failed-restore tests RED→GREEN. Fixed timeout process descendants (including detached session) via tree termination/reaping and unique attempt pending paths; actual orphan test RED→GREEN. Full suite102/102 (4.760s).
Final: minor (deferred): acceptance script checks fixture source inventory rather than each worker clone; manual clone hash verification will supplement evidence, automated enhancement remains deferred.
Final: Ruling: general hardware/lecture speed and Aoede narration quality are outside available local synthetic benchmark; report no universal speed or voice-quality claim. Cost if wrong: actual lesson performance requires a separate full-source run.
Final: Ruling: HF versions beyond0.8.137 not tested; keep version pin. Cost if wrong: other versions may differ.
Final: Ruling: reviewer did not inspect completed artifacts; author finishes strict acceptance and representative-frame checks before merge. Cost if wrong: visual review lacks independent artifact inspection.
Dynamic fonts-ready final: full real acceptance exit0,1/2/6=67.899/50.899/28.186s,44.6% shorter2→6. All1800 frames/master/PCM/AAC exact equal, sources/check/decode/subtitles passed. Repeat final safety code using production mux_with_receipt for2/6 to verify new commit path.
Task 2: complete actual final safety-code render2/6=48.715/29.839s (38.747% reduction), exact1800 frames/master/PCM/AAC; sourcechecks/decode/sync/subtitles passed. Real cache:2 parts reused,0 render calls,4 file mtimes unchanged. Browser static/dynamic28+28 checks passed, representative frames directly inspected. Actual worker originals110files unchanged per clone. Precommit suite102/102 (5.052s), skill valid, exact15-file staged set, no unrelated changes.
Feature commit: 8c416cf3287f059b700f448185291d7468b0547b (exact15 files). Main local merge authorized by user; no push.
Main local merge:7098e0cc042dab4f2660eebe1fa69c3ebc28dcae, feature8c416cf3287f059b700f448185291d7468b0547b. Merged main full suite102/102 (5.215s), skill valid. Main live defaults workers6/CPU/browserGPUauto/fastfalse. Unrelated tracked modification retained, no push.
