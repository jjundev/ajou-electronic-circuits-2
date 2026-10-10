# P10.72 render assumptions: completed audit

Scope: HyperFrames 0.8.137, FFmpeg full 9.0.2, Apple M5. Production composition was read only. Diagnostic inputs and outputs remain inside this performance-test folder.

## Bounded browser diagnostic

The copied composition changes only root duration to 8 seconds and its GSAP clock to source frames 1800 through 2040. The tested output covers source time 60.000 through 67.9667 seconds, 240 frames at 1920x1080/30 fps. Each case ran once, sequentially, with workers=4, quality=delivery and CPU video encoding.

| Case | Requested browser capture | time real | Successful capture stage | Encode stage |
|---|---|---:|---:|---:|
| A | Metal, screenshot | 8.54 s | 3.831 s | 1.101 s |
| B | Software, screenshot | 8.38 s | 4.493 s | 0.840 s |
| C | Metal, fast capture | 11.08 s | 3.526 s after retry | 0.942 s |

A used ANGLE Metal Apple M5. B launched SwiftShader and forced screenshot capture. All cases resolved to 4 workers. C initially engaged drawElement, then failed self-verification at frames 60, 120 and 180: 23.1, 22.9 and 22.7 dB versus the 32 dB floor. It automatically rerendered with screenshot capture. C.log lines 109-110 contain the verification failure and retry. Its listed successful capture stage excludes the failed 3.246-second attempt; time real includes it.

Consequently, C does not demonstrate successful fast-capture fidelity or acceleration. A and C final outputs have identical RGB decoded hashes for all 240 aligned frames because C fell back to screenshot. This concrete failure supports retaining the normal verification gates and keeping fast capture out of automatic production adoption for this composition.

A and B differ in all 240 exact RGB decoded hashes. At the nine sampled frames [0,30,60,90,120,150,180,210,239], aggregate PSNR is 48.125385 dB (minimum 47.065886 dB), and SSIM is 0.999675. These show small measured pixel differences at those sample positions; neither direction is a fidelity ground truth. Visual inspection of sample-05.png (source 64 seconds) from A and B found the same visible text, formula and layout without an apparent defect at normal display scale. This does not certify every frame or small-text edge.

The diagnostic fully decoded all three videos to aligned RGB framemd5, validated all 240 frames and metadata, exported nine PNGs for each case, and verified unchanged hashes for every production composition file. See results.json, comparisons.json, *.framemd5, *-psnr.stats and *-ssim.stats. PNG sample-01 is frame0/source60s; sample-05 is frame120/source64s; sample-09 is frame239/source67.9667s.

Single short trials contain substantial browser startup and encode overhead. A capture was faster than B capture, while their complete elapsed times differ by only 0.16 seconds in the opposite direction. This cannot establish a full-video browser-GPU speed ranking.

## Completed primary-run audit

All six primary render logs resolve to the requested workers 2/4/6, use disk screenshot capture, and report the same hardware ANGLE Metal Apple M5 browser backend. No capture retry/fallback was found in those logs. CPU in case names means CPU video encoding; Chrome still uses the hardware browser GPU.

Baseline worker2 real times are 178.95 and 174.33 seconds (mean 176.64). Worker6 times are 81.63 and 88.57 seconds (mean 85.10). Worker6 therefore reduced observed mean elapsed time by 51.8%, approximately 2.08x speed, for this composition and environment. Two repeats support the observed comparison without establishing an environment-independent guarantee. CPU seconds were similar across these configurations, so the test does not establish reduced CPU work or energy consumption.

Worker4 CPU took 107.38 seconds, while worker4 requested GPU encoding took 117.23 seconds. CPU time fell from 235.55 to 171.16 seconds, but encode time rose from 15.912 to 26.805 seconds. This single comparison supports lower measured CPU time and slower observed elapsed time under these settings. The GPU run's sampled summed RSS peak was 1597.47 MiB, versus 1365.02 MiB for worker4 CPU; do not claim it lowered render memory.

ffprobe stream tags report Lavc63.1.102 libx264 for worker4 CPU and Lavc63.1.102 h264_videotoolbox for worker4 GPU. Installed HF source chunk-TTBOUHWT.js:7539-7546 and 8617-8638 adds -allow_sw 1 for VideoToolbox probing and actual encoding. Thus selected VideoToolbox is verified, but the primary run does not prohibit software fallback and cannot certify the actual session used hardware encoding. Different libx264 CRF and VT bitrate control also prevent treating quality=delivery as equal quality across encoders.

Caption timings were current 15.30 seconds, preset-fast 16.55 seconds, and VideoToolbox 26.53 seconds. The VT caption command explicitly set -allow_sw 0 and succeeded, so software encoder fallback was prohibited in that specific trial. Its CPU seconds and sampled summed RSS were lower, but its elapsed time and output size were higher. These are single-run observations; no quality parity or general hardware-speed conclusion follows. Subtitle rendering and decode still perform CPU work.

One-second summed descendant RSS is a sampled process-memory metric: it can miss short peaks and double-count shared pages. It is not exact physical-memory consumption. /usr/bin/time real is the runtime authority; the Python polling wall clock can include up to roughly one second extra. Swap measurements describe the whole machine and cannot attribute changes solely to a case. Source hashes before/after the main benchmark match; separate delivered-file verification is owned by the parent.

## Remaining evidence boundary

The parent owns primary-output full-decode, full-frame worker comparison, audio validation, representative caption quality review and delivered-file hashes. Until those checks finish, do not label the full videos equivalent or production-ready based only on metadata, equal file size, this eight-second diagnostic, or encoder names.
