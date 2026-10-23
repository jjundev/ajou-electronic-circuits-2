# EC2 Shape Writing Speed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 답 상자의 조각 수에 따라 늘어나는 필기 시간을 제거하고 음성 뒤 필기 지연을 정확히 검출한다.

**Architecture:** 원본 도형 단위로 draw 예산을 정한 뒤 clip에 배분한다. 기존 reveal 타임라인이 이 예산을 사용하고, pacing 분석은 필기 지연과 완성 화면 hold를 별도로 보고한다. 음성은 재사용한다.

**Tech Stack:** Python unittest, PyMuPDF, 30fps HyperFrames/GSAP, 24kHz PCM, libass FFmpeg.

**Spec:** ../specs/2026-10-09-ec2-shape-writing-speed-design.md (실행 전 함께 읽을 것)

## Global Constraints
- spatial pencil만 시간 배분 수정. 기존 7.5 chars/sec, interval=ceil(30/chars_per_second), 카메라 전환 12프레임 유지.
- B=min(90,max(18,ceil(W/H*interval))), 각 조각 최소 1프레임, 전체 draw 합계 B. 조각 수>B면 InputError.
- 필기 지연 60프레임 초과 시 review-required. 정확히 60프레임이면 이 조건은 통과.
- PDF/대본/원본 geometry/공개 순서/typing/non-spatial 동작 보존. 기존 WAV 재사용, 유료 요청 0.
- 실제 P10.72 마지막 필기 지연을 60프레임 이하로 해결; 예외 승인으로 우회하지 않는다.
- 기존 검토 영상과 증거를 보존. 청취 불가 시 complete=false/audio_meaning=unverified 및 publish/latest 유지.
- Native 실행 방식 유지. 작업 전 현재 변경 목록을 기록해 앞선 미커밋 청크 동기화 작업을 보존한다. 이번 요청은 계획 작성이므로 Git commit/push는 별도 사용자 요청 후 진행한다.

## Review Focus
- 세로선/zero-height 분수선: 세로선 단일 조각은 18프레임, 가로선은 폭 비례로 공개하며 누락되지 않는다 (Task 1).
- 지나치게 많은 조각/불균등 폭: 조용한 시간 증가 없이 명시적 오류, 정수 합계와 최소 1프레임 보장 (Task 1).
- 줄 첫 unit에 여러 대상/공백: lifted 비용은 첫 대상에만 적용하고 뒤 대상은 일반 이동 (Task 2).
- 오래된 gaps 승인/음성 trailing silence: 필기 지연은 PCM 끝으로 계산하고 별도 최신 예외만 인정 (Task 3).
- 코드 변경 뒤 재개/음성이 필기보다 긴 경우: timing 이후만 무효화하며 WAV 보존, hold는 음성 중 시간을 포함하지 않는다 (Tasks 3–4).

---

## File Structure
이하 P는 `.agents/skills/ec2-solution-video`다. 실행 명령에서만 shell 변수 P를 지정한다.
- Create P/scripts/solution_video/shape_timing.py: 순수 도형별 draw 프레임 배분.
- Modify P/scripts/solution_video/reveal.py: helper 사용과 첫 대상 줄 이동.
- Modify P/scripts/solution_video/narration_pacing.py: 필기 지연/완성 hold 측정과 별도 예외.
- Modify P/scripts/solution_video/state.py: 새 helper를 timing fingerprint에 추가.
- Create P/tests/test_shape_timing.py; modify tests/test_reveal.py, test_writing_units.py, test_narration_pacing.py, test_state.py.
- Modify P/SKILL.md, references/narration-and-timing.md, references/verification.md: 시간 배분/지연 검토 정책을 코드와 일치시킴.

### Task 1: 도형 전체 draw 예산과 clip 배분

**Files:** Create P/scripts/solution_video/shape_timing.py; Create P/tests/test_shape_timing.py; Modify P/tests/test_writing_units.py.

**Interfaces:** `allocate_shape_frames(units: list[dict], layers: dict, step_id: str, height: float, interval: int) -> dict[tuple[str,int],int]`. compile_writing_units 결과를 입력받고 (unit_id,piece_index)별 shape draw 프레임을 반환한다. glyph key는 포함하지 않는다. 실패는 InputError.

- [x] **Step 1: 실패 검사 작성.** test_split_invariance는 W=120,H=10,interval=4인 한 조각/24개 같은 폭 조각의 합계가 모두 48임을 검사. test_unequal_widths는 W=40,H=10,interval=4, 폭10/30 → [5,13]을 검사(B=18). test_minimum_and_overfragmentation는 각 할당≥1 및 19개 조각/B=18에서 shape_id를 포함한 InputError를 검사. test_vertical_and_zero_height는 W=0 단일조각=18, zero-height 가로선 W=120=48을 검사. test_identity_scope는 다른 shape/step 예산을 합치지 않음을 검사.
- [x] **Step 2: red 확인.** `P=.agents/skills/ec2-solution-video; PYTHONPATH="$P/scripts" python3 -m unittest discover -s "$P/tests" -p test_shape_timing.py -v`. Expected FAIL: helper 미구현.
- [x] **Step 3: helper 구현.** 원본 bbox로 B 계산, clip 폭에 대한 1프레임 하한 비례 배분/최대 나머지 정수화, authored 순서 동률 처리. NaN/비양수 H/잘못된 interval/누락 대상은 InputError. clip coverage 검증은 기존 compiler를 그대로 사용.
- [x] **Step 4: green 확인.** Step 2 명령과 test_writing_units.py를 각각 실행; 모두 OK.

### Task 2: reveal 연결 및 줄 이동 수정

**Files:** Modify P/scripts/solution_video/reveal.py:18–49; Modify P/tests/test_reveal.py.

**Interfaces:** Task 1 helper를 사용. `build_timeline(...)` 공개 signature 및 writing_spans/events 형식을 유지.

- [x] **Step 1: 실패 검사 작성.** test_spatial_shape_budget는 24조각 상자 draw 합계=48 및 마지막 조각에서만 shape 완료 event가 생김을 검사. test_lift_once_per_new_line은 새 줄 첫 unit에 glyph/shape/공백을 섞어 lifted=True 이동이 첫 대상 한 번임을 검사. test_legacy_writing_unchanged는 typing/non-spatial fixture의 기존 프레임/이벤트 동일성을 검사.
- [x] **Step 2: red 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_reveal.py -v`. 신규 회귀 검사 FAIL, 기존 fixture 통과 여부 기록.
- [x] **Step 3: 연결 구현.** step별 helper 결과를 spatial shape draw에만 적용. lifted는 새 줄 첫 unit의 첫 piece일 때만 true; 공백 첫 대상도 lifted move를 먼저 적용. glyph draw/인접 이동/카메라 전환/clip 순서는 유지.
- [x] **Step 4: green 확인.** Step 2 명령과 test_writing_flow.py를 실행; 모두 OK. 마지막 원본 완성 상태/seek 재현성을 기존 검사로 확인.

### Task 3: 필기 지연과 완성 화면 hold 분리

**Files:** Modify P/scripts/solution_video/narration_pacing.py:36–66; Modify P/tests/test_narration_pacing.py; Modify P/SKILL.md 및 references/narration-and-timing.md, references/verification.md.

**Interfaces:** `analyze_narration_pacing(timeline: dict, audio: list[dict], run: Path) -> dict` signature 유지. segments 각 row에 voice_end_frame, writing_end_frame, writing_lag_frames, completed_hold_frames 추가. top-level unreviewed_writing_lags 추가. `pacing-review.json` 별도 `writing_lags` row = {segment_id,voice_end_frame,writing_end_frame,reason}; 기존 input_hash 동일성 필수.

- [x] **Step 1: 실패 검사 작성.** test_lag_boundary: PCM90프레임, 필기150→lag60으로 통과/151→61로 review-required. test_completed_hold: PCM120, 필기90, segment200→hold80/lag0. test_gap_review_cannot_approve_lag: 과거 gaps 이유만 넣어도 lag61은 미승인. test_explicit_current_lag_review는 별도 일치 row만 승인, stale hash/빈 reason/불일치 경계는 실패. test_pcm_end_separate_from_energy는 PCM tail silence가 voice_end를 앞당기지 않고 기존 energy gaps에 남음을 검사.
- [x] **Step 2: red 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_narration_pacing.py -v`; 신규 검사 FAIL.
- [x] **Step 3: 분석 구현.** voice_end=start_frame+ceil(audio.samples/800), writing_end=마지막 writing_span end, lag=max(0,writing_end-voice_end), hold=max(0,segment_end-max(voice_end,writing_end)). 기존 long-gap 검사 유지. 미승인 gap 또는 lag가 있으면 review-required. 별도 lag 예외는 정확한 경계/현재 hash/비어있지 않은 reason만 인정.
- [x] **Step 4: 정책 문서 갱신.** 지연은 읽기 hold가 아니며 2초 초과 시 별도 검토, audio meaning 검토와 무관함을 명시.
- [x] **Step 5: green 확인.** Step 2 명령 실행; 기존 내부 무음 검사의 기대 결과를 새로운 필기 지연 조건과 분리해 모두 OK.

### Task 4: 재개 검증과 실제 영상 재생성

**Files:** Modify P/scripts/solution_video/state.py:14; Modify P/tests/test_state.py. 새 검토 run과 verification 자료는 기존 날짜의 제작자료 안에 보존.

**Interfaces:** MODULES['timing']에 shape_timing 추가. 기존 CLI retime/assemble/render/captions/verify 그대로 사용. Task 3 보고서 기준으로 실제 마지막 지연을 검사.

- [x] **Step 1: 실패 검사 작성.** test_shape_timing_invalidates_only_timing_and_later: helper 변경 시 voice까지 유효, timing부터 stale이며 WAV 해시 동일.
- [x] **Step 2: red 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p test_state.py -v` → 신규 검사 FAIL.
- [x] **Step 3: fingerprint 수정 및 green 확인.** timing modules에 helper 등록 후 Step 2 명령 OK.
- [x] **Step 4: 전체 회귀 확인.** `PYTHONPATH=.agents/skills/ec2-solution-video/scripts EC2_FFMPEG=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v` 및 `git diff --check`. Expected 모든 tests OK(환경별 기존 skip 명시), diff check exit0.
- [x] **Step 5: Native 최종 독립 리뷰.** 한 명의 새 reviewer가 도형 예산/줄 이동/지연 예외/기존 청크 동기화 유지 여부를 검토. 지적 사항은 red→green 후 반영.
- [x] **Step 6: 기존 산출물 보존과 새 run 준비.** 현재 20261009-193836-6994a849/videos/problem-d885c8738da3 전체를 새 실행 경로에 복사하고 보존본의 final/WAV 해시를 기록. source 절대 경로·state 참조가 있으면 새 run과 실제 snapshot을 대조하며 정정; state 검사를 우회하지 않음. 원본/복사 run의 단계 상태 확인 후 retime부터 진행 가능한지 확인.
- [x] **Step 7: 무료 재생성.** `video.py retime --run RUN`, `assemble --run RUN --runtime /ABS/gsap.min.js`, `render --run RUN --hyperframes-entry /ABS/hyperframes/dist/cli.js`, `captions --run RUN` 순차 실행. 설치 경로 확인 후 실행; tts 호출 안 함. Expected paid_requests=0, 현재 timeline/새 final 생성.
- [x] **Step 8: 수치 검증.** raw/joined WAV SHA256 모두 동일, 청크 누적 샘플 기반 SRT 정렬 통과, 마지막 write_part_3_0의 writing_lag_frames≤60, 누락 glyph/shape 없음. 이전 29.5초 필기/14.4초 상자 draw와 새 측정값을 비교해 기록.
- [x] **Step 9: 전체 시각 검토와 verify.** 시작/중간/마지막 도형/줄 이동/전체 답안 hold를 확인하고 최신 visual review 기록. 실제 청취 가능한 경우만 audio review 작성. `video.py verify --run RUN --hyperframes-entry /ABS/hyperframes/dist/cli.js` 실행; 기술 검사 통과, 청취 불가면 audio_meaning만 unverified 상태를 명시. 기존 잘못된 pacing 승인은 새 run에서 재사용하지 않음.
- [x] **Step 10: 전달.** 새 검토 MP4와 마지막 구간 전후 시간 비교를 사용자에게 제시. 미검증 범위 명시; 게시/커밋/푸시는 별도 요청 범위로 유지.

## Self-review
- 설계의 도형 예산/정수 배분/과분할 오류/줄 이동/지연 기준/예외/무료 재생성/보존 요구는 Tasks 1–4에 대응.
- helper key=(unit_id,piece_index), 모든 pacing row/예외 필드 이름 일치 확인.
- 다섯 Review Focus의 회귀 검사를 각 담당 Task에 포함. 실제 마지막 지연은 예외 우회 없이 ≤60으로 확인.
- 변경 전 미커밋 청크 작업을 보존하며 이 계획은 구현 승인 전 문서만 작성한다.

## 실행 중 확인한 구도 보완
글자 없는 shape-only chunk는 글자 높이에 맞춘 확대 대신 페이지 전체와 연필 여백이 들어오는 구도를 사용한다. 빈 상자 오른쪽으로 확대돼 답안이 사라지는 현상을 막는다. glyph가 있는 chunk의 26px 최소 크기/기존 전환은 유지한다. writing_camera.py와 test_writing_camera.py의 test_shape_only_chunk_keeps_page_context가 담당하며 RED→GREEN 확인 후 assemble/render/captions/verify를 다시 수행한다.

## 실행 결과
225 tests OK(skipped2), 독립 코드 리뷰 clean, 최종 기술/시각 검사12개 passed. PCM66개 해시 보존/유료요청0. 마지막 필기29.5→17.8667초, 상자14.4→3초, 필기지연0. 음성 청취는 unverified이므로 complete=false이며 publish/latest/commit/push를 수행하지 않았다. 새 검토본: 문제풀이영상/1007/1007_제작자료/실행/20261009-200646-shape-speed/videos/problem-d885c8738da3/renders/final.mp4.
